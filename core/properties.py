import bpy

# Import property name constants to ensure consistency across modules
from .constants import (
    EXPORT_FOLDER_PROP,
    EXPORT_INDIVIDUAL_PROP,
    EXPORT_ONLY_ORPHANS_PROP,
    SELECT_BY_NAME_QUERY_PROP,
    SELECT_BY_NAME_EXACT_PROP,
    BAKE_AO_SIZE_PROP,
    BAKE_AO_SAMPLES_PROP,
    BAKE_AO_MARGIN_PROP,
)

# Texture sizes offered for AO baking, from 128px up to 4096px
_BAKE_SIZE_ITEMS = tuple(
    (str(size), f"{size} x {size}", f"Bake at {size} x {size} px")
    for size in (128, 256, 512, 1024, 2048, 4096)
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
            description="Individual mode only: export only parentless roots with full hierarchies and place each exported root at (0,0,0). When disabled, each selected object exports separately at (0,0,0).",
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
    # Bake settings: output texture size for AO bakes
    setattr(
        bpy.types.Scene,
        BAKE_AO_SIZE_PROP,
        bpy.props.EnumProperty(
            name="Size",
            description="Resolution of the baked AO texture",
            items=_BAKE_SIZE_ITEMS,
            default="1024",
        ),
    )
    # Bake settings: render samples used for the AO bake
    setattr(
        bpy.types.Scene,
        BAKE_AO_SAMPLES_PROP,
        bpy.props.IntProperty(
            name="Samples",
            description="Number of render samples used for the AO bake",
            default=32,
            min=1,
            soft_max=512,
        ),
    )
    # Bake settings: padding (in pixels) around baked UV islands
    setattr(
        bpy.types.Scene,
        BAKE_AO_MARGIN_PROP,
        bpy.props.IntProperty(
            name="Margin",
            description="Padding, in pixels, added around each UV island to avoid seams/bleeding",
            default=16,
            min=0,
            soft_max=64,
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
        BAKE_AO_SIZE_PROP,
        BAKE_AO_SAMPLES_PROP,
        BAKE_AO_MARGIN_PROP,
    ):
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
