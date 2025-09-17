"""
TikTok Gift Notifications for Sims 4
Displays in-game notifications when TikTok gifts are received
"""
from typing import Dict, Any
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.tiktok_bridge_client import get_bridge_client
from sims_tik_tok_mod.tiktok_effect_mappings import TikTokEffectMappings

log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokActionNotifications')  # type: ignore[attr-defined]
log.enable()

class TikTokActionNotifications:
    """Handles TikTok action notifications in Sims 4"""

    @staticmethod
    def initialize() -> None:
        """Initialize the TikTok gift notification system"""
        log.info("Initializing TikTok gift notifications...")
        
        # Get the bridge client and set up the callbacks
        bridge_client = get_bridge_client()
        bridge_client.set_action_callback(TikTokActionNotifications._handle_action_event)
        bridge_client.set_connection_callback(TikTokActionNotifications._handle_connection_event)

        # Start the bridge client
        bridge_client.start()
            
    @staticmethod
    def shutdown() -> None:
        """Shutdown the TikTok gift notification system"""
        log.info("Shutting down TikTok gift notifications...")
        bridge_client = get_bridge_client()
        bridge_client.stop()
        
    @staticmethod
    def _handle_action_event(action_data: Dict[str, Any]) -> None:
        """Handle a Sims action event from the TikTok bridge"""
        try:
            user = action_data.get('user', 'Unknown')
            user_nickname = action_data.get('userNickname', 'Unknown')
            action = action_data.get('action', 'unknown')
            count = action_data.get('count', 1)
            context = action_data.get('context', {})
            
            # Extract gift context for logging and notifications
            gift_name = context.get('giftName', 'Unknown Gift')
            diamond_count = context.get('diamondCount', 0)
            is_manual = context.get('isManual', False)
            
            log.info(f"Sims action received: {user} -> {action} (from {gift_name}, x{count})")
            
            # Get the action description for notifications
            action_description = TikTokEffectMappings.ACTION_DESCRIPTIONS.get(action, TikTokEffectMappings.ACTION_DESCRIPTIONS['default'])
            
            # Create the notification title and description
            title = f"TikTok Gift from {user_nickname} ({user})"
            
            # Streamlined description - just the effect
            description = action_description
            
            # Add test indicator if manual
            if is_manual:
                description += " (Test)"
            
            TikTokActionNotifications._show_gift_notification(title, description)
            
            # Send response back to bridge (optional)
            bridge_client = get_bridge_client()
            bridge_client.send_response(action_data, action_description)
            
            # Apply the actual game effect based on the action
            TikTokEffectMappings.apply_action_effect(user_nickname, action, count, context)
            
        except Exception as e:
            log.error(f"Error handling Sims action event: {e}")
            
            
    @staticmethod
    def _handle_connection_event(is_connected: bool, message: str) -> None:
        """Handle connection status change events from the TikTok bridge"""
        try:
            if is_connected:
                title = "TikTok Bridge Connected"
                description = "Successfully connected to TikTok service! Ready to receive gifts and interactions from your stream."
                log.info(f"TikTok bridge connected: {message}")
            else:
                title = "TikTok Bridge Connection Failed"
                # Use the specific error message from the bridge client, with a fallback
                if "Make sure the bridge application is running" in message:
                    description = f"{message} Start the bridge application and try again."
                elif "bridge service" in message.lower():
                    description = message
                else:
                    description = f"{message} Check the bridge service and try again."
                log.error(f"TikTok bridge connection failed: {message}")
            
            # Show the connection notification in-game
            TikTokActionNotifications._show_connection_notification(title, description)
            
        except Exception as e:
            log.error(f"Error handling connection event: {e}")
            
    @staticmethod
    def _show_gift_notification(title: str, description: str) -> None:
        """Show a gift notification in-game"""
        try:
            notification = CommonBasicNotification(
                title,
                description
            )
            notification.show()
            log.debug(f"[TikTokActionNotifications] Showed notification: {title}")
            
        except Exception as e:
            log.error(f"Error showing gift notification: {e}")

    @staticmethod
    def _show_connection_notification(title: str, description: str) -> None:
        """Show a connection status notification in-game"""
        try:
            notification = CommonBasicNotification(
                title,
                description
            )
            notification.show()
            log.debug(f"[TikTokActionNotifications] Showed connection notification: {title}")
            
        except Exception as e:
            log.error(f"Error showing connection notification: {e}")
