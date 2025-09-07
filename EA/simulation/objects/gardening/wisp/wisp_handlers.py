import gsi_handlersimport servicesfrom sims4.gsi.dispatcher import GsiHandlerfrom sims4.gsi.schema import GsiGridSchemawisp_schema = GsiGridSchema(label='Wisp', auto_refresh=True)wisp_schema.add_field('is_active', label='Is Active', width=1)wisp_schema.add_field('current_state', label='Current State', width=1)with wisp_schema.add_has_many('effected_plant_object_data', GsiGridSchema) as plant_data_schema:
    plant_data_schema.add_field('object_id', label='Object ID', width=1, unique_field=True)
    plant_data_schema.add_field('class', label='Class', width=3)
    plant_data_schema.add_field('definition', label='Definition', width=3)with wisp_schema.add_view_cheat('objects.focus_camera_on_object', label='Focus On Selected Object') as cheat:
    cheat.add_token_param('object_id')
@GsiHandler('wisp_data', wisp_schema)
def generate_wisp_data(*args, **kwargs):
    wisp_data = []
    object_manager = services.object_manager()
    wisp_service = services.get_wisp_service()
    wisp = wisp_service.get_wisp()
    if object_manager is None or wisp_service is None or wisp is None:
        return wisp_data
    is_active = wisp.is_active
    current_state = wisp.current_state
    entry = {'is_active': str(is_active), 'current_state': str(current_state), 'effected_plant_object_data': []}
    if is_active:
        for plant_object_id in wisp.current_state.get_effected_plant_object_ids():
            plant_object = object_manager.get(plant_object_id)
            if plant_object is None:
                pass
            else:
                entry['effected_plant_object_data'].append({'object_id': hex(plant_object_id), 'class': gsi_handlers.gsi_utils.format_object_name(plant_object), 'definition': str(plant_object.definition.name)})
    wisp_data.append(entry)
    return wisp_data
