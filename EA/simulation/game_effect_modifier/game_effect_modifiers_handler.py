from collections import defaultdictimport servicesfrom sims4.gsi.dispatcher import GsiHandlerfrom sims4.gsi.schema import GsiGridSchemahandler_schema = GsiGridSchema(label='Game Effect Modifiers', sim_specific=True)handler_schema.add_field('modifier_type', label='Type')handler_schema.add_field('count', label='Count')with handler_schema.add_has_many('items', GsiGridSchema, label='Items') as sub_schema:
    sub_schema.add_field('modifier', label='Modifier')
@GsiHandler('game_effect_modifiers', handler_schema)
def generate_modifiers_data(sim_id:int=None):
    sim_info_manager = services.sim_info_manager()
    if sim_info_manager is None:
        return []
    sim_info = sim_info_manager.get(sim_id)
    if sim_info is None:
        return []
    modifiers_data = []
    modifiers_by_type = defaultdict(set)
    buff_component = sim_info.Buffs
    modifiers = [buff.effect_modification for buff in buff_component]
    for modifier in modifiers:
        for (modifier_type, modifiers_for_type) in modifier._modifier_map.items():
            modifiers_by_type[modifier_type].update(modifiers_for_type)
    for (modifier_type, modifiers_for_type) in modifiers_by_type.items():
        entry = {'modifier_type': str(modifier_type), 'count': len(modifiers_for_type)}
        items = []
        for (modifier, handle) in modifiers_for_type:
            items.append({'modifier': repr(modifier)})
        entry['items'] = items
        modifiers_data.append(entry)
    return modifiers_data
