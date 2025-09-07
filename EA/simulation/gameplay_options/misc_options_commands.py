import servicesimport sims4from event_testing.game_option_tests import TestableGameOptionsfrom event_testing.test_events import TestEventfrom sims4.common import Pack
@sims4.commands.Command('misc_options.restrict_npc_werewolves', pack=Pack.GP12, command_type=sims4.commands.CommandType.Live)
def restrict_npc_werewolves(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_restrict_npc_werewolves(enabled)
    services.get_event_manager().process_event(TestEvent.TestedGameOptionChanged, custom_keys=(TestableGameOptions.RESTRICT_NPC_WEREWOLVES,))
    return True

@sims4.commands.Command('misc_options.restrict_npc_fairies', pack=Pack.EP19, command_type=sims4.commands.CommandType.Live)
def restrict_npc_fairies(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_restrict_npc_fairies(enabled)
    services.get_event_manager().process_event(TestEvent.TestedGameOptionChanged, custom_keys=(TestableGameOptions.RESTRICT_NPC_FAIRIES,))
    return True

@sims4.commands.Command('misc_options.self_discovery_enabled', pack=Pack.EP13, command_type=sims4.commands.CommandType.Live)
def self_discovery_enabled(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_self_discovery_enabled(enabled)
    services.get_event_manager().process_event(TestEvent.TestedGameOptionChanged, custom_keys=(TestableGameOptions.SELF_DISCOVERY_ENABLED,))
    return True

@sims4.commands.Command('misc_options.automatic_death_inventory_handling_enabled', command_type=sims4.commands.CommandType.Live)
def automatic_death_inventory_handling_enabled(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_automatic_death_inventory_handling_enabled(enabled)
    return True

@sims4.commands.Command('misc_options.heirloom_objects_enabled', pack=Pack.EP17, command_type=sims4.commands.CommandType.Live)
def heirloom_objects_enabled(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_heirloom_objects_enabled(enabled)
    return True

@sims4.commands.Command('burglar.set_burglar_enabled', command_type=sims4.commands.CommandType.Live)
def set_burglar_enabled(enabled:bool=True, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_burglar_enabled(enabled)
    services.get_event_manager().process_event(TestEvent.TestedGameOptionChanged, custom_keys=(TestableGameOptions.BURGLAR_ENABLED,))
    return True

@sims4.commands.Command('misc_options.guidance_auto_enabled', command_type=sims4.commands.CommandType.Live)
def set_guidance_auto_enabled(enabled:bool=True, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_guidance_auto_enabled(enabled)
    tutorial_service = services.get_tutorial_service()
    if tutorial_service is None:
        return False
    tutorial_service.set_guidance_auto_enabled(enabled)
    return True

@sims4.commands.Command('misc_options.set_balance_system_enabled', pack=Pack.EP19, command_type=sims4.commands.CommandType.Live)
def set_balance_system_enabled(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_balance_system_enabled(enabled)
    services.get_event_manager().process_event(TestEvent.TestedGameOptionChanged, custom_keys=(TestableGameOptions.BALANCE_SYSTEM_ENABLED,))
    return True

@sims4.commands.Command('misc_options.set_ailments_enabled', pack=Pack.EP19, command_type=sims4.commands.CommandType.Live)
def set_ailments_enabled(enabled:bool=False, _connection=None):
    misc_options_service = services.misc_options_service()
    if misc_options_service is None:
        return False
    misc_options_service.set_ailments_enabled(enabled)
    services.get_event_manager().process_event(TestEvent.TestedGameOptionChanged, custom_keys=(TestableGameOptions.AILMENTS_ENABLED,))
    return True
