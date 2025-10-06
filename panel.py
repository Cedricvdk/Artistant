# panel.py
import bpy

class ARTISTANT_PT_panel(bpy.types.Panel):
    bl_label = "Artistant"
    bl_idname = "ARTISTANT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Artistant'

    def draw(self, context):
        layout = self.layout

        # --- Tools ---
        tools_box = layout.box()
        tools_box.label(text="Tools", icon='TOOL_SETTINGS')
        col = tools_box.column(align=True)
        col.operator("artistant.auto_lattice_operator", text="Auto Lattice", icon='MOD_LATTICE')
        col.operator("artistant.smart_group_operator", text="Smart Group", icon='GROUP')

        col.separator()
        row = col.row(align=True)
        row.enabled = bool(getattr(context, "selected_editable_objects", []))
        row.operator("artistant.visualize_normals", text="Visualize Normals", icon='MOD_NORMALEDIT')

        # --- Export section ---
        export_box = layout.box()
        export_box.label(text="Export Unity Asset", icon='EXPORT')
        col = export_box.column(align=True)
        col.prop(context.scene, "export_folder")
        col.prop(context.scene, "export_individual")

        # New: Mode dropdown
        col.prop(context.scene, "export_fbx_mode", text="Mode")
        col.prop(context.scene, "export_reset_location", text="Reset Root Location (0,0,0)")
        # Pass the chosen mode to the operator
        op = col.operator("artistant.export_unity_fbx", text="Export to FBX", icon='FILE_FOLDER')
        op.mode = context.scene.export_fbx_mode  # hand the selection to operator
        op.reset_location = context.scene.export_reset_location

        # --- Selection (NEW) ---
        select_box = layout.box()
        select_box.label(text="Select By Name", icon='FILTER')
        col = select_box.column(align=True)
        col.prop(context.scene, "select_by_name_query", text="Name")
        col.prop(context.scene, "select_by_name_exact", text="Exact")

        op = col.operator("artistant.select_by_name", text="Select", icon='RESTRICT_SELECT_OFF')
        op.query = context.scene.select_by_name_query
        op.exact = context.scene.select_by_name_exact

        # --- Utilities ---
        util_box = layout.box()
        util_box.label(text="Utilities", icon='FILE_REFRESH')
        util_box.operator("artistant.reload_images", text="Reload Images", icon='IMAGE')