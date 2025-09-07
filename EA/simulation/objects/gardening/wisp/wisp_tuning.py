from __future__ import annotationsimport servicesimport sims4.resourcesfrom scheduler import WeeklySchedulefrom sims4.tuning.tunable import TunableRange, TunablePackSafeReference, Tunablefrom typing import TYPE_CHECKINGfrom vfx import PlayEffectif TYPE_CHECKING:
    from typing import *
class WispTuning:
    IDLE_VFX_DURATION = TunableRange(description='\n        The target duration for the Idle VFX.\n        ', tunable_type=float, default=10, minimum=0)
    IDLE_VFX_STATE = TunablePackSafeReference(description='\n        Idle VFX State.\n        ', manager=services.get_instance_manager(sims4.resources.Types.OBJECT_STATE), class_restrictions='ObjectState')
    IDLE_VFX_STATE_VALUE_OFF = TunablePackSafeReference(description='\n        Idle VFX State Value for when the Wisp is not active on a Plant.\n        ', manager=services.get_instance_manager(sims4.resources.Types.OBJECT_STATE), class_restrictions='ObjectStateValue')
    IDLE_VFX_STATE_VALUE_ON = TunablePackSafeReference(description='\n        Idle VFX State Value for when the Wisp is active on a Plant.\n        ', manager=services.get_instance_manager(sims4.resources.Types.OBJECT_STATE), class_restrictions='ObjectStateValue')
    TRAVEL_VFX = PlayEffect.TunableFactory(description='\n        The VFX to play wisp is travel from one plant to another\n        ')
    TRAVEL_VFX_DURATION = TunableRange(description='\n        The target duration for the Travel VFX.\n        ', tunable_type=float, default=5, minimum=0)
    PLANT_SEARCH_RADIUS = Tunable(description='\n        The radius for searching for surrounding plants to travel to.\n        ', tunable_type=float, default=10.0)
    WISP_SCHEDULE = WeeklySchedule.TunableFactory(description='\n        The schedule for when to start the wisp.\n        ')
    MINIMUM_NUMBER_OF_ENCHANTED_PLANTS_ON_LOT = TunableRange(description='\n        The minimum number of enchanted plants on the lot to start the wisp.\n        ', tunable_type=int, default=5, minimum=0)
    MINIMUM_NUMBER_OF_SURROUNDING_ENCHANTED_PLANTS = TunableRange(description='\n        The minimum number of surrounding enchanted plants to start the wisp on a selected plant.\n        ', tunable_type=int, default=5, minimum=0)
