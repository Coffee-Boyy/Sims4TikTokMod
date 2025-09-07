from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from situations.situation import Situationfrom careers.career_tuning import Careerfrom careers.career_tuning import _get_career_notification_tunable_factoryfrom careers.career_base import RESPONSE_ID_GO_TO_WORK, RESPONSE_ID_TAKE_PTO, RESPONSE_ID_CALL_IN_SICK, TELEMETRY_WORKDAY_TYPE_WORK_FROM_HOMEfrom careers.career_event import CareerEventfrom careers.career_ops import CareerTimeOffReasonfrom date_and_time import date_and_time_from_week_timefrom event_testing.resolver import SingleSimResolver, DoubleSimResolverfrom interactions.utils.tested_variant import TunableTestedVariantfrom sims4.callback_utils import CallableListfrom sims4.tuning.tunable import TunableReference, TunableTuplefrom sims4.tuning.tunable_base import GroupNamesfrom situations.bouncer.bouncer_request import RequestSpawningOptionfrom situations.bouncer.bouncer_types import BouncerRequestPriorityfrom situations.situation_guest_list import SituationGuestList, SituationGuestInfofrom situations.situation_types import SituationCallbackOption, SituationDisplayTypefrom ui.ui_dialog import UiDialogResponsefrom ui.ui_dialog_generic import UiDialogfrom ui.ui_dialog_notification import UiDialogNotificationimport servicesimport sims4.logimport randomRESPONSE_ID_WORK_FROM_HOME_ASSIGNMENTS = 4RESPONSE_ID_WORK_FROM_HOME_EVENTS = 5logger = sims4.log.Logger('Careers', default_owner='rpang')
class WorkFromHomeEvent(CareerEvent):
    INSTANCE_TUNABLES = {'client_arrival_notification': UiDialogNotification.TunableFactory(description='\n            Dialog to display message that client has arrived\n            ', tuning_group=GroupNames.CUSTOMER), 'client_situation': TunableReference(description='\n            Situation to apply to client when spawned onto work lot\n            ', manager=services.get_instance_manager(sims4.resources.Types.SITUATION), tuning_group=GroupNames.CUSTOMER), 'client_situation_job': TunableReference(description='\n            Situation job to put client sim into when spawned onto work lot\n            ', manager=services.get_instance_manager(sims4.resources.Types.SITUATION_JOB), tuning_group=GroupNames.CUSTOMER)}

    def __init__(self, career):
        super().__init__(career)
        self._client_sim = None

    @classmethod
    def get_sim_filter_gsi_name(cls) -> 'str':
        return str(cls)

    def on_career_event_start(self):
        super().on_career_event_start()
        self.setup_client()

    def on_career_event_stop(self):
        super().on_career_event_stop()
        self.cleanup_client(destroy_situation=True)

    def _on_client_situation_ended(self, situation_id, callback_option, _):
        current_zone = services.current_zone()
        if current_zone.is_zone_shutting_down:
            return
        self.cleanup_client(destroy_situation=False)

    def setup_client(self) -> 'None':
        client_situation_id = self.get_event_situation_id()
        if client_situation_id != 0:
            return
        client_situation_id = self._create_client_situation()
        if client_situation_id is None or client_situation_id == 0:
            logger.error('WorkFromHomeCareer::setup_client() Unable to create client situation')
            return
        if self._client_sim is None:
            logger.error('WorkFromHomeCareer::setup_client() Unable to get client sim to start situation')
        self.set_event_situation_id(client_situation_id)
        self.show_client_dialog()
        services.get_zone_situation_manager().register_for_callback(client_situation_id, SituationCallbackOption.END_OF_SITUATION, self._on_client_situation_ended)

    def cleanup_client(self, destroy_situation:'bool'=False) -> 'None':
        situation_manager = services.get_zone_situation_manager()
        client_situation_id = self.get_event_situation_id()
        if client_situation_id is not None:
            situation_manager.unregister_callback(client_situation_id, SituationCallbackOption.END_OF_SITUATION, self._on_client_situation_ended)
            if destroy_situation:
                situation_manager.destroy_situation_by_id(client_situation_id)
        self.set_event_situation_id(0)
        self._client_sim = None

    def _create_client_situation(self) -> 'Optional[int]':
        client_situation_id = self.get_event_situation_id()
        if client_situation_id != 0:
            return client_situation_id
        filter_results = services.sim_filter_service().submit_filter(sim_filter=self.client_situation_job.filter, callback=None, requesting_sim_info=self.sim_info, allow_yielding=False, blacklist_sim_ids={sim_info.sim_id for sim_info in services.active_household()}, start_time=self.career.start_time, end_time=self.career.start_time + self.career.current_work_duration, gsi_source_fn=self.get_sim_filter_gsi_name)
        self._client_sim = filter_results[0].sim_info if filter_results else None
        if self._client_sim is None:
            logger.error('WorkFromHomeCareer::_create_client_situation() Unable to create situation, no valid client sim found')
            return
        logger.info('WorkFromHomeCareer::_create_client_situation() Adding client {} (SimID: {}) to WorkFromHome workday situation', self._client_sim, self._client_sim.sim_id)
        guest_list = SituationGuestList(invite_only=True, host_sim_id=self.sim_info.sim_id)
        guest_list.add_guest_info(SituationGuestInfo(self._client_sim.sim_id, self.client_situation_job, RequestSpawningOption.DONT_CARE, BouncerRequestPriority.EVENT_VIP, expectation_preference=True))
        client_situation_id = services.get_zone_situation_manager().create_situation(self.client_situation, guest_list=guest_list, user_facing=False, zone_id=services.current_zone_id())
        return client_situation_id

    def show_client_dialog(self) -> 'None':
        if self.sim_info and self._client_sim:
            dialog = self.client_arrival_notification(owner=self.sim_info, target_sim_id=self._client_sim.sim_id, resolver=DoubleSimResolver(self.sim_info, self._client_sim))
            dialog.show_dialog()

