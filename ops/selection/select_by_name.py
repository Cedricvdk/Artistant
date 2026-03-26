import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty


class ARTISTANT_OT_select_by_name(Operator):
    """Select objects by name (exact or contains)"""
    bl_idname = "artistant.select_by_name"
    bl_label = "Select By Name"
    bl_description = "Select objects whose name matches (Exact) or contains the query"
    bl_options = {'REGISTER', 'UNDO'}

    # These are set by the panel when invoking the operator
    query: StringProperty(
        name="Name",
        description="Text to match against object names",
        default=""
    )
    exact: BoolProperty(
        name="Exact",
        description="Exact match (OFF = contains, case-insensitive)",
        default=False
    )

    def execute(self, context):
        # Normalize query string
        query = (self.query or "").strip()
        if not query:
            self.report({'WARNING'}, "Please enter a name to search.")
            return {'CANCELLED'}

        # Ensure we're in OBJECT mode for reliable selection
        if context.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass

        # Clear the selection before performing the search
        bpy.ops.object.select_all(action='DESELECT')

        # Prepare for case-insensitive search if not exact match
        q_lower = query.lower()
        matches = []

        # Search through all objects in current view layer
        for obj in context.view_layer.objects:
            name = obj.name
            # Check if name matches (exact or contains)
            is_match = (name == query) if self.exact else (q_lower in name.lower())
            if is_match:
                obj.select_set(True)
                matches.append(obj)

        # Report results and set active object for convenience
        if matches:
            try:
                context.view_layer.objects.active = matches[0]
            except Exception:
                pass
            self.report({'INFO'}, f"Selected {len(matches)} object(s) matching '{query}'.")
            return {'FINISHED'}
        else:
            self.report({'INFO'}, f"No objects matched '{query}'.")
            return {'CANCELLED'}
