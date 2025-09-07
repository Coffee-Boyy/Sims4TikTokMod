from __future__ import annotationsimport enumimport zone_typesfrom buffs.appearance_modifier.appearance_modifier import AppearanceModifier, AppearanceModifierPriorityfrom jewelry_crafting.jewelry_crafting_tuning import JewelryCraftingTuningfrom sims.occult.occult_enums import OccultTypefrom sims4.common import Packfrom sims4.utils import classpropertyfrom tunable_multiplier import TunableMultiplierfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims.sim_info import SimInfo
    from sims.sim import Simimport servicesfrom objects import ALL_HIDDEN_REASONSfrom cas.cas import OutfitData, get_caspart_bodytype, OutfitOverrideOptionFlags, get_caspart_hide_occult_flagsfrom distributor.rollback import ProtocolBufferRollbackfrom objects.components.types import JEWELRY_COMPONENTfrom objects.components.jewelry_component import JewelryComponent, AppearanceModifierTuplefrom objects.components.sim_inventory_component import SimInventoryComponentfrom sims.outfits.outfit_enums import OutfitCategoryfrom sims.sim_info_tracker import SimInfoTrackerfrom dataclasses import dataclass
@dataclass
class CasPartObjectId:
    __annotations__['cas_part'] = 'int'
    __annotations__['object_id'] = 'int'

    def __hash__(self):
        return hash((self.cas_part, self.object_id))

class ObjectUpdateAction(enum.Int):
    ADD = (0,)
    REMOVE = (1,)
    UPDATE = 2

