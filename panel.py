import bpy
import math
import mathutils
from . import utils
from bpy.types import Panel, Operator
from bpy.props import EnumProperty, StringProperty, BoolProperty, FloatProperty

class OBJECT_OT_recreate_slider_templates(Operator):
    """Recreate all slider templates"""
    bl_idname = "object.recreate_slider_templates"
    bl_label = "Recreate Templates"
    bl_description = "Recreate all slider templates"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Remove existing template collection / 기존 템플릿 컬렉션 삭제
        template_collection = None
        for collection in context.scene.collection.children:
            if collection.name == "ShapeKeySliderTemplates":
                # Remove all objects in collection / 컬렉션 내의 모든 오브젝트 삭제
                for obj in collection.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                # Remove collection / 컬렉션 삭제
                bpy.data.collections.remove(collection)
                break
        
        # Create new templates / 새로운 템플릿 생성
        from . import operators
        template_collection = operators.ensure_template_collection()
        operators.create_templates(template_collection)
        
        self.report({'INFO'}, "Templates recreated successfully")
        return {'FINISHED'}
    
class OBJECT_OT_find_metarig(Operator):
    """Find metarig in scene"""
    bl_idname = "object.find_metarig"
    bl_label = "Find Metarig"
    bl_description = "Auto-find metarig in scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 씬에서 메타리그 찾기
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE' and "metarig" in obj.name.lower():
                context.scene.metarig = obj
                self.report({'INFO'}, f"Found metarig: {obj.name}")
                return {'FINISHED'}
        
        self.report({'WARNING'}, "No metarig found in scene")
        return {'CANCELLED'}
    
class OBJECT_OT_find_rigify(Operator):
    """Find Rigify rig in scene"""
    bl_idname = "object.find_rigify_rig"
    bl_label = "Find Rigify"
    bl_description = "Auto-find rigify rig in scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 씬에서 root 아마추어 찾기
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE' and obj.name.lower() == "root":
                context.scene.rigify_rig = obj
                self.report({'INFO'}, f"Found root armature: {obj.name}")
                return {'FINISHED'}
        
        self.report({'WARNING'}, "No root armature found in scene")
        return {'CANCELLED'}

class SHAPEKEY_PT_tools_creator(Panel):
    """Shape Key Text Creator Panel"""
    bl_idname = "SHAPEKEY_PT_tools_creator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shape Key Tools'
    bl_label = "Shape Key Text Creator"
    bl_description = "Create text objects with sliders for shape keys"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # 템플릿 관리 섹션
        box = layout.box()
        row = box.row()
        row.operator("object.recreate_slider_templates", 
                        icon='FILE_REFRESH', 
                        text="Recreate Templates")

        # 메타리그 선택 UI
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Meta-Rig:")
        row.prop(context.scene, "metarig", 
                text="")
        row.operator("object.find_metarig", 
                    text="", 
                    icon='EYEDROPPER')

        # 리기파이 리그 선택 UI
        row = box.row(align=True)
        row.label(text="Rigify Rig:")
        row.prop(context.scene, "rigify_rig", 
                text="")
        row.operator("object.find_rigify_rig", 
                    text="", 
                    icon='EYEDROPPER')
    
        # 리기파이 리제네레이트 버튼
        box = layout.box()
        row = box.row()
        row.operator("armature.rigify_regenerate_with_widgets", 
                    text="Regenerate (Preserve Widgets)", 
                    icon='ARMATURE_DATA')

        # 본 추가 버튼
        if context.scene.metarig:
            row = box.row()
            row.operator("object.add_shape_key_bone", 
                        text="Add Shape Key Bone", 
                           icon='BONE_DATA')
        
        # 본 삭제 버튼 (에딧 모드나 포즈 모드에서 리기파이 본이 선택된 경우에만 표시)
        if context.mode in {'EDIT_ARMATURE', 'POSE'}:
            is_rigify_bone = False
            if context.mode == 'EDIT_ARMATURE':
                is_rigify_bone = (context.active_bone and 
                                context.active_object == context.scene.rigify_rig)
            else:  # POSE
                is_rigify_bone = (context.active_pose_bone and 
                                context.active_object == context.scene.rigify_rig)
            
            if is_rigify_bone:
                box = layout.box()
                row = box.row()
                row.operator("edit.delete_shape_key_bone", 
                           text="Delete Shape Key Bone", 
                           icon='TRASH')
        
        # 포즈 모드 UI
        if context.mode == 'POSE' and context.active_pose_bone:
            box = layout.box()
            box.operator("object.create_shape_key_slider", 
                        text="Create Shape Key Slider",
                        icon='ADD')
        else:
            box = layout.box()
            row = box.row()
            row.label(text="Select a bone in Pose mode", 
                    icon='INFO')
                
        # Apply to Bone 버튼 - 리기파이 리그의 에딧 모드에서만 활성화
        available_meshes = utils.get_available_meshes(context)
        if available_meshes:
            row = layout.row()
            row.operator("object.apply_shape_key_to_bone", 
                        text="Apply to Bone", 
                        icon='CHECKMARK')
            # 리기파이 리그가 선택되고 에딧 모드일 때만 활성화
            row.enabled = (context.mode == 'EDIT_ARMATURE' and 
                        is_rigify_bone)

        if context.mode == 'POSE':
            if available_meshes:
                box = layout.box()
                col = box.column()
                
                # 헤더
                row = col.row(align=True)
                is_expanded = context.window_manager.show_shape_keys
                row.prop(context.window_manager, "show_shape_keys",
                        icon='DOWNARROW_HLT' if is_expanded else 'RIGHTARROW',
                        icon_only=True, emboss=False)
                row.label(text="Available Shape Keys")
                
                if is_expanded:
                    scroll_box = box.box()
                    scroll = scroll_box.column_flow(columns=1, align=True)
                    scroll.scale_y = 1
                    
                    for mesh_obj in available_meshes:
                        scroll.label(text=f"Mesh: {mesh_obj.name}", icon='MESH_DATA')
                        utils.draw_shape_key_list(scroll, mesh_obj)

        # 오브젝트 모드
        elif obj and obj.type == 'MESH' and obj.data.shape_keys:
            layout.operator("object.create_shape_key_text", 
                            text="Create Shape Key Text",
                            icon='FONT_DATA')
            
            box = layout.box()
            col = box.column()
            
            # 헤더
            row = col.row(align=True)
            is_expanded = context.window_manager.show_shape_keys
            row.prop(context.window_manager, "show_shape_keys",
                    icon='DOWNARROW_HLT' if is_expanded else 'RIGHTARROW',
                    icon_only=True, emboss=False)
            row.label(text="Available Shape Keys")
            
            if is_expanded:
                scroll_box = box.box()
                scroll = scroll_box.column_flow(columns=1, align=True)
                scroll.scale_y = 1
                utils.draw_shape_key_list(scroll, obj)
                                
