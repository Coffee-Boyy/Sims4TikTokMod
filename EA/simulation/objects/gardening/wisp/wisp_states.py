from __future__ import annotationsfrom date_and_time import create_time_spanimport randomimport routingimport servicesfrom objects.game_object import GameObjectfrom objects.gardening.wisp.wisp_tuning import WispTuningfrom sims4.log import Loggerfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from date_and_time import TimeSpanlogger = Logger('Wisp', default_owner='swhitehurst')
class WispState:
    STATE_ID = 0

    def exit(self) -> 'None':
        raise NotImplemented

    def get_duration(self) -> 'float':
        raise NotImplemented

    def get_next_state(self) -> 'WispState':
        raise NotImplemented

    def get_state_id(self) -> 'int':
        return self.STATE_ID

    def get_effected_plant_object_ids(self) -> 'List[int]':
        raise NotImplemented

class IdleWispState(WispState):
    STATE_ID = 1

    def __init__(self, plant_object_id:'int') -> 'None':
        plant_object = services.object_manager().get(plant_object_id)
        if plant_object is None:
            logger.error('Unable to set the Idle Wisp State because the object with this id {} cannot be found', plant_object_id)
            return
        plant_object.set_state(state=WispTuning.IDLE_VFX_STATE, new_value=WispTuning.IDLE_VFX_STATE_VALUE_ON)
        self._plant_object_id = plant_object_id

    def exit(self) -> 'None':
        if self._plant_object_id is None:
            return
        plant_object = services.object_manager().get(self._plant_object_id)
        if plant_object is None:
            return
        plant_object.set_state(state=WispTuning.IDLE_VFX_STATE, new_value=WispTuning.IDLE_VFX_STATE_VALUE_OFF, immediate=True, force_update=True)
        self._plant_object_id = None

    def get_duration(self) -> 'TimeSpan':
        return create_time_span(minutes=WispTuning.IDLE_VFX_DURATION)

    def get_next_state(self) -> 'Optional[WispState]':
        compatible_travel_target = self._get_compatible_travel_target()
        if compatible_travel_target is None:
            return
        source_plant = services.object_manager().get(self._plant_object_id)
        if source_plant is None:
            return
        return TravelWispState(self._plant_object_id, compatible_travel_target.id)

    def _get_compatible_travel_target(self) -> 'Optional[GameObject]':
        source_plant = services.object_manager().get(self._plant_object_id)
        if source_plant is None:
            return
        enchanted_plants = services.get_wisp_service().get_nearby_enchanted_gardening_objects(level=source_plant.level, center=source_plant.position, radius=WispTuning.PLANT_SEARCH_RADIUS)
        if len(enchanted_plants) == 0:
            return
        random.shuffle(enchanted_plants)
        for obj in enchanted_plants:
            if obj == source_plant:
                pass
            else:
                source_plant_parent = source_plant.parent if source_plant.parent else source_plant
                target_plant_parent = obj.parent if obj.parent else obj
                (result, blocking_objects) = source_plant_parent.check_line_of_sight(target_plant_parent.transform, verbose=True, use_standard_ignored_objects=True)
                if result == routing.RAYCAST_HIT_TYPE_LOS_IMPASSABLE:
                    pass
                else:
                    return obj

    def get_effected_plant_object_ids(self) -> 'List[int]':
        return [self._plant_object_id]

class TravelWispState(WispState):
    STATE_ID = 2

    def __init__(self, source_plant_id:'int', target_plant_id:'int') -> 'None':
        source_plant = services.object_manager().get(source_plant_id)
        target_plant = services.object_manager().get(target_plant_id)
        if source_plant is None or target_plant is None:
            return
        self._source_plant_id = source_plant_id
        self._target_plant_id = target_plant_id
        self._travel_vfx = WispTuning.TRAVEL_VFX(source_plant, joint_name=WispTuning.TRAVEL_VFX.joint_name, target_actor_id=self._target_plant_id, target_joint_name_hash=WispTuning.TRAVEL_VFX.joint_name, play_immediate=True)
        self._travel_vfx.start()

    def exit(self) -> 'None':
        self._travel_vfx.stop()
        self._travel_vfx = None
        self._source_plant_id = None
        self._target_plant_id = None

    def get_duration(self) -> 'TimeSpan':
        return create_time_span(minutes=WispTuning.TRAVEL_VFX_DURATION)

    def get_next_state(self) -> 'Optional[WispState]':
        if services.object_manager().get(self._target_plant_id) is not None:
            return IdleWispState(self._target_plant_id)
        else:
            return

    def get_effected_plant_object_ids(self) -> 'List[int]':
        return [self._source_plant_id, self._target_plant_id]
