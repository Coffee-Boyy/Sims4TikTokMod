from __future__ import annotationsfrom dataclasses import dataclassfrom luck.luck_archiver import LuckArchiveEntry, add_luck_archive_entryfrom luck.luck_tuning import LuckTuningfrom sims4.callback_utils import CallableListfrom sims4.common import Packfrom sims4.log import Loggerfrom sims4.math import remap_rangefrom sims4.random import weighted_random_indexfrom sims4.service_manager import Servicefrom sims4.utils import classpropertyfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.resolver import Resolver
    from luck.luck_tuning import LuckLevel
    from luck.luck_config import LuckConfig
    from protocolbuffers.GameplaySaveData_pb2 import GameplayOptions
    from sims.sim_info import SimInfologger = Logger('Luck', default_owner='mjuskelis')
@dataclass(frozen=True)
class LuckOption:
    __annotations__['weight'] = 'float'
    __annotations__['perceived_value'] = 'float'
    __annotations__['user_data'] = 'Any'
    show_luck_impacts = True
    __annotations__['show_luck_impacts'] = 'bool'

@dataclass(frozen=True)
class LuckChoiceResult:
    __annotations__['selected_option'] = 'LuckOption'
    __annotations__['did_luck_impact_selection'] = 'bool'
    luck_level = None
    __annotations__['luck_level'] = 'Optional[LuckLevel]'

    @property
    def selected_data(self) -> 'Any':
        return self.selected_option.user_data

    @property
    def should_show_impacts(self) -> 'bool':
        return self.did_luck_impact_selection and (self.luck_level is not None and (self.luck_level.should_show_impacts and self.selected_option.show_luck_impacts))

    def __repr__(self) -> 'str':
        return super().__repr__()

class _LuckSelectionData:
    __slots__ = ('options', 'selection_index', 'selection')

    def __init__(self, options:'List[LuckOption]', weights:'List[float]') -> 'None':
        self.options = options
        self.selection_index = weighted_random_index(zip(weights, options))
        self.selection = options[self.selection_index]

class _LuckChoiceData:
    __slots__ = ('input_options', 'input_weights', 'normal_selection', 'normal_selection_perception', 'luck_weights', 'luck_selection', 'luck_selection_perception', 'luck_level', 'target', 'archiver')

    def __init__(self, input_options:'List[LuckOption]') -> 'None':
        self.input_options = input_options
        self.input_weights = [option.weight for option in input_options]
        self.normal_selection = _LuckSelectionData(self.input_options, self.input_weights)
        self.normal_selection_perception = 0
        self.luck_weights = []
        self.luck_selection = None
        self.luck_selection_perception = 0
        self.luck_level = None
        self.target = None
        self.archiver = None

    def add_archiving(self, archive_entry:'LuckArchiveEntry') -> 'None':
        self.archiver = archive_entry
        self.archiver.choice_data = self

    def add_target(self, target:'SimInfo') -> 'None':
        self.target = target

    def add_luck_selection(self, luck_level:'LuckLevel') -> 'None':
        self.luck_level = luck_level
        self.luck_weights = LuckService._get_weights_for_luck_level(self.input_options, luck_level)
        self.luck_selection = _LuckSelectionData(self.input_options, self.luck_weights)
        self.normal_selection_perception = LuckService._get_option_perception_for_level(self.input_options[self.normal_selection.selection_index], self.luck_level)
        self.luck_selection_perception = LuckService._get_option_perception_for_level(self.input_options[self.luck_selection.selection_index], self.luck_level)

    def _log_archive_entry(self, used_luck:'bool', surfaced_luck:'bool') -> 'None':
        if self.archiver is None:
            return

    def choose_option(self) -> 'Optional[LuckChoiceResult]':
        if self.luck_selection is None:
            self._log_archive_entry(used_luck=False, surfaced_luck=False)
            return LuckChoiceResult(self.normal_selection.selection, False)
        if self.luck_selection.selection_index == self.normal_selection.selection_index:
            self._log_archive_entry(used_luck=False, surfaced_luck=False)
            return LuckChoiceResult(self.normal_selection.selection, False)
        if self.luck_selection_perception > self.normal_selection_perception:
            self._log_archive_entry(used_luck=True, surfaced_luck=True)
            return LuckChoiceResult(self.luck_selection.selection, True, self.luck_level)
        self._log_archive_entry(used_luck=True, surfaced_luck=False)
        return LuckChoiceResult(self.luck_selection.selection, False)

