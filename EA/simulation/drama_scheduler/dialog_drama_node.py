from __future__ import annotationsimport itertoolsimport servicesimport sims4.resourcesfrom drama_scheduler.drama_node import BaseDramaNode, CooldownOption, DramaNodeRunOutcomefrom drama_scheduler.drama_node_types import DramaNodeTypefrom live_events.live_event_service import LiveEventNamefrom situations.custom_states.pivotal_moment_situation import QuestPopupSupressionfrom live_events.live_event_telemetry import LiveEventTelemetryfrom sims4.localization import TunableLocalizedStringFactoryfrom sims4.tuning.tunable import TunableVariant, TunableList, TunableReference, HasTunableSingletonFactory, AutoFactoryInit, TunableTuple, Tunable, OptionalTunable, TunableEnumEntryfrom sims4.utils import classpropertyfrom tunable_utils.tested_list import TunableTestedListfrom typing import TYPE_CHECKINGfrom ui.ui_dialog import UiDialogOk, UiDialogOkCancel, ButtonType, UiDialog, UiDialogResponsefrom ui.ui_dialog_notification import UiDialogNotificationif TYPE_CHECKING:
    from typing import *
    from pivotal_moments.pivotal_moment import PivotalMoment
    from event_testing.resolver import Resolver
class _dialog_and_loot(HasTunableSingletonFactory, AutoFactoryInit):

    def on_node_run(self, drama_node):
        raise NotImplementedError

