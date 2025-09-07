from __future__ import annotationsimport pathsfrom dataclasses import dataclassfrom interactions import ParticipantTypefrom interactions.payment.payment_element import PaymentElementfrom protocolbuffers import Consts_pb2, Business_pb2import servicesimport sims4from business.business_enums import SmallBusinessAttendanceSaleMode, BusinessTypefrom distributor.rollback import ProtocolBufferRollbackfrom event_testing.test_events import TestEventfrom interactions.payment.payment_info import PaymentBusinessRevenueTypefrom sims.funds import get_funds_for_source, FundsSourcefrom small_business.small_business_tuning import SmallBusinessTunablesfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.resolver import DataResolver, InteractionResolver
    from small_business.small_business_manager import SmallBusinessManager
    from interactions.base.interaction import Interaction
    from interactions.payment.payment_dest import _PaymentDest
    from interactions.payment.payment_altering_service import PaymentAlteringService
    from sims.sim import Sim
    from sims.sim_info import SimInfo
    from tag import Taglogger = sims4.log.Logger('SmallBusinessIncomeData', default_owner='sersanchez')
@dataclass
class SingleInteractionIncomeRecord:
    total_amount = 0
    __annotations__['total_amount'] = 'int'
    already_paid_amount = 0
    __annotations__['already_paid_amount'] = 'int'
    payer_sim_id = None
    __annotations__['payer_sim_id'] = 'int'

@dataclass
class SingleRevenueSourceRecord:
    count = 0
    __annotations__['count'] = 'int'
    profit = 0
    __annotations__['profit'] = 'int'

    def add_profit(self, profit:'int'):
        self.count += 1
        self.profit += profit

class SmallBusinessIncomeRecord:

    def __init__(self):
        self.revenue_source_records = {}
        self.customers_visited = 0
        self.aggregate_customers_hours = 0
        self.revenue_source_records[PaymentBusinessRevenueType.SMALL_BUSINESS_ATTENDANCE_HOURLY_FEE] = SingleRevenueSourceRecord()
        self.revenue_source_records[PaymentBusinessRevenueType.SMALL_BUSINESS_ATTENDANCE_ENTRY_FEE] = SingleRevenueSourceRecord()
        self.revenue_source_records[PaymentBusinessRevenueType.SMALL_BUSINESS_INTERACTION_FEE] = SingleRevenueSourceRecord()
        self.revenue_source_records[PaymentBusinessRevenueType.SMALL_BUSINESS_LIGHT_RETAIL_FEE] = SingleRevenueSourceRecord()
        self.revenue_source_records[PaymentBusinessRevenueType.SMALL_BUSINESS_OPENING_FEE] = SingleRevenueSourceRecord()
        self.revenue_source_records[PaymentBusinessRevenueType.EMPLOYEE_WAGES] = SingleRevenueSourceRecord()
        self.revenue_source_records[PaymentBusinessRevenueType.SMALL_BUSINESS_TIP_JAR_FEE] = SingleRevenueSourceRecord()

    def save_data(self, small_business_income_record_data) -> 'None':
        small_business_income_record_data.customers_visited = self.customers_visited
        small_business_income_record_data.aggregate_customers_hours = self.aggregate_customers_hours
        for (revenue_type, revenue_source_record) in self.revenue_source_records.items():
            with ProtocolBufferRollback(small_business_income_record_data.records_by_revenue) as record_by_revenue:
                record_by_revenue.revenue_type = revenue_type
                record_by_revenue.count = revenue_source_record.count
                record_by_revenue.profit = revenue_source_record.profit

    def load_data(self, small_business_income_record_data) -> 'None':
        self.customers_visited = small_business_income_record_data.customers_visited
        self.aggregate_customers_hours = small_business_income_record_data.aggregate_customers_hours
        for record_by_revenue in small_business_income_record_data.records_by_revenue:
            record = SingleRevenueSourceRecord(count=record_by_revenue.count, profit=record_by_revenue.profit)
            self.revenue_source_records[PaymentBusinessRevenueType(record_by_revenue.revenue_type)] = record

