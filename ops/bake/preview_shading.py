import bpy
from bpy.types import Operator

from ..common.image_nodes import iter_object_image_texture_nodes
from .texture_list import get_selected_texture_name


class ARTISTANT_OT_preview_bake(Operator):
    """Show the selected texture on the active object via Solid / Texture / Flat viewport shading"""
    bl_idname = "artistant.preview_bake"
    bl_label = "Preview"
    bl_description = "Show the selected texture on the active object using Solid shading, Texture color, and Flat lighting"
    bl_options = {'REGISTER'}

    def _activate_selected_texture(self, context):
        """Make the chosen texture's node the active/selected one on each material
        that contains it, so Solid/Texture shading displays it.
        """
        texture_name = get_selected_texture_name(context)
        if not texture_name:
            return

        for mat, node in iter_object_image_texture_nodes(context.active_object):
            if node.image.name != texture_name:
                continue
            # Compare by name, not identity: bpy_struct wrappers returned while
            # iterating nodes aren't guaranteed to be the same Python object.
            for n in mat.node_tree.nodes:
                n.select = (n.name == node.name)
            mat.node_tree.nodes.active = node
            node.select = True

    def execute(self, context):
        self._activate_selected_texture(context)

        changed = 0
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                space = area.spaces.active
                if space is None or space.type != 'VIEW_3D':
                    continue
                space.shading.type = 'SOLID'
                space.shading.color_type = 'TEXTURE'
                space.shading.light = 'FLAT'
                changed += 1

        if changed == 0:
            self.report({'WARNING'}, "No 3D Viewport found")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Preview shading applied to {changed} viewport(s)")
        return {'FINISHED'}
