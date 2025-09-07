from __future__ import annotationsfrom event_testing.resolver import SingleSimResolverfrom protocolbuffers import SimObjectAttributes_pb2import servicesimport sims4from buffs.appearance_modifier.appearance_modifier import AppearanceModifier, AppearanceModifierPriorityfrom cas.cas import OutfitOverrideOptionFlags, get_caspart_bodytype, caspart_has_tagfrom dataclasses import dataclassfrom distributor.rollback import ProtocolBufferRollbackfrom objects.components.jewelry_component import AppearanceModifierTuplefrom rewards.tunable_reward_base import TunableRewardBasefrom sims.occult.occult_enums import OccultTypefrom sims.outfits.outfit_enums import BodyTypefrom sims.sim_info_tracker import SimInfoTrackerfrom sims4.common import Packfrom sims4.localization import LocalizationHelperTuningfrom sims4.math import Operatorfrom sims4.tuning.tunable import TunableOperatorfrom sims4.utils import classpropertyfrom tattoo.tattoo_tuning import TattooQuality, TattooSentimentType, TattooTuningfrom tunable_multiplier import TunableMultiplierfrom typing import TYPE_CHECKINGif TYPE_CHECKING:
    from typing import *
    from sims.sim_info import SimInfo
    from tattoo.tattoo_tuning import CheckTattooDataNotificationlogger = sims4.log.Logger('TattooTracker')
@dataclass
class TattooData:
    __annotations__['quality'] = 'TattooQuality'
    __annotations__['sentimental_target'] = 'int'
    __annotations__['sentimental_type'] = 'TattooSentimentType'
    __annotations__['subparts_hash_list'] = 'list'
    __annotations__['custom_texture'] = 'int'

    def __hash__(self):
        return hash((self.quality, self.sentimental_target, self.sentimental_type))

