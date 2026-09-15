# Artistant

Small Blender helper add-on for common game art tasks.

## Panel Location

- 3D Viewport -> N-panel -> Artistant

## Current Features

### Tools

- **Smart Group**
Creates a cube-shaped Empty around the selected objects and parents them to it (Maya-like grouping workflow).

- **Floor Pivot**
Moves each selected mesh object's pivot/origin down to the lowest point of its geometry.
Works from Object Mode and Edit Mesh Mode.

- **Floor Object**
Moves each selected object so its origin is at world Z = 0 (translation only).

- **Select Orphans**
Selects only parentless objects.
If nothing is selected, it selects all parentless objects in the current scene.
If objects are selected, it removes parented objects from the current selection.

- **Visualize Normals**
Adds a quick normals visualization setup for selected editable objects.

### Export Unity Asset

- **Export Folder**
Choose the destination folder for exported FBX files.

- **Export to FBX**
Exports Unity-ready FBX files through a duplicate-based pipeline (original objects are not modified).

- **Individual** toggle
If enabled, exports multiple FBX files.
If disabled, exports all selected objects into one FBX.

- **Only Orphans** toggle (enabled only when Individual is on)
When enabled, exports only selected orphan roots and includes each root's full child hierarchy.
When disabled, exports each selected object as its own FBX (without automatically adding children).

- **Apply Modifiers** and **Embed Textures** options are supported by the export operator.

### Select By Name

- Search by name text
- **Exact** toggle (exact match vs contains)
- Select matching scene objects quickly

### Utilities

- **Reload Images**
Reloads all images in the current Blender file from disk.

### Bake (UV/Image Editor)

- **Panel Location**: UV/Image Editor -> N-panel -> Artistant

- **Bake AO**
Bakes an Ambient Occlusion texture for each selected mesh object. Select object(s) in the 3D Viewport, then press Bake AO from the UV/Image Editor sidebar.
  - Creates one `<ObjectName>_AO` image per object (replacing any previous bake of the same name) at the chosen **Size**, using the chosen **Samples** and **Margin** (padding, in pixels, added around each UV island to avoid seams/bleeding).
  - Adds a dedicated, unconnected Image Texture node to each of the object's materials (creating a default material first if it has none) so the bake target is set up automatically; the node is not wired into the shader.
  - Temporarily switches the render engine to Cycles for the bake and restores the original engine and sample count afterward.
  - Objects without a UV map are skipped with a warning. The baked image is not written to disk automatically — save or pack it manually once you're happy with the result.

- **Preview**
Switches every open 3D Viewport to Solid shading / Texture color / Flat lighting, so the baked texture (via its material's active image node) displays directly on the mesh without needing to wire it into the shader.

## Mode-Aware UI Behavior

- Object-mode only buttons are automatically disabled outside Object Mode.
- **Floor Pivot** remains available in Object Mode and Edit Mesh Mode.
- **Reload Images** stays available in all modes.
