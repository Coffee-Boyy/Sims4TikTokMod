from __future__ import annotationsimport servicesfrom event_testing.results import TestResultfrom event_testing.test_base import BaseTestfrom interactions import ParticipantTypeObjectfrom sims4.tuning.tunable import HasTunableSingletonFactory, AutoFactoryInit, TunableVariant, TunableEnumEntry, Tunablefrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims4.localization import TunableLocalizedStringFactory
    from interactions import ParticipantType
class _IsWispOnObjectTest(HasTunableSingletonFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'subject': TunableEnumEntry(description='\n            The target of this Wisp test.  This should be an object participant.\n            ', tunable_type=ParticipantTypeObject, default=ParticipantTypeObject.Object)}

    def _get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return {'subject': self.subject}

    def _evaluate(self, negate:'bool', tooltip:'TunableLocalizedStringFactory', subject:'Tuple[ParticipantType, ...]'=()) -> 'TestResult':
        wisp_service = services.get_wisp_service()
        if wisp_service is None:
            return TestResult(False, "The Wisp Service returned None. Seems like it wasn't loaded.", tooltip=tooltip)
        subject = next(iter(subject))
        if subject is None:
            return TestResult(False, 'The subject is None, fix in tuning.', tooltip=tooltip)
        if wisp_service.is_wisp_running_on_object(subject):
            if negate:
                return TestResult(False, 'Subject {} has a Wisp running on it.', subject, tooltip=tooltip)
            return TestResult.TRUE
        if negate:
            return TestResult.TRUE
        return TestResult(False, 'Subject {} does have a Wisp running on it.', subject, tooltip=tooltip)

class _IsWispActiveTest(HasTunableSingletonFactory, AutoFactoryInit):

    def _get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return {}

    def _evaluate(self, negate:'bool', tooltip:'TunableLocalizedStringFactory') -> 'TestResult':
        wisp_service = services.get_wisp_service()
        if wisp_service is None:
            return TestResult(False, "The Wisp Service returned None. Seems like it wasn't loaded.", tooltip=tooltip)
        wisp = wisp_service.get_wisp()
        if wisp is None:
            return TestResult(False, 'The wisp has not been initialized yet.', tooltip=tooltip)
        if wisp.is_active:
            if negate:
                return TestResult(False, 'The wisp is active.', tooltip=tooltip)
            return TestResult.TRUE
        if negate:
            return TestResult.TRUE
        TestResult(False, 'The wisp is not active.', tooltip=tooltip)

class WispTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    FACTORY_TUNABLES = {'test_type': TunableVariant(description='\n            The type of wisp test to run.\n            ', is_wisp_on_object=_IsWispOnObjectTest.TunableFactory(), is_wisp_active=_IsWispActiveTest.TunableFactory()), 'negate': Tunable(description='\n            Returns the opposite of the test results.\n            ', tunable_type=bool, default=False)}

    def get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return self.test_type._get_expected_args()

    def __call__(self, subject:'Tuple[str, ParticipantType]'=None) -> 'TestResult':
        return self.test_type._evaluate(self.negate, self.tooltip, subject=subject)