class TattooTracker(SimInfoTracker):

    def __init__(self, sim_info:'SimInfo'):
        self._sim_info = sim_info
        self._equipped_tattoos = None
        self._pending_tattoo_data = None
        self._stored_picked_tattoo = 0

    @classproperty
    def required_packs(cls):
        return (Pack.EP18,)

    def on_lod_update(self, old_lod, new_lod):
        if not self.is_valid_for_lod(new_lod):
            self._clean_up()

    @property
    def sim_info(self):
        return self._sim_info

    def get_current_equipped_tattoos(self, create_if_not_set:'bool'=False) -> 'Dict':
        current_occult_type = self._sim_info.occult_tracker.get_current_occult_types()
        if create_if_not_set:
            self._equipped_tattoos = {}
            self._equipped_tattoos[current_occult_type] = {}
        if current_occult_type not in self._equipped_tattoos:
            self._equipped_tattoos[current_occult_type] = {}
        if self._equipped_tattoos is None and create_if_not_set and self._equipped_tattoos is not None and current_occult_type in self._equipped_tattoos:
            return self._equipped_tattoos[current_occult_type]

    @property
    def has_data_to_save(self) -> 'bool':
        return bool(self._equipped_tattoos) or (self._pending_tattoo_data is not None or self._stored_picked_tattoo != 0)

    def save_equipped_tattoos(self, tattoo_saved_data) -> 'bool':
        if self._equipped_tattoos:
            for (occult_type, equipped_tattoos) in self._equipped_tattoos.items():
                for (body_type, tattoo_data) in equipped_tattoos.items():
                    with ProtocolBufferRollback(tattoo_saved_data.body_type_tattoo_data) as body_type_tattoo_data:
                        body_type_tattoo_data.body_type = body_type
                        body_type_tattoo_data.quality = tattoo_data.quality
                        body_type_tattoo_data.sentimental_type = tattoo_data.sentimental_type
                        body_type_tattoo_data.sentimental_target = tattoo_data.sentimental_target
                        body_type_tattoo_data.body_part_hashes.extend(tattoo_data.subparts_hash_list)
                        body_type_tattoo_data.body_part_custom_texture = tattoo_data.custom_texture
                        if hasattr(body_type_tattoo_data, 'occult_type'):
                            body_type_tattoo_data.occult_type = occult_type
        if self._pending_tattoo_data is not None:
            pending_tattoo_data = SimObjectAttributes_pb2.TattooData()
            pending_tattoo_data.body_type = BodyType.NONE
            pending_tattoo_data.quality = self._pending_tattoo_data.quality
            pending_tattoo_data.sentimental_type = self._pending_tattoo_data.sentimental_type
            pending_tattoo_data.sentimental_target = self._pending_tattoo_data.sentimental_target
            tattoo_saved_data.pending_tattoo_data = pending_tattoo_data
        if hasattr(tattoo_saved_data, 'stored_picked_tattoo'):
            tattoo_saved_data.stored_picked_tattoo = self._stored_picked_tattoo
        return True

    def load_equipped_tatoo_data(self, tatoo_saved_data) -> 'None':
        if tatoo_saved_data.body_type_tattoo_data or sims4.protocol_buffer_utils.has_field(tatoo_saved_data, 'pending_tattoo_data') and tatoo_saved_data.pending_tattoo_data is None and sims4.protocol_buffer_utils.has_field(tatoo_saved_data, 'stored_picked_tattoo') and tatoo_saved_data.stored_picked_tattoo == 0:
            return
        self._equipped_tattoos = {}
        for element in tatoo_saved_data.body_type_tattoo_data:
            if hasattr(element, 'occult_type'):
                occult_type = element.occult_type
            else:
                occult_type = OccultType.HUMAN
            body_type = element.body_type
            quality = element.quality
            sentimental_type = element.sentimental_type
            sentimental_target = element.sentimental_target
            tattoo_data = None
            if occult_type not in self._equipped_tattoos:
                self._equipped_tattoos[occult_type] = {}
            equipped_tattoos = self._equipped_tattoos[occult_type]
            if body_type not in equipped_tattoos:
                tattoo_data = TattooData(quality=quality, sentimental_target=sentimental_target, sentimental_type=sentimental_type, subparts_hash_list=list(), custom_texture=0)
                equipped_tattoos[body_type] = tattoo_data
            else:
                tattoo_data = equipped_tattoos[body_type]
            tattoo_data.subparts_hash_list = list(element.body_part_hashes)
            tattoo_data.custom_texture = element.body_part_custom_texture
        if sims4.protocol_buffer_utils.has_field(tatoo_saved_data, 'pending_tattoo_data'):
            pending_tattoo_data = tatoo_saved_data.pending_tattoo_data
            if pending_tattoo_data is not None:
                self._pending_tattoo_data = TattooData(quality=pending_tattoo_data.quality, sentimental_type=pending_tattoo_data.sentimental_type, sentimental_target=pending_tattoo_data.sentimental_target, subparts_hash_list=list(), custom_texture=0)
        if sims4.protocol_buffer_utils.has_field(tatoo_saved_data, 'stored_picked_tattoo'):
            self._stored_picked_tattoo = tatoo_saved_data.stored_picked_tattoo

    def get_free_layer(self, body_type:'BodyType') -> 'int':
        current_equipped_tattoos = self.get_current_equipped_tattoos()
        if current_equipped_tattoos is not None and body_type in current_equipped_tattoos:
            tattoo_data = current_equipped_tattoos[body_type]
            layer = tattoo_data.subparts_hash_list.index(0) if 0 in tattoo_data.subparts_hash_list else len(tattoo_data.subparts_hash_list)
            return layer
        return 0

    def has_free_layer_in_bodytype(self, body_type:'BodyType') -> 'bool':
        layer = self.get_free_layer(body_type)
        return layer < TattooTuning.TATTOO_MAX_LAYERS

    def has_free_layer(self) -> 'bool':
        for body_type in TattooTuning.TATTOO_BODY_TYPES:
            if self.has_free_layer_in_bodytype(body_type):
                return True
        return False

    def get_filtered_tattoo_data(self, body_types, quality:'TattooQuality', quality_comparison, sentiment_type, sentimental_target_id:'int', sentimental_target_comparison:'TunableOperator') -> 'set':
        result = set()
        current_equipped_tattoos = self.get_current_equipped_tattoos()
        if current_equipped_tattoos is None:
            return result
        body_types_list = body_types if body_types else TattooTuning.TATTOO_BODY_TYPES
        for body_type in body_types_list:
            if body_type not in current_equipped_tattoos:
                pass
            else:
                tattoo_data = current_equipped_tattoos[body_type]
                if quality is not None:
                    threshold = sims4.math.Threshold(quality, quality_comparison)
                    if not threshold.compare(tattoo_data.quality):
                        pass
                    elif sentiment_type is not None and sentiment_type != tattoo_data.sentimental_type:
                        pass
                    elif sentimental_target_id and not sentimental_target_comparison(sentimental_target_id, tattoo_data.sentimental_target):
                        pass
                    else:
                        result.add(tattoo_data)
                elif sentiment_type is not None and sentiment_type != tattoo_data.sentimental_type:
                    pass
                elif sentimental_target_id and not sentimental_target_comparison(sentimental_target_id, tattoo_data.sentimental_target):
                    pass
                else:
                    result.add(tattoo_data)
        return result

    def track_custom_tatoo(self, quality:'TattooQuality', sentimental_target:'int'=0, sentimental_type:'TattooSentimentType'=None) -> 'None':
        if TattooTuning.TATTOOING_PROCESS_BUFFS is not None:
            buff = TattooTuning.TATTOOING_PROCESS_BUFFS.waiting_for_result
            if buff is not None:
                self._sim_info.add_buff_from_op(buff.buff_type, buff.buff_reason)
        self._pending_tattoo_data = TattooData(quality, sentimental_target, sentimental_type, list(), 0)

    def track_regular_tattoo(self, cas_part:'int', quality:'TattooQuality', sentimental_target:'int'=0, sentimental_type:'TattooSentimentType'=None) -> 'None':
        if self._equipped_tattoos is None:
            self._equipped_tattoos = {}
        current_equipped_tattoos = self.get_current_equipped_tattoos(True)
        body_type = get_caspart_bodytype(cas_part)
        layer = 0
        tattoo_data = None
        if body_type in current_equipped_tattoos:
            tattoo_data = current_equipped_tattoos[body_type]
            layer = self.get_free_layer(body_type)
        if cas_part is not None:
            self.apply_add_modifier(cas_part, layer)
        if tattoo_data is None:
            tattoo_data = TattooData(quality=quality, sentimental_target=sentimental_target, sentimental_type=sentimental_type, subparts_hash_list=list(), custom_texture=0)
        else:
            sentimental_target = sentimental_target if sentimental_target != 0 else tattoo_data.sentimental_target
            sentimental_type = sentimental_type if sentimental_type is not None and sentimental_type != TattooSentimentType.NONE else tattoo_data.sentimental_type
            tattoo_data.quality = quality
            tattoo_data.sentimental_target = sentimental_target
            tattoo_data.sentimental_type = sentimental_type
        outfits = self._sim_info.get_outfits()
        current_outfit_values = self._sim_info.get_current_outfit()
        current_outfit = outfits.get_outfit(*current_outfit_values)
        part_hashes = current_outfit.part_hashes
        if body_type not in part_hashes:
            if body_type in current_equipped_tattoos:
                del current_equipped_tattoos[body_type]
            return
        tattoo_data.subparts_hash_list = part_hashes[body_type]
        current_equipped_tattoos[body_type] = tattoo_data

    def track_tattoo(self, cas_part:'int', quality:'TattooQuality', sentimental_target:'int'=0, sentimental_type:'TattooSentimentType'=None, unlock_design_participant:'SimInfo'=None) -> 'None':
        if cas_part is not None:
            self.track_regular_tattoo(cas_part, quality, sentimental_target, sentimental_type)
            if unlock_design_participant is not None:
                household = unlock_design_participant.household
                if not household.part_in_reward_inventory(cas_part):
                    household.add_cas_part_to_reward_inventory(cas_part, sim_id=unlock_design_participant.id)
                    TunableRewardBase.send_unlock_telemetry(unlock_design_participant, cas_part, 0)
        else:
            self.track_custom_tatoo(quality, sentimental_target, sentimental_type)

    def remove_tattoo(self, body_types:'list[BodyType]') -> 'None':
        body_types_list = body_types if body_types else TattooTuning.TATTOO_BODY_TYPES
        for body_type in body_types_list:
            modifier = AppearanceModifier.RemoveCASPartByBodyType(body_type=body_type, update_genetics=True, outfit_type_compatibility=None, appearance_modifier_tag=None, _is_combinable_with_same_type=False, should_refresh_thumbnail=False, remove_custom_textures=True)
            element = AppearanceModifierTuple(modifier, TunableMultiplier.ONE)
            self.sim_info.appearance_tracker.add_appearance_modifiers(((element,),), self.sim_info.id, AppearanceModifierPriority.INVALID, True, OutfitOverrideOptionFlags.APPLY_IN_CURRENT_MODIFIED_SIM_INFO | OutfitOverrideOptionFlags.OVERRIDE_TATTOO_CUSTOM_TEXTURES, source='tattoo_tracker')
            current_equipped_tattoos = self.get_current_equipped_tattoos()
            if current_equipped_tattoos is not None and body_type in current_equipped_tattoos:
                del current_equipped_tattoos[body_type]

    def set_quality(self, body_types:'list[BodyType]', quality:'TattooQuality') -> 'None':
        body_types_list = body_types if body_types else TattooTuning.TATTOO_BODY_TYPES
        current_equipped_tattoos = self.get_current_equipped_tattoos()
        for body_type in body_types_list:
            if body_type in current_equipped_tattoos:
                current_equipped_tattoos[body_type].quality = quality

    def _clean_up(self):
        self._sim_info = None
        self._equipped_tattoos = None

    def on_sim_startup(self):
        self._check_equipped_tattoos()

    def apply_add_modifier(self, cas_part:'int', layer:'int') -> 'None':
        modifier = AppearanceModifier.SetCASPart(cas_part=cas_part, should_toggle=False, replace_with_random=False, update_genetics=True, _is_combinable_with_same_type=False, remove_conflicting=True, outfit_type_compatibility=None, appearance_modifier_tag=None, expect_invalid_parts=False, hsv_color_shift=None, object_id=None, part_layer_index=layer, rgba_color_shift=0, should_refresh_thumbnail=False)
        element = AppearanceModifierTuple(modifier, TunableMultiplier.ONE)
        self.sim_info.appearance_tracker.add_appearance_modifiers(((element,),), self.sim_info.id, AppearanceModifierPriority.INVALID, True, OutfitOverrideOptionFlags.APPLY_IN_CURRENT_MODIFIED_SIM_INFO, source='TattooTracker')

    def check_modified_tattoos(self) -> 'None':
        current_equipped_tattoos = self.get_current_equipped_tattoos(True)
        outfits = self._sim_info.get_outfits()
        current_outfit_values = self._sim_info.get_current_outfit()
        current_outfit = outfits.get_outfit(*current_outfit_values)
        modified = False
        current_outfit_part_hashes_dic = current_outfit.part_hashes
        custom_tattoos_dic = self._sim_info.parts_custom_tattoos
        for body_type in TattooTuning.TATTOO_BODY_TYPES:
            if body_type not in current_outfit_part_hashes_dic and body_type not in custom_tattoos_dic:
                if body_type in current_equipped_tattoos:
                    del current_equipped_tattoos[body_type]
                    part_hashes = current_outfit_part_hashes_dic[body_type] if body_type in current_outfit_part_hashes_dic else list()
                    custom_texture = custom_tattoos_dic[body_type] if body_type in custom_tattoos_dic else 0
                    quality = TattooTuning.TATTOO_DEFAULT_QUALITY
                    sentimental_type = TattooTuning.TATTOO_DEFAULT_SENTIMENTAL_TYPE_VALUE
                    sentimental_target = 0
                    pending_sentimental_target = 0
                    pending_sentimental_type = TattooSentimentType.NONE
                    if self._pending_tattoo_data is not None:
                        quality = self._pending_tattoo_data.quality
                        pending_sentimental_target = self._pending_tattoo_data.sentimental_target
                        pending_sentimental_type = self._pending_tattoo_data.sentimental_type
                    if body_type in current_equipped_tattoos:
                        current_sentimental_target = current_equipped_tattoos[body_type].sentimental_target
                        current_sentimental_type = current_equipped_tattoos[body_type].sentimental_type
                        sentimental_target = pending_sentimental_target if pending_sentimental_target != 0 else current_sentimental_target
                        sentimental_type = pending_sentimental_type if pending_sentimental_type != TattooSentimentType.NONE else current_sentimental_type
                        current_equipped_tattoos[body_type].sentimental_type = sentimental_type
                        current_equipped_tattoos[body_type].sentimental_target = sentimental_target
                        if current_equipped_tattoos[body_type].subparts_hash_list != part_hashes:
                            current_equipped_tattoos[body_type].subparts_hash_list = part_hashes
                            modified = len(part_hashes) > 0
                        if current_equipped_tattoos[body_type].custom_texture != custom_texture:
                            current_equipped_tattoos[body_type].custom_texture = custom_texture
                            modified = custom_texture > 0
                            tattoo_data = TattooData(quality=quality, sentimental_target=sentimental_target, sentimental_type=sentimental_type, subparts_hash_list=part_hashes, custom_texture=custom_texture)
                            current_equipped_tattoos[body_type] = tattoo_data
                            modified = True
                    else:
                        tattoo_data = TattooData(quality=quality, sentimental_target=sentimental_target, sentimental_type=sentimental_type, subparts_hash_list=part_hashes, custom_texture=custom_texture)
                        current_equipped_tattoos[body_type] = tattoo_data
                        modified = True
            else:
                part_hashes = current_outfit_part_hashes_dic[body_type] if body_type in current_outfit_part_hashes_dic else list()
                custom_texture = custom_tattoos_dic[body_type] if body_type in custom_tattoos_dic else 0
                quality = TattooTuning.TATTOO_DEFAULT_QUALITY
                sentimental_type = TattooTuning.TATTOO_DEFAULT_SENTIMENTAL_TYPE_VALUE
                sentimental_target = 0
                pending_sentimental_target = 0
                pending_sentimental_type = TattooSentimentType.NONE
                if self._pending_tattoo_data is not None:
                    quality = self._pending_tattoo_data.quality
                    pending_sentimental_target = self._pending_tattoo_data.sentimental_target
                    pending_sentimental_type = self._pending_tattoo_data.sentimental_type
                if body_type in current_equipped_tattoos:
                    current_sentimental_target = current_equipped_tattoos[body_type].sentimental_target
                    current_sentimental_type = current_equipped_tattoos[body_type].sentimental_type
                    sentimental_target = pending_sentimental_target if pending_sentimental_target != 0 else current_sentimental_target
                    sentimental_type = pending_sentimental_type if pending_sentimental_type != TattooSentimentType.NONE else current_sentimental_type
                    current_equipped_tattoos[body_type].sentimental_type = sentimental_type
                    current_equipped_tattoos[body_type].sentimental_target = sentimental_target
                    if current_equipped_tattoos[body_type].subparts_hash_list != part_hashes:
                        current_equipped_tattoos[body_type].subparts_hash_list = part_hashes
                        modified = len(part_hashes) > 0
                    if current_equipped_tattoos[body_type].custom_texture != custom_texture:
                        current_equipped_tattoos[body_type].custom_texture = custom_texture
                        modified = custom_texture > 0
                        tattoo_data = TattooData(quality=quality, sentimental_target=sentimental_target, sentimental_type=sentimental_type, subparts_hash_list=part_hashes, custom_texture=custom_texture)
                        current_equipped_tattoos[body_type] = tattoo_data
                        modified = True
                else:
                    tattoo_data = TattooData(quality=quality, sentimental_target=sentimental_target, sentimental_type=sentimental_type, subparts_hash_list=part_hashes, custom_texture=custom_texture)
                    current_equipped_tattoos[body_type] = tattoo_data
                    modified = True
        if TattooTuning.TATTOOING_PROCESS_BUFFS is not None:
            buff = TattooTuning.TATTOOING_PROCESS_BUFFS.finished if modified else TattooTuning.TATTOOING_PROCESS_BUFFS.cancelled
            if buff is not None:
                self._sim_info.add_buff_from_op(buff.buff_type, buff.buff_reason)
        self._pending_tattoo_data = None

    def _fixup_non_layered_tattoos(self) -> 'None':
        if self._equipped_tattoos is not None:
            return
        equipped_tattoos = {}
        outfits = self._sim_info.get_outfits()
        current_outfit_values = self._sim_info.get_current_outfit()
        current_outfit = outfits.get_outfit(*current_outfit_values)
        body_types = list(current_outfit.body_types)
        custom_tattoos_dic = self._sim_info.parts_custom_tattoos
        part_hashes = current_outfit.part_hashes
        if part_hashes:
            return
        for body_type in TattooTuning.TATTOO_BODY_TYPES:
            if body_type in body_types:
                idx = current_outfit.body_types.index(body_type)
                part_id = current_outfit.part_ids[idx]
                if part_id != 0:
                    ignore_part = caspart_has_tag(part_id, list(TattooTuning.IGNORE_TAGS))
                    if not ignore_part:
                        self.apply_add_modifier(part_id, 0)
                        current_outfit = outfits.get_outfit(*current_outfit_values)
                    if body_type not in part_hashes and body_type not in custom_tattoos_dic:
                        pass
                    else:
                        part_hashes_by_body_type = part_hashes[body_type] if body_type in part_hashes else list()
                        custom_texture_by_body_type = custom_tattoos_dic[body_type] if body_type in custom_tattoos_dic else 0
                        tattoo_data = TattooData(quality=TattooTuning.TATTOO_DEFAULT_QUALITY, sentimental_target=0, sentimental_type=0, subparts_hash_list=part_hashes_by_body_type, custom_texture=custom_texture_by_body_type)
                        equipped_tattoos[body_type] = tattoo_data
        if equipped_tattoos:
            self._equipped_tattoos = {}
            current_occult_type = self._sim_info.occult_tracker.get_current_occult_types()
            self._equipped_tattoos[current_occult_type] = equipped_tattoos

    def _check_equipped_tattoos(self) -> 'None':
        self._fixup_non_layered_tattoos()
        self.check_modified_tattoos()

    def show_check_tattoo_notification(self):
        data = self.get_current_equipped_tattoos()
        sim_info_manager = services.sim_info_manager()
        lines = []
        notification = TattooTuning.CHECK_TATTOO_NOTIFICATION
        for (body_type, tattoo_data) in data.items():
            quality = tattoo_data.quality
            sentimental_type = tattoo_data.sentimental_type
            sentimental_target = tattoo_data.sentimental_target
            if sentimental_target != 0:
                sim_info = sim_info_manager.get(sentimental_target)
                if sim_info is not None:
                    lines.append(notification.sentimental_entry(notification.body_type_strings[body_type](), notification.quality_strings[quality](), sim_info, notification.sentiment_type_strings[sentimental_type]()))
                else:
                    lines.append(notification.sentimental_no_sim_entry(notification.body_type_strings[body_type](), notification.quality_strings[quality](), notification.sentiment_type_strings[sentimental_type]()))
                    lines.append(notification.non_sentimental(notification.body_type_strings[body_type](), notification.quality_strings[quality]()))
            else:
                lines.append(notification.non_sentimental(notification.body_type_strings[body_type](), notification.quality_strings[quality]()))
        notification_lines = LocalizationHelperTuning.get_new_line_separated_strings(lines)
        notification_bullets = LocalizationHelperTuning.get_bulleted_list((None,), tuple(notification_lines))
        resolver = SingleSimResolver(self.sim_info)
        dialog = notification.notification(self.sim_info, resolver, text=lambda *_: notification_bullets)
        dialog.show_dialog()

    def get_sentimental_tattoo_sims(self, sentiment_type:'TattooSentimentType', sim_id:'int', comparison:'TunableOperator') -> 'set()':
        sim_ids = set()
        current_equipped_tattoos = self.get_current_equipped_tattoos()
        if current_equipped_tattoos is None:
            return sim_ids
        for data in current_equipped_tattoos.values():
            if not sim_id is None:
                if comparison(sim_id, data.sentimental_target):
                    sim_ids.add(data.sentimental_target)
            sim_ids.add(data.sentimental_target)
        return sim_ids

    def store_picked_tattoo(self, picked_tattoo:'int') -> 'None':
        self._stored_picked_tattoo = picked_tattoo

    def get_picked_tattoo(self) -> 'int':
        return self._stored_picked_tattoo
