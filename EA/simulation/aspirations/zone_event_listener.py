from __future__ import annotationsfrom aspirations.aspiration_tuning import AspirationBasicfrom aspirations.aspiration_types import AspriationTypefrom sims4.tuning.instances import lock_instance_tunablesfrom sims4.tuning.tunable import TunableList, TunableTuplefrom sims4.utils import constproperty, blueprintmethodfrom tunable_time import TunableTimeOfDayimport servicesimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.event_data_tracker import EventDataTracker
    from event_testing.resolver import DataResolver
    from sims.sim_info import SimInfologger = sims4.log.Logger('ZoneEventListener')
class ZoneDirectorEventListener(AspirationBasic):
    INSTANCE_TUNABLES = {'valid_times': TunableList(description='\n            The valid times that this event listener can be completed.\n            ', tunable=TunableTuple(description='\n                A period time that this event listener can be completed.\n                ', start_time=TunableTimeOfDay(description='\n                    The start of this period of time that this event listener\n                    can be completed.\n                    ', default_hour=9), end_time=TunableTimeOfDay(description='\n                    The end time of this period of time that this event\n                    listener can be completed.\n                    ', default_hour=17)))}

    @blueprintmethod
    def _verify_tuning_callback(self) -> 'None':
        for objective in self.objectives:
            if not objective.resettable:
                logger.error('Objective {} tuned in {} is not resettable.', objective, self)

    @constproperty
    def aspiration_type():
        return AspriationType.ZONE_DIRECTOR

    @blueprintmethod
    def handle_event(self, sim_info:'SimInfo', event:'EventDataTracker', resolver:'DataResolver') -> 'None':
        if sim_info is None:
            return
        if sim_info.aspiration_tracker is None:
            return
        now = services.time_service().sim_now
        if not any(now.time_between_day_times(time_period.start_time, time_period.end_time) for time_period in self.valid_times):
            return
        sim_info.aspiration_tracker.handle_event(self, event, resolver)
lock_instance_tunables(ZoneDirectorEventListener, do_not_register_events_on_load=True, screen_slam=None)