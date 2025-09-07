from __future__ import annotationsimport servicesfrom careers.career_enums import GigScoringBucketfrom event_testing.results import TestResultNumericfrom event_testing.test_base import BaseTestfrom interactions import ParticipantTypefrom sims4.resources import Typesfrom sims4.tuning.tunable import HasTunableSingletonFactory, AutoFactoryInit, TunableList, TunableEnumEntry, Tunable, TunableReference, HasTunableFactory, OptionalTunable, TunableVariantfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from careers.career_gig import Gig
    from event_testing.results import TestResult
class _BaseGigSelector(HasTunableFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'gig_career': OptionalTunable(description='\n            If enabled, we will filter out gigs that are\n            not associated with this career.\n            ', tunable=TunableReference(description='\n                The Gig Career we want to filter by.\n                ', manager=services.get_instance_manager(Types.CAREER)))}

    def get_gigs(self) -> 'List[Gig]':
        gigs = self._get_selected_gigs()
        if self.gig_career is None:
            return gigs
        return [gig for gig in gigs if gig.career == self.gig_career]

    def _get_selected_gigs(self) -> 'List[Gig]':
        raise NotImplementedError

class _ListGigSelector(_BaseGigSelector):
    FACTORY_TUNABLES = {'gigs': TunableList(description='\n            The list of gigs we want to test.\n            ', tunable=TunableReference(description='\n                A single gig we want to test.\n                ', manager=services.get_instance_manager(Types.CAREER_GIG)))}

    def _get_selected_gigs(self) -> 'List[Gig]':
        return self.gigs

class _BucketGigSelector(_BaseGigSelector):
    FACTORY_TUNABLES = {'buckets': TunableList(tunable=TunableEnumEntry(description='\n                Bucket to test against.\n                ', tunable_type=GigScoringBucket, default=GigScoringBucket.DEFAULT), unique_entries=True)}

    def _get_selected_gigs(self) -> 'List[Gig]':
        all_gigs = services.get_instance_manager(Types.CAREER_GIG).types.values()
        gigs_to_return = []
        for gig in all_gigs:
            if gig.picker_scoring is not None and gig.picker_scoring.bucket in self.buckets:
                gigs_to_return.append(gig)
        return gigs_to_return

class GigVisibilityTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    FACTORY_TUNABLES = {'participants': TunableEnumEntry(description='\n            The sim(s) to test.\n            ', tunable_type=ParticipantType, default=ParticipantType.Actor), 'test_individual': Tunable(description='\n            If true, the test will pass if any of the participants pass the criteria. If false,\n            all participants must pass the test.\n            ', tunable_type=bool, default=False), 'invert': Tunable(description='\n            If true, will take the output of the test and invert it. \n            ', tunable_type=bool, default=False), 'gigs': TunableVariant(description='\n            Which gigs do we want to test?\n            ', by_bucket=_BucketGigSelector.TunableFactory(), by_list=_ListGigSelector.TunableFactory(), default='by_bucket'), 'count': Tunable(description='\n            How many of the tested gigs need to be visible in order\n            for this test to pass?\n            ', tunable_type=int, default=1)}

    def get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return {'test_targets': self.participants}

    def __call__(self, test_targets:'Tuple[Any, ...]'=()) -> 'TestResult':
        result = TestResultNumeric.TRUE
        for target in test_targets:
            result = self._test(target)
            if result:
                if self.test_individual:
                    break
                    if not self.test_individual:
                        break
            elif not self.test_individual:
                break
        if self.invert:
            if result:
                return TestResultNumeric(False, 'Passed tests, but the test is inverted.', current_value=result.current_value, goal_value=result.goal_value, tooltip=self.tooltip)
            else:
                return TestResultNumeric(True, current_value=result.current_value, goal_value=result.goal_value)
        return result

    def _test(self, test_target:'Any') -> 'TestResultNumeric':
        gigs = self.gigs().get_gigs()
        passed_gigs = 0
        for gig in gigs:
            result = gig.picker_row_result(owner=test_target, run_visibility_tests=True, disable_row_if_visibility_tests_fail=True)
            if result is not None and result.is_enable:
                passed_gigs += 1
        if passed_gigs >= self.count:
            return TestResultNumeric(True, current_value=passed_gigs, goal_value=self.count)
        return TestResultNumeric(False, 'Not enough gigs passed their visibility tests.', current_value=passed_gigs, goal_value=0, tooltip=self.tooltip)
