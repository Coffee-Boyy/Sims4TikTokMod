from __future__ import annotationsimport enumfrom collections import namedtuplefrom dataclasses import dataclassfrom luck.luck_option import TunableLuckOptionDatafrom luck.luck_service import LuckOptionfrom sims4.localization import TunableLocalizedStringFactoryfrom sims4.tuning.tunable import HasTunableSingletonFactory, AutoFactoryInit, TunableList, TunableTuple, TunableReference, TunableRangefrom snippets import define_snippetfrom tunable_multiplier import TunableMultiplierimport servicesimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.resolver import Resolver
    from fishing.fish_object import Fish
    from luck.luck_config import LuckConfig
    from luck.luck_service import LuckChoiceResult, LuckService
    from luck.luck_tuning import LuckLevel
    from objects.game_object import GameObject
    from SimObjectAttributes_pb2 import FishingDatalogger = sims4.log.Logger('Fishing', default_owner='TrevorLindsey')
class FishingChoiceCategory(enum.Int):
    NONE = (0,)
    FISH = (1,)
    TREASURE = (2,)
    JUNK = (3,)

@dataclass
class FishingChoiceResult:
    chosen_item = None
    __annotations__['chosen_item'] = 'Any'
    chosen_category = FishingChoiceCategory.NONE
    __annotations__['chosen_category'] = 'FishingChoiceCategory'
    should_show_luck_impact = False
    __annotations__['should_show_luck_impact'] = 'bool'
    luck_level = None
    __annotations__['luck_level'] = 'LuckLevel'

    def capture_luck_result(self, result:'LuckChoiceResult') -> 'None':
        self.should_show_luck_impact |= result.should_show_impacts
        if result.luck_level is not None:
            self.luck_level = result.luck_level

