import bpy


class ARTISTANT_PT_uv_panel(bpy.types.Panel):
    """Artistant sidebar panel in the UV/Image Editor, for texture baking."""
    bl_label = "Artistant"
    bl_idname = "ARTISTANT_PT_uv_panel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Artistant'

    def draw(self, context):
        layout = self.layout

        bake_box = layout.box()
        bake_box.label(text="Bake", icon='RENDER_STILL')
        col = bake_box.column(align=True)
        col.prop(context.scene, "bake_ao_size", text="Size")
        col.prop(context.scene, "bake_ao_samples", text="Samples")
        col.prop(context.scene, "bake_ao_margin", text="Margin")
        col.operator("artistant.bake_ao", text="Bake AO", icon='SHADING_RENDERED')
        col.operator("artistant.preview_bake", text="Preview", icon='SHADING_TEXTURE')
