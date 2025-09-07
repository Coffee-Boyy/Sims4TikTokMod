"""
TikTok Gift Notifications for Sims 4
Displays in-game notifications when TikTok gifts are received
"""
import time
from typing import Dict, Any

from sims4communitylib.enums.common_currency_modify_reasons import CommonCurrencyModifyReason
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_currency_utils import CommonSimCurrencyUtils
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.tiktok_bridge_client import get_bridge_client
from sims_tik_tok_mod.sim_character_creator import SimCharacterCreator

# Create a logger for this module
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokGiftNotifications')
log.enable()

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
    
    # Like accumulation settings
    LIKES_THRESHOLD = 100  # Number of likes needed to trigger simoleon reward
    LIKES_TIMEOUT = 60     # Time in seconds before accumulated likes expire
    
    # Track accumulated likes per user
    _like_accumulator: Dict[str, Dict[str, Any]] = {}
    
    @staticmethod
    def initialize() -> None:
        """Initialize the TikTok gift notification system"""
        log.info("Initializing TikTok gift notifications...")
        
        # Initialize the sim character creator
        SimCharacterCreator.initialize()
        
        # Get the bridge client and set up the callbacks
        bridge_client = get_bridge_client()
        bridge_client.set_gift_callback(TikTokGiftNotifications._handle_gift_event)
        bridge_client.set_like_callback(TikTokGiftNotifications._handle_like_event)

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
            
            log.info(f"Gift received: {user} sent {gift_name} (x{gift_count})")
            
            # Get the action for this gift
            gift_key = gift_name.lower()
            action = TikTokGiftNotifications.GIFT_ACTIONS.get(gift_key, 
                     TikTokGiftNotifications.GIFT_ACTIONS['default'])
            
            # Create the notification title and description
            title = "TikTok Gift Received!"
            
            if gift_count > 1:
                description = f"{user} sent {gift_count} x {gift_name}!\n{action}"
            else:
                description = f"{user} sent {gift_name}!\n{action}"
                
            if diamond_count > 0:
                description += f"\nWorth {diamond_count} diamonds"
            
            # Show the notification in-game (disabled - only showing sim spawned notifications)
            # TikTokGiftNotifications._show_gift_notification(title, description)
            
            # Process gift data for sim character creation
            SimCharacterCreator.process_gift_data(gift_data)
            
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
            log.error(f"Error handling gift event: {e}")
            
    @staticmethod
    def _handle_like_event(like_data: Dict[str, Any]) -> None:
        """Handle a like event from the TikTok bridge"""
        try:
            user = like_data.get('user', 'Unknown')
            like_count = like_data.get('likeCount', 1)
            
            log.info(f"Like received: {user} liked (total: {like_count})")
            
            # Clean up expired likes first
            TikTokGiftNotifications._cleanup_expired_likes()
            
            # Accumulate likes for this user
            TikTokGiftNotifications._accumulate_likes(user, like_count)
            
        except Exception as e:
            log.error(f"Error handling like event: {e}")
            
    @staticmethod
    def _show_gift_notification(title: str, description: str) -> None:
        """Show a gift notification in-game"""
        try:
            notification = CommonBasicNotification(
                title,
                description
            )
            notification.show()
            log.debug(f"[TikTokGiftNotifications] Showed notification: {title}")
            
        except Exception as e:
            log.error(f"Error showing gift notification: {e}")
            
    @staticmethod
    def _accumulate_likes(user: str, like_count: int) -> None:
        """Accumulate likes for a user and trigger reward when threshold is reached"""
        try:
            current_time = time.time()
            
            # Initialize user data if not exists
            if user not in TikTokGiftNotifications._like_accumulator:
                TikTokGiftNotifications._like_accumulator[user] = {
                    'total_likes': 0,
                    'first_like_time': current_time,
                    'last_like_time': current_time
                }
            
            user_data = TikTokGiftNotifications._like_accumulator[user]
            
            # Add likes to accumulator
            user_data['total_likes'] += like_count
            user_data['last_like_time'] = current_time
            
            log.info(f"[TikTokGiftNotifications] User {user} now has {user_data['total_likes']} accumulated likes")
            
            # Check if we should trigger a reward
            TikTokGiftNotifications._check_and_trigger_like_reward(user, user_data)
            
        except Exception as e:
            log.error(f"Error accumulating likes: {e}")
            
    @staticmethod
    def _check_and_trigger_like_reward(user: str, user_data: Dict[str, Any]) -> None:
        """Check if user has reached threshold or timeout and trigger reward"""
        try:
            current_time = time.time()
            total_likes = user_data['total_likes']
            time_since_first = current_time - user_data['first_like_time']
            
            # Check if threshold reached or timeout elapsed
            should_trigger = (total_likes >= TikTokGiftNotifications.LIKES_THRESHOLD or 
                            time_since_first >= TikTokGiftNotifications.LIKES_TIMEOUT)
            
            if should_trigger:
                # Trigger reward
                TikTokGiftNotifications._trigger_like_reward(user, total_likes)
                
                # Reset accumulator for this user
                del TikTokGiftNotifications._like_accumulator[user]
                
        except Exception as e:
            log.error(f"Error checking like reward trigger: {e}")
            
    @staticmethod
    def _trigger_like_reward(user: str, total_likes: int) -> None:
        """Trigger the simoleon reward for accumulated likes"""
        try:
            # Add simoleons (1 per like)
            TikTokGiftNotifications._add_simoleons_for_like(total_likes)
            
            # Create and show notification
            title = "TikTok Like Milestone!"
            description = f"{user} reached {total_likes} likes!\nAdded §{total_likes} to household funds!"
            
            # TikTokGiftNotifications._show_gift_notification(title, description)  # Disabled - only showing sim spawned notifications
            
            log.info(f"[TikTokGiftNotifications] Triggered reward for {user}: {total_likes} likes = §{total_likes}")
            
        except Exception as e:
            log.error(f"Error triggering like reward: {e}")
            
    @staticmethod
    def _add_simoleons_for_like(like_count: int) -> None:
        """Add simoleons to the active household for TikTok likes"""
        try:
            # Get the active sim
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if active_sim_info is None:
                log.error("No active sim found, cannot add simoleons for like")
                return
                
            # Add 1 simoleon per like
            amount_to_add = like_count
            result = CommonSimCurrencyUtils.add_simoleons_to_household(
                active_sim_info, 
                amount_to_add, 
                CommonCurrencyModifyReason.EVENT_REWARD
            )
            
            if result:
                log.info(f"[TikTokGiftNotifications] Added §{amount_to_add} to household funds for {like_count} like(s)")
            else:
                log.error(f"[TikTokGiftNotifications] Failed to add simoleons: {result.reason}")
                
        except Exception as e:
            log.error(f"Error adding simoleons for like: {e}")
            
    @staticmethod
    def _cleanup_expired_likes() -> None:
        """Clean up expired like accumulations"""
        try:
            current_time = time.time()
            expired_users = []
            
            for user, user_data in TikTokGiftNotifications._like_accumulator.items():
                time_since_first = current_time - user_data['first_like_time']
                if time_since_first >= TikTokGiftNotifications.LIKES_TIMEOUT:
                    expired_users.append(user)
            
            # Trigger rewards for expired users
            for user in expired_users:
                user_data = TikTokGiftNotifications._like_accumulator[user]
                total_likes = user_data['total_likes']
                if total_likes > 0:
                    TikTokGiftNotifications._trigger_like_reward(user, total_likes)
                del TikTokGiftNotifications._like_accumulator[user]
                
            if expired_users:
                log.info(f"[TikTokGiftNotifications] Cleaned up {len(expired_users)} expired like accumulations")
                
        except Exception as e:
            log.error(f"Error cleaning up expired likes: {e}")
            
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
