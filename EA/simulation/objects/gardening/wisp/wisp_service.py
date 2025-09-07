from __future__ import annotationsimport alarmsimport servicesfrom objects.components.types import GARDENING_COMPONENTfrom objects.gardening.gardening_tuning import GardeningTuningfrom objects.gardening.wisp.wisp import Wispfrom objects.gardening.wisp.wisp_tuning import WispTuningfrom persistence_error_types import ErrorCodesfrom sims4 import randomfrom sims4.common import Packfrom sims4.service_manager import Servicefrom sims4.utils import classpropertyfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from objects.game_object import GameObject
    from Math_pb2 import Vector3
    from protocolbuffers.FileSerialization_pb2 import ZoneData, OpenStreetsData, SaveSlotData
    from scheduler import AlarmData, WeeklySchedule
class WispService(Service):

    def __init__(self, *args, **kwargs) -> 'None':
        super().__init__(*args, **kwargs)
        self._wisp = None
        self._weekly_wisp_schedule = WispTuning.WISP_SCHEDULE(start_callback=self._try_scheduled_start_wisp, cross_zone=True)
        self._end_alarm_handle = None

    @classproperty
    def required_packs(cls) -> 'Tuple[Pack]':
        return (Pack.EP19,)

    @classproperty
    def save_error_code(cls) -> 'ErrorCodes':
        return ErrorCodes.SERVICE_SAVE_FAILED_WISP_SERVICE

    @staticmethod
    def get_nearby_enchanted_gardening_objects(*, level, center, radius) -> 'List[GameObject]':
        if GardeningTuning.ENCHANTED_STATE is None:
            return []
        enchanted_gardening_objects = []
        gardening_service = services.get_gardening_service()
        for obj in gardening_service.get_gardening_objects(level=level, center=center, radius=radius):
            if GardeningTuning.is_enchanted(obj):
                enchanted_gardening_objects.append(obj)
        return enchanted_gardening_objects

    @staticmethod
    def _get_all_gardening_plants() -> 'List[GameObject]':
        gardening_plants = []
        for obj in services.object_manager().get_all_objects_with_component_gen(GARDENING_COMPONENT):
            gardening_component = obj.get_component(GARDENING_COMPONENT)
            if not gardening_component.is_plant:
                pass
            else:
                gardening_plants.append(obj)
        return gardening_plants

    def get_wisp(self) -> 'Optional[Wisp]':
        return self._wisp

    def is_wisp_running_on_object(self, obj:'GameObject') -> 'bool':
        if self._wisp is None or not self._wisp.is_active:
            return False
        elif obj.id in self._wisp.current_state.get_effected_plant_object_ids():
            return True
        return False

    def _try_scheduled_start_wisp(self, scheduler:'WeeklySchedule', alarm_data:'AlarmData', extra_data:'Optional[Any]') -> 'None':
        if self._wisp is not None and self._wisp.is_active:
            return
        enchanted_plant_objects = []
        for plant_obj in self._get_all_gardening_plants():
            if not GardeningTuning.is_enchanted(plant_obj):
                pass
            else:
                surrounding_enchanted_plants = self.get_nearby_enchanted_gardening_objects(level=plant_obj.level, center=plant_obj.position, radius=WispTuning.PLANT_SEARCH_RADIUS)
                num_of_surrounding_enchanted_plants = len(surrounding_enchanted_plants)
                if num_of_surrounding_enchanted_plants < WispTuning.MINIMUM_NUMBER_OF_SURROUNDING_ENCHANTED_PLANTS:
                    pass
                else:
                    enchanted_plant_objects.append((num_of_surrounding_enchanted_plants, plant_obj))
        if len(enchanted_plant_objects) < WispTuning.MINIMUM_NUMBER_OF_ENCHANTED_PLANTS_ON_LOT:
            return
        random_obj = random.weighted_random_item(enchanted_plant_objects)
        if self._wisp is None:
            self._wisp = Wisp()
        self._wisp.start(random_obj.id)
        now = services.time_service().sim_now
        time_to_end = alarm_data.end_time - now.time_since_beginning_of_week()
        self._end_alarm_handle = alarms.add_alarm(self, time_to_end, callback=self._on_scheduled_stop_wisp, cross_zone=True)

    def _on_scheduled_stop_wisp(self, *args) -> 'None':
        if self._wisp.is_active:
            self._wisp.stop()

    def force_start_wisp_on_object(self, plant_object_id:'int') -> 'None':
        if plant_object_id is None:
            return
        if self._wisp is None:
            self._wisp = Wisp()
        self._wisp.start(plant_object_id)

    def stop_wisp(self) -> 'None':
        if self._wisp is not None:
            self._wisp.stop()

    def save(self, object_list:'List[GameObject]'=None, zone_data:'ZoneData'=None, open_street_data:'OpenStreetsData'=None, save_slot_data:'SaveSlotData'=None) -> 'None':
        if self._wisp is not None and self._wisp.is_active:
            wisp_service_data = save_slot_data.gameplay_data.wisp_service
            self._wisp.save_wisp_to_proto(wisp_service_data.wisp_data)

    def load(self, zone_data:'ZoneData'=None) -> 'None':
        save_slot_data_msg = services.get_persistence_service().get_save_slot_proto_buff()
        wisp_service_data = save_slot_data_msg.gameplay_data.wisp_service
        if wisp_service_data is None:
            return
        if wisp_service_data.wisp_data:
            if self._wisp is None:
                self._wisp = Wisp()
            self._wisp.load_wisp_from_proto(wisp_service_data.wisp_data)

    def on_plant_removed(self, plant_object:'GameObject') -> 'None':
        if self._wisp is None or not self._wisp.is_active:
            return
        plant_object_id = plant_object.id
        if plant_object_id in self._wisp.current_state.get_effected_plant_object_ids():
            self.stop_wisp()
