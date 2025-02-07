import bpy
import math
import mathutils
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty

def ensure_template_collection():
    """Ensure template collection exists and create if missing"""
    template_collection = None
    # Check existing collections / 기존 컬렉션 확인
    for collection in bpy.context.scene.collection.children:
        if collection.name == "ShapeKeySliderTemplates":
            template_collection = collection
            break
            
    # Create new collection if not found / 컬렉션이 없으면 새로 생성
    if template_collection is None:
        template_collection = bpy.data.collections.new("ShapeKeySliderTemplates")
        bpy.context.scene.collection.children.link(template_collection)
        template_collection.hide_viewport = True
        template_collection.hide_render = True
    
    return template_collection

def create_templates(template_collection):
    """Create required template objects for shape key controls"""
    # Create slider line template / 슬라이더 라인 템플릿 생성
    if "slider_line_template" not in template_collection.objects:
        bpy.ops.mesh.primitive_plane_add(size=1)
        slider_line = bpy.context.view_layer.objects.active
        slider_line.name = "slider_line_template"
        # 면 삭제하고 엣지만 남기기
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        # 템플릿 컬렉션으로 이동
        for col in slider_line.users_collection:
            col.objects.unlink(slider_line)
        template_collection.objects.link(slider_line)

    # 슬라이더 핸들 템플릿 생성
    if "slider_handle_template" not in template_collection.objects:
        bpy.ops.mesh.primitive_circle_add(radius=0.1, vertices=16)
        handle = bpy.context.view_layer.objects.active
        handle.name = "slider_handle_template"
        # 원을 채우기 위해 면 생성
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.mode_set(mode='OBJECT')
        # 템플릿 컬렉션으로 이동
        for col in handle.users_collection:
            col.objects.unlink(handle)
        template_collection.objects.link(handle)
        
TRANSFORM_ITEMS = [
    ('ROT_X', "Rotation X", "Use X axis rotation"),
    ('ROT_Y', "Rotation Y", "Use Y axis rotation"),
    ('ROT_Z', "Rotation Z", "Use Z axis rotation"),
    ('LOC_X', "Location X", "Use X axis location"),
    ('LOC_Y', "Location Y", "Use Y axis location"),
    ('LOC_Z', "Location Z", "Use Z axis location"),
    ('SCALE_X', "Scale X", "Use X axis scale"),
    ('SCALE_Y', "Scale Y", "Use Y axis scale"),
    ('SCALE_Z', "Scale Z", "Use Z axis scale"),
]

def setup_shape_key_driver(armature, bone_name, shape_key, transform_type, multiplier=4.0):
    """Set up driver for shape key control
    
    Args:
        armature: Armature object containing the control bone
        bone_name: Name of the control bone
        shape_key: Shape key to be controlled
        transform_type: Type of transform to use (LOC/ROT/SCALE)
        multiplier: Driver influence multiplier
    """
    try:
        # 기존 드라이버 제거
        if shape_key.id_data.animation_data:
            for driver in shape_key.id_data.animation_data.drivers:
                if driver.data_path == f'key_blocks["{shape_key.name}"].value':
                    shape_key.id_data.animation_data.drivers.remove(driver)
        
        # 새 드라이버 추가
        driver = shape_key.driver_add('value').driver
        driver.type = 'SCRIPTED'
        var = driver.variables.new()
        var.name = "bone_transform"
        var.type = 'TRANSFORMS'
        
        # 타겟 설정
        target = var.targets[0]
        target.id = armature
        target.bone_target = bone_name
        target.transform_type = transform_type
        target.transform_space = 'LOCAL_SPACE'
        
        # 드라이버 표현식 설정
        if 'ROT' in transform_type:
            driver.expression = f"bone_transform * {57.2958 * multiplier}"  # 라디안을 도로 변환하고 multiplier 적용
        elif 'LOC' in transform_type:
            driver.expression = f"bone_transform * {multiplier}"
        else:  # SCALE
            driver.expression = f"(bone_transform - 1.0) * {multiplier}"
        
        return True, ""
        
    except Exception as e:
        return False, str(e)

