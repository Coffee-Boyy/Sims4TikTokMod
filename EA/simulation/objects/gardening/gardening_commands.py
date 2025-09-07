from objects.components import typesfrom objects.components.types import GARDENING_COMPONENTfrom sims4.commands import CommandTypeimport servicesimport sims4.commandsfrom sims4.common import Pack
@sims4.commands.Command('gardening.cleanup_gardening_objects')
def cleanup_gardening_objects(_connection=None):
    for obj in services.object_manager().get_all_objects_with_component_gen(GARDENING_COMPONENT):
        gardening_component = obj.get_component(types.GARDENING_COMPONENT)
        if not gardening_component.is_fruit_seed:
            pass
        elif obj.parent is None and not (obj.is_in_inventory() or obj.is_on_active_lot()):
            sims4.commands.output('Destroyed object {} on open street was found without a parent at position {}, parent_type {}.'.format(obj, obj.position, obj.parent_type), _connection)
            obj.destroy(source=obj, cause='Fruit/Flower with no parent on open street')
    sims4.commands.output('Gardening cleanup complete', _connection)
    return True

@sims4.commands.Command('gardening.remove_all_fruits', command_type=CommandType.Automation)
def remove_all_fruits(_connection=None):
    objs_to_delete = []
    for obj in services.object_manager().get_all_objects_with_component_gen(GARDENING_COMPONENT):
        gardening_component = obj.get_component(types.GARDENING_COMPONENT)
        if not gardening_component.is_fruit_seed:
            pass
        else:
            objs_to_delete.append(obj)
    for obj in objs_to_delete:
        sims4.commands.output('Destroyed object {} at position {}, parent_type {}.'.format(obj, obj.position, obj.parent_type), _connection)
        obj.destroy(source=obj, cause='Destroyed by cheat command gardening.remove_all_fruits')
    sims4.commands.output('Gardening cleanup complete', _connection)
    return True

@sims4.commands.Command('gardening.force_start_wisp', pack=Pack.EP19, command_type=CommandType.DebugOnly)
def force_start_wisp_on_gardening_object(source_plant_id:int, _connection=None):
    source_plant_object = services.object_manager().get(source_plant_id)
    if source_plant_object is None:
        return False
    wisp_service = services.get_wisp_service()
    if wisp_service is None:
        return False
    wisp_service.force_start_wisp_on_object(source_plant_id)

@sims4.commands.Command('gardening.stop_wisp', pack=Pack.EP19, command_type=CommandType.DebugOnly)
def stop_wisp(_connection=None):
    wisp_service = services.get_wisp_service()
    if wisp_service is None:
        return False
    wisp_service.stop_wisp()
