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

## Mode-Aware UI Behavior

- Object-mode only buttons are automatically disabled outside Object Mode.
- **Floor Pivot** remains available in Object Mode and Edit Mesh Mode.
- **Reload Images** stays available in all modes.
