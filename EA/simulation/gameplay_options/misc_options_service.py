from sims4.service_manager import Service
class MiscOptionsService(Service):

    def __init__(self) -> None:
        self._restrict_npc_werewolves = False
        self._self_discovery_enabled = True
        self._automatic_death_inventory_handling_enabled = True
        self._heirloom_objects_enabled = True
        self._burglar_enabled = True
        self._cheat_sheet_enabled = False
        self._guidance_auto_enabled = True
        self._restrict_npc_fairies = False
        self._balance_system_enabled = True
        self._ailments_enabled = True

    def save_options(self, options_proto) -> None:
        options_proto.restrict_npc_werewolves = self._restrict_npc_werewolves
        options_proto.self_discovery_enabled = self._self_discovery_enabled
        options_proto.automatic_death_inventory_handling_enabled = self._automatic_death_inventory_handling_enabled
        options_proto.heirloom_objects_enabled = self._heirloom_objects_enabled
        options_proto.burglar_enabled = self._burglar_enabled
        options_proto.cheat_sheet_enabled = self._cheat_sheet_enabled
        try:
            if options_proto.guidance_auto_enabled is not None:
                options_proto.guidance_auto_enabled = self._guidance_auto_enabled
        except:
            options_proto.guidance_auto_enabled = False
        options_proto.restrict_npc_fairies = self._restrict_npc_fairies
        options_proto.balance_system_enabled = self._balance_system_enabled
        options_proto.ailments_enabled = self._ailments_enabled

    def load_options(self, options_proto) -> None:
        self._restrict_npc_werewolves = options_proto.restrict_npc_werewolves
        self._self_discovery_enabled = options_proto.self_discovery_enabled
        self._automatic_death_inventory_handling_enabled = options_proto.automatic_death_inventory_handling_enabled
        self._heirloom_objects_enabled = options_proto.heirloom_objects_enabled
        self._burglar_enabled = options_proto.burglar_enabled
        self._cheat_sheet_enabled = options_proto.cheat_sheet_enabled
        self._restrict_npc_fairies = options_proto.restrict_npc_fairies
        self._balance_system_enabled = options_proto.balance_system_enabled
        self._ailments_enabled = options_proto.ailments_enabled
        try:
            if options_proto.guidance_auto_enabled is not None:
                self._guidance_auto_enabled = options_proto.guidance_auto_enabled
        except:
            self._guidance_auto_enabled = False

    @property
    def restrict_npc_werewolves(self) -> bool:
        return self._restrict_npc_werewolves

    def set_restrict_npc_werewolves(self, enabled:bool) -> None:
        self._restrict_npc_werewolves = enabled

    @property
    def restrict_npc_fairies(self) -> bool:
        return self._restrict_npc_fairies

    def set_restrict_npc_fairies(self, enabled:bool) -> None:
        self._restrict_npc_fairies = enabled

    @property
    def self_discovery_enabled(self) -> bool:
        return self._self_discovery_enabled

    def set_self_discovery_enabled(self, enabled:bool) -> None:
        self._self_discovery_enabled = enabled

    @property
    def automatic_death_inventory_handling_enabled(self) -> bool:
        return self._automatic_death_inventory_handling_enabled

    def set_automatic_death_inventory_handling_enabled(self, enabled:bool) -> None:
        self._automatic_death_inventory_handling_enabled = enabled

    @property
    def heirloom_objects_enabled(self) -> bool:
        return self._heirloom_objects_enabled

    def set_heirloom_objects_enabled(self, enabled:bool) -> None:
        self._heirloom_objects_enabled = enabled

    def set_burglar_enabled(self, enabled:bool) -> None:
        self._burglar_enabled = enabled

    def cheat_sheet_enabled(self) -> bool:
        return self._cheat_sheet_enabled

    def set_cheat_sheet_enabled(self, enabled:bool):
        self._cheat_sheet_enabled = enabled

    def guidance_auto_enabled(self) -> bool:
        return self._guidance_auto_enabled

    def set_guidance_auto_enabled(self, enabled:bool):
        self._guidance_auto_enabled = enabled

    @property
    def balance_system_enabled(self) -> bool:
        return self._balance_system_enabled

    def set_balance_system_enabled(self, enabled:bool) -> None:
        self._balance_system_enabled = enabled

    @property
    def ailments_enabled(self) -> bool:
        return self._ailments_enabled

    def set_ailments_enabled(self, enabled:bool) -> None:
        self._ailments_enabled = enabled
