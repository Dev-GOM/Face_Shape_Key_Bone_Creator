import bpy
import mathutils
import random
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty, FloatProperty, StringProperty

class ShapeKeyManager:
    def invert_shape_key(self, mesh_obj, shape_key_name):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key_block = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]

            for i in range(len(mesh_obj.data.vertices)):
                shape_key_block.data[i].co = basis.data[i].co - (shape_key_block.data[i].co - basis.data[i].co)

            return True, "Shape key inverted successfully"
        except Exception as e:
            return False, f"Error inverting shape key: {str(e)}"

    def mirror_shape_key(self, mesh_obj, shape_key_name, axis='X'):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key_block = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            axis_index = {'X': 0, 'Y': 1, 'Z': 2}[axis]
            vertex_map = {}
            vertices = mesh_obj.data.vertices
            
            # 대칭점 찾기
            for v1 in vertices:
                if v1.index in vertex_map:
                    continue
                    
                pos1 = v1.co
                for v2 in vertices:
                    if v2.index == v1.index or v2.index in vertex_map.values():
                        continue
                        
                    pos2 = v2.co
                    if all(abs(pos1[j] - (-pos2[j] if j == axis_index else pos2[j])) < 0.0001 for j in range(3)):
                        vertex_map[v1.index] = v2.index
                        vertex_map[v2.index] = v1.index
                        break
            
            # 변형 적용
            for v_idx, mirror_idx in vertex_map.items():
                diff = shape_key_block.data[v_idx].co - basis.data[v_idx].co
                mirror_diff = diff.copy()
                mirror_diff[axis_index] *= -1
                shape_key_block.data[mirror_idx].co = basis.data[mirror_idx].co + mirror_diff
            
            return True, f"Shape key mirrored successfully along {axis} axis"
        except Exception as e:
            return False, f"Error mirroring shape key: {str(e)}"

    def normalize_shape_key(self, mesh_obj, shape_key_name):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key_block = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            max_deformation = max((shape_key_block.data[i].co - basis.data[i].co).length 
                                for i in range(len(mesh_obj.data.vertices)))
            
            if max_deformation == 0:
                return False, "No deformation found in shape key"
            
            for i in range(len(mesh_obj.data.vertices)):
                diff = shape_key_block.data[i].co - basis.data[i].co
                if diff.length > 0:
                    normalized_diff = diff * (1.0 / max_deformation)
                    shape_key_block.data[i].co = basis.data[i].co + normalized_diff
            
            return True, "Shape key normalized successfully"
        except Exception as e:
            return False, f"Error normalizing shape key: {str(e)}"
        
    def merge_shape_keys(self, mesh_obj, shape_keys_to_merge, new_name="Merged"):
        try:
            shape_keys = mesh_obj.data.shape_keys
            basis = shape_keys.key_blocks["Basis"]
            
            new_key = mesh_obj.shape_key_add(name=new_name)
            
            for i in range(len(mesh_obj.data.vertices)):
                basis_co = basis.data[i].co
                combined_diff = mathutils.Vector((0, 0, 0))
                
                for key_name in shape_keys_to_merge:
                    if key_name in shape_keys.key_blocks:
                        key_block = shape_keys.key_blocks[key_name]
                        diff = key_block.data[i].co - basis_co
                        combined_diff += diff
                
                new_key.data[i].co = basis_co + combined_diff
            
            return True, f"Successfully merged {len(shape_keys_to_merge)} shape keys"
        except Exception as e:
            return False, f"Error merging shape keys: {str(e)}"

    def split_shape_key(self, mesh_obj, shape_key_name, threshold=0.5):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            high_key = mesh_obj.shape_key_add(name=f"{shape_key_name}_High")
            low_key = mesh_obj.shape_key_add(name=f"{shape_key_name}_Low")
            
            max_deform = max((shape_key.data[i].co - basis.data[i].co).length 
                           for i in range(len(mesh_obj.data.vertices)))
            
            for i in range(len(mesh_obj.data.vertices)):
                current_co = shape_key.data[i].co
                basis_co = basis.data[i].co
                diff = current_co - basis_co
                deform_ratio = diff.length / max_deform if max_deform > 0 else 0
                
                if deform_ratio > threshold:
                    high_key.data[i].co = current_co
                    low_key.data[i].co = basis_co
                else:
                    high_key.data[i].co = basis_co
                    low_key.data[i].co = current_co
            
            return True, f"Shape key split into {high_key.name} and {low_key.name}"
        except Exception as e:
            return False, f"Error splitting shape key: {str(e)}"

    def smooth_shape_key(self, mesh_obj, shape_key_name, strength=0.5):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            vertex_connections = {}
            for edge in mesh_obj.data.edges:
                v1, v2 = edge.vertices
                if v1 not in vertex_connections:
                    vertex_connections[v1] = []
                if v2 not in vertex_connections:
                    vertex_connections[v2] = []
                vertex_connections[v1].append(v2)
                vertex_connections[v2].append(v1)
            
            new_coordinates = {}
            
            for i in range(len(mesh_obj.data.vertices)):
                if i not in vertex_connections:
                    continue
                
                current_co = shape_key.data[i].co
                basis_co = basis.data[i].co
                neighbors = vertex_connections[i]
                
                if not neighbors:
                    continue
                
                avg_diff = sum((shape_key.data[n].co - basis.data[n].co) 
                             for n in neighbors) / len(neighbors)
                current_diff = current_co - basis_co
                interpolated_diff = current_diff.lerp(avg_diff, strength)
                new_coordinates[i] = basis_co + interpolated_diff
            
            for idx, co in new_coordinates.items():
                shape_key.data[idx].co = co
            
            return True, f"Shape key smoothed with strength {strength}"
        except Exception as e:
            return False, f"Error smoothing shape key: {str(e)}"

    def transfer_shape_key(self, source_mesh, target_mesh, shape_key_name):
        try:
            if not source_mesh.data.shape_keys or shape_key_name not in source_mesh.data.shape_keys.key_blocks:
                return False, "Source shape key not found"
            
            source_key = source_mesh.data.shape_keys.key_blocks[shape_key_name]
            source_basis = source_mesh.data.shape_keys.key_blocks["Basis"]
            
            if not target_mesh.data.shape_keys:
                target_mesh.shape_key_add(name="Basis")
            target_key = target_mesh.shape_key_add(name=shape_key_name)
            
            # KDTree 생성
            size = len(source_mesh.data.vertices)
            kd = mathutils.kdtree.KDTree(size)
            for i, v in enumerate(source_mesh.data.vertices):
                kd.insert(v.co, i)
            kd.balance()
            
            for i, v in enumerate(target_mesh.data.vertices):
                co, index, dist = kd.find(v.co)
                if index is not None:
                    source_diff = source_key.data[index].co - source_basis.data[index].co
                    target_key.data[i].co = v.co + source_diff
            
            return True, f"Shape key transferred to {target_mesh.name}"
        except Exception as e:
            return False, f"Error transferring shape key: {str(e)}"
        
    def clean_shape_key(self, mesh_obj, shape_key_name, threshold=0.0001):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            cleaned_count = 0
            for i in range(len(mesh_obj.data.vertices)):
                diff = shape_key.data[i].co - basis.data[i].co
                if diff.length <= threshold:
                    shape_key.data[i].co = basis.data[i].co
                    cleaned_count += 1
            
            return True, f"Cleaned {cleaned_count} vertices in shape key"
        except Exception as e:
            return False, f"Error cleaning shape key: {str(e)}"

    def symmetrize_shape_key(self, mesh_obj, shape_key_name, direction='POSITIVE_X'):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            axis = direction[-1].lower()
            is_positive = direction.startswith('POSITIVE')
            axis_index = {'x': 0, 'y': 1, 'z': 2}[axis]
            
            vertex_map = {}
            vertices = mesh_obj.data.vertices
            
            # 대칭점 찾기
            for v1 in vertices:
                if v1.index in vertex_map:
                    continue
                
                pos1 = v1.co
                for v2 in vertices:
                    if v2.index == v1.index or v2.index in vertex_map.values():
                        continue
                    
                    pos2 = v2.co
                    if all(abs(pos1[j] - (-pos2[j] if j == axis_index else pos2[j])) < 0.0001 for j in range(3)):
                        vertex_map[v1.index] = v2.index
                        vertex_map[v2.index] = v1.index
                        break
            
            # 변형 대칭화
            for v in vertices:
                if v.index in vertex_map:
                    mirror_idx = vertex_map[v.index]
                    
                    if is_positive == (v.co[axis_index] > 0):
                        source_idx = v.index
                        target_idx = mirror_idx
                    else:
                        source_idx = mirror_idx
                        target_idx = v.index
                    
                    source_diff = shape_key.data[source_idx].co - basis.data[source_idx].co
                    mirror_diff = source_diff.copy()
                    mirror_diff[axis_index] *= -1
                    shape_key.data[target_idx].co = basis.data[target_idx].co + mirror_diff
            
            return True, f"Shape key symmetrized along {direction}"
        except Exception as e:
            return False, f"Error symmetrizing shape key: {str(e)}"

    def randomize_shape_key(self, mesh_obj, shape_key_name, strength=0.1):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            for i in range(len(mesh_obj.data.vertices)):
                random_vector = mathutils.Vector((
                    (random.random() * 2 - 1) * strength,
                    (random.random() * 2 - 1) * strength,
                    (random.random() * 2 - 1) * strength
                ))
                shape_key.data[i].co = shape_key.data[i].co + random_vector
            
            return True, f"Random variation added with strength {strength}"
        except Exception as e:
            return False, f"Error randomizing shape key: {str(e)}"

    def flip_shape_key(self, mesh_obj, shape_key_name, axes=['X']):
        try:
            shape_keys = mesh_obj.data.shape_keys
            shape_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            axis_indices = {'X': 0, 'Y': 1, 'Z': 2}
            flip_axes = [axis_indices[axis] for axis in axes]
            
            for i in range(len(mesh_obj.data.vertices)):
                diff = shape_key.data[i].co - basis.data[i].co
                for axis in flip_axes:
                    diff[axis] *= -1
                shape_key.data[i].co = basis.data[i].co + diff
            
            return True, f"Shape key flipped along {', '.join(axes)} axes"
        except Exception as e:
            return False, f"Error flipping shape key: {str(e)}"

    def duplicate_with_mirror(self, mesh_obj, shape_key_name, axis='X'):
        try:
            shape_keys = mesh_obj.data.shape_keys
            source_key = shape_keys.key_blocks[shape_key_name]
            basis = shape_keys.key_blocks["Basis"]
            
            new_name = f"{shape_key_name}_mirror_{axis}"
            new_key = mesh_obj.shape_key_add(name=new_name)
            
            axis_index = {'X': 0, 'Y': 1, 'Z': 2}[axis]
            
            # vertex 매핑 생성 및 대칭 복사
            vertex_map = {}
            for v1 in mesh_obj.data.vertices:
                if v1.index in vertex_map:
                    continue
                
                pos1 = v1.co
                for v2 in mesh_obj.data.vertices:
                    if v2.index == v1.index or v2.index in vertex_map.values():
                        continue
                    
                    pos2 = v2.co
                    if all(abs(pos1[j] - (-pos2[j] if j == axis_index else pos2[j])) < 0.0001 for j in range(3)):
                        vertex_map[v1.index] = v2.index
                        vertex_map[v2.index] = v1.index
                        break
            
            for i in range(len(mesh_obj.data.vertices)):
                if i in vertex_map:
                    mirror_idx = vertex_map[i]
                    source_diff = source_key.data[i].co - basis.data[i].co
                    mirror_diff = source_diff.copy()
                    mirror_diff[axis_index] *= -1
                    new_key.data[mirror_idx].co = basis.data[mirror_idx].co + mirror_diff
                else:
                    new_key.data[i].co = basis.data[i].co
            
            return True, f"Created mirrored shape key: {new_name}"
        except Exception as e:
            return False, f"Error duplicating shape key: {str(e)}"