def setup_bone_constraints(pose_bone, transform_type):
    """Set up bone constraints for shape key control
    
    Args:
        pose_bone: Pose bone to set up constraints on
        transform_type: Type of transform to limit
    """
    # 기존 제약 조건 제거
    for const in pose_bone.constraints:
        pose_bone.constraints.remove(const)

    if 'LOC' in transform_type:
        const = pose_bone.constraints.new('LIMIT_LOCATION')
        const.name = "Shape Key Control"
        const.owner_space = 'LOCAL'  # 로컬 스페이스로 설정
        const.use_transform_limit = True  # 변환 제한 활성화
        
        # 축 제한 설정
        const.use_min_x = True
        const.use_max_x = True
        const.use_min_y = True
        const.use_max_y = True
        const.use_min_z = True
        const.use_max_z = True
        
        if 'X' in transform_type:
            const.min_x = -1.0
            const.max_x = 1.0
            const.use_min_y = False
            const.use_max_y = False
            const.use_min_z = False
            const.use_max_z = False
        elif 'Y' in transform_type:
            const.min_y = -1.0
            const.max_y = 1.0
            const.use_min_x = False
            const.use_max_x = False
            const.use_min_z = False
            const.use_max_z = False
        elif 'Z' in transform_type:
            const.min_z = -1.0
            const.max_z = 1.0
            const.use_min_x = False
            const.use_max_x = False
            const.use_min_y = False
            const.use_max_y = False

    elif 'ROT' in transform_type:
        const = pose_bone.constraints.new('LIMIT_ROTATION')
        const.name = "Shape Key Control"
        const.owner_space = 'LOCAL'
        const.use_transform_limit = True
        
        const.use_limit_x = True
        const.use_limit_y = True
        const.use_limit_z = True
        
        if 'X' in transform_type:
            const.min_x = -1.571
            const.max_x = 1.571
            const.use_limit_y = False
            const.use_limit_z = False
        elif 'Y' in transform_type:
            const.min_y = -1.571
            const.max_y = 1.571
            const.use_limit_x = False
            const.use_limit_z = False
        elif 'Z' in transform_type:
            const.min_z = -1.571
            const.max_z = 1.571
            const.use_limit_x = False
            const.use_limit_y = False

    elif 'SCALE' in transform_type:
        const = pose_bone.constraints.new('LIMIT_SCALE')
        const.name = "Shape Key Control"
        const.owner_space = 'LOCAL'
        const.use_transform_limit = True
        
        const.use_min_x = True
        const.use_max_x = True
        const.use_min_y = True
        const.use_max_y = True
        const.use_min_z = True
        const.use_max_z = True
        
        if 'X' in transform_type:
            const.min_x = 0.0
            const.max_x = 2.0
            const.use_min_y = False
            const.use_max_y = False
            const.use_min_z = False
            const.use_max_z = False
        elif 'Y' in transform_type:
            const.min_y = 0.0
            const.max_y = 2.0
            const.use_min_x = False
            const.use_max_x = False
            const.use_min_z = False
            const.use_max_z = False
        elif 'Z' in transform_type:
            const.min_z = 0.0
            const.max_z = 2.0
            const.use_min_x = False
            const.use_max_x = False
            const.use_min_y = False
            const.use_max_y = False

    # 본의 변환 모드 설정
    pose_bone.rotation_mode = 'XYZ'
    