class FishingDataBase:

    def get_possible_fish_gen(self):
        yield from self.possible_fish

    def choose_fish(self, resolver:'Resolver', require_bait:'bool', luck_config:'Optional[LuckConfig]') -> 'FishingChoiceResult':
        result = FishingChoiceResult()
        result.chosen_category = FishingChoiceCategory.FISH
        luck_service = services.get_luck_service()
        if luck_config is None or luck_service is None:
            result.chosen_item = self._choose_individual_fish(resolver, require_bait)
        else:
            luck_result = self._choose_individual_fish_with_luck(resolver, require_bait, luck_config, luck_service)
            result.capture_luck_result(luck_result)
            result.chosen_item = luck_result.selected_option.user_data
        if result.chosen_item is None:
            result.chosen_category = FishingChoiceCategory.NONE
        return result

    def _choose_individual_fish(self, resolver:'Resolver', require_bait:'bool') -> 'Optional[GameObject]':
        weighted_fish = [(f.weight.get_multiplier(resolver), f.fish) for f in self.possible_fish if f.fish.cls.can_catch(resolver, require_bait=require_bait)]
        if weighted_fish:
            return sims4.random.weighted_random_item(weighted_fish)

    def _choose_individual_fish_with_luck(self, resolver:'Resolver', require_bait:'bool', luck_config:'LuckConfig', luck_service:'LuckService') -> 'Optional[LuckChoiceResult]':
        weighted_fish = []
        for potential_fish in self.possible_fish:
            if not potential_fish.fish.cls.can_catch(resolver, require_bait=require_bait):
                pass
            else:
                weighted_fish.append(LuckOption(weight=potential_fish.weight.get_multiplier(resolver), perceived_value=potential_fish.luck_option_config.player_perception, user_data=potential_fish.fish, show_luck_impacts=potential_fish.luck_option_config.show_impacts))
        if weighted_fish:
            return luck_service.choose_with_luck(self, weighted_fish, resolver, luck_config)

    def _choose_individual_treasure(self, resolver:'Resolver') -> 'Optional[GameObject]':
        weighted_treasures = [(t.weight.get_multiplier(resolver), t.treasure) for t in self.possible_treasures]
        if weighted_treasures:
            return sims4.random.weighted_random_item(weighted_treasures)

    def _choose_individual_treasure_with_luck(self, resolver:'Resolver', luck_config:'LuckConfig', luck_service:'LuckService') -> 'Optional[LuckChoiceResult]':
        weighted_treasures = []
        for potential_treasure in self.possible_treasures:
            weighted_treasures.append(LuckOption(weight=potential_treasure.weight.get_multiplier(resolver), perceived_value=potential_treasure.luck_option_config.player_perception, user_data=potential_treasure.treasure, show_luck_impacts=potential_treasure.luck_option_config.show_impacts))
        if weighted_treasures:
            return luck_service.choose_with_luck(self, weighted_treasures, resolver, luck_config)

    def choose_any(self, resolver:'Resolver', luck_config:'Optional[LuckConfig]') -> 'FishingChoiceResult':
        result = FishingChoiceResult()
        luck_service = services.get_luck_service()
        if luck_config is None or luck_service is None:
            result.chosen_category = self._choose_category_option(resolver)
            if result.chosen_category == FishingChoiceCategory.JUNK:
                return result
            if result.chosen_category == FishingChoiceCategory.FISH:
                result.chosen_item = self._choose_individual_fish(resolver, require_bait=True)
            if result.chosen_category == FishingChoiceCategory.TREASURE:
                result.chosen_item = self._choose_individual_treasure(resolver)
            if result.chosen_item is None:
                result.chosen_category = FishingChoiceCategory.NONE
            return result
        luck_category_choice_result = self._choose_category_option_with_luck(resolver, luck_config, luck_service)
        result.capture_luck_result(luck_category_choice_result)
        result.chosen_category = luck_category_choice_result.selected_data
        luck_item_choice_result = None
        if result.chosen_category == FishingChoiceCategory.JUNK:
            return result
        if result.chosen_category == FishingChoiceCategory.FISH:
            luck_item_choice_result = self._choose_individual_fish_with_luck(resolver, True, luck_config, luck_service)
        elif result.chosen_category == FishingChoiceCategory.TREASURE:
            luck_item_choice_result = self._choose_individual_treasure_with_luck(resolver, luck_config, luck_service)
        if luck_item_choice_result is None:
            result.chosen_category = FishingChoiceCategory.NONE
        else:
            result.capture_luck_result(luck_item_choice_result)
            result.chosen_item = luck_item_choice_result.selected_data
        return result

    def _choose_category_option(self, resolver:'Resolver') -> 'FishingChoiceCategory':
        weighted_outcomes = [(self.weight_fish.weight.get_multiplier(resolver), FishingChoiceCategory.FISH), (self.weight_junk.weight.get_multiplier(resolver), FishingChoiceCategory.JUNK), (self.weight_treasure.weight.get_multiplier(resolver), FishingChoiceCategory.TREASURE)]
        return sims4.random.weighted_random_item(weighted_outcomes)

    def _choose_category_option_with_luck(self, resolver:'Resolver', luck_config:'LuckConfig', luck_service:'LuckService') -> 'LuckChoiceResult':
        weighted_outcomes = [LuckOption(weight=self.weight_fish.weight.get_multiplier(resolver), perceived_value=self.weight_fish.luck_option_config.player_perception, user_data=FishingChoiceCategory.FISH, show_luck_impacts=self.weight_fish.luck_option_config.show_impacts), LuckOption(weight=self.weight_junk.weight.get_multiplier(resolver), perceived_value=self.weight_junk.luck_option_config.player_perception, user_data=FishingChoiceCategory.JUNK, show_luck_impacts=self.weight_junk.luck_option_config.show_impacts), LuckOption(weight=self.weight_treasure.weight.get_multiplier(resolver), perceived_value=self.weight_treasure.luck_option_config.player_perception, user_data=FishingChoiceCategory.TREASURE, show_luck_impacts=self.weight_treasure.luck_option_config.show_impacts)]
        result = luck_service.choose_with_luck(self, weighted_outcomes, resolver, luck_config)
        return result

    def choose_any_multiple(self, resolver:'Resolver', luck_config:'Optional[LuckConfig]', count:'int', allow_empty:'bool') -> 'List[FishingChoiceResult]':
        results = []
        while len(results) < count:
            result = self.choose_any(resolver, luck_config)
            if not allow_empty:
                if result.chosen_category != FishingChoiceCategory.NONE:
                    results.append(result)
            results.append(result)
        return results

class TunedFishingData(FishingDataBase, HasTunableSingletonFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'weight_fish': TunableTuple(weight=TunableMultiplier.TunableFactory(description='\n                A tunable list of tests and multipliers to apply to the weight \n                used to determine if the Sim will catch a fish instead of treasure \n                or junk. This will be used in conjunction with the Weight Junk and \n                Weight Treasure.\n                '), luck_option_config=TunableLuckOptionData()), 'weight_junk': TunableTuple(weight=TunableMultiplier.TunableFactory(description='\n                A tunable list of tests and multipliers to apply to the weight\n                used to determine if the Sim will catch junk instead of a fish or \n                treasure. This will be used in conjunction with the Weight Fish and \n                Weight Treasure.\n                '), luck_option_config=TunableLuckOptionData()), 'weight_treasure': TunableTuple(weight=TunableMultiplier.TunableFactory(description='\n                A tunable list of tests and multipliers to apply to the weight\n                used to determine if the Sim will catch a treasure instead of fish \n                or junk. This will be used in conjunction with the Weight Fish and \n                Weight Junk.\n                '), luck_option_config=TunableLuckOptionData()), 'possible_treasures': TunableList(description="\n            If the Sim catches a treasure, we'll pick one of these based on their weights.\n            Higher weighted treasures have a higher chance of being caught.\n            ", tunable=TunableTuple(treasure=TunableReference(manager=services.definition_manager(), pack_safe=True), weight=TunableMultiplier.TunableFactory(), luck_option_config=TunableLuckOptionData())), 'possible_fish': TunableList(description="\n            If the Sim catches a fish, we'll pick one of these based on their weights.\n            Higher weighted fish have a higher chance of being caught.\n            ", tunable=TunableTuple(fish=TunableReference(manager=services.definition_manager(), pack_safe=True), weight=TunableMultiplier.TunableFactory(), luck_option_config=TunableLuckOptionData()))}

    def _verify_tuning_callback(self):
        import fishing.fish_object
        for fish in self.possible_fish:
            if not issubclass(fish.fish.cls, fishing.fish_object.Fish):
                logger.error("Possible Fish on Fishing Data has been tuned but there either isn't a definition tuned for the fish, or the definition currently tuned is not a Fish.\n{}", self)
