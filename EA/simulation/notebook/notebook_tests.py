import servicesfrom event_testing.results import TestResultfrom event_testing.test_base import BaseTestfrom caches import cached_testfrom interactions import ParticipantTypeActorTargetSimfrom sims4.tuning.tunable import HasTunableSingletonFactory, AutoFactoryInit, TunableEnumEntry, TunableReferencefrom tunable_utils.tunable_white_black_list import TunableWhiteBlackListfrom ui.notebook_tuning import NotebookCategories, NotebookSubCategoriesimport sims4.loglogger = sims4.log.Logger('Notebook', default_owner='mkartika')
class NotebookCategoriesTest(HasTunableSingletonFactory, AutoFactoryInit, BaseTest):
    FACTORY_TUNABLES = {'subject': TunableEnumEntry(description='\n            The subject of the test.\n            ', tunable_type=ParticipantTypeActorTargetSim, default=ParticipantTypeActorTargetSim.Actor), 'unlocked_categories': TunableWhiteBlackList(description='\n            This allow/block list will check whether or not the subject has\n            unlocked notebook categories.\n            ', tunable=TunableEnumEntry(description='\n                Notebook categories.\n                ', tunable_type=NotebookCategories, default=NotebookCategories.INVALID, invalid_enums=(NotebookCategories.INVALID,), pack_safe=True)), 'unlocked_subcategories': TunableWhiteBlackList(description='\n            This allow/block list will check whether or not the subject has\n            unlocked specific notebook subcategories.\n            ', tunable=TunableEnumEntry(description='\n                 Notebook subcategories.\n                 ', tunable_type=NotebookSubCategories, default=NotebookSubCategories.INVALID, invalid_enums=(NotebookSubCategories.INVALID,), pack_safe=True)), 'unlocked_entries': TunableWhiteBlackList(description='\n            This allow/block list will check whether or not the subject has\n            unlocked specific notebook entries.\n            ', tunable=TunableReference(description='\n                Notebook entry.\n                ', manager=services.get_instance_manager(sims4.resources.Types.NOTEBOOK_ENTRY), class_restrictions=('NotebookEntry',), pack_safe=True))}

    def get_expected_args(self):
        return {'subject': self.subject}

    @cached_test
    def __call__(self, subject=None):
        subject = next(iter(subject))
        tracker = subject.notebook_tracker
        if tracker is None:
            return TestResult(False, 'Sim {} has no notebook tracker', subject, tooltip=self.tooltip)
        if not self.unlocked_categories.test_collection(tracker.unlocked_category_ids):
            return TestResult(False, 'Sim {} do not meet allow/block list unlocked notebook categories requirements.', subject, tooltip=self.tooltip)
        subcategory_ids = tracker.unlocked_subcategory_ids
        if not self.unlocked_subcategories.test_collection(subcategory_ids):
            return TestResult(False, 'Sim {} do not meet allow/block list unlocked notebook subcategories requirements.', subject, tooltip=self.tooltip)
        if subcategory_ids or self.unlocked_entries.whitelist_item_required:
            return TestResult(False, 'Sim {} has nothing unlocked in the notebook and is testingentries requirements. Cannot possible have met whitelist requirements.', subject, tooltip=self.tooltip)
        for subcategory_id in subcategory_ids:
            if not self.unlocked_entries.test_collection(tracker.unlocked_entry_ids(subcategory_id)):
                return TestResult(False, 'Sim {} do not meet allow/block list unlocked notebook entries requirements.', subject, tooltip=self.tooltip)
        return TestResult.TRUE
