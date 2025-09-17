import random
from sims.sim import Sim
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from interactions.context import QueueInsertStrategy, InteractionContext
from interactions.priority import Priority
from sims4communitylib.utils.sims.common_sim_interaction_utils import CommonSimInteractionUtils
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from sims_tik_tok_mod.modinfo import ModInfo
from interactions.interaction_finisher import FinishingType
import alarms
from date_and_time import REAL_MILLISECONDS_PER_SIM_SECOND, TimeSpan

LOG = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'TikTokPosePlayerUtils')  # type: ignore[attr-defined]
LOG.enable()

SA_POSE = 12880964001135365186
SA_POSE_STOP = 12580983238869710811


class TikTokPosePlayerUtils:
    _active_alarms = {}

    @staticmethod
    def play_pose_by_name(sim: Sim, pose_name: str, pose_duration: float = 1.1) -> bool:
        """Push PoseInteraction directly with a pose_name"""
        sim_info = CommonSimUtils.get_sim_info(sim)
        context = InteractionContext(sim, InteractionContext.SOURCE_SCRIPT, Priority.Critical, insert_strategy=QueueInsertStrategy.FIRST, must_run_next=True)

        queue_result = CommonSimInteractionUtils.queue_super_interaction(
            sim_info=sim_info, # type: ignore[reportAssignmentType]
            super_interaction_id=SA_POSE,
            interaction_context=context,
            pose_name=pose_name
        )

        alarm_id = random.randint(0, 1000000)

        def _on_alarm(_):
            try:
                LOG.info(f'Stopping pose {pose_name}')
                for si in sim.si_state:
                    if hasattr(si, 'pose_name') and si.pose_name == pose_name:
                        time_running = si.consecutive_running_time_span.in_real_world_seconds()
                        LOG.info(f'Pose {pose_name} has been running for {time_running} seconds')

                        if time_running > pose_duration:
                            LOG.info(f'Stopping pose {pose_name} after {time_running} seconds')
                            si.cancel(FinishingType.SI_FINISHED, 'Stop Posing')
                            TikTokPosePlayerUtils._active_alarms.pop(alarm_id, None).cancel()
            except Exception as e:
                LOG.error(f'Error stopping pose {pose_name}: {e}')

        alarm_time_span = TimeSpan(REAL_MILLISECONDS_PER_SIM_SECOND)
        alarm_handle = alarms.add_alarm(
            sim,
            alarm_time_span,
            _on_alarm,
            repeating=True,
            repeating_time_span=alarm_time_span
        )

        TikTokPosePlayerUtils._active_alarms[alarm_id] = alarm_handle

        return bool(queue_result)