(TunableFishingDataReference, TunableFishingDataSnippet) = define_snippet('fishing_data', TunedFishingData.TunableFactory())PossibleFish = namedtuple('PossibleFish', 'fish, weight, luck_option_config')
class DynamicFishingData(FishingDataBase):

    def __init__(self, tuned_fishing_data, owner):
        self.possible_fish = [PossibleFish(possible_fish.fish, possible_fish.weight, possible_fish.luck_option_config) for possible_fish in tuned_fishing_data.possible_fish]
        self.weight_fish = tuned_fishing_data.weight_fish
        self.weight_junk = tuned_fishing_data.weight_junk
        self.weight_treasure = tuned_fishing_data.weight_treasure
        self.possible_treasures = tuned_fishing_data.possible_treasures
        self.owner = owner
        self._tuned_fishing_data = tuned_fishing_data

    def _get_fish_catch_multiplier(self, fish):
        weight = fish.cls.catch_multiplier
        for tuned_possible_fish_info in self._tuned_fishing_data.possible_fish:
            if tuned_possible_fish_info.fish is fish:
                weight = tuned_possible_fish_info.weight
                break
        return weight

    def _get_fish_luck_option_config(self, fish:'Fish') -> 'TunableLuckOptionData':
        for tuned_possible_fish_info in self._tuned_fishing_data.possible_fish:
            if tuned_possible_fish_info.fish is fish:
                return tuned_possible_fish_info.luck_option_config
        return fish.cls.luck_option_config

    def add_possible_fish(self, fish_definitions:'List[Fish]', should_sync_pond:'bool'=True) -> 'None':
        for fish in fish_definitions:
            if fish not in [possible_fish.fish for possible_fish in self.possible_fish]:
                self.possible_fish.append(PossibleFish(fish, self._get_fish_catch_multiplier(fish), self._get_fish_luck_option_config(fish)))
        if not should_sync_pond:
            return
        associated_pond_obj = self.owner.fishing_location_component.associated_pond_obj
        if associated_pond_obj is not None:
            associated_pond_obj.update_and_sync_fish_data(fish_definitions, self.owner, is_add=True)

    def remove_possible_fish(self, fish_definitions, should_sync_pond=True):
        self.possible_fish = [fish_info for fish_info in self.possible_fish if fish_info.fish not in fish_definitions]
        if not should_sync_pond:
            return
        associated_pond_obj = self.owner.fishing_location_component.associated_pond_obj
        if associated_pond_obj is not None:
            associated_pond_obj.update_and_sync_fish_data(fish_definitions, self.owner, is_add=False)

    def save(self, msg):
        msg.possible_fish_ids.extend(f.fish.id for f in self.possible_fish)

    def load(self, persistable_data:'FishingData') -> 'None':
        self.possible_fish = []
        for possible_fish_id in persistable_data.possible_fish_ids:
            fish = services.definition_manager().get(possible_fish_id)
            if fish is None:
                pass
            else:
                self.possible_fish.append(PossibleFish(fish, self._get_fish_catch_multiplier(fish), self._get_fish_luck_option_config(fish)))

class FishingBait(HasTunableSingletonFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'bait_name': TunableLocalizedStringFactory(description='\n            Name of fishing bait.\n            '), 'bait_description': TunableLocalizedStringFactory(description='\n            Description of fishing bait.\n            '), 'bait_icon_definition': TunableReference(description='\n            Object definition that will be used to render icon of fishing bait.\n            ', manager=services.definition_manager()), 'bait_buff': TunableReference(description='\n            Buff of fishing bait.\n            ', manager=services.get_instance_manager(sims4.resources.Types.BUFF)), 'bait_priority': TunableRange(description='\n            The priority of the bait. When an object can be categorized into\n            multiple fishing bait categories, the highest priority category \n            will be chosen.\n            ', tunable_type=int, default=1, minimum=1)}
(TunableFishingBaitReference, _) = define_snippet('fishing_bait', FishingBait.TunableFactory())