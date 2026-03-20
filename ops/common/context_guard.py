from contextlib import contextmanager

import bpy


@contextmanager
def preserve_selection_and_active(context):
    original_selection = list(context.selected_objects)
    original_active = context.view_layer.objects.active
    try:
        yield
    finally:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            try:
                obj.select_set(True)
            except Exception:
                pass
        if original_active:
            context.view_layer.objects.active = original_active
