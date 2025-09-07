from __future__ import annotationsimport dataclassesfrom dataclasses import dataclassfrom distributor.shared_messages import IconInfoDatafrom event_testing.test_events import TestEventfrom indexed_manager import CallbackTypesfrom objects.components.types import STORED_SIM_INFO_COMPONENT, BRANDING_ICON_COMPONENTfrom sims.sim_info import SimInfofrom tag import Tagfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from interactions.utils.loot import LootActionsimport sims4from default_property_stream_reader import DefaultPropertyStreamReaderfrom event_testing.resolver import SingleActorAndObjectResolver, SingleSimResolverfrom objects.game_object import GameObjectfrom sims4.localization import LocalizationHelperTuning, TunableLocalizedStringFactoryfrom sims4.tuning.instances import lock_instance_tunablesfrom sims4.tuning.tunable import TunableInterval, TunableSimMinute, TunableTuple, TunableList, TunableReference, HasTunableSingletonFactory, AutoFactoryInit, OptionalTunable, TunableSet, TunableEnumEntryfrom sims4.tuning.tunable_base import GroupNamesfrom situations.situation_complex import SituationComplexCommon, CommonSituationState, SituationStateDatafrom situations.situation_types import SituationCreationUIOptionimport servicesfrom ui.ui_dialog_notification import UiDialogNotificationCUSTOMER_SITUATIONS_TOKEN = 'customer_situation_ids'SITUATION_ALARM = 'situation_alarm'SALES_TOKEN = 'yard_sale_sales'INITIATING_SELLING_PLATFORM_ID = 'initiating_sellling_platform_id'
class ManageCustomersState(CommonSituationState):
    FACTORY_TUNABLES = {'time_between_customer_checks': TunableSimMinute(description='\n            Time in Sim minutes between situation checks to see if we need to add\n            more Sims to be customers.\n            ', default=10)}

    def __init__(self, *args, time_between_customer_checks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_between_customer_checks = time_between_customer_checks

    def on_activate(self, reader=None):
        super().on_activate(reader)
        self.number_of_situations = self.owner.number_of_expected_customers.random_int()
        self._create_or_load_alarm(SITUATION_ALARM, self.time_between_customer_checks, lambda _: self._check_customers(), repeating=True, should_persist=False, reader=reader)

    def _check_customers(self):
        customer_situations = self.owner.get_customer_situations()
        if len(customer_situations) < self.number_of_situations:
            num_to_create = self.number_of_situations - len(customer_situations)
            num_to_create = min(num_to_create, 2)
            for _ in range(num_to_create):
                self.owner.create_customer_situation()

@dataclass
class SaleResultInfo:
    quantity = 0
    __annotations__['quantity'] = 'int'
    simoleons_earned = 0
    __annotations__['simoleons_earned'] = 'int'
    recipe_id = 0
    __annotations__['recipe_id'] = 'int'

    def increase_value(self, quantity:'int', simoleons_earned:'int'):
        self.quantity = self.quantity + quantity
        self.simoleons_earned = self.simoleons_earned + simoleons_earned

class YardSaleEndDialogNotification(HasTunableSingletonFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'notification': UiDialogNotification.TunableFactory(description='\n            The notification displayed when the sale ends.\n            ', locked_args={'text': None}), 'notification_header': TunableLocalizedStringFactory(description='\n            Header text when the business name is set.\n            {0.String} {1.Money)\n            '), 'notification_header_default': TunableLocalizedStringFactory(description='\n            Header text when the business name is not set\n            {0.Money}\n            '), 'notification_line': TunableLocalizedStringFactory(description='\n                The localized string for a sale lane.\n                {0.Number} {1.String} {2.Money}\n        ')}

class YardSaleSituation(SituationComplexCommon):
    INSTANCE_TUNABLES = {'user_job': TunableTuple(description='\n            The job and role which the Sim is placed into.\n            ', situation_job=TunableReference(description='\n                A reference to a SituationJob that can be performed at this Situation.\n                ', manager=services.get_instance_manager(sims4.resources.Types.SITUATION_JOB), class_restrictions=('SituationJob',)), role_state=TunableReference(description='\n                A role state the sim assigned to the job will perform.\n                ', manager=services.get_instance_manager(sims4.resources.Types.ROLE_STATE), class_restrictions=('RoleState',))), 'manage_customers_state': ManageCustomersState.TunableFactory(tuning_group=SituationComplexCommon.SITUATION_STATE_GROUP), 'customer_situation': TunableReference(description='\n            Customer Situation to spawn that will pull customers to purchase\n            items from the craft sales table.\n            ', manager=services.get_instance_manager(sims4.resources.Types.SITUATION), class_restrictions=('YardSaleCustomerSituation',)), 'number_of_expected_customers': TunableInterval(description='\n            The number of customers we expect to have at any given time the\n            yard sale is running. The yard sale will attempt to manage this\n            many customer situations at any given time.\n            ', tunable_type=int, default_lower=0, default_upper=10, minimum=0, maximum=10), 'tending_sim_on_sell_rewards': OptionalTunable(tunable=TunableTuple(description='\n               Tunable with list of loot operations that will be awarded to the tending sim when an object has been sold and interaction to be checked to get the tending sim\n               ', on_sell_loot_actions=TunableList(description='\n                   List of loots operations that will be awarded to the tending sim when an object has been sold.\n                   ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',))), tend_interactions=TunableList(description='\n                   Interactions to be checked on the parent object when an object has been sold to get the tending sim\n                   ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.INTERACTION), allow_none=True))), tuning_group=GroupNames.REWARDS), 'initiating_sim_on_sell_rewards': OptionalTunable(description='\n           List of loots operations that will be awarded to the initiating sim when the situation starts.\n           ', tunable=TunableList(tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',))), tuning_group=GroupNames.REWARDS), 'end_sale_dialog_notification': OptionalTunable(description='\n            If enabled, end sale dialog notification configuration\n            ', tunable=YardSaleEndDialogNotification.TunableFactory()), 'initiating_sim_on_start_rewards': OptionalTunable(description='\n           List of loots operations that will be awarded to the initiating sim when an object has been sold.\n           ', tunable=TunableList(tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',))), tuning_group=GroupNames.REWARDS), 'purchase_interaction_tags': OptionalTunable(description='\n            Tags to filter payments\n            ', tunable=TunableSet(description='\n                This attribute is used to test for affordances that contain any of the tags in this set.\n                ', tunable=TunableEnumEntry(description='\n                    These tag values are used for testing interactions.\n                    ', tunable_type=Tag, default=Tag.INVALID))), 'initiating_sim_on_end_naturally_rewards': OptionalTunable(description='\n           List of loots operations that will be awarded to the initiating sim when the sale has ended naturally.\n           ', tunable=TunableList(tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',))), tuning_group=GroupNames.REWARDS), 'initiating_sim_on_end_rewards': OptionalTunable(description='\n           List of loots operations that will be awarded to the initiating sim when the sale has ended, regardless of why\n           it ended\n           ', tunable=TunableList(tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',))), tuning_group=GroupNames.REWARDS)}

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.scoring_enabled = False
        reader = self._seed.custom_init_params_reader
        self.customer_situations = []
        self.sales = {}
        self._initiating_selling_platform_id = None
        self._initiating_selling_platform_name = None
        self._initiating_selling_platform_icon = None
        if reader is not None:
            self.customer_situations = list(reader.read_uint32s(CUSTOMER_SITUATIONS_TOKEN, list()))
            self._parse_saved_sales(reader)
            self._parse_initiating_platform_id(reader)
        elif 'resolver' in self._seed.extra_kwargs:
            self._initiating_selling_platform_id = self._seed.extra_kwargs['resolver'].target.id
        (self._initiating_selling_platform_name, self._initiating_selling_platform_icon) = self._get_initiating_platform_selling_data()
        if self.purchase_interaction_tags is not None:
            services.get_event_manager().register(self, (TestEvent.PaymentDone,))
        object_manager = services.object_manager()
        object_manager.register_callback(CallbackTypes.ON_OBJECT_REMOVE, self._on_object_removed)

    def _destroy(self):
        object_manager = services.object_manager()
        object_manager.unregister_callback(CallbackTypes.ON_OBJECT_REMOVE, self._on_object_removed)
        super()._destroy()

    def _get_initiating_platform_selling_data(self):
        platform_name = self._initiating_selling_platform_name
        platform_icon = self._initiating_selling_platform_icon
        if self._initiating_selling_platform_id is not None:
            initiating_selling_platform = services.object_manager().get(self._initiating_selling_platform_id)
            if initiating_selling_platform.has_custom_name():
                platform_name = LocalizationHelperTuning.get_object_name(initiating_selling_platform)
            branding_icon_component = initiating_selling_platform.get_component(BRANDING_ICON_COMPONENT) if initiating_selling_platform is not None and initiating_selling_platform is not None else None
            if branding_icon_component.has_icon():
                platform_icon = branding_icon_component.get_icon()
        return (platform_name, platform_icon)

    def _parse_initiating_platform_id(self, reader):
        if reader is not None:
            self._initiating_selling_platform_id = reader.read_uint64(INITIATING_SELLING_PLATFORM_ID, None)

    def _parse_saved_sales(self, reader:'DefaultPropertyStreamReader'):
        sales_list = list(reader.read_uint64s(SALES_TOKEN, list()))
        fields = dataclasses.fields(SaleResultInfo())
        for i in range(0, len(sales_list), len(fields) + 1):
            sale = SaleResultInfo(quantity=sales_list[i + 1], simoleons_earned=sales_list[i + 2], recipe_id=sales_list[i + 3])
            self.sales[sales_list[i]] = sale

    def _save_custom_situation(self, writer):
        writer.write_uint32s(CUSTOMER_SITUATIONS_TOKEN, self.customer_situations)
        if self._initiating_selling_platform_id is not None:
            writer.write_uint64(INITIATING_SELLING_PLATFORM_ID, self._initiating_selling_platform_id)
        if self.sales:
            values = []
            for (object_id, sale) in self.sales.items():
                values.append(object_id)
                values.append(sale.quantity)
                values.append(sale.simoleons_earned)
                values.append(sale.recipe_id)
            writer.write_uint64s(SALES_TOKEN, values)

    @classmethod
    def default_job(cls):
        pass

    @classmethod
    def _get_tuned_job_and_default_role_state_tuples(cls):
        return [(cls.user_job.situation_job, cls.user_job.role_state)]

    @classmethod
    def _states(cls):
        return (SituationStateData(1, ManageCustomersState, factory=cls.manage_customers_state),)

    def start_situation(self):
        super().start_situation()
        self._change_state(self.manage_customers_state())
        self._give_loot(self.initiating_sim_on_start_rewards, self.initiating_sim_info, None)

    def on_remove(self):
        super().on_remove()
        if self.purchase_interaction_tags is not None:
            services.get_event_manager().unregister(self, (TestEvent.PaymentDone,))
        self._give_loot(self.initiating_sim_on_end_rewards, self.initiating_sim_info, None)
        self.show_end_sale_dialog_notification()

    def _self_destruct(self):
        self._give_loot(self.initiating_sim_on_end_naturally_rewards, self.initiating_sim_info, None)
        situation_manager = services.get_zone_situation_manager()
        for situation_id in self.customer_situations:
            situation = situation_manager.get(situation_id)
            if situation is not None:
                situation._self_destruct()
        self.customer_situations.clear()
        super()._self_destruct()

    def get_customer_situations(self):
        customers = []
        situation_manager = services.get_zone_situation_manager()
        for situation_id in self.customer_situations:
            situation = situation_manager.get(situation_id)
            if situation is not None:
                customers.append(situation)
        self.customer_situations = [situation.id for situation in customers]
        return self.customer_situations

    def create_customer_situation(self):
        situation_manager = services.get_zone_situation_manager()
        situation_id = situation_manager.create_situation(self.customer_situation, guest_list=None, user_facing=False)
        self.customer_situations.append(situation_id)

    def object_sold(self, target:'GameObject', amount:'int'):
        old_value = target.current_value
        target.current_value = amount
        if self.tending_sim_on_sell_rewards.on_sell_loot_actions:
            selling_platform = target.parent
            sell_interactions = (interaction for interaction in selling_platform.interaction_refs if interaction.affordance in self.tending_sim_on_sell_rewards.tend_interactions)
            for interaction in sell_interactions:
                tending_sim = interaction.context.sim.sim_info
                stored_sim_info_component = target.get_component(STORED_SIM_INFO_COMPONENT)
                if stored_sim_info_component is None:
                    target.add_dynamic_component(STORED_SIM_INFO_COMPONENT, sim_id=interaction.context.sim.id)
                else:
                    stored_sim_info_component.add_sim_id_to_list(interaction.context.sim.id)
                self._give_loot(self.tending_sim_on_sell_rewards.on_sell_loot_actions, tending_sim, target)
        self.increase_sale(target, amount)
        self._give_loot(self.initiating_sim_on_sell_rewards, self.initiating_sim_info, target)
        target.current_value = old_value

    def increase_sale(self, object_sold:'GameObject', amount:'int'):
        if self.end_sale_dialog_notification is None:
            return
        object_key = object_sold.definition.id
        sale = None
        if object_key not in self.sales:
            recipe_id = 0
            if object_sold.crafting_component is not None:
                crafting_process = object_sold.get_crafting_process()
                if crafting_process.original_target != object_sold:
                    recipe = crafting_process.recipe
                    if recipe is not None:
                        recipe_id = recipe.guid64
            sale = SaleResultInfo(recipe_id=recipe_id)
            self.sales[object_key] = sale
        else:
            sale = self.sales[object_key]
        sale.increase_value(1, amount)

    def _give_loot(self, loot:'Tuple[LootActions]', sim_info:'SimInfo', target:'GameObject'):
        if loot is not None:
            resolver = SingleSimResolver(sim_info) if target is None else SingleActorAndObjectResolver(sim_info, target, source=self)
            for loot_action in loot:
                loot_action.apply_to_resolver(resolver)

    def show_end_sale_dialog_notification(self):
        if self.end_sale_dialog_notification is not None:
            lines = []
            definition_manager = services.definition_manager()
            total_earned = 0
            for (object_sold_id, sale) in self.sales.items():
                lines.append(self.end_sale_dialog_notification.notification_line(sale.quantity, LocalizationHelperTuning.get_recipe_or_object_name(definition_id=object_sold_id, recipe_id=sale.recipe_id), sale.simoleons_earned))
                total_earned = total_earned + sale.simoleons_earned
            (initiating_selling_platform_name, initiating_selling_platform_icon) = self._get_initiating_platform_selling_data()
            header = None
            if initiating_selling_platform_name is not None:
                header = self.end_sale_dialog_notification.notification_header(initiating_selling_platform_name, total_earned)
            else:
                header = self.end_sale_dialog_notification.notification_header_default(total_earned)
            notification_lines = LocalizationHelperTuning.get_new_line_separated_strings(lines)
            notification_bullets = LocalizationHelperTuning.get_bulleted_list(header, tuple(notification_lines))
            sim_info = self.initiating_sim_info
            resolver = SingleSimResolver(sim_info)
            text_to_show = notification_bullets if notification_bullets is not None else header
            dialog = self.end_sale_dialog_notification.notification(sim_info, resolver, text=lambda *_: text_to_show)
            if initiating_selling_platform_icon is not None:
                icon_override = IconInfoData(initiating_selling_platform_icon)
                dialog.show_dialog(icon_override=icon_override)
            else:
                dialog.show_dialog()

    def _check_valid_tags(self, interaction_tags, valid_tags):
        return any(interaction_tag in valid_tags for interaction_tag in interaction_tags)

    def handle_event(self, sim_info, event, resolver):
        if event == TestEvent.PaymentDone and resolver.event_kwargs is not None and 'resolver' in resolver.event_kwargs:
            payment_info = resolver.event_kwargs['payment_info']
            payment_resolver = resolver.event_kwargs['resolver']
            if hasattr(payment_resolver, 'interaction'):
                tags = payment_resolver.interaction.interaction_category_tags
                if self._check_valid_tags(tags, self.purchase_interaction_tags):
                    target = payment_resolver.target
                    self.object_sold(target, payment_info.amount)

    def _on_object_removed(self, obj):
        if obj.id == self._initiating_selling_platform_id:
            self._self_destruct()
lock_instance_tunables(YardSaleSituation, creation_ui_option=SituationCreationUIOption.NOT_AVAILABLE)