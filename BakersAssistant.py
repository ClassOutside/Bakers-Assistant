import bpy
import os

bl_info = {
    "name": "Baker's Assistant",
    "author": "ClassOutside",
    "version": (1, 0),
    "blender": (4, 1, 1),
    "description": "Assists with baking diffuse and normal maps in Blender",
}

class BakersAssistant(bpy.types.Operator):
    bl_idname = "object.simple_operator"
    bl_label = "Baker's Assistant"

    def object_items(self, context):
        return [(obj.name, obj.name, "") for obj in bpy.data.objects]

    source: bpy.props.EnumProperty(name="Source", items=object_items)
    destination: bpy.props.EnumProperty(name="Destination", items=object_items)
    cage: bpy.props.EnumProperty(name="Cage", items=object_items)


    diffuse: bpy.props.BoolProperty(
        name="Diffuse",
        default=True
    )
    normal: bpy.props.BoolProperty(
        name="Normal",
        default=True
    )
    resolution: bpy.props.EnumProperty(
        name="Resolution",
        items=[
            ('1024', '1024', 'Use 1024 resolution'),
            ('2048', '2048', 'Use 2048 resolution'),
            ('4096', '4096', 'Use 4096 resolution'),
            ('8192', '8192', 'Use 8192 resolution')
        ],
        default='4096'
    )

    def create_image_texture(self, nodes, resolution, name):
        image_texture_node = nodes.new('ShaderNodeTexImage')
        image_texture_node.image = bpy.data.images.new(name, width=int(resolution), height=int(resolution))
        return image_texture_node

    def plug_into_base_color(self, mat, image_texture_node, principled_bsdf_node):
        mat.node_tree.links.new(image_texture_node.outputs['Color'], principled_bsdf_node.inputs['Base Color'])

    # Check if a diffuse image is already connected
    # If nothing is connected, create a new image texture and plug it in to base color.
    def prepare_diffuse_image(self, destination_obj):
        if destination_obj.data.materials:
            mat = destination_obj.data.materials[0]
            nodes = mat.node_tree.nodes
            principled_bsdf_node = nodes.get('Principled BSDF')

            if principled_bsdf_node:
                if principled_bsdf_node.inputs['Base Color'].links:
                    from_node = principled_bsdf_node.inputs['Base Color'].links[0].from_node

                    if isinstance(from_node, bpy.types.ShaderNodeTexImage):
                        print("Image texture is already plugged into the base color.")
                        return from_node
                    else:
                        image_texture_node = self.create_image_texture(nodes, self.resolution, 'gen_diffuse')
                        self.plug_into_base_color(mat, image_texture_node, principled_bsdf_node)
                        return image_texture_node
                else:
                    image_texture_node = self.create_image_texture(nodes, self.resolution, 'gen_diffuse')
                    self.plug_into_base_color(mat, image_texture_node, principled_bsdf_node)
                    return image_texture_node

    # Delete anything connected to the normal input
    # Create a new image texture, and normal map, and connect to normal input
    def prepare_normal_image(self, destination_obj):
        if destination_obj.data.materials:
            mat = destination_obj.data.materials[0]
            nodes = mat.node_tree.nodes
            principled_bsdf_node = nodes.get('Principled BSDF')

            if principled_bsdf_node:
                if principled_bsdf_node.inputs['Normal'].links:
                    from_node = principled_bsdf_node.inputs['Normal'].links[0].from_node

                    nodes_to_delete = [from_node]
                    while nodes_to_delete:
                        node = nodes_to_delete.pop()
                        nodes_to_delete.extend(link.from_node for socket in node.inputs for link in socket.links)
                        nodes.remove(node)

                image_texture_node = self.create_image_texture(nodes, self.resolution, 'gen_normal')
                image_texture_node.image.colorspace_settings.name = 'Non-Color'

                normal_map_node = self.create_normal_map(mat, nodes, image_texture_node)

                mat.node_tree.links.new(normal_map_node.outputs['Normal'], principled_bsdf_node.inputs['Normal'])
                return image_texture_node


    def create_normal_map(self, mat, nodes, image_texture_node):
        normal_map_node = nodes.new('ShaderNodeNormalMap')

        mat.node_tree.links.new(image_texture_node.outputs['Color'], normal_map_node.inputs['Color'])

        return normal_map_node

    # Configure baking settings
    # set contribution to only color, selected to active to true, add the cage, and bake
    def bake_diffuse(self, context, image_texture_node):
        image_texture_node.select = True
        bpy.context.object.active_material.node_tree.nodes.active = image_texture_node
        bpy.context.scene.cycles.bake_type = 'DIFFUSE'

        bpy.context.scene.render.bake.use_pass_color = True
        bpy.context.scene.render.bake.use_pass_direct = False
        bpy.context.scene.render.bake.use_pass_indirect = False

        bpy.context.scene.render.bake.use_selected_to_active = True

        bpy.context.scene.render.bake.use_cage = True

        bpy.context.scene.render.bake.cage_object = bpy.data.objects[self.cage]

        bpy.context.view_layer.objects.active = bpy.data.objects[self.source]
        bpy.data.objects[self.source].select_set(True)

        bpy.context.view_layer.objects.active = bpy.data.objects[self.destination]
        bpy.data.objects[self.destination].select_set(True)

        bpy.ops.object.bake(type='DIFFUSE')

    # Configure baking settings
    # set type to normal, selected to active, add the cage, and bake.
    def bake_normal(self, context, image_texture_node):
        image_texture_node.select = True
        bpy.context.object.active_material.node_tree.nodes.active = image_texture_node
        bpy.context.scene.cycles.bake_type = 'NORMAL'

        bpy.context.scene.render.bake.use_selected_to_active = True

        bpy.context.scene.render.bake.use_cage = True

        bpy.context.scene.render.bake.cage_object = bpy.data.objects[self.cage]

        bpy.context.view_layer.objects.active = bpy.data.objects[self.source]
        bpy.data.objects[self.source].select_set(True)

        bpy.context.view_layer.objects.active = bpy.data.objects[self.destination]
        bpy.data.objects[self.destination].select_set(True)

        bpy.ops.object.bake(type='NORMAL')
        
    def unhide_objects(self):
        bpy.data.objects[self.source].hide_set(False)
        bpy.data.objects[self.destination].hide_set(False)
        bpy.data.objects[self.cage].hide_set(False)

    def hide_objects(self):
        bpy.data.objects[self.source].hide_set(True)
        bpy.data.objects[self.cage].hide_set(True)
        
    # Save diffuse and normal images to file
    def save_images(self, diffuse_image_texture_node, normal_image_texture_node):
        blend_file_directory = bpy.path.abspath('//')
        materials_folder = os.path.join(blend_file_directory, 'materials')
        
        if not os.path.exists(materials_folder):
            os.makedirs(materials_folder)
        
        # Save diffuse image
        if diffuse_image_texture_node:
            diffuse_image = diffuse_image_texture_node.image
            if diffuse_image:
                diffuse_image.file_format = 'PNG'
                diffuse_image.filepath_raw = os.path.join(materials_folder, 'diffuse.png')
                diffuse_image.save()
        
        # Save normal image
        if normal_image_texture_node:
            normal_image = normal_image_texture_node.image
            if normal_image:
                normal_image.file_format = 'PNG'
                normal_image.filepath_raw = os.path.join(materials_folder, 'normal.png')
                normal_image.save()

    def execute(self, context):
        print("Source: %s, Destination: %s, Cage: %s, Diffuse: %s, Normal: %s, Resolution: %s" % (
            self.source, self.destination, self.cage, self.diffuse, self.normal, self.resolution))

        self.unhide_objects()
        
        destination_obj = bpy.data.objects[self.destination]

        # Prepare the diffuse image and bake it
        if self.diffuse:
            diffuse_image_texture_node = self.prepare_diffuse_image(destination_obj)
            self.bake_diffuse(context, diffuse_image_texture_node)

        # Prepare the normal image and bake it
        if self.normal:
            normal_image_texture_node = self.prepare_normal_image(destination_obj)
            self.bake_normal(context, normal_image_texture_node)
            
        # Hide objects at the end of execution
        self.hide_objects()
        
        # Save images after baking
        self.save_images(diffuse_image_texture_node, normal_image_texture_node)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "source")
        layout.prop(self, "destination")
        layout.prop(self, "cage")
        layout.prop(self, "diffuse")
        layout.prop(self, "normal")
        layout.prop(self, "resolution")

def draw_func(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_DEFAULT'
    layout.operator("object.simple_operator", text="Start Baking")

def register():
    bpy.utils.register_class(BakersAssistant)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_func)

def unregister():
    bpy.utils.unregister_class(BakersAssistant)
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_func)

if __name__ == "__main__":
    register()


