from mathutils import Vector


def world_bounds_from_objects(objects):
    min_bound = Vector((float('inf'), float('inf'), float('inf')))
    max_bound = Vector((float('-inf'), float('-inf'), float('-inf')))

    for obj in objects:
        for vertex in obj.bound_box:
            world_vertex = obj.matrix_world @ Vector(vertex)
            min_bound = Vector((
                min(min_bound.x, world_vertex.x),
                min(min_bound.y, world_vertex.y),
                min(min_bound.z, world_vertex.z),
            ))
            max_bound = Vector((
                max(max_bound.x, world_vertex.x),
                max(max_bound.y, world_vertex.y),
                max(max_bound.z, world_vertex.z),
            ))

    return min_bound, max_bound
