# Bakers-Assistant
Blender add-on  to assist with baking and saving diffuse and normal maps using a cage.


# Use
1. Install the add-on in Blender
2. Save your Blender file
3. Create your destination mesh
4. Unwrap the UVs for your destination mesh
5. Create a new material for the destination mesh
6. Duplicate the destination mesh
7. Inflate the destination mesh to be larger than the source mesh
8. Right click the destination mesh and select the "Start Baking" option
9. In the new pop-up window choose your source, destination, and cage meshes
10. Choose the output resolution of the desired image textures.
11. Choose whether to bake just diffuse, normal, or both.
12. Click the button and start baking.

After a moment the textures should be baked, and the source and cage meshes will be hidden in the viewport.
The materials should be saved to a 'materials' folder in the same directory as your blend file.