def create_shape_key_text_widget(context, text_name, text_body, bone=None):
    """Create text widget for shape key control
    
    Args:
        context: Current context
        text_name: Name for the text object
        text_body: Content of the text
        bone: Optional pose bone to attach widget to
    """
    try:
        # 현재 선택된 오브젝트와 모드 저장
        active_object = context.active_object
        active_mode = context.mode
        
        # 오브젝트 모드로 전환
        if active_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        # 본의 월드 매트릭스 계산
        if bone and isinstance(bone, bpy.types.PoseBone):
            armature = active_object
            world_matrix = armature.matrix_world @ bone.matrix
            bone_loc = world_matrix.translation
            bone_rot = world_matrix.to_euler('XYZ')
            # 본의 길이 계산
            bone_length = bone.length
            # 본 길이를 기준으로 기본 스케일 설정
            base_scale = bone_length * 0.5  # 본 길이의 절반을 기본 크기로
            slider_width = bone_length * 2  # 슬라이더 길이는 본 길이의 2배
            slider_height = bone_length * 0.1  # 슬라이더 높이는 본 길이의 10%
            text_scale = bone_length * 0.4  # 텍스트 크기는 본 길이의 40%
        else:
            bone_loc = mathutils.Vector((0, 0, 0))
            bone_rot = mathutils.Euler((0, 0, 0))
            base_scale = 0.2
            slider_width = base_scale * 4
            slider_height = base_scale * 0.2
            text_scale = base_scale

        # 템플릿 컬렉션 확인 및 생성
        template_collection = ensure_template_collection()
        create_templates(template_collection)

        # 슬라이더 라인 복제
        line_template = template_collection.objects.get("slider_line_template")
        if not line_template:
            return None, "Slider line template not found!"
            
        slider_line = line_template.copy()
        slider_line.name = f"SLIDE_{text_name}"
        slider_line.data = line_template.data.copy()

        # 핸들 복제
        handle_template = template_collection.objects.get("slider_handle_template")
        if not handle_template:
            return None, "Slider handle template not found!"
            
        handle = handle_template.copy()
        handle.name = text_name
        handle.data = handle_template.data.copy()

        # 텍스트 생성
        bpy.ops.object.text_add(location=bone_loc)
        text_obj = context.active_object
        text_obj.name = f"TEXT_{text_name}"
        text_obj.data.body = text_body
        text_obj.data.align_x = 'CENTER'
        text_obj.data.fill_mode = 'NONE'

        # 본의 회전 정보 계산
        bone_rot_quat = world_matrix.to_quaternion()

        # 위치 및 크기 조정
        handle.location = bone_loc
        handle.rotation_euler = bone_rot
        handle.scale = mathutils.Vector((base_scale, base_scale, base_scale))

        # 슬라이더 설정
        slider_line.location = bone_loc
        slider_line.rotation_mode = 'XYZ'
        slider_line.rotation_euler = (math.radians(90), bone_rot.y, bone_rot.z)
        slider_line.scale = mathutils.Vector((slider_width, slider_height, base_scale))

        # 텍스트 위치 조정
        text_offset = mathutils.Vector((0, bone_length * 0.3, 0))  # 본 길이의 30% 만큼 위로
        text_offset.rotate(bone_rot_quat)
        text_obj.location = bone_loc + text_offset
        text_obj.rotation_euler = bone_rot
        text_obj.scale = mathutils.Vector((text_scale, text_scale, text_scale))

        # 모든 오브젝트를 와이어프레임으로 표시
        text_obj.display_type = 'WIRE'
        slider_line.display_type = 'WIRE'
        handle.display_type = 'WIRE'

        # Widgets 컬렉션 확인 또는 생성
        widgets_collection = bpy.data.collections.get("Widgets")
        if not widgets_collection:
            widgets_collection = bpy.data.collections.new("Widgets")
            context.scene.collection.children.link(widgets_collection)

        # 위젯 세트를 위한 새 컬렉션 생성
        widget_set_collection = bpy.data.collections.new(text_name)
        widgets_collection.children.link(widget_set_collection)

        # 현재 컬렉션에서 제거하고 새 위젯 세트 컬렉션으로 이동
        for obj in [text_obj, slider_line, handle]:
            if obj.name in context.scene.collection.objects:
                context.scene.collection.objects.unlink(obj)
            for col in obj.users_collection:
                col.objects.unlink(obj)
            widget_set_collection.objects.link(obj)

        # 본이 제공된 경우 커스텀 쉐이프로 설정
        if bone and isinstance(bone, bpy.types.PoseBone):
            bone.custom_shape = handle
            bone.use_custom_shape_bone_size = True
            bone.custom_shape_scale_xyz = (1, 1, 1)
            bone.custom_shape_translation = (0, 0, 0)
            bone.custom_shape_rotation_euler = (0, 0, 0)

        # 원래 모드로 복원
        if active_mode != 'OBJECT':
            context.view_layer.objects.active = active_object
            bpy.ops.object.mode_set(mode=active_mode)

        return handle, ""

    except Exception as e:
        return None, str(e)

