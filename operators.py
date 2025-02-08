import bpy
import math
import mathutils
from . import utils
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty, PointerProperty

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
            template_collection = utils.ensure_template_collection()
            
            # 템플릿 오브젝트 확인 및 생성
            utils.create_templates(template_collection)
            
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
        text_obj, error = utils.create_shape_key_text_widget(
            context,
            f"WGT_{self.shape_key}",  # WGT_ 접두어 사용
            self.shape_key,
            None,
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
        ]
    ) # type: ignore

    target_shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to connect",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, context.active_object).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else []
    ) # type: ignore

    shape_collection: EnumProperty(
        name="Shape Collection",
        description="Select collection containing shape objects",
        items=lambda self, context: [
            (col.name, col.name, "")
            for col in bpy.data.collections
        ]
    ) # type: ignore

    transform_type: EnumProperty(
        name="Transform Type",
        description="Type of transform to control the shape key",
        items=utils.TRANSFORM_ITEMS,
        default='LOC_X'
    ) # type: ignore

    multiplier: FloatProperty(
        name="Influence",
        description="Driver influence multiplier (higher value = stronger effect)",
        default=30,
        min=0.0,
        max=100.0,
        step=1.0,
        precision=1
    ) # type: ignore
    
    @classmethod
    def poll(cls, context):
        # 에딧 모드나 포즈 모드에서 본이 선택되었는지 확인
        if context.mode not in {'EDIT_ARMATURE', 'POSE'}:
            return False
            
        return (context.mode == 'EDIT_ARMATURE' and context.active_bone) or \
               (context.mode == 'POSE' and context.active_pose_bone)
    
    def invoke(self, context, event):
        # 현재 본 이름 가져오기
        bone_name = context.active_bone.name if context.mode == 'EDIT_ARMATURE' else context.active_pose_bone.name
        
        # 'shape_key_ctrl_' 접두어가 있는 경우 제거하여 쉐이프 키 이름 추출
        shape_key_name = bone_name.replace('shape_key_ctrl_', '') if bone_name.startswith('shape_key_ctrl_') else bone_name
        
        # 추출된 쉐이프 키 이름으로 메쉬 찾기
        found = False
        for obj in context.scene.objects:
            if obj.type == 'MESH' and obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks[1:]:  # Basis 제외
                    if key.name == shape_key_name:
                        self.target_mesh = obj.name
                        self.target_shape_key = key.name
                        found = True
                        break
            if found:
                break

        # 연결된 쉐이프 키가 없는 경우 첫 번째 사용 가능한 메쉬와 쉐이프 키 선택
        if not self.target_mesh:
            for obj in context.scene.objects:
                if (obj.type == 'MESH' and obj.data.shape_keys):
                    self.target_mesh = obj.name
                    if obj.data.shape_keys.key_blocks:
                        self.target_shape_key = obj.data.shape_keys.key_blocks[1].name  # 0은 Basis
                    break

        # WGT_shape_key_ctrl_로 시작하는 컬렉션 찾기
        widgets_collection = bpy.data.collections.get("Widgets")
        if widgets_collection:
            for col in widgets_collection.children:
                if col.name.startswith("WGT_shape_key_ctrl_"):
                    if shape_key_name in col.name.replace("WGT_shape_key_ctrl_", ""):
                        self.shape_collection = col.name
                        break
        
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_mesh")
        if self.target_mesh:
            layout.prop(self, "target_shape_key")
        layout.prop(self, "shape_collection")
        layout.prop(self, "transform_type")
        layout.prop(self, "multiplier", slider=True)
    
    def execute(self, context):
        armature = context.active_object
        
        # 현재 모드에 따라 본 이름 가져오기
        if context.mode == 'EDIT_ARMATURE':
            bone_name = context.active_bone.name
            edit_bone = context.active_bone
            pose_bone = armature.pose.bones[bone_name]
        else:
            bone_name = context.active_pose_bone.name
            pose_bone = context.active_pose_bone
            edit_bone = None
        
        target_mesh = bpy.data.objects.get(self.target_mesh)
        if not target_mesh:
            self.report({'ERROR'}, "Selected mesh not found!")
            return {'CANCELLED'}
        
        try:
            # 1. 쉐이프 키 드라이버 설정
            if self.target_shape_key in target_mesh.data.shape_keys.key_blocks:
                shape_key = target_mesh.data.shape_keys.key_blocks[self.target_shape_key]
                
                # Widgets 컬렉션 확인 또는 생성
                widgets_collection = bpy.data.collections.get("Widgets")
                if not widgets_collection:
                    widgets_collection = bpy.data.collections.new("Widgets")
                    context.scene.collection.children.link(widgets_collection)
                
                # 2. 컬렉션 처리
                if self.shape_collection:
                    # 기존 컬렉션 사용
                    widget_collection = bpy.data.collections.get(self.shape_collection)
                    if not widget_collection:
                        self.report({'ERROR'}, "Selected collection not found!")
                        return {'CANCELLED'}
                else:
                    # 새 위젯과 컬렉션 생성
                    widget, error = utils.create_shape_key_text_widget(
                        context,
                        f"WGT_{bone_name}",
                        self.target_shape_key,
                        pose_bone,
                        shape_key
                    )
                    
                    if not widget:
                        self.report({'ERROR'}, f"Failed to create widget: {error}")
                        return {'CANCELLED'}
                    
                    # 새 컬렉션 생성 및 Widgets 컬렉션에 추가
                    widgets_collection.children.link(widget_collection)
                    
                    # 위젯을 새 컬렉션으로 이동
                    if widget.name in context.scene.collection.objects:
                        context.scene.collection.objects.unlink(widget)
                    widget_collection.objects.link(widget)
                
                # 3. 드라이버 설정
                success, error_message = utils.setup_shape_key_driver(
                    armature,
                    bone_name,
                    shape_key,
                    self.transform_type,
                    self.multiplier
                )
                
                if not success:
                    self.report({'ERROR'}, f"Error setting up driver: {error_message}")
                    return {'CANCELLED'}
                
                self.report({'INFO'}, f"Successfully connected bone '{bone_name}' to shape key '{self.target_shape_key}'")
                
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
                # 첫 번째 사용 가능한 쉐이프 키를 선택
                mesh_obj = bpy.data.objects.get(self.target_mesh)
                if mesh_obj and mesh_obj.data.shape_keys:
                    shape_keys = mesh_obj.data.shape_keys.key_blocks
                    if len(shape_keys) > 1:  # Basis 제외
                        self.target_shape_key = shape_keys[1].name
                
                # 본 이름 업데이트
                self.bone_name = "shape_key_ctrl"
                self.suggested_name = "shape_key_ctrl"
        except Exception as e:
            print(f"Error updating mesh selection: {str(e)}")

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
        items=utils.TRANSFORM_ITEMS,
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
        default=30,
        min=0.0,
        max=100.0,
        step=1.0,
        precision=1
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
                utils.setup_bone_constraints(pose_bone, self.transform_type)

                # 드라이버 연결이 선택된 경우
                if self.connect_driver and self.target_mesh and self.target_shape_key:
                    target_mesh = bpy.data.objects.get(self.target_mesh)
                    if target_mesh and target_mesh.data.shape_keys:
                        shape_key = target_mesh.data.shape_keys.key_blocks.get(self.target_shape_key)
                        if shape_key:
                            # 리기파이 리그 확인
                            rig = context.scene.rigify_rig
                            if rig:
                                success, error_message = utils.setup_shape_key_driver(
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
        
class EDIT_OT_sync_metarig_bone(Operator):
    """Sync metarig bone with rigify bone"""
    bl_idname = "edit.sync_metarig_bone"
    bl_label = "Sync with Metarig"
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

    target_shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to connect",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, context.active_object).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else []
    ) # type: ignore

    shape_collection: EnumProperty(
        name="Shape Collection",
        description="Select collection containing shape objects",
        items=lambda self, context: [
            (col.name, col.name, "")
            for col in bpy.data.collections.get("Widgets", []).children
        ]
    ) # type: ignore

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_ARMATURE' and 
                context.active_bone and 
                context.scene.metarig and 
                context.scene.rigify_rig and
                context.active_object == context.scene.rigify_rig)

    def invoke(self, context, event):
        # 현재 본 이름 가져오기
        bone_name = context.active_bone.name
        
        # 'shape_key_ctrl_' 접두어가 있는 경우 제거하여 쉐이프 키 이름 추출
        shape_key_name = bone_name.replace('shape_key_ctrl_', '') if bone_name.startswith('shape_key_ctrl_') else bone_name
        
        # 쉐이프 키 이름으로 메쉬와 쉐이프 키 찾기
        found = False
        for obj in context.scene.objects:
            if obj.type == 'MESH' and obj.data.shape_keys:
                for key in obj.data.shape_keys.key_blocks[1:]:  # Basis 제외
                    if key.name == shape_key_name:
                        self.target_mesh = obj.name
                        self.target_shape_key = key.name
                        found = True
                        break
            if found:
                break

        # 연결된 쉐이프 키가 없는 경우 첫 번째 사용 가능한 메쉬와 쉐이프 키 선택
        if not self.target_mesh:
            for obj in context.scene.objects:
                if (obj.type == 'MESH' and obj.data.shape_keys):
                    self.target_mesh = obj.name
                    if obj.data.shape_keys.key_blocks:
                        self.target_shape_key = obj.data.shape_keys.key_blocks[1].name  # 0은 Basis
                    break
        
        # WGT_shape_key_ctrl_로 시작하는 컬렉션 찾기
        widgets_collection = bpy.data.collections.get("Widgets")
        if widgets_collection:
            for col in widgets_collection.children:
                if col.name.startswith("WGT_shape_key_ctrl_"):
                    if shape_key_name in col.name.replace("WGT_shape_key_ctrl_", ""):
                        self.shape_collection = col.name
                        break
        
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_mesh")
        if self.target_mesh:
            layout.prop(self, "target_shape_key")
        layout.prop(self, "shape_collection")

    def execute(self, context):
        # 현재 본과 오브젝트 정보 저장
        rigify_bone = context.active_bone
        bone_name = rigify_bone.name
        rigify_rig = context.scene.rigify_rig
        metarig = context.scene.metarig
        
        # 선택된 컬렉션과 쉐이프 키 가져오기
        shape_collection = bpy.data.collections.get(self.shape_collection)
        target_mesh = bpy.data.objects.get(self.target_mesh)
        
        if target_mesh and target_mesh.data.shape_keys:
            shape_key = target_mesh.data.shape_keys.key_blocks.get(self.target_shape_key)
        else:
            shape_key = None
        
        # 본의 현재 변환값 저장
        head_pos = rigify_bone.head.copy()
        tail_pos = rigify_bone.tail.copy()
        roll_value = rigify_bone.roll
        
        try:
            # 메타리그 상태 저장
            was_hidden = metarig.hide_viewport
            was_hidden_select = metarig.hide_select
            was_hidden_get = metarig.hide_get()
            
            # 메타리그 완전히 활성화
            metarig.hide_viewport = False
            metarig.hide_select = False
            metarig.hide_set(False)
            
            # 1. 리기파이 리그에서 오브젝트 모드로 전환
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # 2. 메타리그로 전환
            bpy.ops.object.select_all(action='DESELECT')
            metarig.select_set(True)
            context.view_layer.objects.active = metarig
            
            # 3. 에딧 모드로 전환
            bpy.ops.object.mode_set(mode='EDIT')
            
            # 4. 본 트랜스폼 복사
            metarig_bone = metarig.data.edit_bones.get(bone_name)
            if metarig_bone:
                metarig_bone.head = head_pos
                metarig_bone.tail = tail_pos
                metarig_bone.roll = roll_value
            else:
                self.report({'ERROR'}, f"Bone {bone_name} not found in metarig edit_bones")
                return {'CANCELLED'}
            
            # 5. 오브젝트 모드로 전환
            bpy.ops.object.mode_set(mode='OBJECT')
            
            # 6. 쉐이프 컬렉션 처리
            if shape_collection and shape_collection.objects:
                # 트랜스폼 계산
                bone_matrix = metarig.matrix_world @ metarig.pose.bones[bone_name].matrix
                transforms = utils.calculate_widget_transforms(
                    bone_matrix,
                    metarig.pose.bones[bone_name].length,
                    shape_key  # 선택한 쉐이프 키 전달
                )
                
                # 위젯 오브젝트에 적용
                for obj in shape_collection.objects:
                    if obj.name.startswith('TEXT_'):
                        utils.apply_widget_transforms(obj, transforms, 'TEXT')
                    elif obj.name.startswith('SLIDE_'):
                        utils.apply_widget_transforms(obj, transforms, 'SLIDE')
                    elif obj.name.startswith('WGT_'):
                        utils.apply_widget_transforms(obj, transforms, 'WGT')
            
            # 7. 리기파이 리그로 돌아가기
            bpy.ops.object.select_all(action='DESELECT')
            rigify_rig.select_set(True)
            context.view_layer.objects.active = rigify_rig
            bpy.ops.object.mode_set(mode='EDIT')
            
            # 메타리그 원래 상태로 복원
            metarig.hide_viewport = was_hidden
            metarig.hide_select = was_hidden_select
            metarig.hide_set(was_hidden_get)
            
            self.report({'INFO'}, f"Successfully synced bone: {bone_name}")
            return {'FINISHED'}
            
        except Exception as e:
            # 에러 발생 시 메타리그 상태 복원
            if 'was_hidden' in locals():
                metarig.hide_viewport = was_hidden
                metarig.hide_select = was_hidden_select
                metarig.hide_set(was_hidden_get)
            
            print(f"\nError details: {str(e)}")
            print(f"Current mode: {context.mode}")
            print(f"Active object: {context.active_object.name if context.active_object else 'None'}")
            
            self.report({'ERROR'}, f"Error syncing bones: {str(e)}")
            return {'CANCELLED'}
        
