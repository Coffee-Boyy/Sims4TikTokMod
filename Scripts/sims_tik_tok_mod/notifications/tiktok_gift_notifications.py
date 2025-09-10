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
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokActionNotifications')
log.enable()

class TikTokActionNotifications:
    """Handles TikTok action notifications in Sims 4"""
    
    # Action mappings - you can customize these actions
    ACTION_DESCRIPTIONS = {
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
        bridge_client.set_action_callback(TikTokActionNotifications._handle_action_event)
        bridge_client.set_like_callback(TikTokActionNotifications._handle_like_event)

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
    def _handle_action_event(action_data: Dict[str, Any]) -> None:
        """Handle a Sims action event from the TikTok bridge"""
        try:
            user = action_data.get('user', 'Unknown')
            action = action_data.get('action', 'unknown')
            count = action_data.get('count', 1)
            context = action_data.get('context', {})
            
            # Extract gift context for logging and notifications
            gift_name = context.get('giftName', 'Unknown Gift')
            diamond_count = context.get('diamondCount', 0)
            is_manual = context.get('isManual', False)
            
            log.info(f"Sims action received: {user} -> {action} (from {gift_name}, x{count})")
            
            # Handle sim creation action
            if action == 'create_sim':
                SimCharacterCreator.process_gift_data(action_data)
                return
            
            # Get the action description for notifications
            action_description = TikTokActionNotifications.ACTION_DESCRIPTIONS.get(action, 
                                TikTokActionNotifications.ACTION_DESCRIPTIONS['default'])
            
            # Create the notification title and description
            title = "TikTok Action Triggered!"
            
            if count > 1:
                description = f"{user} triggered {count} x {action}!\n{action_description}"
            else:
                description = f"{user} triggered {action}!\n{action_description}"
                
            if diamond_count > 0:
                description += f"\nFrom {gift_name} ({diamond_count} diamonds)"
            elif gift_name != 'Unknown Gift':
                description += f"\nFrom {gift_name}"
                
            if is_manual:
                description += "\n(Manual test)"
            
            # Show the notification in-game (disabled - only showing sim spawned notifications)
            # TikTokActionNotifications._show_gift_notification(title, description)
            
            # Send response back to bridge (optional)
            bridge_client = get_bridge_client()
            bridge_client.send_response(action_data, action_description)
            
            # Apply the actual game effect based on the action
            TikTokActionNotifications._apply_action_effect(action, count, context)
            
        except Exception as e:
            log.error(f"Error handling Sims action event: {e}")
            
    @staticmethod
    def _handle_like_event(like_data: Dict[str, Any]) -> None:
        """Handle a like event from the TikTok bridge"""
        try:
            user = like_data.get('user', 'Unknown')
            like_count = like_data.get('likeCount', 1)
            
            log.info(f"Like received: {user} liked (total: {like_count})")
            
            # Clean up expired likes first
            TikTokActionNotifications._cleanup_expired_likes()
            
            # Accumulate likes for this user
            TikTokActionNotifications._accumulate_likes(user, like_count)
            
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
            log.debug(f"[TikTokActionNotifications] Showed notification: {title}")
            
        except Exception as e:
            log.error(f"Error showing gift notification: {e}")
            
    @staticmethod
    def _accumulate_likes(user: str, like_count: int) -> None:
        """Accumulate likes for a user and trigger reward when threshold is reached"""
        try:
            current_time = time.time()
            
            # Initialize user data if not exists
            if user not in TikTokActionNotifications._like_accumulator:
                TikTokActionNotifications._like_accumulator[user] = {
                    'total_likes': 0,
                    'first_like_time': current_time,
                    'last_like_time': current_time
                }
            
            user_data = TikTokActionNotifications._like_accumulator[user]
            
            # Add likes to accumulator
            user_data['total_likes'] += like_count
            user_data['last_like_time'] = current_time
            
            log.info(f"[TikTokActionNotifications] User {user} now has {user_data['total_likes']} accumulated likes")
            
            # Check if we should trigger a reward
            TikTokActionNotifications._check_and_trigger_like_reward(user, user_data)
            
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
            should_trigger = (total_likes >= TikTokActionNotifications.LIKES_THRESHOLD or 
                            time_since_first >= TikTokActionNotifications.LIKES_TIMEOUT)
            
            if should_trigger:
                # Trigger reward
                TikTokActionNotifications._trigger_like_reward(user, total_likes)
                
                # Reset accumulator for this user
                del TikTokActionNotifications._like_accumulator[user]
                
        except Exception as e:
            log.error(f"Error checking like reward trigger: {e}")
            
    @staticmethod
    def _trigger_like_reward(user: str, total_likes: int) -> None:
        """Trigger the simoleon reward for accumulated likes"""
        try:
            # Add simoleons (1 per like)
            TikTokActionNotifications._add_simoleons_for_like(total_likes)
            
            # Create and show notification
            title = "TikTok Like Milestone!"
            description = f"{user} reached {total_likes} likes!\nAdded §{total_likes} to household funds!"
            
            # TikTokActionNotifications._show_gift_notification(title, description)  # Disabled - only showing sim spawned notifications
            
            log.info(f"[TikTokActionNotifications] Triggered reward for {user}: {total_likes} likes = §{total_likes}")
            
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
                log.info(f"[TikTokActionNotifications] Added §{amount_to_add} to household funds for {like_count} like(s)")
            else:
                log.error(f"[TikTokActionNotifications] Failed to add simoleons: {result.reason}")
                
        except Exception as e:
            log.error(f"Error adding simoleons for like: {e}")
            
    @staticmethod
    def _cleanup_expired_likes() -> None:
        """Clean up expired like accumulations"""
        try:
            current_time = time.time()
            expired_users = []
            
            for user, user_data in TikTokActionNotifications._like_accumulator.items():
                time_since_first = current_time - user_data['first_like_time']
                if time_since_first >= TikTokActionNotifications.LIKES_TIMEOUT:
                    expired_users.append(user)
            
            # Trigger rewards for expired users
            for user in expired_users:
                user_data = TikTokActionNotifications._like_accumulator[user]
                total_likes = user_data['total_likes']
                if total_likes > 0:
                    TikTokActionNotifications._trigger_like_reward(user, total_likes)
                del TikTokActionNotifications._like_accumulator[user]
                
            if expired_users:
                log.info(f"[TikTokActionNotifications] Cleaned up {len(expired_users)} expired like accumulations")
                
        except Exception as e:
            log.error(f"Error cleaning up expired likes: {e}")

    @staticmethod
    def _apply_action_effect(action: str, count: int, context: Dict[str, Any]) -> None:
        """Apply the actual game effect for a Sims action"""
        # TODO: Implement actual game effects here based on the action
        # This is where you would add money, apply buffs, break objects, etc.
        
        log.info(f"TODO: Apply effect for action '{action}' x{count}")
        
        # Example implementations:
        # if action == 'flirt':
        #     # Apply flirty buff to all sims in household
        #     for sim in CommonSimUtils.get_sim_instances_for_household():
        #         CommonBuffUtils.add_buff(sim, CommonBuffId.FLIRTY)
        #         log.info(f"Applied flirty buff to {sim.first_name}")
        #
        # elif action == 'give_money':
        #     # Add money to household funds
        #     active_household = CommonHouseholdUtils.get_active_household()
        #     if active_household:
        #         amount = context.get('diamondCount', 10) * 10  # 10 simoleons per diamond
        #         active_household.funds.try_add_funds(amount * count)
        #         log.info(f"Added {amount * count} simoleons")
        #
        # elif action == 'break_object':
        #     # Find and break a random object
        #     # Implementation would go here
        #     pass
        pass
