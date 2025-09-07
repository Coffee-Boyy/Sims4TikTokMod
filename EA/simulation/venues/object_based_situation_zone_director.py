from __future__ import annotationsimport sysfrom dataclasses import dataclassfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from protocolbuffers.GameplaySaveData_pb2 import ZoneDirectorData
    from sims4 import PropertyStreamWriter, PropertyStreamReader
    from objects.game_object import GameObjectfrom _weakrefset import WeakSetfrom date_and_time import TimeSpanfrom event_testing.resolver import SingleObjectResolverfrom objects.components import situation_scheduler_componentfrom objects.components.types import SITUATION_SCHEDULER_COMPONENT, STORED_SIM_INFO_COMPONENTfrom scheduler import SituationWeeklyScheduleVariant, WeightedSituationsWeeklySchedule, WeeklySchedule, AlarmDatafrom sims4.tuning.tunable import TunableMapping, TunableTuple, Tunable, OptionalTunable, TunableRange, TunableListfrom sims4.tuning.tunable_base import GroupNamesfrom situations.situation_shifts import SituationShiftsfrom tag import TunableTagimport servicesimport sims4.loglogger = sims4.log.Logger('ObjectBasedSituationZoneDirector', default_owner='hbabaran')
class ObjectBasedSituationData:
    __slots__ = ('situation_schedule', 'schedule_immediate', 'consider_off_lot_objects')

    def __init__(self, situation_schedule=None, schedule_immediate=False, consider_off_lot_objects=True):
        self.situation_schedule = situation_schedule
        self.schedule_immediate = schedule_immediate
        self.consider_off_lot_objects = consider_off_lot_objects

@dataclass
class ObjectSituationShifts:
    situation_shifts = None
    __annotations__['situation_shifts'] = 'SituationShifts'
    schedule_immediate = False
    __annotations__['schedule_immediate'] = 'bool'
    consider_off_lot_objects = True
    __annotations__['consider_off_lot_objects'] = 'bool'
    affected_object_cap = sys.maxsize
    __annotations__['affected_object_cap'] = 'int'
    include_container_tag_list = None
    __annotations__['include_container_tag_list'] = 'list'

