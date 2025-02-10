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

def setup_shape_key_driver(armature, bone_name, shape_key, transform_type, multiplier=30.0):
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
    
def get_available_meshes(context):
    """Returns visible mesh objects with shape keys"""
    meshes = [obj for obj in context.scene.objects 
             if (obj.type == 'MESH' and 
                 obj.visible_get() and
                 obj.data.shape_keys)]
    return meshes

def draw_shape_key_list(layout, mesh_obj):
    """Draw shape key list UI"""
    shape_keys = mesh_obj.data.shape_keys
    
    for key_block in shape_keys.key_blocks[1:]:
        row = layout.row(align=True)
        value_row = row.split(factor=0.7, align=True)
        value_row.prop(key_block, "value", text=key_block.name)
        
        if shape_keys.animation_data and shape_keys.animation_data.drivers:
            for driver in shape_keys.animation_data.drivers:
                if driver.data_path == f'key_blocks["{key_block.name}"].value':
                    var = driver.driver.variables[0]
                    transform_type = var.targets[0].transform_type
                    current_value = get_driver_value(driver, transform_type)
                    
                    # UI 처리
                    sub_row = value_row.row(align=True)
                    if isinstance(current_value, str):  # 문자열인 경우
                        if current_value == "Custom":
                            sub_row.label(text="Custom", icon='DRIVER')
                        else:
                            # 수식을 표시
                            sub_row.label(text=current_value, icon='DRIVER')
                    else:
                        # 숫자값인 경우 기존 UI 사용
                        props = sub_row.operator("shape.adjust_driver_value", 
                                              text=f"{current_value:.1f}", 
                                              icon='DRIVER')
                        props.mesh_name = mesh_obj.name
                        props.shape_key_name = key_block.name
                        props.transform_type = transform_type
                        props.value = current_value
                    break

def get_driver_value(driver, transform_type):
    """Calculate current value of driver"""
    try:
        expression = driver.driver.expression
        
        # 애드온으로 만든 표준 형식 체크
        if 'bone_transform' in expression:
            if 'ROT' in transform_type:
                return float(expression.split('*')[2]) / 57.2958
            elif 'LOC' in transform_type:
                return float(expression.split('*')[1])
            else:  # SCALE
                return float(expression.split('*')[1])
        
        # 사용자 정의 드라이버 처리
        else:
            # 복잡한 수식인 경우 원본 표시
            if any(op in expression for op in ['+', '-', '*', '/', '(', ')']):
                return expression  # 수식 그대로 반환
            
            # 단순 숫자만 있는 경우
            try:
                return float(expression)
            except:
                return "Custom"  # 파싱 불가능한 경우
            
    except Exception as e:
        print(f"Error parsing driver value: {e}")
        return "Custom"

def update_driver_expression(driver, value, transform_type, mesh_obj=None):
    """
    Update driver expression
    Args:
        driver: Driver object
        value: New value
        transform_type: Transform type
        mesh_obj: Mesh object (optional)
    """
    rounded_value = round(value, 1)
    
    if 'ROT' in transform_type:
        driver.expression = f"bone_transform * {57.2958 * rounded_value:.1f}"
    elif 'LOC' in transform_type:
        driver.expression = f"bone_transform * {rounded_value}"
    else:  # SCALE
        driver.expression = f"(bone_transform - 1.0) * {rounded_value}"
    
    # 메쉬 객체가 제공된 경우 Basis 선택
    if mesh_obj:
        mesh_obj.active_shape_key_index = 0
        
def calculate_widget_base_scales(bone_length):
    """Calculate base scales for widgets based on bone length"""
    return {
        "base_scale": bone_length * 0.5,  # 본 길이의 절반을 기본 크기로
        "slider_width": bone_length * 2,   # 슬라이더 길이는 본 길이의 2배
        "slider_height": bone_length * 0.1, # 슬라이더 높이는 본 길이의 10%
        "text_scale": bone_length * 0.4    # 텍스트 크기는 본 길이의 40%
    }

