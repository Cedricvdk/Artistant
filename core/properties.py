import bpy

# Import property name constants to ensure consistency across modules
from .constants import (
    EXPORT_FOLDER_PROP,
    EXPORT_INDIVIDUAL_PROP,
    EXPORT_ONLY_ORPHANS_PROP,
    SELECT_BY_NAME_QUERY_PROP,
    SELECT_BY_NAME_EXACT_PROP,
)


def register_scene_properties():
    """Attach custom properties to bpy.types.Scene for user-facing add-on settings."""
    # Export settings: folder path for FBX output
    setattr(
        bpy.types.Scene,
        EXPORT_FOLDER_PROP,
        bpy.props.StringProperty(
            name="Export Folder",
            subtype='DIR_PATH',
            default=""
        ),
    )
    # Export settings: export individual objects as separate FBX files
    setattr(
        bpy.types.Scene,
        EXPORT_INDIVIDUAL_PROP,
        bpy.props.BoolProperty(
            name="Individual",
            default=False
        ),
    )
    # Export settings: when individual export is enabled, export only orphan roots with full hierarchy
    setattr(
        bpy.types.Scene,
        EXPORT_ONLY_ORPHANS_PROP,
        bpy.props.BoolProperty(
            name="Only Orphans",
            description="When enabled, only objects without parents are exported, each with their full hierarchy.",
            default=False
        ),
    )
    # Selection settings: query string for "Select by Name" operator
    setattr(
        bpy.types.Scene,
        SELECT_BY_NAME_QUERY_PROP,
        bpy.props.StringProperty(
            name="Name",
            description="Select objects whose name matches or contains this text",
            default=""
        ),
    )
    # Selection settings: use exact name match vs contains match
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
    """Remove custom properties from bpy.types.Scene during add-on unregistration."""
    # Remove all registered properties in order
    for prop_name in (
        EXPORT_FOLDER_PROP,
        EXPORT_INDIVIDUAL_PROP,
        EXPORT_ONLY_ORPHANS_PROP,
        SELECT_BY_NAME_QUERY_PROP,
        SELECT_BY_NAME_EXACT_PROP,
    ):
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
