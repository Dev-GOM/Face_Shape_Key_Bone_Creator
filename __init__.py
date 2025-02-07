# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Shape Key Control Creator",
    "author": "Dev.GOM",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Shape Key Control Creator",
    "description": "Creates text objects with sliders for shape keys / 쉐이프 키를 위한 텍스트 슬라이더 생성 / シェイプキー用のテキストスライダーを作成 / 为形态键创建文本滑块",
    "category": "Object",
    "doc_url": "https://github.com/Dev-GOM/Face_Shape_Key_Bone_Creator/blob/main/README.md",
    "tracker_url": "https://github.com/Dev-GOM/Face_Shape_Key_Bone_Creator/issues",
    "warning": "",
    "support": "COMMUNITY"
}

import bpy
from . import translations
from . import operators
from . import panel

def register():
    """Register all modules and translations"""
    try:
        # Register translations
        translations.register()
        
        # Register classes
        for cls in operators.classes:
            try:
                bpy.utils.register_class(cls)
            except Exception as e:
                print(f"Failed to register {cls.__name__}: {str(e)}")
                
        for cls in panel.classes:
            try:
                bpy.utils.register_class(cls)
            except Exception as e:
                print(f"Failed to register {cls.__name__}: {str(e)}")
        
        # Register properties
        bpy.types.Scene.metarig = bpy.props.PointerProperty(
            type=bpy.types.Object,
            name="Meta-Rig",
            description="Metarig armature for creating shape key controls",
            poll=lambda self, obj: obj.type == 'ARMATURE'
        )

        bpy.types.Scene.rigify_rig = bpy.props.PointerProperty(
            type=bpy.types.Object,
            name="Rigify Rig",
            description="Rigify rig for connecting shape key drivers",
            poll=lambda self, obj: obj.type == 'ARMATURE'
        )

        bpy.types.WindowManager.show_shape_keys = bpy.props.BoolProperty(
            name="Show Shape Keys",
            description="Show available shape keys",
            default=True
        )
        
        bpy.types.Scene.widget_collection = bpy.props.PointerProperty(
            type=bpy.types.Collection,
            name="Widget Collection",
            description="Select collection containing widget objects",
            poll=lambda self, obj: obj.name.startswith('WGT_')
        )
        
        bpy.types.Scene.target_pose_bone = bpy.props.StringProperty(
            name="Target Bone",
            description="Select bone to assign the widget",
        )
        
        bpy.types.Scene.is_sync_enabled = bpy.props.BoolProperty(
            name="Enable Auto Sync",
            description="Automatically sync metarig bone with rigify bone",
            default=True
        )
        
        # Register handlers
        if operators.transform_handler not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(operators.transform_handler)
        
        print("Shape Key Control Creator: Registration successful")
        
    except Exception as e:
        print(f"Shape Key Control Creator: Registration failed: {str(e)}")

def unregister():
    """Unregister all modules and translations"""
    try:
        # Unregister handlers
        if operators.transform_handler in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(operators.transform_handler)
        
        # Unregister properties
        del bpy.types.Scene.is_sync_enabled
        del bpy.types.Scene.metarig
        del bpy.types.Scene.rigify_rig
        del bpy.types.WindowManager.show_shape_keys
        del bpy.types.Scene.widget_collection
        del bpy.types.Scene.target_pose_bone
        
        # Unregister classes
        for cls in reversed(panel.classes):
            try:
                bpy.utils.unregister_class(cls)
            except Exception as e:
                print(f"Failed to unregister {cls.__name__}: {str(e)}")
                
        for cls in reversed(operators.classes):
            try:
                bpy.utils.unregister_class(cls)
            except Exception as e:
                print(f"Failed to unregister {cls.__name__}: {str(e)}")
        
        # Unregister translations
        translations.unregister()
        
        print("Shape Key Control Creator: Unregistration successful")
        
    except Exception as e:
        print(f"Shape Key Control Creator: Unregistration failed: {str(e)}")

if __name__ == "__main__":
    register()