class OBJECT_OT_text_input_dialog(Operator):
    """Dialog for entering custom text for shape key widgets"""
    bl_idname = "object.text_input_dialog"
    bl_label = "Text Input"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def create_slider_from_template(self, context, text_content):
        """Create slider objects from template
        
        Args:
            context: Current context
            text_content: Text content for the slider
        """
        # 현재 선택된 오브젝트 저장
        active_object = context.view_layer.objects.active

        try:
            # 템플릿 컬렉션 확인 및 생성
            template_collection = ensure_template_collection()
            
            # 템플릿 오브젝트 확인 및 생성
            create_templates(template_collection)
            
            # 슬라이더 컬렉션 생성 또는 가져오기
            slider_collection = bpy.data.collections.get("ShapeKeySliders")
            if not slider_collection:
                slider_collection = bpy.data.collections.new("ShapeKeySliders")
                context.scene.collection.children.link(slider_collection)
            
            # 슬라이더 라인 복제
            line_template = template_collection.objects.get("slider_line_template")
            if not line_template:
                self.report({'ERROR'}, "Slider line template not found!")
                return {'CANCELLED'}
            
            slider_line = line_template.copy()
            slider_line.name = f"Slider_{text_content}"
            slider_line.data = line_template.data.copy()
            context.scene.collection.objects.link(slider_line)
            
            # 슬라이더 핸들 복제
            handle_template = template_collection.objects.get("slider_handle_template")
            if not handle_template:
                self.report({'ERROR'}, "Slider handle template not found!")
                return {'CANCELLED'}
            
            handle = handle_template.copy()
            handle.name = f"Handle_{text_content}"
            handle.data = handle_template.data.copy()
            context.scene.collection.objects.link(handle)
            
            # 텍스트 생성 (슬라이더 생성 후에 위치 조정을 위해 순서 변경)
            bpy.ops.object.text_add(location=(0, 0, 0))
            text_obj = context.view_layer.objects.active
            text_obj.name = f"Text_{text_content}"
            text_obj.data.body = text_content
            text_obj.data.fill_mode = 'NONE'
            
            # 위치 및 크기 조정 (고정된 가로 방향)
            slider_line.scale.x = 2
            slider_line.scale.y = 0.1
            
            # 텍스트를 슬라이더 위에 배치
            text_obj.location = slider_line.location.copy()
            text_obj.location.y += 0.3  # 슬라이더 위로 조정
            
            # 모든 오브젝트를 와이어프레임으로 표시
            text_obj.display_type = 'WIRE'
            slider_line.display_type = 'WIRE'
            handle.display_type = 'WIRE'
            
            # 생성된 오브젝트들을 슬라이더 컬렉션으로 이동
            context.scene.collection.objects.unlink(text_obj)
            context.scene.collection.objects.unlink(slider_line)
            context.scene.collection.objects.unlink(handle)
            slider_collection.objects.link(text_obj)
            slider_collection.objects.link(slider_line)
            slider_collection.objects.link(handle)
            
            return {'FINISHED'}
            
        finally:
            # 이전 선택 상태 복원
            if active_object:
                context.view_layer.objects.active = active_object
    
    text_input: StringProperty(
        name="Custom Text",
        description="Enter custom text for the object",
        default=""
    ) # type: ignore

    use_shape_key_name: BoolProperty(
        name="Use Shape Key Name",
        description="Use shape key name instead of custom text",
        default=True
    ) # type: ignore

    shape_key_name: StringProperty(
        name="Shape Key Name",
        description="Name of the selected shape key"
    ) # type: ignore

    def execute(self, context):
        if not self.shape_key_name and not self.text_input:
            self.report({'ERROR'}, "No text content provided")
            return {'CANCELLED'}
        text_content = self.shape_key_name if self.use_shape_key_name else self.text_input
        return self.create_slider_from_template(context, text_content)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_shape_key_name", text="Use Shape Key Name")
        
        if self.use_shape_key_name:
            layout.label(text=f"Shape Key Name: {self.shape_key_name}")
        else:
            layout.prop(self, "text_input")

