from __future__ import annotationsfrom interactions import ParticipantTypefrom interactions.liability import Liabilityfrom sims4.localization import TunableLocalizedStringfrom sims4.tuning.tunable import TunableSingletonFactory, TunablePackSafeReference, TunableReference, OptionalTunable, TunableFactory, TunableEnumFlags, TunableVariant, HasTunableFactoryimport event_testingimport servicesimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from buffs.buff import Buff
    from interactions.utils.loot import Interaction, Loot, LootActionlogger = sims4.log.Logger('Buffs')
class BuffReference:
    __slots__ = ('_buff_type', '_buff_reason', '_buff_source')

    def __init__(self, buff_type:'Buff'=None, buff_reason:'str'=None, buff_source:'Union[Interaction, Loot, LootAction]'=None) -> 'None':
        self._buff_type = buff_type
        self._buff_reason = buff_reason
        self._buff_source = buff_source

    @property
    def buff_type(self) -> 'Buff':
        return self._buff_type

    @property
    def buff_reason(self) -> 'str':
        return self._buff_reason

    @property
    def buff_source(self) -> 'Union[Interaction, Loot, LootAction]':
        return self._buff_source

class TunableBuffReference(TunableSingletonFactory):
    __slots__ = ()
    FACTORY_TYPE = BuffReference

    def __init__(self, reload_dependent:'bool'=False, pack_safe:'bool'=False, allow_none:'bool'=False, **kwargs) -> 'None':
        super().__init__(buff_type=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.BUFF), description='Buff that will get added to sim.', allow_none=allow_none, reload_dependent=reload_dependent, pack_safe=pack_safe), buff_reason=OptionalTunable(description='\n                            If set, specify a reason why the buff was added.\n                            ', tunable=TunableLocalizedString(description='\n                                The reason the buff was added. This will be displayed in the\n                                buff tooltip.\n                                ')), buff_source=OptionalTunable(tunable=TunableVariant(description='\n                                The tuning file that applied this buff. This is typically tuned to be the same file that\n                                this buff is being tuned on. This is NOT player facing, and is used for telemetry only. \n                                ', from_loot=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION)), from_interaction=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.INTERACTION)))), **kwargs)

class TunablePackSafeBuffReference(TunableSingletonFactory):
    __slots__ = ()
    FACTORY_TYPE = BuffReference

    def __init__(self, reload_dependent:'bool'=False, allow_none:'bool'=False, **kwargs) -> 'None':
        super().__init__(buff_type=TunablePackSafeReference(manager=services.get_instance_manager(sims4.resources.Types.BUFF), description='Buff that will get added to sim.', allow_none=allow_none, reload_dependent=reload_dependent), buff_reason=OptionalTunable(description='\n                            If set, specify a reason why the buff was added.\n                            ', tunable=TunableLocalizedString(description='\n                                The reason the buff was added. This will be displayed in the\n                                buff tooltip.\n                                ')), buff_source=OptionalTunable(tunable=TunableVariant(description='\n                                The tuning file that applied this buff. This is typically tuned to be the same file that\n                                this buff is being tuned on. This is NOT player facing, and is used for telemetry only. \n                                ', from_loot=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.ACTION)), from_interaction=TunableReference(manager=services.get_instance_manager(sims4.resources.Types.INTERACTION)))), **kwargs)

class TunableBuffElement(TunableFactory):

    @staticmethod
    def _verify_tunable_callback(instance_class, tunable_name, source, tests, buff_type, subject):
        if buff_type.buff_type is None:
            return
        if buff_type.buff_type._temporary_commodity_info is not None:
            logger.error('TunableBuffElement: {} has a buff element with a buff {} with a temporary commodity tuned.', instance_class, buff_type.buff_type)

    @staticmethod
    def factory(interaction, subject, tests, buff_type, sequence=()):
        if buff_type.buff_type is not None:
            for sim in interaction.get_participants(subject):
                if tests.run_tests(interaction.get_resolver()):
                    sequence = buff_type.buff_type.build_critical_section(sim, buff_type.buff_reason, sequence)
        return sequence

    FACTORY_TYPE = factory

    def __init__(self, description='A buff that will get added to the subject when running the interaction if the tests succeeds.', **kwargs):
        super().__init__(subject=TunableEnumFlags(ParticipantType, ParticipantType.Actor, description='Who will receive the buff.'), tests=event_testing.tests.TunableTestSet(), buff_type=TunablePackSafeBuffReference(description='The buff type to be added to the Sim.'), verify_tunable_callback=TunableBuffElement._verify_tunable_callback, description=description, **kwargs)

class RemoveBuffLiability(Liability, HasTunableFactory):
    LIABILITY_TOKEN = 'RemoveBuffLiability'
    FACTORY_TUNABLES = {'buff_to_remove': TunablePackSafeReference(description='\n            The buff to remove on the interaction finishing.\n            ', manager=services.get_instance_manager(sims4.resources.Types.BUFF))}

    def __init__(self, interaction, buff_to_remove, **kwargs):
        super().__init__(**kwargs)
        self._sim_info = interaction.sim.sim_info
        self._buffs_to_remove = set()
        if buff_to_remove is not None:
            self._buffs_to_remove.add(buff_to_remove)

    def merge(self, interaction, key, new_liability):
        new_liability._buffs_to_remove.update(self._buffs_to_remove)
        return new_liability

    def release(self):
        for buff_type in self._buffs_to_remove:
            self._sim_info.remove_buff_by_type(buff_type)
