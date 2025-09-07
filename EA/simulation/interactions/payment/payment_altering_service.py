from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import Optional, Callable, Dict, List, Set
    from event_testing.resolver import InteractionResolver
    from interactions.payment.payment_dest import _PaymentDest
    from interactions.base.interaction import Interaction
    from sims.sim import Sim
    from tag import Tagimport sims4from dataclasses import dataclassfrom sims4.service_manager import Servicelogger = sims4.log.Logger('Payment', default_owner='sersanchez')
@dataclass
class PaymentModifierEntry:
    payment_extra_test = None
    __annotations__['payment_extra_test'] = 'Optional[Callable[[List[_PaymentDest], InteractionResolver, int], bool]]'
    money_loot_test = None
    __annotations__['money_loot_test'] = 'Optional[Callable[[Sim, int, Optional[Interaction], Optional[Set[Tag]]], bool]]'
    crafting_process_test = None
    __annotations__['crafting_process_test'] = 'Optional[Callable[[Sim, Sim], bool]]'
    picker_test = None
    __annotations__['picker_test'] = 'Optional[Callable[[Sim, Sim], bool]]'
    get_modifier_value = None
    __annotations__['get_modifier_value'] = 'Optional[Callable[[], float]]'

class PaymentAlteringService(Service):

    def __init__(self) -> 'None':
        super().__init__()
        self.sim_id_to_payment_modifier_entry_dictionary = {}
        self.default_modifier = 1.0

    def remove_sim_entry(self, sim_id:'int') -> 'None':
        if sim_id in self.sim_id_to_payment_modifier_entry_dictionary:
            entry = self.sim_id_to_payment_modifier_entry_dictionary[sim_id]
            entry.payment_extra_test = None
            entry.money_loot_test = None
            entry.crafting_process_test = None
            entry.picker_test = None
            entry.get_modifier_value = None
            del entry

    def add_sim_entry(self, sim_id:'int', payment_extra_tester:'Optional[Callable[[List[_PaymentDest], InteractionResolver, int], bool]]'=None, money_loot_tester:'Optional[Callable[[Sim, int, Optional[Interaction], Optional[Set[Tag]]], bool]]'=None, crafting_process_tester:'Optional[Callable[[Sim, Sim], bool]]'=None, picker_tester:'Optional[Callable[[Sim, Sim], bool]]'=None, get_modifier_value:'Optional[Callable[[], float]]'=None) -> 'None':
        self.sim_id_to_payment_modifier_entry_dictionary.update({sim_id: PaymentModifierEntry(payment_extra_tester, money_loot_tester, crafting_process_tester, picker_tester, get_modifier_value)})

    def clear_all_entries(self) -> 'None':
        self.sim_id_to_payment_modifier_entry_dictionary.clear()

    def get_payment_extra_modifier(self, sim_id:'int', payment_dest:'List[_PaymentDest]', interaction_resolver:'InteractionResolver', amount:'int') -> 'float':
        payment_modifier_data = self.sim_id_to_payment_modifier_entry_dictionary.get(sim_id)
        if payment_modifier_data is not None and payment_modifier_data.get_modifier_value is not None and (payment_modifier_data.payment_extra_test is None or payment_modifier_data.payment_extra_test(payment_dest, interaction_resolver, amount)):
            return payment_modifier_data.get_modifier_value()
        else:
            return self.default_modifier

    def get_money_loot_modifier(self, sim_id:'int', sim:'Sim', amount:'int', interaction:'Optional[Interaction]', tags:'Optional[Set[Tag]]') -> 'float':
        payment_modifier_data = self.sim_id_to_payment_modifier_entry_dictionary.get(sim_id)
        if payment_modifier_data is not None and payment_modifier_data.get_modifier_value is not None and (payment_modifier_data.money_loot_test is None or payment_modifier_data.money_loot_test(sim, amount, interaction, tags)):
            return payment_modifier_data.get_modifier_value()
        else:
            return self.default_modifier

    def get_crafting_process_modifier(self, sim_id:'int', payer_sim:'Sim', crafting_sim:'Sim') -> 'float':
        payment_modifier_data = self.sim_id_to_payment_modifier_entry_dictionary.get(sim_id)
        if payment_modifier_data is not None and payment_modifier_data.get_modifier_value is not None and (payment_modifier_data.crafting_process_test is None or payment_modifier_data.crafting_process_test(payer_sim, crafting_sim)):
            return payment_modifier_data.get_modifier_value()
        else:
            return self.default_modifier

    def get_picker_payment_modifier(self, sim_id:'int', payer_sim:'Sim', crafting_sim:'Sim') -> 'float':
        payment_modifier_data = self.sim_id_to_payment_modifier_entry_dictionary.get(sim_id)
        if payment_modifier_data is not None and payment_modifier_data.get_modifier_value is not None and (payment_modifier_data.picker_test is None or payment_modifier_data.picker_test(payer_sim, crafting_sim)):
            return payment_modifier_data.get_modifier_value()
        else:
            return self.default_modifier