class SmallBusinessIncomeData:

    def __init__(self, small_business_manager:'SmallBusinessManager') -> 'None':
        self._small_business_manager = small_business_manager
        self._current_day_business_income_record = SmallBusinessIncomeRecord()
        self._total_business_income_record = SmallBusinessIncomeRecord()
        self._attendance_sale_mode = SmallBusinessAttendanceSaleMode.DISABLED
        self._is_light_retail_enabled = True
        self._supported_interactionless_money_loot_tags = SmallBusinessTunables.SUPPORTED_INTERACTIONLESS_MONEY_LOOT_TAGS
        self._current_day_ongoing_interactions = {}

    @property
    def attendance_sale_mode(self) -> 'SmallBusinessAttendanceSaleMode':
        return self._attendance_sale_mode

    @property
    def is_light_retail_enabled(self) -> 'bool':
        return self._is_light_retail_enabled

    @property
    def total_business_income_record(self) -> 'SmallBusinessIncomeRecord':
        return self._total_business_income_record

    @property
    def current_day_business_income_record(self) -> 'SmallBusinessIncomeRecord':
        return self._current_day_business_income_record

    def start_payment_handling(self) -> 'None':
        services.get_event_manager().register(self, (TestEvent.PaymentDone, TestEvent.MoneyLoot, TestEvent.CraftPayment, TestEvent.PaymentDoneToVoid, TestEvent.InteractionComplete))
        if paths.AUTOMATION_MODE:
            services.get_event_manager().register(self, (TestEvent.InteractionStart, TestEvent.InteractionUpdate))

    def stop_payment_handling(self) -> 'None':
        services.get_event_manager().unregister(self, (TestEvent.PaymentDone, TestEvent.MoneyLoot, TestEvent.CraftPayment, TestEvent.PaymentDoneToVoid, TestEvent.InteractionComplete))
        if paths.AUTOMATION_MODE:
            services.get_event_manager().unregister(self, (TestEvent.InteractionStart, TestEvent.InteractionUpdate))

    def start_interaction_sales_markup_tracking_for_sim(self, sim_id:'int') -> 'None':
        payment_altering_service = services.payment_altering_service()
        if payment_altering_service is not None:
            payment_altering_service.add_sim_entry(sim_id, self.should_apply_markup_for_payment_extra, self.should_apply_markup_for_money_loot, self.should_apply_markup_for_crafting_process, self.should_apply_markup_for_crafting_process, self.get_markup_multiplier)

    def stop_interaction_sales_markup_tracking_for_sim(self, sim_id:'int') -> 'None':
        payment_altering_service = services.payment_altering_service()
        if payment_altering_service is not None:
            payment_altering_service.remove_sim_entry(sim_id)

    def handle_event(self, sim_info, event:'TestEvent', resolver:'DataResolver') -> 'None':
        if event == TestEvent.PaymentDone or event == TestEvent.PaymentDoneToVoid:
            self.on_payment_done_event(resolver)
        elif event == TestEvent.MoneyLoot:
            self.on_money_loot_event(resolver)
        elif event == TestEvent.CraftPayment:
            self.on_craft_payment_event(resolver)
        elif event == TestEvent.InteractionComplete:
            self.on_interaction_complete_event(resolver)
        elif event == TestEvent.InteractionStart or event == TestEvent.InteractionUpdate:
            self.on_interaction_update_event(resolver)

    def on_interaction_update_event(self, resolver:'DataResolver') -> 'None':
        if paths.AUTOMATION_MODE:
            if resolver is None or resolver.interaction is None:
                return
            interaction = resolver.interaction
            if interaction.is_super and interaction.basic_extras is not None and any(extra.factory is PaymentElement for extra in interaction.basic_extras):
                connection = services.client_manager().get_first_client_id()
                if connection is None:
                    return
                if interaction.started:
                    sims4.commands.automation_output('InteractionSale; Status:Update, InteractionId:{}, SimId:{}'.format(interaction.id, interaction.sim.sim_id), connection)
                else:
                    sims4.commands.automation_output('InteractionSale; Status:Start, InteractionId:{}, SimId:{}'.format(interaction.id, interaction.sim.sim_id), connection)

    def on_payment_done_event(self, resolver:'DataResolver') -> 'None':
        if resolver.event_kwargs is not None and 'resolver' in resolver.event_kwargs and 'payment_info' in resolver.event_kwargs:
            payment_info = resolver.event_kwargs['payment_info']
            payment_resolver = resolver.event_kwargs['resolver']
            payment_destination = None
            if 'dest' in resolver.event_kwargs:
                payment_destination = resolver.event_kwargs['dest']
            amount = abs(payment_info.amount)
            if payment_info.revenue_type != PaymentBusinessRevenueType.INVALID:
                revenue_type = payment_info.revenue_type
            else:
                revenue_type = PaymentBusinessRevenueType.SMALL_BUSINESS_INTERACTION_FEE
            payer_sim = payment_resolver.get_participant(ParticipantType.Actor)
            if revenue_type == PaymentBusinessRevenueType.SMALL_BUSINESS_INTERACTION_FEE:
                payment_target = payment_resolver.get_participant(ParticipantType.TargetSim)
                owner_household_id = self._small_business_manager.owner_household_id
                if payment_destination is not None:
                    (should_handle_interaction_sale, already_paid_to_owner) = payment_destination.should_handle_interaction_sale_info(self._small_business_manager, payment_resolver)
                else:
                    should_handle_interaction_sale = True
                    already_paid_to_owner = False if payment_info.amount > 0 else owner_household_id == payer_sim.household_id
                if should_handle_interaction_sale:
                    if payment_target.is_sim:
                        payer_sim = payment_target
                    self.handle_interaction_sale(payer_sim, amount, payment_resolver.interaction, already_paid_to_owner=already_paid_to_owner, allow_instant_register=payment_resolver.interaction is None)
            else:
                self.register_payment(amount, revenue_type, payer_sim_id=payer_sim.sim_id)
                if self.is_attendance_revenue_type(revenue_type) or revenue_type == PaymentBusinessRevenueType.SMALL_BUSINESS_LIGHT_RETAIL_FEE:
                    self.attempt_apply_tip_value(amount)
            if paths.AUTOMATION_MODE:
                if payment_resolver is None or payment_resolver.interaction is None:
                    return
                connection = services.client_manager().get_first_client_id()
                if connection is None:
                    return
                sims4.commands.automation_output('InteractionSale; Status:PaymentDone, InteractionId:{}, SimId:{}'.format(payment_resolver.interaction.id, payment_resolver.interaction.sim.sim_id), connection)

    def on_money_loot_event(self, resolver:'DataResolver') -> 'None':
        if resolver.event_kwargs is not None and ('subject' in resolver.event_kwargs and ('interaction' in resolver.event_kwargs and 'amount' in resolver.event_kwargs)) and 'tags' in resolver.event_kwargs:
            payment_subject = resolver.event_kwargs['subject']
            interaction = resolver.event_kwargs['interaction']
            amount = resolver.event_kwargs['amount']
            tags = resolver.event_kwargs['tags']
            allow_instant_register = False
            if len(tags.intersection(self._supported_interactionless_money_loot_tags)) > 0:
                allow_instant_register = True
            if interaction is None and tags is not None and amount > 0:
                self.handle_interaction_gain(payment_subject, amount, interaction, allow_instant_register=allow_instant_register)
            elif amount < 0:
                self.handle_interaction_sale(payment_subject, amount, interaction, allow_instant_register=allow_instant_register)
            if paths.AUTOMATION_MODE:
                connection = services.client_manager().get_first_client_id()
                if connection is None or interaction is None:
                    return
                sims4.commands.automation_output('InteractionSale; Status:MoneyLoot, InteractionId:{}, SimId:{}'.format(interaction.id, interaction.sim.sim_id), connection)

    def on_craft_payment_event(self, resolver:'DataResolver') -> 'None':
        if resolver.event_kwargs is not None and ('paying_sim' in resolver.event_kwargs and ('cost' in resolver.event_kwargs and 'crafter_sim' in resolver.event_kwargs)) and 'crafting_interaction' in resolver.event_kwargs:
            paying_sim = resolver.event_kwargs['paying_sim']
            cost = resolver.event_kwargs['cost']
            crafter_sim = resolver.event_kwargs['crafter_sim']
            crafting_interaction = resolver.event_kwargs['crafting_interaction']
            if crafter_sim != paying_sim:
                owner_household_id = self._small_business_manager.owner_household_id
                if paying_sim.household_id == owner_household_id:
                    return
                is_crafter_an_employee = self.is_sim_an_employee(crafter_sim.sim_info)
                if crafter_sim.household_id != owner_household_id and not is_crafter_an_employee:
                    return
                self.handle_interaction_sale(paying_sim, cost, crafting_interaction, allow_instant_register=crafting_interaction is None)
                if paths.AUTOMATION_MODE:
                    connection = services.client_manager().get_first_client_id()
                    if connection is None or crafting_interaction is None:
                        return
                    sims4.commands.automation_output('InteractionSale; Status:CraftPayment, InteractionId:{}, SimId:{}'.format(crafting_interaction.id, crafting_interaction.sim.sim_id), connection)

    def should_apply_markup_for_payment_extra(self, payment_destinations:'List[_PaymentDest]', payment_resolver:'InteractionResolver', amount:'int') -> 'bool':
        if payment_resolver is None:
            return False
        if payment_destinations == () or payment_destinations[0].should_handle_interaction_sale_info(self._small_business_manager, payment_resolver)[0]:
            payment_subject = payment_resolver.get_participant(ParticipantType.Actor)
            if payment_subject is None:
                return False
            if self.is_sim_an_employee(payment_subject) or self._small_business_manager.owner_household_id == payment_subject.household_id:
                payment_target = payment_resolver.get_participant(ParticipantType.TargetSim)
                if payment_target.is_sim:
                    payment_subject = payment_target
                    amount = abs(amount)
            if amount > 0:
                return self._should_apply_markup_for_sale(payment_subject)
            elif amount < 0:
                interaction = None
                if hasattr(payment_resolver, 'interaction'):
                    interaction = payment_resolver.interaction
                if hasattr(payment_resolver, 'affordance'):
                    interaction = payment_resolver.affordance
                return self._should_apply_markup_for_gain(payment_subject, interaction)
        return False

    def should_apply_markup_for_money_loot(self, payment_subject:'Sim', amount:'int', interaction:'Optional[Interaction]', tags:'Optional[Set[Tag]]') -> 'bool':
        if amount < 0:
            return self._should_apply_markup_for_sale(payment_subject)
        elif amount > 0:
            return self._should_apply_markup_for_gain(payment_subject, interaction, tags)
        else:
            return False
        return False

    def should_apply_markup_for_crafting_process(self, paying_sim:'Sim', crafter_sim:'Sim') -> 'bool':
        if paying_sim is None or crafter_sim is None or crafter_sim == paying_sim:
            return False
        owner_household_id = self._small_business_manager.owner_household_id
        if paying_sim.household_id == owner_household_id:
            return False
        if crafter_sim.household_id != owner_household_id and not self.is_sim_an_employee(crafter_sim.sim_info):
            return False
        return self._should_apply_markup_for_sale(paying_sim)

    def _should_apply_markup_for_sale(self, payer_sim:'Sim') -> 'bool':
        owner_household_id = self._small_business_manager.owner_household_id
        if payer_sim is None:
            return False
        elif owner_household_id != payer_sim.household_id and self.is_sim_checked_in(payer_sim):
            return True
        return False

    def _should_apply_markup_for_gain(self, target_sim:'Sim', interaction:'Optional[Interaction]', tags:'Optional[Set[Tag]]'=None) -> 'bool':
        if target_sim is None:
            return False
        else:
            owner_household_id = services.sim_info_manager().get(self._small_business_manager.owner_sim_id).household_id
            target_household_id = target_sim.household_id
            if interaction is None:
                if tags is not None and len(tags.intersection(self._supported_interactionless_money_loot_tags)) > 0:
                    return owner_household_id == target_household_id or self.is_sim_an_employee(target_sim.sim_info)
                return False
        return False
        if owner_household_id == target_household_id:
            return True
        elif self.is_sim_an_employee(target_sim.sim_info):
            if interaction.sim and interaction.sim is not property and interaction.sim.household_id == owner_household_id:
                return False
            else:
                return True
        return True
        return False

    def on_interaction_complete_event(self, resolver:'DataResolver') -> 'None':
        if resolver.interaction is not None:
            self.apply_pending_interaction_payment(resolver.interaction.aop_id)
            if paths.AUTOMATION_MODE:
                interaction = resolver.interaction
                connection = services.client_manager().get_first_client_id()
                if connection is None or interaction.basic_extras is None:
                    return
                if any(extra.factory is PaymentElement for extra in interaction.basic_extras):
                    sims4.commands.automation_output('InteractionSale; Status:Complete, InteractionId:{}, SimId:{}'.format(interaction.id, interaction.sim.sim_id), connection)

    def is_sim_checked_in(self, sim_to_check:'Union[Sim, SimInfo]') -> 'bool':
        sim = sim_to_check.sim_info.get_sim_instance()
        sim_situations = services.get_zone_situation_manager().get_situations_sim_is_in(sim)
        if not sim_situations:
            return False
        for situation in sim_situations:
            role_tags = situation.get_role_tags_for_sim(sim)
            if role_tags is not None and SmallBusinessTunables.SMALL_BUSINESS_VISIT_ROLE_TAG in role_tags:
                return True
        return False

    def is_sim_an_employee(self, sim_to_check:'Union[Sim, SimInfo]') -> 'bool':
        if self._small_business_manager.is_employee(sim_to_check.sim_info):
            return True
        sim = sim_to_check.sim_info.get_sim_instance()
        sim_situations = services.get_zone_situation_manager().get_situations_sim_is_in(sim)
        if not sim_situations:
            return False
        for situation in sim_situations:
            role_tags = situation.get_role_tags_for_sim(sim)
            if role_tags is not None and len(role_tags.intersection(SmallBusinessTunables.HIRED_TEMPORARY_EMPLOYEES_SITUATION_TAGS)) > 0:
                return True
        return False

    def handle_interaction_gain(self, target_sim, amount:'int', interaction:'Interaction', allow_instant_register:'bool'=False) -> 'None':
        if target_sim is None:
            return
        target_household_id = target_sim.household_id
        owner_sim_info = services.sim_info_manager().get(self._small_business_manager.owner_sim_id)
        owner_household_id = owner_sim_info.household_id
        if allow_instant_register:
            if owner_household_id == target_household_id:
                self.apply_interaction_payment(amount, already_paid_amount=amount, payer_sim_id=target_sim.sim_info.id)
            elif self.is_sim_an_employee(target_sim.sim_info):
                self.apply_interaction_payment(amount, already_paid_amount=0, payer_sim_id=target_sim.sim_info.id)
        else:
            if interaction is None:
                return
            aop_id = None
            if interaction.super_interaction is not None:
                aop_id = interaction.super_interaction.aop_id
            if aop_id is not None:
                if owner_household_id == target_household_id:
                    self.group_interaction_payments(aop_id, amount, amount)
                elif self.is_sim_an_employee(target_sim.sim_info):
                    if interaction.sim and interaction.sim.household_id == owner_household_id:
                        return
                    self.group_interaction_payments(aop_id, amount, 0)

    def handle_interaction_sale(self, payer_sim, amount:'int', interaction:'Interaction', already_paid_to_owner:'bool'=False, allow_instant_register:'bool'=False) -> 'None':
        if payer_sim is None:
            return
        payer_household_id = payer_sim.household_id
        owner_household_id = self._small_business_manager.owner_household_id
        if allow_instant_register:
            already_paid_amount = amount if already_paid_to_owner else 0
            self.apply_interaction_payment(amount, already_paid_amount=already_paid_amount, payer_sim_id=payer_sim.sim_info.id)
        else:
            if interaction is None:
                return
            aop_id = None
            if interaction.super_interaction is not None:
                aop_id = interaction.super_interaction.aop_id
            if aop_id is not None:
                if owner_household_id == payer_household_id and payer_sim.sim_id == self._small_business_manager.owner_sim_id:
                    self.group_interaction_payments(aop_id, amount, amount, payer_sim.sim_id)
                elif self.is_sim_checked_in(payer_sim):
                    already_paid_amount = amount if already_paid_to_owner else 0
                    self.group_interaction_payments(aop_id, amount, already_paid_amount, payer_sim.sim_id)
                elif self.is_sim_an_employee(payer_sim) and already_paid_to_owner:
                    self.apply_interaction_payment(amount, already_paid_amount=amount, payer_sim_id=payer_sim.sim_info.id)

    def group_interaction_payments(self, aop_id:'int', amount:'int', already_paid_amount:'int'=0, payer_sim_id:'int'=None) -> 'None':
        if aop_id in self._current_day_ongoing_interactions:
            self._current_day_ongoing_interactions[aop_id].total_amount += amount
            self._current_day_ongoing_interactions[aop_id].already_paid_amount += already_paid_amount
            if self._current_day_ongoing_interactions[aop_id].payer_sim_id is None:
                self._current_day_ongoing_interactions[aop_id].payer_sim_id = payer_sim_id
        else:
            self._current_day_ongoing_interactions[aop_id] = SingleInteractionIncomeRecord(total_amount=amount, already_paid_amount=already_paid_amount, payer_sim_id=payer_sim_id)

    def apply_interaction_payment(self, total_amount:'int', already_paid_amount:'int'=0, payer_sim_id:'int'=None):
        owner_sim_info = services.sim_info_manager().get(self._small_business_manager.owner_sim_id)
        owner_funds = get_funds_for_source(FundsSource.HOUSEHOLD, sim=owner_sim_info)
        funds_to_add = abs(total_amount - already_paid_amount)
        funds_to_add += self.get_tip_value(total_amount)
        owner_funds.add(funds_to_add, reason=Consts_pb2.FUNDS_SMALL_BUSINESS_INTERACTION_REWARD)
        self.register_payment(int(total_amount), PaymentBusinessRevenueType.SMALL_BUSINESS_INTERACTION_FEE, payer_sim_id)

    def apply_pending_interaction_payment(self, aop_id:'int') -> 'None':
        if aop_id in self._current_day_ongoing_interactions:
            interaction_payment_info = self._current_day_ongoing_interactions[aop_id]
            self.apply_interaction_payment(interaction_payment_info.total_amount, interaction_payment_info.already_paid_amount, interaction_payment_info.payer_sim_id)
            self._current_day_ongoing_interactions.pop(aop_id)
            if self._small_business_manager.is_customer_appreciation_day_perk_active():
                active_household = services.active_household()
                if active_household is not None:
                    active_household.funds.send_money_update(vfx_amount=0, reason=self._small_business_manager.get_customer_appreciation_day_reason())

    def apply_all_pending_interaction_payments(self) -> 'None':
        stored_aop_ids = list(self._current_day_ongoing_interactions)
        for aop_id in stored_aop_ids:
            self.apply_pending_interaction_payment(aop_id)

    def register_payment(self, amount:'int', revenue_type:'PaymentBusinessRevenueType', payer_sim_id:'int'=None) -> 'None':
        if not self.is_expense_type(revenue_type):
            owner_sim_info = services.sim_info_manager().get(self._small_business_manager.owner_sim_id)
            services.get_event_manager().process_event(TestEvent.SmallBusinessPaymentRegistered, sim_info=owner_sim_info, markup=self.get_markup_multiplier(), payer_sim_id=payer_sim_id, amount=amount, revenue_type=revenue_type)
            if self.get_total_revenue() == 0 and amount > 0:
                services.get_event_manager().process_event(TestEvent.BusinessFirstSimoleonEarned, sim_info=owner_sim_info, event_business_type=BusinessType.SMALL_BUSINESS)
        self._current_day_business_income_record.revenue_source_records[revenue_type].add_profit(amount)
        self._total_business_income_record.revenue_source_records[revenue_type].add_profit(amount)

    def is_expense_type(self, revenue_type:'PaymentBusinessRevenueType') -> 'bool':
        return revenue_type == PaymentBusinessRevenueType.SMALL_BUSINESS_OPENING_FEE or revenue_type == PaymentBusinessRevenueType.EMPLOYEE_WAGES

    def is_attendance_revenue_type(self, revenue_type:'PaymentBusinessRevenueType') -> 'bool':
        return revenue_type == PaymentBusinessRevenueType.SMALL_BUSINESS_ATTENDANCE_HOURLY_FEE or revenue_type == PaymentBusinessRevenueType.SMALL_BUSINESS_ATTENDANCE_ENTRY_FEE

    def clear_current_day_income(self) -> 'None':
        self._current_day_business_income_record = SmallBusinessIncomeRecord()

    def get_markup_multiplier(self) -> 'float':
        if self._small_business_manager.is_customer_appreciation_day_perk_active():
            return 0
        return self._small_business_manager.markup_multiplier

    def get_hourly_fee(self) -> 'int':
        rank_level = self._small_business_manager.get_business_rank_level()
        hourly_fee = 0
        if rank_level < len(SmallBusinessTunables.BUSINESS_RANK_HOURLY_BASELINES):
            hourly_fee = SmallBusinessTunables.BUSINESS_RANK_HOURLY_BASELINES[rank_level]*self.get_markup_multiplier()
        return int(hourly_fee)

    def get_entry_fee(self) -> 'int':
        rank_level = self._small_business_manager.get_business_rank_level()
        entry_fee = 0
        if rank_level < len(SmallBusinessTunables.BUSINESS_RANK_HOURLY_BASELINES):
            entry_fee = SmallBusinessTunables.BUSINESS_RANK_ENTRY_BASELINES[rank_level]*self.get_markup_multiplier()
        return int(entry_fee)

    def compute_retail_markup_fee(self, value:'int') -> 'int':
        return int(value*self.get_markup_multiplier() - value)

    def get_satisfaction_rate_for_markup(self, markup:'float') -> 'float':
        if markup in SmallBusinessTunables.MARKUP_AND_SATISFACTION_MAPPING:
            return SmallBusinessTunables.MARKUP_AND_SATISFACTION_MAPPING[markup]
        else:
            logger.error('Tried getting the satisfaction rate for a invalid markup [{}]. Valid markup multipliers are: {}.', markup, SmallBusinessTunables.MARKUP_AND_SATISFACTION_MAPPING.keys())
            return 1

    def get_current_satisfaction_rate(self) -> 'float':
        return self.get_satisfaction_rate_for_markup(self.get_markup_multiplier())

    def set_markup_multiplier(self, markup:'float') -> 'None':
        self._small_business_manager.set_markup_multiplier(markup)
        if self._small_business_manager.is_open:
            services.get_event_manager().process_event(TestEvent.BusinessDataUpdated)

    def get_tip_value(self, total_amount:'int') -> 'Optional[int]':
        tip_value = 0
        owner_sim_info = services.sim_info_manager().get(self._small_business_manager.owner_sim_id)
        if owner_sim_info.household.is_active_household:
            tip_jar_settings = SmallBusinessTunables.PERK_SETTINGS.tip_jar
            bucks_tracker = self._small_business_manager.get_bucks_tracker()
            if bucks_tracker is not None:
                for tip_type in tip_jar_settings.tip_types:
                    if bucks_tracker.is_perk_unlocked_and_unfrozen(tip_type.perk):
                        tip_value = int(total_amount*tip_type.tip_percent) if total_amount > 0 else tip_jar_settings.default_tip
                        break
        return tip_value

    def attempt_apply_tip_value(self, total_amount:'int') -> 'Optional[int]':
        tip_value = self.get_tip_value(total_amount)
        if tip_value is not None and tip_value > 0:
            owner_sim_info = services.sim_info_manager().get(self._small_business_manager.owner_sim_id)
            if owner_sim_info is not None:
                owner_funds = get_funds_for_source(FundsSource.HOUSEHOLD, sim=owner_sim_info)
                if owner_funds is not None:
                    owner_funds.add(tip_value, reason=Consts_pb2.FUNDS_SMALL_BUSINESS_INTERACTION_REWARD)
                    self.register_payment(tip_value, PaymentBusinessRevenueType.SMALL_BUSINESS_TIP_JAR_FEE)
        return tip_value

    def set_attendance_sales_mode(self, mode:'SmallBusinessAttendanceSaleMode', send_data_to_client:'bool'=True) -> 'None':
        self._attendance_sale_mode = mode
        if send_data_to_client:
            self._small_business_manager.send_data_to_client()

    def set_light_retail_sales_enabled(self, enabled:'bool') -> 'None':
        self._is_light_retail_enabled = enabled

    def get_total_revenue(self) -> 'int':
        revenue = sum(revenue_source_record.profit for (revenue_type, revenue_source_record) in self._total_business_income_record.revenue_source_records.items() if not self.is_expense_type(revenue_type))
        return revenue

    def save_data(self, small_business_income_data):
        small_business_income_data.current_day_business_income_record = Business_pb2.SmallBusinessIncomeRecord()
        small_business_income_data.total_business_income_record = Business_pb2.SmallBusinessIncomeRecord()
        self._current_day_business_income_record.save_data(small_business_income_data.current_day_business_income_record)
        self._total_business_income_record.save_data(small_business_income_data.total_business_income_record)
        small_business_income_data.attendance_sale_mode_enum = self._attendance_sale_mode
        small_business_income_data.is_light_retail_enabled = self._is_light_retail_enabled

    def load_data(self, small_business_income_data):
        self._current_day_business_income_record.load_data(small_business_income_data.current_day_business_income_record)
        self._total_business_income_record.load_data(small_business_income_data.total_business_income_record)
        self._attendance_sale_mode = small_business_income_data.attendance_sale_mode_enum
        self._is_light_retail_enabled = small_business_income_data.is_light_retail_enabled
