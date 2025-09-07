from __future__ import annotationsfrom event_testing.results import TestResultfrom event_testing.test_base import BaseTestfrom interactions import ParticipantTypefrom sims4.tuning.tunable import HasTunableSingletonFactory, AutoFactoryInit, TunableEnumEntry, Tunable, TunableListfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
class LuckTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    FACTORY_TUNABLES = {'participants': TunableEnumEntry(description='\n            The sim(s) to test.\n            ', tunable_type=ParticipantType, default=ParticipantType.Actor), 'luck_level_indices': TunableList(description='\n            A list of luck level indices that we are interested in\n            checking. If any of these pass, the test passes.\n            ', tunable=Tunable(description='\n                The index of the luck level we are checking for.\n                ', tunable_type=int, default=0)), 'test_individual': Tunable(description='\n            If true, the test will pass if any of the participants pass the criteria. If false,\n            all participants must pass the test.\n            ', tunable_type=bool, default=False), 'invert': Tunable(description='\n            If true, will take the output of the test and invert it. \n            ', tunable_type=bool, default=False)}

    def get_expected_args(self) -> 'Dict[str, ParticipantType]':
        return {'test_targets': self.participants}

    def __call__(self, test_targets:'Tuple[Any, ...]'=()) -> 'TestResult':
        test_result = TestResult.TRUE
        for target in test_targets:
            tracker = target.luck_tracker
            if tracker is None:
                test_result = TestResult(False, 'Target {} does not have a luck tracker.', target, tooltip=self.tooltip)
                break
            luck_level_index = tracker.try_get_luck_level_index()
            if luck_level_index is None:
                test_result = TestResult(False, 'Target {} has no luck level.', target, tooltip=self.tooltip)
                break
            if luck_level_index not in self.luck_level_indices:
                test_result = TestResult(False, 'Target {} has luck level {} which is not in tested levels.', target, luck_level_index, tooltip=self.tooltip)
                if not self.test_individual:
                    break
                    if self.test_individual:
                        test_result = TestResult.TRUE
                        break
            elif self.test_individual:
                test_result = TestResult.TRUE
                break
        if self.invert:
            if test_result:
                return TestResult(False, 'Passed tests, but the test is inverted.', tooltip=self.tooltip)
            else:
                return TestResult.TRUE
        return test_result
