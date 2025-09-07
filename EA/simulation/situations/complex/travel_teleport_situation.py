from __future__ import annotationsimport servicesimport sims4.resourcesfrom codecs import StreamReaderWriterfrom event_testing.resolver import Resolverfrom event_testing.test_events import TestEventfrom indexed_manager import CallbackTypesfrom objects.base_object import BaseObjectfrom role.role_state import RoleStatefrom sims.sim import Simfrom sims.sim_info import SimInfofrom sims4.tuning.instances import lock_instance_tunablesfrom sims4.tuning.tunable import TunableReferencefrom situations.bouncer.bouncer_types import BouncerExclusivityCategoryfrom situations.situation import Situationfrom situations.situation_complex import CommonInteractionCompletedSituationState, SituationComplexCommon, SituationStateDatafrom situations.situation_serialization import JobDatafrom situations.situation_types import SituationCreationUIOptionfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *TARGET_OBJECT_TOKEN = 'target_object'
class _GatherAtTeleporterState(CommonInteractionCompletedSituationState):

    def timer_expired(self) -> 'None':
        travel_teleport_situation = self.owner
        self._change_state(travel_teleport_situation.teleport_state())

    def _get_role_state_overrides(self, sim:'Sim', job_type:'JobData', role_state_type:'RoleState', role_affordance_target:'BaseObject') -> '(RoleState, BaseObject)':
        return (role_state_type, self.owner.target_object)

    def handle_event(self, sim_info:'SimInfo', event:'TestEvent', resolver:'Resolver') -> 'None':
        try:
            self._sim_info = sim_info
            super().handle_event(sim_info, event, resolver)
        finally:
            self._sim_info = None

    def _on_interaction_of_interest_complete(self, **kwargs) -> 'None':
        travel_teleport_situation = self.owner
        travel_teleport_situation.set_sim_as_gathered(self._sim_info)
        if not travel_teleport_situation.gathering_sim_ids:
            self._change_state(travel_teleport_situation.teleport_state())

class _TeleportState(CommonInteractionCompletedSituationState):

    def _get_role_state_overrides(self, sim:'Sim', job_type:'JobData', role_state_type:'RoleState', role_affordance_target:'BaseObject') -> '(RoleState, BaseObject)':
        return (role_state_type, self.owner.target_object)

    def _additional_tests(self, sim_info:'SimInfo', event:'TestEvent', resolver:'Resolver') -> 'bool':
        travel_teleport_situation = self.owner
        return travel_teleport_situation.is_sim_info_in_situation(sim_info)

    def _on_interaction_of_interest_complete(self, **kwargs) -> 'None':
        travel_teleport_situation = self.owner
        travel_teleport_situation.finish_travel_teleport_situation()

class TravelTeleportSituation(SituationComplexCommon):
    INSTANCE_TUNABLES = {'guest_job': TunableReference(description='\n            The situation job for those gathering to teleport\n            ', manager=services.get_instance_manager(sims4.resources.Types.SITUATION_JOB), class_restrictions=('SituationJob',)), 'host_job': TunableReference(description='\n            The situation job for the Sim responsible for interacting with the teleport object\n            ', manager=services.get_instance_manager(sims4.resources.Types.SITUATION_JOB), class_restrictions=('SituationJob',)), 'gather_at_teleporter_state': _GatherAtTeleporterState.TunableFactory(description='\n            The state to bring all picked Sims to gather at the teleporter.\n            ', display_name='1. Gather at Teleporter State', tuning_group=SituationComplexCommon.SITUATION_STATE_GROUP), 'teleport_state': _TeleportState.TunableFactory(description='\n            The state to have an actor start the teleport action.\n            ', display_name='2. Teleport State', tuning_group=SituationComplexCommon.SITUATION_STATE_GROUP)}
    REMOVE_INSTANCE_TUNABLES = Situation.NON_USER_FACING_REMOVE_INSTANCE_TUNABLES

    def __init__(self, *args, **kwargs) -> 'None':
        super().__init__(*args, **kwargs)
        self.gathering_sim_ids = set()
        self.target_object = self._get_target_object()
        object_manager = services.object_manager()
        object_manager.register_callback(CallbackTypes.ON_OBJECT_REMOVE, self._on_object_removed)
        if self.target_object:
            self.target_object.register_on_location_changed(self._on_object_location_changed)

    def _destroy(self) -> 'None':
        object_manager = services.object_manager()
        object_manager.unregister_callback(CallbackTypes.ON_OBJECT_REMOVE, self._on_object_removed)
        if self.target_object:
            self.target_object.unregister_on_location_changed(self._on_object_location_changed)
        super()._destroy()

    def start_situation(self) -> 'None':
        super().start_situation()
        self._change_state(self.gather_at_teleporter_state())

    def finish_travel_teleport_situation(self) -> 'None':
        self._self_destruct()

    def _on_add_sim_to_situation(self, sim:'Sim', job_type:'JobData', role_state_type_override:'RoleState'=None) -> 'None':
        super()._on_add_sim_to_situation(sim, job_type, role_state_type_override)
        self.gathering_sim_ids.add(sim.id)

    def _on_remove_sim_from_situation(self, sim:'Sim') -> 'None':
        super()._on_remove_sim_from_situation(sim)
        self.gathering_sim_ids.discard(sim.id)

    @classmethod
    def _states(cls) -> '(SituationStateData, SituationStateData)':
        return (SituationStateData(1, _GatherAtTeleporterState, factory=cls.gather_at_teleporter_state), SituationStateData(2, _TeleportState, factory=cls.teleport_state))

    @classmethod
    def _get_tuned_job_and_default_role_state_tuples(cls) -> 'list[Any]':
        return list(cls.gather_at_teleporter_state._tuned_values.job_and_role_changes.items())

    @classmethod
    def default_job(cls) -> 'JobData':
        return cls.guest_job

    def get_target_object(self) -> 'BaseObject':
        return self.target_object

    def _get_target_object(self) -> 'Optional[BaseObject]':
        reader = self._seed.custom_init_params_reader
        if reader is None:
            target_object_id = self._seed.extra_kwargs.get('default_target_id', None)
        else:
            target_object_id = reader.read_uint64(TARGET_OBJECT_TOKEN, None)
        if target_object_id:
            return services.object_manager().get(target_object_id)
        else:
            return

    def set_sim_as_gathered(self, sim_info:'SimInfo') -> 'None':
        if sim_info is None:
            return
        self.gathering_sim_ids.discard(sim_info.id)

    def _on_object_removed(self, obj:'BaseObject') -> 'None':
        if obj.id == self.target_object.id:
            self._self_destruct()

    def _on_object_location_changed(self, obj:'BaseObject') -> 'None':
        if obj.id == self.target_object.id and obj.is_in_inventory():
            self._self_destruct()

    def _save_custom_situation(self, writer:'StreamReaderWriter') -> 'None':
        super()._save_custom_situation(writer)
        if self.target_object is not None:
            writer.write_uint64(TARGET_OBJECT_TOKEN, self.target_object.id)
lock_instance_tunables(TravelTeleportSituation, exclusivity=BouncerExclusivityCategory.NORMAL, creation_ui_option=SituationCreationUIOption.NOT_AVAILABLE)