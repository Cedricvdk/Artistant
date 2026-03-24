import math
import os

import bpy
from bpy.types import Operator
from ..common.context_guard import preserve_selection_and_active


def _fbx_supported_object_types():
    """Query supported object_types for FBX exporter in this Blender build."""
    try:
        prop = bpy.ops.export_scene.fbx.get_rna_type().properties['object_types']
        return {item.identifier for item in prop.enum_items}
    except Exception:
        # Sensible default fallback for Blender 4.x family
        return {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'}


def _fbx_object_types_for_export():
    """Return a valid set to pass to object_types for Unity export."""
    desired = {'MESH', 'ARMATURE', 'EMPTY', 'CAMERA', 'LIGHT', 'OTHER'}
    supported = _fbx_supported_object_types()
    chosen = desired & supported
    if 'ARMATURE' in supported:
        chosen.add('ARMATURE')
    return chosen or ({'ARMATURE', 'MESH'} & supported) or {'MESH'}


def _root_objects(objs):
    """Return only objects whose parent is not inside 'objs'."""
    s = set(objs)
    return [o for o in objs if (o.parent not in s)]


class ARTISTANT_OT_export_unity_fbx(Operator):
    """Export selected objects as Unity-ready FBX through a duplicate-only pipeline"""
    bl_idname = "artistant.export_unity_fbx"
    bl_label = "Export Unity Asset"
    bl_options = {'REGISTER', 'UNDO'}

    reset_location: bpy.props.BoolProperty(
        name="Reset Root Location (0,0,0)",
        description="Force exported root(s) to have Location (0,0,0). Children keep relative offsets",
        default=False,
    )

    apply_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        default=True,
    )
    embed_textures: bpy.props.BoolProperty(
        name="Embed Textures (FBX)",
        default=False,
    )

    def _export_selected_duplicates(self, export_path: str):
        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=True,
            use_active_collection=False,
            object_types=_fbx_object_types_for_export(),
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_UNITS',
            axis_forward='-Z',
            axis_up='Y',
            use_space_transform=True,
            add_leaf_bones=False,
            bake_anim=False,
            use_mesh_modifiers=self.apply_modifiers,
            mesh_smooth_type='FACE',
            use_tspace=True,
            path_mode='COPY' if self.embed_textures else 'AUTO',
            embed_textures=self.embed_textures,
        )

    def _duplicate_objects(self, objs, temp_coll_name="IGP_TMP_EXPORT"):
        """Duplicate objects into a dedicated temp collection and return duplicates + collection."""
        temp_coll = bpy.data.collections.new(temp_coll_name)
        bpy.context.scene.collection.children.link(temp_coll)

        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.duplicate(linked=False)
        dups = [obj for obj in bpy.context.selected_objects]

        for d in dups:
            for c in list(d.users_collection):
                c.objects.unlink(d)
            temp_coll.objects.link(d)

        return dups, temp_coll

    def _counter_rotate_apply(self, objs):
        """Rotate -90° X, apply rotation, then +90° X (not applied)."""
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]

        for o in objs:
            o.rotation_euler.rotate_axis('X', -math.radians(90))
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        for o in objs:
            o.rotation_euler.rotate_axis('X', math.radians(90))

    def _cleanup_temp(self, dups, temp_coll):
        bpy.ops.object.select_all(action='DESELECT')
        for d in dups:
            d.select_set(True)
        bpy.ops.object.delete(use_global=False)
        if temp_coll and temp_coll.name in bpy.data.collections:
            try:
                bpy.data.collections.remove(temp_coll)
            except Exception:
                pass

    def _gather_with_children(self, root):
        out, stack, seen = [], [root], set()
        while stack:
            o = stack.pop()
            if o.name in seen:
                continue
            seen.add(o.name)
            out.append(o)
            stack.extend(list(o.children))
        return out

    def _reset_duplicate_roots(self, dups, anchor_location, do_reset: bool):
        """Shift duplicate roots so the chosen anchor exports at world origin."""
        if not do_reset or not dups:
            return
        dup_roots = _root_objects(dups)
        if not dup_roots:
            dup_roots = dups[:]

        delta = -anchor_location.copy()
        for root in dup_roots:
            root.location = root.location + delta

    def _export_duplicate_set(self, *, export_path: str, source_objs, anchor_location):
        dups, temp_coll = self._duplicate_objects(source_objs)
        try:
            self._reset_duplicate_roots(dups, anchor_location, self.reset_location)
            self._counter_rotate_apply(dups)

            bpy.ops.object.select_all(action='DESELECT')
            for d in dups:
                d.select_set(True)
            bpy.context.view_layer.objects.active = dups[0]

            self._export_selected_duplicates(export_path)
        finally:
            self._cleanup_temp(dups, temp_coll)

    def execute(self, context):
        selected_objects = [o for o in context.selected_objects if o.visible_get()]
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        export_folder = context.scene.export_folder
        if not export_folder:
            self.report({'ERROR'}, "No export path specified")
            return {'CANCELLED'}

        export_individual = context.scene.export_individual
        active = context.view_layer.objects.active
        anchor = active if active and active in selected_objects else selected_objects[0]

        try:
            os.makedirs(export_folder, exist_ok=True)
            exported_paths = []

            with preserve_selection_and_active(context):
                if export_individual:
                    for src_obj in selected_objects:
                        export_name = src_obj.name
                        export_path = os.path.join(export_folder, f"{export_name}.fbx")
                        source_objs = self._gather_with_children(src_obj)
                        self._export_duplicate_set(
                            export_path=export_path,
                            source_objs=source_objs,
                            anchor_location=src_obj.location,
                        )
                        exported_paths.append(export_path)
                else:
                    export_name = anchor.name if anchor in selected_objects else "Export"
                    export_path = os.path.join(export_folder, f"{export_name}.fbx")
                    self._export_duplicate_set(
                        export_path=export_path,
                        source_objs=selected_objects,
                        anchor_location=anchor.location,
                    )
                    exported_paths.append(export_path)

        except Exception as e:
            self.report({'ERROR'}, f"FBX export failed: {e}")
            return {'CANCELLED'}

        plural = "FBXs" if len(exported_paths) > 1 else "FBX"
        self.report({'INFO'}, f"Exported {len(exported_paths)} {plural} to: {export_folder}")
        return {'FINISHED'}