class SHAPE_OT_adjust_driver_value(Operator):
    """Adjust driver multiplier value"""
    bl_idname = "shape.adjust_driver_value"
    bl_label = "Adjust Driver Value"
    bl_options = {'REGISTER', 'UNDO'}
    
    value: FloatProperty(
        name="Multiplier",  # 레이블 변경
        description="Driver multiplier value",
        default=4.0,
        min=0.0,
        max=100.0,
        step=1.0,
        precision=1,
        subtype='FACTOR'
    ) # type: ignore

    mesh_name: StringProperty()  # type: ignore
    shape_key_name: StringProperty()  # type: ignore
    transform_type: StringProperty()  # type: ignore
    
    def execute(self, context):
        mesh_obj = bpy.data.objects.get(self.mesh_name)
        if not mesh_obj or not mesh_obj.data.shape_keys or not mesh_obj.data.shape_keys.animation_data:
            return {'CANCELLED'}
            
        shape_keys = mesh_obj.data.shape_keys
        driver_path = f'key_blocks["{self.shape_key_name}"].value'
        
        for driver in shape_keys.animation_data.drivers:
            if driver.data_path == driver_path:
                utils.update_driver_expression(
                    driver.driver,
                    self.value,
                    self.transform_type,
                    mesh_obj
                )
                break
                
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        
        # 정보 표시 박스
        box = layout.box()
        col = box.column(align=True)
        
        # 메쉬 이름 표시
        row = col.row()
        row.label(text="Mesh:", icon='MESH_DATA')
        row.label(text=self.mesh_name)
        
        # 쉐이프 키 이름 표시
        row = col.row()
        row.label(text="Shape Key:", icon='SHAPEKEY_DATA')
        row.label(text=self.shape_key_name)
        
        # 변환 타입 표시
        row = col.row()
        row.label(text="Transform:", icon='DRIVER_TRANSFORM')
        # TRANSFORM_ITEMS에서 현재 transform_type에 해당하는 레이블 찾기
        transform_label = next((item[1] for item in utils.TRANSFORM_ITEMS 
                            if item[0] == self.transform_type), 
                            self.transform_type)
        row.label(text=transform_label)
        
        # 구분선
        layout.separator()
        
        # 슬라이더 UI
        layout.prop(self, "value", slider=True)
    
