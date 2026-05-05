import re

import bpy
from mathutils import Vector
from bpy.types import Operator


def _next_collider_name(source_name: str):
    """Return the next deterministic collider name for a source object.

    Naming policy:
    - Legacy unsuffixed name (<source>_collider) is normalized to a suffixed name.
    - New colliders always get numeric suffixes: 01, 02, 03, ...
    """
    stem = f"{source_name}_collider"

    # Normalize legacy unsuffixed collider names before allocating a new index.
    legacy_obj = bpy.data.objects.get(stem)
    if legacy_obj:
        legacy_target = f"{stem}01"
        if bpy.data.objects.get(legacy_target):
            i = 2
            while bpy.data.objects.get(f"{stem}{i:02d}"):
                i += 1
            legacy_target = f"{stem}{i:02d}"
        legacy_obj.name = legacy_target

    pattern = re.compile(rf"^{re.escape(stem)}(\d+)$")
    max_index = 0
    for obj in bpy.data.objects:
        match = pattern.match(obj.name)
        if match:
            max_index = max(max_index, int(match.group(1)))

    return f"{stem}{max_index + 1:02d}"


def _box_mesh_from_world_bounds(min_corner, max_corner):
    """Build a mesh datablock for an axis-aligned world-space bounds box."""
    min_x, min_y, min_z = min_corner
    max_x, max_y, max_z = max_corner

    vertices = [
        (min_x, min_y, min_z),
        (max_x, min_y, min_z),
        (max_x, max_y, min_z),
        (min_x, max_y, min_z),
        (min_x, min_y, max_z),
        (max_x, min_y, max_z),
        (max_x, max_y, max_z),
        (min_x, max_y, max_z),
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]

    mesh = bpy.data.meshes.new("ColliderMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


class ARTISTANT_OT_generate_collider(Operator):
    """Create a collider mesh for the active mesh object based on collider type"""
    bl_idname = "artistant.generate_collider"
    bl_label = "Add Collider"
    bl_description = "Create a collider object for the active mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def _ensure_active_viewport_wire_object_mode(self, context):
        """Ensure active 3D viewport uses Object wireframe color mode."""
        area = context.area
        if not area or area.type != 'VIEW_3D':
            return
        space = area.spaces.active
        if not space or space.type != 'VIEW_3D':
            return
        if space.shading.wireframe_color_type != 'OBJECT':
            space.shading.wireframe_color_type = 'OBJECT'

    def _create_box_collider(self, context, source_obj):
        """Create a world-space axis-aligned box collider for source_obj."""
        world_corners = [source_obj.matrix_world @ Vector(corner) for corner in source_obj.bound_box]

        xs = [c.x for c in world_corners]
        ys = [c.y for c in world_corners]
        zs = [c.z for c in world_corners]
        min_corner = (min(xs), min(ys), min(zs))
        max_corner = (max(xs), max(ys), max(zs))

        collider_name = _next_collider_name(source_obj.name)
        mesh = _box_mesh_from_world_bounds(min_corner, max_corner)
        mesh.name = f"{collider_name}_mesh"

        collider_obj = bpy.data.objects.new(collider_name, mesh)
        context.collection.objects.link(collider_obj)

        # Visual collider styling in viewport.
        collider_obj.display_type = 'WIRE'
        collider_obj.color = (0.0, 1.0, 0.0, 1.0)

        # Parent while preserving the collider's world transform.
        world_matrix = collider_obj.matrix_world.copy()
        collider_obj.parent = source_obj
        collider_obj.matrix_parent_inverse = source_obj.matrix_world.inverted()
        collider_obj.matrix_world = world_matrix

        return collider_obj

    def execute(self, context):
        source_obj = context.view_layer.objects.active
        if source_obj is None:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        if source_obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}

        collider_type = getattr(context.scene, "collider_type", "BOX")

        try:
            self._ensure_active_viewport_wire_object_mode(context)

            if collider_type == 'BOX':
                collider_obj = self._create_box_collider(context, source_obj)
            else:
                self.report({'ERROR'}, f"Unsupported collider type: {collider_type}")
                return {'CANCELLED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Failed to create collider: {exc}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Created collider: {collider_obj.name}")
        return {'FINISHED'}
