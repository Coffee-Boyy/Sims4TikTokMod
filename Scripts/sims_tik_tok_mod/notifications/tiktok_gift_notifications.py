"""
TikTok Gift Notifications for Sims 4
Displays in-game notifications when TikTok gifts are received
"""
from typing import Dict, Any

from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.tiktok_bridge_client import get_bridge_client

# Create a logger for this module
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokGiftNotifications')


class TikTokGiftNotifications:
    """Handles TikTok gift notifications in Sims 4"""
    
    # Gift mappings - you can customize these actions
    GIFT_ACTIONS = {
        'rose': '💐 Added §500 to household funds!',
        'popular vote': '🗳️ Popularity boost!',
        'go popular': '🗳️ Popularity boost!',
        'heart': '❤️ Applied Happy buff for 4 hours!',
        'gg': '💥 Something broke in the house!',
        'diamond': '💎 Added §1000 to household funds!',
        'rocket': '🚀 House is on fire!',
        'lion': '🦁 Celebrity spotted!',
        'default': '🎁 Thank you for the gift!'
    }
    
    @staticmethod
    def initialize() -> None:
        """Initialize the TikTok gift notification system"""
        log.info("Initializing TikTok gift notifications...")
        
        # Get the bridge client and set up the gift callback
        bridge_client = get_bridge_client()
        bridge_client.set_gift_callback(TikTokGiftNotifications._handle_gift_event)
        
        # Start the bridge client
        if bridge_client.start():
            log.info("✅ TikTok bridge client started successfully")
        else:
            log.error("❌ Failed to start TikTok bridge client")
            
    @staticmethod
    def shutdown() -> None:
        """Shutdown the TikTok gift notification system"""
        log.info("Shutting down TikTok gift notifications...")
        bridge_client = get_bridge_client()
        bridge_client.stop()
        
    @staticmethod
    def _handle_gift_event(gift_data: Dict[str, Any]) -> None:
        """Handle a gift event from the TikTok bridge"""
        try:
            user = gift_data.get('user', 'Unknown')
            gift_name = gift_data.get('giftDisplayName', gift_data.get('gift', 'Unknown'))
            gift_count = gift_data.get('value', 1)
            diamond_count = gift_data.get('diamondCount', 0)
            
            log.info(f"🎁 Gift received: {user} sent {gift_name} (x{gift_count})")
            
            # Get the action for this gift
            gift_key = gift_name.lower()
            action = TikTokGiftNotifications.GIFT_ACTIONS.get(gift_key, 
                     TikTokGiftNotifications.GIFT_ACTIONS['default'])
            
            # Create the notification title and description
            title = "🎁 TikTok Gift Received!"
            
            if gift_count > 1:
                description = f"{user} sent {gift_count} x {gift_name}!\n{action}"
            else:
                description = f"{user} sent {gift_name}!\n{action}"
                
            if diamond_count > 0:
                description += f"\n💎 Worth {diamond_count} diamonds"
            
            # Show the notification in-game
            TikTokGiftNotifications._show_gift_notification(title, description)
            
            # Send response back to bridge (optional)
            bridge_client = get_bridge_client()
            bridge_client.send_response(gift_data, action)
            
            # TODO: Here you can add actual game effects based on the gift
            # For example:
            # - Add money to household funds
            # - Apply buffs to Sims
            # - Trigger events in the game
            # TikTokGiftNotifications._apply_gift_effect(gift_key, gift_count)
            
        except Exception as e:
            log.exception(f"Error handling gift event: {e}")
            
    @staticmethod
    def _show_gift_notification(title: str, description: str) -> None:
        """Show a gift notification in-game"""
        try:
            notification = CommonBasicNotification(
                title,
                description
            )
            notification.show()
            log.debug(f"Showed notification: {title}")
            
        except Exception as e:
            log.exception(f"Error showing gift notification: {e}")
            
    @staticmethod
    def _apply_gift_effect(gift_key: str, count: int) -> None:
        """Apply the actual game effect for a gift (to be implemented)"""
        # TODO: Implement actual game effects here
        # This is where you would add money, apply buffs, break objects, etc.
        
        log.info(f"TODO: Apply effect for gift '{gift_key}' x{count}")
        
        # Example implementations:
        # if gift_key == 'rose':
        #     # Add money to household
        #     active_household = CommonHouseholdUtils.get_active_household()
        #     if active_household:
        #         active_household.funds.add(500 * count)
        #         
        # elif gift_key == 'heart':
        #     # Apply happy buff to active sim
        #     active_sim = CommonSimUtils.get_active_sim()
        #     if active_sim:
        #         # Add happy buff (you'd need to find the correct buff ID)
        #         pass
        #         
        # elif gift_key == 'gg':
        #     # Break a random object in the house
        #     # Find objects and set them to broken state
        #     pass
