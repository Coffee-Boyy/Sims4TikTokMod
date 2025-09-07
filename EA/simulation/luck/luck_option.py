from luck.luck_tuning import LuckTuningfrom sims4.tuning.tunable import TunableTuple, TunableRange, Tunable
class TunableLuckOptionData(TunableTuple):

    def __init__(self, description='The luck specific data for this option.', **kwargs):
        super().__init__(description=description, player_perception=TunableRange(description=f'
                The player's perception of the option,
                from {LuckTuning.PERCEPTION_RANGE.lower_bound} to {LuckTuning.PERCEPTION_RANGE.upper_bound}. For example, if a sim
                is fishing, pulling up a boot would be
                seen as {LuckTuning.PERCEPTION_RANGE.lower_bound}, while pulling up a treasure
                chest would be seen as {LuckTuning.PERCEPTION_RANGE.upper_bound}.
                ', tunable_type=float, default=0, minimum=LuckTuning.PERCEPTION_RANGE.lower_bound, maximum=LuckTuning.PERCEPTION_RANGE.upper_bound), show_impacts=Tunable(description='\n                If luck influences the selection process and selects this option,\n                and this bool is True, then we will telegraph that impact to the player.\n                An example of when to turn this off is for "do nothing" options, where\n                we don\'t want the game to say "luck chose something!" but nothing\n                visibly happened for the player.\n                ', tunable_type=bool, default=True), **kwargs)