class EDIT_OT_delete_shape_key_bone(Operator):
    """Delete shape key bone and related objects"""
    bl_idname = "edit.delete_shape_key_bone"
    bl_label = "Delete Shape Key Bone"
    bl_description = "Delete selected bone from both rigs and its shape collection"
    bl_options = {'REGISTER', 'UNDO'}

    def remove_selected_drivers(self, context, bone_name):
        """선택된 드라이버 제거"""
        removed_count = 0
        selected_driver = self.shape_key_drivers

        obj = bpy.data.objects.get(self.target_mesh)
        if obj and obj.data.shape_keys and obj.data.shape_keys.animation_data:
            shape_keys = obj.data.shape_keys
            
            # 선택된 쉐이프 키의 드라이버 제거
            data_path = f'key_blocks["{selected_driver}"].value'
            try:
                # 드라이버 제거
                shape_keys.driver_remove(data_path)
                removed_count += 1
                
                # Basis 쉐이프키 선택
                obj.active_shape_key_index = 0
                        
            except:
                pass
                        
        return removed_count

    delete_collection: BoolProperty(
        name="Delete Widget Collection",
        description="Delete associated widget collection",
        default=True
    ) # type: ignore

    widget_collection: EnumProperty(
        name="Widget Collection",
        description="Select widget collection to delete",
        items=lambda self, context: [
            (col.name, col.name, "")
            for col in bpy.data.collections.get("Widgets", {}).children
        ] if self.delete_collection else []
    ) # type: ignore

    delete_drivers: BoolProperty(
        name="Delete Shape Key Drivers",
        description="Delete associated shape key drivers",
        default=True
    ) # type: ignore

    target_mesh: EnumProperty(
        name="Target Mesh",
        description="Select mesh containing shape key drivers",
        items=lambda self, context: utils.get_meshes_with_drivers(self, context)
    ) # type: ignore

    shape_key_drivers: EnumProperty(
        name="Shape Key Drivers",
        description="Select shape key drivers to delete",
        items=lambda self, context: utils.get_shape_key_drivers(self, context)
    ) # type: ignore

    @classmethod
    def poll(cls, context):
        if context.mode not in {'EDIT_ARMATURE', 'POSE'}:
            return False
            
        if not (context.scene.metarig and context.scene.rigify_rig):
            return False
            
        if context.mode == 'EDIT_ARMATURE':
            return (context.active_bone and 
                   context.active_object == context.scene.rigify_rig)
        else:  # POSE
            return (context.active_pose_bone and 
                   context.active_object == context.scene.rigify_rig)

    def invoke(self, context, event):
        # 기본 컬렉션 이름 설정
        if context.mode == 'EDIT_ARMATURE':
            bone_name = context.active_bone.name
        else:  # POSE
            bone_name = context.active_pose_bone.name
            
        # Widgets 컬렉션이 있는지 확인
        widgets_collection = bpy.data.collections.get("Widgets")
        if widgets_collection and widgets_collection.children:
            # WGT_로 시작하는 컬렉션 중에서 본 이름이 포함된 것을 찾기
            for col in widgets_collection.children:
                if bone_name in col.name:
                    self.widget_collection = col.name
                    break
        
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        
        # 드라이버 삭제 옵션
        row = layout.row()
        row.prop(self, "delete_drivers")
        
        # 드라이버 선택 (delete_drivers가 True일 때만)
        if self.delete_drivers:
            box = layout.box()
            box.label(text="Select Drivers to Delete:", icon='DRIVER')
            
            # 메쉬 선택
            box.prop(self, "target_mesh")
            
            # 선택된 메쉬의 쉐이프 키 드라이버 선택
            if self.target_mesh:
                box.prop(self, "shape_key_drivers")
        
        # 컬렉션 삭제 옵션
        row = layout.row()
        row.prop(self, "delete_collection")
        
        # 컬렉션 선택 (delete_collection이 True일 때만)
        if self.delete_collection:
            row = layout.row()
            row.prop(self, "widget_collection")
        
        # 경고 메시지
        box = layout.box()
        box.label(text="Warning: This operation cannot be undone!", icon='ERROR')
        if self.delete_drivers:
            box.label(text="Selected shape key drivers will be deleted")
        if self.delete_collection:
            box.label(text="Selected widget collection will be deleted")

    def execute(self, context):
        rigify_rig = context.scene.rigify_rig
        metarig = context.scene.metarig
        
        # 현재 선택된 본 이름 가져오기
        if context.mode == 'EDIT_ARMATURE':
            bone_name = context.active_bone.name
        else:  # POSE
            bone_name = context.active_pose_bone.name
            
        try:
            removed_drivers = 0
            removed_objects = 0

            # 1. 선택된 드라이버 제거
            if self.delete_drivers:
                removed_drivers = self.remove_selected_drivers(context, bone_name)
            
            # 2. 선택된 위젯 컬렉션 삭제
            if self.delete_collection and self.widget_collection:
                collection = bpy.data.collections.get(self.widget_collection)
                if collection:
                    removed_objects = len(collection.objects)
                    for obj in collection.objects:
                        bpy.data.objects.remove(obj, do_unlink=True)
                    bpy.data.collections.remove(collection)
            
            # 3. 메타리그의 본 삭제
            # 메타리그 상태 저장
            was_hidden = metarig.hide_viewport
            was_hidden_select = metarig.hide_select
            was_hidden_get = metarig.hide_get()
            
            # 메타리그 활성화
            metarig.hide_viewport = False
            metarig.hide_select = False
            metarig.hide_set(False)
            
            # 현재 모드와 선택 상태 저장
            current_active = context.active_object
            current_mode = context.mode
            
            # 메타리그로 전환
            bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = metarig
            bpy.ops.object.mode_set(mode='EDIT')
            
            # 본 삭제
            if bone_name in metarig.data.edit_bones:
                metarig_bone = metarig.data.edit_bones[bone_name]
                metarig.data.edit_bones.remove(metarig_bone)
            
            # 원래 상태로 복원
            bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = current_active
            if current_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode=current_mode)
            
            # 메타리그 상태 복원
            metarig.hide_viewport = was_hidden
            metarig.hide_select = was_hidden_select
            metarig.hide_set(was_hidden_get)
            
            # 4. 리기파이 리그의 본 삭제
            if context.mode == 'EDIT_ARMATURE':
                rigify_bone = rigify_rig.data.edit_bones[bone_name]
                rigify_rig.data.edit_bones.remove(rigify_bone)
            else:  # POSE
                # 에딧 모드로 전환하여 본 삭제
                bpy.ops.object.mode_set(mode='EDIT')
                rigify_bone = rigify_rig.data.edit_bones[bone_name]
                rigify_rig.data.edit_bones.remove(rigify_bone)
                bpy.ops.object.mode_set(mode='POSE')
            
            # 결과 메시지 생성
            message = f"Deleted bone: {bone_name}"
            if self.delete_drivers and removed_drivers > 0:
                message += f", {removed_drivers} drivers"
            if self.delete_collection and removed_objects > 0:
                message += f", {removed_objects} widget objects"
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error deleting bone: {str(e)}")
            return {'CANCELLED'}
        
