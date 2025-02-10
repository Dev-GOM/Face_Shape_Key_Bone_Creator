import bpy
import math
import mathutils

from . import properties
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

class OBJECT_OT_add_shape_key_bone(Operator, properties.ShapeKeyCommonProperties):
    """Add new bone for shape key control to metarig"""
    bl_idname = "object.add_shape_key_bone"
    bl_label = "Add Shape Key Bone"
    bl_options = {'REGISTER', 'UNDO'}

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
                    break
        else:
            obj = bpy.data.objects.get(self.target_mesh)
            if obj and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 1:
                shape_key_name = obj.data.shape_keys.key_blocks[1].name
                self.target_shape_key = shape_key_name
                new_name = f"shape_key_ctrl_{shape_key_name}"
                self.suggested_name = new_name
                self.bone_name = new_name
        
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
                    pose_bone.rigify_parameters.make_deform = False  # deform을 False로 변경
                    pose_bone.rigify_parameters.widget_type = 'bone'
                    pose_bone.rigify_parameters.generate = False  # generate 옵션 추가

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
        
class EDIT_OT_sync_metarig_bone(Operator, properties.ShapeKeyCommonProperties):
    """Sync metarig bone with rigify bone"""
    bl_idname = "edit.sync_metarig_bone"
    bl_label = "Sync with Metarig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_ARMATURE' and 
                context.scene.metarig and 
                context.scene.rigify_rig and
                context.active_object == context.scene.rigify_rig)    

    def invoke(self, context, event):
        # 선택된 본들 가져오기
        selected_bones = [bone.name for bone in context.selected_bones]
        
        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        # 선택된 본들 정보 저장
        self.selected_bones = ",".join(selected_bones)
        
        # 여러 본이 선택된 경우
        if len(selected_bones) > 1:
            self.show_confirmation = True
            
            # 선택된 모든 본에 대한 정보 수집
            self.bone_info = []
            for bone_name in selected_bones:
                info = {'bone_name': bone_name}
                
                # 위젯 컬렉션 찾기
                widgets_collection = bpy.data.collections.get("Widgets")
                if widgets_collection:
                    for col in widgets_collection.children:
                        if bone_name in col.name:
                            info['widget_collection'] = col
                            break
                
                # 메쉬와 쉐이프 키 찾기
                if bone_name.startswith("shape_key_ctrl_"):
                    shape_key_name = bone_name[len("shape_key_ctrl_"):]
                    for obj in bpy.data.objects:
                        if obj.type == 'MESH' and obj.data.shape_keys:
                            for key in obj.data.shape_keys.key_blocks:
                                if key.name == shape_key_name:
                                    info['mesh'] = obj.name
                                    info['shape_key'] = key.name
                                    break
                            if 'mesh' in info:
                                break
                
                self.bone_info.append(info)
            
            return context.window_manager.invoke_props_dialog(self, width=400)
        
        # 단일 본 선택시
        bone_name = selected_bones[0]
        
        # 연결된 메쉬와 쉐이프 키 찾기
        if bone_name.startswith("shape_key_ctrl_"):
            shape_key_name = bone_name[len("shape_key_ctrl_"):]
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and obj.data.shape_keys:
                    for key in obj.data.shape_keys.key_blocks:
                        if key.name == shape_key_name:
                            self.target_mesh = obj.name
                            self.target_shape_key = key.name
                            break
                    if self.target_mesh:
                        break

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        if self.show_confirmation:
            # 여러 본이 선택된 경우의 UI
            box = layout.box()
            box.label(text="Selected bones to sync:", icon='BONE_DATA')
            for bone_name in self.selected_bones.split(","):
                row = box.row()
                row.label(text=bone_name)

            # 경고 메시지
            box = layout.box()
            box.label(text="This will sync all selected bones with metarig", icon='INFO')
        else:
            # 단일 본 선택시의 UI
            box = layout.box()
            box.label(text="Sync Settings:", icon='SETTINGS')
            
            # 메쉬 선택
            row = box.row()
            row.prop(self, "target_mesh")
            
            # 쉐이프 키 선택
            if self.target_mesh:
                row = box.row()
                row.prop(self, "target_shape_key")
            
            # 본 정보
            row = box.row()
            row.label(text="Selected Bone:")
            row.label(text=context.active_bone.name)

    def sync_single_bone(self, context, bone_name, widget_collection=None):
        """단일 본 동기화 처리"""
        try:
            # 본 동기화 실행
            success, message = utils.sync_bones_and_widgets(
                context,
                bone_name,
                widget_collection
            )

            if not success:
                self.report({'WARNING'}, f"Error syncing bone {bone_name}: {message}")
                return False

            return True

        except Exception as e:
            self.report({'WARNING'}, f"Error syncing bone {bone_name}: {str(e)}")
            return False

    def execute(self, context):
        # 여러 본이 선택된 경우
        if self.show_confirmation:
            success_count = 0
            for info in self.bone_info:
                widget_collection = info.get('widget_collection')
                if self.sync_single_bone(context, info['bone_name'], widget_collection):
                    success_count += 1
            
            self.report({'INFO'}, f"Successfully synced {success_count} of {len(self.bone_info)} bones")
            return {'FINISHED'}
        
        # 단일 본 선택시
        bone_name = context.active_bone.name
        # 위젯 컬렉션 찾기
        widget_collection = None
        widgets_collection = bpy.data.collections.get("Widgets")
        if widgets_collection:
            for col in widgets_collection.children:
                if bone_name in col.name:
                    widget_collection = col
                    break
                    
        if self.sync_single_bone(context, bone_name, widget_collection):
            self.report({'INFO'}, f"Successfully synced bone: {bone_name}")
            return {'FINISHED'}
                
        return {'CANCELLED'}
        
