# __init__.py
bl_info = {
    "name": "IGP Artistant",
    "blender": (4, 3, 0),
    "category": "3D View",
    "author": "Cedric Van der Kelen",
    "description": "IGP Artistant: Adds functionalities like Auto-Lattice and Smart Group to create game art in Blender.",
}

import bpy

from .panel import ARTISTANT_PT_panel
from .operators import (
    ARTISTANT_OT_auto_lattice_operator,
    ARTISTANT_OT_smart_group_operator,
)
from .export_operator import ARTISTANT_OT_export_unity_fbx
from .reload_images_operator import ARTISTANT_OT_reload_images
from .visualize_normals_operator import ARTISTANT_OT_visualize_normals

# List all classes here to keep register()/unregister() tidy
classes = (
    ARTISTANT_PT_panel,
    ARTISTANT_OT_auto_lattice_operator,
    ARTISTANT_OT_smart_group_operator,
    ARTISTANT_OT_export_unity_fbx,
    ARTISTANT_OT_reload_images,
    ARTISTANT_OT_visualize_normals,
)

def register():
    # Register UI + operators
    for cls in classes:
        bpy.utils.register_class(cls)

    # Define Scene properties (do this once; keep it out of panel.py)
    bpy.types.Scene.export_folder = bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH',
        default=""
    )
    bpy.types.Scene.export_individual = bpy.props.BoolProperty(
        name="Individual",
        default=False
    )

    # NEW: Export FBX Mode dropdown
    bpy.types.Scene.export_fbx_mode = bpy.props.EnumProperty(
        name="Unity Export Mode",
        items=[
            ('AUTO', "Auto", "Detect rigs/hierarchies and choose best mode"),
            ('SIMPLE', "Simple (fast)", "Use Apply Transform on export"),
            ('HSAFE', "Hierarchy-safe (slow)", "Duplicate + counter-rotate + export"),
        ],
        default='AUTO'
    )
        
    bpy.types.Scene.export_reset_location = bpy.props.BoolProperty(
        name="Reset Root Location",
        description="Force exported root(s) to have Location (0,0,0)",
        default=False
    )


def unregister():
    # Remove Scene properties if they exist
    if hasattr(bpy.types.Scene, "export_folder"):
        del bpy.types.Scene.export_folder
    if hasattr(bpy.types.Scene, "export_individual"):
        del bpy.types.Scene.export_individual
    if hasattr(bpy.types.Scene, "export_fbx_mode"):
        del bpy.types.Scene.export_fbx_mode
    if hasattr(bpy.types.Scene, "export_reset_location"):
        del bpy.types.Scene.export_reset_location


    # Unregister in reverse order
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()