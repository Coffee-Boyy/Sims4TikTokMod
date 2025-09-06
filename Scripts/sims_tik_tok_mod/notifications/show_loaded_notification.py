from sims_tik_tok_mod.enums.string_enums import S4CLSampleModStringId
from sims4communitylib.events.event_handling.common_event_registry import CommonEventRegistry
from sims4communitylib.events.zone_spin.events.zone_late_load import S4CLZoneLateLoadEvent
from sims4communitylib.events.zone_spin.events.zone_early_load import S4CLZoneEarlyLoadEvent
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.notifications.tiktok_gift_notifications import TikTokGiftNotifications


class S4CLSampleModShowLoadedMessage:
    """ A class that listens for a zone load event and shows a notification upon loading into a household. """
    @staticmethod
    def show_loaded_notification() -> None:
        """ Show that the sample mod has loaded. """
        notification = CommonBasicNotification(
            "🎮 Sims 4 TikTok Mod",
            "Mod loaded! Connecting to TikTok bridge..."
        )
        notification.show()

    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def _show_loaded_notification_when_loaded(event_data: S4CLZoneLateLoadEvent) -> bool:
        if event_data.game_loaded:
            # If the game has not loaded yet, we don't want to show our notification.
            return False
        S4CLSampleModShowLoadedMessage.show_loaded_notification()
        
        # Initialize TikTok gift notifications
        TikTokGiftNotifications.initialize()
        
        return True
        
    @staticmethod
    @CommonEventRegistry.handle_events(ModInfo.get_identity().name)
    def _shutdown_tiktok_bridge(event_data: S4CLZoneEarlyLoadEvent) -> bool:
        """ Shutdown TikTok bridge when leaving a zone """
        TikTokGiftNotifications.shutdown()
        return True