class OBJECT_OT_create_shape_key_text(Operator):
    """Create text object from selected shape key"""
    bl_idname = "object.create_shape_key_text"
    bl_label = "Create Shape Key Text"
    bl_options = {'REGISTER', 'UNDO'}
    
    shape_key: EnumProperty(
        items=lambda self, context: [
            (sk.name, sk.name, "") 
            for sk in context.active_object.data.shape_keys.key_blocks[1:]
        ] if context.active_object.data.shape_keys else [],
        name="Shape Key",
        description="Select shape key to create text for"
    ) # type: ignore
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'MESH' and 
                context.active_object.data.shape_keys)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "shape_key")
    
    def execute(self, context):
        text_obj, error = create_shape_key_text_widget(
            context,
            f"WGT_{self.shape_key}",  # WGT_ 접두어 사용
            self.shape_key
        )
        
        if text_obj:
            self.report({'INFO'}, f"Created shape key text: {text_obj.name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Error creating text: {error}")
            return {'CANCELLED'}

class OBJECT_OT_apply_shape_key_to_bone(Operator):
    """Apply shape key animation to selected bone"""
    bl_idname = "object.apply_shape_key_to_bone"
    bl_label = "Apply Shape Key to Bone"
    bl_options = {'REGISTER', 'UNDO'}

    target_mesh: EnumProperty(
        name="Target Mesh",
        description="Select mesh with shape keys",
        items=lambda self, context: [
            (obj.name, obj.name, "")
            for obj in context.scene.objects
            if obj.type == 'MESH' and obj.data.shape_keys
        ],
        update=lambda self, context: self.on_mesh_updated()
    ) # type: ignore

    target_shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to connect",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, context.active_object).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else [],
        update=lambda self, context: self.on_shape_key_updated()
    ) # type: ignore

    transform_type: EnumProperty(
        name="Transform Type",
        description="Type of transform to control the shape key",
        items=TRANSFORM_ITEMS,
        default='LOC_X'
    ) # type: ignore

    multiplier: FloatProperty(
        name="Influence",
        description="Driver influence multiplier (higher value = stronger effect)",
        default=4,
        min=0.0,
        max=30.0,
        step=0.1,
        precision=3
    ) # type: ignore
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.active_pose_bone
    
    def invoke(self, context, event):
        # 기본값 설정: 첫 번째 사용 가능한 메쉬와 쉐이프 키 선택
        if not self.target_mesh:
            for obj in context.scene.objects:
                if (obj.type == 'MESH' and obj.data.shape_keys):
                    self.target_mesh = obj.name
                    # 첫 번째 쉐이프 키 선택
                    if obj.data.shape_keys.key_blocks:
                        self.target_shape_key = obj.data.shape_keys.key_blocks[1].name  # 0은 Basis
                    break
        
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_mesh")
        if self.target_mesh:
            layout.prop(self, "target_shape_key")
        layout.prop(self, "transform_type")
        layout.prop(self, "multiplier", slider=True)  # 슬라이더로 표시
    
    def execute(self, context):
        pose_bone = context.active_pose_bone
        armature = context.active_object
        
        target_mesh = bpy.data.objects.get(self.target_mesh)
        if not target_mesh:
            self.report({'ERROR'}, "Selected mesh not found!")
            return {'CANCELLED'}
        
        try:
            if self.target_shape_key in target_mesh.data.shape_keys.key_blocks:
                shape_key = target_mesh.data.shape_keys.key_blocks[self.target_shape_key]
                
                success, error_message = setup_shape_key_driver(
                    armature,
                    pose_bone.name,
                    shape_key,
                    self.transform_type,
                    self.multiplier
                )
                
                if not success:
                    self.report({'ERROR'}, f"Error setting up driver: {error_message}")
                    return {'CANCELLED'}
                
                self.report({'INFO'}, f"Successfully connected bone '{pose_bone.name}' to shape key '{self.target_shape_key}'")
            else:
                self.report({'ERROR'}, f"Shape key '{self.target_shape_key}' not found in mesh")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class OBJECT_OT_add_shape_key_bone(Operator):
    """Add new bone for shape key control to metarig"""
    bl_idname = "object.add_shape_key_bone"
    bl_label = "Add Shape Key Bone"
    bl_options = {'REGISTER', 'UNDO'}

    def update_connect_driver(self, context):
        """Update bone name when connect driver option changes"""
        try:
            if self.connect_driver and self.target_shape_key:
                new_name = f"shape_key_ctrl_{self.target_shape_key}"
                self.suggested_name = new_name
                self.bone_name = new_name
            else:
                self.bone_name = "shape_key_ctrl"
                self.suggested_name = "shape_key_ctrl"
        except Exception as e:
            self.report({'ERROR'}, f"Error updating connect driver: {str(e)}")

    def update_mesh(self, context):
        """Update bone name when target mesh changes"""
        try:
            if self.target_mesh:
                self.target_shape_key = ''
                self.bone_name = "shape_key_ctrl"
                self.suggested_name = "shape_key_ctrl"
        except Exception as e:
            self.report({'ERROR'}, f"Error updating mesh selection: {str(e)}")

    def update_shape_key(self, context):
        """Update bone name when shape key selection changes"""
        try:
            if self.connect_driver and self.target_shape_key:
                new_name = f"shape_key_ctrl_{self.target_shape_key}"
                self.suggested_name = new_name
                self.bone_name = new_name
                # 텍스트 내용 업데이트
                self.text_content = self.target_shape_key
                
                # UI 강제 업데이트
                for area in context.screen.areas:
                    area.tag_redraw()
        except Exception as e:
            self.report({'ERROR'}, f"Error updating shape key selection: {str(e)}")

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
        items=TRANSFORM_ITEMS,
        default='LOC_X'
    ) # type: ignore

    target_mesh: EnumProperty(
        name="Target Mesh",
        description="Select mesh with shape keys",
        items=lambda self, context: [
            (obj.name, obj.name, "")
            for obj in context.scene.objects
            if obj.type == 'MESH' and obj.data.shape_keys
        ],
        update=update_mesh
    ) # type: ignore

    target_shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to connect",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, context.active_object).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else [],
        update=update_shape_key
    ) # type: ignore

    connect_driver: BoolProperty(
        name="Connect Shape Key Driver",
        description="Connect to shape key after creating bone",
        default=True,
        update=update_connect_driver
    ) # type: ignore

    multiplier: FloatProperty(
        name="Influence",
        description="Driver influence strength multiplier",
        default=4,
        min=0.0,
        max=30.0,
        step=0.1,
        precision=3
    ) # type: ignore

    create_text_widget: BoolProperty(
        name="Create Text Widget",
        description="Create shape key text and use it as bone widget",
        default=True
    ) # type: ignore

    text_content: StringProperty(
        name="Widget Text",
        description="Text content for the widget",
        default=""
    ) # type: ignore

    @classmethod
    def poll(cls, context):
        return context.scene.metarig and context.scene.metarig.type == 'ARMATURE'

    def invoke(self, context, event):
        self.connect_driver = True
        
        # 첫 번째 사용 가능한 메쉬와 쉐이프 키 선택
        if not self.target_mesh:
            for obj in context.scene.objects:
                if obj.type == 'MESH' and obj.data.shape_keys:
                    self.target_mesh = obj.name
                    if len(obj.data.shape_keys.key_blocks) > 1:
                        shape_key_name = obj.data.shape_keys.key_blocks[1].name
                        self.target_shape_key = shape_key_name
                        new_name = f"shape_key_ctrl_{shape_key_name}"
                        self.suggested_name = new_name
                        self.bone_name = new_name
                        self.text_content = shape_key_name  # 텍스트 내용 초기화
                    break
        else:
            obj = bpy.data.objects.get(self.target_mesh)
            if obj and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 1:
                shape_key_name = obj.data.shape_keys.key_blocks[1].name
                self.target_shape_key = shape_key_name
                new_name = f"shape_key_ctrl_{shape_key_name}"
                self.suggested_name = new_name
                self.bone_name = new_name
                self.text_content = shape_key_name  # 텍스트 내용 초기화
        
        # UI 강제 업데이트
        for area in context.screen.areas:
            area.tag_redraw()
        
        return context.window_manager.invoke_props_dialog(self) if self.target_mesh else {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Bone Settings:", icon='BONE_DATA')
        box.prop(self, "bone_name")
        box.prop(self, "transform_type")
        
        box = layout.box()
        box.label(text="Driver Settings:", icon='DRIVER')
        row = box.row()
        row.prop(self, "connect_driver", text="Connect to Shape Key")
        
        if self.connect_driver:
            col = box.column(align=True)
            col.prop(self, "target_mesh")
            if self.target_mesh:
                col.prop(self, "target_shape_key")
                if self.target_shape_key:
                    box.prop(self, "multiplier", slider=True)
                    # 텍스트 위젯 설정 추가
                    box.prop(self, "create_text_widget")
                    if self.create_text_widget:
                        box.prop(self, "text_content")

    def execute(self, context):
        metarig = context.scene.metarig
        if not metarig or metarig.type != 'ARMATURE':
            self.report({'ERROR'}, "No valid metarig selected!")
            return {'CANCELLED'}

        # 드라이버 연결이 활성화된 경우에만 메쉬와 쉐이프 키 확인
        if self.connect_driver:
            if not self.target_mesh or not self.target_shape_key:
                bpy.ops.object.show_select_mesh_popup('INVOKE_DEFAULT')
                return {'CANCELLED'}
            
            target_mesh = bpy.data.objects.get(self.target_mesh)
            if not target_mesh or not target_mesh.data.shape_keys:
                bpy.ops.object.show_select_mesh_popup('INVOKE_DEFAULT')
                return {'CANCELLED'}

        try:
            # 현재 활성 오브젝트와 모드 저장
            current_active = context.active_object
            current_mode = context.mode if current_active else 'OBJECT'

            # 메타리그를 활성화
            metarig.hide_viewport = False
            metarig.hide_set(False)
            
            # 오브젝트 모드로 전환
            if current_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            
            bpy.ops.object.select_all(action='DESELECT')
            metarig.select_set(True)
            context.view_layer.objects.active = metarig

            # 편집 모드로 전환
            if context.active_object:
                bpy.ops.object.mode_set(mode='EDIT')

            # 새로운 본 추가
            new_bone = metarig.data.edit_bones.new(self.bone_name)
            new_bone.head = (0, 0, 0)
            new_bone.tail = (0, 0, 0.1)

            # 리깅 설정을 위한 본 속성 설정
            new_bone.use_deform = False

            # 새로운 본 선택
            for b in metarig.data.edit_bones:
                b.select = False
                b.select_head = False
                b.select_tail = False
            new_bone.select = True
            new_bone.select_head = True
            new_bone.select_tail = True
            metarig.data.edit_bones.active = new_bone

            # 포즈 모드로 전환
            if context.active_object:
                bpy.ops.object.mode_set(mode='POSE')

            # 새로 생성된 본 선택
            pose_bone = metarig.pose.bones.get(self.bone_name)
            if pose_bone:
                # 모든 본의 선택 해제
                for pb in metarig.pose.bones:
                    pb.bone.select = False
                # 새 본 선택
                pose_bone.bone.select = True
                metarig.data.bones.active = pose_bone.bone
                
                # 디폼 설정
                pose_bone.bone.use_deform = True

                # rigify 타입 설정
                pose_bone.rigify_type = 'basic.super_copy'
                
                # rigify 파라미터 설정
                if hasattr(pose_bone, 'rigify_parameters'):
                    pose_bone.rigify_parameters.make_widget = True
                    pose_bone.rigify_parameters.make_control = True
                    pose_bone.rigify_parameters.make_deform = True
                    pose_bone.rigify_parameters.widget_type = 'bone'

                # 드라이버 타입에 따른 제약 설정
                setup_bone_constraints(pose_bone, self.transform_type)

                # 드라이버 연결이 선택된 경우
                if self.connect_driver and self.target_mesh and self.target_shape_key:
                    target_mesh = bpy.data.objects.get(self.target_mesh)
                    if target_mesh and target_mesh.data.shape_keys:
                        shape_key = target_mesh.data.shape_keys.key_blocks.get(self.target_shape_key)
                        if shape_key:
                            # 리기파이 리그 확인
                            rig = context.scene.rigify_rig
                            if rig:
                                success, error_message = setup_shape_key_driver(
                                    rig,  # 리기파이 리그 사용
                                    self.bone_name,
                                    shape_key,
                                    self.transform_type,
                                    self.multiplier
                                )
                                if not success:
                                    self.report({'WARNING'}, f"Error setting up driver: {error_message}")
                            else:
                                self.report({'WARNING'}, "No rigify rig selected")
                        else:
                            self.report({'WARNING'}, "Shape key not found")
                    else:
                        self.report({'WARNING'}, "Target mesh not found or has no shape keys")

                self.report({'INFO'}, f"Created bone '{self.bone_name}' with rigify settings")

                # 메타리그를 선택하고 에딧 모드로 설정
                context.view_layer.objects.active = metarig
                bpy.ops.object.mode_set(mode='EDIT')

                # 새로 생성한 본 선택
                edit_bone = metarig.data.edit_bones.get(self.bone_name)
                if edit_bone:
                    for b in metarig.data.edit_bones:
                        b.select = False
                        b.select_head = False
                        b.select_tail = False
                    edit_bone.select = True
                    edit_bone.select_head = True
                    edit_bone.select_tail = True
                    metarig.data.edit_bones.active = edit_bone

                return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            # 에러 발생 시 팝업 표시
            bpy.ops.object.show_select_mesh_popup('INVOKE_DEFAULT')
            # 에러 발생 시 메타리그 에딧 모드로 설정 시도
            try:
                context.view_layer.objects.active = metarig
                bpy.ops.object.mode_set(mode='EDIT')
                # 새로 생성한 본 선택
                edit_bone = metarig.data.edit_bones.get(self.bone_name)
                if edit_bone:
                    for b in metarig.data.edit_bones:
                        b.select = False
                        b.select_head = False
                        b.select_tail = False
                    edit_bone.select = True
                    edit_bone.select_head = True
                    edit_bone.select_tail = True
                    metarig.data.edit_bones.active = edit_bone
            except:
                pass
            return {'CANCELLED'}

class OBJECT_OT_show_select_mesh_popup(Operator):
    """Show popup when mesh selection is required"""
    bl_idname = "object.show_select_mesh_popup"
    bl_label = "Shape Key Required"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Shape Key Connection Required!", icon='ERROR')
        row = layout.row()
        row.label(text="Please select a mesh and shape key first.")

classes = (
    OBJECT_OT_text_input_dialog,
    OBJECT_OT_create_shape_key_text,
    OBJECT_OT_apply_shape_key_to_bone,
    OBJECT_OT_add_shape_key_bone,
    OBJECT_OT_show_select_mesh_popup,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
