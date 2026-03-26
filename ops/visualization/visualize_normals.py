import os
import bpy
from bpy.types import Operator

from ...core.paths import asset_path


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
    BLEND_FILE_NAME = "visualize_normals.blend"

    @classmethod
    def poll(cls, context):
        # At least one selectable object
        return bool(getattr(context, "selected_editable_objects", []))

    def _get_or_load_node_group(self):
        """Return the Geometry Node group, loading it from the bundled .blend if needed.
        
        Returns:
            The showNormals node group, or None if loading failed.
        """
        # Check if the node group is already loaded in memory
        ng = bpy.data.node_groups.get(self.NODE_GROUP_NAME)
        if ng:
            return ng

        # Construct path to the bundled .blend file
        blend_path = asset_path(self.BLEND_FILE_NAME)

        if not os.path.exists(blend_path):
            self.report({'ERROR'}, f"Blend file not found: {blend_path}")
            return None

        try:
            # Load (not link) the node group from the .blend file
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                if self.NODE_GROUP_NAME not in data_from.node_groups:
                    self.report(
                        {'ERROR'},
                        f"Node group '{self.NODE_GROUP_NAME}' not found in '{self.BLEND_FILE_NAME}'. "
                        f"Available: {', '.join(data_from.node_groups)}"
                    )
                    return None
                # Append the node group to this .blend file
                data_to.node_groups = [self.NODE_GROUP_NAME]
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load node group: {e}")
            return None

        # Return the now-loaded node group
        return bpy.data.node_groups.get(self.NODE_GROUP_NAME)

    def execute(self, context):
        # Load the node group (or use cached version if already loaded)
        ng = self._get_or_load_node_group()
        if not ng:
            return {'CANCELLED'}

        # Define object types that support Geometry Nodes modifiers
        supported_types = {'MESH', 'CURVE', 'CURVES', 'POINTCLOUD', 'VOLUME', 'GREASEPENCIL', 'GPENCIL'}
        affected = 0

        # Apply the node group to each selected object
        for obj in context.selected_editable_objects:
            if obj.type not in supported_types:
                continue

            # Skip if object already has this node group (avoid duplicates)
            already_has = any(
                (m.type == 'NODES' and getattr(m, "node_group", None) == ng)
                for m in obj.modifiers
            )
            if already_has:
                continue

            # Create a new Geometry Nodes modifier with the showNormals group
            mod = obj.modifiers.new(self.modifier_name, 'NODES')
            mod.node_group = ng
            affected += 1

        # Report how many objects were modified
        if affected == 0:
            self.report({'INFO'}, "Nothing to do. Selected objects already use 'showNormals' (or are unsupported types).")
        else:
            self.report({'INFO'}, f"Applied 'showNormals' to {affected} object(s).")

        return {'FINISHED'}
