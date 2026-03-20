import bpy

from ..ui.panel_main import ARTISTANT_PT_panel
from ..ops.modeling.auto_lattice import ARTISTANT_OT_auto_lattice_operator
from ..ops.modeling.smart_group import ARTISTANT_OT_smart_group_operator
from ..ops.export.unity_fbx import ARTISTANT_OT_export_unity_fbx
from ..ops.util.reload_images import ARTISTANT_OT_reload_images
from ..ops.visualization.visualize_normals import ARTISTANT_OT_visualize_normals
from ..ops.selection.select_by_name import ARTISTANT_OT_select_by_name
from .properties import register_scene_properties, unregister_scene_properties


classes = (
    ARTISTANT_PT_panel,
    ARTISTANT_OT_auto_lattice_operator,
    ARTISTANT_OT_smart_group_operator,
    ARTISTANT_OT_export_unity_fbx,
    ARTISTANT_OT_reload_images,
    ARTISTANT_OT_visualize_normals,
    ARTISTANT_OT_select_by_name,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_scene_properties()


def unregister():
    unregister_scene_properties()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
