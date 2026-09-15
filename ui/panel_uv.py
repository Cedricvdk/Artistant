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
        col.prop(context.scene, "bake_map_type", text="Map")
        col.prop(context.scene, "bake_size", text="Size")
        col.prop(context.scene, "bake_samples", text="Samples")
        col.prop(context.scene, "bake_margin", text="Margin")
        col.operator("artistant.bake", text="Bake", icon='SHADING_RENDERED')

        bake_box.separator()
        list_header = bake_box.row(align=True)
        list_header.label(text="Textures")
        list_header.operator("artistant.refresh_bake_texture_list", text="", icon='FILE_REFRESH')
        bake_box.template_list(
            "ARTISTANT_UL_bake_textures", "",
            context.scene, "bake_texture_list",
            context.scene, "bake_texture_list_index",
            rows=4,
        )
        bake_box.operator("artistant.preview_bake", text="Preview", icon='SHADING_TEXTURE')
