import servicesfrom balloon.passive_balloons import PassiveBalloonsfrom server_commands.argument_helpers import OptionalSimInfoParam, get_optional_targetfrom sims4.commands import Commandfrom typing import Optional
@Command('balloons.trigger_passive_balloon')
def trigger_passive_balloon(opt_sim:OptionalSimInfoParam=None, _connection=None) -> Optional[bool]:
    sim_info = get_optional_target(opt_sim, target_type=OptionalSimInfoParam, _connection=_connection)
    PassiveBalloons.request_passive_balloon(sim_info.get_sim_instance(), services.time_service().sim_now)
