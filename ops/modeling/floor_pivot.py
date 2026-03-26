import bpy
from bpy.types import Operator


class ARTISTANT_OT_floor_pivot(Operator):
    """Move each selected mesh object's origin to the lowest point of its geometry in world Z"""
    bl_idname = "artistant.floor_pivot"
    bl_label = "Floor Pivot"
    bl_description = (
        "Move the origin (pivot) of each selected mesh object down to its lowest "
        "geometry vertex in world-space Z"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def _mode_for_mode_set(context_mode: str) -> str:
        """Map context.mode values to bpy.ops.object.mode_set(mode=...) values."""
        if context_mode == 'EDIT_MESH':
            return 'EDIT'
        return context_mode

    def execute(self, context):
        starting_mode = context.mode
        switched_to_object = False

        # origin_set requires Object mode
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            switched_to_object = True

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not selected_meshes:
            if switched_to_object:
                bpy.ops.object.mode_set(mode=self._mode_for_mode_set(starting_mode))
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        cursor = context.scene.cursor

        # Snapshot cursor and selection so we can restore them after the operation
        saved_cursor_loc = cursor.location.copy()
        saved_selection = list(context.selected_objects)
        saved_active = context.view_layer.objects.active

        count = 0
        for obj in selected_meshes:
            # Evaluate the mesh with all modifiers applied
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            if not mesh or not mesh.vertices:
                eval_obj.to_mesh_clear()
                continue

            # Find the minimum world-space Z among all vertices
            mat = obj.matrix_world
            min_z = min((mat @ v.co).z for v in mesh.vertices)
            eval_obj.to_mesh_clear()

            # Place the 3D cursor at the object's current XY origin but at floor Z.
            # This keeps the pivot centred over the object, only dropping it to the bottom.
            world_origin = obj.matrix_world.translation
            cursor.location = (world_origin.x, world_origin.y, min_z)

            # Isolate the object so origin_set only affects this one
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            count += 1

        # Restore cursor, selection, and active object
        cursor.location = saved_cursor_loc
        bpy.ops.object.select_all(action='DESELECT')
        for obj in saved_selection:
            obj.select_set(True)
        if saved_active and saved_active.name in context.view_layer.objects:
            context.view_layer.objects.active = saved_active

        # Return user to the mode they were in before running the operator
        if switched_to_object:
            bpy.ops.object.mode_set(mode=self._mode_for_mode_set(starting_mode))

        self.report({'INFO'}, f"Floor pivot applied to {count} object(s)")
        return {'FINISHED'}
