def iter_object_image_texture_nodes(obj):
    """Yield (material, node) for every Image Texture node with an assigned image
    on a mesh object's materials.
    """
    if not obj or obj.type != 'MESH':
        return

    for mat in obj.data.materials:
        if not mat or not mat.use_nodes or not mat.node_tree:
            continue
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                yield mat, node
