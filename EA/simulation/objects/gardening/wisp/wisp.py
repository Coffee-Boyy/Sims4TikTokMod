from __future__ import annotationsimport alarmsimport servicesfrom objects.gardening.wisp.wisp_states import IdleWispState, TravelWispState, WispStatefrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from GameplaySaveData_pb2 import WispData
class Wisp:

    def __init__(self) -> 'None':
        self._alarm_handle = None
        self._current_state = None

    @property
    def is_active(self) -> 'bool':
        return self._current_state is not None

    @property
    def current_state(self) -> 'Optional[WispState]':
        return self._current_state

    def start(self, source_plant_id:'int', target_plant_id:'Optional[int]'=None) -> 'None':
        if self.is_active:
            return
        if target_plant_id is None:
            self._current_state = IdleWispState(source_plant_id)
        else:
            self._current_state = TravelWispState(source_plant_id, target_plant_id)
        if self._current_state:
            self._set_state_alarm()

    def _set_state_alarm(self) -> 'None':
        if self._alarm_handle is not None:
            self._stop_alarm()
        if self._current_state is None:
            return
        current_state_duration = self._current_state.get_duration()
        self._alarm_handle = alarms.add_alarm(self, time_span=current_state_duration, callback=self._on_state_finished)

    def _stop_alarm(self) -> 'None':
        if self._alarm_handle is not None:
            alarms.cancel_alarm(self._alarm_handle)
            self._alarm_handle = None

    def _on_state_finished(self, *args) -> 'None':
        next_state = self._current_state.get_next_state()
        self._current_state.exit()
        if next_state is not None:
            self._current_state = next_state
            self._set_state_alarm()
        else:
            self._current_state = None

    def stop(self) -> 'None':
        self._current_state.exit()
        self._stop_alarm()
        self._current_state = None

    def save_wisp_to_proto(self, wisp_proto:'WispData') -> 'None':
        wisp_proto.cycle_state_id = self._current_state.get_state_id()
        wisp_proto.plant_object_ids.extend(self._current_state.get_effected_plant_object_ids())

    def load_wisp_from_proto(self, wisp_proto:'WispData') -> 'None':
        previous_cycle_state_id = wisp_proto.cycle_state_id
        if previous_cycle_state_id == 0:
            return
        if previous_cycle_state_id == IdleWispState.STATE_ID:
            plant_object = services.object_manager().get(wisp_proto.plant_object_ids[0])
            if plant_object is not None:
                self._current_state = IdleWispState(wisp_proto.plant_object_ids[0])
            else:
                return
        elif previous_cycle_state_id == TravelWispState.STATE_ID:
            source_plant_object = services.object_manager().get(wisp_proto.plant_object_ids[0])
            target_plant_object = services.object_manager().get(wisp_proto.plant_object_ids[1])
            if source_plant_object is not None and target_plant_object is not None:
                self._current_state = TravelWispState(wisp_proto.plant_object_ids[0], wisp_proto.plant_object_ids[1])
            else:
                return
        if self._current_state:
            self._set_state_alarm()
