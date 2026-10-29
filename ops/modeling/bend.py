import os

import bpy
from bpy.types import Operator

from ...core.paths import asset_path


class ARTISTANT_OT_add_bend_modifier(Operator):
    """Add the Bend Geometry Nodes modifier (gizmos are built into the node group)"""
    bl_idname = "object.artistant_add_bend_modifier"
    bl_label = "Bend"
    bl_options = {'REGISTER', 'UNDO'}

    NODE_GROUP_NAME = "Bend"
    BLEND_FILE_NAME = "bend_modifier.blend"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type in {'MESH', 'CURVE', 'CURVES', 'POINTCLOUD'}

    def _get_or_load_node_group(self):
        """Return the Bend node group, appending it from the bundled .blend if needed."""
        ng = bpy.data.node_groups.get(self.NODE_GROUP_NAME)
        if ng:
            return ng

        blend_path = asset_path(self.BLEND_FILE_NAME)
        if not os.path.exists(blend_path):
            self.report({'ERROR'}, f"Blend file not found: {blend_path}")
            return None

        try:
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

        return bpy.data.node_groups.get(self.NODE_GROUP_NAME)

    def execute(self, context):
        ng = self._get_or_load_node_group()
        if not ng:
            return {'CANCELLED'}

        mod = context.object.modifiers.new("Bend", 'NODES')
        mod.node_group = ng
        return {'FINISHED'}


def draw_add_bend_menu_item(self, context):
    """Append Bend to Add Modifier > Deform."""
    self.layout.separator()
    self.layout.operator(ARTISTANT_OT_add_bend_modifier.bl_idname, text="Bend", icon='MOD_SIMPLEDEFORM')
