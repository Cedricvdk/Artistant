import colorsys
import random

import bpy
from bpy.types import Operator

from ..common.context_guard import preserve_selection_and_active


# Maps our own map-type identifiers to the Cycles bake pass type they use.
CYCLES_BAKE_TYPE = {
    'AO': 'AO',
    'MESH_ID': 'EMIT',
}

# Suffix used for each map type's generated image name.
IMAGE_SUFFIX = {
    'AO': 'AO',
    'MESH_ID': 'MeshID',
}

# Name of the temporary vertex color attribute used to carry per-loose-part
# Mesh ID colors into the bake.
MESH_ID_COLOR_ATTR_NAME = "Artistant_Bake_ID_Color"


def _bake_node_name(map_type):
    """Stable, per-map-type node name so re-running a bake reuses the same
    node/image instead of accumulating duplicates, while different map types
    (baked on the same object) each keep their own node and stay selectable.
    """
    return f"Artistant_Bake_{map_type}"


def _compute_loose_parts(mesh):
    """Group a mesh's vertices into "loose parts" (Blender's own term for
    connected components: pieces that share no edge/vertex with each other,
    even within the same mesh datablock) via union-find over its edges.

    Returns (vertex_index -> part_id list, part_count).
    """
    n = len(mesh.vertices)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for edge in mesh.edges:
        a, b = edge.vertices[0], edge.vertices[1]
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    roots = {}
    vertex_part = [0] * n
    for i in range(n):
        root = find(i)
        part_id = roots.setdefault(root, len(roots))
        vertex_part[i] = part_id

    return vertex_part, len(roots)


def _mesh_id_part_color(obj, part_index):
    """Deterministic, visually distinct color for one loose part of obj, so the
    same object/part combination gets the same color across re-bakes.
    """
    rng = random.Random(f"{obj.name}::{part_index}")
    hue = rng.random()
    return colorsys.hsv_to_rgb(hue, 0.65, 0.95)


