from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_spawn_utils import CommonSimSpawnUtils
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
    def create_dog_sim(user_nickname: str) -> bool:
        try:
            active_sim_info = CommonSimUtils.get_active_sim_info()
            if active_sim_info is None:
                log.error("No active sim found. Cannot open CAS.")
                return False

            first_name, last_name = user_nickname.split(" ")
            sim_info = CommonSimSpawnUtils.create_small_dog_sim_info(
                gender=TikTokCASUtils.get_random_gender(),
                age=TikTokCASUtils.get_random_age(),
                first_name=first_name[:20],
                last_name=last_name[:20],
                source="TikTok"
            )

            if sim_info is None:
                log.error("Failed to create dog sim info.")
                return False

            success = CommonSimSpawnUtils.spawn_sim_at_active_sim_location(sim_info)
            if not success:
                log.error("Failed to spawn dog sim at active sim location.")
                return False

            return True
        except Exception as e:
            log.error(f"Error opening CAS for sim creation: {e}")
            return False
