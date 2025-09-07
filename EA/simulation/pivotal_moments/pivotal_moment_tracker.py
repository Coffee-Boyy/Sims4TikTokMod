from __future__ import annotationsimport servicesimport sims4from situations.situation_serialization import SituationSeedfrom distributor.system import Distributorimport distributorimport distributor.opsfrom event_testing.resolver import SingleSimResolverfrom situations.situation_types import SituationDisplayTypefrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from pivotal_moments.pivotal_moment import PivotalMoment
    from typing import Dict, List, Set
class PivotalMomentTracker:

    def __init__(self):
        self._pivotal_moments = {}
        self._completed_pivotal_moment_ids = set()
        self._rewarded_pivotal_moment_ids = set()
        self._pivotal_moment_situation_seeds = []

    def get_pivotal_moments(self) -> 'Dict[int, PivotalMoment]':
        return self._pivotal_moments

    def add_pivotal_moment(self, pivotal_moment:'PivotalMoment') -> 'None':
        self._pivotal_moments[pivotal_moment.guid64] = pivotal_moment

    def set_pivotal_moment_completed(self, pivotal_moment_id:'int') -> 'None':
        if pivotal_moment_id not in self._completed_pivotal_moment_ids:
            self._completed_pivotal_moment_ids.add(pivotal_moment_id)

    def remove_pivotal_moment(self, pivotal_moment_id:'int') -> 'None':
        self._pivotal_moments.pop(pivotal_moment_id)

    def get_completed_pivotal_moments(self) -> 'List[int]':
        return self._completed_pivotal_moment_ids

    def add_completed_pivotal_moment(self, pivotal_moment_id:'int') -> 'None':
        self._completed_pivotal_moment_ids.add(pivotal_moment_id)

    def add_completed_pivotal_moments(self, pivotal_moment_ids:'List[int]') -> 'None':
        self._completed_pivotal_moment_ids |= set(pivotal_moment_ids)

    def remove_completed_pivotal_moment(self, pivotal_moment_id:'int') -> 'None':
        self._completed_pivotal_moment_ids.pop(pivotal_moment_id)

    def update_completed_pivotal_moments(self, completed_list:'List[int]') -> 'None':
        self._completed_pivotal_moment_ids.update(completed_list)

    def difference_update_completed_pivotal_moments(self, completed_quest_ids:'set[int]') -> 'None':
        self._completed_pivotal_moment_ids.difference_update(completed_quest_ids)

    def add_rewarded_pivotal_moment(self, pivotal_moment_id:'int') -> 'None':
        self._rewarded_pivotal_moment_ids.add(pivotal_moment_id)

    def remove_rewarded_pivotal_moment(self, pivotal_moment_id:'int') -> 'None':
        self._rewarded_pivotal_moment_ids.pop(pivotal_moment_id)

    def update_rewarded_pivotal_moments(self, completed_list:'List[int]') -> 'None':
        self._rewarded_pivotal_moment_ids.update(completed_list)

    def is_pivotal_moment_tracked(self, pivotal_moment_id:'int') -> 'bool':
        return pivotal_moment_id in self._pivotal_moments

    def get_pivotal_moment_inst(self, pivotal_moment_id:'int') -> 'PivotalMoment':
        return self._pivotal_moments.get(pivotal_moment_id)

    def load_pivotal_moment(self, piv_moment:'PivotalMoment', pivotal_moment_save_data, tutorial_service):
        piv_moment_inst = piv_moment()
        if not piv_moment_inst.should_load():
            return
        piv_moment_inst.load(pivotal_moment_save_data, tutorial_service)
        self._pivotal_moments[piv_moment.guid64] = piv_moment_inst

    def update_activation_triggers(self) -> 'None':
        if len(self._pivotal_moments) > 0:
            for pivotal_moment in self._pivotal_moments.values():
                pivotal_moment.update_activation_triggers()

    def is_pivotal_moment_completed(self, pivotal_moment_id:'int') -> 'bool':
        return pivotal_moment_id in self._completed_pivotal_moment_ids

    def on_pivotal_moment_complete(self, pivotal_moment_id:'int', rewarded:'bool') -> 'None':
        if pivotal_moment_id not in self._completed_pivotal_moment_ids:
            self._completed_pivotal_moment_ids.add(pivotal_moment_id)
        if rewarded and pivotal_moment_id not in self._rewarded_pivotal_moment_ids:
            self._rewarded_pivotal_moment_ids.add(pivotal_moment_id)

    def is_pivotal_moment_rewarded(self, pivotal_moment_id:'int') -> 'bool':
        return pivotal_moment_id in self._rewarded_pivotal_moment_ids

    def set_pivotal_moment_situation_seeds(self, situation_seeds:'List[SituationSeed]') -> 'None':
        self._pivotal_moment_situation_seeds = [seed.get_deserializable_seed_from_serializable_seed() for seed in situation_seeds]

    def add_pivotal_moment_situation_seed(self, seed:'SituationSeed') -> 'None':
        self._pivotal_moment_situation_seeds.append(seed)

    def clear_pivotal_moment_situation_seeds(self) -> 'None':
        self._pivotal_moment_situation_seeds.clear()

    def reevaluate_pending_situations(self) -> 'None':
        tutorial_service = services.get_tutorial_service()
        if not tutorial_service:
            return
        guidance_allows_situation_start = tutorial_service.guidance_allows_situation_start()
        discovery_quest_enables_situation_start = tutorial_service.discovery_quest_enables_situation_start()
        for pivotal_moment_inst in self._pivotal_moments.values():
            is_delayed = pivotal_moment_inst.is_delayed()
            can_start = pivotal_moment_inst.can_situation_start()
            if is_delayed and can_start:
                is_onboarding_requirement = pivotal_moment_inst.is_pivotal_moment_on_required_for_onboarding()
                auto_activate_situation = False
                if guidance_allows_situation_start and is_onboarding_requirement:
                    auto_activate_situation = True
                elif discovery_quest_enables_situation_start:
                    auto_activate_situation = True
                if auto_activate_situation:
                    self.activate_pivotal_moment(pivotal_moment_inst.guid64)

    def activate_minimized_live_events(self:'PivotalMomentTracker') -> 'None':
        for pivotal_moment_inst in self._pivotal_moments.values():
            is_delayed = pivotal_moment_inst.is_delayed()
            is_live_Event = pivotal_moment_inst.get_display_type() == SituationDisplayType.LIVE_EVENT
            if is_delayed and is_live_Event:
                self.activate_pivotal_moment(pivotal_moment_inst.guid64)

    def are_active_discovery_quests_complete(self) -> 'bool':
        for pivotal_moment_inst in self._pivotal_moments.values():
            if not pivotal_moment_inst.is_active():
                pass
            if pivotal_moment_inst.is_onboarding_requirement and pivotal_moment_inst.guid64 not in self._completed_pivotal_moment_ids:
                return False
        return True

    def activate_pivotal_moment(self, pivotal_moment_id):
        for pivotal_moment_inst in self._pivotal_moments.values():
            if pivotal_moment_id == pivotal_moment_inst.guid64 and pivotal_moment_inst.is_delayed():
                pivotal_moment_inst.set_is_pending_from_minimization(True)
                resolver = SingleSimResolver(services.active_sim_info())
                drama_scheduler = services.drama_scheduler_service()
                drama_scheduler.run_node(pivotal_moment_inst.drama_node, resolver)

    def load_pivotal_moment_situations(self) -> 'None':
        situation_manager = services.get_zone_situation_manager()
        if situation_manager is None:
            return
        for seed in self._pivotal_moment_situation_seeds:
            seed._guest_list = seed.situation_type.get_predefined_guest_list()
            situation_manager.create_situation_from_seed(seed)
        self._pivotal_moment_situation_seeds.clear()

    def reset_pivotal_moment(self, pivotal_moment_id:'int', should_reset_rewards:'bool') -> 'None':
        self._pivotal_moments.pop(pivotal_moment_id, None)
        self._completed_pivotal_moment_ids.discard(pivotal_moment_id)
        if should_reset_rewards:
            self._rewarded_pivotal_moment_ids.discard(pivotal_moment_id)
