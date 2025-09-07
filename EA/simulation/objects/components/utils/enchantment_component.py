from __future__ import annotationsimport operatorimport sims4from objects.components import Component, componentmethod_with_fallbackfrom objects.components.types import ENCHANTMENT_COMPONENTfrom objects.gardening.gardening_tuning import GardeningTuningfrom objects.hovertip import TooltipFieldsCompletefrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from date_and_time import DateAndTime
    from objects.components.state import ObjectState, ObjectStateValue
    from protocolbuffers.SimObjectAttributes_pb2 import PersistenceMaster
    from statistics.commodity import Commoditylogger = sims4.log.Logger('EnchantmentComponent', default_owner='swhitehurst')
class EnchantmentComponent(Component, component_name=ENCHANTMENT_COMPONENT):

    def __init__(self, *args, **kwargs) -> 'None':
        super().__init__(*args, **kwargs)
        self._enchantment_listener_handle = None
        self._last_enchantment_time = None
        self.hovertip_requested = False
        tooltip_component = self.owner.tooltip_component
        if tooltip_component is not None:
            self.hovertip_requested = tooltip_component.hovertip_requested
        self._enchantment_off_timer_state_value = GardeningTuning.ENCHANTED_STATE_VALUE_OFF
        self.on_add_hovertip()

    def on_hovertip_requested(self) -> 'bool':
        if not self.hovertip_requested:
            self.hovertip_requested = True
            self.refresh_timer()
            return True
        return False

    def on_remove(self) -> 'None':
        self.remove_time_listener()
        self.owner.update_tooltip_field(TooltipFieldsComplete.enchantment_time, None)

    def on_state_changed(self, state:'ObjectState', old_value:'ObjectStateValue', new_value:'ObjectStateValue', from_init:'bool') -> 'None':
        self.refresh_timer()

    def refresh_timer(self) -> 'None':
        self.remove_time_listener()
        self.on_add_hovertip()

    def on_add_hovertip(self) -> 'None':
        self._add_time_listener()

    def save(self, persistence_master_message:'PersistenceMaster') -> 'None':
        self.pre_save()

    def pre_save(self) -> 'None':
        self.owner.update_tooltip_field(TooltipFieldsComplete.enchantment_time, 0, should_update=True)

    @componentmethod_with_fallback(lambda : None)
    def post_tooltip_save_data_stored(self) -> 'None':
        if self._last_enchantment_time is not None:
            self._on_time_changed(None, self._last_enchantment_time)

    def _on_time_changed(self, _:'Commodity', enchantment_time:'DateAndTime') -> 'None':
        if self._last_enchantment_time is None or self._last_enchantment_time != enchantment_time:
            self._last_enchantment_time = enchantment_time
        if enchantment_time is not None and GardeningTuning.is_enchanted(self.owner):
            time_in_ticks = enchantment_time.absolute_ticks()
            self.owner.update_tooltip_field(TooltipFieldsComplete.enchantment_time, time_in_ticks, should_update=True)
            logger.debug('{} will no longer be enchanted at {}', self.owner, enchantment_time)
        else:
            self.owner.update_tooltip_field(TooltipFieldsComplete.enchantment_time, 0, should_update=True)

    def _on_timer_finished(self, _:'Commodity') -> 'None':
        self._last_enchantment_time = None
        self.owner.update_object_tooltip()
        if self.owner.has_component(ENCHANTMENT_COMPONENT):
            self.owner.remove_component(ENCHANTMENT_COMPONENT)

    def _add_time_listener(self) -> 'None':
        check_operator = operator.lt
        if self._enchantment_listener_handle is None:
            linked_stat = self._enchantment_off_timer_state_value.state.linked_stat
            tracker = self.owner.get_tracker(linked_stat)
            if tracker is None:
                return
            threshold = sims4.math.Threshold()
            threshold.value = self._enchantment_off_timer_state_value.range.upper_bound
            threshold.comparison = check_operator
            self._enchantment_listener_handle = tracker.create_and_add_listener(linked_stat, threshold, self._on_timer_finished, on_callback_alarm_reset=self._on_time_changed)

    def remove_time_listener(self) -> 'None':
        if self._enchantment_listener_handle is not None:
            enchantment_tracker = self.owner.get_tracker(self._enchantment_off_timer_state_value.state.linked_stat)
            enchantment_tracker.remove_listener(self._enchantment_listener_handle)
            self._enchantment_listener_handle = None
        self._last_enchantment_time = None
