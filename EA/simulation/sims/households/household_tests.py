from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *from caches import cached_testfrom event_testing.resolver import SingleSimResolverfrom event_testing.results import TestResultfrom event_testing.test_base import BaseTestfrom event_testing.test_events import TestEventfrom interactions import ParticipantType, ParticipantTypeSim, ParticipantTypeSingle, ParticipantTypeSingleSim, TargetTypefrom sims.households.household_tests_enums import HouseholdSizeChangeTypefrom sims.sim_info_tests import SimInfoTestfrom sims4.tuning.tunable import AutoFactoryInit, HasTunableSingletonFactory, OptionalTunable, TunableSingletonFactory, Tunable, TunableEnumEntryimport event_testingimport services
class PlayerPopulationTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):

    def get_expected_args(self):
        return {}

    @cached_test
    def __call__(self):
        culling_service = services.get_culling_service()
        max_player_population = culling_service.get_max_player_population()
        if max_player_population:
            household_manager = services.household_manager()
            player_population = sum(len(household) for household in household_manager.values() if household.is_player_household)
            if player_population >= max_player_population:
                return TestResult(False, 'Over the maximum player population ({}/{})', player_population, max_player_population, tooltip=lambda *_, **__: self.tooltip(player_population, max_player_population))
        return TestResult.TRUE

class InSameHouseholdTest(AutoFactoryInit, event_testing.test_base.BaseTest):
    test_events = ()
    FACTORY_TUNABLES = {'description': '\n            Require the specified participants to be or not to be in the same household.\n            ', 'subject_a': TunableEnumEntry(description="\n            The participant's household to be compared to subject_b.\n            ", tunable_type=ParticipantTypeSingle, default=ParticipantTypeSingle.Actor), 'subject_b': TunableEnumEntry(description="\n            The participant's household to be compared to subject_a.\n            ", tunable_type=ParticipantTypeSingle, default=ParticipantTypeSingle.TargetSim), 'subjects_households_match': Tunable(description='\n            If True, subject_a must be in the same household as subject_b. If False, they must not be.\n            ', tunable_type=bool, default=True)}

    def get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return {'subject_a': self.subject_a, 'subject_b': self.subject_b, 'affordance': ParticipantType.Affordance, 'context': ParticipantType.InteractionContext}

    @cached_test
    def __call__(self, subject_a:'Optional[ParticipantTypeSingle]'=None, subject_b:'Optional[ParticipantTypeSingle]'=None, affordance:'Optional[ParticipantType]'=None, context:'Optional[ParticipantType]'=None) -> 'TestResult':
        subject_a = next(iter(subject_a), None)
        subject_b = next(iter(subject_b), None)
        if affordance.target_type == TargetType.ACTOR:
            if self.subject_a == ParticipantType.TargetSim or self.subject_a == ParticipantType.Object:
                subject_a = context.sim.sim_info
            if self.subject_b == ParticipantType.TargetSim or self.subject_b == ParticipantType.Object:
                subject_b = context.sim.sim_info
        if affordance is not None and subject_a is None or subject_b is None:
            return TestResult(False, 'One of the subject is None, subject_a: {}, subject_b: {}', subject_a, subject_b, tooltip=self.tooltip)
        if self.subjects_households_match:
            if subject_a.household_id != subject_b.household_id:
                return TestResult(False, "{}'s household must match {}, but household ids are {} and {}.", subject_a, subject_b, subject_a.household_id, subject_b.household_id, tooltip=self.tooltip)
        elif subject_a.household_id == subject_b.household_id:
            return TestResult(False, "{}'s household must not match {}, but household ids are {} and {}.", subject_a, subject_b, subject_a.household_id, subject_b.household_id, tooltip=self.tooltip)
        return TestResult.TRUE

class IsLastPlayedHomeZone(HasTunableSingletonFactory, AutoFactoryInit, event_testing.test_base.BaseTest):
    FACTORY_TUNABLES = {'subject': TunableEnumEntry(description="\n            The participant's household that will be tested.\n            ", tunable_type=ParticipantTypeSingleSim, default=ParticipantTypeSingleSim.Actor), 'negate': Tunable(description="\n            If checked then this test will pass if subject's current home zone is different from\n            its last played home zone.\n            ", tunable_type=bool, default=False)}

    def get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return {'targets': self.subject}

    def __call__(self, targets:'Set[Any]') -> 'TestResult':
        target = next(iter(targets), None)
        if target is None:
            return TestResult(False, "There isn't a valid target for participant {}", self.subject, tooltip=self.tooltip)
        household = target.household
        if household is None:
            return TestResult(False, "There isn't a valid household for target participant {}", self.subject, tooltip=self.tooltip)
        is_last_played_home_zone = household.has_home_zone_been_active()
        if self.negate:
            if is_last_played_home_zone:
                return TestResult(False, 'The current home zone is same as the lasted played home zone but the result was negated', tooltip=self.tooltip)
            return TestResult.TRUE
        if is_last_played_home_zone:
            return TestResult.TRUE
        return TestResult(False, 'The current home zone is different from lasted played home zone', tooltip=self.tooltip)

class HouseholdSizeChangeTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    test_events = (TestEvent.HouseholdChanged,)
    FACTORY_TUNABLES = {'change_type': TunableEnumEntry(description='\n            Which household size-change event type to test.\n\n            ADD: Test Sims that have been added to the household.\n\n            REMOVE: Test Sims that have been removed from the household.\n\n            ALL: Test all Sims that use the household change event.\n            ', tunable_type=HouseholdSizeChangeType, default=HouseholdSizeChangeType.ADD), 'siminfo_test': OptionalTunable(description='\n            If enabled, run this test on each Sim that is added to\n            or removed from the household.\n            ', tunable=SimInfoTest.TunableFactory(locked_args={'who': ParticipantType.Actor, 'tooltip': None}))}

    def get_expected_args(self) -> 'Dict':
        return {'participants': ParticipantTypeSim.TargetSim, 'sim_removed': event_testing.test_constants.FROM_EVENT_DATA}

    @cached_test
    def __call__(self, participants:'Set[Any]', sim_removed:'bool') -> 'TestResult':
        if not participants:
            return TestResult(False, 'HouseholdSizeChangeTest: Required participants not found.', tooltip=self.tooltip)
        for participant in participants:
            if not participant.is_sim:
                return TestResult(False, 'Participant {} is not a sim.', participant, tooltip=self.tooltip)
            if self.change_type == HouseholdSizeChangeType.ADD and sim_removed:
                return TestResult(False, 'Participant {} is being removed and the test uses type {}.', participant, self.change_type, tooltip=self.tooltip)
            if self.change_type == HouseholdSizeChangeType.REMOVE and not sim_removed:
                return TestResult(False, 'Participant {} is being added and the test uses type {}.', participant, self.change_type, tooltip=self.tooltip)
            if self.siminfo_test is not None:
                resolver = SingleSimResolver(participant.sim_info)
                if not resolver(self.siminfo_test):
                    return TestResult(False, 'Participant {} did not meet requirements.', participant, tooltip=self.tooltip)
        return TestResult.TRUE
TunableInSameHouseholdTest = TunableSingletonFactory.create_auto_factory(InSameHouseholdTest)