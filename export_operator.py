# export_operator.py
import bpy
import os
import math
from bpy.types import Operator
from mathutils import Vector


# ---------------- Heuristics & helpers ----------------

def _needs_hierarchy_safe(objs):
    """Heuristic for Auto mode: true if we detect rigs or deep hierarchies."""
    for o in objs:
        # Any armature object or armature modifier on a mesh
        if o.type == 'ARMATURE':
            return True
        if any(m.type == 'ARMATURE' for m in getattr(o, "modifiers", [])):
            return True
        # Parent depth > 1 or children depth > 1
        if o.parent and o.parent.parent:
            return True
        if any(c.children for c in o.children):
            return True
        # Constraints often imply hierarchy/rig behavior
        if getattr(o, "constraints", None) and len(o.constraints) > 0:
            return True
    return False


def _fbx_supported_object_types():
    """Query supported object_types for FBX exporter in this Blender build."""
    try:
        prop = bpy.ops.export_scene.fbx.get_rna_type().properties['object_types']
        return {item.identifier for item in prop.enum_items}
    except Exception:
        # Sensible default fallback for Blender 4.x family
        return {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'}


def _fbx_object_types_for_export():
    """Return a valid set to pass to object_types (prefer meshes, keep common types)."""
    desired = {'MESH', 'ARMATURE', 'EMPTY', 'CAMERA', 'LIGHT', 'OTHER'}
    supported = _fbx_supported_object_types()
    chosen = desired & supported
    return chosen or {'MESH'}


def _roots_in_selection(objs):
    """Return only objects whose parent is not inside 'objs'."""
    s = set(objs)
    return [o for o in objs if (o.parent not in s)]


# ---------------- Operator ----------------

class ARTISTANT_OT_export_unity_fbx(Operator):
    """Export selected objects as Unity-ready FBX with selectable modes"""
    bl_idname = "artistant.export_unity_fbx"
    bl_label = "Export Unity Asset"
    bl_options = {'REGISTER', 'UNDO'}

    # Panel will pass the Scene setting; can also be picked in Redo panel
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('AUTO', "Auto", "Detect rigs/hierarchies, choose best mode"),
            ('SIMPLE', "Simple (fast)", "Use exporter bake (Apply Transform)"),
            ('HSAFE', "Hierarchy-safe (slow)", "Duplicate + counter-rotate + export"),
        ],
        default='AUTO'
    )

    # New: Reset root location to 0,0,0 for the exported asset
    reset_location: bpy.props.BoolProperty(
        name="Reset Root Location (0,0,0)",
        description="Force exported root(s) to have Location (0,0,0). Children keep relative offsets",
        default=False,
    )

    # Usual toggles (available in the F9/Redo panel)
    apply_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        default=True,
    )
    embed_textures: bpy.props.BoolProperty(
        name="Embed Textures (FBX)",
        default=False,
    )

    # -------- SIMPLE PATH (fast) --------
    def _export_simple(self, *, export_path: str, use_selection=True):
        bpy.ops.export_scene.fbx(
            filepath=export_path,
            use_selection=use_selection,
            use_active_collection=False,
            object_types=_fbx_object_types_for_export(),
            # Units/scaling so Unity imports at Scale=1 (meters)
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_UNITS',
            # Axis mapping aimed at Unity (Y-up, Z-forward)
            axis_forward='-Z',
            axis_up='Y',
            # Bake axis conversion into the file so Unity sees identity
            use_space_transform=True,
            bake_space_transform=True,  # Blender 4.5+ Python API for "Apply Transform"
            add_leaf_bones=False,
            bake_anim=False,
            use_mesh_modifiers=self.apply_modifiers,
            mesh_smooth_type='FACE',
            use_tspace=True,  # export tangents
            path_mode='COPY' if self.embed_textures else 'AUTO',
            embed_textures=self.embed_textures,
        )

    # -------- HIERARCHY-SAFE PATH (duplicate + counter-rotate) --------
    def _duplicate_objects(self, objs, temp_coll_name="IGP_TMP_EXPORT"):
        """Duplicate objects into a dedicated temp collection and return duplicates + collection."""
        temp_coll = bpy.data.collections.new(temp_coll_name)
        bpy.context.scene.collection.children.link(temp_coll)

        # Duplicate as a block
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.duplicate(linked=False)
        dups = [obj for obj in bpy.context.selected_objects]

        # Move duplicates exclusively to temp collection
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

    # ---- Reset-to-origin helpers ----
    def _reset_origin_simple_single(self, obj, do_reset: bool):
        """Temporarily move a single object so its local Location=0,0,0; restore after export."""
        if not do_reset:
            return None  # no-op
        original_loc = obj.location.copy()
        obj.location = Vector((0.0, 0.0, 0.0))
        return original_loc

    def _restore_origin_simple_single(self, obj, saved_loc):
        if saved_loc is not None:
            obj.location = saved_loc

    def _reset_origin_simple_batch(self, context, selected_objs, do_reset: bool):
        """Temporarily move root-most objects so that ACTIVE object's root sits at world origin.
        Returns dict of {root_obj: original_location} for restoration.
        """
        if not do_reset or not selected_objs:
            return {}

        active = context.view_layer.objects.active
        anchor = active if (active and active in selected_objs) else selected_objs[0]

        roots = _roots_in_selection(selected_objs)
        if not roots:
            roots = selected_objs[:]  # fallback

        # We want the anchor's world location to become (0,0,0):
        delta = -anchor.location.copy()

        saved = {}
        for r in roots:
            saved[r] = r.location.copy()
            r.location = r.location + delta
        return saved

    def _restore_origin_simple_batch(self, saved: dict):
        for obj, loc in saved.items():
            obj.location = loc

    def _reset_origin_hsafe_for_one(self, dups, original_root_name, do_reset: bool):
        """Set duplicate root location to origin."""
        if not do_reset:
            return
        # Prefer name match
        root_dup = next((d for d in dups if d.name == original_root_name), None)
        if root_dup is None:
            # Fallback: pick duplicate with no parent among duplicates
            dup_set = set(dups)
            root_dup = next((d for d in dups if d.parent not in dup_set), dups[0])
        root_dup.location = Vector((0.0, 0.0, 0.0))

    def _reset_origin_hsafe_for_set(self, dups, source_objs, do_reset: bool):
        """Shift the entire duplicate set so the active (or first) duplicate root lands at origin.
        We shift only duplicate roots to avoid moving children twice.
        """
        if not do_reset or not dups:
            return
        # Map name->dup
        name_to_dup = {d.name: d for d in dups}
        # Choose anchor in source selection
        active = bpy.context.view_layer.objects.active
        anchor_src = active if (active and active in source_objs) else source_objs[0]
        anchor_dup = name_to_dup.get(anchor_src.name, dups[0])

        dup_set = set(dups)
        dup_roots = [d for d in dups if d.parent not in dup_set]
        delta = -anchor_dup.location.copy()
        for r in dup_roots:
            r.location = r.location + delta

    # ---------- Export implementations ----------

    def _export_hsafe_for_set(self, *, export_path: str, source_objs):
        dups, temp_coll = self._duplicate_objects(source_objs)
        try:
            # Reset origin on duplicates (before counter-rotate)
            self._reset_origin_hsafe_for_set(dups, source_objs, self.reset_location)
            # Bake orientation
            self._counter_rotate_apply(dups)

            bpy.ops.object.select_all(action='DESELECT')
            for d in dups:
                d.select_set(True)
            bpy.context.view_layer.objects.active = dups[0]

            bpy.ops.export_scene.fbx(
                filepath=export_path,
                use_selection=True,
                use_active_collection=False,
                object_types=_fbx_object_types_for_export(),
                apply_unit_scale=True,
                apply_scale_options='FBX_SCALE_UNITS',
                axis_forward='-Z',
                axis_up='Y',
                # We already did the counter-rotate; don't bake again
                use_space_transform=True,
                bake_space_transform=False,
                add_leaf_bones=False,
                bake_anim=False,
                use_mesh_modifiers=self.apply_modifiers,
                mesh_smooth_type='FACE',
                use_tspace=True,
                path_mode='COPY' if self.embed_textures else 'AUTO',
                embed_textures=self.embed_textures,
            )
        finally:
            self._cleanup_temp(dups, temp_coll)

    def _export_hsafe_for_one(self, *, export_path: str, src_obj):
        dups, temp_coll = self._duplicate_objects(self._gather_with_children(src_obj))
        try:
            # Reset duplicate root to origin
            self._reset_origin_hsafe_for_one(dups, src_obj.name, self.reset_location)
            # Bake orientation
            self._counter_rotate_apply(dups)

            bpy.ops.object.select_all(action='DESELECT')
            for d in dups:
                d.select_set(True)
            bpy.context.view_layer.objects.active = dups[0]

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
                bake_space_transform=False,
                add_leaf_bones=False,
                bake_anim=False,
                use_mesh_modifiers=self.apply_modifiers,
                mesh_smooth_type='FACE',
                use_tspace=True,
                path_mode='COPY' if self.embed_textures else 'AUTO',
                embed_textures=self.embed_textures,
            )
        finally:
            self._cleanup_temp(dups, temp_coll)

    # ---------- TOP-LEVEL EXECUTION ----------
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

        # Determine mode (AUTO → decide using heuristic)
        mode = self.mode
        if mode == 'AUTO':
            mode = 'HSAFE' if _needs_hierarchy_safe(selected_objects) else 'SIMPLE'

        # Preserve selection and active
        original_selection = list(context.selected_objects)
        original_active = context.view_layer.objects.active

        try:
            os.makedirs(export_folder, exist_ok=True)
            exported_paths = []

            if export_individual:
                for src_obj in selected_objects:
                    export_name = src_obj.name
                    export_path = os.path.join(export_folder, f"{export_name}.fbx")

                    if mode == 'SIMPLE':
                        # Optional reset for a single object
                        saved_loc = self._reset_origin_simple_single(src_obj, self.reset_location)
                        try:
                            bpy.ops.object.select_all(action='DESELECT')
                            src_obj.select_set(True)
                            context.view_layer.objects.active = src_obj
                            self._export_simple(export_path=export_path, use_selection=True)
                        finally:
                            self._restore_origin_simple_single(src_obj, saved_loc)
                    else:
                        self._export_hsafe_for_one(export_path=export_path, src_obj=src_obj)

                    exported_paths.append(export_path)

                # Restore selection
                bpy.ops.object.select_all(action='DESELECT')
                for obj in original_selection:
                    obj.select_set(True)
                if original_active:
                    context.view_layer.objects.active = original_active

            else:
                # Batch: one FBX for all selected
                active = context.view_layer.objects.active
                export_name = active.name if active and active in selected_objects else "Export"
                export_path = os.path.join(export_folder, f"{export_name}.fbx")

                if mode == 'SIMPLE':
                    # Move only root-most objects so the active lands at origin
                    saved = self._reset_origin_simple_batch(context, selected_objects, self.reset_location)
                    try:
                        bpy.ops.object.select_all(action='DESELECT')
                        for o in selected_objects:
                            o.select_set(True)
                        if active and active in selected_objects:
                            context.view_layer.objects.active = active
                        self._export_simple(export_path=export_path, use_selection=True)
                    finally:
                        self._restore_origin_simple_batch(saved)
                else:
                    self._export_hsafe_for_set(export_path=export_path, source_objs=selected_objects)

                exported_paths.append(export_path)

        except Exception as e:
            # Restore selection before reporting
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                obj.select_set(True)
            if original_active:
                context.view_layer.objects.active = original_active

            self.report({'ERROR'}, f"FBX export failed: {e}")
            return {'CANCELLED'}

        # Restore selection at the end (success)
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        if original_active:
            context.view_layer.objects.active = original_active

        # Report
        plural = "FBXs" if len(exported_paths) > 1 else "FBX"
        self.report({'INFO'}, f"Exported {len(exported_paths)} {plural} to: {export_folder} (Mode: {mode})")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ARTISTANT_OT_export_unity_fbx)

def unregister():
    bpy.utils.unregister_class(ARTISTANT_OT_export_unity_fbx)
