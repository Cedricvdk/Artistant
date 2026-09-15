import bpy
from bpy.types import Operator

from ..common.context_guard import preserve_selection_and_active


# Stable name so re-running the bake reuses the same node/image instead of
# accumulating duplicates in the material.
BAKE_NODE_NAME = "Artistant_Bake_AO"


class ARTISTANT_OT_bake_ao(Operator):
    """Bake an Ambient Occlusion texture for each selected mesh object"""
    bl_idname = "artistant.bake_ao"
    bl_label = "Bake AO"
    bl_description = "Bake an Ambient Occlusion texture for each selected mesh object"
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

    def _create_bake_image(self, obj, size):
        """Create a fresh AO image for obj, replacing any previous bake of the same name."""
        image_name = f"{obj.name}_AO"
        existing = bpy.data.images.get(image_name)
        if existing is not None:
            bpy.data.images.remove(existing)

        image = bpy.data.images.new(name=image_name, width=size, height=size, alpha=False)
        # AO is grayscale data, not color-managed footage.
        image.colorspace_settings.name = 'Non-Color'
        return image

    def _get_or_create_bake_node(self, mat):
        """Return the material's dedicated bake image node, creating it if needed."""
        nt = mat.node_tree
        node = nt.nodes.get(BAKE_NODE_NAME)
        if node is None or node.type != 'TEX_IMAGE':
            node = nt.nodes.new('ShaderNodeTexImage')
            node.name = BAKE_NODE_NAME
            node.label = BAKE_NODE_NAME
            node.location = (-400, 300)
        return node

    def _bake_object_ao(self, context, obj, size):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        materials = self._ensure_object_materials(obj)
        image = self._create_bake_image(obj, size)

        # Left unconnected: the image is created purely as a bake target for
        # export, not wired into the shader.
        for mat in materials:
            if not mat.use_nodes:
                mat.use_nodes = True
            node = self._get_or_create_bake_node(mat)
            node.image = image
            # Compare by name, not identity: bpy_struct wrappers returned while
            # iterating nodes aren't guaranteed to be the same Python object as
            # `node`, so `n is node` can miss the very node we just created.
            for n in mat.node_tree.nodes:
                n.select = (n.name == node.name)
            mat.node_tree.nodes.active = node
            node.select = True

        result = bpy.ops.object.bake(type='AO')
        if 'FINISHED' not in result:
            raise RuntimeError("bake operator did not finish (see console for details)")

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

        size = int(context.scene.bake_ao_size)
        samples = context.scene.bake_ao_samples
        margin = context.scene.bake_ao_margin

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

        # Per-bake sample progress is already shown natively by Blender's own
        # job status bar. This just adds an across-objects progress indicator
        # for multi-object batches (wm.progress_* is a thin, built-in API).
        wm = context.window_manager
        wm.progress_begin(0, len(objects_to_bake))

        try:
            context.scene.render.engine = 'CYCLES'
            context.scene.cycles.samples = samples
            context.scene.render.bake.margin = margin

            with preserve_selection_and_active(context):
                for index, obj in enumerate(objects_to_bake):
                    try:
                        self._bake_object_ao(context, obj, size)
                        baked.append(obj.name)
                    except Exception as e:
                        failed.append(f"{obj.name} ({e})")
                    wm.progress_update(index + 1)
        finally:
            wm.progress_end()
            context.scene.render.engine = original_engine
            context.scene.cycles.samples = original_samples
            context.scene.render.bake.margin = original_margin
            if switched_to_object:
                bpy.ops.object.mode_set(mode=self._mode_for_mode_set(starting_mode))

        if missing_uv:
            self.report({'WARNING'}, f"Skipped (no UV map): {', '.join(missing_uv)}")

        if baked and not failed:
            self.report({'INFO'}, f"Baked AO for {len(baked)} object(s)")
            return {'FINISHED'}
        elif baked and failed:
            self.report({'WARNING'}, f"Baked {len(baked)} object(s); failed: {', '.join(failed)}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Bake failed: {', '.join(failed)}")
            return {'CANCELLED'}
