import bpy

# Import all operator and UI classes to register
from ..ui.panel_main import ARTISTANT_PT_panel
from ..ops.modeling.smart_group import ARTISTANT_OT_smart_group_operator
from ..ops.modeling.floor_pivot import ARTISTANT_OT_floor_pivot
from ..ops.modeling.floor_object import ARTISTANT_OT_floor_object
from ..ops.modeling.generate_collider import ARTISTANT_OT_generate_collider
from ..ops.export.unity_fbx import ARTISTANT_OT_export_unity_fbx
from ..ops.util.reload_images import ARTISTANT_OT_reload_images
from ..ops.visualization.visualize_normals import ARTISTANT_OT_visualize_normals
from ..ops.selection.select_by_name import ARTISTANT_OT_select_by_name
from ..ops.selection.select_orphans import ARTISTANT_OT_select_orphans
from .properties import register_scene_properties, unregister_scene_properties


# Central registry of all classes to be registered with Blender
classes = (
    ARTISTANT_PT_panel,
    ARTISTANT_OT_smart_group_operator,
    ARTISTANT_OT_floor_pivot,
    ARTISTANT_OT_floor_object,
    ARTISTANT_OT_generate_collider,
    ARTISTANT_OT_export_unity_fbx,
    ARTISTANT_OT_reload_images,
    ARTISTANT_OT_visualize_normals,
    ARTISTANT_OT_select_by_name,
    ARTISTANT_OT_select_orphans,
)


def register():
    """Register all operator, panel, and scene property classes with Blender."""
    # Register operator and panel classes with Blender's registration system
    for cls in classes:
        bpy.utils.register_class(cls)
    # Register custom scene properties (export folder, export mode, etc.)
    register_scene_properties()


def unregister():
    """Unregister all scene properties and operator/panel classes from Blender."""
    # Unregister in reverse order: properties first, then classes
    unregister_scene_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
