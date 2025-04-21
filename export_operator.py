import bpy
import os

class ARTISTANT_OT_export_unity_fbx(bpy.types.Operator):
    bl_idname = "artistant.export_unity_fbx"
    bl_label = "Export Unity Asset"

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        export_folder = context.scene.export_folder
        if not export_folder:
            self.report({'ERROR'}, "No export path specified")
            return {'CANCELLED'}

        # Ensure the export folder exists
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)

        export_individual = context.scene.export_individual

        if export_individual:
            for obj in selected_objects:
                # Deselect all objects
                bpy.ops.object.select_all(action='DESELECT')
        
                # Select the current object
                obj.select_set(True)
                context.view_layer.objects.active = obj
        
                export_name = obj.name
                export_path = os.path.join(export_folder, f"{export_name}.fbx")
        
                bpy.ops.export_scene.fbx(
                    filepath=export_path,
                    use_selection=True,
                    apply_scale_options='FBX_SCALE_UNITS',
                    axis_forward='-Y',
                    axis_up='Z',
                    apply_unit_scale=True,
                    use_space_transform=False
                )
        
            # Reselect the original objects
            for obj in selected_objects:
                obj.select_set(True)
        else:
            export_name = context.view_layer.objects.active.name
            export_path = os.path.join(export_folder, f"{export_name}.fbx")
            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=True,
                apply_scale_options='FBX_SCALE_UNITS',
                axis_forward='-Y',
                axis_up='Z',
                apply_unit_scale=True,
                use_space_transform=False
            )


        self.report({'INFO'}, f"Exported to {export_folder}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ARTISTANT_OT_export_unity_fbx)

def unregister():
    bpy.utils.unregister_class(ARTISTANT_OT_export_unity_fbx)
