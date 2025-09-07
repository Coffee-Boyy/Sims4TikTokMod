from __future__ import annotationsfrom animation.arb import Arbfrom animation.arb_element import distribute_arb_elementfrom interactions.aop import AffordanceObjectPairfrom interactions.context import InteractionContextfrom interactions.interaction_finisher import FinishingTypefrom interactions.priority import Priorityfrom postures import PostureEvent, PostureTrackfrom sims4.tuning.tunable import HasTunableFactory, AutoFactoryInit, TunableReferenceimport servicesimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from interactions.base.interaction import Interaction
    from typing import *logger = sims4.log.Logger('Animation')
class AnimationOverlay(HasTunableFactory, AutoFactoryInit):
    FACTORY_TUNABLES = {'_overlay_animation': TunableReference(description='\n            The animation element controlling the overlay.\n            ', manager=services.get_instance_manager(sims4.resources.Types.ANIMATION), class_restrictions=('AnimationElement',))}

    def __init__(self, sim, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sim = sim
        self._sim.on_posture_event.append(self._on_posture_changed)
        self._overlay_interaction = None

    def start_overlay(self, interaction:'Interaction') -> 'None':
        aop = AffordanceObjectPair(interaction, None, interaction, None, hide_unrelated_held_props=False)
        context = InteractionContext(self._sim, InteractionContext.SOURCE_SCRIPT, Priority.High)
        self._overlay_interaction = aop.interaction_factory(context).interaction

    def stop_overlay(self):
        if self._overlay_interaction is None:
            return
        self._overlay_interaction.cancel(FinishingType.RESET, 'Stopping overlay animations.')
        self._overlay_interaction.on_removed_from_queue()
        self._overlay_interaction = None

    def update_overlay(self):

        def restart_overlay_asm(asm):
            asm.set_current_state('entry')
            return True

        if self._overlay_interaction is None:
            return
        overlay_animation = self._overlay_animation(self._overlay_interaction, setup_asm_additional=restart_overlay_asm, enable_auto_exit=False)
        asm = overlay_animation.get_asm()
        if asm is None:
            logger.warn(' Unable to get a valid overlay ASM ({}) for {}.', self._overlay_animation, self._sim)
            return
        arb = Arb()
        overlay_animation.append_to_arb(asm, arb)
        distribute_arb_element(arb)

    def _on_posture_changed(self, change, dest_state, track, old_value, new_value):
        if change == PostureEvent.POSTURE_CHANGED and track == PostureTrack.BODY and self._overlay_interaction is not None:
            self._overlay_interaction.clear_animation_liability_cache()
