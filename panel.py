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