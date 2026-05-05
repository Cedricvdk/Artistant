import os
import uuid

import bpy
from bpy.types import Operator
from ..common.context_guard import preserve_selection_and_active


ORIGIN_MODE_PRESERVE = "preserve"
ORIGIN_MODE_ROOTS_TO_ZERO = "roots_to_zero"
EXPORT_ID_KEY = "_igp_export_id"


def _fbx_supported_object_types():
    """Query supported object_types for FBX exporter in this Blender build.
    
    Returns:
        A set of valid object type identifiers (e.g., 'MESH', 'ARMATURE', 'EMPTY')
    """
    try:
        # Dynamically query the FBX exporter's available object types
        prop = bpy.ops.export_scene.fbx.get_rna_type().properties['object_types']
        return {item.identifier for item in prop.enum_items}
    except Exception:
        # Sensible default fallback for Blender 4.x family if query fails
        return {'EMPTY', 'CAMERA', 'LIGHT', 'ARMATURE', 'MESH', 'OTHER'}


def _fbx_object_types_for_export():
    """Return a valid set to pass to object_types for Unity export.
    
    Matches requested types against what's supported in this build,
    ensuring ARMATURE is included if available (important for rigs).
    """
    # Desired object types for a complete Unity export
    desired = {'MESH', 'ARMATURE', 'EMPTY', 'CAMERA', 'LIGHT', 'OTHER'}
    # Query what this Blender build actually supports
    supported = _fbx_supported_object_types()
    # Keep only types that are both desired and supported
    chosen = desired & supported
    # Ensure ARMATURE is included if available (critical for skeletal animation)
    if 'ARMATURE' in supported:
        chosen.add('ARMATURE')
    # Fallback: if no chosen types, at least try ARMATURE and MESH
    return chosen or ({'ARMATURE', 'MESH'} & supported) or {'MESH'}


def _root_objects(objs):
    """Return only objects whose parent is not inside 'objs'.
    
    This identifies objects that are "roots" within a given set.
    Useful for distinguishing which objects need transform conversion
    (roots) vs which should be left alone (children).
    
    Args:
        objs: List of objects to filter
    
    Returns:
        Subset of objs containing only those without parents in objs
    """
    s = set(objs)
    return [o for o in objs if (o.parent not in s)]