def calculate_slider_offset(scales, shape_key=None):
    """Calculate slider offset based on shape key range"""
    base_offset = mathutils.Vector((-scales["slider_width"] / 2, 0, 0))  # 기본 위치
    
    if shape_key and isinstance(shape_key, bpy.types.ShapeKey):
        min_value = shape_key.slider_min
        max_value = shape_key.slider_max
        
        if min_value == -1 and max_value == 1:
            # -1~1 범위일 경우 본이 중앙에 오도록
            base_offset = mathutils.Vector((0, 0, 0))
            print("Centered slider")
        elif not (min_value == 0 and max_value == 1):
            # 다른 범위의 경우 오프셋 계산
            total_range = max_value - min_value
            mid_value = (max_value + min_value) / 2
            offset_ratio = -mid_value / total_range
            x_offset = scales["slider_width"] * offset_ratio
            base_offset += mathutils.Vector((x_offset, 0, 0))
            print(f"Offset slider by {x_offset}")
            
    return base_offset

def calculate_widget_transforms(bone_matrix, bone_length, shape_key=None):
    """Calculate all widget transforms"""
    bone_loc = bone_matrix.translation
    bone_rot = bone_matrix.to_euler('XYZ')
    bone_rot_quat = bone_matrix.to_quaternion()

    # 기본 스케일 계산
    scales = calculate_widget_base_scales(bone_length)
    
    # 오프셋 계산
    base_offset = calculate_slider_offset(scales, shape_key)
    base_offset.rotate(bone_rot_quat)
    
    # 텍스트 오프셋 계산
    text_offset = mathutils.Vector((0, bone_length * 0.3, 0))
    text_offset.rotate(bone_rot_quat)

    return {
        "bone_loc": bone_loc,
        "bone_rot": bone_rot,
        "bone_rot_quat": bone_rot_quat,
        **scales,
        "base_offset": base_offset,
        "text_offset": text_offset
    }

def apply_widget_transforms(obj, transforms, obj_type):
    """Apply calculated transforms to widget object"""
    if obj_type == 'TEXT':
        obj.location = transforms["bone_loc"] + transforms["text_offset"]
        obj.rotation_euler = transforms["bone_rot"]
        obj.scale = mathutils.Vector((transforms["text_scale"],) * 3)
        obj.display_type = 'WIRE'
        
    elif obj_type == 'SLIDE':
        obj.location = transforms["bone_loc"] - transforms["base_offset"]
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler = (math.radians(90), transforms["bone_rot"].y, transforms["bone_rot"].z)
        obj.scale = mathutils.Vector((transforms["slider_width"], transforms["slider_height"], transforms["base_scale"]))
        obj.display_type = 'WIRE'
        
    elif obj_type == 'WGT':
        obj.location = transforms["bone_loc"]
        obj.rotation_euler = transforms["bone_rot"]
        obj.scale = mathutils.Vector((transforms["base_scale"],) * 3)
        obj.display_type = 'WIRE'

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
    
def find_existing_widgets(text_name):
    """Find existing widgets collection and objects
    
    Args:
        text_name: Full widget name (e.g., 'WGT_shape_key_ctrl_Ah')
        
    Returns:
        tuple: (collection, handle, slider, text) or (None, None, None, None)
    """
    if text_name in bpy.data.collections:
        collection = bpy.data.collections[text_name]
        handle = collection.objects.get(text_name)
        slider = collection.objects.get(f"SLIDE_{text_name}")
        text = collection.objects.get(f"TEXT_{text_name}")
        if all([handle, slider, text]):
            return collection, handle, slider, text
    return None, None, None, None

