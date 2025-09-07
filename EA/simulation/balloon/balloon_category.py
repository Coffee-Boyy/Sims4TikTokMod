from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.resolver import InteractionResolverimport randomfrom balloon.balloon_enums import BalloonTypeEnumfrom balloon.balloon_variant import BalloonVariantfrom sims4.tuning.instances import HashedTunedInstanceMetaclass, TuningClassMixinfrom sims4.tuning.tunable import TunableEnumEntry, TunablePercent, TunableListfrom sims4.utils import blueprintmethodfrom singletons import DEFAULTimport servicesimport sims4.resources
class BalloonCategory(TuningClassMixin, metaclass=HashedTunedInstanceMetaclass, manager=services.get_instance_manager(sims4.resources.Types.BALLOON)):
    INSTANCE_TUNABLES = {'balloon_type': TunableEnumEntry(description='\n             The visual style of the balloon background.\n             ', tunable_type=BalloonTypeEnum, default=BalloonTypeEnum.THOUGHT), 'balloon_chance': TunablePercent(description='\n             The chance that a balloon from the list is actually shown.\n             ', default=100), 'balloons': TunableList(description='\n             The list of possible balloons.\n             ', tunable=BalloonVariant.TunableFactory(balloon_type=None))}

    def __init__(self, init_blueprint_func=None):
        if init_blueprint_func is not None:
            init_blueprint_func(self)

    @blueprintmethod
    def get_balloon_icons(self, resolver:'InteractionResolver', balloon_type=DEFAULT, gsi_category=None, **kwargs) -> 'List':
        if gsi_category is None:
            gsi_category = self.tuning_name
        else:
            gsi_category = '{}/{}'.format(gsi_category, self.tuning_name)
        possible_balloons = []
        if random.random() <= self.balloon_chance:
            for balloon in self.balloons:
                for balloon_icon in balloon.get_balloon_icons(resolver, balloon_type=self.balloon_type, gsi_category=gsi_category, **kwargs):
                    if balloon_icon:
                        possible_balloons.append(balloon_icon)
        return possible_balloons
