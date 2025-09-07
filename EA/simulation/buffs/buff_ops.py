from __future__ import annotationsimport interactionsfrom autonomy.autonomy_modifier import AutonomyModifierfrom buffs import BuffPolarityfrom buffs.tunable import BuffReference, TunableBuffReferencefrom interactions import ParticipantTypefrom interactions.utils import LootTypefrom interactions.utils.loot_basic_op import BaseLootOperation, BaseTargetedLootOperationfrom sims4.localization import TunableLocalizedStringfrom sims4.tuning.tunable import Tunable, TunableMapping, TunableReference, TunableList, OptionalTunable, TunableEnumEntry, TunableFactory, TunableRangefrom sims4.tuning.tunable_base import GroupNamesfrom statistics.statistic_categories import StatisticCategoryfrom tag import TunableTagsimport servicesimport sims4.logimport singletonsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims.sim_info import SimInfo
    from event_testing.resolver import Resolver
    from interactions.base.interaction import Interactionlogger = sims4.log.Logger('Buffs')
class BuffOp(BaseLootOperation):
    FACTORY_TUNABLES = {'buff': TunableBuffReference(pack_safe=True)}

    def __init__(self, buff, **kwargs):
        super().__init__(**kwargs)
        self._buff = buff

    @property
    def loot_type(self) -> 'LootType':
        return interactions.utils.LootType.BUFF

    @property
    def buff(self) -> 'BuffReference':
        return self._buff

    def _apply_to_subject_and_target(self, subject:'SimInfo', target:'SimInfo', resolver:'Resolver') -> 'Optional[bool]':
        if self._buff.buff_type is not None:
            if subject is None:
                logger.error('Subject is None for the buff loot {}, resolver {}.', self._buff.buff_type, resolver)
                return False
            subject.add_buff_from_op(self._buff.buff_type, self._buff.buff_reason, buff_source=self._buff.buff_source)

    def apply_to_interaction_statistic_change_element(self, interaction:'Interaction') -> 'Optional[Dict[SimInfo, AutonomyModifier]]':
        if self._buff.buff_type is None or not self._buff.buff_type.commodity:
            return
        autonomy_modifier_handlers = None
        locked_stat = [self._buff.buff_type.commodity]
        for recipient in interaction.get_participants(self.subject):
            if recipient.add_buff_from_op(self._buff.buff_type, self._buff.buff_reason, buff_source=self._buff.buff_source):
                if autonomy_modifier_handlers is None:
                    autonomy_modifier_handlers = {}
                autonomy_modifier_handlers[recipient] = AutonomyModifier(locked_stats=locked_stat)
        return autonomy_modifier_handlers

class BuffTransferOp(BaseTargetedLootOperation):
    FACTORY_TUNABLES = {'moods_only': Tunable(description='\n            Checking this box will limit the operations to only the buffs with\n            an associated mood.\n            ', tunable_type=bool, default=True), 'buff_reason': OptionalTunable(description='\n            If set, specify a reason why the buff was added.\n            ', tunable=TunableLocalizedString(description='\n                The reason the buff was added. This will be displayed in the\n                buff tooltip.\n                ')), 'mood_types': OptionalTunable(TunableList(description='\n                If enabled, only transfer buffs with associated moods in this list.\n                ', tunable=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.MOOD)))), 'polarity': OptionalTunable(TunableEnumEntry(description='\n                If enabled, only transfer buffs that match the selected polarity.\n                ', tunable_type=BuffPolarity, default=BuffPolarity.NEUTRAL, tuning_group=GroupNames.UI))}

    def __init__(self, moods_only, buff_reason, mood_types=None, polarity=None, **kwargs):
        super().__init__(**kwargs)
        self._moods_only = moods_only
        self._buff_reason = buff_reason
        self._mood_types = mood_types
        self._polarity = polarity

    def _apply_to_subject_and_target(self, subject, target, resolver):
        old_buff_types = list(subject.get_active_buff_types())
        if self._moods_only:
            for buff_entry in old_buff_types:
                if buff_entry.mood_type is not None:
                    subject.remove_buff_by_type(buff_entry)
        else:
            for buff_entry in old_buff_types:
                subject.remove_buff_by_type(buff_entry)
        for target_buff in target.get_active_buff_types():
            if self._moods_only and target_buff.mood_type is None:
                pass
            elif self._mood_types is not None and target_buff.mood_type not in self._mood_types:
                pass
            elif self._polarity is not None and self._polarity is not target_buff.polarity:
                pass
            else:
                buff_commodity = target_buff.commodity
                subject.add_buff(target_buff)
                if buff_commodity is not None:
                    tracker = subject.get_tracker(buff_commodity)
                    tracker.set_max(buff_commodity)
                    subject.set_buff_reason(target_buff, self._buff_reason)

