import os

import bpy
import bpy.utils.previews

from ...core.paths import asset_path


# Map types the Bake operator supports. Kept short on purpose: each entry
# needs matching setup logic in ops/bake/bake.py. Each entry's thumbnail is
# assets/thumbnails/bake_<id lowercase>.png (e.g. bake_mesh_id.png).
BAKE_MAP_TYPES = (
    ('AO', "Ambient Occlusion", "Bake ambient occlusion shading into a texture"),
    ('MESH_ID', "Mesh ID", "Bake a distinct color per connected mesh part (loose part); useful as an object/part mask"),
    ('WORLD_GRADIENT', "World Gradient", "Bake a black (lowest point) to white (highest point) gradient along world Z, spanning all selected objects"),
    ('OBJECT_GRADIENT', "Object Gradient", "Bake a black (bottom) to white (top) gradient along each object's own local Z axis"),
)

_preview_collection = None


def _thumbnail_path(map_id):
    return asset_path(os.path.join("thumbnails", f"bake_{map_id.lower()}.png"))


def bake_map_type_items(self, context):
    """EnumProperty items callback: map types with their thumbnail as icon.

    A map type whose thumbnail file is missing just shows without an icon.
    """
    items = []
    for index, (map_id, name, description) in enumerate(BAKE_MAP_TYPES):
        preview = _preview_collection.get(map_id) if _preview_collection else None
        items.append((map_id, name, description, preview.icon_id if preview else 0, index))
    return items


def register_thumbnails():
    global _preview_collection
    _preview_collection = bpy.utils.previews.new()
    for map_id, _name, _description in BAKE_MAP_TYPES:
        path = _thumbnail_path(map_id)
        if os.path.isfile(path):
            _preview_collection.load(map_id, path, 'IMAGE')


def unregister_thumbnails():
    global _preview_collection
    if _preview_collection is not None:
        bpy.utils.previews.remove(_preview_collection)
        _preview_collection = None
