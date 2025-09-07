import servicesimport sims4from event_testing.resolver import SingleSimResolverfrom interactions import ParticipantTypefrom luck.luck_config import LuckConfigfrom luck.luck_service import LuckOption, LuckServicefrom luck.luck_tuning import LuckTuningfrom server_commands.argument_helpers import OptionalSimInfoParam, get_optional_targetfrom sims4.commands import Command, output, automation_output, CommandTypefrom sims4.math import interpolatefrom typing import Optional
@Command('luck.set_luck_enabled', command_type=sims4.commands.CommandType.Live)
def set_luck_enabled(enabled:bool=False, _connection=None) -> Optional[bool]:
    luck_service = services.get_luck_service()
    if luck_service is None:
        return
    luck_service._set_luck_enabled(enabled)

@Command('luck.get_luck', command_type=sims4.commands.CommandType.Automation)
def get_luck(opt_sim:OptionalSimInfoParam=None, _connection=None) -> Optional[bool]:
    sim_info = get_optional_target(opt_sim, target_type=OptionalSimInfoParam, _connection=_connection)
    luck_tracker = sim_info.luck_tracker
    if luck_tracker is None:
        return
    packed_result = luck_tracker._debug_get_luck_value_breakdown()
    luck_level = luck_tracker.try_get_luck_level()
    if luck_level is None or packed_result is None:
        return
    (base_luck_value, luck_modifier, total_luck) = packed_result
    luck_level_index = LuckTuning.LUCK_LEVELS.index(luck_level)
    msg = f'Base Luck value: {base_luck_value}
Luck modifier: {luck_modifier}
Total Luck value: {total_luck}
Luck level index: {luck_level_index}
Luck level tuning: {repr(luck_level())}'
    automation_output(msg, _connection)
    output(msg, _connection)

@Command('luck.refresh_luck')
def refresh_luck(opt_sim:OptionalSimInfoParam=None, _connection=None) -> Optional[bool]:
    sim_info = get_optional_target(opt_sim, target_type=OptionalSimInfoParam, _connection=_connection)
    luck_tracker = sim_info.luck_tracker
    if luck_tracker is None:
        return
    luck_tracker.refresh_luck_value()

@Command('luck.set_luck')
def set_luck(luck_value:float, opt_sim:OptionalSimInfoParam=None, _connection=None) -> Optional[bool]:
    sim_info = get_optional_target(opt_sim, target_type=OptionalSimInfoParam, _connection=_connection)
    luck_tracker = sim_info.luck_tracker
    if luck_tracker is None:
        return
    luck_tracker._debug_force_luck_value(luck_value)

@Command('luck.test_luck', command_type=CommandType.DebugOnly)
def test_luck(opt_sim:OptionalSimInfoParam=None, _connection=None) -> Optional[bool]:
    sim_info = get_optional_target(opt_sim, target_type=OptionalSimInfoParam, _connection=_connection)
    luck_service = services.get_luck_service()
    if luck_service is None:
        return
    options = []
    for i in range(-100, 110, 10):
        option = LuckOption(weight=1, perceived_value=i, user_data=i)
        output(f'Item: {option}', _connection)
        options.append(option)
    result = luck_service.choose_with_luck('debug', options, SingleSimResolver(sim_info), LuckConfig(participant=ParticipantType.Actor))
    output(f'Result: {result}', _connection)

@Command('luck.test_weights', command_type=CommandType.DebugOnly)
def test_weights(_connection=None) -> Optional[bool]:
    options = []
    for i in range(-100, 110, 10):
        option = LuckOption(weight=1, perceived_value=i, user_data=i)
        options.append(option)
    for luck_level in LuckTuning.LUCK_LEVELS:
        output(f'Luck level: {luck_level()}', _connection)
        weights = LuckService._get_weights_for_luck_level(options, luck_level)
        for (index, weight) in enumerate(weights):
            output(f'	Weight for item ({options[index]}): {weight}', _connection)
