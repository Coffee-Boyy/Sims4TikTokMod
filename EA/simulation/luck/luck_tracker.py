from __future__ import annotationsimport operatorimport servicesimport telemetry_helperfrom distributor.ops import GenericProtocolBufferOpfrom distributor.system import Distributorfrom event_testing.resolver import SingleSimResolverfrom event_testing.test_events import TestEventfrom luck.luck_tuning import LuckTuningfrom sims.sim_info_lod import SimInfoLODLevelfrom protocolbuffers import Sims_pb2from protocolbuffers.DistributorOps_pb2 import Operationfrom sims.sim_info_tracker import SimInfoTrackerfrom sims4 import randomfrom sims4.common import Packfrom sims4.math import Threshold, clampfrom sims4.telemetry import TelemetryWriterfrom sims4.utils import classpropertyfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from luck.luck_tuning import LuckLevel
    from sims.sim_info import SimInfo
    from statistics.base_statistic import BaseStatistic
    from event_testing.resolver import ResolverTELEMETRY_GROUP_LUCK = 'LUCK'TELEMETRY_HOOK_OPTION_DISABLED_EVENT = 'OPTL'TELEMETRY_LUCK_TOTAL_VALUE = 'leve'TELEMETRY_LUCK_BASE_VALUE = 'bsvl'TELEMETRY_LUCK_MODIFIER = 'mdfr'luck_disabled_telemetry_writer = TelemetryWriter(TELEMETRY_GROUP_LUCK)