class WorkFromHomeCareer(Career):
    INSTANCE_TUNABLES = {'work_option_dialog': TunableTuple(description='\n            Provides options to the player to go to work, do work assignments, play career events or take pto.\n            NOTE: Similar to career_early_warning_alarm setup in career_tuning.py, but that is restricted to be\n                  a phone dialog and has specific setup in PhoneAlert.as and this is a standard dialog.\n            ', dialog=UiDialog.TunableFactory(description='\n                Dialog to allow the player to choose what to do for the work day.\n                '), go_to_work_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button text for choosing to go to office.\n                '), work_assignments_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button text to offer player career assignments to play. Requires assignments to be set up.\n                '), work_career_event_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button text to offer player career events to play. Requires at least 1 valid career event.\n                '), work_career_event_disabled_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button tooltip text to show when work career event button is disabled\n                due to no valid career events being selected.\n                '), work_career_event_active_disabled_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button tooltip text to show when work career event button is disabled\n                due to another active career event. Only 1 can be active at any time.\n                '), take_pto_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button text to allow player to take PTO. Requires the sim to have enough PTO.\n                '), call_in_sick_text=sims4.localization.TunableLocalizedStringFactory(description='\n                Button text to call in sick. Shows this instead of PTO button if the Sim does not have enough PTO.\n                '), work_career_event_daily_end_notification=TunableTestedVariant(description='\n                Notification message on when sim ends work from home event\n                ', tunable_type=_get_career_notification_tunable_factory(), locked_args={'no_notification': None}), tuning_group=GroupNames.UI)}
    _work_option_callbacks = CallableList()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._available_events = list()
        self._pending_career_event = None
        self._scheduler = None
        self._alarm_data = None
        self._extra_data = None

    def _get_career_event(self) -> 'CareerEvent':
        if self.sim_info.is_npc:
            return
        if not self.sim_info.is_instanced():
            return
        else:
            if not self._available_events:
                resolver = SingleSimResolver(self.sim_info)
                self._available_events.extend(event for event in self.career_events if self.is_career_event_on_cooldown(event) or event.tests.run_tests(resolver))
            if self._available_events:
                return random.choice(self._available_events)
            else:
                return
        return

    def has_active_career_event(self) -> 'bool':
        household = self._sim_info.household
        for sim_info in household.sim_info_gen():
            if any(career.is_at_active_event for career in sim_info.careers.values()):
                return True
        return False

    def _get_work_option_responses(self):
        dialog_tuning = self.work_option_dialog if self.work_option_dialog is not None else None
        if dialog_tuning is None:
            return []
        responses = []
        responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_GO_TO_WORK, text=dialog_tuning.go_to_work_text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST))
        responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_WORK_FROM_HOME_ASSIGNMENTS, text=dialog_tuning.work_assignments_text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST))
        if self._pending_career_event is None:
            responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_WORK_FROM_HOME_EVENTS, text=dialog_tuning.work_career_event_text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST, disabled_text=dialog_tuning.work_career_event_disabled_text()))
        elif self.has_active_career_event():
            responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_WORK_FROM_HOME_EVENTS, text=dialog_tuning.work_career_event_text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST, disabled_text=dialog_tuning.work_career_event_active_disabled_text()))
        else:
            responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_WORK_FROM_HOME_EVENTS, text=dialog_tuning.work_career_event_text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST))
        if self.pto > 0:
            responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_TAKE_PTO, text=dialog_tuning.take_pto_text, ui_request=UiDialogResponse.UiDialogUiRequest.NO_REQUEST))
        else:
            responses.append(UiDialogResponse(dialog_response_id=RESPONSE_ID_CALL_IN_SICK, text=dialog_tuning.call_in_sick_text, ui_request=UiDialogResponse.UiDialogUiRequest.CAREER_CALL_IN_SICK))
        return responses

    def _on_work_option_response(self, dialog:'UiDialog', scheduler, alarm_data, extra_data) -> 'None':
        response = dialog.response
        if response != RESPONSE_ID_WORK_FROM_HOME_EVENTS:
            self._pending_career_event = None
        if response == RESPONSE_ID_GO_TO_WORK:
            self._requested_day_off_reason = CareerTimeOffReason.NO_TIME_OFF
            self._taking_day_off_reason = CareerTimeOffReason.NO_TIME_OFF
        elif response == RESPONSE_ID_WORK_FROM_HOME_ASSIGNMENTS:
            self._requested_day_off_reason = CareerTimeOffReason.WORK_FROM_HOME
            self._taking_day_off_reason = CareerTimeOffReason.WORK_FROM_HOME
        elif response == RESPONSE_ID_TAKE_PTO:
            self.request_day_off(CareerTimeOffReason.PTO)
            self.add_pto(-1)
            self.resend_career_data()
        elif response == RESPONSE_ID_CALL_IN_SICK:
            self.request_day_off(CareerTimeOffReason.FAKE_SICK)
        super()._start_work_callback(scheduler=scheduler, alarm_data=alarm_data, extra_data=extra_data)
        if response == RESPONSE_ID_WORK_FROM_HOME_ASSIGNMENTS:
            current_time = services.time_service().sim_now
            self._current_work_end = date_and_time_from_week_time(current_time.week(), alarm_data.end_time)
            self._create_end_of_work_day_alarm()
        self._scheduler = None
        self._alarm_data = None
        self._extra_data = None
        self.remove_work_option_dialog_callback(self.setup_work_dialog)

    def _start_work_callback(self, scheduler, alarm_data, extra_data):
        reason = self._get_drama_node_time_off_reason(end_time=alarm_data.end_time)
        if reason != CareerTimeOffReason.NO_TIME_OFF:
            self._requested_day_off_reason = reason
            self.resend_at_work_info()
            return
        is_on_pto = self.should_skip_next_shift(use_current_time=True) or self._should_automatically_use_pto()
        if is_on_pto or self.sim_info.is_npc or not self.sim_info.is_instanced():
            super()._start_work_callback(scheduler=scheduler, alarm_data=alarm_data, extra_data=extra_data)
            return
        if self._at_work:
            return
        if not services.get_career_service().enabled:
            return
        self._prune_stale_career_event_cooldowns()
        if self.on_assignment:
            self.clear_career_assignments()
            self.resend_career_data()
        self._taking_day_off_reason = CareerTimeOffReason.NO_TIME_OFF
        self._scheduler = scheduler
        self._alarm_data = alarm_data
        self._extra_data = extra_data
        self.add_work_option_dialog_callback(self.setup_work_dialog)

    def setup_work_dialog(self) -> 'None':
        self._pending_career_event = self._get_career_event()
        dialog = self.work_option_dialog.dialog(owner=self.sim_info, resolver=SingleSimResolver(self.sim_info))
        dialog.set_responses(self._get_work_option_responses())
        dialog.show_dialog(on_response=lambda work_option_dialog: self._on_work_option_response(dialog=work_option_dialog, scheduler=self._scheduler, alarm_data=self._alarm_data, extra_data=self._extra_data))

    @classmethod
    def add_work_option_dialog_callback(cls, callback) -> 'None':
        if cls._work_option_callbacks is None:
            cls._work_option_callbacks = CallableList()
        cls._work_option_callbacks.register(callback)
        if len(cls._work_option_callbacks) == 1:
            callback()

    @classmethod
    def remove_work_option_dialog_callback(cls, callback) -> 'None':
        cls._work_option_callbacks.unregister(callback)
        if len(cls._work_option_callbacks) > 0:
            cls._work_option_callbacks[0]()

    def _try_offer_career_event(self):
        if not self._pending_career_event:
            return False
        if issubclass(self._pending_career_event, WorkFromHomeEvent):
            if self._pending_career_event.scorable_situation and self._pending_career_event.scorable_situation.situation:
                self.remove_rival_situation(self._pending_career_event.scorable_situation.situation)
            additional_sims = set()
            self.on_career_event_accepted(career_event=self._pending_career_event, additional_sims=additional_sims, is_additional_sim=False)
        else:
            services.get_career_service().try_add_pending_career_event_offer(self, self._pending_career_event)
        self._send_workday_info_telemetry(TELEMETRY_WORKDAY_TYPE_WORK_FROM_HOME)
        return True

    def _show_start_work_notification(self) -> 'None':
        if self._pending_career_event and issubclass(self._pending_career_event, WorkFromHomeEvent):
            pass
        elif not self.on_assignment:
            self.send_career_message(self.career_messages.career_daily_start_notification)
        if not self.on_assignment:
            self.resend_career_data()
            self.resend_at_work_info()

    def _get_daily_end_notification(self) -> 'TunableTestedVariant':
        if self._pending_career_event:
            return self.work_option_dialog.work_career_event_daily_end_notification
        return self.career_messages.career_daily_end_notification

    def _end_work_callback(self, _):
        if self.on_assignment:
            self._handle_assignment_results()
            self.clear_career_assignments()
            self.resend_career_data()
            return
        super()._end_work_callback(_)

    def end_career_session(self) -> 'None':
        super().end_career_session()
        self._available_events.clear()
        self._pending_career_event = None

    def remove_rival_situation(self, situation:'Situation') -> 'None':
        situation_manager = services.get_zone_situation_manager()
        if situation_manager is None:
            return
        wfh_display_type = situation.situation_display_type_override if situation.situation_display_type_override is not None else SituationDisplayType.NORMAL
        allows_multiple_instances = situation_manager.allows_multiple_instances(situation)
        if not allows_multiple_instances:
            for situation in tuple(situation_manager.get_user_facing_situations_gen()):
                if situation.situation_display_type == wfh_display_type:
                    logger.warn('work_from_home_career::remove_situation() Found situation with same display type, destroying situation {} - {} to allow career event situation to display properly', situation.id, situation)
                    situation_manager.destroy_situation_by_id(situation.id)