class ARTISTANT_OT_export_unity_fbx(Operator):
    """Export selected objects as Unity-ready FBX through a duplicate-only pipeline"""
    bl_idname = "artistant.export_unity_fbx"
    bl_label = "Export Unity Asset"
    bl_options = {'REGISTER', 'UNDO'}

    apply_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        default=True,
    )
    embed_textures: bpy.props.BoolProperty(
        name="Embed Textures (FBX)",
        default=False,
    )

    def _export_selected_duplicates(self, export_path: str):
        """Call Blender's FBX exporter on the currently selected objects."""
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
            bake_space_transform=True,
            add_leaf_bones=False,
            bake_anim=False,
            use_mesh_modifiers=self.apply_modifiers,
            mesh_smooth_type='FACE',
            use_tspace=True,
            path_mode='COPY' if self.embed_textures else 'AUTO',
            embed_textures=self.embed_textures,
        )

    def _duplicate_objects(self, objs, temp_coll_name="IGP_TMP_EXPORT"):
        """Duplicate objects into a dedicated temp collection.
        
        Creates a temporary collection to preserve duplicates from interfering
        with the original scene structure during export operations.
        
        Args:
            objs: List of objects to duplicate
            temp_coll_name: Name for the temporary collection
        
        Returns:
            Tuple of (duplicated_objects, temporary_collection)
        """
        # Create a temporary collection for the duplicates
        temp_coll = bpy.data.collections.new(temp_coll_name)
        bpy.context.scene.collection.children.link(temp_coll)

        # Duplicate the source objects
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.duplicate(linked=False)
        dups = [obj for obj in bpy.context.selected_objects]

        # Move duplicates to the temp collection (remove from default collection)
        for d in dups:
            for c in list(d.users_collection):
                c.objects.unlink(d)
            temp_coll.objects.link(d)

        return dups, temp_coll

    def _assign_export_ids(self, source_objs):
        """Assign temporary per-object export IDs and return restore metadata."""
        state = {}
        for obj in source_objs:
            had_key = EXPORT_ID_KEY in obj
            prev_val = obj.get(EXPORT_ID_KEY) if had_key else None
            obj[EXPORT_ID_KEY] = uuid.uuid4().hex
            state[obj] = {
                "had_key": had_key,
                "prev_val": prev_val,
            }
        return state

    def _restore_export_ids(self, export_id_state):
        """Restore or remove temporary export ID custom properties."""
        for obj, meta in export_id_state.items():
            if meta["had_key"]:
                obj[EXPORT_ID_KEY] = meta["prev_val"]
            elif EXPORT_ID_KEY in obj:
                del obj[EXPORT_ID_KEY]

    def _build_source_to_duplicate_map(self, source_objs, dups):
        """Build exact source->duplicate object mapping via export IDs."""
        source_by_id = {}
        for src in source_objs:
            sid = src.get(EXPORT_ID_KEY)
            if not sid:
                raise RuntimeError(f"Missing export ID on source object: {src.name}")
            if sid in source_by_id:
                raise RuntimeError(f"Duplicate export ID detected on source objects: {sid}")
            source_by_id[sid] = src

        source_to_dup = {}
        for dup in dups:
            did = dup.get(EXPORT_ID_KEY)
            if not did:
                continue
            src = source_by_id.get(did)
            if not src:
                continue
            if src in source_to_dup:
                raise RuntimeError(f"Multiple duplicates mapped to source object: {src.name}")
            source_to_dup[src] = dup

        if len(source_to_dup) != len(source_objs):
            missing = [src.name for src in source_objs if src not in source_to_dup]
            raise RuntimeError(f"Failed to map duplicates for source objects: {', '.join(missing)}")

        return source_to_dup

    def _capture_original_names(self, source_objs):
        """Capture original names for restoration and duplicate rename swap."""
        return {obj: obj.name for obj in source_objs}

    def _apply_name_swap(self, source_to_dup, original_names):
        """Temporarily free source names and assign them to duplicates for export."""
        # Phase 1: move source objects out of the way with guaranteed-unique names.
        for src in source_to_dup:
            src.name = f"__IGP_SRC_TMP_{uuid.uuid4().hex}"

        # Phase 2: assign exact original source names to duplicates.
        for src, dup in source_to_dup.items():
            dup.name = original_names[src]

    def _release_duplicate_names(self, dups):
        """Rename duplicates away from source names before restoring source names."""
        for dup in dups:
            dup.name = f"__IGP_DUP_TMP_{uuid.uuid4().hex}"

    def _restore_source_names(self, original_names):
        """Restore source object names exactly to their captured originals."""
        for src, original_name in original_names.items():
            src.name = original_name

    def _prepare_duplicates_for_export(self, dups, origin_mode=ORIGIN_MODE_PRESERVE):
        """Prepare duplicates for export.

        - Detach duplicate objects that still reference non-export parents while preserving world transforms.
        - Apply origin normalization policy to duplicate roots when requested.
        """
        dup_set = set(dups)

        # Break links to parents outside the duplicate set so exported transforms stay stable.
        for dup in dups:
            if dup.parent and dup.parent not in dup_set:
                world = dup.matrix_world.copy()
                dup.parent = None
                dup.matrix_world = world

        dup_roots = _root_objects(dups)
        if not dup_roots:
            dup_roots = list(dups)

        if origin_mode == ORIGIN_MODE_ROOTS_TO_ZERO:
            for root in dup_roots:
                root.location = (0.0, 0.0, 0.0)

    def _cleanup_temp(self, dups, temp_coll):
        """Delete temporary duplicates and remove their collection.
        
        Cleans up after export to leave the scene in its original state.
        """
        # Delete all duplicate objects
        bpy.ops.object.select_all(action='DESELECT')
        for d in dups:
            d.select_set(True)
        bpy.ops.object.delete(use_global=False)
        # Remove the temporary collection
        if temp_coll and temp_coll.name in bpy.data.collections:
            try:
                bpy.data.collections.remove(temp_coll)
            except Exception:
                pass

    def _gather_with_children(self, root):
        """Recursively gather a root object and all its descendants.
        
        Used to collect a complete hierarchy when exporting individual objects
        with the export_individual flag enabled.
        
        Args:
            root: The root object to gather from
        
        Returns:
            List containing root and all descendants in depth-first order
        """
        out, stack, seen = [], [root], set()
        # Depth-first traversal using a stack
        while stack:
            o = stack.pop()
            # Avoid adding the same object twice
            if o.name in seen:
                continue
            seen.add(o.name)
            out.append(o)
            # Add all children to the stack for processing
            stack.extend(list(o.children))
        return out

    def _export_duplicate_set(self, *, export_path: str, source_objs, origin_mode=ORIGIN_MODE_PRESERVE):
        """Execute the core export pipeline: duplicate -> prepare -> export.
        
        Args:
            export_path: Full file path for the output FBX
            source_objs: List of objects to duplicate and export
            origin_mode: Origin normalization strategy for duplicate roots
        """
        # Step 1: Assign deterministic export IDs to source objects, then duplicate.
        export_id_state = self._assign_export_ids(source_objs)
        dups = []
        temp_coll = None
        source_to_dup = {}
        original_names = {}
        name_swap_active = False
        try:
            dups, temp_coll = self._duplicate_objects(source_objs)

            # Step 2: Build source<->duplicate mapping by export IDs.
            source_to_dup = self._build_source_to_duplicate_map(source_objs, dups)
            original_names = self._capture_original_names(source_objs)

            # Step 3: Prepare duplicate transforms according to mode.
            self._prepare_duplicates_for_export(
                dups,
                origin_mode=origin_mode,
            )

            # Step 4: Temporarily swap names so duplicates carry exact source names in FBX.
            name_swap_active = True
            self._apply_name_swap(source_to_dup, original_names)

            # Step 5: Select duplicates and prepare for export
            bpy.ops.object.select_all(action='DESELECT')
            for d in dups:
                d.select_set(True)
            bpy.context.view_layer.objects.active = dups[0]

            # Step 6: Call the FBX exporter while duplicates hold original names.
            self._export_selected_duplicates(export_path)
        finally:
            restore_error = None
            try:
                # Restore source names even if export failed.
                if name_swap_active and original_names:
                    self._release_duplicate_names(dups)
                    self._restore_source_names(original_names)
            except Exception as exc:
                restore_error = exc
            finally:
                # Always restore/remove export IDs and cleanup temp duplicates.
                self._restore_export_ids(export_id_state)
                self._cleanup_temp(dups, temp_coll)

            if restore_error:
                raise RuntimeError(f"Critical name-restore failure after export: {restore_error}")

    def execute(self, context):
        """Main operator entry point. Exports selected objects as FBX.
        
        Supports three modes:
        - Batch: all selected objects exported to one FBX with world transforms preserved
        - Individual (all selected): each selected object exported alone, normalized to origin
        - Individual (only orphans): each orphan exported with full hierarchy and root at origin
        """
        # Gather selected objects (excluding hidden ones)
        selected_objects = [o for o in context.selected_objects if o.visible_get()]
        if not selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        # Get export destination folder from scene properties
        export_folder = context.scene.export_folder
        if not export_folder:
            self.report({'ERROR'}, "No export path specified")
            return {'CANCELLED'}

        # Check if we should export each object individually or as a batch
        export_individual = context.scene.export_individual
        export_only_orphans = getattr(context.scene, "export_only_orphans", False)

        selected_set = set(selected_objects)
        external_parented = [o for o in selected_objects if o.parent and o.parent not in selected_set]
        if external_parented:
            self.report(
                {'WARNING'},
                "Some selected objects have unselected parents; export keeps world transforms and detaches those links in output.",
            )

        # Determine which object to use as the default filename anchor
        active = context.view_layer.objects.active
        anchor = active if active and active in selected_objects else selected_objects[0]

        try:
            # Ensure export folder exists
            os.makedirs(export_folder, exist_ok=True)
            exported_paths = []

            # Export while preserving the user's original selection and active object
            with preserve_selection_and_active(context):
                if export_individual:
                    if export_only_orphans:
                        # Case C: export only selection orphans, each with full hierarchy.
                        selected_roots = _root_objects(selected_objects)
                        orphan_roots = [obj for obj in selected_roots if obj.parent is None]
                        if not orphan_roots:
                            self.report({'WARNING'}, "No orphan objects selected")
                            return {'CANCELLED'}

                        for src_obj in orphan_roots:
                            export_name = src_obj.name
                            export_path = os.path.join(export_folder, f"{export_name}.fbx")
                            source_objs = self._gather_with_children(src_obj)
                            self._export_duplicate_set(
                                export_path=export_path,
                                source_objs=source_objs,
                                origin_mode=ORIGIN_MODE_ROOTS_TO_ZERO,
                            )
                            exported_paths.append(export_path)
                    else:
                        # Case B: export every selected object by itself (no children).
                        for src_obj in selected_objects:
                            export_name = src_obj.name
                            export_path = os.path.join(export_folder, f"{export_name}.fbx")
                            self._export_duplicate_set(
                                export_path=export_path,
                                source_objs=[src_obj],
                                origin_mode=ORIGIN_MODE_ROOTS_TO_ZERO,
                            )
                            exported_paths.append(export_path)
                else:
                    # Case A: export all selected objects together as one FBX.
                    export_name = anchor.name if anchor in selected_objects else "Export"
                    export_path = os.path.join(export_folder, f"{export_name}.fbx")
                    self._export_duplicate_set(
                        export_path=export_path,
                        source_objs=selected_objects,
                        origin_mode=ORIGIN_MODE_PRESERVE,
                    )
                    exported_paths.append(export_path)

        except Exception as e:
            self.report({'ERROR'}, f"FBX export failed: {e}")
            return {'CANCELLED'}

        # Report success
        plural = "FBXs" if len(exported_paths) > 1 else "FBX"
        self.report({'INFO'}, f"Exported {len(exported_paths)} {plural} to: {export_folder}")
        return {'FINISHED'}
