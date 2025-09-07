from __future__ import annotationsimport sims4from sims4 import logfrom cas.cas import set_caspart, OutfitOverrideOptionFlags, remove_caspart_by_bodytype, apply_siminfo_overridefrom interactions.utils.loot_basic_op import BaseLootOperationfrom sims import sim_info_base_wrapperfrom sims4.tuning.tunable import TunableCasPartfrom sims.outfits.outfit_enums import BodyTypefrom sims.occult.occult_enums import OccultTypefrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from event_testing.resolver import Resolver
    from sims.sim_info import SimInfologger = sims4.log.Logger('FairyWingOps', default_owner='jewei')
class SetFairyWingsOnSim(BaseLootOperation):
    FACTORY_TUNABLES = {'fairy_wings_reference': TunableCasPart(description='\n            The CAS object for the fairy wings to be set on the sim.\n            ', pack_safe=True)}

    def __init__(self, fairy_wings_reference:'TunableCasPart', **kwargs) -> 'None':
        super().__init__(**kwargs)
        self.fairy_wings_reference = fairy_wings_reference

    def _apply_to_subject_and_target(self, subject:'SimInfo', target:'SimInfo', resolver:'Resolver') -> 'None':
        if subject is None or not subject.is_sim:
            logger.error('Cannot set wings on {}. They must be a sim to perform this operation.', subject)
            return
        occult_sim_info = subject.occult_tracker._sim_info_map[OccultType.FAIRY]
        if occult_sim_info is None:
            logger.error('Cannot set wings on {}. They must be a fairy sim to perform this operation.', subject)
            return
        if self.fairy_wings_reference is not None:
            modified_sim_info = sim_info_base_wrapper.SimInfoBaseWrapper(gender=subject.gender, age=subject.age, species=subject.species, first_name=subject.first_name, last_name=subject.last_name, breed_name=subject.breed_name, full_name_key=subject.full_name_key, breed_name_key=subject.breed_name_key)
            if not remove_caspart_by_bodytype(subject._base, modified_sim_info._base, BodyType.WINGS, True, True):
                logger.warn('No wings were removed from the sim {}. If they are turning into a fairy for the first time, this is expected behavior.', subject)
            if not set_caspart(subject._base, modified_sim_info._base, self.fairy_wings_reference, False, False, True, 0, True):
                logger.error('No wings were added to the sim {}.', subject)
                return
            option_flags = OutfitOverrideOptionFlags.DEFAULT
            apply_siminfo_override(subject._base, modified_sim_info._base, subject._base, option_flags)
            apply_siminfo_override(occult_sim_info._base, modified_sim_info._base, occult_sim_info._base, option_flags)
            occult_human_sim_info = subject.occult_tracker._sim_info_map[OccultType.HUMAN]
            if occult_human_sim_info is None:
                logger.error('This sim does not have a human form {}.', subject)
                return
            occult_human_sim_info.pelt_layers = modified_sim_info.pelt_layers
            occult_human_sim_info._base.pelt_layers = modified_sim_info._base.pelt_layers