class OBJECT_OT_shape_key_adjustments(Operator):
    """Operator to perform shape key adjustments"""    
    bl_idname = "object.shape_key_adjustments"
    bl_label = "Shape Key Adjustments"
    bl_options = {'REGISTER', 'UNDO'}

    target_mesh: EnumProperty(
        name="Target Mesh",
        description="Select mesh with shape keys",
        items=lambda self, context: [
            (obj.name, obj.name, "")
            for obj in context.scene.objects
            if obj.type == 'MESH' and obj.data.shape_keys
        ]
    ) # type: ignore

    shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to adjust",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, None).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else []
    ) # type: ignore

    action: EnumProperty(
        name="Action",
        description="Select action for the shape key",
        items=[
            ('INVERT', "Invert", "Invert the shape key value"),
            ('MIRROR', "Mirror", "Mirror the shape key along an axis"),
            ('NORMALIZE', "Normalize", "Normalize shape key deformation"),
            ('MERGE', "Merge", "Merge multiple shape keys"),
            ('SPLIT', "Split", "Split shape key by deformation amount"),
            ('SMOOTH', "Smooth", "Smooth shape key deformation"),
            ('TRANSFER', "Transfer", "Transfer to another mesh"),
            ('CLEAN', "Clean", "Remove tiny deformations"),
            ('SYMMETRIZE', "Symmetrize", "Make perfectly symmetrical"),
            ('RANDOMIZE', "Randomize", "Add random variation"),
            ('FLIP', "Flip", "Flip along axes"),
            ('DUPLICATE_MIRROR', "Duplicate Mirror", "Create mirrored copy")
        ]
    ) # type: ignore

    # Mirror options
    mirror_axis: EnumProperty(
        name="Mirror Axis",
        description="Axis to mirror along",
        items=[
            ('X', "X Axis", "Mirror along X axis"),
            ('Y', "Y Axis", "Mirror along Y axis"),
            ('Z', "Z Axis", "Mirror along Z axis")
        ],
        default='X'
    ) # type: ignore

    # Merge options
    shape_keys_to_merge: EnumProperty(
        name="Shape Keys to Merge",
        description="Select shape keys to merge",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, None).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else [],
        options={'ENUM_FLAG'}
    ) # type: ignore

    merged_name: StringProperty(
        name="Merged Name",
        description="Name for the merged shape key",
        default="Merged"
    ) # type: ignore

    # Split options
    split_threshold: FloatProperty(
        name="Split Threshold",
        description="Threshold for splitting shape key",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    ) # type: ignore

    # Smooth options
    smooth_strength: FloatProperty(
        name="Smooth Strength",
        description="Strength of smoothing effect",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    ) # type: ignore

    # Transfer options
    target_transfer_mesh: EnumProperty(
        name="Target Mesh",
        description="Select target mesh for transfer",
        items=lambda self, context: [
            (obj.name, obj.name, "")
            for obj in context.scene.objects
            if obj.type == 'MESH' and obj != context.object
        ]
    ) # type: ignore

    # Clean options
    clean_threshold: FloatProperty(
        name="Clean Threshold",
        description="Minimum deformation threshold",
        default=0.0001,
        min=0.0,
        max=1.0,
        precision=6
    ) # type: ignore

    # Symmetrize options
    symmetrize_direction: EnumProperty(
        name="Symmetrize Direction",
        description="Direction for symmetrization",
        items=[
            ('POSITIVE_X', "X+ to X-", "Positive X to negative X"),
            ('NEGATIVE_X', "X- to X+", "Negative X to positive X"),
            ('POSITIVE_Y', "Y+ to Y-", "Positive Y to negative Y"),
            ('NEGATIVE_Y', "Y- to Y+", "Negative Y to positive Y"),
            ('POSITIVE_Z', "Z+ to Z-", "Positive Z to negative Z"),
            ('NEGATIVE_Z', "Z- to Z+", "Negative Z to positive Z")
        ],
        default='POSITIVE_X'
    ) # type: ignore

    # Randomize options
    random_strength: FloatProperty(
        name="Random Strength",
        description="Strength of random variation",
        default=0.1,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    ) # type: ignore

    # Flip options
    flip_axes: EnumProperty(
        name="Flip Axes",
        description="Select axes to flip",
        items=[
            ('X', "X", "Flip X axis"),
            ('Y', "Y", "Flip Y axis"),
            ('Z', "Z", "Flip Z axis")
        ],
        options={'ENUM_FLAG'},
        default={'X'}
    ) # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        # Shape Key Selection
        box = layout.box()
        box.label(text="Shape Key Selection:", icon='SHAPEKEY_DATA')
        box.prop(self, "target_mesh")
        if self.target_mesh:
            box.prop(self, "shape_key")
        
        # Action Selection
        box = layout.box()
        box.label(text="Action:", icon='MODIFIER')
        box.prop(self, "action")
        
        # Action specific options
        if self.action == 'MIRROR':
            box = layout.box()
            box.label(text="Mirror Options:", icon='MOD_MIRROR')
            box.prop(self, "mirror_axis")
        
        elif self.action == 'MERGE':
            box = layout.box()
            box.label(text="Merge Options:", icon='AUTOMERGE_ON')
            box.prop(self, "shape_keys_to_merge", text="")
            box.prop(self, "merged_name")
        
        elif self.action == 'SPLIT':
            box = layout.box()
            box.label(text="Split Options:", icon='MOD_EDGESPLIT')
            box.prop(self, "split_threshold", slider=True)
        
        elif self.action == 'SMOOTH':
            box = layout.box()
            box.label(text="Smooth Options:", icon='MOD_SMOOTH')
            box.prop(self, "smooth_strength", slider=True)
        
        elif self.action == 'TRANSFER':
            box = layout.box()
            box.label(text="Transfer Options:", icon='TRANSFER_DATA')
            box.prop(self, "target_transfer_mesh")
        
        elif self.action == 'CLEAN':
            box = layout.box()
            box.label(text="Clean Options:", icon='BRUSH_DATA')
            box.prop(self, "clean_threshold", slider=True)
        
        elif self.action == 'SYMMETRIZE':
            box = layout.box()
            box.label(text="Symmetrize Options:", icon='MOD_MIRROR')
            box.prop(self, "symmetrize_direction")
        
        elif self.action == 'RANDOMIZE':
            box = layout.box()
            box.label(text="Randomize Options:", icon='MOD_NOISE')
            box.prop(self, "random_strength", slider=True)
        
        elif self.action == 'FLIP':
            box = layout.box()
            box.label(text="Flip Options:", icon='ARROW_LEFTRIGHT')
            box.prop(self, "flip_axes")
        
        elif self.action == 'DUPLICATE_MIRROR':
            box = layout.box()
            box.label(text="Duplicate Mirror Options:", icon='MOD_MIRROR')
            box.prop(self, "mirror_axis")

    def execute(self, context):
        if not self.target_mesh or not self.shape_key:
            self.report({'ERROR'}, "Please select both mesh and shape key")
            return {'CANCELLED'}

        mesh_obj = bpy.data.objects[self.target_mesh]
        manager = ShapeKeyManager()

        try:
            if self.action == 'INVERT':
                success, message = manager.invert_shape_key(mesh_obj, self.shape_key)
            
            elif self.action == 'MIRROR':
                success, message = manager.mirror_shape_key(
                    mesh_obj, 
                    self.shape_key, 
                    self.mirror_axis
                )
            
            elif self.action == 'NORMALIZE':
                success, message = manager.normalize_shape_key(mesh_obj, self.shape_key)
            
            elif self.action == 'MERGE':
                if not self.shape_keys_to_merge:
                    self.report({'ERROR'}, "Please select shape keys to merge")
                    return {'CANCELLED'}
                success, message = manager.merge_shape_keys(
                    mesh_obj,
                    list(self.shape_keys_to_merge),
                    self.merged_name
                )
            
            elif self.action == 'SPLIT':
                success, message = manager.split_shape_key(
                    mesh_obj,
                    self.shape_key,
                    self.split_threshold
                )
            
            elif self.action == 'SMOOTH':
                success, message = manager.smooth_shape_key(
                    mesh_obj,
                    self.shape_key,
                    self.smooth_strength
                )
            
            elif self.action == 'TRANSFER':
                if not self.target_transfer_mesh:
                    self.report({'ERROR'}, "Please select target mesh")
                    return {'CANCELLED'}
                target_obj = bpy.data.objects[self.target_transfer_mesh]
                success, message = manager.transfer_shape_key(
                    mesh_obj,
                    target_obj,
                    self.shape_key
                )
            
            elif self.action == 'CLEAN':
                success, message = manager.clean_shape_key(
                    mesh_obj,
                    self.shape_key,
                    self.clean_threshold
                )
            
            elif self.action == 'SYMMETRIZE':
                success, message = manager.symmetrize_shape_key(
                    mesh_obj,
                    self.shape_key,
                    self.symmetrize_direction
                )
            
            elif self.action == 'RANDOMIZE':
                success, message = manager.randomize_shape_key(
                    mesh_obj,
                    self.shape_key,
                    self.random_strength
                )
            
            elif self.action == 'FLIP':
                if not self.flip_axes:
                    self.report({'ERROR'}, "Please select at least one axis")
                    return {'CANCELLED'}
                success, message = manager.flip_shape_key(
                    mesh_obj,
                    self.shape_key,
                    list(self.flip_axes)
                )
            
            elif self.action == 'DUPLICATE_MIRROR':
                success, message = manager.duplicate_with_mirror(
                    mesh_obj,
                    self.shape_key,
                    self.mirror_axis
                )
            
            else:
                success, message = False, "Unknown action"

            if success:
                self.report({'INFO'}, message)
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Operation failed: {str(e)}")
            return {'CANCELLED'}

classes = (
    OBJECT_OT_shape_key_adjustments,
)
