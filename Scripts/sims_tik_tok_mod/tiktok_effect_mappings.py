from sims4communitylib.utils.sims.common_buff_utils import CommonBuffUtils
from sims4communitylib.utils.sims.common_household_utils import CommonHouseholdUtils
from sims4communitylib.utils.sims.common_sim_currency_utils import CommonSimCurrencyUtils
from sims4communitylib.utils.sims.common_relationship_utils import CommonRelationshipUtils
from sims4communitylib.enums.relationship_tracks_enum import CommonRelationshipTrackId
from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils
from sims_tik_tok_mod.utils.cas_utils import TikTokCASUtils
from sims4communitylib.enums.buffs_enum import CommonBuffId
from sims4communitylib.enums.common_currency_modify_reasons import CommonCurrencyModifyReason
from sims4communitylib.enums.common_species import CommonSpecies
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims_tik_tok_mod.modinfo import ModInfo
from sims_tik_tok_mod.utils.vfx_utils import TikTokVFXUtils
from sims_tik_tok_mod.utils.pose_player_utils import TikTokPosePlayerUtils
from typing import Dict, Any
from sims.sim_info import SimInfo

log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokEffectMappings')  # type: ignore[attr-defined]
log.enable()

class TikTokEffectMappings:
    ACTION_DESCRIPTIONS = {
        'flirty_compliment': 'Applied flirty buff to all household members!',
        'show_off': 'Active Sim is showing off with confidence!',
        'romantic_hug': 'Active Sim is giving romantic hugs to nearby Sims!',
        'create_sim': 'Created a Sim for the gifter!',
        'create_small_dog_sim': 'Created a Small Dog for the gifter!',
        'create_large_dog_sim': 'Created a Large Dog for the gifter!',
        'create_cat_sim': 'Created a Cat for the gifter!',
        'default': 'Thank you for the gift!'
    }

    @staticmethod
    def apply_action_effect(user_nickname: str, action: str, count: int, context: Dict[str, Any]) -> None:
        """Apply the actual game effect for a Sims action"""
        if action == 'create_sim':
            TikTokCASUtils.create_sim_and_open_cas(user_nickname)

        elif action == 'create_small_dog_sim':
            TikTokCASUtils.create_non_household_animal_sim(user_nickname, CommonSpecies.SMALL_DOG)

        elif action == 'create_large_dog_sim':
            TikTokCASUtils.create_non_household_animal_sim(user_nickname, CommonSpecies.LARGE_DOG)

        elif action == 'create_cat_sim':
            TikTokCASUtils.create_non_household_animal_sim(user_nickname, CommonSpecies.CAT)

        elif action == 'flirty_compliment':
            TikTokVFXUtils.play_one_shot_on_sim('attraction_first_attraction_heart_spin', joint_name='b__Head__', duration=3)
            
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
                active_household.funds.add(amount * count, CommonCurrencyModifyReason.CHEAT)
                log.info(f"Added {amount * count} simoleons")
        
        elif action == 'break_object':
            # Find and break a random object
            # Implementation would go here
            pass
        
        elif action == 'show_off':
            # Apply confident buff and make the active Sim show off
            TikTokEffectMappings._apply_show_off_action(count)
        
        elif action == 'romantic_hug':
            # Make the active Sim give romantic hugs to nearby Sims
            TikTokEffectMappings._apply_romantic_hug_action(count)
        
        elif action == 'like_reward':
            # Add simoleons to household for like milestone reward
            TikTokEffectMappings._add_simoleons_for_like_reward(count, context)
        
        elif action == 'hand_heart':
            # Make the active Sim give a hand heart to nearby Sims
            TikTokEffectMappings._apply_hand_heart_action(count)
        
        else:
            log.info(f"TODO: Apply effect for action '{action}' x{count}")

    @staticmethod
    def _apply_hand_heart_action(count: int) -> None:
        """Apply hand heart action - makes the active Sim give a hand heart to nearby Sims"""
        try:
            sim = CommonSimUtils.get_active_sim()
            if not sim:
                log.error("No active sim found for hand heart action")
                return

            TikTokVFXUtils.play_one_shot_on_sim('ep1_givebirth_alien', joint_name='b__Root__')
            TikTokPosePlayerUtils.play_pose_by_name(sim, 'flowurtheweirdo:PosePack_202302100125254978_set_1', pose_duration=1.4)
        except Exception as e:
            log.error(f"Error applying hand heart action: {e}")

    @staticmethod
    def _apply_show_off_action(count: int) -> None:
        """Apply show off action - makes the active Sim confident and perform show-off interactions"""
        try:
            
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
    def _apply_romantic_hug_action(count: int) -> None:
        """Apply romantic hug action - makes the active Sim give romantic hugs to nearby Sims"""
        try:
            # Get the active sim
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if not active_sim_info:
                log.error("No active sim found for romantic_hug action")
                return

            TikTokVFXUtils.play_one_shot_on_sim('attraction_first_attraction_heart_spin', joint_name='b__Head__', duration=3)

            # Apply flirty buff to the active sim
            result = CommonBuffUtils.add_buff(active_sim_info, CommonBuffId.FLIRTY_BY_POTION, buff_reason="Romantic mood from TikTok gift")
            if result:
                log.info(f"Applied flirty buff to {active_sim_info.first_name} for romantic hug action")
            else:
                log.error(f"Failed to apply flirty buff: {result.reason}")
            
            # Get targets from current interactions
            interaction_targets = TikTokEffectMappings.get_all_running_interaction_targets(active_sim_info)
            
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
            
            if not unique_targets or len(unique_targets) == 0:
                log.info("No interaction targets found for romantic hug - applying romantic mood to active Sim only")
                return
            
            target_sim_info = unique_targets[0]
            try:
                # Apply flirty buff to target as well
                buff_result = CommonBuffUtils.add_buff(target_sim_info, CommonBuffId.FLIRTY_BY_POTION, buff_reason="Romantic hug from TikTok gift")
                if buff_result:
                    log.info(f"Applied romantic buff to {target_sim_info.first_name}")
                
                # Try to improve relationship between the sims
                try:
                    CommonRelationshipUtils.change_relationship_level_of_sims(
                        active_sim_info,
                        target_sim_info,
                        CommonRelationshipTrackId.FRIENDSHIP,
                        20.0
                    )
                    CommonRelationshipUtils.change_relationship_level_of_sims(
                        active_sim_info, 
                        target_sim_info, 
                        CommonRelationshipTrackId.ROMANCE,
                        20.0
                    )
                except Exception as rel_error:
                    log.debug(f"Could not change relationship: {rel_error}")
                
            except Exception as e:
                log.error(f"Error applying romantic hug to {target_sim_info.first_name}: {e}")
            
            log.info(f"Romantic hug action completed between {active_sim_info.first_name} and {target_sim_info.first_name}")
            
        except Exception as e:
            log.error(f"Error applying romantic hug action: {e}")
    
    @staticmethod
    def _add_simoleons_for_like_reward(like_count: int, context: Dict[str, Any]) -> None:
        """Add simoleons to the active household for TikTok like milestone reward"""
        try:
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if active_sim_info is None:
                log.error("No active sim found, cannot add simoleons for like reward")
                return

            amount_to_add = like_count
            CommonSimCurrencyUtils.add_simoleons_to_household(
                active_sim_info, 
                amount_to_add, 
                CommonCurrencyModifyReason.EVENT_REWARD
            )
        except Exception as e:
            log.error(f"Error adding simoleons for like reward: {e}")

    @staticmethod
    def get_all_running_interaction_targets(sim_info: SimInfo):
        """Get all targets from the sim's currently running interactions"""
        sim = CommonSimUtils.get_sim_instance(sim_info)
        if sim is None or sim.si_state is None:
            return []
        targets = []
        for interaction in CommonSimInteractionUtils.get_running_interactions_gen(sim_info):
            targets.append(getattr(interaction, 'target', None))
        return targets
