bl_info = {
    "name": "IGP Artistant",
    "blender": (4, 3, 0),
    "category": "3D View",
    "author": "Cedric Van der Kelen",
    "description": "IGP Artistant: Adds functionalities like Auto-Lattice and Smart Group to create game art in Blender.",
}

from ast import BoolOp
import bpy
from .panel import ARTISTANT_PT_panel
from .operators import ARTISTANT_OT_auto_lattice_operator, ARTISTANT_OT_smart_group_operator
from .export_operator import ARTISTANT_OT_export_unity_fbx

def register():
    bpy.utils.register_class(ARTISTANT_PT_panel)
    bpy.utils.register_class(ARTISTANT_OT_auto_lattice_operator)
    bpy.utils.register_class(ARTISTANT_OT_smart_group_operator)
    bpy.utils.register_class(ARTISTANT_OT_export_unity_fbx)
    bpy.types.Scene.export_folder = bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH',
        default=""
    )
    bpy.types.Scene.export_individual = bpy.props.BoolProperty(
        name="Individual",
        default=False
    )

def unregister():
    del bpy.types.Scene.export_folder
    del bpy.types.Scene.export_individual
    bpy.utils.unregister_class(ARTISTANT_PT_panel)
    bpy.utils.unregister_class(ARTISTANT_OT_auto_lattice_operator)
    bpy.utils.unregister_class(ARTISTANT_OT_smart_group_operator)
    bpy.utils.unregister_class(ARTISTANT_OT_export_unity_fbx)

if __name__ == "__main__":
    register()
