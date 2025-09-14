from sims4communitylib.enums.common_species import CommonSpecies
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_spawn_utils import CommonSimSpawnUtils
from sims4communitylib.utils.sims.common_sim_location_utils import CommonSimLocationUtils
from sims4communitylib.utils.sims.common_household_utils import CommonHouseholdUtils
from sims4communitylib.enums.common_gender import CommonGender
from sims4communitylib.enums.common_age import CommonAge
from sims_tik_tok_mod.modinfo import ModInfo
from server.client import Client
import sims4.commands
import services
from sims.sim_info import SimInfo
import random
from sims.household import Household

log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokCASUtils')  # type: ignore[attr-defined]
log.enable()

class TikTokCASUtils:
    """Utilities for interacting with Create-A-Sim."""

    @staticmethod
    def get_random_gender() -> CommonGender:
        return random.choice([CommonGender.MALE, CommonGender.FEMALE])
    
    @staticmethod
    def get_random_age() -> CommonAge:
        suitable_ages = [
            CommonAge.CHILD,
            CommonAge.ADULT,
            CommonAge.ELDER
        ]
        return random.choice(suitable_ages)

    @staticmethod
    def create_sim_and_open_cas(user_nickname: str) -> bool:
        """
        Opens the Create-A-Sim screen to add a new Sim to the active household.
        """
        try:
            client: Client = services.client_manager().get_first_client()  # pyright: ignore[reportAssignmentType]
            if not client:
                log.error("Failed to get client.")
                return False

            active_sim_info: SimInfo = CommonSimUtils.get_active_sim_info()  # pyright: ignore[reportAssignmentType]
            if active_sim_info is None:
                log.error("No active sim found. Cannot open CAS.")
                return False

            log.info(f"Creating new sim for TikTok user: {user_nickname}")

            target_household: Household = active_sim_info.household  # type: ignore[attr-defined]
            if target_household is None:
                log.error("Active sim has no household.")
                return False

            first_name, last_name = user_nickname.split(" ")
            sim_info: SimInfo = CommonSimSpawnUtils.create_human_sim_info(  # pyright: ignore[reportAssignmentType]
                gender=TikTokCASUtils.get_random_gender(),
                age=TikTokCASUtils.get_random_age(),
                first_name=first_name[:20],
                last_name=last_name[:20],
                source="TikTok",
                household=target_household  # type: ignore[arg-type]
            )
            
            if sim_info is None:
                log.error("Failed to create sim info.")
                return False
            
            target_household.save_data()
            
            log.info(f"Created sim info for {sim_info.first_name} {sim_info.last_name} (ID: {sim_info.sim_id})")

            success = CommonSimSpawnUtils.spawn_sim_at_active_sim_location(sim_info)  # type: ignore[arg-type]
            if not success:
                log.error("Failed to spawn sim at active sim location.")
                return False
            
            log.info(f"Successfully spawned {sim_info.first_name} in world")
            
            # Make the sim selectable so they appear in the UI panel
            # This must be done AFTER spawning to ensure the sim is properly initialized
            if sim_info.household_id == target_household.id:  # type: ignore[attr-defined]
                client.add_selectable_sim_info(sim_info)
                log.info(f"Made {sim_info.first_name} selectable in UI")
            
            # Force the sim to be selected as the active sim before opening CAS
            # This helps ensure CAS focuses on the correct sim
            try:
                client.set_active_sim(sim_info)
                log.info(f"Set {sim_info.first_name} as active sim")
            except Exception as e:
                log.warning(f"Could not set new sim as active: {e}")
            
            sims4.commands.client_cheat(
                f'sims.exit2caswithhouseholdid {sim_info.sim_id} {sim_info.household_id}',
                client.id
            )
            
            return True
        except Exception as e:
            log.error(f"Error opening CAS for sim creation: {e}")
            return False

    @staticmethod
    def create_non_household_animal_sim(user_nickname: str, animal_type: CommonSpecies = CommonSpecies.SMALL_DOG) -> bool:
        """
        Creates an animal sim that hangs around the lot without being added to the household.
        The animal will behave as if they belong but won't be part of the household.
        
        Args:
            user_nickname: Name for the animal
            animal_type: Type of animal (CommonSpecies.SMALL_DOG, CommonSpecies.CAT, etc.)
        """
        try:
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if active_sim_info is None:
                log.error("No active sim found. Cannot create non-household animal.")
                return False

            # Create a temporary household for the animal
            household_manager = services.household_manager()
            temp_household = household_manager.create_household(account=None)
            if temp_household is None:
                log.error("Failed to create temporary household for animal.")
                return False

            # Parse name
            name_parts = user_nickname.split(" ")
            first_name = name_parts[0][:20]
            last_name = name_parts[1][:20] if len(name_parts) > 1 else ""

            # Create the animal sim info without specifying household (will be added later)
            if animal_type == CommonSpecies.CAT:
                sim_info = CommonSimSpawnUtils.create_cat_sim_info(
                    gender=TikTokCASUtils.get_random_gender(),
                    age=TikTokCASUtils.get_random_age(),
                    first_name=first_name,
                    last_name=last_name,
                    source="TikTok_NonHousehold"
                )
            elif animal_type == CommonSpecies.LARGE_DOG:
                sim_info = CommonSimSpawnUtils.create_large_dog_sim_info(
                    gender=TikTokCASUtils.get_random_gender(),
                    age=TikTokCASUtils.get_random_age(),
                    first_name=first_name,
                    last_name=last_name,
                    source="TikTok_NonHousehold"
                )
            else:
                sim_info = CommonSimSpawnUtils.create_small_dog_sim_info(
                    gender=TikTokCASUtils.get_random_gender(),
                    age=TikTokCASUtils.get_random_age(),
                    first_name=first_name,
                    last_name=last_name,
                    source="TikTok_NonHousehold"
                )

            if sim_info is None:
                log.error(f"Failed to create {animal_type} sim info.")
                CommonHouseholdUtils.delete_household(temp_household)
                return False

            # Add the sim to the temporary household
            temp_household.add_sim_info(sim_info)

            # Get active sim's location for spawning
            active_sim_location = CommonSimLocationUtils.get_location(active_sim_info)
            if active_sim_location is None:
                log.error("Could not get active sim location.")
                CommonHouseholdUtils.delete_household(temp_household)
                return False

            # Spawn the animal at the active sim's location
            success = CommonSimSpawnUtils.spawn_sim(sim_info, location=active_sim_location)
            
            if not success:
                log.error(f"Failed to spawn {animal_type} sim at active sim location.")
                CommonHouseholdUtils.delete_household(temp_household)
                return False

            # Create a visitor situation to keep the animal on the lot
            TikTokCASUtils._create_visitor_situation_for_animal(sim_info)
            
            log.info(f"Successfully created non-household {animal_type} '{first_name} {last_name}' that will hang around the lot")
            return True

        except Exception as e:
            log.error(f"Error creating non-household animal sim: {e}")
            return False

    @staticmethod
    def _create_visitor_situation_for_animal(sim_info) -> bool:
        """
        Creates a visitor situation for the animal to keep them on the lot
        without being part of the household.
        """
        try:
            situation_manager = services.get_zone_situation_manager()
            if situation_manager is None:
                log.error("Could not get situation manager")
                return False

            # Use the create_visit_situation method which handles visitor scenarios
            sim_instance = CommonSimUtils.get_sim_instance(sim_info)
            if sim_instance is None:
                log.error("Could not get sim instance for visitor situation")
                return False

            # Create a long-duration visit situation
            from date_and_time import create_time_span
            long_duration = create_time_span(hours=12)
            
            situation_id = situation_manager.create_visit_situation(
                sim_instance,
                duration_override=long_duration
            )

            if situation_id is None:
                log.error("Failed to create visitor situation for animal")
                return False

            log.info(f"Created visitor situation {situation_id} for animal {sim_info.first_name} {sim_info.last_name}")
            return True

        except Exception as e:
            log.error(f"Error creating visitor situation for animal: {e}")
            # Even if situation creation fails, the animal should still be spawned
            # The game will handle basic NPC behavior
            log.info("Animal will use default NPC behavior instead of visitor situation")
            return True