class ARMATURE_OT_rigify_regenerate_with_widgets(Operator):
    """Regenerate rigify rig while preserving custom widgets"""
    bl_idname = "armature.rigify_regenerate_with_widgets"
    bl_label = "Regenerate Rigify (Preserve Widgets)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            # 현재 리기파이 리그의 커스텀 위젯 정보 저장
            rigify_rig = context.scene.rigify_rig
            stored_widgets = utils.store_custom_widgets(rigify_rig)

            # 오브젝트 모드로 전환
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            # 메타리그 선택 및 활성화
            metarig = context.scene.metarig
            if not metarig:
                self.report({'ERROR'}, "Metarig not found")
                return {'CANCELLED'}

            metarig.hide_select = False
            metarig.hide_set(False)
            metarig.select_set(True)
            context.view_layer.objects.active = metarig
            
            try:
                # 리기파이 리제네레이트 실행
                bpy.ops.pose.rigify_generate()
            except Exception as e:
                self.report({'ERROR'}, f"Rigify generation failed: {str(e)}")
                return {'CANCELLED'}

            # 새로운 리기파이 리그 찾기
            new_rigify_rig = context.active_object

            # 저장된 커스텀 위젯 정보 복원
            utils.restore_custom_widgets(new_rigify_rig, stored_widgets)

            # 메타리그 비활성화
            metarig.hide_select = True
            metarig.hide_set(True)

            # 리기파이 리그 선택 및 활성화
            new_rigify_rig.select_set(True)
            context.view_layer.objects.active = new_rigify_rig

            # 포즈 모드로 전환
            bpy.ops.object.mode_set(mode='POSE')

            self.report({'INFO'}, "Rigify regenerated and widgets preserved")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error during regeneration: {str(e)}")
            return {'CANCELLED'}

classes = (
    OBJECT_OT_text_input_dialog,
    OBJECT_OT_create_shape_key_text,
    OBJECT_OT_apply_shape_key_to_bone,
    OBJECT_OT_add_shape_key_bone,
    OBJECT_OT_show_select_mesh_popup,
    EDIT_OT_sync_metarig_bone,
    EDIT_OT_delete_shape_key_bone,
    ARMATURE_OT_rigify_regenerate_with_widgets,
)