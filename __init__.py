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
import os
from . import translations
from . import operators
from . import panel

modules = (
    translations,
    operators,
    panel,
)

def register():
    """Register all modules and translations / 모든 모듈과 번역 등록"""
    try:
        # Register modules / 모듈 등록
        for module in modules:
            module.register()
        
        print("Shape Key Text Creator: Registration successful")
    except Exception as e:
        print(f"Shape Key Text Creator: Registration failed: {str(e)}")

def unregister():
    """Unregister all modules and translations / 모든 모듈과 번역 등록 해제"""
    try:
        # Unregister modules / 모듈 등록 해제
        for module in reversed(modules):
            module.unregister()
        
        print("Shape Key Text Creator: Unregistration successful")
    except Exception as e:
        print(f"Shape Key Text Creator: Unregistration failed: {str(e)}")

if __name__ == "__main__":
    register()
