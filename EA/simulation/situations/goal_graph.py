from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import List, Tuple, Optional, Dictfrom collections import defaultdictfrom situations.situation_goal import SituationGoalfrom situations.situation_goal_set import SituationGoalSetfrom situations.realized_goal_manager import RealizedGoalManagerimport sims4.loglogger = sims4.log.Logger('GoalGraph', default_owner='hbarcelos')
class GoalGraph:

    def __init__(self, start_minor_goals:'List[SituationGoalSet]') -> 'None':
        if start_minor_goals:
            self._graph_unlocks = defaultdict(list)
            self._graph_requires = defaultdict(list)
            self._goals = {}
            self._unlocked_goals_ids = []
            self._completed_goals_ids = []
            self._create_graphs(start_minor_goals)

    def destroy(self) -> 'None':
        self._graph_requires = None
        self._graph_unlocks = None
        self._goals = None
        self._unlocked_goals_ids = None
        self._completed_goals_ids = None

    def _create_graphs(self, start_minor_goals:'List[SituationGoalSet]') -> 'None':
        nodes = list(start_minor_goals)
        while nodes:
            node_a = nodes.pop()
            goal_a = node_a.goals[0].goal
            self._goals[goal_a.guid64] = goal_a
            for node_b in node_a.chained_goal_sets:
                goal_b = node_b.goals[0].goal
                self._goals[goal_b.guid64] = goal_b
                if goal_b not in self._graph_unlocks[goal_a.guid64]:
                    self._graph_unlocks[goal_a.guid64].append(goal_b)
                if goal_a not in self._graph_requires[goal_b.guid64]:
                    self._graph_requires[goal_b.guid64].append(goal_a)
                nodes.append(node_b)

    def get_situation_goal(self, goal_id:'int') -> 'Optional[SituationGoal]':
        return self._goals.get(goal_id, None)

    def init_list_of_unlocked_goals_ids(self, start_minor_goals:'List[SituationGoalSet]') -> 'None':
        if not self._completed_goals_ids:
            for goal_set in list(start_minor_goals):
                self._unlocked_goals_ids.append(goal_set.goals[0].goal.guid64)

    def load_unlocked_goals_ids(self, loaded_unlocked_goals_ids:'List[int]') -> 'None':
        if loaded_unlocked_goals_ids:
            self._unlocked_goals_ids.extend(loaded_unlocked_goals_ids)

    def load_completed_goals_ids(self, loaded_completed_goals_ids:'List[int]') -> 'None':
        if loaded_completed_goals_ids:
            self._completed_goals_ids.extend(loaded_completed_goals_ids)

    def _add_completed_goal(self, goal_completed:'SituationGoal') -> 'None':
        for unlocked_goal_id in self._unlocked_goals_ids:
            if goal_completed.guid64 == unlocked_goal_id:
                self._unlocked_goals_ids.remove(goal_completed.guid64)
                self._completed_goals_ids.append(goal_completed.guid64)
                break

    def _try_add_new_unlocked_goals_ids(self, goal_completed:'SituationGoal') -> 'None':
        possible_unlocked_goals_ids = []
        for goal_guid in list(self._graph_unlocks.keys()):
            if goal_guid == goal_completed.guid64:
                possible_unlocked_goals_ids = self._graph_unlocks[goal_guid]
                break
        if possible_unlocked_goals_ids:
            for possible_unlocked_goal in possible_unlocked_goals_ids:
                requires = self._graph_requires[possible_unlocked_goal.guid64]
                for required_goal in requires:
                    for completed_goal_id in self._completed_goals_ids:
                        if required_goal.guid64 == completed_goal_id:
                            break
                    break
                self._unlocked_goals_ids.append(possible_unlocked_goal.guid64)

    def on_goal_complete(self, goal_completed:'SituationGoal') -> 'None':
        self._add_completed_goal(goal_completed)
        self._try_add_new_unlocked_goals_ids(goal_completed)

    def offer_n_goals(self, n_goals:'int', realized_goal_manager:'RealizedGoalManager') -> 'List[SituationGoal]':
        new_goals = []
        if len(realized_goal_manager) == 0:
            for unlocked_goal_id in self._unlocked_goals_ids[:n_goals]:
                new_goals.append(self.get_situation_goal(unlocked_goal_id))
        else:
            for possible_goal_id in self._unlocked_goals_ids:
                possible_goal = self.get_situation_goal(possible_goal_id)
                if not realized_goal_manager.is_goal_realized(possible_goal):
                    new_goals.append(possible_goal)
                    if len(new_goals) == n_goals:
                        break
        return new_goals

    @property
    def unlocked_goals_ids(self) -> 'Tuple[int, ...]':
        return tuple(self._unlocked_goals_ids)

    @property
    def completed_goals_ids(self) -> 'Tuple[int, ...]':
        return tuple(self._completed_goals_ids)
