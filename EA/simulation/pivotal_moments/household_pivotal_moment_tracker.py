from __future__ import annotationsimport servicesimport sims4from distributor.rollback import ProtocolBufferRollbackfrom households.household_tracker import HouseholdTrackerfrom situations.situation_serialization import SituationSeedfrom pivotal_moments.pivotal_moment_tracker import PivotalMomentTrackerfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from sims.household import Household
class HouseholdPivotalMomentTracker(HouseholdTracker, PivotalMomentTracker):

    def __init__(self, household:'Household'):
        super().__init__()
        self._household = household

    def save_data(self, household_pivotal_moment_tracker_proto) -> 'None':
        for cpm_id in self._completed_pivotal_moment_ids:
            household_pivotal_moment_tracker_proto.completed_pivotal_moment_ids.append(cpm_id)
        for rpm_id in self._rewarded_pivotal_moment_ids:
            household_pivotal_moment_tracker_proto.rewarded_pivotal_moment_ids.append(rpm_id)
        situation_manager = services.get_zone_situation_manager()
        for pivotal_moment_inst in self._pivotal_moments.values():
            with ProtocolBufferRollback(household_pivotal_moment_tracker_proto.pivotal_moments) as pivotal_moment_data:
                pivotal_moment_inst.save(pivotal_moment_data)
            situation = situation_manager.get(pivotal_moment_inst.situation_id)
            if situation is not None:
                with ProtocolBufferRollback(household_pivotal_moment_tracker_proto.situation_seeds) as seed_proto:
                    seed = situation.save_situation()
                    seed.serialize_to_proto(seed_proto)

    def load_data(self, household_pivotal_moment_tracker_proto) -> 'None':
        tutorial_service = services.get_tutorial_service()
        for cpm_id in household_pivotal_moment_tracker_proto.completed_pivotal_moment_ids:
            if not self.is_pivotal_moment_completed(cpm_id):
                self.add_completed_pivotal_moment(cpm_id)
        for rpm_id in household_pivotal_moment_tracker_proto.rewarded_pivotal_moment_ids:
            if not self.is_pivotal_moment_rewarded(rpm_id):
                self.add_completed_pivotal_moment(rpm_id)
        snippet_manager = services.get_instance_manager(sims4.resources.Types.SNIPPET)
        if snippet_manager is not None:
            for pivotal_moment_save_data in household_pivotal_moment_tracker_proto.pivotal_moments:
                piv_moment = snippet_manager.get(pivotal_moment_save_data.pivotal_moment_id)
                self.load_pivotal_moment(piv_moment, pivotal_moment_save_data, tutorial_service)
        for situation_seed_proto in household_pivotal_moment_tracker_proto.situation_seeds:
            seed = SituationSeed.deserialize_from_proto(situation_seed_proto)
            if seed is not None:
                self.add_pivotal_moment_situation_seed(seed)

    def reset_pivotal_moments(self, should_reset_rewards:'bool'=False) -> 'List':
        pivotal_moment_ids_to_reset = []
        for pivotal_moment_inst in self._pivotal_moments.values():
            if not pivotal_moment_inst.reset():
                pass
            else:
                pivotal_moment_ids_to_reset.append(pivotal_moment_inst.guid64)
        for pivotal_moment_id in pivotal_moment_ids_to_reset:
            self._pivotal_moments.pop(pivotal_moment_id, None)
            if pivotal_moment_id in self._completed_pivotal_moment_ids:
                self._completed_pivotal_moment_ids.remove(pivotal_moment_id)
            if should_reset_rewards and pivotal_moment_id in self._rewarded_pivotal_moment_ids:
                self._rewarded_pivotal_moment_ids.remove(pivotal_moment_id)
        return pivotal_moment_ids_to_reset
