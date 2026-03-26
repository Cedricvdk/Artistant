import bpy
from bpy.types import Operator


class ARTISTANT_OT_floor_object(Operator):
    """Translate each selected object so its origin sits at world Z = 0"""
    bl_idname = "artistant.floor_object"
    bl_label = "Floor Object"
    bl_description = "Move each selected object so its origin (pivot) is at world Z = 0"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}

        count = 0
        for obj in selected:
            world_z = obj.matrix_world.translation.z
            if abs(world_z) < 1e-6:
                # Already at Z = 0 — skip to avoid unnecessary updates
                continue

            # Build an updated world matrix with Z translation zeroed out.
            # Assigning to matrix_world automatically back-propagates the change
            # to matrix_local, so this works correctly for both parented and
            # unparented objects without manual parent-space math.
            new_mat = obj.matrix_world.copy()
            new_mat.translation.z = 0.0
            obj.matrix_world = new_mat
            count += 1

        self.report({'INFO'}, f"Floored {count} object(s) to world Z = 0")
        return {'FINISHED'}
