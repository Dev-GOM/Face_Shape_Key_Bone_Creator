import bpy
import math
import mathutils

# Constants
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

def ensure_template_collection():
    """Ensure template collection exists and create if missing"""
    template_collection = None
    for collection in bpy.context.scene.collection.children:
        if collection.name == "ShapeKeySliderTemplates":
            template_collection = collection
            break
            
    if template_collection is None:
        template_collection = bpy.data.collections.new("ShapeKeySliderTemplates")
        bpy.context.scene.collection.children.link(template_collection)
        template_collection.hide_viewport = True
        template_collection.hide_render = True
    
    return template_collection

def create_templates(template_collection):
    """Create required template objects for shape key controls"""
    # Create slider line template
    if "slider_line_template" not in template_collection.objects:
        bpy.ops.mesh.primitive_plane_add(size=1)
        slider_line = bpy.context.view_layer.objects.active
        slider_line.name = "slider_line_template"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='ONLY_FACE')
        bpy.ops.object.mode_set(mode='OBJECT')
        for col in slider_line.users_collection:
            col.objects.unlink(slider_line)
        template_collection.objects.link(slider_line)

    if "slider_handle_template" not in template_collection.objects:
        bpy.ops.mesh.primitive_circle_add(radius=0.1, vertices=16)
        handle = bpy.context.view_layer.objects.active
        handle.name = "slider_handle_template"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edge_face_add()
        bpy.ops.object.mode_set(mode='OBJECT')
        for col in handle.users_collection:
            col.objects.unlink(handle)
        template_collection.objects.link(handle)

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
        
        # 드라이버 설정 후 Basis 쉐이프키 선택
        mesh_obj = None
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data.shape_keys == shape_key.id_data:
                mesh_obj = obj
                break
                
        if mesh_obj:
            mesh_obj.active_shape_key_index = 0  # Basis 선택
        
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
    
def get_meshes_with_drivers(self, context):
    """드라이버가 있는 메쉬 목록 생성"""
    items = []
    
    # 본 이름 가져오기
    if context.mode == 'EDIT_ARMATURE':
        bone_name = context.active_bone.name
    else:  # POSE
        bone_name = context.active_pose_bone.name
    
    # 드라이버가 있는 메쉬 검색
    for obj in context.scene.objects:
        if obj.type == 'MESH' and obj.data.shape_keys and obj.data.shape_keys.animation_data:
            has_driver = False
            for driver in obj.data.shape_keys.animation_data.drivers:
                for var in driver.driver.variables:
                    if (var.type == 'TRANSFORMS' and 
                        var.targets[0].bone_target == bone_name):
                        has_driver = True
                        break
                if has_driver:
                    items.append((obj.name, obj.name, ""))
                    break
    
    return items

def get_shape_key_drivers(self, context):
    """선택된 메쉬의 모든 쉐이프 키 드라이버 목록 생성"""
    items = []
    
    if not hasattr(self, 'target_mesh') or not self.target_mesh:
        return items

    # 선택된 메쉬의 드라이버 검사
    obj = bpy.data.objects.get(self.target_mesh)
    if obj and obj.data.shape_keys and obj.data.shape_keys.animation_data:
        shape_keys = obj.data.shape_keys
        
        # 모든 드라이버 순회
        for driver in shape_keys.animation_data.drivers:
            # 쉐이프 키 이름 추출
            try:
                # 드라이버 데이터 경로에서 쉐이프 키 이름 추출
                # 예: 'key_blocks["name"].value' -> 'name'
                shape_key_name = driver.data_path.split('"')[1]
                items.append((shape_key_name, shape_key_name, ""))
            except:
                continue
    
    return items
