import bpy


class ARTISTANT_PT_panel(bpy.types.Panel):
    """Main sidebar panel for the Artistant add-on in the 3D View.
    
    Provides quick access to all add-on operators and settings from the sidebar.
    """
    bl_label = "Artistant v2.0"
    bl_idname = "ARTISTANT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Artistant'

    def draw(self, context):
        # Draw the panel UI with four main sections: Tools, Export, Select, Utilities."""
        layout = self.layout

        # --- Tools Section: Modeling and Visualization ---
        tools_box = layout.box()
        tools_box.label(text="Tools", icon='TOOL_SETTINGS')
        col = tools_box.column(align=True)
        in_object_mode = (context.mode == 'OBJECT')

        # Smart Group: Object mode only
        row = col.row(align=True)
        row.enabled = in_object_mode
        row.operator("artistant.smart_group_operator", text="Smart Group", icon='GROUP')

        col.separator()
        # Floor Pivot: works in Object mode and Edit Mesh mode
        row = col.row(align=True)
        row.enabled = context.mode in {'OBJECT', 'EDIT_MESH'}
        row.operator("artistant.floor_pivot", text="Floor Pivot", icon='OBJECT_ORIGIN')
        # Floor Object: Object mode only
        row = col.row(align=True)
        row.enabled = in_object_mode
        row.operator("artistant.floor_object", text="Floor Object", icon='SORT_ASC')

        col.separator()
        # Select Orphans: Object mode only
        row = col.row(align=True)
        row.enabled = in_object_mode
        row.operator("artistant.select_orphans", text="Select Orphans", icon='OUTLINER_OB_EMPTY')

        col.separator()
        # Visualize Normals: Object mode only, and only when objects are selected
        row = col.row(align=True)
        row.enabled = in_object_mode and bool(getattr(context, "selected_editable_objects", []))
        row.operator("artistant.visualize_normals", text="Visualize Normals", icon='MOD_NORMALEDIT')

        # --- Export Section: Unity FBX Export Pipeline ---
        export_box = layout.box()
        export_box.label(text="Export Unity Asset", icon='EXPORT')
        col = export_box.column(align=True)
        col.enabled = (context.mode == 'OBJECT')
        # Export destination folder
        col.prop(context.scene, "export_folder")
        # Export mode: individual files per object or batch export
        col.prop(context.scene, "export_individual")
        # Optional individual mode behavior: export only orphan roots with full hierarchies
        orphan_row = col.row(align=True)
        orphan_row.enabled = context.scene.export_individual
        orphan_row.prop(context.scene, "export_only_orphans")
        # Main export operator
        col.operator("artistant.export_unity_fbx", text="Export to FBX", icon='FILE_FOLDER')

        # --- Selection Section: Find and Select by Name ---
        select_box = layout.box()
        select_box.label(text="Select By Name", icon='FILTER')
        col = select_box.column(align=True)
        col.enabled = (context.mode == 'OBJECT')
        # Name query input field
        col.prop(context.scene, "select_by_name_query", text="Name")
        # Exact match vs contains match toggle
        col.prop(context.scene, "select_by_name_exact", text="Exact")
        # Perform the selection
        op = col.operator("artistant.select_by_name", text="Select", icon='RESTRICT_SELECT_OFF')
        op.query = context.scene.select_by_name_query
        op.exact = context.scene.select_by_name_exact

        # --- Utilities Section: Image and Asset Management ---
        util_box = layout.box()
        util_box.label(text="Utilities", icon='FILE_REFRESH')
        # Reload all images from disk (useful after external texture updates)
        util_box.operator("artistant.reload_images", text="Reload Images", icon='IMAGE')