class OBJECT_OT_create_shape_key_slider(Operator):
    """Create a new slider for shape key control"""
    bl_idname = "object.create_shape_key_slider"
    bl_label = "Create Shape Key Slider"
    bl_description = "Create a new slider for shape key control"
    bl_options = {'REGISTER', 'UNDO'}
    
    target_mesh: EnumProperty(
        name="Target Mesh",
        description="Select mesh containing shape keys",
        items=lambda self, context: [
            (obj.name, obj.name, "")
            for obj in context.scene.objects
            if obj.type == 'MESH' and obj.data.shape_keys
        ]
    ) # type: ignore
    
    shape_key: EnumProperty(
        name="Shape Key",
        description="Select shape key to control",
        items=lambda self, context: [
            (sk.name, sk.name, "")
            for sk in bpy.data.objects.get(self.target_mesh, None).data.shape_keys.key_blocks[1:]
        ] if self.target_mesh and bpy.data.objects.get(self.target_mesh).data.shape_keys else []
    ) # type: ignore
    
    custom_text: StringProperty(
        name="Custom Text",
        description="Enter custom text for the shape key",
        default=""
    ) # type: ignore

    use_head_constraint: BoolProperty(
        name="Parent to Head",
        description="Add Child Of constraint to Rigify head bone",
        default=False
    ) # type: ignore
    
    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and 
                context.active_pose_bone is not None)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "target_mesh")
        if self.target_mesh:
            layout.prop(self, "shape_key")
            if self.shape_key:
                layout.prop(self, "custom_text")
        layout.prop(self, "use_head_constraint")
    
    def execute(self, context):
        if not self.target_mesh or not self.shape_key:
            self.report({'ERROR'}, "Please select both mesh and shape key")
            return {'CANCELLED'}
        
        bone = context.active_pose_bone
        if not bone:
            self.report({'ERROR'}, "No active pose bone")
            return {'CANCELLED'}
        
        # 텍스트 내용 결정
        text_content = self.custom_text if self.custom_text else self.shape_key
        
        # Head 본에 Parent 설정
        if self.use_head_constraint:
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
        mesh_obj = bpy.data.objects[self.target_mesh]
        shape_key_block = mesh_obj.data.shape_keys.key_blocks[self.shape_key]

        # 기존 드라이버의 값 가져오기
        current_value = 3.0  # 기본값
        if shape_key_block.id_data.animation_data:
            for driver in shape_key_block.id_data.animation_data.drivers:
                if driver.data_path == f'key_blocks["{shape_key_block.name}"].value':
                    var = driver.driver.variables[0]
                    transform_type = var.targets[0].transform_type
                    try:
                        if 'ROT' in transform_type:
                            current_value = float(driver.driver.expression.split('*')[2]) / 57.2958
                        elif 'LOC' in transform_type:
                            current_value = float(driver.driver.expression.split('*')[1])
                        else:  # SCALE
                            current_value = float(driver.driver.expression.split('*')[1])
                    except:
                        pass
                    break

        # 위젯 생성 - shape_key_block 전달
        widget, error = utils.create_shape_key_text_widget(
            context,
            f"WGT_{bone.name}",
            text_content,
            bone,
            shape_key_block
        )

        if not widget:
            self.report({'ERROR'}, f"Failed to create widget: {error}")
            return {'CANCELLED'}

        # Head 본에 콘스트레인트 추가
        if self.use_head_constraint:
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
        success, error = utils.setup_shape_key_driver(
            context.active_object,
            bone.name,
            shape_key_block,
            'LOC_X',
            current_value
        )

        if not success:
            self.report({'ERROR'}, f"Failed to setup driver: {error}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Successfully created shape key slider")
        return {'FINISHED'}

