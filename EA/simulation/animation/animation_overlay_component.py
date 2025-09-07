from __future__ import annotationsfrom animation.animation_interaction import AnimationInteractionfrom animation.animation_overlay import AnimationOverlayfrom event_testing.test_events import TestEventfrom objects.components import Component, types, componentmethodfrom sims4.tuning.tunable import HasTunableFactory, AutoFactoryInit, TunableListimport servicesimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from sims4.tuning.tunable import TunableFactory
    from typing import *logger = sims4.log.Logger('Animation')
class AnimationOverlayComponent(Component, HasTunableFactory, AutoFactoryInit, component_name=types.ANIMATION_OVERLAY_COMPONENT):
    ANIMATION_OVERLAY_EVENTS = (TestEvent.MoodChange,)
    FACTORY_TUNABLES = {'animation_overlays': TunableList(description='\n            A list of animation overlays to play on this Sim.\n            ', tunable=AnimationOverlay.TunableFactory())}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._animation_overlays = []

    def on_add(self):
        for animation_overlay in self.animation_overlays:
            self._animation_overlays.append(animation_overlay(self.owner))
        services.get_event_manager().register(self, self.ANIMATION_OVERLAY_EVENTS)

    def on_remove(self):
        services.get_event_manager().unregister(self, self.ANIMATION_OVERLAY_EVENTS)

    def handle_event(self, sim_info, event_type, resolver):
        if self.owner.is_sim and self.owner.sim_info is not sim_info:
            return
        self.update_animation_overlays()

    def _try_get_overlay_from_tuning(self, overlay:'TunableFactory.TunableFactoryWrapper') -> 'Optional[AnimationOverlay]':
        for active_overlay in self._animation_overlays:
            if active_overlay._overlay_animation == overlay._overlay_animation:
                return active_overlay

    @componentmethod
    def add_overlay(self, overlay:'TunableFactory.TunableFactoryWrapper') -> 'None':
        if self._try_get_overlay_from_tuning(overlay) is None:
            animation_overlay = overlay(self.owner)
            self._animation_overlays.append(animation_overlay)
            animation_overlay.start_overlay(interaction=AnimationInteraction)

    @componentmethod
    def remove_overlay(self, overlay:'TunableFactory.TunableFactoryWrapper') -> 'None':
        active_overlay = self._try_get_overlay_from_tuning(overlay)
        if active_overlay is not None:
            active_overlay.stop_overlay()
            self._animation_overlays.remove(active_overlay)

    @componentmethod
    def start_animation_overlays(self):
        for animation_overlay in self._animation_overlays:
            animation_overlay.start_overlay(interaction=AnimationInteraction)

    @componentmethod
    def stop_animation_overlays(self):
        for animation_overlay in self._animation_overlays:
            animation_overlay.stop_overlay()

    @componentmethod
    def update_animation_overlays(self):
        for animation_overlay in self._animation_overlays:
            animation_overlay.update_overlay()
