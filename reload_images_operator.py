import bpy
import os

class ARTISTANT_OT_reload_images(bpy.types.Operator):
    bl_idname = "artistant.reload_images"
    bl_label = "Reload Images"
    bl_description = "Reload all images in the current Blender file"
    
    def execute(self, context):
        for image in bpy.data.images:
            image.reload()
    
        return {'FINISHED'}