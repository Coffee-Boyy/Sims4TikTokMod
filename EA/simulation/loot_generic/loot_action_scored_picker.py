from __future__ import annotationsimport randomimport servicesimport sims4from interactions.utils.loot_basic_op import BaseLootOperationfrom sims4.tuning.tunable import TunableList, TunableReference, TunableTuplefrom tunable_multiplier import TestedSumfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.resolver import Resolver
    from interactions.utils.loot import LootActions
    from sims.sim_info import SimInfo
class ScoredLootActionPicker(BaseLootOperation):
    FACTORY_TUNABLES = {'scored_loot_actions_list': TunableList(description='\n            A list of loot actions and their corresponding tested sums that are\n            eligible to be picked based on score. If there is a tie for the highest score,\n            a result will be picked randomly between the tied loot action lists. If no tests pass, \n            then the first set of tuned loot actions will be run.\n            ', tunable=TunableTuple(loot_actions=TunableList(description='\n                    The list of loot actions that will be run if this outcome is selected.\n                    ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',))), tested_score=TestedSum.TunableFactory(description='\n                    The score (calculated by modifiers) this loot action will have based on\n                    the number of tests passed.                \n                    ')))}

    def __init__(self, scored_loot_actions_list:'List[TunableTuple]', **kwargs) -> 'None':
        super().__init__(**kwargs)
        self.scored_loot_actions_list = scored_loot_actions_list

    def get_loot_actions_to_run(self, resolver:'Resolver') -> 'List[LootActions]':
        if not self.scored_loot_actions_list:
            return []
        loot_action_set_to_score = {}
        test_passed = False
        for candidate in self.scored_loot_actions_list:
            modified_score = candidate.tested_score.get_modified_value(resolver)
            if modified_score != candidate.tested_score.base_value:
                test_passed = True
            loot_action_set_to_score[candidate.loot_actions] = modified_score
        if not test_passed:
            return self.scored_loot_actions_list[0].loot_actions
        candidates = [key for (key, value) in loot_action_set_to_score.items() if value == max(loot_action_set_to_score.values())]
        if len(candidates) > 1:
            return random.choice(candidates)
        return candidates[0]

    def _apply_to_subject_and_target(self, subject:'SimInfo', target:'SimInfo', resolver:'Resolver') -> 'None':
        loot_action_set_to_run = self.get_loot_actions_to_run(resolver)
        for loot_action in loot_action_set_to_run:
            loot_action.apply_to_resolver(resolver)
