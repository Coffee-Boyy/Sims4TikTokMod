from __future__ import annotationsfrom aspirations.aspiration_types import AspriationTypefrom sims4.tuning.instanced_class_manager import InstancedClassManagerimport sims4.logfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *logger = sims4.log.Logger('Aspirations')
class AspirationInstanceManager(InstancedClassManager):

    def all_whim_sets_gen(self) -> 'AspriationType':
        for aspiration in self.types.values():
            if aspiration.aspiration_type == AspriationType.WHIM_SET:
                yield aspiration
