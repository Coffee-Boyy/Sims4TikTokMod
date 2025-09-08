"""
Sim Character Creation Pipeline for TikTok Integration
Creates new sims when the bridge service indicates diamond threshold has been reached
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass

from sims4communitylib.enums.common_gender import CommonGender
from sims4communitylib.enums.common_age import CommonAge
from sims4communitylib.utils.sims.common_sim_spawn_utils import CommonSimSpawnUtils
from sims4communitylib.utils.sims.common_sim_location_utils import CommonSimLocationUtils
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims4communitylib.classes.math.common_vector3 import CommonVector3
from sims4communitylib.classes.math.common_location import CommonLocation
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.notifications.common_basic_notification import CommonBasicNotification
from sims_tik_tok_mod.modinfo import ModInfo
from sims.outfits.outfit_enums import BodyType  # type: ignore[import]
from cas.cas import get_caspart_bodytype  # type: ignore[import]
from buffs.appearance_modifier.appearance_modifier import AppearanceModifier, AppearanceModifierPriority  # type: ignore[import]

# Create a logger for this module
log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'SimCharacterCreator')  # type: ignore[attr-defined]
log.enable()

@dataclass
class AppearanceAttributes:
    """Data class to store analyzed appearance attributes"""
    hair_color: str = "brown"
    skin_tone: str = "medium"
    eye_color: str = "brown"
    gender: str = "male"
    age: str = "adult"
    hair_style: str = "short"
    confidence: float = 0.0


class SimCharacterCreator:
    """Handles sim character creation when triggered by bridge service"""
    # Optional mapping tables for deterministic appearance (fill with real IDs as needed)
    SKIN_TONE_TO_ID = {
        'very_light': 0x0000000000040B2F,
        'light': 0x0000000000040B92,
        'fair': 0x0000000000003840,
        'medium': 0x000000000000AFC7,
        'tan': 0x0000000000040A92,
        'olive': 0x00000000000406E3,
        'brown': 0x00000000000406E5,
        'dark': 0x00000000000407F0,
        'very_dark': 0x0000000000040CA8,
    }

    HAIR_STYLE_TO_CAS_PART = {
        'short': 0x00000000000442F0,
        'medium': 0x0000000000044410,
        'long': 0x00000000000443B1,
        # 'bald': None,  # handled separately
    }
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize the sim character creator system"""
        log.info("Initializing Sim Character Creator...")
        log.info("✅ Sim Character Creator initialized")
        
    @classmethod
    def process_gift_data(cls, gift_data: Dict[str, Any]) -> None:
        """Process gift data from bridge service"""
        try:
            user = gift_data.get('user', 'Unknown')
            if user is None:
                user = 'Unknown'
            
            diamond_tracking = gift_data.get('diamondTracking')
            appearance_analysis = gift_data.get('appearanceAnalysis')
            
            # Check if bridge service indicates we should create a sim
            if diamond_tracking and diamond_tracking.get('shouldCreateSim', False):
                log.info(f"Bridge service indicates sim creation needed for {user}")
                cls._create_sim_for_user(user, appearance_analysis, diamond_tracking)
            elif diamond_tracking:
                # Just log the diamond progress
                total_diamonds = diamond_tracking.get('totalDiamonds', 0)
                log.info(f"User {user} has {total_diamonds} accumulated diamonds")
                
        except Exception as e:
            log.error(f"Error processing gift data: {e}")
    
    @classmethod
    def _create_sim_for_user(cls, user: str, appearance_analysis: Optional[Dict[str, Any]], diamond_tracking: Dict[str, Any]) -> None:
        """Create a sim for the user based on bridge service data"""
        try:
            # Ensure user is not None
            if user is None:
                user = "Unknown"
            
            total_diamonds = diamond_tracking.get('totalDiamonds', 0)
            log.info(f"🎉 Creating sim for {user} who reached {total_diamonds} diamonds!")
            
            # Show notification (disabled - only showing sim spawned notification)
            # cls._show_sim_creation_notification(user, total_diamonds)
            
            # Parse appearance data if available
            if appearance_analysis:
                appearance = cls._parse_appearance_data(appearance_analysis)
                log.info(f"Using analyzed appearance for {user}: {appearance}")
            else:
                appearance = cls._get_default_appearance()
                log.info(f"No appearance analysis available for {user}, using defaults")
            
            # Create sim with appearance
            sim_info = cls._create_sim_with_appearance(user, appearance)
            
            # Spawn the sim in the game
            if sim_info:
                cls._spawn_sim_in_game(sim_info, user)
            
        except Exception as e:
            log.error(f"Error creating sim for user: {e}")
    
    @classmethod
    def _show_sim_creation_notification(cls, user: str, diamond_count: int) -> None:
        """Show notification about sim creation"""
        try:
            title = "🎉 New Sim Created!"
            description = f"{user} reached {diamond_count} diamonds!\nCreating a new sim based on their profile..."
            
            notification = CommonBasicNotification(title, description)
            notification.show()
            
        except Exception as e:
            log.error(f"Error showing sim creation notification: {e}")
    
    @classmethod
    def _parse_appearance_data(cls, appearance_data: Dict[str, Any]) -> AppearanceAttributes:
        """Parse appearance data from bridge service into AppearanceAttributes"""
        try:
            return AppearanceAttributes(
                hair_color=appearance_data.get('hair_color', 'brown'),
                skin_tone=appearance_data.get('skin_tone', 'medium'),
                eye_color=appearance_data.get('eye_color', 'brown'),
                gender=appearance_data.get('gender', 'male'),
                age=appearance_data.get('age', 'adult'),
                hair_style=appearance_data.get('hair_style', 'short'),
                confidence=float(appearance_data.get('confidence', 0.5))
            )
        except Exception as e:
            log.error(f"Error parsing appearance data: {e}")
            return cls._get_default_appearance()
    
    
    @classmethod
    def _get_default_appearance(cls) -> AppearanceAttributes:
        """Get default appearance attributes when analysis fails"""
        return AppearanceAttributes(
            hair_color="brown",
            skin_tone="medium",
            eye_color="brown",
            gender="male",
            age="adult",
            hair_style="short",
            confidence=0.0
        )
    
    @classmethod
    def _create_sim_with_appearance(cls, user: str, appearance: AppearanceAttributes) -> Optional[Any]:
        """Create a sim with the analyzed appearance attributes"""
        try:
            # Convert appearance attributes to Sims 4 enums
            gender = cls._convert_gender(appearance.gender)
            age = cls._convert_age(appearance.age)
            
            # Create the sim info
            sim_info = CommonSimSpawnUtils.create_human_sim_info(
                gender=gender,
                age=age,
                first_name=user[:20],  # Limit name length
                last_name="TikTok"
            )
            
            if sim_info:
                log.info(f"Created sim info for {user}: {sim_info}")
                # Apply absolute skin tone if mapped; otherwise use value shift approximation
                try:
                    skin_tone_key = (appearance.skin_tone or "").lower().strip()
                    # Absolute id mapping (if provided)
                    try:
                        mapped_skin_id = cls.SKIN_TONE_TO_ID.get(skin_tone_key)  # type: ignore[attr-defined]
                    except Exception:
                        mapped_skin_id = None
                    if isinstance(mapped_skin_id, int) and mapped_skin_id != 0:
                        try:
                            # setattr(sim_info, 'skin_tone_val_shift', float(0))
                            # resend_fn = getattr(sim_info, 'resend_skin_tone_val_shift', None)
                            # if callable(resend_fn):
                            #     resend_fn()

                            setattr(sim_info, 'skin_tone', mapped_skin_id)
                            resend_phys = getattr(sim_info, 'resend_physical_attributes', None)
                            if callable(resend_phys):
                                resend_phys()
                            log.info(f"Applied absolute skin tone id {mapped_skin_id} for '{skin_tone_key}'")
                        except Exception as e:
                            log.error(f"Could not apply absolute skin tone id {mapped_skin_id} for '{skin_tone_key}': {e}")
                except Exception as skin_err:
                    log.debug(f"Could not apply skin tone shift: {skin_err}")

                # Apply deterministic hair style (CAS part id) if mapped; otherwise tint existing
                try:
                    hair_style_key = (appearance.hair_style or "").lower().strip()
                    if hair_style_key in {'bald', 'shaved', 'none'}:
                        # Remove hair to achieve a bald style using EA appearance modifier
                        remove_hair = AppearanceModifier.RemoveCASPartByBodyType(
                            body_type=BodyType.HAIR,
                            update_genetics=True,
                            remove_custom_textures=True,
                            outfit_type_compatibility=None,
                            appearance_modifier_tag=None,
                            _is_combinable_with_same_type=False,
                            should_refresh_thumbnail=False
                        )
                        tracker = getattr(sim_info, 'appearance_tracker', None)
                        sim_id = getattr(sim_info, 'id', None)
                        if tracker is not None and sim_id is not None:
                            tracker.add_appearance_modifier(
                                remove_hair,
                                sim_id,
                                AppearanceModifierPriority.INVALID,
                                True,
                                source='SimCharacterCreator'
                            )
                            tracker.evaluate_appearance_modifiers()
                        log.info("Applied hair style 'bald' via EA RemoveCASPartByBodyType")
                    else:
                        # Apply mapped hair CAS part id if available
                        try:
                            mapped_part_id = cls.HAIR_STYLE_TO_CAS_PART.get(hair_style_key)  # type: ignore[attr-defined]
                        except Exception:
                            mapped_part_id = None

                        hair_part_id = mapped_part_id if mapped_part_id is not None else cls._get_current_hair_part_id(sim_info)
                        if hair_part_id is not None:
                            rgba_shift = cls._map_hair_color_to_rgba_shift(appearance.hair_color)
                            if rgba_shift is not None:
                                set_hair_color = AppearanceModifier.SetCASPart(
                                    cas_part=hair_part_id,
                                    should_toggle=False,
                                    replace_with_random=False,
                                    update_genetics=True,
                                    _is_combinable_with_same_type=False,
                                    remove_conflicting=False,
                                    hsv_color_shift=None,
                                    object_id=0,
                                    part_layer_index=-1,
                                    rgba_color_shift=rgba_shift,
                                    should_refresh_thumbnail=False,
                                    outfit_type_compatibility=None,
                                    appearance_modifier_tag=None,
                                    expect_invalid_parts=False
                                )
                                tracker = getattr(sim_info, 'appearance_tracker', None)
                                sim_id = getattr(sim_info, 'id', None)
                                if tracker is not None and sim_id is not None:
                                    tracker.add_appearance_modifier(
                                        set_hair_color,
                                        sim_id,
                                        AppearanceModifierPriority.INVALID,
                                        True,
                                        source='SimCharacterCreator'
                                    )
                                    tracker.evaluate_appearance_modifiers()
                                log.info(f"Applied hair color tint using rgba shift {rgba_shift} to part {hair_part_id}")
                            else:
                                log.info(f"No mapped color shift for hair color '{appearance.hair_color}', leaving default color")
                        else:
                            log.info("No current hair part found on outfit; skipping hair color application")
                except Exception as hair_err:
                    log.debug(f"Could not apply hair style/color: {hair_err}")
                
            return sim_info
            
        except Exception as e:
            log.error(f"Error creating sim with appearance: {e}")
            return None

    @classmethod
    def _get_current_hair_part_id(cls, sim_info: Any) -> Optional[int]:
        try:
            current_outfit = sim_info.get_current_outfit()
            outfit_data = sim_info.get_outfit(current_outfit[0], current_outfit[1])
            if outfit_data is None:
                return None
            for part_id in getattr(outfit_data, 'part_ids', tuple()):
                try:
                    if get_caspart_bodytype(part_id) == BodyType.HAIR:
                        return part_id
                except Exception:
                    continue
            return None
        except Exception:
            return None

    @classmethod
    def _map_hair_color_to_rgba_shift(cls, hair_color: Optional[str]) -> Optional[int]:
        """Map simple hair color names to an RGBA color shift integer understood by EA CAS API."""
        if hair_color is None:
            return None
        name = hair_color.lower().strip()
        rgb_map = {
            'black': (20, 20, 20),
            'dark_brown': (70, 50, 40),
            'brown': (85, 60, 40),
            'light_brown': (120, 90, 60),
            'blonde': (200, 170, 90),
            'platinum': (225, 215, 180),
            'red': (150, 40, 30),
            'ginger': (180, 70, 40),
            'auburn': (120, 50, 40),
            'blue': (40, 70, 160),
            'green': (40, 140, 70),
            'pink': (200, 80, 140),
            'purple': (120, 60, 160),
            'gray': (150, 150, 150),
            'grey': (150, 150, 150),
            'white': (230, 230, 230),
        }
        rgb = rgb_map.get(name)
        if rgb is None:
            return None
        r, g, b = rgb
        a = 255
        return ((r & 0xFF) << 24) | ((g & 0xFF) << 16) | ((b & 0xFF) << 8) | (a & 0xFF)
    
    @classmethod
    def _convert_gender(cls, gender_str: str) -> CommonGender:
        """Convert string gender to CommonGender enum"""
        gender_map = {
            'male': CommonGender.MALE,
            'female': CommonGender.FEMALE
        }
        return gender_map.get(gender_str.lower(), CommonGender.MALE)
    
    @classmethod
    def _convert_age(cls, age_str: str) -> CommonAge:
        """Convert string age to CommonAge enum"""
        age_map = {
            'young_adult': CommonAge.YOUNGADULT,
            'adult': CommonAge.ADULT,
            'elder': CommonAge.ELDER
        }
        return age_map.get(age_str.lower(), CommonAge.ADULT)
    
    @classmethod
    def _spawn_sim_in_game(cls, sim_info: Any, user: str) -> None:
        """Spawn the created sim in the game right next to the main character"""
        try:
            # Get the active sim's position
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if active_sim_info is None:
                log.error("No active sim found, cannot spawn new sim")
                
                # Show error notification for no active sim
                title = "❌ No Active Sim"
                description = f"Cannot spawn sim for {user} - no active sim found. Please select a sim first."
                notification = CommonBasicNotification(title, description)
                notification.show()
                return
            
            # Get the active sim's location and position
            active_location = CommonSimLocationUtils.get_location(active_sim_info)
            active_position = CommonSimLocationUtils.get_position(active_sim_info)
            
            if active_position is None or active_location is None:
                log.error("Could not get active sim position or location, falling back to default spawn")
                success = CommonSimSpawnUtils.spawn_sim_at_active_sim_location(sim_info)
                
                # Show warning notification for fallback spawn
                if not success:
                    title = "⚠️ Spawn Fallback Failed"
                    description = f"Failed to spawn sim for {user} even with fallback method. Check logs for details."
                    notification = CommonBasicNotification(title, description)
                    notification.show()
            else:
                # Create a position next to the active sim (2 units to the right)
                nearby_position = CommonVector3(
                    active_position.x + 2.0,
                    active_position.y,
                    active_position.z
                )
                
                # Spawn the sim at the nearby position
                success = CommonSimSpawnUtils.spawn_sim(
                    sim_info, 
                    location=active_location, 
                    position=nearby_position
                )
            
            if success:
                log.info(f"✅ Successfully spawned sim for {user} next to active sim")
                
                # Show success notification
                title = "🎉 Sim Spawned!"
                description = f"New sim '{user}' has been created and spawned right next to you!"
                notification = CommonBasicNotification(title, description)
                notification.show()
            else:
                log.error(f"❌ Failed to spawn sim for {user}")
                
                # Show error notification
                title = "❌ Sim Spawn Failed"
                description = f"Failed to spawn sim for {user}. Please try again or check the logs for more details."
                notification = CommonBasicNotification(title, description)
                notification.show()
                
        except Exception as e:
            log.error(f"Error spawning sim in game: {e}")
            
            # Show error notification for exceptions
            title = "❌ Sim Spawn Error"
            description = f"An error occurred while spawning sim for {user}: {str(e)}"
            notification = CommonBasicNotification(title, description)
            notification.show()
    
