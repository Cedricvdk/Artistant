import bpy

# Import all operator and UI classes to register
from ..ui.panel_main import ARTISTANT_PT_panel
from ..ui.panel_uv import ARTISTANT_PT_uv_panel
from ..ops.modeling.smart_group import ARTISTANT_OT_smart_group_operator
from ..ops.modeling.floor_pivot import ARTISTANT_OT_floor_pivot
from ..ops.modeling.floor_object import ARTISTANT_OT_floor_object
from ..ops.export.unity_fbx import ARTISTANT_OT_export_unity_fbx
from ..ops.util.reload_images import ARTISTANT_OT_reload_images
from ..ops.visualization.visualize_normals import ARTISTANT_OT_visualize_normals
from ..ops.selection.select_by_name import ARTISTANT_OT_select_by_name
from ..ops.selection.select_orphans import ARTISTANT_OT_select_orphans
from ..ops.bake.bake import ARTISTANT_OT_bake
from ..ops.bake.preview_shading import ARTISTANT_OT_preview_bake
from ..ops.bake.texture_list import (
    ARTISTANT_texture_list_item,
    ARTISTANT_UL_bake_textures,
    ARTISTANT_OT_refresh_bake_texture_list,
    register_active_object_watcher,
    unregister_active_object_watcher,
)
from .properties import register_scene_properties, unregister_scene_properties


# Central registry of all classes to be registered with Blender
classes = (
    ARTISTANT_PT_panel,
    ARTISTANT_PT_uv_panel,
    ARTISTANT_OT_smart_group_operator,
    ARTISTANT_OT_floor_pivot,
    ARTISTANT_OT_floor_object,
    ARTISTANT_OT_export_unity_fbx,
    ARTISTANT_OT_reload_images,
    ARTISTANT_OT_visualize_normals,
    ARTISTANT_OT_select_by_name,
    ARTISTANT_OT_select_orphans,
    ARTISTANT_texture_list_item,
    ARTISTANT_UL_bake_textures,
    ARTISTANT_OT_bake,
    ARTISTANT_OT_preview_bake,
    ARTISTANT_OT_refresh_bake_texture_list,
)


def register():
    """Register all operator, panel, and scene property classes with Blender."""
    # Register operator and panel classes with Blender's registration system
    for cls in classes:
        bpy.utils.register_class(cls)
    # Register custom scene properties (export folder, export mode, etc.)
    register_scene_properties()
    # Keep the bake texture list in sync with the active object (see
    # ops/bake/texture_list.py for why this can't just happen in Panel.draw()).
    register_active_object_watcher()


def unregister():
    """Unregister all scene properties and operator/panel classes from Blender."""
    # Unregister in reverse order: watcher and properties first, then classes
    unregister_active_object_watcher()
    unregister_scene_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