class LuckService(Service):

    def __init__(self) -> 'None':
        self._luck_enabled = True
        self._luck_enabled_changed_listeners = CallableList()
        self._zone_ready_listeners = CallableList()

    def save_options(self, options_proto:'GameplayOptions') -> 'None':
        options_proto.luck_enabled = self.luck_enabled

    def load_options(self, options_proto:'GameplayOptions') -> 'None':
        self._set_luck_enabled(options_proto.luck_enabled, True)

    @classproperty
    def required_packs(cls) -> 'Tuple[Pack, ...]':
        return (Pack.EP19,)

    @property
    def luck_enabled(self) -> 'bool':
        return self._luck_enabled

    def register_option_changed_listener(self, callback:'Callable[[bool, bool], None]') -> 'None':
        self._luck_enabled_changed_listeners.register(callback)

    def unregister_option_changed_listener(self, callback:'Callable[[bool, bool], None]') -> 'None':
        self._luck_enabled_changed_listeners.unregister(callback)

    def _set_luck_enabled(self, value:'bool', from_load:'bool'=False) -> 'None':
        self._luck_enabled = value
        self._luck_enabled_changed_listeners(value, from_load)

    def register_zone_ready_listener(self, callback:'Callable[[], None]') -> 'None':
        self._zone_ready_listeners.register(callback)

    def unregister_zone_ready_listener(self, callback:'Callable[[], None]') -> 'None':
        self._zone_ready_listeners.unregister(callback)

    def on_zone_load(self):
        self._zone_ready_listeners()

    @staticmethod
    def _get_weights_for_luck_level(options:'List[LuckOption]', luck_level:'LuckLevel') -> 'List[float]':
        weights = [option.weight*LuckService._get_option_perception_for_level(option, luck_level) for option in options]
        min_weight = min(weights)
        if min_weight <= 0:
            weights = [weight + abs(min_weight) + LuckTuning.NORMALIZED_LUCK_WEIGHT_RANGE.lower_bound for weight in weights]
        return weights

    @staticmethod
    def _get_option_perception_for_level(option:'LuckOption', level:'LuckLevel') -> 'float':
        multiplier = option.perceived_value*level.perceived_value_bias
        return remap_range(multiplier, LuckTuning.PERCEPTION_RANGE.lower_bound, LuckTuning.PERCEPTION_RANGE.upper_bound, LuckTuning.NORMALIZED_LUCK_WEIGHT_RANGE.lower_bound, LuckTuning.NORMALIZED_LUCK_WEIGHT_RANGE.upper_bound)

    def choose_with_luck(self, caller:'Any', options:'List[LuckOption]', resolver:'Resolver', luck_config:'LuckConfig') -> 'LuckChoiceResult':
        filtered_options = [option for option in options if option.weight > 0]
        choice_data = _LuckChoiceData(filtered_options)
        if not self.luck_enabled:
            return choice_data.choose_option()
        subject = resolver.get_participant(luck_config.participant)
        if subject is None:
            logger.error("Tried to choose luck with participant type '{}' for resolver '{}'.", subject_participant, resolver)
            return choice_data.choose_option()
        choice_data.add_target(subject)
        luck_tracker = subject.luck_tracker
        if luck_tracker is None:
            return choice_data.choose_option()
        luck_level = luck_tracker.try_get_luck_level()
        if luck_level is not None and luck_level.should_use_luck:
            choice_data.add_luck_selection(luck_level)
        return choice_data.choose_option()

    def choose_with_luck_and_apply_loots(self, caller:'Any', options:'List[LuckOption]', resolver:'Resolver', luck_config:'LuckConfig') -> 'LuckChoiceResult':
        result = self.choose_with_luck(caller, options, resolver, luck_config)
        if result.should_show_impacts:
            result.luck_level.impact_loot.apply_to_resolver(resolver)
            for loot in luck_config.loot_actions:
                loot.apply_to_resolver(resolver)
        return result
