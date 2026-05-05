import os

import bpy
from bpy.types import Operator
from ..common.context_guard import preserve_selection_and_active


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
            use_space_transform=False,
            bake_space_transform=False,
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

    def _prepare_duplicates_for_export(self, dups, source_roots):
        """Rotate duplicate roots for Unity, apply rotation, and preserve root naming."""
        dup_roots = _root_objects(dups)
        if not dup_roots:
            dup_roots = list(dups)

        bpy.ops.object.select_all(action='DESELECT')
        for root in dup_roots:
            root.rotation_mode = 'XYZ'
            root.rotation_euler.x += -1.5707963267948966
            root.select_set(True)

        bpy.context.view_layer.objects.active = dup_roots[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        # Keep exported root naming stable for import pipelines.
        if len(source_roots) == 1 and len(dup_roots) == 1:
            dup_roots[0].name = source_roots[0].name

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

    def _export_duplicate_set(self, *, export_path: str, source_objs):
        """Execute the core export pipeline: duplicate → rotate/apply → export.
        
        Args:
            export_path: Full file path for the output FBX
            source_objs: List of objects to duplicate and export
        """
        # Step 1: Duplicate the source objects into a temporary collection
        dups, temp_coll = self._duplicate_objects(source_objs)
        try:
            source_roots = _root_objects(source_objs)
            if not source_roots:
                source_roots = list(source_objs)

            # Step 2: Rotate duplicate root(s), apply rotation, and restore root naming
            self._prepare_duplicates_for_export(dups, source_roots)

            # Step 3: Select duplicates and prepare for export
            bpy.ops.object.select_all(action='DESELECT')
            for d in dups:
                d.select_set(True)
            bpy.context.view_layer.objects.active = dups[0]

            # Step 4: Call the FBX exporter
            self._export_selected_duplicates(export_path)
        finally:
            # Clean up: delete duplicates and temporary collection
            self._cleanup_temp(dups, temp_coll)

    def execute(self, context):
        """Main operator entry point. Exports selected objects as FBX.
        
        Supports three modes:
        - Batch: All selected objects exported to one FBX
        - Individual (all selected): each selected object exported alone (no children)
        - Individual (only orphans): each orphan exported with its full hierarchy
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
                            )
                            exported_paths.append(export_path)
                else:
                    # Case A: export all selected objects together as one FBX.
                    export_name = anchor.name if anchor in selected_objects else "Export"
                    export_path = os.path.join(export_folder, f"{export_name}.fbx")
                    self._export_duplicate_set(
                        export_path=export_path,
                        source_objs=selected_objects,
                    )
                    exported_paths.append(export_path)

        except Exception as e:
            self.report({'ERROR'}, f"FBX export failed: {e}")
            return {'CANCELLED'}

        # Report success
        plural = "FBXs" if len(exported_paths) > 1 else "FBX"
        self.report({'INFO'}, f"Exported {len(exported_paths)} {plural} to: {export_folder}")
        return {'FINISHED'}
