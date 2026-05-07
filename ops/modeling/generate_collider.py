import re
import math

import bpy
import bmesh
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


def _world_bounds_of_object(source_obj):
    """Compute world-space axis-aligned bounding box of an object.
    
    Returns:
        Tuple of (min_corner, max_corner, center) as 3-tuples of floats.
    """
    world_corners = [source_obj.matrix_world @ Vector(corner) for corner in source_obj.bound_box]
    
    xs = [c.x for c in world_corners]
    ys = [c.y for c in world_corners]
    zs = [c.z for c in world_corners]
    
    min_corner = (min(xs), min(ys), min(zs))
    max_corner = (max(xs), max(ys), max(zs))
    center = (
        (min_corner[0] + max_corner[0]) / 2,
        (min_corner[1] + max_corner[1]) / 2,
        (min_corner[2] + max_corner[2]) / 2,
    )
    
    return min_corner, max_corner, center


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

    def _finalize_collider_object(self, context, source_obj, collider_obj, mesh, collider_name):
        """Apply common collider styling and parenting to a newly-created collider object.
        
        Handles: mesh naming, object naming, collection linking, wireframe display,
        green color, and parenting while preserving world transform.
        """
        # Name the mesh datablock
        mesh.name = f"{collider_name}_mesh"
        
        # Name the object
        collider_obj.name = collider_name
        
        # Unlink from any existing collections (operators like primitive_uv_sphere_add auto-link)
        # then link to the target collection
        for coll in list(collider_obj.users_collection):
            coll.objects.unlink(collider_obj)
        context.collection.objects.link(collider_obj)
        
        # Visual collider styling
        collider_obj.display_type = 'WIRE'
        collider_obj.color = (0.0, 1.0, 0.0, 1.0)
        
        # Parent while preserving world transform
        world_matrix = collider_obj.matrix_world.copy()
        collider_obj.parent = source_obj
        collider_obj.matrix_parent_inverse = source_obj.matrix_world.inverted()
        collider_obj.matrix_world = world_matrix
        
        return collider_obj

    def _create_box_collider(self, context, source_obj):
        """Create a world-space axis-aligned box collider for source_obj."""
        min_corner, max_corner, _ = _world_bounds_of_object(source_obj)

        collider_name = _next_collider_name(source_obj.name)
        mesh = _box_mesh_from_world_bounds(min_corner, max_corner)

        collider_obj = bpy.data.objects.new(collider_name, mesh)
        return self._finalize_collider_object(context, source_obj, collider_obj, mesh, collider_name)

    def _create_sphere_collider(self, context, source_obj):
        """Create a sphere collider that encloses the world-space bounds of source_obj.
        
        Sphere is centered at the bounding box center, with radius = half the diagonal
        of the bounding box, guaranteeing enclosure of all corners.
        """
        min_corner, max_corner, center = _world_bounds_of_object(source_obj)
        
        # Compute box dimensions
        dx = max_corner[0] - min_corner[0]
        dy = max_corner[1] - min_corner[1]
        dz = max_corner[2] - min_corner[2]
        
        # old formula
        # Radius = half the space diagonal of the bounding box (guaranteed enclosure)
        # diagonal = math.sqrt(dx * dx + dy * dy + dz * dz)
        # radius = diagonal / 2.0

        radius = max(dx, dy, dz) / 2.0
        
        # Create ico sphere at the center with the computed radius
        collider_name = _next_collider_name(source_obj.name)
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=2,
            radius=radius,
            location=center,
            enter_editmode=False,
            align='WORLD'
        )
        sphere_obj = context.object
        mesh = sphere_obj.data
        
        return self._finalize_collider_object(context, source_obj, sphere_obj, mesh, collider_name)

    def _create_mesh_collider(self, context, source_obj):
        """Create a collider by duplicating the active object's mesh data and transform."""
        collider_name = _next_collider_name(source_obj.name)
        mesh = source_obj.data.copy()

        collider_obj = bpy.data.objects.new(collider_name, mesh)
        collider_obj.matrix_world = source_obj.matrix_world.copy()
        return self._finalize_collider_object(context, source_obj, collider_obj, mesh, collider_name)

    def _create_convex_hull_collider(self, context, source_obj):
        """Create a collider by duplicating mesh geometry and reducing it to a convex hull."""
        collider_name = _next_collider_name(source_obj.name)
        mesh = source_obj.data.copy()

        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            geom_input = list(bm.verts) + list(bm.edges) + list(bm.faces)
            result = bmesh.ops.convex_hull(bm, input=geom_input)

            # Remove interior/unused geometry returned by convex_hull so only hull remains.
            # In Blender 5.1 these lists can overlap, so delete in one pass after dedupe.
            geom_to_delete = []
            seen_ids = set()
            for elem in result.get("geom_interior", []) + result.get("geom_unused", []):
                if not getattr(elem, "is_valid", False):
                    continue
                elem_id = id(elem)
                if elem_id in seen_ids:
                    continue
                seen_ids.add(elem_id)
                geom_to_delete.append(elem)

            if geom_to_delete:
                bmesh.ops.delete(bm, geom=geom_to_delete, context='VERTS')

            bm.to_mesh(mesh)
            mesh.update()
        finally:
            bm.free()

        collider_obj = bpy.data.objects.new(collider_name, mesh)
        collider_obj.matrix_world = source_obj.matrix_world.copy()
        return self._finalize_collider_object(context, source_obj, collider_obj, mesh, collider_name)

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
            elif collider_type == 'SPHERE':
                collider_obj = self._create_sphere_collider(context, source_obj)
            elif collider_type == 'MESH':
                collider_obj = self._create_mesh_collider(context, source_obj)
            elif collider_type == 'CONVEX_HULL':
                collider_obj = self._create_convex_hull_collider(context, source_obj)
            else:
                self.report({'ERROR'}, f"Unsupported collider type: {collider_type}")
                return {'CANCELLED'}

        except Exception as exc:
            self.report({'ERROR'}, f"Failed to create collider: {exc}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Created collider: {collider_obj.name}")
        return {'FINISHED'}
