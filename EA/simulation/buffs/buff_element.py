from buffs.tunable import TunablePackSafeBuffReferencefrom event_testing.resolver import InteractionResolverfrom event_testing.tests import TunableTestSetfrom interactions import ParticipantTypeSimfrom interactions.utils.interaction_elements import XevtTriggeredElementimport sims4.logfrom sims4.tuning.tunable import TunableEnumEntrylogger = sims4.log.Logger('Buffs')
class BuffFireAndForgetElement(XevtTriggeredElement):

    @staticmethod
    def _verify_tunable_callback(cls, tunable_name, source, buff, participant, success_chance, timing, tests):
        if buff.buff_type is None:
            return
        if buff.buff_type._temporary_commodity_info is None:
            logger.error('BuffFireAndForgetElement: {} has a buff element with a buff {} without a temporary commodity tuned.', cls, buff.buff_type)

    FACTORY_TUNABLES = {'buff': TunablePackSafeBuffReference(description='\n            A buff to be added to the Sim.\n            '), 'participant': TunableEnumEntry(description='\n            The Sim(s) to give the buff to.\n            ', tunable_type=ParticipantTypeSim, default=ParticipantTypeSim.Actor), 'tests': TunableTestSet(description='\n            Tests to verify if this buff should be added to the sim.\n            '), 'verify_tunable_callback': _verify_tunable_callback}

    def _do_behavior(self, *args, **kwargs):
        if self.buff.buff_type is None:
            return
        participants = self.interaction.get_participants(self.participant)
        if not participants:
            logger.error('Got empty participants trying to run a BuffFireAndForgetElement element. Buff: {} Participant:{}', self, self.participant)
        resolver = self.interaction.get_resolver()
        if self.tests.run_tests(resolver):
            for participant in participants:
                participant.add_buff_from_op(self.buff.buff_type, buff_reason=self.buff.buff_reason, buff_source=self.buff.buff_source)