class LuckTracker(SimInfoTracker):
    LUCK_VALIDITY_TEST_EVENTS = (TestEvent.AgedUp,)
    LUCK_RECALCULATION_TEST_EVENTS = (TestEvent.OnInventoryChanged, TestEvent.ObjectStateChange)
    ALL_TEST_EVENTS = LUCK_VALIDITY_TEST_EVENTS + LUCK_RECALCULATION_TEST_EVENTS

    def __init__(self, sim_info:'SimInfo') -> 'None':
        self._owning_sim_info = sim_info
        self._sim_id = self._owning_sim_info.sim_id
        self._resolver = SingleSimResolver(sim_info)
        self._weekly_refresh_schedule = LuckTuning.LUCK_REFRESH_SCHEDULE(start_callback=self._on_scheduled_refresh, cross_zone=True)
        self._stat_tracker = self._owning_sim_info.get_tracker(LuckTuning.LUCK_STAT)
        self._refresh_missed = False
        self._threshold_listeners = []
        self._current_luck_level = None
        self._luck_service = services.get_luck_service()
        self._luck_service.register_option_changed_listener(self._on_luck_setting_changed)
        self._luck_service.register_zone_ready_listener(self._on_zone_ready)
        self._event_service = services.get_event_manager()
        self._event_service.register(self, self.ALL_TEST_EVENTS)
        self._sim_info_manager = services.sim_info_manager()
        self._sim_info_manager.on_sim_info_removed.append(self._on_sim_info_removed)
        if services.current_zone().is_zone_running:
            self._on_zone_ready()

    @property
    def _has_luck(self) -> 'bool':
        return self._stat_tracker.has_statistic(LuckTuning.LUCK_STAT)

    @property
    def _should_have_luck(self) -> 'bool':
        return LuckTuning.SHOULD_HAVE_LUCK_TESTS.run_tests(self._resolver)

    def _on_zone_ready(self) -> 'None':
        self._update_luck_validity()
        self._subscribe_to_thresholds()
        self._recalculate_luck_level()
        self._send_luck_to_ui()

    def _on_luck_setting_changed(self, enabled:'bool', from_load:'bool') -> 'None':
        if enabled or from_load:
            return
        if enabled or self._owning_sim_info.household_id == services.active_household_id():
            self._send_luck_disabled_telemetry()
        if enabled and self._refresh_missed:
            self.refresh_luck_value()

    def handle_event(self, sim_info:'SimInfo', event:'TestEvent', resolver:'Resolver') -> 'None':
        if sim_info != self._owning_sim_info:
            return
        if event in self.LUCK_VALIDITY_TEST_EVENTS:
            self._update_luck_validity()
        if event in self.LUCK_RECALCULATION_TEST_EVENTS:
            self._recalculate_luck_level()

    @classproperty
    def required_packs(cls) -> 'Tuple[Pack, ...]':
        return (Pack.EP19,)

    @classproperty
    def _tracker_lod_threshold(cls) -> 'SimInfoLODLevel':
        return SimInfoLODLevel.INTERACTED

    def on_lod_update(self, old_lod:'SimInfoLODLevel', new_lod:'SimInfoLODLevel') -> 'None':
        if not self.is_valid_for_lod(new_lod):
            self._teardown()
        elif new_lod >= SimInfoLODLevel.ACTIVE:
            self._send_luck_to_ui()

    def _on_sim_info_removed(self, sim_info:'SimInfo') -> 'None':
        if sim_info.sim_id == self._owning_sim_info.sim_id:
            self._teardown()

    def _teardown(self) -> 'None':
        if self._weekly_refresh_schedule is not None:
            self._weekly_refresh_schedule.destroy()
        if self._luck_service is not None:
            self._luck_service.unregister_option_changed_listener(self._on_luck_setting_changed)
            self._luck_service.unregister_zone_ready_listener(self._on_zone_ready)
        if self._event_service is not None:
            self._event_service.unregister(self, self.ALL_TEST_EVENTS)
        if self._sim_info_manager is not None:
            self._sim_info_manager.on_sim_info_removed.remove(self._on_sim_info_removed)

    def _send_luck_disabled_telemetry(self) -> 'None':
        if not self._has_luck:
            return
        with telemetry_helper.begin_hook(luck_disabled_telemetry_writer, TELEMETRY_HOOK_OPTION_DISABLED_EVENT, sim_info=self._owning_sim_info) as hook:
            luck_stat_instance = self._owning_sim_info.get_stat_instance(LuckTuning.LUCK_STAT, add=True)
            raw_luck_stat_value = luck_stat_instance.get_raw_value()
            luck_stat_value = luck_stat_instance.get_user_value()
            hook.write_float(TELEMETRY_LUCK_BASE_VALUE, raw_luck_stat_value)
            hook.write_float(TELEMETRY_LUCK_MODIFIER, luck_stat_value - raw_luck_stat_value)
            hook.write_float(TELEMETRY_LUCK_TOTAL_VALUE, luck_stat_value)

    def _on_scheduled_refresh(self, *_) -> 'None':
        self.refresh_luck_value()

    def _subscribe_to_thresholds(self) -> 'None':
        for listener in self._threshold_listeners:
            self._stat_tracker.remove_listener(listener)
        self._threshold_listeners.clear()
        if not self._has_luck:
            return
        for luck_level in LuckTuning.LUCK_LEVELS:
            threshold = Threshold(luck_level.interval.lower_bound, operator.ge)
            self._threshold_listeners.append(self._stat_tracker.create_and_add_listener(LuckTuning.LUCK_STAT, threshold, self._on_luck_stat_threshold))

    def _update_luck_validity(self) -> 'None':
        if self._has_luck == self._should_have_luck:
            return
        if self._should_have_luck:
            self.refresh_luck_value()
            self._subscribe_to_thresholds()
            self._recalculate_luck_level()
        else:
            self._stat_tracker.remove_statistic(LuckTuning.LUCK_STAT)

    def refresh_luck_value(self) -> 'None':
        if LuckTuning.LUCK_STAT is None or not self._should_have_luck:
            return
        if not self._luck_service.luck_enabled:
            self._refresh_missed = True
            self._current_luck_level = None
            return
        target_luck_instance = self._owning_sim_info.get_stat_instance(LuckTuning.LUCK_STAT, add=True)
        max_luck = target_luck_instance.max_value
        min_luck = target_luck_instance.min_value
        new_luck_value = random.uniform(min_luck, max_luck)
        target_luck_instance.set_user_value(new_luck_value)
        self._recalculate_luck_level()

    def try_get_luck_level(self) -> 'Optional[LuckLevel]':
        luck_value = self._try_get_luck_value()
        if luck_value is None:
            return
        for luck_level in LuckTuning.LUCK_LEVELS:
            if luck_value in luck_level.interval:
                return luck_level

    def try_get_luck_level_index(self) -> 'Optional[int]':
        luck_level = self.try_get_luck_level()
        if luck_level is None:
            return
        return LuckTuning.LUCK_LEVELS.index(luck_level)

    def _try_get_luck_value(self) -> 'Optional[float]':
        if LuckTuning.LUCK_STAT is None or not (self._luck_service.luck_enabled and self._should_have_luck):
            return
        luck_stat_instance = self._owning_sim_info.get_stat_instance(LuckTuning.LUCK_STAT, add=True)
        luck_stat_value = luck_stat_instance.get_user_value()
        luck_modifier = LuckTuning.LUCK_MODIFIERS.get_modified_value(self._resolver)
        luck_total = clamp(luck_stat_instance.min_value, luck_stat_value + luck_modifier, luck_stat_instance.max_value)
        return luck_total

    def _debug_get_luck_value_breakdown(self) -> 'Optional[Tuple[float, float, float]]':
        if LuckTuning.LUCK_STAT is None or not (self._luck_service.luck_enabled and self._should_have_luck):
            return
        luck_stat_instance = self._owning_sim_info.get_stat_instance(LuckTuning.LUCK_STAT, add=True)
        luck_stat_value = luck_stat_instance.get_user_value()
        luck_modifier = LuckTuning.LUCK_MODIFIERS.get_modified_value(self._resolver)
        luck_total = clamp(luck_stat_instance.min_value, luck_stat_value + luck_modifier, luck_stat_instance.max_value)
        return (luck_stat_value, luck_modifier, luck_total)

    def _debug_force_luck_value(self, value:'float') -> 'None':
        if LuckTuning.LUCK_STAT is None:
            return
        luck_instance = self._owning_sim_info.get_stat_instance(LuckTuning.LUCK_STAT, add=True)
        luck_instance.set_user_value(value)

    def _on_luck_stat_threshold(self, stat_type:'BaseStatistic') -> 'None':
        if services.current_zone().is_zone_running:
            self._recalculate_luck_level()

    def _recalculate_luck_level(self) -> 'None':
        current_level = self.try_get_luck_level()
        if current_level is None or current_level not in LuckTuning.LUCK_LEVELS:
            return
        if current_level == self._current_luck_level:
            return
        self._current_luck_level = current_level
        self._on_luck_level_changed()

    def _on_luck_level_changed(self) -> 'None':
        for loot in self._current_luck_level.loot_on_enter:
            loot.apply_to_resolver(self._resolver)
        self._send_luck_to_ui()

    def _send_luck_to_ui(self) -> 'None':
        if self._owning_sim_info.valid_for_distribution and self._current_luck_level is None:
            return
        current_level_index = LuckTuning.LUCK_LEVELS.index(self._current_luck_level)
        msg = Sims_pb2.LuckUpdate()
        msg.sim_id = self._owning_sim_info.sim_id
        msg.current_level = current_level_index
        distributor = Distributor.instance()
        distributor.add_op(self._owning_sim_info, GenericProtocolBufferOp(Operation.LUCK_UPDATE, msg))
