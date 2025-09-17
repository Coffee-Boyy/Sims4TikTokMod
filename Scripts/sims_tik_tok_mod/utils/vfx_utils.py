import random
import alarms
from date_and_time import create_time_span
from sims.sim import Sim
from sims4.hash_util import hash32
from _math import Vector3
from typing import Tuple, Optional
from sims_tik_tok_mod.modinfo import ModInfo
from sims4communitylib.utils.common_log_registry import CommonLogRegistry
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils

# Core effect player
from vfx import PlayEffect

log = CommonLogRegistry.get().register_log(ModInfo.get_identity(), 'SimsTikTokModVFX')  # type: ignore[attr-defined]
log.enable()

class TikTokVFXUtils:
    """Convenience helpers to play attached VFX on a Sim."""

    _active_alarms = {}

    @staticmethod
    def play_one_shot_on_sim(
        effect_name: str,
        joint_name: str = 'b__Head__',
        duration: int = 2,
        offset: Optional[Tuple[float, float, float]] = (0.0, 0.0, 0.0),
    ) -> bool:
        try:
            target: Sim = CommonSimUtils.get_active_sim() # type: ignore[reportAssignmentType]
            transform_override = None
            joint_hash = hash32(joint_name) if joint_name else PlayEffect.JOINT_NAME_CURRENT_POSITION

            if offset is not None:
                transform_override = Vector3(offset[0], offset[1], offset[2])

            vfx = PlayEffect(
                target=target, # type: ignore[reportAssignmentType]
                effect_name=effect_name,
                joint_name=joint_hash,
                target_joint_offset=transform_override,
                play_immediate=True
            )
            vfx.start()

            alarm_id = random.randint(0, 1000000)

            def _on_alarm(_):
                try:
                    log.info(f'Stopping effect {effect_name}')
                    TikTokVFXUtils.stop(vfx)
                    TikTokVFXUtils._active_alarms.pop(alarm_id, None).cancel()
                except Exception as e:
                    log.error(f'Error stopping effect {effect_name}: {e}')

            time_span = create_time_span(minutes=duration)
            alarm_handle = alarms.add_alarm(
                target,
                time_span,
                _on_alarm,
                repeating=False
            )

            TikTokVFXUtils._active_alarms[alarm_id] = alarm_handle

            return True
        except Exception as ex:
            log.error(f'Failed to play one-shot VFX "{effect_name}": {ex}')
            return False

    @staticmethod
    def stop(vfx_instance, immediate: bool = False):
        """Stop a previously started loop effect."""
        try:
            if vfx_instance is not None:
                vfx_instance.stop(immediate=immediate)
        except Exception as ex:
            log.error(f'Failed to stop VFX: {ex}')