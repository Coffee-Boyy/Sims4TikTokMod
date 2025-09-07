from __future__ import annotationsimport servicesimport sims4.logimport telemetry_helperfrom sims4.telemetry import TelemetryWriterfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from buffs.buff import Buff
    from interactions.utils.loot import Interaction, Loot, LootAction
    from sims.sim_info import SimInfoTELEMETRY_GROUP_BUFF = 'BUFF'TELEMETRY_HOOK_ADD_BUFF = 'BADD'TELEMETRY_HOOK_REMOVE_BUFF = 'BRMV'TELEMETRY_FIELD_BUFF_ID = 'idbf'TELEMETRY_FIELD_BUFF_SOURCE_ID = 'scbf'buff_telemetry_writer = TelemetryWriter(TELEMETRY_GROUP_BUFF)logger = sims4.log.Logger('BuffTelemetry', default_owner='jdimailig')
def write_buff_telemetry(hook_tag:'str', buff:'Buff', sim:'SimInfo', buff_source:'Union[Interaction, Loot, LootAction]'=None) -> 'None':
    if not sim.is_simulating:
        return
    current_zone = services.current_zone()
    if current_zone is None or not current_zone.is_zone_running:
        return
    logger.debug('{}: buff:{}', hook_tag, buff.buff_type)
    with telemetry_helper.begin_hook(buff_telemetry_writer, hook_tag, sim=sim) as hook:
        hook.write_int(TELEMETRY_FIELD_BUFF_ID, buff.buff_type.guid64)
        if buff_source:
            hook.write_int(TELEMETRY_FIELD_BUFF_SOURCE_ID, buff_source.guid64)