def create_shape_key_text_widget(context, text_name, text_body, bone=None, shape_key=None):
    """Create text widget for shape key control
    
    Args:
        context: Current context
        text_name: Full widget name (e.g., 'WGT_shape_key_ctrl_Ah')
        text_body: Content of the text
        bone: Optional pose bone to attach widget to
        shape_key: Optional shape key for range calculation
    """
    try:
        # 기존 위젯 찾기
        collection, handle, slider_line, text_obj = find_existing_widgets(text_name)
        
        # 기존 위젯이 있으면 재사용
        if handle:
            # 본이 제공된 경우 커스텀 쉐이프로 설정
            if bone and isinstance(bone, bpy.types.PoseBone):
                bone.custom_shape = handle
                bone.use_custom_shape_bone_size = True
                bone.custom_shape_scale_xyz = (1, 1, 1)
                bone.custom_shape_translation = (0, 0, 0)
                bone.custom_shape_rotation_euler = (0, 0, 0)
            return handle, ""

        # 현재 선택된 오브젝트와 모드 저장
        active_object = context.active_object
        active_mode = context.mode
        
        # 오브젝트 모드로 전환
        if active_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 트랜스폼 계산
        if bone and isinstance(bone, bpy.types.PoseBone):
            world_matrix = active_object.matrix_world @ bone.matrix
            transforms = calculate_widget_transforms(world_matrix, bone.length, shape_key)
        else:
            transforms = calculate_widget_transforms(
                mathutils.Matrix.Identity(4),
                0.2,  # 기본 본 길이
                shape_key
            )

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
        bpy.ops.object.text_add(location=transforms["bone_loc"])
        text_obj = context.active_object
        text_obj.name = f"TEXT_{text_name}"
        text_obj.data.body = text_body
        text_obj.data.align_x = 'CENTER'
        text_obj.data.fill_mode = 'NONE'

        # 위젯들에 트랜스폼 적용
        apply_widget_transforms(handle, transforms, 'WGT')
        apply_widget_transforms(slider_line, transforms, 'SLIDE')
        apply_widget_transforms(text_obj, transforms, 'TEXT')

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
        print(f"Error in create_shape_key_text_widget: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, str(e)
    
def get_mesh_items(self, context):
    """메쉬 선택용 아이템 리스트 생성"""
    return [
        (obj.name, obj.name, "")
        for obj in context.scene.objects
        if obj.type == 'MESH' and obj.data.shape_keys
    ]

def get_shape_key_items(self, context):
    """쉐이프 키 선택용 아이템 리스트 생성"""
    if not self.target_mesh:
        return []
    
    mesh_obj = bpy.data.objects.get(self.target_mesh)
    if not mesh_obj or not mesh_obj.data.shape_keys:
        return []
        
    return [
        (sk.name, sk.name, "")
        for sk in mesh_obj.data.shape_keys.key_blocks[1:]  # Basis 제외
    ]
    
def get_meshes_with_drivers(self, context):
    """드라이버가 있는 메쉬 목록 생성"""
    items = []
    
    # 본 이름 가져오기
    bone_name = None
    if context.mode == 'EDIT_ARMATURE':
        if context.active_bone:
            bone_name = context.active_bone.name
    else:  # POSE
        if context.active_pose_bone:
            bone_name = context.active_pose_bone.name
    
    if not bone_name:
        return []
    
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

def store_custom_widgets(armature):
    """Store custom widget information and parent relationship
    Only stores custom widgets that start with 'WGT_shape_key_ctrl'
    """
    # 현재 모드 확인
    current_mode = bpy.context.mode
    
    # 포즈 모드로 전환
    if current_mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    
    stored_widgets = {}
    for pose_bone in armature.pose.bones:
        if (pose_bone.custom_shape and 
            pose_bone.custom_shape.name.startswith('WGT_shape_key_ctrl')):
            stored_widgets[pose_bone.name] = {
                'widget': pose_bone.custom_shape,
                'parent': pose_bone.parent.name if pose_bone.parent else None
            }
    
    return stored_widgets

def restore_custom_widgets(armature, stored_widgets):
    """Restore custom widget information and parent relationship"""
    # 현재 선택 상태 저장
    current_mode = bpy.context.mode
    
    # 포즈 모드로 전환
    if current_mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    
    # 본 이름 매핑 생성
    bone_mapping = {
        bone.name: bone.name 
        for bone in armature.pose.bones 
        if bone.name in stored_widgets
    }
    
    # 커스텀 위젯과 부모 관계 복원
    for old_bone_name, stored_data in stored_widgets.items():
        # 새로운 본 이름 찾기
        new_bone_name = bone_mapping.get(old_bone_name, old_bone_name)
        
        if new_bone_name in armature.pose.bones:
            pose_bone = armature.pose.bones[new_bone_name]
            widget = stored_data['widget']
            parent_name = stored_data['parent']
            
            # 위젯이 여전히 존재하는지 확인
            if widget and widget.name in bpy.data.objects:
                # 커스텀 쉐이프 설정
                pose_bone.custom_shape = widget
            
            # 부모 관계 복원
            if parent_name:
                # 에딧 모드로 전환
                bpy.ops.object.mode_set(mode='EDIT')
                edit_bone = armature.data.edit_bones[new_bone_name]
                if parent_name in armature.data.edit_bones:
                    edit_bone.parent = armature.data.edit_bones[parent_name]
                bpy.ops.object.mode_set(mode='POSE')

def transform_handler(scene):
    """Transform handler for auto-sync"""
    try:
        if (scene.is_sync_enabled and 
            scene.metarig and 
            scene.rigify_rig and 
            bpy.context.mode == 'EDIT_ARMATURE' and
            bpy.context.active_bone and
            bpy.context.active_object == scene.rigify_rig):
            
            # 현재 본 정보
            rigify_bone = bpy.context.active_bone
            bone_name = rigify_bone.name
            
            # 연결된 위젯 찾기
            widget_name = f"WGT_{bone_name}"
            widget_collection = None
            widget_objects = []
            
            # 모든 컬렉션에서 위젯 검색
            for collection in bpy.data.collections:
                for obj in collection.objects:
                    if obj.name.startswith(widget_name):
                        widget_collection = collection
                        widget_objects = [obj for obj in collection.objects 
                                        if obj.name.startswith(('WGT_', 'SLIDE_', 'TEXT_'))]
                        break
                if widget_collection:
                    break
            
            # 위젯이 있는 경우 위치 업데이트
            if widget_objects:
                # 쉐이프 키 찾기
                shape_key = None
                for obj in widget_objects:
                    if obj.name.startswith('WGT_'):
                        # 위젯 이름에서 본 이름 추출
                        widget_bone_name = obj.name[4:]  # 'WGT_' 제외
                        # 연결된 메쉬에서 쉐이프 키 찾기
                        for mesh_obj in bpy.data.objects:
                            if (mesh_obj.type == 'MESH' and 
                                mesh_obj.data.shape_keys and 
                                mesh_obj.data.shape_keys.animation_data):
                                for driver in mesh_obj.data.shape_keys.animation_data.drivers:
                                    if widget_bone_name in driver.data_path:
                                        shape_key_name = driver.data_path.split('"')[1]
                                        shape_key = mesh_obj.data.shape_keys.key_blocks[shape_key_name]
                                        break
                                if shape_key:
                                    break
                        break
                
                # 본 매트릭스 계산
                bone_matrix = scene.metarig.matrix_world @ scene.metarig.pose.bones[bone_name].matrix
                
                # 트랜스폼 계산 및 적용
                transforms = calculate_widget_transforms(
                    bone_matrix,
                    scene.metarig.pose.bones[bone_name].length,
                    shape_key
                )
                
                # 각 위젯 오브젝트 업데이트
                for obj in widget_objects:
                    if obj.name.startswith('WGT_'):
                        apply_widget_transforms(obj, transforms, 'WGT')
                    elif obj.name.startswith('SLIDE_'):
                        apply_widget_transforms(obj, transforms, 'SLIDE')
                    elif obj.name.startswith('TEXT_'):
                        apply_widget_transforms(obj, transforms, 'TEXT')
            
            # 본 동기화 실행
            bpy.ops.edit.sync_metarig_bone()
            
    except Exception as e:
        print(f"Error in transform handler: {str(e)}")

def regenerate_rigify_with_widgets(context):
    """리기파이 리그 재생성 (위젯 보존)"""
    try:
        # 현재 리기파이 리그의 커스텀 위젯 정보 저장
        rigify_rig = context.scene.rigify_rig
        stored_widgets = store_custom_widgets(rigify_rig)

        # 오브젝트 모드로 전환
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        # 메타리그 선택 및 활성화
        metarig = context.scene.metarig
        if not metarig:
            return False, f"Error Metarig not found"

        metarig.hide_select = False
        metarig.hide_set(False)
        metarig.select_set(True)
        context.view_layer.objects.active = metarig
        
        try:
            # 리기파이 리제네레이트 실행
            bpy.ops.pose.rigify_generate()
        except Exception as e:
            return False, f"Rigify generation failed: {str(e)}"

        # 새로운 리기파이 리그 찾기
        new_rigify_rig = context.active_object

        # 저장된 커스텀 위젯 정보 복원
        restore_custom_widgets(new_rigify_rig, stored_widgets)

        # 메타리그 비활성화
        metarig.hide_select = True
        metarig.hide_set(True)

        # 리기파이 리그 선택 및 활성화
        new_rigify_rig.select_set(True)
        context.view_layer.objects.active = new_rigify_rig

        # 포즈 모드로 전환
        bpy.ops.object.mode_set(mode='POSE')

        return True, new_rigify_rig
    except Exception as e:
        return False, str(e)

def create_shape_key_slider(context, bone, target_mesh, shape_key, custom_text="", use_head_parent=True, multiplier=17.0):
    """쉐이프 키 슬라이더 생성"""
    try:
        # 텍스트 내용 결정
        text_content = custom_text if custom_text else shape_key
        
        # Head 본에 Parent 설정
        if use_head_parent:
            rig = context.active_object
            if "head" in rig.pose.bones:
                # 현재 모드 저장
                current_mode = context.mode
                
                # Edit 모드로 전환
                bpy.ops.object.mode_set(mode='EDIT')
                
                # Edit Bone의 parent 설정
                edit_bone = rig.data.edit_bones[bone.name]
                head_edit_bone = rig.data.edit_bones["head"]
                edit_bone.parent = head_edit_bone
                
                # 원래 모드로 복귀
                bpy.ops.object.mode_set(mode=current_mode)
        
        # 드라이버 설정을 위한 shape key block 가져오기
        mesh_obj = bpy.data.objects[target_mesh]
        shape_key_block = mesh_obj.data.shape_keys.key_blocks[shape_key]

        # 위젯 생성 - shape_key_block 전달
        widget, error = create_shape_key_text_widget(
            context,
            f"WGT_{bone.name}",
            text_content,
            bone,
            shape_key_block
        )

        if not widget:
            return False, f"Failed to create widget: {error}"

        # 위젯 Head 본에 Child Of 콘스트레인트 추가
        if use_head_parent:
            rig = context.active_object
            if "head" in rig.pose.bones:
                head_bone = rig.pose.bones["head"]
                
                # 위젯 컬렉션의 모든 오브젝트에 콘스트레인트 추가
                widget_collection = widget.users_collection[0]
                for obj in widget_collection.objects:
                    constraint = obj.constraints.new('CHILD_OF')
                    constraint.target = rig
                    constraint.subtarget = "head"
                    constraint.use_scale_x = False
                    constraint.use_scale_y = False
                    constraint.use_scale_z = False

        # 드라이버 설정 - 기존 드라이버의 값 사용
        success, error = setup_shape_key_driver(
            context.active_object,
            bone.name,
            shape_key_block,
            'LOC_X',
            multiplier
        )

        return True, widget
    except Exception as e:
        return False, str(e)

def sync_bones_and_widgets(context, rigify_bone_name, widget_collection=None):
    """메타리그와 리기파이 리그 간의 본 동기화 및 위젯 업데이트를 처리하는 함수"""
    try:
        rigify_rig = context.scene.rigify_rig
        metarig = context.scene.metarig
        
        if not all([rigify_rig, metarig]):
            return False, "Rigify rig or metarig not found"

        # 현재 본과 오브젝트 정보 저장
        rigify_bone = rigify_rig.data.edit_bones.get(rigify_bone_name)
        if not rigify_bone:
            return False, f"Bone '{rigify_bone_name}' not found in rigify rig"

        # 본의 현재 변환값 저장
        head_pos = rigify_bone.head.copy()
        tail_pos = rigify_bone.tail.copy()
        roll_value = rigify_bone.roll

        # 메타리그 상태 저장
        was_hidden = metarig.hide_viewport
        was_hidden_select = metarig.hide_select
        was_hidden_get = metarig.hide_get()
        was_mirror_x = metarig.data.use_mirror_x  # 미러 설정 저장

        try:
            # 메타리그 완전히 활성화 및 미러 비활성화
            metarig.hide_viewport = False
            metarig.hide_select = False
            metarig.hide_set(False)
            metarig.data.use_mirror_x = False  # 미러 비활성화

            # 1. 리기파이 리그에서 오브젝트 모드로 전환
            bpy.ops.object.mode_set(mode='OBJECT')

            # 2. 메타리그로 전환
            bpy.ops.object.select_all(action='DESELECT')
            metarig.select_set(True)
            context.view_layer.objects.active = metarig

            # 3. 에딧 모드로 전환
            bpy.ops.object.mode_set(mode='EDIT')

            # 4. 본 트랜스폼 복사
            metarig_bone = metarig.data.edit_bones.get(rigify_bone_name)
            if metarig_bone:
                metarig_bone.head = head_pos
                metarig_bone.tail = tail_pos
                metarig_bone.roll = roll_value
            else:
                return False, f"Bone {rigify_bone_name} not found in metarig edit_bones"

            # 5. 오브젝트 모드로 전환
            bpy.ops.object.mode_set(mode='OBJECT')

            # 6. 쉐이프 컬렉션 처리
            if widget_collection and widget_collection.objects:
                # 실제 쉐이프 키 찾기
                actual_shape_key = None
                
                # 본 이름에서 쉐이프 키 이름 추출
                if rigify_bone_name.startswith("shape_key_ctrl_"):
                    shape_key_name = rigify_bone_name[len("shape_key_ctrl_"):]
                    
                    # 모든 메쉬 오브젝트에서 쉐이프 키 찾기
                    for obj in bpy.data.objects:
                        if obj.type == 'MESH' and obj.data.shape_keys:
                            for key in obj.data.shape_keys.key_blocks:
                                if key.name == shape_key_name:
                                    actual_shape_key = key
                                    break
                            if actual_shape_key:
                                break

                # 트랜스폼 계산
                bone_matrix = metarig.matrix_world @ metarig.pose.bones[rigify_bone_name].matrix
                transforms = calculate_widget_transforms(
                    bone_matrix,
                    metarig.pose.bones[rigify_bone_name].length,
                    actual_shape_key
                )

                # 위젯 오브젝트에 적용
                for obj in widget_collection.objects:
                    if obj.name.startswith('TEXT_'):
                        apply_widget_transforms(obj, transforms, 'TEXT')
                    elif obj.name.startswith('SLIDE_'):
                        apply_widget_transforms(obj, transforms, 'SLIDE')
                    elif obj.name.startswith('WGT_'):
                        apply_widget_transforms(obj, transforms, 'WGT')

            # 7. 리기파이 리그로 돌아가기
            bpy.ops.object.select_all(action='DESELECT')
            rigify_rig.select_set(True)
            context.view_layer.objects.active = rigify_rig
            bpy.ops.object.mode_set(mode='EDIT')

            return True, "Sync completed successfully"

        finally:
            # 메타리그 상태 복원
            metarig.hide_viewport = was_hidden
            metarig.hide_select = was_hidden_select
            metarig.hide_set(was_hidden_get)
            metarig.data.use_mirror_x = was_mirror_x  # 미러 설정 복원

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error during sync: {str(e)}"
    