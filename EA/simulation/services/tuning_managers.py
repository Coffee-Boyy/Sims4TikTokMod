from __future__ import annotationsimport cachesimport pythonutilsimport servicesfrom sims4.common import Packfrom sims4.resources import INSTANCE_TUNING_DEFINITIONS, register_pack_hotload_request_callback, register_pack_hotload_callbackimport pathsfrom sims4.tuning.instance_manager import TuningInstanceManagerimport sims4.tuning.serializationfrom sims4.tuning.tunable_perf import TuningAttrCleanupHelperfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import List, Callable
class InstanceTuningManagers(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._type_to_def_mapping = {d.TYPE_ENUM_VALUE: d for d in INSTANCE_TUNING_DEFINITIONS}

    def __missing__(self, resource_type_enum):
        if resource_type_enum not in self._type_to_def_mapping:
            raise KeyError('Cannot create manager for {}, key not found in instance tuning manager type map'.format(resource_type_enum))
        definition = self._type_to_def_mapping[resource_type_enum]
        manager = self._create_instance_manager(definition, resource_type_enum)
        self[resource_type_enum] = manager
        return manager

    def clear(self):
        self._unregister_for_pack_hot_load()
        self._type_to_def_mapping.clear()
        super().clear()

    def _create_instance_manager(self, definition, resource_type_enum):
        from sims4.tuning.instance_manager import InstanceManager
        mgr_type = resource_type_enum
        mgr_path = paths.TUNING_ROOTS[definition.resource_type]
        mgr_factory = InstanceManager
        args = (mgr_path, mgr_type)
        kwargs = {}
        kwargs['use_guid_for_ref'] = definition.use_guid_for_ref
        kwargs['base_game_only'] = definition.base_game_only
        kwargs['require_reference'] = definition.require_reference
        if definition.manager_type is not None:
            from sims4.tuning.instance_manager_utils import MANAGER_TYPES
            mgr_factory = MANAGER_TYPES[definition.manager_type]
        return mgr_factory(*args, **kwargs)

    @staticmethod
    def _hot_load_unload_packs(packs:'List[Pack]', is_loading:'bool', log_fn:'Callable[[str], None]'=None) -> 'bool':
        caches.clear_all_caches()
        from animation import posture_manifest
        posture_manifest._posture_name_to_posture_type_cache = None
        from sims4.tuning.merged_tuning_manager import get_manager
        merged_tuning_manager = get_manager()
        if not merged_tuning_manager.prepare_hot_load_unload(packs=packs):
            return True
        instantiated_tuning_managers = []
        for definition in INSTANCE_TUNING_DEFINITIONS:
            instantiated_tuning_managers.append(services.get_instance_manager(definition.TYPE_ENUM_VALUE))
        tuning_instance_manager = TuningInstanceManager(instantiated_tuning_managers, packs_to_load=packs)
        result = True
        try:
            pythonutils.change_gc_policy(0)
            merged_tuning_manager.USE_CACHE = False
            TuningAttrCleanupHelper.enabled = True
            if is_loading:
                tuning_instance_manager.execute(log_fn=log_fn)
            else:
                tuning_instance_manager.unload_packs(packs)
            sims4.tuning.serialization.finalize_tuning()
        except:
            result = False
        finally:
            merged_tuning_manager.USE_CACHE = True
            pythonutils.change_gc_policy(3)
        return result

    @staticmethod
    def hot_load_packs(packs:'List[Pack]', log_fn:'Callable[[str], None]'=None) -> 'bool':
        return InstanceTuningManagers._hot_load_unload_packs(packs, is_loading=True, log_fn=log_fn)

    @staticmethod
    def hot_unload_packs(packs:'List[Pack]') -> 'bool':
        return InstanceTuningManagers._hot_load_unload_packs(packs, is_loading=False)

    def _pack_hot_load_requested_callback(self, is_load_request:'bool', pack_ids:'List[int]') -> 'bool':
        return True

    def _pack_hot_load_callback(self, is_load_request:'bool', pack_ids:'List[int]') -> 'bool':
        if not pack_ids:
            return True
        packs = [Pack(pack_id) for pack_id in pack_ids]
        if is_load_request:
            result = self.hot_load_packs(packs)
        else:
            result = self.hot_unload_packs(packs)
        return result

    def register_for_pack_hot_load(self):
        register_pack_hotload_request_callback(True, self._pack_hot_load_requested_callback)
        register_pack_hotload_callback(True, self._pack_hot_load_callback)

    def _unregister_for_pack_hot_load(self):
        register_pack_hotload_request_callback(False, self._pack_hot_load_requested_callback)
        register_pack_hotload_callback(False, self._pack_hot_load_callback)
