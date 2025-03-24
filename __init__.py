bl_info = {
    "name": "IGP Artistant",
    "blender": (4, 3, 0),
    "category": "3D View",
    "author": "Cedric Van der Kelen",
    "description": "IGP Artistant: Adds functionalities like Auto-Lattice and Smart Group to create game art in Blender.",
}

import bpy
from .panel import ARTISTANT_PT_panel
from .operators import ARTISTANT_OT_auto_lattice_operator, ARTISTANT_OT_smart_group_operator

def register():
    bpy.utils.register_class(ARTISTANT_PT_panel)
    bpy.utils.register_class(ARTISTANT_OT_auto_lattice_operator)
    bpy.utils.register_class(ARTISTANT_OT_smart_group_operator)

def unregister():
    bpy.utils.unregister_class(ARTISTANT_PT_panel)
    bpy.utils.unregister_class(ARTISTANT_OT_auto_lattice_operator)
    bpy.utils.unregister_class(ARTISTANT_OT_smart_group_operator)

if __name__ == "__main__":
    register()