class OBJECT_OT_assign_shape_key_widget(Operator):
    """Assign widget to selected bone"""
    bl_idname = "object.assign_shape_key_widget"
    bl_label = "Assign Widget To Bone"
    bl_description = "Assign existing widget to selected bone"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        if not context.scene.rigify_rig:
            self.report({'ERROR'}, "Please select Rigify rig first")
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        
        # 위젯 선택
        box1 = layout.box()
        box1.label(text="Select Widget:")
        row = box1.row(align=True)
        row.prop(context.scene, "widget_collection", text="")
        
        # 본 선택
        box2 = layout.box()
        box2.label(text="Select Bone:")
        row = box2.row(align=True)
        row.prop_search(context.scene, "target_pose_bone", context.scene.rigify_rig.pose, "bones", text="")
    
    def execute(self, context):
        if not context.scene.widget_collection or not context.scene.target_pose_bone:
            self.report({'ERROR'}, "Please select both widget and bone")
            return {'CANCELLED'}
            
        # 리기파이 리그 가져오기
        rig = context.scene.rigify_rig
        if not rig:
            self.report({'ERROR'}, "Rigify rig not found")
            return {'CANCELLED'}
            
        # 본 가져오기
        bone = rig.pose.bones.get(context.scene.target_pose_bone)
        if not bone:
            self.report({'ERROR'}, "Selected bone not found")
            return {'CANCELLED'}
        
        # 위젯 컴포넌트 찾기
        widget_collection = context.scene.widget_collection
        handle = None
        slider = None
        text = None
        
        for obj in widget_collection.objects:
            if obj.name.startswith('WGT_'):
                handle = obj
            elif obj.name.startswith('SLIDE_'):
                slider = obj
            elif obj.name.startswith('TEXT_'):
                text = obj
        
        if not all([handle, slider, text]):
            self.report({'ERROR'}, "Widget components not found")
            return {'CANCELLED'}
        
        # 모든 오브젝트의 부모 관계 해제
        for obj in [handle, slider, text]:
            if obj.parent:
                obj.parent = None
                obj.matrix_world = obj.matrix_world
            
        # 본의 월드 매트릭스 계산
        world_matrix = rig.matrix_world @ bone.matrix
        bone_loc = world_matrix.translation
        
        # 기본 크기 설정
        base_scale = 0.05
        
        # 핸들 설정
        handle.location = bone_loc
        handle.rotation_euler = world_matrix.to_euler('XYZ')
        handle.scale = mathutils.Vector((base_scale, base_scale, base_scale))
        
        # 슬라이더 설정
        slider.location = bone_loc
        slider.rotation_mode = 'QUATERNION'
        
        # 본의 로컬 회전을 쿼터니온으로 변환
        bone_rot_quat = world_matrix.to_quaternion()
        
        # Y축으로 90도 회전하는 쿼터니온
        y_rot_quat = mathutils.Quaternion((0.7071068, 0.0, 0.7071068, 0.0))  # Y축 90도 회전
        
        # 최종 회전 적용
        slider.rotation_quaternion = bone_rot_quat @ y_rot_quat
        slider.scale = mathutils.Vector((base_scale * 8, base_scale * 0.2, base_scale))
        
        # 텍스트 설정
        text_offset = mathutils.Vector((0, base_scale * 2, 0))
        text_offset.rotate(bone_rot_quat)
        text.location = bone_loc + text_offset
        text.rotation_euler = (0, 0, 0)  # 항상 정면을 향하도록
        text.scale = mathutils.Vector((base_scale * 2, base_scale * 2, base_scale * 2))
        
        # 핸들을 본의 커스텀 쉐이프로 설정
        bone.custom_shape = handle
        bone.use_custom_shape_bone_size = True
        bone.custom_shape_scale_xyz = (1, 1, 1)
        bone.custom_shape_translation = (0, 0, 0)
        bone.custom_shape_rotation_euler = (0, 0, 0)
        
        # 위젯들을 본에 페어런트
        for obj in [handle, slider, text]:
            obj.parent = rig
            obj.parent_type = 'BONE'
            obj.parent_bone = bone.name
            obj.matrix_parent_inverse = world_matrix.inverted()
        
        self.report({'INFO'}, "Widget assigned successfully")
        return {'FINISHED'}

class SHAPEKEY_PT_sync_settings(Panel):
    """Shape Key Sync Settings Panel"""
    bl_label = "Shape Key Sync"
    bl_idname = "SHAPEKEY_PT_sync_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Shape Key Tools'

    @classmethod
    def poll(cls, context):
        # 메타리그와 리기파이 리그가 모두 설정되어 있는지 확인
        return (context.mode == 'EDIT_ARMATURE' and 
                context.scene.metarig and 
                context.scene.rigify_rig)
        
    def draw(self, context):
        layout = self.layout
        
        # Rigify 본 선택 상태 확인
        is_rigify_bone = (context.active_bone and 
                        context.active_object == context.scene.rigify_rig)
        
        # 동기화 설정
        box = layout.box()
        row = box.row()
        row.enabled = is_rigify_bone
        row.prop(context.scene, "is_sync_enabled", text="Enable Auto Sync")
        
        row = box.row()
        row.operator("edit.sync_metarig_bone", text="Sync Now")
        
        # 상태 메시지 표시
        if not is_rigify_bone:
            box.label(text="Select a Rigify bone in Edit mode", icon='INFO')

classes = (
    OBJECT_OT_recreate_slider_templates,
    SHAPEKEY_PT_tools_creator,
    OBJECT_OT_find_metarig,
    OBJECT_OT_find_rigify,
    OBJECT_OT_create_shape_key_slider,    
    SHAPE_OT_adjust_driver_value,
    OBJECT_OT_assign_shape_key_widget,
    SHAPEKEY_PT_sync_settings,
)