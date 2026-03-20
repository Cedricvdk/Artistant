import bpy

from .constants import (
    EXPORT_FOLDER_PROP,
    EXPORT_INDIVIDUAL_PROP,
    EXPORT_FBX_MODE_PROP,
    EXPORT_RESET_LOCATION_PROP,
    SELECT_BY_NAME_QUERY_PROP,
    SELECT_BY_NAME_EXACT_PROP,
)


def register_scene_properties():
    setattr(
        bpy.types.Scene,
        EXPORT_FOLDER_PROP,
        bpy.props.StringProperty(
            name="Export Folder",
            subtype='DIR_PATH',
            default=""
        ),
    )
    setattr(
        bpy.types.Scene,
        EXPORT_INDIVIDUAL_PROP,
        bpy.props.BoolProperty(
            name="Individual",
            default=False
        ),
    )
    setattr(
        bpy.types.Scene,
        EXPORT_FBX_MODE_PROP,
        bpy.props.EnumProperty(
            name="Unity Export Mode",
            items=[
                ('AUTO', "Auto", "Detect rigs/hierarchies and choose best mode"),
                ('SIMPLE', "Simple (fast)", "Use Apply Transform on export"),
                ('HSAFE', "Hierarchy-safe (slow)", "Duplicate + counter-rotate + export"),
            ],
            default='AUTO'
        ),
    )
    setattr(
        bpy.types.Scene,
        EXPORT_RESET_LOCATION_PROP,
        bpy.props.BoolProperty(
            name="Reset Root Location",
            description="Force exported root(s) to have Location (0,0,0)",
            default=False
        ),
    )
    setattr(
        bpy.types.Scene,
        SELECT_BY_NAME_QUERY_PROP,
        bpy.props.StringProperty(
            name="Name",
            description="Select objects whose name matches or contains this text",
            default=""
        ),
    )
    setattr(
        bpy.types.Scene,
        SELECT_BY_NAME_EXACT_PROP,
        bpy.props.BoolProperty(
            name="Exact",
            description="Use exact name match instead of contains",
            default=False
        ),
    )


def unregister_scene_properties():
    for prop_name in (
        EXPORT_FOLDER_PROP,
        EXPORT_INDIVIDUAL_PROP,
        EXPORT_FBX_MODE_PROP,
        EXPORT_RESET_LOCATION_PROP,
        SELECT_BY_NAME_QUERY_PROP,
        SELECT_BY_NAME_EXACT_PROP,
    ):
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
