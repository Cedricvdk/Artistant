from contextlib import contextmanager

import bpy


@contextmanager
def preserve_selection_and_active(context):
    """Context manager that preserves the active and selected objects.
    
    This is useful for operators that temporarily modify the scene state
    (e.g., duplication, export) without affecting the user's selection.
    
    Usage:
        with preserve_selection_and_active(context):
            # Do work here; selection will be restored at the end
    """
    # Save current selection and active object before any changes
    original_selection = list(context.selected_objects)
    original_active = context.view_layer.objects.active
    try:
        # Yield control to the calling code
        yield
    finally:
        # Always restore the original state, even if an error occurred
        bpy.ops.object.select_all(action='DESELECT')
        # Restore originally selected objects
        for obj in original_selection:
            try:
                obj.select_set(True)
            except Exception:
                # Object may have been deleted or is otherwise inaccessible
                pass
        # Restore the active object
        if original_active:
            context.view_layer.objects.active = original_active