class EDIT_OT_delete_shape_key_bone(Operator, properties.ShapeKeyCommonProperties):
    bl_idname = "edit.delete_shape_key_bone"
    bl_label = "Delete Shape Key Bone"
    bl_description = "Delete selected bone from both rigs and its shape collection"
    bl_options = {'REGISTER', 'UNDO'}

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
        # 선택된 본들 가져오기
        selected_bones = []
        if context.mode == 'EDIT_ARMATURE':
            selected_bones = [bone.name for bone in context.selected_bones]
        else:  # POSE
            selected_bones = [bone.name for bone in context.selected_pose_bones]

        if not selected_bones:
            self.report({'ERROR'}, "No bones selected")
            return {'CANCELLED'}

        # 관련 정보 수집
        collections_info = []
        drivers_info = []
        
        for bone_name in selected_bones:
            # 위젯 컬렉션 찾기
            widgets_collection = bpy.data.collections.get("Widgets")
            if widgets_collection and widgets_collection.children:
                for col in widgets_collection.children:
                    if bone_name in col.name:
                        collections_info.append((bone_name, col.name))
                        break
            
            # 드라이버 찾기
            if bone_name.startswith("shape_key_ctrl_"):
                shape_key_name = bone_name[len("shape_key_ctrl_"):]
                for obj in bpy.data.objects:
                    if obj.type == 'MESH' and obj.data.shape_keys:
                        for key in obj.data.shape_keys.key_blocks:
                            if key.name == shape_key_name:
                                drivers_info.append((bone_name, obj.name, key.name))
                                break

        # 찾은 정보 저장
        self.selected_bones = ",".join(selected_bones)
        self.selected_collections = ";".join([f"{bone}:{col}" for bone, col in collections_info])
        self.selected_drivers = ";".join([f"{bone}:{mesh}:{key}" for bone, mesh, key in drivers_info])
        self.show_confirmation = True

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        
        # 선택된 본들 표시
        box = layout.box()
        box.label(text="Selected bones to delete:", icon='BONE_DATA')
        for bone_name in self.selected_bones.split(","):
            row = box.row()
            row.label(text=bone_name)

        # 삭제될 위젯 컬렉션 표시
        if self.selected_collections:
            box = layout.box()
            box.label(text="Widget collections to delete:", icon='OUTLINER_COLLECTION')
            for info in self.selected_collections.split(";"):
                if info:
                    bone, col = info.split(":")
                    row = box.row()
                    row.label(text=f"{col}")

        # 삭제될 드라이버 표시
        if self.selected_drivers:
            box = layout.box()
            box.label(text="Drivers to delete:", icon='DRIVER')
            for info in self.selected_drivers.split(";"):
                if info:
                    bone, mesh, key = info.split(":")
                    row = box.row()
                    row.label(text=f"{mesh} -> {key}")

        # 옵션
        row = layout.row()
        row.prop(self, "delete_drivers")
        row = layout.row()
        row.prop(self, "delete_collection")

        # 경고 메시지
        box = layout.box()
        box.label(text="Warning: This operation cannot be undone!", icon='ERROR')

    def delete_single_bone(self, context, bone_name):
        rigify_rig = context.scene.rigify_rig
        metarig = context.scene.metarig
            
        try:
            removed_drivers = 0
            removed_objects = 0

            # 1. 드라이버 제거
            if self.delete_drivers and self.selected_drivers:
                for info in self.selected_drivers.split(";"):
                    if info:
                        driver_bone, mesh_name, key_name = info.split(":")
                        if driver_bone == bone_name:
                            obj = bpy.data.objects.get(mesh_name)
                            if obj and obj.data.shape_keys:
                                shape_keys = obj.data.shape_keys
                                data_path = f'key_blocks["{key_name}"].value'
                                shape_keys.driver_remove(data_path)
                                removed_drivers += 1
                                obj.active_shape_key_index = 0

            # 2. 위젯 컬렉션 삭제
            if self.delete_collection and self.selected_collections:
                for info in self.selected_collections.split(";"):
                    if info:
                        col_bone, col_name = info.split(":")
                        if col_bone == bone_name:
                            collection = bpy.data.collections.get(col_name)
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
            was_mirror_x = metarig.data.use_mirror_x  # 미러 설정 저장
            
            try:
                # 메타리그 활성화 및 미러 비활성화
                metarig.hide_viewport = False
                metarig.hide_select = False
                metarig.hide_set(False)
                metarig.data.use_mirror_x = False  # 미러 비활성화
                
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
                
            finally:
                # 메타리그 상태 복원
                metarig.hide_viewport = was_hidden
                metarig.hide_select = was_hidden_select
                metarig.hide_set(was_hidden_get)
                metarig.data.use_mirror_x = was_mirror_x  # 미러 설정 복원

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
            return True

        except Exception as e:
            self.report({'ERROR'}, f"Error deleting bone: {str(e)}")
            return False

    def execute(self, context):
        # 여러 본이 선택된 경우
        if self.show_confirmation:
            selected_bones = self.selected_bones.split(",")
            
            for bone_name in selected_bones:
                # 각 본에 대해 삭제 프로세스 실행
                try:
                    self.delete_single_bone(context, bone_name)
                except Exception as e:
                    self.report({'WARNING'}, f"Error deleting bone {bone_name}: {str(e)}")
                    continue
            
            self.report({'INFO'}, f"Successfully deleted {len(selected_bones)} bones")
            return {'FINISHED'}
        
        # 단일 본 선택시
        if context.mode == 'EDIT_ARMATURE':
            bone_name = context.active_bone.name
        else:  # POSE
            bone_name = context.active_pose_bone.name
        
        if self.delete_single_bone(context, bone_name):
            return {'FINISHED'}
        return {'CANCELLED'}
        
