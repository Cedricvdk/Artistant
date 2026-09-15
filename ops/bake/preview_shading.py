import bpy
from bpy.types import Operator


class ARTISTANT_OT_preview_bake(Operator):
    """Switch 3D Viewport shading to Solid / Texture / Flat lighting, to preview a baked texture"""
    bl_idname = "artistant.preview_bake"
    bl_label = "Preview"
    bl_description = "Switch the 3D Viewport to Solid shading, Texture color, and Flat lighting"
    bl_options = {'REGISTER'}

    def execute(self, context):
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
