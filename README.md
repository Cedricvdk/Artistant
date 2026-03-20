**Game Art assistant for the gamedevver**

Functionalities:

**Smart Group**
Creates an empty (box shape) as a bounding box over the selected objects and parents those objects to that empty, for a Maya-esque grouping functionality.

**Export Unity Asset**
exports the selected objects as an FBX with the correct orientation for unity (when importing into unity, check "Bake Axis Conversion", no way of adding that to the fbx metadata for the moment)
Name of the FBX file is the active object.
The folder has to be absolute for the moment, **relative paths won't work.**
**Individual** checkbox to export each selected object as a seperate fbx file, with the name of the object as the name of the fbx file.

**Reload Images**
Quickly reload all images in the Blender project for a quicker texturing workflow from Substance, 3Dcoat or similar.
