from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import Optional, List, Tuplefrom distributor.rollback import ProtocolBufferRollbackfrom distributor.system import Distributorfrom protocolbuffers import Situations_pb2from situations.base_situation_goal_tracker import BaseSituationGoalTrackerfrom situations.goal_graph import GoalGraphfrom situations.realized_goal_manager import RealizedGoalManagerfrom situations.situation_goal import SituationGoal, UiSituationGoalStatusfrom situations.situation_goal_set import SituationGoalSetfrom situations.situation_serialization import GoalTrackerType, GoalTrackerSeedling, SituationSeedimport distributorimport services
class SituationGraphedGoalTracker(BaseSituationGoalTracker):

    def __init__(self, situation) -> 'None':
        super().__init__(situation)
        self._inherited_target_sim_info = None
        self._realized_minor_goals = RealizedGoalManager()
        self._goals_graph = GoalGraph(self._situation.get_minor_goal_chains())

    def destroy(self) -> 'None':
        self._goals_graph.destroy()
        self._realized_minor_goals.destroy()
        super().destroy()

    def save_to_seed(self, situation_seed:'SituationSeed') -> 'None':
        target_sim_id = 0 if self._inherited_target_sim_info is None else self._inherited_target_sim_info.id
        tracker_seedling = situation_seed.setup_for_goal_tracker_save(GoalTrackerType.STANDARD_GRAPHED_GOAL_TRACKER, self._has_offered_goals, target_sim_id)
        for goal_data in self._realized_minor_goals.get_goals():
            if goal_data:
                goal_seedling = goal_data.create_seedling()
                tracker_seedling.add_minor_goal(goal_seedling)
        tracker_seedling.graphed_goal_seedling.completed_goals_ids = list(self._goals_graph.completed_goals_ids)
        tracker_seedling.graphed_goal_seedling.unlocked_goals_ids = list(self._goals_graph.unlocked_goals_ids)

    def load_from_seedling(self, tracker_seedling:'GoalTrackerSeedling') -> 'None':
        if self._has_offered_goals:
            raise AssertionError('Attempting to load goals for situation: {} but goals have already been offered.'.format(self))
        self._has_offered_goals = tracker_seedling.has_offered_goals
        if tracker_seedling.inherited_target_id != 0:
            self._inherited_target_sim_info = services.sim_info_manager().get(tracker_seedling.inherited_target_id)
        for goal_seedling in tracker_seedling.minor_goals:
            sim_info = services.sim_info_manager().get(goal_seedling.actor_id)
            goal = goal_seedling.goal_type(sim_info=sim_info, situation=self._situation, goal_id=self._goal_id_generator(), count=goal_seedling.count, reader=goal_seedling.reader, locked=goal_seedling.locked, completed_time=goal_seedling.completed_time)
            goal.setup()
            goal.register_for_on_goal_completed_callback(self._on_goal_completed)
            self._realized_minor_goals.add_goal(goal)
        self._goals_graph.load_completed_goals_ids(tracker_seedling.graphed_goal_seedling.completed_goals_ids)
        self._goals_graph.load_unlocked_goals_ids(tracker_seedling.graphed_goal_seedling.unlocked_goals_ids)
        self.send_goal_update_to_client()
        self._validate_goal_status()

    def _offer_goals(self) -> 'bool':
        if not self._realized_minor_goals.can_add_new_goal():
            return False
        else:
            self._goals_graph.init_list_of_unlocked_goals_ids(self._situation.get_minor_goal_chains())
            self._has_offered_goals = True
            goal_actor = self._situation.get_situation_goal_actor()
            goal_actor_sim = goal_actor.get_sim_instance() if goal_actor is not None else None
            MAX_MINOR_GOALS = 3
            num_new_goals = MAX_MINOR_GOALS - len(self._realized_minor_goals)
            new_available_goals = self._goals_graph.offer_n_goals(num_new_goals, self._realized_minor_goals)
            if new_available_goals:
                for goal in new_available_goals:
                    if self._realized_minor_goals.can_add_new_goal() and goal.can_be_given_as_goal(goal_actor_sim, self._situation, inherited_target_sim_info=self._inherited_target_sim_info):
                        goal = self._extract_goal(goal)
                        goal.setup()
                        goal.on_goal_offered()
                        goal.register_for_on_goal_completed_callback(self._on_goal_completed)
                        self._realized_minor_goals.add_goal(goal)
                self._validate_goal_status()
                return True
        return False

    def _validate_goal_status(self):
        for goal in self._realized_minor_goals.get_goals():
            if goal:
                goal.validate_completion()

    def _on_goal_completed(self, goal:'SituationGoal', goal_completed:'bool') -> 'None':
        if goal_completed:
            if self._realized_minor_goals.is_goal_realized(goal):
                self._realized_minor_goals.remove_goal_completed(goal)
                self._goals_graph.on_goal_complete(goal)
                goal.decommision()
                self._inherited_target_sim_info = goal.get_actual_target_sim_info()
                self._situation.on_goal_completed(goal)
                self.refresh_goals(completed_goal=goal)
        else:
            self.send_goal_update_to_client()

    def get_goal_info(self) -> 'List[Tuple[SituationGoal, Optional[SituationGoalSet]]]':
        infos = []
        if self._realized_minor_goals:
            for goal in self._realized_minor_goals.get_goals():
                if goal is not None:
                    infos.append((goal, None))
        return infos

    def get_completed_goal_info(self) -> 'List[Tuple[SituationGoal, Optional[SituationGoalSet]]]':
        return []

    def send_goal_update_to_client(self, completed_goal:'SituationGoal'=None, goal_preferences=None):
        situation_manager = services.get_zone_situation_manager()
        if situation_manager is None or not situation_manager.sim_assignment_complete:
            return
        situation = self._situation
        situation.on_situation_goal_completed(completed_goal)
        if situation.is_user_facing and situation.should_display_score and situation.is_running:
            msg = Situations_pb2.SituationGoalsUpdate()
            msg.situation_id = situation.id
            highlight_first_incomplete_minor_goal = situation.highlight_first_incomplete_minor_goal
            goal_sub_text = situation.get_goal_sub_text()
            if goal_sub_text is not None:
                msg.goal_sub_text = goal_sub_text
            goal_button_text = situation.get_goal_button_text()
            if goal_button_text is not None:
                msg.goal_button_data.button_text = goal_button_text
                msg.goal_button_data.is_enabled = situation.is_goal_button_enabled
            for goal in self._realized_minor_goals.get_goals():
                if goal:
                    if not goal.is_visible:
                        pass
                    else:
                        with ProtocolBufferRollback(msg.goals) as goal_msg:
                            goal.build_goal_message(goal_msg)
                            if highlight_first_incomplete_minor_goal:
                                goal_msg.highlight_goal = True
                                highlight_first_incomplete_minor_goal = False
            msg.goal_status = UiSituationGoalStatus.COMPLETED
            if completed_goal is not None:
                msg.completed_goal_id = completed_goal.id
                goal_status_override = completed_goal.goal_status_override
                if goal_status_override is not None:
                    msg.goal_status = goal_status_override
            op = distributor.ops.SituationGoalUpdateOp(msg)
            Distributor.instance().add_op(situation, op)

    def all_goals_gen(self):
        if len(self._realized_minor_goals) > 0:
            for minor_goal in self._realized_minor_goals.get_goals():
                if minor_goal:
                    yield minor_goal

    def debug_force_complete_by_goal_id(self, goal_id, target_sim=None) -> 'bool':
        for goal in self._realized_minor_goals.get_goals():
            if goal and goal.id == goal_id:
                goal.force_complete(target_sim=target_sim)
                return True
        return False

    def _extract_goal(self, tuned_goal:'SituationGoal') -> 'SituationGoal':
        goal = tuned_goal(sim_info=self._situation.get_situation_goal_actor(), situation=self._situation, goal_id=self._goal_id_generator(), inherited_target_sim_info=self._inherited_target_sim_info)
        return goal
