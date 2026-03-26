import bpy
from bpy.types import Operator


class ARTISTANT_OT_select_orphans(Operator):
    """Select parentless objects — filters current selection or selects all scene orphans"""
    bl_idname = "artistant.select_orphans"
    bl_label = "Select Orphans"
    bl_description = (
        "No selection: select all parentless objects in the scene. "
        "With selection: deselect objects that have a parent, keeping only orphans"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = list(context.selected_objects)

        if not selected:
            # Case A — nothing selected: select every parentless object in the scene
            count = 0
            for obj in context.scene.objects:
                if obj.parent is None:
                    obj.select_set(True)
                    count += 1
            self.report({'INFO'}, f"Selected {count} orphan object(s)")
        else:
            # Case B — filter current selection: deselect objects that have a parent
            kept = 0
            removed = 0
            for obj in selected:
                if obj.parent is not None:
                    obj.select_set(False)
                    removed += 1
                else:
                    kept += 1
            self.report(
                {'INFO'},
                f"Kept {kept} orphan(s), deselected {removed} parented object(s)",
            )

        return {'FINISHED'}
