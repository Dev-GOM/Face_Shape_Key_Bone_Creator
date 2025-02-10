import bpy
from . import utils
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty

class ShapeKeyCommonProperties:    
    def update_connect_driver(self, context):
        try:
            if self.connect_driver and self.target_shape_key:
                new_name = f"shape_key_ctrl_{self.target_shape_key}"
                self.suggested_name = new_name
                self.bone_name = new_name
            else:
                self.bone_name = "shape_key_ctrl"
                self.suggested_name = "shape_key_ctrl"
        except Exception as e:
            print(f"Error updating connect driver: {str(e)}")

    def update_mesh(self, context):
        try:
            if self.target_mesh:
                mesh_obj = bpy.data.objects.get(self.target_mesh)
                if mesh_obj and mesh_obj.data.shape_keys:
                    shape_keys = mesh_obj.data.shape_keys.key_blocks
                    if len(shape_keys) > 1:
                        self.target_shape_key = shape_keys[1].name
                        if self.connect_driver:
                            new_name = f"shape_key_ctrl_{shape_keys[1].name}"
                            self.suggested_name = new_name
                            self.bone_name = new_name
                        else:
                            self.bone_name = "shape_key_ctrl"
                            self.suggested_name = "shape_key_ctrl"
        except Exception as e:
            print(f"Error updating mesh selection: {str(e)}")

    def update_shape_key(self, context):
        try:
            if self.connect_driver and self.target_shape_key:
                new_name = f"shape_key_ctrl_{self.target_shape_key}"
                self.suggested_name = new_name
                self.bone_name = new_name
                for area in context.screen.areas:
                    area.tag_redraw()
        except Exception as e:
            print(f"Error updating shape key selection: {str(e)}")

    target_mesh: EnumProperty(
        name="Target Mesh",
        description="Select mesh with shape keys",
        items=utils.get_mesh_items,
        update=update_mesh
    ) # type: ignore

    target_shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to connect",
        items=utils.get_shape_key_items,
        update=update_shape_key
    ) # type: ignore
    
    connect_driver: BoolProperty(
        name="Connect Shape Key Driver",
        description="Connect to shape key after creating bone",
        default=True,
        update=update_connect_driver
    ) # type: ignore
    
    selected_bones: StringProperty(
        name="Selected Bones",
        description="List of selected bones",
        default=""
    ) # type: ignore

    selected_collections: StringProperty(
        name="Collections to Delete",
        description="List of widget collections",
        default=""
    ) # type: ignore

    selected_drivers: StringProperty(
        name="Drivers to Delete",
        description="List of drivers",
        default=""
    ) # type: ignore

    show_confirmation: BoolProperty(
        name="Show Confirmation",
        description="Show confirmation dialog",
        default=False
    ) # type: ignore

    delete_collection: BoolProperty(
        name="Delete Widget Collection",
        description="Delete associated widget collection",
        default=True
    ) # type: ignore

    delete_drivers: BoolProperty(
        name="Delete Shape Key Drivers",
        description="Delete associated shape key drivers",
        default=True
    ) # type: ignore

    bone_name: StringProperty(
        name="Bone Name",
        description="Name of the new bone (editable)",
        default="shape_key_ctrl"
    ) # type: ignore

    suggested_name: StringProperty(
        name="Suggested Name",
        description="Suggested name based on shape key",
        default=""
    ) # type: ignore

    transform_type: EnumProperty(
        name="Transform Type",
        description="Type of transform to control the shape key",
        items=utils.TRANSFORM_ITEMS,
        default='LOC_X'
    ) # type: ignore

    multiplier: FloatProperty(
        name="Influence",
        description="Driver influence strength multiplier",
        default=17,
        min=0.0,
        max=100.0,
        step=1.0,
        precision=1
    ) # type: ignore