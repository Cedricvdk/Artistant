import bpy
from mathutils import Vector


class ARTISTANT_OT_smart_group_operator(bpy.types.Operator):
    bl_idname = "artistant.smart_group_operator"
    bl_label = "Smart Group"

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        # Create empty cube
        bpy.ops.object.empty_add(type='CUBE')
        empty = context.object

        # Align empty to bounding box of selected objects
        min_bound = Vector((float('inf'), float('inf'), float('inf')))
        max_bound = Vector((float('-inf'), float('-inf'), float('-inf')))
        for obj in selected_objects:
            for vertex in obj.bound_box:
                world_vertex = obj.matrix_world @ Vector(vertex)
                min_bound = Vector((min(min_bound.x, world_vertex.x), min(min_bound.y, world_vertex.y), min(min_bound.z, world_vertex.z)))
                max_bound = Vector((max(max_bound.x, world_vertex.x), max(max_bound.y, world_vertex.y), max(max_bound.z, world_vertex.z)))

        empty.location = (min_bound + max_bound) / 2
        empty.scale = (max_bound - min_bound) / 2

        # Parent selected objects to empty
        for obj in selected_objects:
            if obj.parent is None:
                obj.select_set(True)
                empty.select_set(True)
                context.view_layer.objects.active = empty
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                obj.select_set(False)

        self.report({'INFO'}, "Smart group created")
        return {'FINISHED'}