class DynamicBuffLootOp(BaseLootOperation):
    FACTORY_TUNABLES = {'description': '\n        This loot will give a random buff based on the weight get tuned inside.\n        ', 'buffs': TunableMapping(description='\n            ', key_type=TunableReference(description='\n                Buff that will get this weight in the random.', manager=services.get_instance_manager(sims4.resources.Types.BUFF)), value_type=Tunable(description='\n                The weight value.', tunable_type=float, default=0)), 'buff_reason': OptionalTunable(description='\n            If set, specify a reason why the buff was added.\n            ', tunable=TunableLocalizedString(description='\n                The reason the buff was added. This will be displayed in the\n                buff tooltip.\n                '))}

    def __init__(self, buffs, buff_reason, **kwargs):
        super().__init__(**kwargs)
        self._buffs = buffs
        self._buff_reason = buff_reason
        self._random_buff = None

    @TunableFactory.factory_option
    def subject_participant_type_options(description=singletons.DEFAULT, **kwargs):
        return BaseLootOperation.get_participant_tunable(*('subject',), invalid_participants=(ParticipantType.Invalid, ParticipantType.All, ParticipantType.PickedItemId), **kwargs)

    def _get_random_buff(self):
        if self._random_buff is None:
            buff_pair_list = list(self._buffs.items())
            self._random_buff = sims4.random.pop_weighted(buff_pair_list, flipped=True)
        return self._random_buff

    def _apply_to_subject_and_target(self, subject, target, resolver):
        random_buff = self._get_random_buff()
        if random_buff is not None:
            if not subject.is_sim:
                logger.error('Tuning error: subject {} of DynamicBuffLootOp giving buff {} for reason {} is not a sim', self.subject, random_buff, self._buff_reason)
                return
            subject.add_buff_from_op(random_buff, self._buff_reason)

    def _on_apply_completed(self):
        random_buff = self._random_buff
        self._random_buff = None
        return random_buff

class BuffRemovalOp(BaseLootOperation):
    FACTORY_TUNABLES = {'buff_categories_to_remove': TunableList(description="\n            All buffs with at least one of the categories tuned here will be removed from the Sim\n            unless it has any category tuned in Categories To Ignore.\n            This comes from the owning commodity which is the category tuning on the buff in Temporary Commodity Info\n            -> Category or from the buff's owning commodity Categories.\n            ", tunable=TunableEnumEntry(description='\n                Category to be removed.\n                ', tunable_type=StatisticCategory, default=StatisticCategory.INVALID, pack_safe=True)), 'categories_to_ignore': TunableList(description='\n            If a buff is found from Buff Categories To Remove and has any category from within this list, then it will\n            be ignored and not removed.\n            ', tunable=TunableEnumEntry(description='\n                Category if found on a buff to make the buff be ignored and not removed.\n                ', tunable_type=StatisticCategory, default=StatisticCategory.INVALID, pack_safe=True)), 'remove_all_visible_buffs': Tunable(description="\n            If checked, all visible buffs on the Sim, excluding those specified in\n            the 'buffs_to_ignore' list will be removed.  If unchecked, buff removal\n            will be handled by the 'buffs_to_remove' list.\n            ", tunable_type=bool, default=False), 'buffs_to_remove': TunableList(description="\n            If 'remove_all_buffs' is not checked, this is the list of buffs that\n            will be removed from the subject.  If 'remove_all_buffs' is checked,\n            this list will be ignored.\n            ", tunable=TunableReference(description='\n                Buff to be removed.\n                ', manager=services.get_instance_manager(sims4.resources.Types.BUFF), pack_safe=True)), 'buff_tags_to_remove': TunableTags(description="\n            If 'remove_all_buffs' is not checked, buffs with any tag in this list\n            will be removed from the subject. If 'remove_all_buffs' is checked, this\n            list will be ignored. You can also specify how many buffs you want to remove\n            by tags in count_to_remove_by_tags\n            ", filter_prefixes=('buff',)), 'count_to_remove_by_tags': OptionalTunable(tunable=TunableRange(description='\n                If enabled, randomly remove x number of buffs specified in buff_tags_to_remove.\n                If disabled, all buffs specified in buff_tags_to_remove will be removed\n                ', tunable_type=int, default=1, minimum=1)), 'buffs_to_ignore': TunableList(description="\n            If 'remove_all_buffs' is checked, no buffs included in this list will\n            be removed.  If 'remove_all_buffs' is unchecked, this list will be\n            ignored.\n            ", tunable=TunableReference(description='\n                Buff to be removed.\n                ', manager=services.get_instance_manager(sims4.resources.Types.BUFF), pack_safe=True))}

    def __init__(self, remove_all_visible_buffs, buffs_to_remove, buff_tags_to_remove, count_to_remove_by_tags, buffs_to_ignore, buff_categories_to_remove, categories_to_ignore, **kwargs):
        super().__init__(**kwargs)
        self._remove_all_visible_buffs = remove_all_visible_buffs
        self._buffs_to_remove = buffs_to_remove
        self._buff_tags_to_remove = buff_tags_to_remove
        self._count_to_remove_by_tags = count_to_remove_by_tags
        self._buffs_to_ignore = buffs_to_ignore
        self._buff_categories_to_remove = buff_categories_to_remove
        self._categories_to_ignore = categories_to_ignore

    def _apply_to_subject_and_target(self, subject, target, resolver):
        if self._remove_all_visible_buffs:
            removal_list = []
            removal_list.extend(subject.Buffs)
            for buff in removal_list:
                if buff.buff_type in self._buffs_to_ignore:
                    pass
                elif not buff.visible:
                    pass
                else:
                    if buff.commodity is not None:
                        if subject.is_statistic_type_added_by_modifier(buff.commodity):
                            pass
                        else:
                            tracker = subject.get_tracker(buff.commodity)
                            commodity_inst = tracker.get_statistic(buff.commodity)
                            if commodity_inst is not None and commodity_inst.core:
                                pass
                            else:
                                subject.Buffs.remove_buff_entry(buff)
                    subject.Buffs.remove_buff_entry(buff)
        else:
            for buff_type in self._buffs_to_remove:
                subject.Buffs.remove_buff_by_type(buff_type)
            subject.Buffs.remove_buffs_by_tags(self._buff_tags_to_remove, count_to_remove=self._count_to_remove_by_tags)
            if self._buff_categories_to_remove:
                subject.Buffs.remove_buffs_by_categories(self._buff_categories_to_remove, self._categories_to_ignore)
