import bpy
from mathutils import Vector

# AUTO LATTICE
class ARTISTANT_OT_auto_lattice_operator(bpy.types.Operator):
    bl_idname = "artistant.auto_lattice_operator"
    bl_label = "Auto-Lattice"

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        # Check if all selected objects are meshes
        for obj in selected_objects:
            if obj.type != 'MESH':
                self.report({'ERROR'}, "All selected objects must be meshes")
                return {'CANCELLED'}

        # Create lattice
        bpy.ops.object.add(type='LATTICE')
        lattice = context.object
        lattice.data.points_u = 3
        lattice.data.points_v = 3
        lattice.data.points_w = 3

        # Align lattice to bounding box of selected objects
        min_bound = Vector((float('inf'), float('inf'), float('inf')))
        max_bound = Vector((float('-inf'), float('-inf'), float('-inf')))
        for obj in selected_objects:
            for vertex in obj.bound_box:
                world_vertex = obj.matrix_world @ Vector(vertex)
                min_bound = Vector((min(min_bound.x, world_vertex.x), min(min_bound.y, world_vertex.y), min(min_bound.z, world_vertex.z)))
                max_bound = Vector((max(max_bound.x, world_vertex.x), max(max_bound.y, world_vertex.y), max(max_bound.z, world_vertex.z)))

        lattice.location = (min_bound + max_bound) / 2
        lattice.scale = (max_bound - min_bound)

        # Parent selected objects to lattice and add lattice modifier
        for obj in selected_objects:
            if obj.parent is None:
                obj.select_set(True)
                lattice.select_set(True)
                context.view_layer.objects.active = lattice
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                obj.select_set(False)
            lattice_modifier = obj.modifiers.new(name="Lattice", type='LATTICE')
            lattice_modifier.object = lattice

        self.report({'INFO'}, "Lattice created and applied")
        return {'FINISHED'}

# SMART GROUP
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