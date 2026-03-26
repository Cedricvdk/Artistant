import bpy


class ARTISTANT_OT_reload_images(bpy.types.Operator):
    """Reload all images in the current Blender file from their source files on disk"""
    bl_idname = "artistant.reload_images"
    bl_label = "Reload Images"
    bl_description = "Reload all images in the current Blender file"

    def execute(self, context):
        # Iterate all image data blocks and reload from disk
        for image in bpy.data.images:
            image.reload()

        return {'FINISHED'}