class ARMATURE_OT_rigify_regenerate_with_widgets(Operator):
    """Regenerate rigify rig while preserving custom widgets"""
    bl_idname = "armature.rigify_regenerate_with_widgets"
    bl_label = "Regenerate Rigify (Preserve Widgets)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            success, result = utils.regenerate_rigify_with_widgets(context)
            
            if success:
                self.report({'INFO'}, "Rigify regenerated and widgets preserved")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, str(result))
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error during regeneration: {str(e)}")
            return {'CANCELLED'}
        
class OBJECT_OT_create_multiple_shape_key_bones(Operator, properties.ShapeKeyCommonProperties):
    bl_idname = "object.create_multiple_shape_key_bones"
    bl_label = "Create Multiple Shape Key Bones"
    bl_options = {'REGISTER', 'UNDO'}

    multiplier: FloatProperty(
        name="Influence",
        description="Driver influence strength multiplier",
        default=17.0,
        min=0.0,
        max=100.0,
        step=1.0,
        precision=1
    ) # type: ignore

    use_head_parent: BoolProperty(
        name="Parent to Head",
        description="Add parent to Rigify head bone",
        default=False
    ) # type: ignore

    @classmethod
    def poll(cls, context):
        if context.mode != 'EDIT_ARMATURE':
            return False
        if not context.active_bone:
            return False
        if not context.scene.metarig:
            return False
        if not context.scene.rigify_rig:
            return False
        return True

    def invoke(self, context, event):
        if not context.scene.metarig:
            self.report({'ERROR'}, "Metarig not found")
            return {'CANCELLED'}
        
        if not context.scene.rigify_rig:
            self.report({'ERROR'}, "Rigify rig not found")
            return {'CANCELLED'}

        meshes_with_shape_keys = [
            obj for obj in bpy.data.objects
            if obj.type == 'MESH' and obj.data.shape_keys
        ]

        if not meshes_with_shape_keys:
            self.report({'ERROR'}, "No meshes with shape keys found")
            return {'CANCELLED'}

        if not self.target_mesh:
            self.target_mesh = meshes_with_shape_keys[0].name

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Target Settings:", icon='MESH_DATA')
        col = box.column()
        col.prop(self, "target_mesh")
        
        if self.target_mesh:
            mesh_obj = bpy.data.objects.get(self.target_mesh)
            if mesh_obj and mesh_obj.data.shape_keys:
                available_keys = []
                for k in mesh_obj.data.shape_keys.key_blocks[1:]:
                    has_driver = False
                    if (mesh_obj.data.shape_keys.animation_data and 
                        mesh_obj.data.shape_keys.animation_data.drivers):
                        for dr in mesh_obj.data.shape_keys.animation_data.drivers:
                            if dr.data_path == f'key_blocks["{k.name}"].value':
                                has_driver = True
                                break
                    if not has_driver:
                        available_keys.append(k)
                
                box.label(text=f"Available Shape Keys: {len(available_keys)}", 
                         icon='SHAPEKEY_DATA')
        
        box = layout.box()
        box.label(text="Driver Settings:", icon='DRIVER')
        col = box.column()
        col.prop(self, "multiplier", slider=True)
        
        box = layout.box()
        box.label(text="Constraint Settings:", icon='CONSTRAINT')
        col = box.column()
        col.prop(self, "use_head_parent")

    def execute(self, context):
        try:
            # 프로그레스 바 초기화
            wm = context.window_manager
            wm.progress_begin(0, 100)
            
            # 초기 검증 (10%)
            wm.progress_update(10)
            if not self.target_mesh:
                self.report({'ERROR'}, "Please select a target mesh")
                return {'CANCELLED'}

            mesh_obj = bpy.data.objects[self.target_mesh]
            if not mesh_obj.data.shape_keys:
                self.report({'ERROR'}, "Selected mesh has no shape keys")
                return {'CANCELLED'}

            active_bone = context.active_bone
            if not active_bone:
                self.report({'ERROR'}, "No active bone selected")
                return {'CANCELLED'}

            metarig = context.scene.metarig
            if not metarig or metarig.type != 'ARMATURE':
                return {'CANCELLED'}

            # 드라이버가 없는 쉐이프 키 찾기 (20%)
            wm.progress_update(20)
            shape_keys_to_process = []
            for key in mesh_obj.data.shape_keys.key_blocks[1:]:
                has_driver = False
                if mesh_obj.data.shape_keys.animation_data and mesh_obj.data.shape_keys.animation_data.drivers:
                    for dr in mesh_obj.data.shape_keys.animation_data.drivers:
                        if dr.data_path == f'key_blocks["{key.name}"].value':
                            has_driver = True
                            break
                if not has_driver:
                    shape_keys_to_process.append(key)

            if not shape_keys_to_process:
                self.report({'WARNING'}, "No shape keys without drivers found")
                return {'CANCELLED'}

            # 본 생성 준비 (30%)
            wm.progress_update(30)
            selected_bone_head = active_bone.head.copy()
            selected_bone_tail = active_bone.tail.copy()
            bone_length = (selected_bone_tail - selected_bone_head).length

            current_active = context.active_object
            current_mode = context.mode if current_active else 'OBJECT'

            metarig.hide_viewport = False
            metarig.hide_set(False)

            if current_active == metarig:
                was_mirror_x = metarig.data.use_mirror_x
                metarig.data.use_mirror_x = False
                metarig.data.edit_bones.remove(active_bone)
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                metarig.select_set(True)
                context.view_layer.objects.active = metarig
                bpy.ops.object.mode_set(mode='EDIT')
                was_mirror_x = metarig.data.use_mirror_x
                metarig.data.use_mirror_x = False
            
            try:
                current_z_offset = 0
                created_bones = []

                # 본 생성 (30-60%)
                total_bones = len(shape_keys_to_process)
                for i, shape_key in enumerate(shape_keys_to_process):
                    progress = 30 + (i / total_bones * 30)
                    wm.progress_update(progress)
                    
                    safe_bone_name = f"shape_key_ctrl_{shape_key.name}"
                    new_bone = metarig.data.edit_bones.new(name=safe_bone_name)
                    
                    new_bone.head = selected_bone_head.copy()
                    new_bone.tail = selected_bone_tail.copy()
                    new_bone.head.z -= current_z_offset
                    new_bone.tail.z -= current_z_offset
                    
                    if self.use_head_parent:
                        if "spine.006" in metarig.data.edit_bones:
                            new_bone.parent = metarig.data.edit_bones["spine.006"]
                    
                    for b in metarig.data.edit_bones:
                        b.select = False
                        b.select_head = False
                        b.select_tail = False
                    
                    new_bone.select = True
                    new_bone.select_head = True
                    new_bone.select_tail = True
                    metarig.data.edit_bones.active = new_bone
                    
                    created_bones.append(new_bone.name)
                    current_z_offset += bone_length

                # Rigify 설정 (60-70%)
                wm.progress_update(70)
                bpy.ops.object.mode_set(mode='POSE')
                
                for bone_name in created_bones:
                    pose_bone = metarig.pose.bones.get(bone_name)
                    if pose_bone:
                        for pb in metarig.pose.bones:
                            pb.bone.select = False
                        
                        pose_bone.bone.select = True
                        metarig.data.bones.active = pose_bone.bone
                        
                        pose_bone.rigify_type = 'basic.super_copy'
                        
                        if hasattr(pose_bone, 'rigify_parameters'):
                            pose_bone.rigify_parameters.make_widget = True
                            pose_bone.rigify_parameters.make_control = True
                            pose_bone.rigify_parameters.make_deform = False
                            pose_bone.rigify_parameters.widget_type = 'bone'
                            pose_bone.rigify_parameters.generate = False
                        
                        utils.setup_bone_constraints(pose_bone, 'LOC_X')

                bpy.ops.object.mode_set(mode='EDIT')

                # Rigify 재생성 (70-80%)
                wm.progress_update(80)
                success, rigify_rig = utils.regenerate_rigify_with_widgets(context)
                if not success:
                    self.report({'ERROR'}, f"Failed to regenerate Rigify: {rigify_rig}")
                    return {'CANCELLED'}

                # 위젯과 드라이버 생성 (80-100%)
                total_widgets = len(created_bones)
                for i, (bone_name, shape_key) in enumerate(zip(created_bones, shape_keys_to_process)):
                    progress = 80 + (i / total_widgets * 20)
                    wm.progress_update(progress)
                    
                    if bone_name in rigify_rig.pose.bones:
                        success, result = utils.create_shape_key_slider(
                            context,
                            rigify_rig.pose.bones[bone_name],
                            self.target_mesh,
                            shape_key.name,
                            custom_text=shape_key.name,
                            use_head_parent=self.use_head_parent,
                            multiplier=self.multiplier
                        )

                        if not success:
                            self.report({'WARNING'}, f"Failed to create widget for {bone_name}: {result}")

                wm.progress_update(100)
                self.report({'INFO'}, f"Successfully created {len(created_bones)} shape key bones with widgets")
                return {'FINISHED'}

            finally:
                metarig.data.use_mirror_x = was_mirror_x
                wm.progress_end()

        except Exception as e:
            wm.progress_end()
            self.report({'ERROR'}, f"Critical error: {str(e)}")
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
    OBJECT_OT_create_multiple_shape_key_bones,
)