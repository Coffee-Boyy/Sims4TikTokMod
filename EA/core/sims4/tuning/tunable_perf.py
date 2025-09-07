from __future__ import annotationsfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims4.tuning.tunable_base import TunableBaseTuningCleanupHelpers = []
class TuningAttrCleanupHelper:
    __slots__ = ('_field_name', '_tracked_objects')
    enabled = True

    def __init__(self, attr_field_name:'str'):
        self._field_name = attr_field_name
        self._tracked_objects = list()
        TuningCleanupHelpers.append(self)

    def __len__(self) -> 'int':
        if self._tracked_objects:
            return len(self._tracked_objects)
        return 0

    @property
    def attribute_name(self) -> 'str':
        return self._field_name

    def register_for_cleanup(self, owner:'TunableBase') -> 'None':
        if TuningAttrCleanupHelper.enabled:
            self._tracked_objects.append(owner)

    def perform_cleanup(self) -> 'bool':
        for obj in self._tracked_objects:
            setattr(obj, self._field_name, None)
        self._tracked_objects.clear()
        return True

class NoOpTuningCleanupHelper:

    def register_for_cleanup(self, owner:'Any') -> 'None':
        pass

    def perform_cleanup(self) -> 'bool':
        return False

    def __len__(self) -> 'int':
        return 0
NO_OP_CLEANUP_HELPER = NoOpTuningCleanupHelper()