class ObjectBasedSituationZoneDirectorMixin:
    INSTANCE_TUNABLES = {'object_situation_shifts': OptionalTunable(description='\n            Enables modern object situation shifts, and ignores deprecated Object Based Situation Schedule.\n            \n            This is a zone-director-based schedule for situations associated with an object tag. The situations \n            specified in this schedule will occur IF: \n                - The tagged object exists in the area (lot or open street), AND\n                - one of the following is true:\n                    > "Use Object Situation Scheduler Component" is unchecked\n                    > the object does not have its own Situations Scheduler Component, \n                    > The object\'s Situations Scheduler Component does not have its own Object Situation Shifts \n                      (Object Based Situation Schedules are deprecated)\n                    > In the object\'s Situations Scheduler Component, "Tests" evaluates to False\n            ', tunable=TunableTuple(description='\n                ', object_situations=TunableMapping(description='\n                    This is a zone-director-based schedule for situations associated with an object tag. The situations \n                    specified in this schedule will occur IF: \n                        - The tagged object exists in the area (lot or open street), AND\n                        - one of the following is true:\n                            > "Use Object Situation Scheduler Component" is unchecked\n                            > the object does not have its own Situations Scheduler Component, \n                            > The object\'s Situations Scheduler Component does not have its own Object Situation Shifts\n                              (Object Based Situation Schedules are deprecated)\n                            > In the object\'s Situations Scheduler Component, "Tests" evaluates to False\n                    ', key_name='object_tag', key_type=TunableTag(description='\n                        An object tag. If the object exist on the zone lot, situations\n                        will be scheduled.\n                        ', filter_prefixes=('func',)), value_name='shift_data', value_type=TunableTuple(description='\n                        This is a zone-director-based schedule for situations associated with an object tag. The situations \n                        specified in this schedule will occur IF: \n                            - The tagged object exists in the area (lot or open street), AND\n                            - one of the following is true:\n                                > "Use Object Situation Scheduler Component" is unchecked\n                                > the object does not have its own Situations Scheduler Component, \n                                > The object\'s Situations Scheduler Component does not have its own Object Situation Shifts\n                                  (Object Based Situation Schedules are deprecated)\n                                > In the object\'s Situations Scheduler Component, "Tests" evaluates to False\n                        ', schedule_immediate=Tunable(description='\n                            This controls the behavior of the scheduler if the current time\n                            happens to fall within a scheduled entry. If this is True, \n                            start_missed_situations will trigger immediately for that entry.\n                            If False, the shift will start at its next scheduled entry.\n                            ', tunable_type=bool, default=True), consider_off_lot_objects=Tunable(description='\n                            If checked, these situations are scheduled for all instances of the object in both the active lot \n                            and the open street. If unchecked, these situations are only scheduled for objects within the active \n                            lot.\n                            ', tunable_type=bool, default=True), affected_object_cap=TunableRange(description='\n                            Specify the maximum number of objects on the zone lot that \n                            can schedule the situations.\n                            ', tunable_type=int, minimum=1, default=1), include_objects_within_object_inventories=OptionalTunable(description="\n                            If enabled, provide one or more Container Object Tags (e.g. func_Crypt). \n                            Objects with any of the Container Object Tags will allow the zone director to include the \n                            container object's inventory in its search for objects that can start situations.\n                            \n                            Staffed Object Situations based on inventoried objects will have the spawned sims \n                            walk up to the container object instead. \n                            ", tunable=TunableList(description='\n                                A list of Container Object Tags. \n                                ', tunable=TunableTag(description="\n                                    An object tag. If an object has this tag, and it has an inventory, the zone director\n                                    can schedule object situations based on objects INSIDE this object's inventory.\n                                    \n                                    Staffed Object Situations based on inventoried objects will have the spawned sims \n                                    walk up to the container object instead.  \n                                    ", filter_prefixes=('func',)))), **SituationShifts.FACTORY_TUNABLES))), tuning_group=GroupNames.SITUATION), 'use_object_situation_scheduler_component': Tunable(description='\n            If this is checked, objects that have their own Situation Scheduler Component enabling Object Situation \n            Shifts with Tests not False will override the schedule defined here with their own.\n            ', tunable_type=bool, default=True, tuning_group=GroupNames.SITUATION), 'object_based_situations_schedule': TunableMapping(description='\n            DEPRECATED: Use Object Situation Shifts instead! \n            If Object Situation Shifts are enabled, this schedule is IGNORED! \n            \n            A zone-director based schedule with an object tag. This schedule is matched to a specific object tag.\n                > If the tagged object doesn\'t exist on the lot, this schedule is ignored. \n                > If the tagged object exists on the zone lot and has its own Situations Scheduler Component AND \n                  "Use Object Provided Situation Schedule" is checked, and the component\'s Tests do not evaluate to \n                   False, this schedule is ignored. \n                > If the tagged object exists on the zone lot, and either does not have its own Situations Scheduler \n                  Component OR "Use Object Provided Situation Schedule" is NOT checked, this schedule is used to spawn \n                  situations.\n            ', deprecated=True, key_type=TunableTag(description='\n                An object tag. If the object exist on the zone lot, situations\n                will be scheduled.\n                ', filter_prefixes=('func',)), value_type=TunableTuple(description='\n                Data associated with situations schedule.\n                ', situation_schedule=SituationWeeklyScheduleVariant(description='\n                    The schedule to trigger the different situations.\n                    ', pack_safe=True, affected_object_cap=True), schedule_immediate=Tunable(description='\n                    This controls the behavior of scheduler if the current time\n                    happens to fall within a schedule entry. If this is True, \n                    a start_callback will trigger immediately for that entry.\n                    If False, the next start_callback will occur on the next entry.\n                    ', tunable_type=bool, default=False), consider_off_lot_objects=Tunable(description='\n                    If True, consider all objects in lot and the open street for\n                    this object situation. If False, only consider objects on\n                    the active lot.\n                    ', tunable_type=bool, default=True))), 'use_object_provided_situations_schedule': Tunable(description='\n            DEPRECATED: Use Object Situation Shifts instead!\n            \n            If checked, objects on the lot and supplement or replace elements of\n            Object Based Situations Schedule.\n            ', deprecated=True, tunable_type=bool, default=True)}

    def __init__(self, *args, **kwargs) -> 'None':
        super().__init__(*args, **kwargs)
        self.affected_objects_map = {}
        self._object_weekly_schedule = {}
        self._object_situation_shifts = {}

    def on_startup(self) -> 'None':
        self._update_object_based_situations_schedule()
        self._start_and_schedule_object_based_situations()
        super().on_startup()

    def on_shutdown(self) -> 'None':
        self._clear_object_situation_shifts()
        super().on_shutdown()

    def _start_and_schedule_object_based_situations(self) -> 'None':
        self._object_weekly_schedule.clear()
        self._cleanup_shifts()
        self._setup_affected_objects_for_weekly_schedule()
        self._start_modern_object_situations()

    def on_exit_buildbuy(self) -> 'None':
        super().on_exit_buildbuy()
        self._update_object_based_situations_schedule()
        self._start_and_schedule_object_based_situations()

    def _save_custom_zone_director(self, zone_director_proto:'ZoneDirectorData', writer:'PropertyStreamWriter') -> 'None':
        zone_director_proto.ClearField('object_situations')
        for (object_tag, object_situation_shifts) in self._object_situation_shifts.items():
            object_situation_shifts.situation_shifts.save_object_situation_shifts(zone_director_proto, object_tag)
        super()._save_custom_zone_director(zone_director_proto, writer)

    def _load_custom_zone_director(self, zone_director_proto:'ZoneDirectorData', reader:'PropertyStreamReader') -> 'None':
        for (object_tag, object_situation_shifts) in self._object_situation_shifts.items():
            object_situation_shifts.situation_shifts.load_object_situation_shifts(zone_director_proto, object_tag)
        super()._load_custom_zone_director(zone_director_proto, reader)

    def _start_modern_object_situations(self) -> 'None':
        for object_situation_shifts in self._object_situation_shifts.values():
            object_situation_shifts.situation_shifts.on_startup()
            object_situation_shifts.situation_shifts.create_situations_during_zone_spin_up()
            if object_situation_shifts.schedule_immediate:
                object_situation_shifts.situation_shifts.start_missed_shifts()

    def _update_object_based_situations_schedule(self) -> 'None':
        self._clear_object_situation_shifts()
        self._object_weekly_schedule.clear()
        if self.object_situation_shifts:
            self._update_object_situation_shifts_schedule()
        else:
            self._update_object_weekly_schedule()

    def _update_object_situation_shifts_schedule(self) -> 'None':
        modern_object_based_situations_schedule = {}
        for (object_tag, shift_data) in self.object_situation_shifts.object_situations.items():
            modern_object_based_situations_schedule[object_tag] = shift_data
        if self.use_object_situation_scheduler_component:
            object_manager = services.object_manager()
            for obj in object_manager.get_valid_objects_gen():
                obj_scheduler_component = obj.get_component(SITUATION_SCHEDULER_COMPONENT)
                if not obj_scheduler_component is None:
                    if obj_scheduler_component.object_situation_shifts is None:
                        pass
                    else:
                        component_shifts_data = obj_scheduler_component.object_situation_shifts
                        resolver = SingleObjectResolver(obj)
                        if not component_shifts_data.tests is None:
                            if not component_shifts_data.tests.run_tests(resolver):
                                pass
                            else:
                                modern_object_based_situations_schedule[component_shifts_data.object_tag] = component_shifts_data
        for (object_tag, modern_object_schedule) in modern_object_based_situations_schedule.items():
            shift_data = {}
            for key in SituationShifts.FACTORY_TUNABLES:
                shift_data[key] = getattr(modern_object_schedule, key)
            self._object_situation_shifts[object_tag] = ObjectSituationShifts(situation_shifts=SituationShifts(**shift_data), schedule_immediate=modern_object_schedule.schedule_immediate, consider_off_lot_objects=modern_object_schedule.consider_off_lot_objects, affected_object_cap=modern_object_schedule.affected_object_cap, include_container_tag_list=modern_object_schedule.include_objects_within_object_inventories)
        self._setup_object_situation_shifts()

    def _update_object_weekly_schedule(self) -> 'None':
        for (object_tag, data) in self.object_based_situations_schedule.items():
            self._object_weekly_schedule[object_tag] = data
        if not self.use_object_provided_situations_schedule:
            return
        object_manager = services.object_manager()
        for obj in object_manager.get_valid_objects_gen():
            obj_situation_scheduler_component = obj.get_component(SITUATION_SCHEDULER_COMPONENT)
            if not obj_situation_scheduler_component is None:
                if obj_situation_scheduler_component.can_remove_weekly_component:
                    pass
                else:
                    data = obj_situation_scheduler_component.object_based_situations_schedule
                    resolver = SingleObjectResolver(obj)
                    if not data.tests is None:
                        if not data.tests.run_tests(resolver):
                            pass
                        else:
                            self._object_weekly_schedule[data.tag] = ObjectBasedSituationData(data.situation_schedule, data.schedule_immediate, data.consider_off_lot_objects)

    def _cleanup_shifts(self) -> 'None':
        self._setup_object_situation_shifts()
        self._cleanup_affected_objects_for_weekly_schedule()

    def _setup_object_situation_shifts(self) -> 'None':
        object_manager = services.object_manager()
        tags_to_del = []
        for (object_tag, shift_data) in self._object_situation_shifts.items():
            tagged_objects = {obj: obj for obj in object_manager.get_objects_with_tag_gen(object_tag) if shift_data.consider_off_lot_objects or obj.is_on_active_lot()}
            if shift_data.include_container_tag_list:
                container_objects = set()
                for container_object_tag in shift_data.include_container_tag_list:
                    container_objects |= {obj for obj in object_manager.get_objects_with_tag_gen(container_object_tag) if not shift_data.consider_off_lot_objects if obj.is_on_active_lot()}
                for container in container_objects:
                    if container.inventory_component:
                        tagged_objects.update({obj: container for obj in container.inventory_component if object_tag in obj.get_tags()})
            if not tagged_objects:
                tags_to_del.append(object_tag)
            else:
                num_affected_objects = min(len(tagged_objects), shift_data.affected_object_cap)
                shift_data.situation_shifts.add_affected_object_count(num_affected_objects)
                object_parameters = []
                for (obj, container) in tagged_objects.items():
                    object_parameters.append({'obj': container, 'sim_from_object': obj.get_stored_sim_info()})
                shift_data.situation_shifts.add_object_parameters(object_parameters)
        for object_tag in tags_to_del:
            self._object_situation_shifts[object_tag].situation_shifts.on_shutdown()
            del self._object_situation_shifts[object_tag]

    def _clear_object_situation_shifts(self) -> 'None':
        for object_situation_shifts in self._object_situation_shifts.values():
            object_situation_shifts.situation_shifts.on_shutdown()
        self._object_situation_shifts.clear()

    @staticmethod
    def _cleanup_object_weekly_schedule(obj:'GameObject') -> 'None':
        obj_situation_scheduler_component = obj.get_component(SITUATION_SCHEDULER_COMPONENT)
        if obj_situation_scheduler_component is None:
            return
        if obj_situation_scheduler_component.can_remove_weekly_component:
            obj.remove_component(SITUATION_SCHEDULER_COMPONENT)
        else:
            obj_situation_scheduler_component.destroy_weekly_scheduler_and_situations()

    def _cleanup_affected_objects_for_weekly_schedule(self) -> 'None':
        object_tags = self._object_weekly_schedule.keys()
        if len(object_tags) == 0:
            return
        object_manager = services.object_manager()
        for obj in object_manager.get_valid_objects_gen():
            if not obj.has_any_tag(object_tags):
                self._cleanup_object_weekly_schedule(obj)

    def _setup_affected_objects_for_weekly_schedule(self) -> 'None':
        object_manager = services.object_manager()
        for (object_tag, data) in self._object_weekly_schedule.items():
            tagged_objects = []
            if data.consider_off_lot_objects:
                tagged_objects = list(object_manager.get_objects_with_tag_gen(object_tag))
            else:
                tagged_objects = [obj for obj in object_manager.get_objects_with_tag_gen(object_tag) if obj.is_on_active_lot()]
            if not tagged_objects:
                pass
            else:
                object_cap = self._get_current_affected_object_cap_for_weekly_schedule(data.situation_schedule)
                if object_tag not in self.affected_objects_map:
                    self.affected_objects_map[object_tag] = WeakSet()
                affected_objects = self.affected_objects_map[object_tag]
                while len(affected_objects) < object_cap and tagged_objects:
                    obj_to_add = tagged_objects.pop()
                    if obj_to_add in affected_objects:
                        pass
                    else:
                        scheduler = data.situation_schedule(start_callback=self._start_weekly_situations, schedule_immediate=data.schedule_immediate, extra_data=obj_to_add)
                        if obj_to_add.has_component(SITUATION_SCHEDULER_COMPONENT):
                            obj_to_add.set_weekly_situation_scheduler(scheduler)
                        else:
                            obj_to_add.add_dynamic_component(SITUATION_SCHEDULER_COMPONENT, scheduler=scheduler)
                        affected_objects.add(obj_to_add)
                while len(affected_objects) > object_cap and affected_objects:
                    obj_to_remove = affected_objects.pop()
                    self._cleanup_object(obj_to_remove)

    def _start_weekly_situations(self, scheduler:'WeeklySchedule', alarm_data:'AlarmData', obj:'GameObject') -> 'None':
        self._setup_affected_objects_for_weekly_schedule()
        if not scheduler.extra_data.has_component(SITUATION_SCHEDULER_COMPONENT):
            return
        if hasattr(alarm_data.entry, 'weighted_situations'):
            resolver = SingleObjectResolver(obj)
            (situation, params) = WeightedSituationsWeeklySchedule.get_situation_and_params(alarm_data.entry, resolver=resolver)
        else:
            situation = alarm_data.entry.situation
            params = {}
        if situation is None:
            return
        obj.create_weekly_situation(situation, **params)

    @staticmethod
    def _get_current_affected_object_cap_for_weekly_schedule(schedule:'WeeklySchedule') -> 'int':
        current_time = services.time_service().sim_now
        (best_time, alarm_data) = schedule().time_until_next_scheduled_event(current_time, schedule_immediate=True)
        if best_time is None:
            current_affected_object_cap = 0
        elif best_time > TimeSpan.ZERO:
            current_affected_object_cap = 1
        else:
            current_affected_object_cap = alarm_data[0].entry.affected_object_cap
        return current_affected_object_cap
