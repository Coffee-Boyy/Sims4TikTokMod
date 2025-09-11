"""
TikTok Gift Notifications for Sims 4
Displays in-game notifications when TikTok gifts are received
"""
import time
from typing import Dict, Any

from sims4communitylib.enums.buffs_enum import CommonBuffId
from sims4communitylib.enums.common_currency_modify_reasons import CommonCurrencyModifyReason
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_buff_utils import CommonBuffUtils
from sims4communitylib.utils.sims.common_household_utils import CommonHouseholdUtils
from sims4communitylib.utils.sims.common_sim_currency_utils import CommonSimCurrencyUtils
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.tiktok_bridge_client import get_bridge_client
from sims_tik_tok_mod.sim_character_creator import SimCharacterCreator

# Create a logger for this module
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokActionNotifications')  # type: ignore[attr-defined]
log.enable()

class TikTokActionNotifications:
    """Handles TikTok action notifications in Sims 4"""
    
    # Action mappings - you can customize these actions
    ACTION_DESCRIPTIONS = {
        'rose': 'Added 500 simoleons to household funds!',
        'popular vote': 'Popularity boost activated!',
        'go popular': 'Popularity boost activated!',
        'heart': 'Applied Happy buff for 4 hours!',
        'gg': 'Something broke in the house!',
        'diamond': 'Added 1000 simoleons to household funds!',
        'rocket': 'House is on fire!',
        'lion': 'Celebrity spotted!',
        'flirty_compliment': 'Applied flirty buff to all household members!',
        'show_off': 'Active Sim is showing off with confidence!',
        'romantic_hug': 'Active Sim is giving romantic hugs to nearby Sims!',
        'default': 'Thank you for the gift!'
    }
    
    
    @staticmethod
    def initialize() -> None:
        """Initialize the TikTok gift notification system"""
        log.info("Initializing TikTok gift notifications...")
        
        # Initialize the sim character creator
        SimCharacterCreator.initialize()
        
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
            title = f"TikTok Gift from {user}"
            
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
            TikTokActionNotifications._apply_action_effect(action, count, context)
            
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

    @staticmethod
    def _apply_action_effect(action: str, count: int, context: Dict[str, Any]) -> None:
        """Apply the actual game effect for a Sims action"""
        if action == 'flirty_compliment':
            # Apply flirty buff to all sims in household
            applied_count = 0
            for sim_info in CommonHouseholdUtils.get_sim_info_of_all_sims_in_active_household_generator():
                result = CommonBuffUtils.add_buff(sim_info, CommonBuffId.FLIRTY_BY_POTION, buff_reason="Flirty Compliment from TikTok")
                if result:
                    applied_count += 1
                    log.info(f"Applied flirty buff to {sim_info.first_name}")
                else:
                    log.error(f"Failed to apply flirty buff to {sim_info.first_name}: {result.reason}")
            log.info(f"Applied flirty buff to {applied_count} household member(s)")
        
        elif action == 'give_money':
            # Add money to household funds
            active_household = CommonHouseholdUtils.get_active_household()
            if active_household:
                amount = context.get('diamondCount', 10) * 10  # 10 simoleons per diamond
                active_household.funds.try_add_funds(amount * count)
                log.info(f"Added {amount * count} simoleons")
        
        elif action == 'break_object':
            # Find and break a random object
            # Implementation would go here
            pass
        
        elif action == 'show_off':
            # Apply confident buff and make the active Sim show off
            TikTokActionNotifications._apply_show_off_action(count)
        
        elif action == 'romantic_hug':
            # Make the active Sim give romantic hugs to nearby Sims
            TikTokActionNotifications._apply_romantic_hug_action(count)
        
        elif action == 'like_reward':
            # Add simoleons to household for like milestone reward
            TikTokActionNotifications._add_simoleons_for_like_reward(count, context)
        
        else:
            log.info(f"TODO: Apply effect for action '{action}' x{count}")
    
    @staticmethod
    def _apply_show_off_action(count: int) -> None:
        """Apply show off action - makes the active Sim confident and perform show-off interactions"""
        try:
            from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
            from sims4communitylib.utils.sims.common_buff_utils import CommonBuffUtils
            from sims4communitylib.enums.buffs_enum import CommonBuffId
            from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils
            
            # Get the active sim
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if not active_sim_info:
                log.error("No active sim found for show_off action")
                return
            
            # Apply confident buff to the active sim
            result = CommonBuffUtils.add_buff(active_sim_info, CommonBuffId.CONFIDENCE_HIGH_CONFIDENCE_BOOST, buff_reason="Showing off from TikTok gift")
            if result:
                log.info(f"Applied confident buff to {active_sim_info.first_name} for show off action")
            else:
                log.error(f"Failed to apply confident buff: {result.reason}")
            
            # Try to make the sim perform a confident/show-off interaction
            # Since we don't have specific show-off interactions in S4CL, we'll use confident posture and buff
            # The confident buff will make the sim naturally perform more confident animations
            
            log.info(f"Show off action applied to {active_sim_info.first_name} with confident buff")
            
        except Exception as e:
            log.error(f"Error applying show off action: {e}")
    
    @staticmethod
    def get_all_running_interaction_targets(sim_info):
        """Get all targets from the sim's currently running interactions"""
        sim = CommonSimUtils.get_sim_instance(sim_info)
        if sim is None or sim.si_state is None:
            return []
        targets = []
        for interaction in CommonSimInteractionUtils.get_running_interactions_gen(sim_info):
            targets.append(getattr(interaction, 'target', None))
        return targets

    @staticmethod
    def _apply_romantic_hug_action(count: int) -> None:
        """Apply romantic hug action - makes the active Sim give romantic hugs to nearby Sims"""
        try:
            from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
            from sims4communitylib.utils.sims.common_buff_utils import CommonBuffUtils
            from sims4communitylib.enums.buffs_enum import CommonBuffId
            from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils
            from sims4communitylib.utils.sims.common_relationship_utils import CommonRelationshipUtils
            from sims4communitylib.utils.location.common_location_utils import CommonLocationUtils
            from sims4communitylib.utils.sims.common_household_utils import CommonHouseholdUtils
            
            # Get the active sim
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if not active_sim_info:
                log.error("No active sim found for romantic_hug action")
                return
            
            # Apply flirty buff to the active sim
            result = CommonBuffUtils.add_buff(active_sim_info, CommonBuffId.FLIRTY_BY_POTION, buff_reason="Romantic mood from TikTok gift")
            if result:
                log.info(f"Applied flirty buff to {active_sim_info.first_name} for romantic hug action")
            else:
                log.error(f"Failed to apply flirty buff: {result.reason}")
            
            # Get targets from current interactions
            interaction_targets = TikTokActionNotifications.get_all_running_interaction_targets(active_sim_info)
            
            # Filter out None targets and convert to sim_info objects
            target_sims = []
            for target in interaction_targets:
                if target is not None:
                    # Check if target is a Sim
                    if hasattr(target, 'sim_info'):
                        target_sims.append(target.sim_info)
                    elif hasattr(target, 'id') and hasattr(target, 'first_name'):
                        # Target is already a sim_info
                        target_sims.append(target)
            
            # Remove duplicates and the active sim itself
            unique_targets = []
            for target_sim_info in target_sims:
                if target_sim_info != active_sim_info and target_sim_info not in unique_targets:
                    unique_targets.append(target_sim_info)
            
            if not unique_targets:
                log.info("No interaction targets found for romantic hug - applying romantic mood to active Sim only")
                return
            
            # Apply romantic interactions/buffs to interaction targets
            hugs_given = 0
            max_hugs = min(count, len(unique_targets), 1)  # Limit to prevent spam
            
            for target_sim_info in unique_targets[:max_hugs]:
                try:
                    # Apply flirty buff to target as well
                    buff_result = CommonBuffUtils.add_buff(target_sim_info, CommonBuffId.FLIRTY_BY_POTION, buff_reason="Romantic hug from TikTok gift")
                    if buff_result:
                        log.info(f"Applied romantic buff to {target_sim_info.first_name}")
                        hugs_given += 1
                    
                    # Try to improve relationship between the sims
                    try:
                        from sims4communitylib.utils.sims.common_relationship_utils import CommonRelationshipUtils
                        from sims4communitylib.enums.relationship_tracks_enum import CommonRelationshipTrackId
                        
                        # Improve romantic relationship track
                        relationship_change_result = CommonRelationshipUtils.change_relationship_level_of_sims(
                            active_sim_info, 
                            target_sim_info, 
                            CommonRelationshipTrackId.ROMANCE,  # Use the romance track
                            100.0  # Add 10 romance relationship points
                        )
                        if relationship_change_result:
                            log.info(f"Improved romantic relationship between {active_sim_info.first_name} and {target_sim_info.first_name}")
                        
                        # Also improve friendship as a base
                        friendship_result = CommonRelationshipUtils.change_relationship_level_of_sims(
                            active_sim_info,
                            target_sim_info,
                            CommonRelationshipTrackId.FRIENDSHIP,  # Use the friendship track
                            100.0  # Add 5 friendship points as well
                        )
                        if friendship_result:
                            log.info(f"Improved friendship between {active_sim_info.first_name} and {target_sim_info.first_name}")
                            
                    except Exception as rel_error:
                        log.debug(f"Could not change relationship: {rel_error}")
                    
                except Exception as e:
                    log.error(f"Error applying romantic hug to {target_sim_info.first_name}: {e}")
            
            log.info(f"Romantic hug action completed - gave {hugs_given} romantic interactions")
            
        except Exception as e:
            log.error(f"Error applying romantic hug action: {e}")
    
    @staticmethod
    def _add_simoleons_for_like_reward(like_count: int, context: Dict[str, Any]) -> None:
        """Add simoleons to the active household for TikTok like milestone reward"""
        try:
            from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
            from sims4communitylib.utils.sims.common_sim_currency_utils import CommonSimCurrencyUtils
            from sims4communitylib.enums.common_currency_modify_reasons import CommonCurrencyModifyReason
            
            # Get the active sim
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if active_sim_info is None:
                log.error("No active sim found, cannot add simoleons for like reward")
                return
                
            # Add 1 simoleon per like
            amount_to_add = like_count
            result = CommonSimCurrencyUtils.add_simoleons_to_household(
                active_sim_info, 
                amount_to_add, 
                CommonCurrencyModifyReason.EVENT_REWARD
            )
            
            if result:
                user = context.get('description', 'TikTok likes')
                log.info(f"[TikTokActionNotifications] Added §{amount_to_add} to household funds for {user}")
                
                # Show notification for like milestone
                title = "TikTok Like Milestone!"
                description = f"Added §{amount_to_add} to household funds!\n{user}"
                TikTokActionNotifications._show_gift_notification(title, description)
            else:
                log.error(f"[TikTokActionNotifications] Failed to add simoleons: {result.reason}")
                
        except Exception as e:
            log.error(f"Error adding simoleons for like reward: {e}")