class _notification_and_loot(_dialog_and_loot):
    FACTORY_TUNABLES = {'notification': UiDialogNotification.TunableFactory(description='\n            The notification that will display to the drama node.\n            '), 'loot_list': TunableList(description='\n            A list of loot operations to apply when this notification is given.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True))}

    def on_node_run(self, drama_node):
        resolver = drama_node._get_resolver()
        target_sim_id = drama_node._sender_sim_info.id if drama_node._sender_sim_info is not None else None
        dialog = self.notification(drama_node._receiver_sim_info, target_sim_id=target_sim_id, resolver=resolver)
        dialog.show_dialog()
        for loot_action in self.loot_list:
            loot_action.apply_to_resolver(resolver)

class _dialog_ok_and_loot(_dialog_and_loot):
    FACTORY_TUNABLES = {'dialog': UiDialogOk.TunableFactory(description='\n            The dialog with an ok button that we will display to the user.\n            '), 'on_dialog_complete_loot_list': TunableList(description='\n            A list of loot that will be applied when the player responds to the\n            dialog or, if the dialog is a phone ring or text message, when the\n            dialog times out due to the player ignoring it for too long.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True)), 'on_dialog_seen_loot_list': TunableList(description='\n            A list of loot that will be applied when player responds to the\n            message.  If the dialog is a phone ring or text message then this\n            loot will not be triggered when the dialog times out due to the\n            player ignoring it for too long.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions',), pack_safe=True))}

    def on_node_run(self, drama_node):
        resolver = drama_node._get_resolver()
        target_sim_id = drama_node._sender_sim_info.id if drama_node._sender_sim_info is not None else None
        dialog = self.dialog(drama_node._receiver_sim_info, target_sim_id=target_sim_id, resolver=resolver)

        def response(dialog):
            for loot_action in self.on_dialog_complete_loot_list:
                loot_action.apply_to_resolver(resolver)
            if dialog.response != ButtonType.DIALOG_RESPONSE_NO_RESPONSE:
                for loot_action in self.on_dialog_seen_loot_list:
                    loot_action.apply_to_resolver(resolver)
            DialogDramaNode.apply_cooldown_on_response(drama_node)
            DialogDramaNode.send_dialog_telemetry(drama_node, dialog)

        dialog.show_dialog(on_response=response)

class _loot_only(_dialog_and_loot):
    FACTORY_TUNABLES = {'on_drama_node_run_loot': TunableList(description='\n            A list of loot operations to apply when the drama node runs.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True))}

    def on_node_run(self, drama_node):
        resolver = drama_node._get_resolver()
        for loot_action in self.on_drama_node_run_loot:
            loot_action.apply_to_resolver(resolver)

class _dialog_ok_cancel_and_loot(_dialog_and_loot):
    FACTORY_TUNABLES = {'dialog': UiDialogOkCancel.TunableFactory(description='\n            The ok cancel dialog that will display to the user.\n            '), 'on_dialog_complete_loot_list': TunableList(description='\n            A list of loot that will be applied when the player responds to the\n            dialog or, if the dialog is a phone ring or text message, when the\n            dialog times out due to the player ignoring it for too long.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True)), 'on_dialog_accepted_loot_list': TunableList(description='\n            A list of loot operations to apply when the player chooses ok.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True)), 'on_dialog_canceled_loot_list': TunableList(description='\n            A list of loot operations to apply when the player chooses cancel.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True)), 'on_dialog_no_response_loot_list': TunableList(description="\n            A list of loot operations to apply when the player ignores and doesn't respond, timing out the dialog.\n            ", tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True))}

    def on_node_run(self, drama_node):
        resolver = drama_node._get_resolver()
        target_sim_id = drama_node._sender_sim_info.id if drama_node._sender_sim_info is not None else None
        dialog = self.dialog(drama_node._receiver_sim_info, target_sim_id=target_sim_id, resolver=resolver)

        def response(dialog):
            for loot_action in self.on_dialog_complete_loot_list:
                loot_action.apply_to_resolver(resolver)
            if dialog.response is not None:
                if dialog.response == ButtonType.DIALOG_RESPONSE_OK:
                    for loot_action in self.on_dialog_accepted_loot_list:
                        loot_action.apply_to_resolver(resolver)
                elif dialog.response == ButtonType.DIALOG_RESPONSE_CANCEL:
                    for loot_action in self.on_dialog_canceled_loot_list:
                        loot_action.apply_to_resolver(resolver)
                elif dialog.response == ButtonType.DIALOG_RESPONSE_NO_RESPONSE:
                    for loot_action in self.on_dialog_no_response_loot_list:
                        loot_action.apply_to_resolver(resolver)
            DialogDramaNode.apply_cooldown_on_response(drama_node)
            DialogDramaNode.send_dialog_telemetry(drama_node, dialog)

        dialog.show_dialog(on_response=response)

class _dialog_multi_tested_response(_dialog_and_loot):
    FACTORY_TUNABLES = {'dialog': UiDialog.TunableFactory(description='\n            The dialog that will display to the user.\n            '), 'on_dialog_complete_loot_list': TunableList(description='\n            A list of loot that will be applied when the player responds to the\n            dialog or, if the dialog is a phone ring or text message, when the\n            dialog times out due to the player ignoring it for too long.\n            ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True)), 'possible_responses': TunableTestedList(description='\n            A tunable tested list of the possible responses to this dialog.\n            ', tunable_type=TunableTuple(description='\n                A possible response for this dialog.\n                ', text=TunableLocalizedStringFactory(description='\n                    The text of the response field.\n                    '), loot=TunableList(description='\n                    A list of loot that will be applied when the player selects this response.\n                    ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION), class_restrictions=('LootActions', 'RandomWeightedLoot'), pack_safe=True))))}

    def on_node_run(self, drama_node):
        resolver = drama_node._get_resolver()
        responses = []
        for (index, possible_response) in self.possible_responses(resolver=resolver, yield_index=True):
            responses.append(UiDialogResponse(dialog_response_id=index, text=possible_response.text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST))
        target_sim_id = drama_node._sender_sim_info.id if drama_node._sender_sim_info is not None else None
        dialog = self.dialog(drama_node._receiver_sim_info, target_sim_id=target_sim_id, resolver=resolver)
        dialog.set_responses(responses)

        def response(dialog):
            for loot_action in self.on_dialog_complete_loot_list:
                loot_action.apply_to_resolver(resolver)
            if 0 <= dialog.response:
                pass
            for loot_action in self.possible_responses[dialog.response].item.loot:
                loot_action.apply_to_resolver(resolver)
            DialogDramaNode.apply_cooldown_on_response(drama_node)
            DialogDramaNode.send_dialog_telemetry(drama_node, dialog)

        dialog.show_dialog(on_response=response)

class DialogDramaNode(BaseDramaNode):
    INSTANCE_TUNABLES = {'dialog_and_loot': TunableVariant(description='\n            The type of dialog and loot that will be applied. If Sender Sim Info was tuned,\n            that Sim will be TargetSim, otherwise Picked Sim Info should be tuned and PickedSim\n            used if desired.\n            ', notification=_notification_and_loot.TunableFactory(), dialog_ok=_dialog_ok_and_loot.TunableFactory(), dialog_ok_cancel=_dialog_ok_cancel_and_loot.TunableFactory(), dialog_multi_response=_dialog_multi_tested_response.TunableFactory(), loot_only=_loot_only.TunableFactory(), default='notification'), 'is_simless': Tunable(description='\n            If checked, this drama node will not be linked to any specific sim. \n            ', tunable_type=bool, default=False), 'live_event_telemetry_name': OptionalTunable(description='\n            If tuned, the dialog shown by this drama node will send telemetry about the live event that opened it.\n            ', tunable=TunableEnumEntry(description='\n                Name of the live event that triggered this drama node.\n                ', tunable_type=LiveEventName, default=LiveEventName.DEFAULT, invalid_enums=(LiveEventName.DEFAULT,)))}

    @classproperty
    def drama_node_type(cls):
        return DramaNodeType.DIALOG

    @classproperty
    def simless(cls):
        return cls.is_simless

    def run(self):
        if self.simless:
            self._receiver_sim_info = services.active_sim_info()
        return super().run()

    def _run(self):
        self.dialog_and_loot.on_node_run(self)
        return DramaNodeRunOutcome.SUCCESS_NODE_COMPLETE

    @classmethod
    def apply_cooldown_on_response(cls, drama_node):
        if drama_node.cooldown is not None and drama_node.cooldown.cooldown_option == CooldownOption.ON_DIALOG_RESPONSE:
            services.drama_scheduler_service().start_cooldown(drama_node)

    @classmethod
    def send_dialog_telemetry(cls, drama_node, dialog):
        if drama_node.live_event_telemetry_name is not None:
            LiveEventTelemetry.send_live_event_dialog_telemetry(drama_node.live_event_telemetry_name, dialog.owner, dialog.response)

class _pivotal_dialog_mixin:
    FACTORY_TUNABLES = {'auto_accept': Tunable(description='\n            If True, bypass the dialog and run response actions as if the player accepted the dialog. If False,\n            show the dialog. \n            \n            This applies to instances triggered via drama nodes.\n            ', tunable_type=bool, default=False)}

    def response(self, dialog:'UiDialogOk', piv_moment_inst:'PivotalMoment', resolver:'Resolver', drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        raise NotImplementedError

    def _get_loots_to_apply(self) -> 'TunableList':
        raise NotImplementedError

    def _get_dialog(self) -> 'UiDialog':
        raise NotImplementedError

    def _get_resolver(self, drama_node:'PivotalMomentDialogDramaNode') -> 'Resolver':
        raise NotImplementedError

    def _get_target_sim_id(self, drama_node:'PivotalMomentDialogDramaNode'):
        raise NotImplementedError

    def _get_receiver_sim_info(self, drama_node:'PivotalMomentDialogDramaNode'):
        raise NotImplementedError

    def on_pivotal_node_run(self, drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        tutorial_service = services.get_tutorial_service()
        if tutorial_service is None:
            return
        piv_moment_inst = tutorial_service.get_pivotal_moment_inst(drama_node.pivotal_moment.guid64)
        if piv_moment_inst is None:
            return
        should_add_minimized_situation = piv_moment_inst.should_add_minimized_Situation()
        can_start_situation = piv_moment_inst.can_situation_start()
        if can_start_situation or not should_add_minimized_situation:
            piv_moment_inst.start_cooldown()
            return
        resolver = self._get_resolver(drama_node)
        target_sim_id = self._get_target_sim_id(drama_node)
        dialog = self._get_dialog(self._get_receiver_sim_info(drama_node), target_sim_id=target_sim_id, resolver=resolver)
        is_pivotal_moment_from_quest = tutorial_service.is_pivotal_moment_active_quest(piv_moment_inst.guid64)
        quest_supressor = QuestPopupSupression()
        auto_accept_for_live_event = is_pivotal_moment_from_quest and quest_supressor.suppress_quest_popups
        is_pivotal_moment_minimized = piv_moment_inst.is_delayed()
        if not is_pivotal_moment_minimized:
            if self.auto_accept or auto_accept_for_live_event:
                piv_moment_inst.send_dialog_telemetry(dialog.owner, ButtonType.DIALOG_RESPONSE_OK)
                if should_add_minimized_situation:
                    piv_moment_inst.add_minimized_situation()
                elif can_start_situation:
                    self._start_pivotal_moment_and_apply_loot(piv_moment_inst, resolver)
                DialogDramaNode.apply_cooldown_on_response(drama_node)
                return
            if piv_moment_inst.is_pending_from_minimization():
                self._apply_loot_and_show_dialog(dialog, piv_moment_inst, resolver, drama_node)
                return
            if should_add_minimized_situation:
                piv_moment_inst.add_minimized_situation()
                return
            if can_start_situation:
                self._apply_loot_and_show_dialog(dialog, piv_moment_inst, resolver, drama_node)
                return
        else:
            if self.auto_accept or auto_accept_for_live_event:
                piv_moment_inst.send_dialog_telemetry(dialog.owner, ButtonType.DIALOG_RESPONSE_OK)
                self._start_pivotal_moment_and_apply_loot(piv_moment_inst, resolver)
                DialogDramaNode.apply_cooldown_on_response(drama_node)
                return
            dialog.show_dialog(on_response=lambda dialog: self.response(dialog, piv_moment_inst, resolver, drama_node))

    def _start_pivotal_moment_and_apply_loot(self, piv_moment_inst:'PivotalMoment', resolver) -> 'None':
        self._apply_loot(resolver)
        piv_moment_inst.start_situation()

    def _apply_loot(self, resolver):
        for loot_action in self._get_loots_to_apply():
            loot_action.apply_to_resolver(resolver)

    def _apply_loot_and_show_dialog(self, dialog, piv_moment_inst, resolver, drama_node):
        self._apply_loot(resolver)
        dialog.show_dialog(on_response=lambda dialog: self.response(dialog, piv_moment_inst, resolver, drama_node))

class _pivotal_dialog_ok(_dialog_ok_and_loot, _pivotal_dialog_mixin):

    def _get_loots_to_apply(self) -> 'TunableList':
        return self.on_dialog_complete_loot_list

    def _get_dialog(self, receiver_sim_info, target_sim_id, resolver) -> 'UiDialog':
        return self.dialog(receiver_sim_info, target_sim_id=target_sim_id, resolver=resolver)

    def _get_resolver(self, drama_node:'PivotalMomentDialogDramaNode') -> 'Resolver':
        return drama_node._get_resolver()

    def _get_target_sim_id(self, drama_node:'PivotalMomentDialogDramaNode'):
        if drama_node._sender_sim_info is not None:
            return drama_node._sender_sim_info.id

    def _get_receiver_sim_info(self, drama_node:'PivotalMomentDialogDramaNode'):
        return drama_node._receiver_sim_info

    def on_node_run(self, drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        super().on_pivotal_node_run(drama_node)

    def response(self, dialog:'UiDialogOk', piv_moment_inst:'PivotalMoment', resolver:'Resolver', drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        for loot_action in self.on_dialog_complete_loot_list:
            loot_action.apply_to_resolver(resolver)
        if dialog.response is not None:
            piv_moment_inst.send_dialog_telemetry(dialog.owner, dialog.response)
            if dialog.response == ButtonType.DIALOG_RESPONSE_NO_RESPONSE:
                piv_moment_inst.start_cooldown()
            else:
                for loot_action in self.on_dialog_seen_loot_list:
                    loot_action.apply_to_resolver(resolver)
                piv_moment_inst.start_situation()
        DialogDramaNode.apply_cooldown_on_response(drama_node)

class _pivotal_dialog_ok_cancel(_dialog_ok_cancel_and_loot, _pivotal_dialog_mixin):

    def _get_loots_to_apply(self) -> 'TunableList':
        return itertools.chain(self.on_dialog_complete_loot_list, self.on_dialog_accepted_loot_list)

    def on_node_run(self, drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        super().on_pivotal_node_run(drama_node)

    def _get_dialog(self, receiver_sim_info, target_sim_id, resolver) -> 'UiDialog':
        return self.dialog(receiver_sim_info, target_sim_id=target_sim_id, resolver=resolver)

    def _get_resolver(self, drama_node:'PivotalMomentDialogDramaNode') -> 'Resolver':
        return drama_node._get_resolver()

    def _get_target_sim_id(self, drama_node:'PivotalMomentDialogDramaNode'):
        if drama_node._sender_sim_info is not None:
            return drama_node._sender_sim_info.id

    def _get_receiver_sim_info(self, drama_node:'PivotalMomentDialogDramaNode'):
        return drama_node._receiver_sim_info

    def response(self, dialog:'UiDialogOk', piv_moment_inst:'PivotalMoment', resolver:'Resolver', drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        for loot_action in self.on_dialog_complete_loot_list:
            loot_action.apply_to_resolver(resolver)
        if dialog.response is not None:
            piv_moment_inst.send_dialog_telemetry(dialog.owner, dialog.response)
            if dialog.response == ButtonType.DIALOG_RESPONSE_OK:
                for loot_action in self.on_dialog_accepted_loot_list:
                    loot_action.apply_to_resolver(resolver)
                piv_moment_inst.start_situation()
            elif dialog.response == ButtonType.DIALOG_RESPONSE_CANCEL:
                for loot_action in self.on_dialog_canceled_loot_list:
                    loot_action.apply_to_resolver(resolver)
                piv_moment_inst.on_pivotal_moment_complete()
            elif dialog.response == ButtonType.DIALOG_RESPONSE_CUSTOM_1:
                piv_moment_inst.start_cooldown()
            elif dialog.response == ButtonType.DIALOG_RESPONSE_NO_RESPONSE:
                for loot_action in self.on_dialog_no_response_loot_list:
                    loot_action.apply_to_resolver(resolver)
                piv_moment_inst.start_cooldown()
        DialogDramaNode.apply_cooldown_on_response(drama_node)

class PivotalMomentDialogDramaNode(BaseDramaNode):
    INSTANCE_TUNABLES = {'pivotal_moment_dialog_variant': TunableVariant(description='\n            The type of dialog to use for pivotal moments, dialog with ok, vs dialog with cancel and ok\n            ', dialog_ok=_pivotal_dialog_ok.TunableFactory(), dialog_ok_cancel=_pivotal_dialog_ok_cancel.TunableFactory(), default='dialog_ok'), 'pivotal_moment': TunableReference(description='\n            The pivotal moment related to this drama node.\n            This is needed so the drama node can ask the pivotal moment to start the situation.\n            ', manager=services.get_instance_manager(sims4.resources.Types.SNIPPET), class_restrictions='PivotalMoment'), 'is_simless': Tunable(description='\n            If checked, this drama node will not be linked to any specific sim. \n            ', tunable_type=bool, default=True)}

    @classproperty
    def drama_node_type(cls) -> 'DramaNodeType':
        return DramaNodeType.DIALOG

    @classproperty
    def simless(cls) -> 'bool':
        return cls.is_simless

    def run(self) -> 'DramaNodeRunOutcome':
        if self.simless:
            self._receiver_sim_info = services.active_sim_info()
        return super().run()

    def _run(self) -> 'DramaNodeRunOutcome':
        self.pivotal_moment_dialog_variant.on_node_run(self)
        return DramaNodeRunOutcome.SUCCESS_NODE_COMPLETE

    @classmethod
    def apply_cooldown_on_response(cls, drama_node:'PivotalMomentDialogDramaNode') -> 'None':
        if drama_node.cooldown is not None and drama_node.cooldown.cooldown_option == CooldownOption.ON_DIALOG_RESPONSE:
            services.drama_scheduler_service().start_cooldown(drama_node)