class JewelryTracker(SimInfoTracker):
    WEREABLE_CATEGORIES = [OutfitCategory.EVERYDAY, OutfitCategory.FORMAL, OutfitCategory.ATHLETIC, OutfitCategory.SLEEP, OutfitCategory.PARTY, OutfitCategory.SWIMWEAR, OutfitCategory.HOTWEATHER, OutfitCategory.COLDWEATHER]

    def __init__(self, sim_info:'SimInfo'):
        self._sim_info = sim_info
        self._equipped_jewels = None
        sim_info.register_for_outfit_changed_callback(self._on_sim_outfit_changed)

    @classproperty
    def required_packs(cls):
        return (Pack.SP49,)

    def on_lod_update(self, old_lod, new_lod):
        if not self.is_valid_for_lod(new_lod):
            self._clean_up()

    @property
    def sim_info(self):
        return self._sim_info

    @property
    def has_data_to_save(self):
        return bool(self._equipped_jewels)

    def _get_outfits_in_category_gen(self, category:'int') -> 'Tuple[SimInfo, OutfitData]':
        sim_infos = []
        if self._sim_info.occult_tracker is not None:
            sim_infos.append((self._sim_info.occult_tracker.get_current_occult_types(), self._sim_info))
            occult_sim_infos = self._sim_info.occult_tracker.get_not_current_sim_infos()
            sim_infos.extend(occult_sim_infos)
        else:
            sim_infos.append((OccultType.HUMAN, self._sim_info))
        for (occult_type, sim_info) in sim_infos:
            for outfit in sim_info.get_outfits_in_category(category):
                yield (occult_type, sim_info, outfit)

    def track_jewel(self, jewel, apply_to_all_outfits:'bool'=True):
        if self._equipped_jewels is None:
            self._equipped_jewels = {}
        jewelry_component = jewel.get_component(JEWELRY_COMPONENT)
        cas_part = jewelry_component.get_cas_part(self.sim_info)
        part = get_caspart_bodytype(cas_part)
        if part not in self._equipped_jewels:
            self._equipped_jewels[part] = {}
        part_data = self._equipped_jewels[part]
        caspartid = CasPartObjectId(cas_part, jewel.id)
        elements_to_unequip = set()
        sim_infos = set()
        part_occult_type_flags = get_caspart_hide_occult_flags(cas_part)
        if apply_to_all_outfits:
            for category in self.WEREABLE_CATEGORIES:
                for (occult_type, sim_info, outfit_data) in self._get_outfits_in_category_gen(category):
                    if occult_type & part_occult_type_flags > 0:
                        pass
                    else:
                        outfit_id = outfit_data.outfit_id
                        if category in part_data and outfit_id in part_data[category]:
                            elements_to_unequip.add(part_data[category][outfit_id])
                        if category not in part_data:
                            part_data[category] = {}
                        part_data[category][outfit_id] = caspartid
                        sim_infos.add(sim_info)
        else:
            (current_outfit_category, current_outfit_data) = self.get_current_outfit_category_and_data()
            current_outfit_id = current_outfit_data.outfit_id
            if current_outfit_category in part_data and current_outfit_id in part_data[current_outfit_category]:
                elements_to_unequip.add(part_data[current_outfit_category][current_outfit_id])
            if current_outfit_category not in part_data:
                part_data[current_outfit_category] = {}
            part_data[current_outfit_category][current_outfit_id] = caspartid
            sim_infos.add(self.sim_info)
        sim_inventory = self._sim_info.get_sim_instance().inventory_component
        for element in elements_to_unequip:
            element_jewel = sim_inventory.try_get_item_by_id(element.object_id)
            element_jewelry_component = element_jewel.get_component(JEWELRY_COMPONENT)
            is_worn_in_any_outfit = not apply_to_all_outfits and self._is_worn_anywhere(element.object_id)
            element_jewelry_component.unequip(self._sim_info, apply_to_all_outfits, is_worn_in_any_outfit, False, None)
        jewelry_component.wear(self._sim_info, apply_to_all_outfits, True, sim_infos)
        sim_inventory.push_inventory_item_update_msg(jewel)

    def _is_worn_anywhere(self, object_id:'int') -> 'bool':
        for element in self._equipped_jewels.values():
            for data in element.values():
                for cas_part_id in data.values():
                    if cas_part_id.object_id == object_id:
                        return True
        return False

    def _is_worn(self, part:'int', category:'int', outfit_id:'int', object_id:'int') -> 'bool':
        return part in self._equipped_jewels and (category in self._equipped_jewels[part] and (outfit_id in self._equipped_jewels[part][category] and self._equipped_jewels[part][category][outfit_id].object_id == object_id))

    def untrack_jewel(self, jewel, apply_to_all_outfits:'bool') -> 'None':
        jewelry_component = jewel.get_component(JEWELRY_COMPONENT)
        cas_part = jewelry_component.get_cas_part(self.sim_info)
        part = get_caspart_bodytype(cas_part)
        part_data = self._equipped_jewels[part]
        (current_outfit_category, current_outfit_data) = self.get_current_outfit_category_and_data()
        current_outfit_id = current_outfit_data.outfit_id
        sim_infos = set()
        if apply_to_all_outfits:
            for category in self.WEREABLE_CATEGORIES:
                for (occult_type, sim_info, outfit_data) in self._get_outfits_in_category_gen(category):
                    outfit_id = outfit_data.outfit_id
                    if category in part_data and outfit_id in part_data[category] and part_data[category][outfit_id].object_id == jewel.id:
                        del part_data[category][outfit_id]
                        sim_infos.add(sim_info)
        elif current_outfit_category in part_data and current_outfit_id in part_data[current_outfit_category] and part_data[current_outfit_category][current_outfit_id].object_id == jewel.id:
            del part_data[current_outfit_category][current_outfit_id]
            sim_infos.add(self._sim_info)
        is_worn_in_other_outfit = not apply_to_all_outfits and self._is_worn_anywhere(jewel.id)
        jewelry_component.unequip(self._sim_info, apply_to_all_outfits, is_worn_in_other_outfit, True, sim_infos)

    def _clean_up(self):
        self._sim_info.unregister_for_outfit_changed_callback(self._on_sim_outfit_changed)
        self._sim_info = None
        self._equipped_jewels = None

    def save_equipped_jewelry(self, jewelry_data):
        if not self._equipped_jewels:
            return
        for (part, part_data) in self._equipped_jewels.items():
            for (category, category_element) in part_data.items():
                for (outfit_id, cas_part_object_id) in category_element.items():
                    with ProtocolBufferRollback(jewelry_data.cas_part_object_id_map) as body_part_cas_part_object_id:
                        body_part_cas_part_object_id.body_part = part
                        body_part_cas_part_object_id.cas_part = cas_part_object_id.cas_part
                        body_part_cas_part_object_id.object_id = cas_part_object_id.object_id
                        body_part_cas_part_object_id.outfit_category = category
                        body_part_cas_part_object_id.outfit_id = outfit_id

    def load_equipped_jewelry(self, jewelry_data):
        if not jewelry_data.cas_part_object_id_map:
            return
        self._equipped_jewels = {}
        for element in jewelry_data.cas_part_object_id_map:
            if element.body_part not in self._equipped_jewels:
                self._equipped_jewels[element.body_part] = {}
            if element.outfit_category not in self._equipped_jewels[element.body_part]:
                self._equipped_jewels[element.body_part][element.outfit_category] = {}
            if hasattr(element, 'outfit_id'):
                outfit_id = element.outfit_id
            else:
                (_, outfit_data) = self.get_current_outfit_category_and_data()
                outfit_id = outfit_data.outfit_id
            self._equipped_jewels[element.body_part][element.outfit_category][outfit_id] = CasPartObjectId(cas_part=element.cas_part, object_id=element.object_id)

    def on_sim_startup(self):
        self._check_missing_objects()
        self._check_outfit_changes()
        self.activate_buffs()
        self.refresh_tense_buff()

    def _check_missing_objects(self) -> 'None':
        if self._equipped_jewels is None:
            return
        sim = self._sim_info.get_sim_instance(allow_hidden_flags=ALL_HIDDEN_REASONS)
        if sim is None:
            return
        sim_inventory = sim.inventory_component
        missing_cas_parts = set()
        missing_elements = set()
        for (body_part, body_part_element) in self._equipped_jewels.items():
            for (category, category_element) in body_part_element.items():
                for (outfit_id, outfit_element) in category_element.items():
                    cas_part = outfit_element.cas_part
                    object_id = outfit_element.object_id
                    jewelry_object = sim_inventory.try_get_item_by_id(object_id)
                    if jewelry_object is None:
                        missing_cas_parts.add((object_id, cas_part))
                        missing_elements.add((body_part, category, outfit_id))
        for (body_part, category, outfit_id) in missing_elements:
            del self._equipped_jewels[body_part][category][outfit_id]
        for (missing_object_id, missing_cas_part) in missing_cas_parts:
            apply_to_all = not sim_inventory.is_object_shelved(missing_object_id)
            self._remove_part(missing_cas_part, apply_to_all)

    def get_current_outfit_category_and_data(self) -> '(int, OutfitData)':
        sim_outfits = self.sim_info.get_outfits()
        current_outfit = sim_outfits.get_current_outfit()
        current_category = current_outfit[0]
        current_outfit_data = sim_outfits.get_outfit(current_category, current_outfit[1])
        return (current_category, current_outfit_data)

    def _remove_part(self, cas_part:'int', apply_to_all:'bool') -> 'None':
        modifier = AppearanceModifier.RemoveCASPart(cas_part=cas_part, update_genetics=True, outfit_type_compatibility=None, appearance_modifier_tag=None, _is_combinable_with_same_type=False, object_id=0, should_refresh_thumbnail=False)
        element = AppearanceModifierTuple(modifier, TunableMultiplier.ONE)
        self.sim_info.appearance_tracker.add_appearance_modifiers(((element,),), self.sim_info.id, AppearanceModifierPriority.INVALID, apply_to_all, OutfitOverrideOptionFlags.DEFAULT, source='JewelryTracker')

    def activate_buffs(self) -> 'None':
        if not self._equipped_jewels:
            return
        sim = self._sim_info.get_sim_instance(allow_hidden_flags=ALL_HIDDEN_REASONS)
        if sim is None:
            return
        (current_outfit_category, current_outfit_data) = self.get_current_outfit_category_and_data()
        current_outfit_id = current_outfit_data.outfit_id
        sim_inventory = sim.inventory_component
        for element in self._equipped_jewels.values():
            if current_outfit_category in element and current_outfit_id in element[current_outfit_category]:
                object_id = element[current_outfit_category][current_outfit_id].object_id
                element_jewel = sim_inventory.try_get_item_by_id(object_id)
                if element_jewel is None:
                    pass
                else:
                    element_jewelry_component = element_jewel.get_component(JEWELRY_COMPONENT)
                    element_jewelry_component.add_buff(self._sim_info, True)

    def _get_equipped_object_ids(self, jewelry_dict:'dict') -> 'set(int)':
        object_ids = set()
        if not self._get_equipped_object_ids:
            return object_ids
        for body_part_element in jewelry_dict.values():
            for category_element in body_part_element.values():
                for outfit_element in category_element.values():
                    object_ids.add(outfit_element.object_id)
        return object_ids

    def _add_equipped_jewel(self, jewelry_dict:'dict', body_type:'int', category:'int', outfit_id:'int', cas_part:'int', object_id:'int'):
        if body_type not in jewelry_dict:
            jewelry_dict[body_type] = {}
        if category not in jewelry_dict[body_type]:
            jewelry_dict[body_type][category] = {}
        jewelry_dict[body_type][category][outfit_id] = CasPartObjectId(cas_part, object_id)

    def _update_object(self, object_ids:'set()', sim_inventory:'SimInventoryComponent', equipped_object_ids:'set()', equipped_object_ids_in_current_outfit:'set()', object_update_action:'ObjectUpdateAction') -> 'None':
        for object_id in object_ids:
            element_jewel = sim_inventory.try_get_item_by_id(object_id)
            if element_jewel is None:
                return
            element_jewelry_component = element_jewel.get_component(JEWELRY_COMPONENT)
            is_worn_in_any_outfit = object_id in equipped_object_ids
            is_worn_in_current_outfit = object_id in equipped_object_ids_in_current_outfit
            if object_update_action == ObjectUpdateAction.ADD and is_worn_in_current_outfit:
                element_jewelry_component.wear(self._sim_info, False, False, None)
            elif object_update_action == ObjectUpdateAction.REMOVE:
                element_jewelry_component.unequip(self._sim_info, False, is_worn_in_any_outfit, False, None)
            else:
                element_jewelry_component.set_worn_state(is_worn_in_current_outfit, is_worn_in_any_outfit, self._sim_info)

    def nested_dict_difference(self, dict1:'dict', dict2:'dict') -> 'dict':
        difference = {}
        for key in dict2:
            if key not in dict1:
                difference[key] = dict2[key]
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                nested_diff = self.nested_dict_difference(dict1[key], dict2[key])
                if nested_diff:
                    difference[key] = nested_diff
                    if dict1[key] != dict2[key]:
                        difference[key] = dict2[key]
            elif dict1[key] != dict2[key]:
                difference[key] = dict2[key]
        return difference

    def _check_outfit_changes(self) -> 'None':
        if self._equipped_jewels is None:
            return
        sim = self._sim_info.get_sim_instance(allow_hidden_flags=ALL_HIDDEN_REASONS)
        if sim is None:
            return
        sim_outfits = self.sim_info.get_outfits()
        sim_inventory = sim.inventory_component
        equipped_object_ids = set()
        equipped_object_ids_in_current_outfit = set()
        (_, current_outfit_data) = self.get_current_outfit_category_and_data()
        jewelry_dict = {}
        for category in self.WEREABLE_CATEGORIES:
            for (occult_type, sim_info, outfit_data) in self._get_outfits_in_category_gen(category):
                outfit_id = outfit_data.outfit_id
                count = len(outfit_data.body_types)
                for iPart in range(0, count):
                    part_objects_id = outfit_data.part_object_ids[iPart]
                    if part_objects_id > 0:
                        body_type = outfit_data.body_types[iPart]
                        self._add_equipped_jewel(jewelry_dict, body_type, category, outfit_data.outfit_id, outfit_data.part_ids[iPart], part_objects_id)
                        if category == current_outfit_data.outfit_category and outfit_id == current_outfit_data.outfit_id:
                            equipped_object_ids_in_current_outfit.add(part_objects_id)
                        equipped_object_ids.add(part_objects_id)
        removed_elements = self.nested_dict_difference(jewelry_dict, self._equipped_jewels)
        added_elements = self.nested_dict_difference(self._equipped_jewels, jewelry_dict)
        removed_elements_object_ids = self._get_equipped_object_ids(removed_elements)
        added_elements_object_ids = self._get_equipped_object_ids(added_elements)
        removed_object_ids = removed_elements_object_ids - added_elements_object_ids
        add_objects_ids = added_elements_object_ids - removed_elements_object_ids
        updated_elements = added_elements_object_ids.intersection(removed_elements)
        self._update_object(removed_object_ids, sim_inventory, equipped_object_ids, equipped_object_ids_in_current_outfit, ObjectUpdateAction.REMOVE)
        self._update_object(add_objects_ids, sim_inventory, equipped_object_ids, equipped_object_ids_in_current_outfit, ObjectUpdateAction.ADD)
        self._update_object(updated_elements, sim_inventory, equipped_object_ids, equipped_object_ids_in_current_outfit, ObjectUpdateAction.UPDATE)
        self._equipped_jewels = jewelry_dict

    def check_buffs(self, new_outfit_data:'OutfitData', old_outfit_data:'OutfitData') -> 'None':
        if self._equipped_jewels is None:
            return
        old_ids = set()
        new_ids = set()
        new_category = new_outfit_data.outfit_category
        new_outfit_id = new_outfit_data.outfit_id
        old_category = old_outfit_data.outfit_category
        old_outfit_id = old_outfit_data.outfit_id
        for element in self._equipped_jewels.values():
            if new_category in element and new_outfit_id in element[new_category]:
                new_ids.add(element[new_category][new_outfit_id].object_id)
        for element in self._equipped_jewels.values():
            if old_category in element and old_outfit_id in element[old_category]:
                old_ids.add(element[old_category][old_outfit_id].object_id)
        to_remove = old_ids.difference(new_ids)
        to_add = new_ids.difference(old_ids)
        if self._sim_info.get_sim_instance() is None:
            return
        for element in to_remove:
            sim_inventory = self._sim_info.get_sim_instance().inventory_component
            element_jewel = sim_inventory.try_get_item_by_id(element)
            if element_jewel is not None:
                element_jewelry_component = element_jewel.get_component(JEWELRY_COMPONENT)
                element_jewelry_component.remove_buff(self._sim_info)
                element_jewelry_component.set_worn_state(False, True, self._sim_info)
        for element in to_add:
            sim_inventory = self._sim_info.get_sim_instance().inventory_component
            element_jewel = sim_inventory.try_get_item_by_id(element)
            if element_jewel is not None:
                element_jewelry_component = element_jewel.get_component(JEWELRY_COMPONENT)
                element_jewelry_component.add_buff(self._sim_info, False)
                element_jewelry_component.set_worn_state(True, True, self._sim_info)

    def _on_sim_outfit_changed(self, sim_info:'SimInfo', outfit_category_and_index, old_outfit_category_and_index):
        if old_outfit_category_and_index is not None:
            sim_outfits = self.sim_info.get_outfits()
            new_outfit = sim_outfits.get_outfit(outfit_category_and_index[0], outfit_category_and_index[1])
            old_outfit = sim_outfits.get_outfit(old_outfit_category_and_index[0], old_outfit_category_and_index[1])
            self.check_buffs(new_outfit, old_outfit)
            self.refresh_tense_buff()

    def has_jewel_in_current_outfit(self, jewel_id:'int') -> 'bool':
        (current_outfit_category, current_outfit_data) = self.get_current_outfit_category_and_data()
        current_outfit_id = current_outfit_data.outfit_id
        for element in self._equipped_jewels.values():
            if not jewel_id is None:
                if element[current_outfit_category][current_outfit_id].object_id == jewel_id:
                    return True
            return True
        return False

    def has_jewel_in_current_outfit_and_part(self, jewel_id:'int', body_parts:'List[int]') -> 'bool':
        (current_outfit_category, current_outfit_data) = self.get_current_outfit_category_and_data()
        current_outfit_id = current_outfit_data.outfit_id
        for part in body_parts:
            if not jewel_id is None:
                if self._equipped_jewels[part][current_outfit_category][current_outfit_id].object_id == jewel_id:
                    return True
            return True
        return False

    def jewel_equipped_test(self, jewel_id:'int', body_parts:'List[int]') -> 'bool':
        if self._equipped_jewels is None:
            return False
        if not body_parts:
            return self.has_jewel_in_current_outfit(jewel_id)
        return self.has_jewel_in_current_outfit_and_part(jewel_id, body_parts)

    def has_bad_energy_jewel(self) -> 'bool':
        (current_category, current_outfit_data) = self.get_current_outfit_category_and_data()
        current_outfit_id = current_outfit_data.outfit_id
        sim = self._sim_info.get_sim_instance()
        if sim is None:
            return False
        sim_inventory = sim.inventory_component
        for element in self._equipped_jewels.values():
            if current_category in element and current_outfit_id in element[current_category]:
                object = element[current_category][current_outfit_id]
                element_jewel = sim_inventory.try_get_item_by_id(object.object_id)
                if element_jewel is not None and element_jewel.state_value_active(JewelryCraftingTuning.JEWELRY_DATA.bad_energy_state_value):
                    return True
        return False

    def refresh_tense_buff(self) -> 'None':
        if self._equipped_jewels is None:
            return
        has_bad_energy = self.has_bad_energy_jewel()
        if has_bad_energy and not self._sim_info.has_buff(JewelryCraftingTuning.JEWELRY_DATA.drained_buff.buff_type):
            self._sim_info.add_buff(JewelryCraftingTuning.JEWELRY_DATA.drained_buff.buff_type, buff_reason=JewelryCraftingTuning.JEWELRY_DATA.drained_buff.buff_reason)
        elif has_bad_energy or self._sim_info.has_buff(JewelryCraftingTuning.JEWELRY_DATA.drained_buff.buff_type):
            self._sim_info.remove_buff_by_type(JewelryCraftingTuning.JEWELRY_DATA.drained_buff.buff_type)

    def on_death(self):
        self._unequip_all_jewelry()

    def _unequip_all_jewelry(self):
        sim_inventory = self._sim_info.get_sim_instance().inventory_component
        equipped_jewels = dict(self._equipped_jewels)
        while equipped_jewels:
            (body_part, categories) = equipped_jewels.popitem()
            while categories:
                (category, outfit_ids) = categories.popitem()
                while outfit_ids:
                    (outfit_id, cas_object_part_id) = outfit_ids.popitem()
                    jewel = sim_inventory.try_get_item_by_id(cas_object_part_id.object_id)
                    if jewel is not None:
                        self.untrack_jewel(jewel, True)
