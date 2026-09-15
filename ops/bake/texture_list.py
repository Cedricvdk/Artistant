import bpy

from ..common.image_nodes import iter_object_image_texture_nodes


class ARTISTANT_texture_list_item(bpy.types.PropertyGroup):
    """One row in the Bake texture list: an Image Texture node found on the active object."""
    # `name` (the found image's name) is provided automatically by PropertyGroup.
    material_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()


class ARTISTANT_UL_bake_textures(bpy.types.UIList):
    """Scrollable list of image textures found on the active object's materials."""
    bl_idname = "ARTISTANT_UL_bake_textures"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name, icon='IMAGE_DATA')


def sync_bake_texture_list(context):
    """Rebuild scene.bake_texture_list to match the active object's current
    image texture nodes, but only when the set of textures actually changed
    (avoids resetting the list's selection on every panel redraw).
    """
    scene = context.scene
    found = []
    seen = set()
    for mat, node in iter_object_image_texture_nodes(context.active_object):
        image_name = node.image.name
        if image_name in seen:
            continue
        seen.add(image_name)
        found.append((image_name, mat.name, node.name))

    existing_names = [item.name for item in scene.bake_texture_list]
    if existing_names == [name for name, _, _ in found]:
        return

    scene.bake_texture_list.clear()
    for image_name, mat_name, node_name in found:
        item = scene.bake_texture_list.add()
        item.name = image_name
        item.material_name = mat_name
        item.node_name = node_name

    if scene.bake_texture_list_index >= len(scene.bake_texture_list):
        scene.bake_texture_list_index = max(0, len(scene.bake_texture_list) - 1)


def get_selected_texture_name(context):
    """Return the currently selected list row's image name, or None if empty."""
    items = context.scene.bake_texture_list
    index = context.scene.bake_texture_list_index
    if 0 <= index < len(items):
        return items[index].name
    return None


class ARTISTANT_OT_refresh_bake_texture_list(bpy.types.Operator):
    """Rebuild the bake texture list for the active object"""
    bl_idname = "artistant.refresh_bake_texture_list"
    bl_label = "Refresh Texture List"
    bl_description = "Rebuild the texture list from the active object's current materials"
    bl_options = {'REGISTER'}

    def execute(self, context):
        sync_bake_texture_list(context)
        return {'FINISHED'}


# Panel.draw() runs in a restricted context that disallows writing ID data
# (e.g. Scene.bake_texture_list.clear()), so the list can't be rebuilt there.
# msgbus lets us rebuild it from a normal callback whenever the active object
# changes instead; the Refresh operator above covers cases that don't involve
# switching objects (e.g. editing nodes on the same object).
_msgbus_owner = object()


def _redraw_image_editors():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.tag_redraw()


def _on_active_object_changed():
    sync_bake_texture_list(bpy.context)
    _redraw_image_editors()


def register_active_object_watcher():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerObjects, "active"),
        owner=_msgbus_owner,
        args=(),
        notify=_on_active_object_changed,
        options={'PERSISTENT'},
    )
    _on_active_object_changed()


def unregister_active_object_watcher():
    bpy.msgbus.clear_by_owner(_msgbus_owner)