class ARTISTANT_OT_bake(Operator):
    """Bake the selected map (see the Map dropdown) for each selected mesh object"""
    bl_idname = "artistant.bake"
    bl_label = "Bake"
    bl_description = "Bake the selected map for each selected mesh object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(o.type == 'MESH' for o in context.selected_objects)

    @staticmethod
    def _mode_for_mode_set(context_mode: str) -> str:
        """Map context.mode values to bpy.ops.object.mode_set(mode=...) values."""
        if context_mode.startswith('EDIT_'):
            return 'EDIT'
        return context_mode

    def _ensure_object_materials(self, obj):
        """Return the object's materials, creating a default one if it has none."""
        materials = [m for m in obj.data.materials if m is not None]
        if materials:
            return materials

        mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
        mat.use_nodes = True
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        return [mat]

    def _create_bake_image(self, obj, size, map_type):
        """Create a fresh image for obj/map_type, replacing any previous bake of the same name."""
        image_name = f"{obj.name}_{IMAGE_SUFFIX[map_type]}"
        existing = bpy.data.images.get(image_name)
        if existing is not None:
            bpy.data.images.remove(existing)

        image = bpy.data.images.new(name=image_name, width=size, height=size, alpha=False)
        # These are data passes, not color-managed footage.
        image.colorspace_settings.name = 'Non-Color'
        return image

    def _get_or_create_bake_node(self, mat, map_type):
        """Return the material's dedicated bake image node for this map type, creating it if needed."""
        nt = mat.node_tree
        node_name = _bake_node_name(map_type)
        node = nt.nodes.get(node_name)
        if node is None or node.type != 'TEX_IMAGE':
            node = nt.nodes.new('ShaderNodeTexImage')
            node.name = node_name
            node.label = node_name
            node.location = (-400, 300)
        return node

    def _activate_bake_target(self, mat, image, map_type):
        """Assign the fresh image to the bake node and make it the active/selected node.

        Left unconnected: the image is created purely as a bake target for
        export, not wired into the shader.
        """
        node = self._get_or_create_bake_node(mat, map_type)
        node.image = image
        # Compare by name, not identity: bpy_struct wrappers returned while
        # iterating nodes aren't guaranteed to be the same Python object as
        # `node`, so `n is node` can miss the very node we just created.
        for n in mat.node_tree.nodes:
            n.select = (n.name == node.name)
        mat.node_tree.nodes.active = node
        node.select = True

    def _prepare_mesh_id_colors(self, obj):
        """Compute the object's loose parts and write a distinct color per part
        into a temporary vertex color attribute.

        Returns a teardown callable that removes the temporary attribute.
        """
        mesh = obj.data
        vertex_part, part_count = _compute_loose_parts(mesh)
        colors = [_mesh_id_part_color(obj, i) for i in range(part_count)]

        existing = mesh.color_attributes.get(MESH_ID_COLOR_ATTR_NAME)
        if existing is not None:
            mesh.color_attributes.remove(existing)
        color_attr = mesh.color_attributes.new(
            name=MESH_ID_COLOR_ATTR_NAME, type='BYTE_COLOR', domain='POINT'
        )
        for v in mesh.vertices:
            r, g, b = colors[vertex_part[v.index]]
            color_attr.data[v.index].color = (r, g, b, 1.0)

        def teardown():
            attr = mesh.color_attributes.get(MESH_ID_COLOR_ATTR_NAME)
            if attr is not None:
                mesh.color_attributes.remove(attr)

        return teardown

    def _prepare_mesh_id_material(self, mat):
        """Temporarily route the ID color attribute into the material's surface
        output as flat emission, so the EMIT bake pass captures per-part colors
        instead of whatever the material actually looks like.

        Returns a teardown callable that restores the material exactly as it was.
        """
        nt = mat.node_tree
        output = next(
            (n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output),
            None,
        )
        if output is None:
            output = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if output is None:
            output = nt.nodes.new('ShaderNodeOutputMaterial')

        surface_input = output.inputs['Surface']
        original_from_socket = surface_input.links[0].from_socket if surface_input.is_linked else None

        attribute = nt.nodes.new('ShaderNodeAttribute')
        attribute.name = "Artistant_Bake_ID_Attribute"
        attribute.label = attribute.name
        attribute.attribute_name = MESH_ID_COLOR_ATTR_NAME
        attribute.location = (output.location.x - 400, output.location.y - 200)

        emission = nt.nodes.new('ShaderNodeEmission')
        emission.name = "Artistant_Bake_ID_Emission"
        emission.label = emission.name
        emission.location = (output.location.x - 200, output.location.y - 200)

        nt.links.new(attribute.outputs['Color'], emission.inputs['Color'])
        nt.links.new(emission.outputs['Emission'], surface_input)

        def teardown():
            for link in list(surface_input.links):
                nt.links.remove(link)
            if original_from_socket is not None:
                nt.links.new(original_from_socket, surface_input)
            nt.nodes.remove(emission)
            nt.nodes.remove(attribute)

        return teardown

    def _bake_object(self, context, obj, size, map_type):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        materials = self._ensure_object_materials(obj)
        image = self._create_bake_image(obj, size, map_type)

        teardowns = []
        try:
            for mat in materials:
                if not mat.use_nodes:
                    mat.use_nodes = True
                self._activate_bake_target(mat, image, map_type)

            if map_type == 'MESH_ID':
                teardowns.append(self._prepare_mesh_id_colors(obj))
                for mat in materials:
                    teardowns.append(self._prepare_mesh_id_material(mat))

            result = bpy.ops.object.bake(type=CYCLES_BAKE_TYPE[map_type])
            if 'FINISHED' not in result:
                raise RuntimeError("bake operator did not finish (see console for details)")
        finally:
            # Reverse order: undo material rewiring before removing the mesh
            # color attribute it (by name) referenced.
            for teardown in reversed(teardowns):
                teardown()

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        missing_uv = [o.name for o in mesh_objects if not o.data.uv_layers]
        objects_to_bake = [o for o in mesh_objects if o.data.uv_layers]
        if not objects_to_bake:
            self.report({'ERROR'}, "Selected mesh object(s) have no UV map")
            return {'CANCELLED'}

        map_type = context.scene.bake_map_type
        size = int(context.scene.bake_size)
        samples = context.scene.bake_samples
        margin = context.scene.bake_margin

        starting_mode = context.mode
        switched_to_object = False
        if starting_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            switched_to_object = True

        original_engine = context.scene.render.engine
        original_samples = context.scene.cycles.samples
        original_margin = context.scene.render.bake.margin

        baked = []
        failed = []

        try:
            context.scene.render.engine = 'CYCLES'
            context.scene.cycles.samples = samples
            context.scene.render.bake.margin = margin

            with preserve_selection_and_active(context):
                for obj in objects_to_bake:
                    try:
                        self._bake_object(context, obj, size, map_type)
                        baked.append(obj.name)
                    except Exception as e:
                        failed.append(f"{obj.name} ({e})")
        finally:
            context.scene.render.engine = original_engine
            context.scene.cycles.samples = original_samples
            context.scene.render.bake.margin = original_margin
            if switched_to_object:
                bpy.ops.object.mode_set(mode=self._mode_for_mode_set(starting_mode))

        if missing_uv:
            self.report({'WARNING'}, f"Skipped (no UV map): {', '.join(missing_uv)}")

        if baked and not failed:
            self.report({'INFO'}, f"Baked {len(baked)} object(s)")
            return {'FINISHED'}
        elif baked and failed:
            self.report({'WARNING'}, f"Baked {len(baked)} object(s); failed: {', '.join(failed)}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Bake failed: {', '.join(failed)}")
            return {'CANCELLED'}
