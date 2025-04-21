import bpy

class ARTISTANT_PT_panel(bpy.types.Panel):
    bl_label = "Artistant"
    bl_idname = "ARTISTANT_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Artistant'

    def draw(self, context):
        layout = self.layout
        layout.operator("artistant.auto_lattice_operator")
        layout.operator("artistant.smart_group_operator")
        
        layout.label(text="Export Unity Asset")
        layout.prop(context.scene, "export_folder")
        layout.prop(context.scene, "export_individual")
        layout.operator("artistant.export_unity_fbx")

def register():
    bpy.types.Scene.export_folder = bpy.props.StringProperty(
        name="Export Folder",
        subtype='DIR_PATH',
        default=""
    )
    bpy.types.Scene.export_individual = bpy.props.BoolProperty(
        name="Individual",
        default=False
    )
    bpy.utils.register_class(ARTISTANT_PT_panel)


def unregister():
    del bpy.types.Scene.export_folder
    del bpy.types.Scene.export_individual
    bpy.utils.unregister_class(ARTISTANT_PT_panel)