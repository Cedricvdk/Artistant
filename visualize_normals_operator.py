
# visualize_normals_operator.py

import os
import bpy
from bpy.types import Operator


class ARTISTANT_OT_visualize_normals(Operator):
    """Add 'showNormals' Geometry Nodes to selected objects (loads the group once per .blend)"""
    bl_idname = "artistant.visualize_normals"
    bl_label = "Visualize Normals"
    bl_options = {'REGISTER', 'UNDO'}

    # You can change this if you want another label for the modifier in the stack
    modifier_name: bpy.props.StringProperty(
        name="Modifier Name",
        default="Show Normals"
    )

    # The node group name and the .blend filename that contains it
    NODE_GROUP_NAME = "showNormals"
    BLEND_FILE_NAME = "vizualizeNormals.blend"

    @classmethod
    def poll(cls, context):
        # At least one selectable object
        return bool(getattr(context, "selected_editable_objects", []))

    def _get_or_load_node_group(self):
        """Return the Geometry Node group, loading it from the bundled .blend if needed"""
        ng = bpy.data.node_groups.get(self.NODE_GROUP_NAME)
        if ng:
            return ng

        # Resolve path to the .blend that ships with the addon (same folder as __init__.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        blend_path = os.path.join(base_dir, self.BLEND_FILE_NAME)

        if not os.path.exists(blend_path):
            self.report({'ERROR'}, f"Blend file not found: {blend_path}")
            return None

        try:
            # Use libraries.load to append (not link) the node group once
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                if self.NODE_GROUP_NAME not in data_from.node_groups:
                    self.report(
                        {'ERROR'},
                        f"Node group '{self.NODE_GROUP_NAME}' not found in '{self.BLEND_FILE_NAME}'. "
                        f"Available: {', '.join(data_from.node_groups)}"
                    )
                    return None
                data_to.node_groups = [self.NODE_GROUP_NAME]
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load node group: {e}")
            return None

        # Should now exist under the intended name
        return bpy.data.node_groups.get(self.NODE_GROUP_NAME)

    def execute(self, context):
        ng = self._get_or_load_node_group()
        if not ng:
            return {'CANCELLED'}

        supported_types = {'MESH', 'CURVE', 'CURVES', 'POINTCLOUD', 'VOLUME', 'GREASEPENCIL', 'GPENCIL'}
        affected = 0

        for obj in context.selected_editable_objects:
            if obj.type not in supported_types:
                continue

            # Skip if object already has a Geometry Nodes modifier using this group
            already_has = any(
                (m.type == 'NODES' and getattr(m, "node_group", None) == ng)
                for m in obj.modifiers
            )
            if already_has:
                continue

            # Create a fresh Geometry Nodes modifier and assign the node group
            mod = obj.modifiers.new(self.modifier_name, 'NODES')
            mod.node_group = ng
            affected += 1

        if affected == 0:
            self.report({'INFO'}, "Nothing to do. Selected objects already use 'showNormals' (or are unsupported types).")
        else:
            self.report({'INFO'}, f"Applied 'showNormals' to {affected} object(s).")

        return {'FINISHED'}
