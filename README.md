# Shape Key Bone Control Creator

[English](#english) | [한글](#korean) | [日本語](#japanese) | [中文](#chinese)

<div style="padding: 16px; background-color: #f0f7ff; border-left: 4px solid #0366d6; margin-bottom: 20px;">
Shape Key Text Creator is a Blender add-on that helps you visualize and control shape keys through text-based sliders.
</div>

## Preview / 미리보기 / プレビュー / 预览

[![Video Tutorial](https://img.youtube.com/vi/ZL2vitS9E3M/maxresdefault.jpg)](https://youtu.be/ZL2vitS9E3M)

<details>
<summary style="color: #d73a49; font-size: 1.1em; padding: 8px; cursor: pointer;">▶️ Watch on YouTube / 유튜브에서 보기 / YouTubeで見る / 在YouTube上观看</summary>

[Shape Keys Bone And Custom Shape Creater - Blender Face Animation Add-on](https://youtu.be/ZL2vitS9E3M)
</details>

## Version History / 버전 기록 / バージョン履歴 / 版本历史

<details>
<summary style="color: #0366d6; font-size: 1.1em; padding: 8px; cursor: pointer;">📌 v1.1 (2025-02-08)</summary>

<details>
<summary style="color: #28a745; padding: 8px 16px;">🇺🇸 English</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- Added head bone parenting option for shape key controllers
- Auto-select Basis shape key after driver operations
- Enhanced widget and bone cleanup during deletion
- Improved driver management system
- Added support for widget parenting to head bone
</div>
</details>

<details>
<summary style="color: #28a745; padding: 8px 16px;">🇰🇷 한글</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- 쉐이프 키 컨트롤러의 헤드 본 페런팅 옵션 추가
- 드라이버 작업 후 자동으로 Basis 쉐이프 키 선택
- 삭제 시 위젯과 본 정리 기능 강화
- 드라이버 관리 시스템 개선
- 헤드 본에 대한 위젯 페런팅 지원 추가
</div>
</details>

<details>
<summary style="color: #28a745; padding: 8px 16px;">🇯🇵 日本語</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- シェイプキーコントローラーにヘッドボーンペアレントオプションを追加
- ドライバー操作後にベーシスシェイプキーを自動選択
- 削除時のウィジェットとボーンのクリーンアップを強化
- ドライバー管理システムを改善
- ヘッドボーンへのウィジェットペアレントをサポート
</div>
</details>

<details>
<summary style="color: #28a745; padding: 8px 16px;">🇨🇳 中文</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- 为形态键控制器添加头部骨骼父级选项
- 驱动器操作后自动选择基础形态键
- 增强删除时的部件和骨骼清理
- 改进驱动器管理系统
- 添加部件到头部骨骼的父级支持
</div>
</details>
</details>

<details>
<summary style="color: #0366d6; font-size: 1.1em; padding: 8px; cursor: pointer;">📌 v1.0 (2025-02-07)</summary>

<details>
<summary style="color: #28a745; padding: 8px 16px;">🇺🇸 English</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- Initial release
- Basic shape key bone creation
- Widget system implementation
- Driver system setup
</div>
</details>
</details>

<a name="english"></a>
# Shape Key Bone Control Creator

<div style="padding: 16px; background-color: #f0f7ff; border-left: 4px solid #0366d6; margin-bottom: 20px;">
Shape Key Text Creator is a Blender add-on that visualizes and controls shape keys through text-based sliders.
</div>

<details>
<summary style="color: #0366d6; font-size: 1.1em; padding: 8px; cursor: pointer;">✨ Features</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- Visualize shape keys as 3D text
- Control shape keys through slider widgets
- Metarig and Rigify rig support
- Bone-based control system
- Automatic driver setup
</div>
</details>

<details>
<summary style="color: #28a745; font-size: 1.1em; padding: 8px; cursor: pointer;">📥 Installation</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

1. Start Blender
2. Go to Edit > Preferences > Add-ons
3. Click "Install..."
4. Select the downloaded ZIP file
5. Activate the add-on
</div>
</details>

<details>
<summary style="color: #5f2eea; font-size: 1.1em; padding: 8px; cursor: pointer;">🎯 How to Use</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### 1. Initial Setup
- Find View3D > Sidebar > Shape Key Tools panel

### 2. Setup Metarig and Rigify rig
- Click "Find Metarig" to auto-detect metarig
- Click "Find Rigify" to auto-detect rigify rig

### 3. Create shape key bone
- Click "Add Shape Key Bone"
- Select target mesh and shape key
- Set transform type and influence
- Choose text widget creation options

### 4. Widget management
- Click "Recreate Templates" to reset templates
- Click "Assign Widget To Bone" for manual widget assignment
</div>
</details>

<details>
<summary style="color: #6f42c1; font-size: 1.1em; padding: 8px; cursor: pointer;">🔧 Feature Details</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### Shape Key Bone Creation
- Create new bone in metarig
- Auto-setup rigify parameters
- Auto-connect drivers
- Auto-generate text widgets

### Widget System
- Composed of handle, slider, and text
- Synchronized with bone movement
- Custom text support

### Driver System
- Location, rotation, scale-based control
- User-defined influence settings
- Automatic driver setup
</div>
</details>

<details>
<summary style="color: #d73a49; font-size: 1.1em; padding: 8px; cursor: pointer;">⚙️ System Requirements</summary>
<div style="padding: 16px; background-color: #fff5f5; border-left: 4px solid #d73a49;">

- Blender 4.0 or higher
- Rigify add-on required
</div>
</details>

<details>
<summary style="color: #24292e; font-size: 1.1em; padding: 8px; cursor: pointer;">📜 License</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

GNU General Public License v3.0 (GPL-3.0)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
</div>
</details>

---

<a name="korean"></a>
# Shape Key Bone Control Creator

<div style="padding: 16px; background-color: #f0f7ff; border-left: 4px solid #0366d6; margin-bottom: 20px;">
쉐이프 키 텍스트 생성기는 Blender 애드온으로, 쉐이프 키를 텍스트 형태의 슬라이더로 시각화하고 조작할 수 있게 해주는 도구입니다.
</div>

<details>
<summary style="color: #0366d6; font-size: 1.1em; padding: 8px; cursor: pointer;">✨ 주요 기능</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- 쉐이프 키를 3D 텍스트로 시각화
- 슬라이더 위젯을 통한 쉐이프 키 제어
- 메타리그와 리기파이 리그 지원
- 본 기반 컨트롤 시스템
- 드라이버 자동 설정
</div>
</details>

<details>
<summary style="color: #28a745; font-size: 1.1em; padding: 8px; cursor: pointer;">📥 설치 방법</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

1. Blender를 실행합니다
2. Edit > Preferences > Add-ons로 이동합니다
3. "Install..." 버튼을 클릭합니다
4. 다운로드 받은 ZIP 파일을 선택합니다
5. 애드온을 활성화합니다
</div>
</details>

<details>
<summary style="color: #5f2eea; font-size: 1.1em; padding: 8px; cursor: pointer;">🎯 사용 방법</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### 1. 초기 설정
- View3D > Sidebar > Shape Key Tools 패널을 찾습니다

### 2. 메타리그와 리기파이 리그 설정
- "Find Metarig" 버튼으로 메타리그 자동 검색
- "Find Rigify" 버튼으로 리기파이 리그 자동 검색

### 3. 쉐이프 키 본 생성
- "Add Shape Key Bone" 버튼 클릭
- 대상 메쉬와 쉐이프 키 선택
- 변형 타입과 영향도 설정
- 텍스트 위젯 생성 옵션 선택

### 4. 위젯 관리
- "Recreate Templates" 버튼으로 템플릿 초기화
- "Assign Widget To Bone" 버튼으로 위젯 수동 할당
</div>
</details>

<details>
<summary style="color: #6f42c1; font-size: 1.1em; padding: 8px; cursor: pointer;">🔧 주요 기능 설명</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### 쉐이프 키 본 생성
- 메타리그에 새로운 본 생성
- 리기파이 파라미터 자동 설정
- 드라이버 자동 연결
- 텍스트 위젯 자동 생성

### 위젯 시스템
- 핸들, 슬라이더, 텍스트로 구성
- 본 움직임과 연동
- 커스텀 텍스트 지원

### 드라이버 시스템
- 위치, 회전, 스케일 기반 제어
- 사용자 정의 영향도 설정
- 자동 드라이버 설정
</div>
</details>

<details>
<summary style="color: #d73a49; font-size: 1.1em; padding: 8px; cursor: pointer;">⚙️ 시스템 요구사항</summary>
<div style="padding: 16px; background-color: #fff5f5; border-left: 4px solid #d73a49;">

- Blender 4.0 이상
- 리기파이 애드온 필요
</div>
</details>

<details>
<summary style="color: #24292e; font-size: 1.1em; padding: 8px; cursor: pointer;">📜 라이선스</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

GNU General Public License v3.0 (GPL-3.0)

이 프로그램은 자유 소프트웨어입니다. GNU 일반 공중 사용 허가서(GPL) 버전 3 또는 그 이후 버전의 조건에 따라 이 프로그램을 재배포하거나 수정할 수 있습니다.
</div>
</details>

---

<a name="japanese"></a>
# シェイプキーテキストクリエーター

<div style="padding: 16px; background-color: #f0f7ff; border-left: 4px solid #0366d6; margin-bottom: 20px;">
シェイプキーテキストクリエーターは、シェイプキーをテキストベースのスライダーで視覚化し、制御するBlenderアドオンです。
</div>

<details>
<summary style="color: #0366d6; font-size: 1.1em; padding: 8px; cursor: pointer;">✨ 主な機能</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- シェイプキーを3Dテキストで視覚化
- スライダーウィジェットによるシェイプキー制御
- メタリグとRigifyリグのサポート
- ボーンベースの制御システム
- ドライバーの自動設定
</div>
</details>

<details>
<summary style="color: #28a745; font-size: 1.1em; padding: 8px; cursor: pointer;">📥 インストール方法</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

1. Blenderを起動
2. Edit > Preferences > Add-onsに移動
3. "Install..."をクリック
4. ダウンロードしたZIPファイルを選択
5. アドオンを有効化
</div>
</details>

<details>
<summary style="color: #5f2eea; font-size: 1.1em; padding: 8px; cursor: pointer;">🎯 使用方法</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### 1. 初期設定
- View3D > Sidebar > Shape Key Toolsパネルを開く

### 2. メタリグとRigifyリグの設定
- "Find Metarig"ボタンでメタリグを自動検出
- "Find Rigify"ボタンでRigifyリグを自動検出

### 3. シェイプキーボーンの作成
- "Add Shape Key Bone"ボタンをクリック
- ターゲットメッシュとシェイプキーを選択
- 変形タイプと影響度を設定
- テキストウィジェット作成オプションを選択

### 4. ウィジェット管理
- "Recreate Templates"ボタンでテンプレートをリセット
- "Assign Widget To Bone"ボタンでウィジェットを手動割り当て
</div>
</details>

<details>
<summary style="color: #6f42c1; font-size: 1.1em; padding: 8px; cursor: pointer;">🔧 機能詳細</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### シェイプキーボーン作成
- メタリグに新規ボーンを作成
- Rigifyパラメータの自動設定
- ドライバーの自動接続
- テキストウィジェットの自動生成

### ウィジェットシステム
- ハンドル、スライダー、テキストで構成
- ボーンの動きと連動
- カスタムテキストのサポート

### ドライバーシステム
- 位置、回転、スケールベースの制御
- ユーザー定義の影響度設定
- 自動ドライバー設定
</div>
</details>

<details>
<summary style="color: #d73a49; font-size: 1.1em; padding: 8px; cursor: pointer;">⚙️ システム要件</summary>
<div style="padding: 16px; background-color: #fff5f5; border-left: 4px solid #d73a49;">

- Blender 4.0以上
- Rigifyアドオンが必要
</div>
</details>

<details>
<summary style="color: #24292e; font-size: 1.1em; padding: 8px; cursor: pointer;">📜 ライセンス</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

GNU General Public License v3.0 (GPL-3.0)

このプログラムはフリーソフトウェアです。フリーソフトウェア財団によって発行されたGNU 一般公衆利用許諾契約書(GPL)バージョン3または、それ以降のバージョンの条件の下で再配布または改変することができます。
</div>
</details>

---

<a name="chinese"></a>
# 形态键文本创建器

<div style="padding: 16px; background-color: #f0f7ff; border-left: 4px solid #0366d6; margin-bottom: 20px;">
形态键文本创建器是一个Blender插件，可以通过基于文本的滑块来可视化和控制形态键。
</div>

<details>
<summary style="color: #0366d6; font-size: 1.1em; padding: 8px; cursor: pointer;">✨ 主要功能</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

- 将形态键可视化为3D文本
- 通过滑块部件控制形态键
- 支持元骨架和Rigify骨架
- 基于骨骼的控制系统
- 自动设置驱动器
</div>
</details>

<details>
<summary style="color: #28a745; font-size: 1.1em; padding: 8px; cursor: pointer;">📥 安装方法</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

1. 启动Blender
2. 进入Edit > Preferences > Add-ons
3. 点击"Install..."
4. 选择下载的ZIP文件
5. 激活插件
</div>
</details>

<details>
<summary style="color: #5f2eea; font-size: 1.1em; padding: 8px; cursor: pointer;">🎯 使用方法</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### 1. 初始设置
- 找到View3D > Sidebar > Shape Key Tools面板

### 2. 设置元骨架和Rigify骨架
- 点击"Find Metarig"自动检测元骨架
- 点击"Find Rigify"自动检测Rigify骨架

### 3. 创建形态键骨骼
- 点击"Add Shape Key Bone"
- 选择目标网格和形态键
- 设置变换类型和影响度
- 选择文本部件创建选项

### 4. 部件管理
- 点击"Recreate Templates"重置模板
- 点击"Assign Widget To Bone"手动分配部件
</div>
</details>

<details>
<summary style="color: #6f42c1; font-size: 1.1em; padding: 8px; cursor: pointer;">🔧 功能详情</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

### 形态键骨骼创建
- 在元骨架中创建新骨骼
- 自动设置Rigify参数
- 自动连接驱动器
- 自动生成文本部件

### 部件系统
- 由手柄、滑块和文本组成
- 与骨骼移动同步
- 支持自定义文本

### 驱动器系统
- 基于位置、旋转、缩放的控制
- 用户自定义影响度设置
- 自动驱动器设置
</div>
</details>

<details>
<summary style="color: #d73a49; font-size: 1.1em; padding: 8px; cursor: pointer;">⚙️ 系统要求</summary>
<div style="padding: 16px; background-color: #fff5f5; border-left: 4px solid #d73a49;">

- Blender 4.0或更高版本
- 需要Rigify插件
</div>
</details>

<details>
<summary style="color: #24292e; font-size: 1.1em; padding: 8px; cursor: pointer;">📜 许可证</summary>
<div style="padding: 16px; background-color: #f6f8fa;">

GNU General Public License v3.0 (GPL-3.0)

本程序是自由软件：您可以根据自由软件基金会发布的GNU通用公共许可证的条款重新分发和/或修改它，可以选择使用版本3或更高版本的许可证。
</div>
</details>
