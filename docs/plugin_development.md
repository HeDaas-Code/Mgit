# MGit 插件开发指南

## 简介

MGit 插件系统允许开发者通过编写自定义插件来扩展 MGit 的功能。插件可以扩展用户界面、添加新特性、实现自定义行为或与外部系统集成。本文档提供了创建和开发 MGit 插件的详细指南，从基础概念到高级技术都有涵盖。

无论您是希望修改编辑器行为、添加新工具、或实现全新功能的开发者，MGit 的插件架构都提供了灵活且强大的扩展机制。

### 为什么开发插件？

- **个性化**：根据个人或团队需求定制 MGit
- **功能扩展**：添加 MGit 核心功能之外的特性
- **工作流集成**：将 MGit 与您的其他工具和系统连接
- **社区贡献**：分享您的创新，帮助所有 MGit 用户

### 开发前准备

开发 MGit 插件需要以下知识和工具：

- Python 编程基础
- PyQt/PySide 基础知识（对于创建 UI 的插件）
- 了解 MGit 的基本架构
- 文本编辑器或 IDE（推荐使用 MGit 本身）

## 插件系统架构

MGit 的插件系统基于 PluginBase 库实现，采用模块化设计，具有清晰的接口和生命周期管理。系统架构如下：

1. **插件管理器**：负责发现、加载、启用和禁用插件
2. **插件基类**：提供插件实现的基础结构和共同接口
3. **事件系统**：允许插件响应应用程序事件
4. **钩子系统**：允许插件修改应用程序行为
5. **设置系统**：管理和持久化插件配置
6. **依赖管理**：自动处理插件间依赖和第三方包依赖

### 系统特性

MGit 的插件系统提供了以下核心功能：

- **热插拔**：支持在 MGit 运行时动态加载和卸载插件
- **自动发现**：应用启动时自动扫描插件目录并加载有效插件
- **隔离执行**：插件错误不会影响主应用程序的稳定性
- **生命周期管理**：提供完整的初始化、启用、禁用和清理流程
- **版本兼容性检查**：确保插件与当前 MGit 版本兼容
- **插件间通信**：允许插件之间互相调用和数据交换
- **设置持久化**：自动保存和恢复插件设置
- **用户界面集成**：提供统一的设置界面和插件管理
- **依赖解析与安装**：自动管理插件依赖的第三方包，无需用户手动干预

### 插件目录与发现

MGit 会在以下位置搜索插件：

1. 应用程序内置插件目录：`plugins/`
2. 用户插件目录：`~/.mgit/plugins/`（Windows 上为 `%USERPROFILE%\.mgit\plugins\`）

这两个目录中的有效插件文件会被自动发现和加载。插件可以是单个 Python 文件（如 `my_plugin.py`）或包含 `__init__.py` 的目录（如 `my_plugin/__init__.py`）。

## 插件系统概述

MGit 的插件系统基于 PluginBase 库实现，提供了以下功能：

- 自动发现和加载插件
- 插件生命周期管理（加载、启用、禁用、卸载）
- 事件系统，允许插件响应应用程序事件
- 钩子系统，允许插件修改应用程序行为
- 插件设置管理
- 用户界面集成
- 自动管理第三方包依赖

## 插件类型

MGit 支持多种类型的插件，每种类型专注于应用程序的不同方面。插件类型决定了插件的主要功能和集成方式。

### 1. 工具栏插件 (ToolbarPlugin)

工具栏插件向 MGit 的主工具栏添加按钮和操作。适用于：
- 添加快速访问工具
- 实现常用操作的快捷方式
- 集成外部服务和功能

**主要特点**：
- 自定义图标和工具提示
- 可添加下拉菜单
- 支持快捷键绑定
- 可根据上下文显示/隐藏
- 可分组在特定类别下

### 2. 编辑器插件 (EditorPlugin)

编辑器插件扩展 MGit 的文本编辑器功能。适用于：
- 增强编辑体验
- 添加自动完成功能
- 实现特殊文本处理
- 自定义语法高亮和格式化

**主要特点**：
- 访问和修改编辑器内容
- 响应编辑器事件（如光标移动、文本更改）
- 添加自定义上下文菜单
- 扩展编辑器的快捷键
- 实现特殊的输入处理和文本转换

### 3. 主题插件 (ThemePlugin)

主题插件自定义 MGit 的外观。适用于：
- 创建新的应用主题
- 修改现有主题样式
- 实现特殊的视觉效果
- 改变应用程序的外观和感觉

**主要特点**：
- 自定义样式表和颜色方案
- 动态响应主题切换
- 可自定义各种 UI 元素的外观
- 支持亮色和暗色模式

### 4. 视图插件 (ViewPlugin)

视图插件添加新的面板或视图到 MGit 界面。适用于：
- 创建辅助工具面板
- 添加特殊内容查看器
- 实现自定义数据可视化
- 集成外部服务的视图

**主要特点**：
- 添加到主界面侧边栏或底部面板
- 访问当前编辑器内容和选定文本
- 可与主界面和其他插件通信
- 支持复杂 UI 构建和交互

### 5. 分析插件 (AnalyzerPlugin)

分析插件处理和分析文档内容。适用于：
- 文本统计和分析
- 内容检查和验证
- 关键词提取和语义分析
- 代码质量和风格检查

**主要特点**：
- 处理和转换文档内容
- 生成分析报告和数据
- 可视化分析结果
- 提供内容建议和优化

### 6. 通用插件 (PluginBase)

通用插件可以实现上述类型之外的功能。适用于：
- 系统级集成
- 自动化任务
- 混合型功能
- 后台服务和处理

**主要特点**：
- 最大的灵活性和自由度
- 可实现多种功能组合
- 可以访问所有可用的 API
- 适合复杂的定制需求

## 创建新插件的详细步骤

### 1. 创建插件文件

有两种方式创建插件：

#### 单文件插件

对于简单插件，创建单个 Python 文件：

```
plugins/
└── my_plugin.py
```

#### 包形式插件

对于复杂插件，创建一个包目录：

```
plugins/
└── my_plugin/
    ├── __init__.py    # 主插件类
    ├── ui/            # UI 组件
    ├── utils/         # 辅助函数
    └── resources/     # 资源文件
```

无论哪种方式，主插件类都必须命名为 `Plugin` 并位于主模块中。

### 2. 导入必要的模块

根据插件类型，导入相应的基类和所需模块：

```python
# 基础必需导入
from src.utils.plugin_base import PluginBase

# 针对特定类型插件
from src.utils.plugin_base import ToolbarPlugin, EditorPlugin, ViewPlugin, ThemePlugin

# 常用 UI 组件
from qfluentwidgets import (FluentIcon, PushButton, ComboBox, CheckBox, 
                           LineEdit, SpinBox, SettingCard, ExpandLayout)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, Signal, QObject
from PyQt5.QtGui import QIcon, QFont

# 日志和异常处理
from src.utils.logger import info, warning, error

# 其他工具和辅助模块
import os
import json
import re
from pathlib import Path
```

### 3. 创建插件类

创建继承自相应基类的 `Plugin` 类，并定义必要的属性和方法：

```python
class Plugin(PluginBase):  # 或者其他特定基类
    """我的插件简介"""
    
    # 插件元数据 - 必需
    name = "我的插件名称"        # 显示名称，支持中文
    version = "1.0.0"          # 版本号，遵循语义化版本规范
    author = "开发者名称"        # 开发者或组织名称
    description = "详细描述..."  # 插件功能的详细描述
    plugin_type = "通用"        # 插件类型：通用、工具栏、编辑器、主题、视图、分析
    
    # 插件元数据 - 可选
    website = "https://example.com"  # 插件官网或文档地址
    license = "MIT"                  # 许可证类型
    min_app_version = "1.0.0"        # 最低兼容的应用版本
    max_app_version = None           # 最高兼容的应用版本（None表示无限制）
    icon = FluentIcon.EMBED          # 插件图标，使用FluentIcon或自定义QIcon
    
    # 依赖定义 - 可选
    requires = ["other_plugin_id"]   # 依赖的其他插件ID列表
    
    # Python包依赖 - 可选
    package_dependencies = [
        "requests>=2.25.0",          # 格式：包名>=最低版本
        "beautifulsoup4>=4.9.0",
    ]
    
    # 插件设置 - 可选
    settings = {
        'enable_feature_x': {
            'type': 'bool',          # 设置类型
            'default': True,         # 默认值
            'description': '启用X功能' # 设置说明
        },
        'api_key': {
            'type': 'string',
            'default': '',
            'description': 'API密钥'
        },
        'max_items': {
            'type': 'int',
            'default': 10,
            'min': 1,
            'max': 100,
            'description': '最大项目数'
        },
        'theme_color': {
            'type': 'color',
            'default': '#1E90FF',
            'description': '主题颜色'
        },
        'data_source': {
            'type': 'choice',
            'default': 'local',
            'options': ['local', 'remote', 'hybrid'],
            'description': '数据源'
        }
    }
    
    def __init__(self):
        """插件初始化，实例创建时调用"""
        super().__init__()
        # 初始化插件状态和实例变量
        self._initialized = False
        self._view = None
        self._data = {}
        
    def initialize(self, app):
        """初始化插件，当插件被加载时调用
        
        Args:
            app: 应用程序主实例，提供对应用核心功能的访问
        """
        super().initialize(app)
        self.app = app
        
        # 初始化资源和数据
        self._load_resources()
        
        # 注册自定义信号处理
        if hasattr(app, 'signal_name'):
            app.signal_name.connect(self._handle_signal)
        
        # 创建和初始化UI组件
        self._create_ui_components()
        
        # 标记初始化完成
        self._initialized = True
        info(f"{self.name} 插件初始化完成")
    
    def cleanup(self):
        """清理资源，当插件被卸载时调用"""
        # 断开信号连接
        if hasattr(self.app, 'signal_name'):
            self.app.signal_name.disconnect(self._handle_signal)
        
        # 释放资源
        self._free_resources()
        
        # 清理UI组件
        if self._view:
            self._view.deleteLater()
            self._view = None
        
        # 保存状态
        self._save_state()
        
        super().cleanup()
        info(f"{self.name} 插件已清理")
    
    def enable(self):
        """启用插件功能"""
        super().enable()
        # 启用插件特定功能
        info(f"{self.name} 插件已启用")
    
    def disable(self):
        """禁用插件功能"""
        # 禁用插件特定功能
        super().disable()
        info(f"{self.name} 插件已禁用")
        
    # 以下是私有辅助方法
    
    def _load_resources(self):
        """加载插件所需的资源和数据"""
        try:
            # 实现资源加载逻辑
            pass
        except Exception as e:
            error(f"加载资源失败: {str(e)}")
    
    def _free_resources(self):
        """释放插件使用的资源"""
        try:
            # 实现资源释放逻辑
            pass
        except Exception as e:
            error(f"释放资源失败: {str(e)}")
    
    def _create_ui_components(self):
        """创建插件UI组件"""
        try:
            # 实现UI创建逻辑
            pass
        except Exception as e:
            error(f"创建UI组件失败: {str(e)}")
    
    def _save_state(self):
        """保存插件状态"""
        try:
            # 实现状态保存逻辑
            pass
        except Exception as e:
            error(f"保存状态失败: {str(e)}")
            
    def _handle_signal(self, *args, **kwargs):
        """处理应用信号"""
        try:
            # 实现信号处理逻辑
            pass
        except Exception as e:
            error(f"处理信号失败: {str(e)}")
```

### 4. 实现插件特定功能

根据插件类型，实现特定的接口和方法：

#### 通用插件

```python
def get_event_listeners(self):
    """获取事件监听器"""
    return {
        'event_name': self.on_event,
        'another_event': self.on_another_event
    }

def get_hooks(self):
    """获取钩子函数"""
    return {
        'hook_name': self.apply_hook
    }

def get_settings_widget(self):
    """获取设置界面"""
    return MySettingsWidget(self)
```

#### 工具栏插件

继承 `ToolbarPlugin`，并实现：

```python
def get_toolbar_items(self):
    """获取工具栏项目列表"""
    return [
        {
            'name': '我的工具',
            'icon': FluentIcon.EDIT,
            'tooltip': '工具提示',
            'callback': self.on_tool_clicked
        }
    ]
```

#### 编辑器插件

继承 `EditorPlugin`，并实现：

```python
def on_editor_created(self, editor):
    """当编辑器创建时调用"""
    # 编辑器扩展代码

def get_context_menu_items(self):
    """获取编辑器上下文菜单项"""
    return [
        {
            'name': '菜单项',
            'icon': FluentIcon.EDIT,
            'callback': self.on_menu_clicked
        }
    ]
```

#### 主题插件

继承 `ThemePlugin`，并实现：

```python
def apply_theme(self):
    """应用主题"""
    # 主题应用代码

def get_style_sheet(self):
    """获取样式表"""
    return "QWidget { background-color: #f0f0f0; }"
```

#### 视图插件

继承 `ViewPlugin`，并实现：

```python
def get_view(self):
    """获取自定义视图"""
    return MyCustomView()

def get_view_name(self):
    """获取视图名称"""
    return "我的视图"
```

#### 分析插件

继承 `PluginBase` 并将 `plugin_type` 设置为 `"分析"`，实现：

```python
def get_view(self):
    """获取分析视图"""
    return MyAnalyzerView()

def process_text(self, text):
    """处理文本内容"""
    # 文本分析处理代码
    return processed_text
```

## 插件设置系统

MGit 提供了强大的设置系统，让插件可以定义用户可配置的选项，这些设置会在插件管理界面中自动显示，并在应用程序重启后保持。

### 设置定义

插件设置通过 `settings` 类属性定义，使用字典格式：

```python
settings = {
    'setting_key': {  # 设置的唯一标识符
        'type': 'bool',  # 设置类型
        'default': True,  # 默认值
        'description': '设置描述',  # 用户界面中显示的描述
        # 可选的其他属性...
    },
    # 更多设置...
}
```

### 支持的设置类型

MGit 支持以下设置类型：

1. **布尔值 (bool)**：开关类选项
   ```python
   'enable_feature': {
       'type': 'bool',
       'default': True,
       'description': '启用此功能'
   }
   ```

2. **字符串 (string)**：文本输入
   ```python
   'api_key': {
       'type': 'string',
       'default': '',
       'description': 'API密钥',
       'placeholder': '请输入密钥...',  # 可选的占位文本
       'password': True,  # 可选，设为True时显示为密码输入框
       'maxLength': 100,  # 可选，最大字符长度
       'validator': r'^[A-Za-z0-9_-]{10,}$'  # 可选，正则表达式验证
   }
   ```

3. **整数 (int)**：数字输入
   ```python
   'max_items': {
       'type': 'int',
       'default': 10,
       'description': '最大项目数',
       'min': 1,  # 最小值
       'max': 100,  # 最大值
       'step': 1,  # 步长
       'prefix': '数量: ',  # 前缀标签
       'suffix': ' 项'  # 后缀标签
   }
   ```

4. **浮点数 (float)**：小数输入
   ```python
   'scale_factor': {
       'type': 'float',
       'default': 1.0,
       'description': '缩放因子',
       'min': 0.1,
       'max': 2.0,
       'step': 0.1,
       'decimals': 2  # 小数位数
   }
   ```

5. **颜色 (color)**：颜色选择器
   ```python
   'highlight_color': {
       'type': 'color',
       'default': '#FF5733',
       'description': '高亮颜色',
       'alpha': True  # 是否允许设置透明度
   }
   ```

6. **字体 (font)**：字体选择器
   ```python
   'editor_font': {
       'type': 'font',
       'default': 'Consolas, 12',  # 格式: "字体名称, 大小"
       'description': '编辑器字体'
   }
   ```

7. **选项 (choice)**：从预定义选项中选择
   ```python
   'alignment': {
       'type': 'choice',
       'default': 'left',
       'options': ['left', 'center', 'right'],  # 选项列表
       'labels': ['左对齐', '居中', '右对齐'],  # 可选，对应选项的显示标签
       'description': '文本对齐方式'
   }
   ```

8. **文件路径 (path)**：文件或目录选择
   ```python
   'data_file': {
       'type': 'path',
       'default': '',
       'description': '数据文件',
       'filter': '所有文件 (*.*);;文本文件 (*.txt)',  # 文件过滤器
       'mode': 'file',  # 'file' 或 'directory'
       'relative': True  # 是否使用相对路径
   }
   ```

9. **日期时间 (datetime)**：日期时间选择器
   ```python
   'schedule_time': {
       'type': 'datetime',
       'default': '',  # 空字符串表示当前时间
       'description': '计划时间',
       'format': 'yyyy-MM-dd HH:mm',  # 日期时间格式
       'mode': 'date_time'  # 'date', 'time', 或 'date_time'
   }
   ```

10. **列表 (list)**：项目列表
    ```python
    'keywords': {
        'type': 'list',
        'default': ['default'],
        'description': '关键词列表',
        'item_type': 'string',  # 列表项类型
        'max_items': 10  # 最大项目数
    }
    ```

### 设置分组

可以通过添加 `group` 属性将设置分组：

```python
'api_key': {
    'type': 'string',
    'default': '',
    'description': 'API密钥',
    'group': '连接设置'  # 分组名称
},
'api_url': {
    'type': 'string',
    'default': 'https://api.example.com',
    'description': 'API地址',
    'group': '连接设置'  # 同一分组
}
```

### 动态设置验证

通过实现 `validate_setting` 方法，可以添加高级设置验证逻辑：

```python
def validate_setting(self, key, value):
    """验证设置值
    
    Args:
        key: 设置键名
        value: 用户输入的设置值
        
    Returns:
        (bool, str): (是否有效, 错误信息)
    """
    if key == 'api_key' and len(value) < 10:
        return False, "API密钥长度不能少于10个字符"
    
    if key == 'server_url':
        try:
            # 验证URL格式
            import re
            if not re.match(r'^https?://.+', value):
                return False, "服务器URL必须以http://或https://开头"
        except Exception:
            return False, "URL格式无效"
            
    # 通过验证
    return True, ""
```

### 获取和设置值

在插件代码中，使用以下方法操作设置：

```python
# 获取设置值（如果设置不存在，返回默认值）
value = self.get_setting('setting_key')

# 获取设置值，指定备用默认值
value = self.get_setting('setting_key', 'fallback_value')

# 设置新值
self.set_setting('setting_key', new_value)

# 重置为默认值
self.reset_setting('setting_key')

# 获取所有设置
all_settings = self.get_all_settings()
```

### 设置变更监听

可以通过事件系统监听设置变更：

```python
def get_event_listeners(self):
    return {
        'plugin_settings_changed': self.on_settings_changed
    }

def on_settings_changed(self, plugin_id, key, value):
    # 仅处理本插件的设置变更
    if plugin_id == self.plugin_id:
        info(f"设置已更改: {key} = {value}")
        # 根据设置变化执行相应操作
        if key == 'theme_color':
            self._update_theme(value)
        elif key == 'data_source':
            self._switch_data_source(value)
```

### 自定义设置界面

如果默认的设置界面无法满足需求，可以提供自定义设置界面：

```python
def get_settings_widget(self):
    """获取自定义设置界面
    
    Returns:
        QWidget: 设置界面组件
    """
    return MyCustomSettingsWidget(self)
```

自定义设置界面示例：

```python
class MyCustomSettingsWidget(QWidget):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建设置控件
        self.enableCheckBox = CheckBox("启用高级功能")
        self.enableCheckBox.setChecked(plugin.get_setting('enable_advanced'))
        self.enableCheckBox.checkedChanged.connect(self._on_enable_changed)
        
        # 添加到布局
        layout.addWidget(self.enableCheckBox)
        # ... 添加更多控件 ...
        
        # 添加应用按钮
        applyButton = PushButton("应用设置")
        applyButton.clicked.connect(self._apply_settings)
        layout.addWidget(applyButton)
        
    def _on_enable_changed(self, checked):
        # 更新设置值
        self.plugin.set_setting('enable_advanced', checked)
    
    def _apply_settings(self):
        # 应用所有设置
        # ...
```

## 事件系统详解

MGit 的事件系统允许插件响应应用程序中发生的各种事件，实现与应用程序的松耦合交互。

### 事件监听注册

插件通过重写 `get_event_listeners` 方法来订阅事件：

```python
def get_event_listeners(self):
    """获取事件监听器字典
    
    Returns:
        dict: 事件名称到处理函数的映射
    """
    return {
        'app_initialized': self.on_app_initialized,
        'file_opened': self.on_file_opened,
        'editor_text_changed': self.on_text_changed,
        # ... 更多事件 ...
    }
```

### 事件处理方法

为每个事件实现相应的处理方法：

```python
def on_app_initialized(self, app):
    """应用程序初始化完成后调用
    
    Args:
        app: 应用程序主实例
    """
    info("应用程序初始化完成")
    # 执行需要应用程序完全初始化后的操作

def on_file_opened(self, file_path):
    """文件打开时调用
    
    Args:
        file_path: 打开的文件路径
    """
    info(f"打开文件: {file_path}")
    
    # 检查文件类型
    _, ext = os.path.splitext(file_path)
    if ext.lower() in ['.md', '.markdown']:
        # 处理 Markdown 文件
        self._process_markdown_file(file_path)
    
def on_text_changed(self, editor):
    """编辑器文本变化时调用
    
    Args:
        editor: 发生变化的编辑器实例
    """
    # 注意：频繁触发的事件应避免执行耗时操作
    # 可以实现节流或防抖机制
    if not self._throttle_check():
        return
        
    # 获取当前文本
    text = editor.toPlainText()
    # 处理文本变化
    self._analyze_text(text)
```

### 事件防抖与节流

对于频繁触发的事件（如文本变化），应实现节流或防抖机制：

```python
import time

def __init__(self):
    super().__init__()
    self._last_process_time = 0
    self._debounce_timer = None

def _throttle_check(self, interval=500):
    """节流检查，限制处理频率
    
    Args:
        interval: 最小间隔时间(毫秒)
        
    Returns:
        bool: 是否应执行处理
    """
    current_time = int(time.time() * 1000)
    if current_time - self._last_process_time > interval:
        self._last_process_time = current_time
        return True
    return False

def _debounce(self, callback, delay=500):
    """防抖处理，延迟执行直到稳定
    
    Args:
        callback: 要执行的回调函数
        delay: 延迟时间(毫秒)
    """
    # 取消之前的计时器
    if self._debounce_timer:
        from PyQt5.QtCore import QTimer
        self._debounce_timer.stop()
    
    # 创建新的计时器
    from PyQt5.QtCore import QTimer
    self._debounce_timer = QTimer()
    self._debounce_timer.setSingleShot(True)
    self._debounce_timer.timeout.connect(callback)
    self._debounce_timer.start(delay)
```

### 自定义事件发射

插件也可以发射自定义事件：

```python
# 调用应用程序的事件管理器发射事件
self.app.event_manager.emit('my_plugin_event', param1, param2)
```

其他插件可以监听此事件：

```python
def get_event_listeners(self):
    return {
        'my_plugin_event': self.on_custom_event
    }

def on_custom_event(self, param1, param2):
    # 处理自定义事件
    pass
```

### 完整事件列表

MGit 提供了丰富的内置事件：

#### 应用程序事件

| 事件名称 | 描述 | 参数 |
|---------|------|------|
| `app_initialized` | 应用程序初始化完成 | `app` - 应用实例 |
| `app_shutdown` | 应用程序关闭前 | 无 |
| `theme_changed` | 主题变更 | `theme_name` - 主题名称, `is_dark` - 是否为暗色主题 |
| `language_changed` | 语言变更 | `language` - 语言代码 |
| `view_changed` | 视图切换 | `view_name` - 视图名称 |

#### 文件事件

| 事件名称 | 描述 | 参数 |
|---------|------|------|
| `file_opened` | 文件打开 | `file_path` - 文件路径 |
| `file_saved` | 文件保存 | `file_path` - 文件路径, `content` - 文件内容 |
| `file_closed` | 文件关闭 | `file_path` - 文件路径 |
| `file_renamed` | 文件重命名 | `old_path` - 旧路径, `new_path` - 新路径 |

#### 编辑器事件

| 事件名称 | 描述 | 参数 |
|---------|------|------|
| `editor_created` | 编辑器创建 | `editor` - 编辑器实例 |
| `editor_text_changed` | 编辑器文本变化 | `editor` - 编辑器实例 |
| `editor_cursor_changed` | 编辑器光标位置变化 | `editor` - 编辑器实例, `position` - 光标位置 |
| `editor_selection_changed` | 编辑器选择变化 | `editor` - 编辑器实例, `selected_text` - 选中文本 |
| `editor_focus_changed` | 编辑器焦点变化 | `editor` - 编辑器实例, `has_focus` - 是否获得焦点 |

#### Git 相关事件

| 事件名称 | 描述 | 参数 |
|---------|------|------|
| `repository_opened` | 打开 Git 仓库 | `repo_path` - 仓库路径 |
| `repository_closed` | 关闭 Git 仓库 | `repo_path` - 仓库路径 |
| `commit_created` | 创建 Git 提交 | `commit_hash` - 提交哈希, `commit_message` - 提交消息 |
| `branch_changed` | 切换 Git 分支 | `branch_name` - 分支名称 |
| `pull_completed` | 完成 Git 拉取 | `success` - 是否成功, `message` - 消息 |
| `push_completed` | 完成 Git 推送 | `success` - 是否成功, `message` - 消息 |

#### 插件系统事件

| 事件名称 | 描述 | 参数 |
|---------|------|------|
| `plugin_loaded` | 插件加载 | `plugin_id` - 插件ID, `plugin` - 插件实例 |
| `plugin_unloaded` | 插件卸载 | `plugin_id` - 插件ID |
| `plugin_enabled` | 插件启用 | `plugin_id` - 插件ID, `plugin` - 插件实例 |
| `plugin_disabled` | 插件禁用 | `plugin_id` - 插件ID, `plugin` - 插件实例 |
| `plugin_settings_changed` | 插件设置变更 | `plugin_id` - 插件ID, `key` - 设置键, `value` - 新值 |

## 钩子系统详解

钩子系统允许插件修改应用程序的行为和数据处理流程。与事件系统不同，钩子允许插件拦截核心功能的执行流程，并修改输入或输出数据。

### 钩子注册

插件通过重写 `get_hooks` 方法来注册钩子：

```python
def get_hooks(self):
    """获取钩子函数字典
    
    Returns:
        dict: 钩子名称到处理函数的映射
    """
    return {
        'pre_save_file': self.pre_save_hook,
        'post_save_file': self.post_save_hook,
        'modify_markdown': self.modify_markdown,
        # ... 更多钩子 ...
    }
```

### 钩子实现

根据钩子类型实现相应的处理方法：

#### 修改数据钩子

这些钩子允许插件修改数据，应返回修改后的数据：

```python
def pre_save_file(self, file_path, content):
    """文件保存前钩子，可修改保存内容
    
    Args:
        file_path: 文件路径
        content: 原始内容
        
    Returns:
        str: 修改后的内容
    """
    # 仅处理特定类型的文件
    if not file_path.lower().endswith('.md'):
        return content
        
    # 修改内容，例如：添加时间戳
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 检查文件是否已有时间戳
    timestamp_pattern = r'Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
    import re
    
    if re.search(timestamp_pattern, content):
        # 更新已有时间戳
        new_content = re.sub(
            timestamp_pattern,
            f'Last updated: {timestamp}',
            content
        )
    else:
        # 添加新的时间戳到文件顶部
        new_content = f'Last updated: {timestamp}\n\n{content}'
    
    return new_content

def modify_markdown(self, html_content, markdown_text):
    """修改 Markdown 渲染结果
    
    Args:
        html_content: 原始HTML内容
        markdown_text: 原始Markdown文本
        
    Returns:
        str: 修改后的HTML内容
    """
    # 实现自定义修改，例如：高亮特定关键词
    if self.get_setting('highlight_keywords', True):
        keywords = self.get_setting('keywords', [])
        for keyword in keywords:
            html_content = html_content.replace(
                keyword,
                f'<span style="background-color: yellow;">{keyword}</span>'
            )
    
    return html_content
```

#### 拦截动作钩子

这些钩子可以取消应用程序的默认行为：

```python
def pre_open_file(self, file_path):
    """文件打开前钩子，可拦截文件打开行为
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否允许继续默认行为
    """
    # 检查文件是否被锁定
    if self._is_file_locked(file_path):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(
            None,
            "文件锁定",
            f"文件 {os.path.basename(file_path)} 当前被锁定，无法打开。"
        )
        # 返回False阻止默认行为
        return False
    
    # 返回True允许继续
    return True
```

#### 修改界面钩子

这些钩子允许插件修改用户界面：

```python
def modify_editor_context_menu(self, menu, editor):
    """修改编辑器上下文菜单
    
    Args:
        menu: QMenu实例
        editor: 编辑器实例
    """
    # 添加自定义菜单项
    action = menu.addAction("插入模板")
    action.triggered.connect(lambda: self._insert_template(editor))
    
    # 添加子菜单
    templates_menu = menu.addMenu("常用模板")
    for template_name in self._get_templates():
        template_action = templates_menu.addAction(template_name)
        template_action.triggered.connect(
            lambda checked, name=template_name: self._insert_named_template(editor, name)
        )

def modify_status_bar(self, status_bar):
    """修改状态栏
    
    Args:
        status_bar: 状态栏实例
    """
    # 添加自定义状态指示器
    if not hasattr(self, '_status_label'):
        from PyQt5.QtWidgets import QLabel
        self._status_label = QLabel("Ready")
        status_bar.addPermanentWidget(self._status_label)
    
    # 更新状态
    self._status_label.setText(self._get_status())
```

### 高级钩子链处理

由于多个插件可能注册相同的钩子，需要考虑钩子链处理：

```python
def pre_save_file(self, file_path, content):
    """要注意，内容可能已被其他插件修改
    
    Args:
        file_path: 文件路径
        content: 可能已被修改的内容
        
    Returns:
        str: 进一步修改的内容
    """
    # 先检查内容是否已被其他插件修改
    if '<!-- Modified by another plugin -->' in content:
        # 可以选择不修改或适应其他插件的修改
        pass
    
    # 进行自己的修改
    modified = self._process_content(content)
    
    # 添加标记，方便调试
    modified += f'\n<!-- Modified by {self.name} v{self.version} -->'
    
    return modified
```

### 钩子执行顺序

当多个插件注册相同钩子时，执行顺序如下：

1. 按照插件优先级从高到低执行（如果定义了 `priority` 属性）
2. 优先级相同时，按照插件加载顺序执行

可以设置插件优先级：

```python
class Plugin(PluginBase):
    name = "我的插件"
    # ...
    priority = 100  # 数字越大，优先级越高
```

### 完整钩子列表

MGit 提供了丰富的内置钩子：

#### 文件处理钩子

| 钩子名称 | 描述 | 参数 | 返回值 |
|---------|------|------|-------|
| `pre_open_file` | 文件打开前 | `file_path` - 文件路径 | `bool` - 是否继续 |
| `post_open_file` | 文件打开后 | `file_path` - 文件路径, `content` - 文件内容 | 无 |
| `pre_save_file` | 文件保存前 | `file_path` - 文件路径, `content` - 文件内容 | `str` - 修改后的内容 |
| `post_save_file` | 文件保存后 | `file_path` - 文件路径, `content` - 保存的内容 | 无 |
| `filter_file_list` | 过滤文件列表 | `file_list` - 文件路径列表 | `list` - 过滤后的文件列表 |

#### Markdown处理钩子

| 钩子名称 | 描述 | 参数 | 返回值 |
|---------|------|------|-------|
| `pre_render_markdown` | Markdown渲染前 | `markdown_text` - 原始Markdown文本 | `str` - 修改后的Markdown文本 |
| `post_render_markdown` | Markdown渲染后 | `html_content` - 渲染后的HTML, `markdown_text` - 原始Markdown | `str` - 修改后的HTML |
| `modify_markdown_toc` | 修改目录 | `toc_html` - 目录HTML, `markdown_text` - 原始Markdown | `str` - 修改后的目录HTML |
| `modify_markdown_link` | 修改链接 | `link_url` - 链接URL, `link_text` - 链接文本 | `tuple` - (修改后的URL, 修改后的文本) |

#### Git操作钩子

| 钩子名称 | 描述 | 参数 | 返回值 |
|---------|------|------|-------|
| `pre_commit` | 提交前 | `commit_message` - 提交消息, `files` - 文件列表 | `str` - 修改后的提交消息 |
| `post_commit` | 提交后 | `commit_hash` - 提交哈希, `commit_message` - 提交消息 | 无 |
| `pre_push` | 推送前 | `remote` - 远程名称, `branch` - 分支名称 | `bool` - 是否继续 |
| `pre_pull` | 拉取前 | `remote` - 远程名称, `branch` - 分支名称 | `bool` - 是否继续 |

#### 界面修改钩子

| 钩子名称 | 描述 | 参数 | 返回值 |
|---------|------|------|-------|
| `modify_editor_context_menu` | 修改编辑器上下文菜单 | `menu` - 菜单实例, `editor` - 编辑器实例 | 无 |
| `modify_file_context_menu` | 修改文件上下文菜单 | `menu` - 菜单实例, `file_path` - 文件路径 | 无 |
| `modify_status_bar` | 修改状态栏 | `status_bar` - 状态栏实例 | 无 |
| `modify_toolbar` | 修改工具栏 | `toolbar` - 工具栏实例 | 无 |
| `modify_main_menu` | 修改主菜单 | `menu_bar` - 菜单栏实例 | 无 |

## 插件生命周期详解

每个 MGit 插件从创建到卸载都经历一系列生命周期阶段。了解这些阶段对于正确管理插件资源和功能至关重要。

### 完整生命周期流程

插件的完整生命周期包括以下阶段：

1. **发现**：应用程序扫描插件目录，找到可能的插件文件
2. **加载**：加载插件模块，验证插件定义
3. **初始化**：创建插件实例，调用 `initialize(app)` 方法
4. **依赖安装**：安装所需的 Python 包依赖
5. **启用**：调用 `enable()` 方法，激活插件功能
6. **运行**：插件处于活动状态，响应事件和钩子
7. **禁用**：调用 `disable()` 方法，暂时停用插件
8. **卸载**：调用 `cleanup()` 方法，释放资源并移除插件

插件可能会在不同阶段之间转换：可以被禁用后重新启用，或卸载后重新加载。

### 详细阶段说明

#### 1. 发现阶段

应用程序启动时，插件管理器会扫描指定的插件目录：
- 内置插件目录: `plugins/`
- 用户插件目录: `~/.mgit/plugins/`

有效的插件文件包括：
- 单个 Python 文件（如 `my_plugin.py`）
- 包含 `__init__.py` 的目录（如 `my_plugin/__init__.py`）

#### 2. 加载阶段

发现插件文件后，插件管理器会：
1. 导入插件模块
2. 验证是否定义了 `Plugin` 类并继承自 `PluginBase` 或其子类
3. 检查必要的元数据（name, version 等）
4. 验证插件与当前 MGit 版本的兼容性
5. 检查依赖的其他插件是否满足

如果验证失败，插件将无法加载，并记录相应的错误信息。

插件加载顺序：
1. 先加载无依赖或依赖已满足的插件
2. 对于具有依赖关系的插件，遵循依赖图的拓扑顺序
3. 检测并跳过循环依赖

#### 3. 初始化阶段

插件模块加载成功后，插件管理器会：
1. 创建 `Plugin` 类的实例
2. 调用插件的 `initialize(app)` 方法，传入应用程序实例
3. 注册插件的事件监听器和钩子函数
4. 加载插件的持久化设置

`initialize` 方法是插件设置其初始状态的地方：

```python
def initialize(self, app):
    """初始化插件
    
    Args:
        app: 应用程序实例，提供对核心功能的访问
    """
    super().initialize(app)  # 必须调用父类方法
    self.app = app
    
    # 创建和初始化资源
    self._create_resources()
    
    # 加载配置
    self._load_config()
    
    # 准备UI组件（但不显示）
    self._prepare_ui()
    
    # 注册应用程序信号处理
    if hasattr(app, 'editor') and app.editor:
        app.editor.textChanged.connect(self._on_text_changed)
    
    info(f"{self.name} 初始化完成")
```

初始化阶段应该：
- 创建必要的对象和资源
- 连接信号和槽
- 加载配置和数据
- 准备UI组件（但不显示或激活功能）

初始化阶段不应该：
- 修改应用程序状态
- 显示UI组件
- 启动后台任务
- 执行耗时操作

#### 4. 依赖安装阶段

如果插件定义了 `package_dependencies`，插件管理器会：
1. 检查每个依赖包是否已安装
2. 安装缺少的依赖包
3. 验证安装后的依赖版本是否满足要求

依赖安装使用 pip，并支持版本规范：

```python
package_dependencies = [
    "requests>=2.25.0,<3.0.0",
    "beautifulsoup4>=4.9.0",
    "numpy"  # 不指定版本则安装最新版
]
```

如果依赖安装失败，插件仍会加载，但可能无法正常工作。应用程序会记录警告信息，并在插件管理界面中显示依赖状态。

#### 5. 启用阶段

插件初始化后，如果配置为自动启用或用户手动启用，插件管理器会调用 `enable()` 方法：

```python
def enable(self):
    """启用插件功能"""
    if self.enabled:
        return  # 已启用，无需重复操作
        
    super().enable()  # 必须调用父类方法
    
    # 显示UI组件
    if self._view:
        self._view.setVisible(True)
    
    # 注册快捷键
    self._register_shortcuts()
    
    # 启动后台任务
    self._start_background_tasks()
    
    # 发出通知
    from src.utils.notification import show_notification
    show_notification(f"{self.name} 已启用", "插件已成功启用")
    
    info(f"{self.name} 已启用")
```

启用阶段应该：
- 显示UI组件
- 注册快捷键
- 启动后台任务
- 开始监听事件

#### 6. 运行阶段

启用后，插件进入运行阶段，可以：
- 响应用户操作
- 处理应用程序事件
- 执行钩子函数
- 修改应用程序行为
- 与其他插件交互

运行阶段是插件的主要工作阶段，插件的核心功能在此阶段发挥作用。

#### 7. 禁用阶段

当用户禁用插件时，插件管理器会调用 `disable()` 方法：

```python
def disable(self):
    """禁用插件功能"""
    if not self.enabled:
        return  # 已禁用，无需重复操作
    
    # 停止后台任务
    self._stop_background_tasks()
    
    # 隐藏UI组件
    if self._view:
        self._view.setVisible(False)
    
    # 注销快捷键
    self._unregister_shortcuts()
    
    super().disable()  # 必须调用父类方法
    
    info(f"{self.name} 已禁用")
```

禁用阶段应该：
- 隐藏UI组件
- 停止后台任务
- 注销快捷键
- 停止监听事件
- 暂停所有活动功能

**重要**：禁用不同于卸载，禁用后插件实例仍存在，只是暂时停止工作。插件应保持内部状态，以便再次启用时能够恢复。

#### 8. 卸载阶段

当插件被卸载或应用程序关闭时，插件管理器会调用 `cleanup()` 方法：

```python
def cleanup(self):
    """清理资源，准备卸载"""
    # 确保先禁用
    if self.enabled:
        self.disable()
    
    # 断开所有信号连接
    if hasattr(self.app, 'editor') and self.app.editor:
        try:
            self.app.editor.textChanged.disconnect(self._on_text_changed)
        except TypeError:
            # 可能已断开，忽略错误
            pass
    
    # 释放所有资源
    self._release_resources()
    
    # 保存配置
    self._save_config()
    
    # 处理UI组件
    if self._view:
        self._view.deleteLater()
        self._view = None
    
    super().cleanup()  # 必须调用父类方法
    
    info(f"{self.name} 清理完成")
```

卸载阶段应该：
- 保存所有需要持久化的数据
- 关闭打开的文件和连接
- 释放所有分配的资源
- 断开所有信号连接
- 删除临时文件
- 清除定时器和事件处理

**重要**：卸载后，插件实例将被销毁，确保所有资源得到正确释放，避免内存泄漏。

### 生命周期状态转换

插件实例可能经历多次状态转换：

1. **初始化 → 启用**：插件加载后自动启用或用户手动启用
2. **启用 → 禁用**：用户禁用插件
3. **禁用 → 启用**：用户重新启用插件
4. **任何状态 → 卸载**：用户卸载插件或应用程序关闭

每次状态转换都应确保正确处理资源和功能，保持应用程序稳定。

### 持久化与状态管理

插件需要在不同生命周期阶段管理其状态：

```python
def __init__(self):
    super().__init__()
    # 初始化内部状态变量
    self._config = {}
    self._runtime_data = {}
    
def _load_config(self):
    """加载持久化配置"""
    try:
        import os
        import json
        config_path = os.path.join(self.get_plugin_dir(), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
    except Exception as e:
        error(f"加载配置失败: {str(e)}")
        self._config = {}

def _save_config(self):
    """保存持久化配置"""
    try:
        import os
        import json
        config_path = os.path.join(self.get_plugin_dir(), 'config.json')
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        error(f"保存配置失败: {str(e)}")

def get_plugin_dir(self):
    """获取插件数据目录"""
    import os
    from pathlib import Path
    # 创建插件特定的数据目录
    plugin_data_dir = os.path.join(
        str(Path.home()),
        '.mgit',
        'plugin_data',
        self.plugin_id
    )
    os.makedirs(plugin_data_dir, exist_ok=True)
    return plugin_data_dir
```

### 生命周期最佳实践

1. **明确职责划分**：
   - `__init__`：仅初始化基本属性，不访问应用程序实例
   - `initialize`：设置初始状态，准备资源，但不激活功能
   - `enable`：激活功能，显示UI，启动任务
   - `disable`：暂停功能，隐藏UI，停止任务
   - `cleanup`：释放所有资源，保存状态

2. **优雅处理异常**：
   - 在每个生命周期方法中捕获异常
   - 记录详细的错误信息
   - 确保部分失败不影响整体功能

3. **资源管理**：
   - 使用 `with` 语句自动管理资源
   - 显式关闭文件和连接
   - 使用 `try-finally` 确保资源释放

4. **信号处理**：
   - 始终在 `cleanup` 中断开信号连接
   - 使用 `try-except` 处理可能已断开的信号

5. **状态持久化**：
   - 在 `cleanup` 中保存状态
   - 在 `initialize` 中恢复状态
   - 使用专用的插件数据目录存储数据

6. **后台任务**：
   - 在 `enable` 中启动
   - 在 `disable` 中停止
   - 使用标志控制任务循环
   - 确保任务可以干净地中断

## 示例插件

### 基础示例：单词计数器插件

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from src.utils.plugin_base import PluginBase

class WordCountWidget(QWidget):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        layout = QVBoxLayout(self)
        self.countLabel = QLabel("单词数: 0")
        layout.addWidget(self.countLabel)
        
        refreshButton = QPushButton("刷新")
        refreshButton.clicked.connect(self.updateCount)
        layout.addWidget(refreshButton)
    
    def updateCount(self):
        editor = self.plugin.app.editor
        if editor:
            text = editor.toPlainText()
            count = len(text.split())
            self.countLabel.setText(f"单词数: {count}")

class Plugin(PluginBase):
    name = "单词计数器"
    version = "1.0.0"
    author = "MGit团队"
    description = "统计文档中的单词数"
    plugin_type = "编辑器"
    
    def __init__(self):
        super().__init__()
        self.widget = None
    
    def initialize(self, app):
        super().initialize(app)
        self.widget = WordCountWidget(self)
    
    def get_view(self):
        return self.widget
```

### 高级示例：使用第三方依赖的Markdown分析插件

```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from src.utils.plugin_base import PluginBase
import io
import re

class MarkdownAnalyzerWidget(QWidget):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        self.keywordTab = QWidget()
        self.wordcloudTab = QWidget()
        
        self.tabs.addTab(self.keywordTab, "关键词分析")
        self.tabs.addTab(self.wordcloudTab, "词云生成")
        
        # 设置内容...
        
        # 分析按钮
        self.analyzeButton = QPushButton("分析当前文档")
        self.analyzeButton.clicked.connect(self.analyzeDocument)
        layout.addWidget(self.analyzeButton)
        
        layout.addWidget(self.tabs)
    
    def analyzeDocument(self):
        # 获取文档文本
        editor = self.plugin.app.editor
        if editor:
            text = editor.toPlainText()
            # 使用第三方库分析文本...

class Plugin(PluginBase):
    name = "Markdown分析器"
    version = "1.0.0"
    author = "MGit团队"
    description = "提供Markdown文档关键词提取和词云生成功能"
    plugin_type = "分析"
    
    # 第三方库依赖
    package_dependencies = [
        "nltk>=3.6.0",
        "wordcloud>=1.8.1",
        "matplotlib>=3.4.0",
        "numpy>=1.20.0",
        "Pillow>=8.2.0"
    ]
    
    def __init__(self):
        super().__init__()
        self.widget = None
    
    def initialize(self, app):
        super().initialize(app)
        # 这里可以执行其他初始化，例如下载NLTK资源
        try:
            import nltk
            nltk.download('punkt')
            nltk.download('stopwords')
        except Exception as e:
            from src.utils.logger import error
            error(f"初始化NLTK资源失败: {str(e)}")
    
    def get_view(self):
        if not self.widget:
            self.widget = MarkdownAnalyzerWidget(self)
        return self.widget
```

## 插件目录结构

对于简单的插件，单个Python文件就足够了。但对于更复杂的插件，可以使用以下目录结构：

```
plugins/
  my_plugin/
    __init__.py      # 包含Plugin类定义
    ui/
      main_view.py   # UI组件
      settings.py    # 设置界面
    utils/
      helpers.py     # 辅助函数
    resources/       # 资源文件（图像、配置等）
```

在 `__init__.py` 中，你需要导出 `Plugin` 类：

```python
from .ui.main_view import MainView

class Plugin(PluginBase):
    # 插件定义...
    
    def get_view(self):
        return MainView(self)
```

## 插件调试

1. **日志记录**：使用日志模块记录信息，帮助调试
   ```python
   from src.utils.logger import info, warning, error
   
   info("插件信息消息")
   warning("插件警告消息")
   error("插件错误消息")
   ```

2. **查看日志**：在MGit应用程序中，选择"帮助" > "查看日志"菜单查看日志

3. **沙箱测试**：在加载到主应用程序前，可以创建一个简单的测试脚本测试插件功能

4. **检查插件状态**：在插件管理界面中查看插件状态和错误信息

## 最佳实践

1. **错误处理**：
   - 捕获所有可能的异常，确保插件错误不会影响主应用程序
   - 使用日志记录详细的错误信息，便于调试
   - 在UI中为用户提供友好的错误提示

2. **资源管理**：
   - 在 `cleanup()` 方法中释放所有资源（文件句柄、网络连接等）
   - 使用 `with` 语句自动管理资源
   - 避免内存泄漏，特别是在处理大文件时

3. **性能考虑**：
   - 在单独的线程中执行耗时操作，避免阻塞UI
   - 实现延迟加载和缓存机制
   - 避免频繁更新UI，可以使用计时器批量更新

4. **代码结构**：
   - 将UI代码与业务逻辑分离
   - 保持类和函数的单一职责
   - 使用注释解释复杂的算法或非常规代码

5. **依赖管理**：
   - 明确声明所有需要的Python包依赖和版本要求
   - 使用 `try-except` 块优雅地处理可选依赖
   - 考虑依赖包的体积和安装难度

6. **兼容性**：
   - 测试插件在不同操作系统和环境下的行为
   - 避免使用OS特定的API，或提供平台特定的实现
   - 与其他插件良好协作，避免冲突

7. **用户体验**：
   - 提供清晰的视觉反馈和提示
   - 实现撤销/重做支持
   - 保存和恢复用户偏好设置

## 可用的事件和钩子

### 事件

- `app_initialized`：应用程序初始化完成
- `file_opened`：打开文件
- `file_saved`：保存文件
- `file_closed`：关闭文件
- `editor_text_changed`：编辑器文本变化
- `editor_cursor_changed`：编辑器光标位置变化
- `repository_opened`：打开Git仓库
- `repository_closed`：关闭Git仓库
- `commit_created`：创建Git提交
- `branch_changed`：切换Git分支
- `theme_changed`：主题变更
- `plugin_enabled`：插件启用
- `plugin_disabled`：插件禁用
- `plugin_settings_changed`：插件设置变更
- `view_changed`：视图切换

### 钩子

- `pre_save_file`：文件保存前，可修改内容
- `post_save_file`：文件保存后
- `pre_commit`：Git提交前，可修改提交信息
- `post_commit`：Git提交后
- `modify_markdown`：修改Markdown渲染结果
- `modify_status_bar`：修改状态栏内容
- `filter_file_list`：过滤文件列表
- `modify_editor_context_menu`：修改编辑器上下文菜单
- `pre_render_preview`：预览前处理
- `post_render_preview`：预览后处理

## 插件分发

开发完插件后，可以通过以下方式分发：

1. **直接分享文件**：用户可以将插件文件放置在 `~/.mgit/plugins` 目录中
2. **打包分发**：将插件文件和文档打包为zip文件分发
3. **创建安装脚本**：提供自动安装脚本，复制文件到正确位置
4. **插件仓库**：未来我们可能提供插件仓库功能，方便用户查找和安装插件

### 插件分发清单

分发插件时，请确保包含以下内容：

1. 插件源代码（.py文件）
2. README.md 文件，包含：
   - 插件功能介绍
   - 安装说明
   - 使用方法
   - 依赖要求
   - 许可证信息
3. 更新日志（CHANGELOG.md）
4. 示例和截图（可选）
5. 测试用例（可选）

## 常见问题

**问题**：插件无法加载，提示找不到模块？  
**解答**：确保插件文件在正确的目录中，并且导入的模块路径正确。检查是否有循环导入问题。

**问题**：插件加载时出现依赖错误？  
**解答**：确保在 `package_dependencies` 中正确声明了所有需要的依赖包及版本。对于特殊依赖，可能需要在文档中提供额外的安装说明。

**问题**：如何在插件中使用第三方库？  
**解答**：在插件的 `package_dependencies` 列表中声明所需的库和版本。MGit 会自动检查并安装缺失的依赖。如果依赖包含 C 扩展，可能需要确保用户环境中有适当的编译器。

**问题**：插件如何在不同主题下保持一致的外观？  
**解答**：使用 qfluentwidgets 提供的组件，它们会自动适应当前主题。或者使用 `.isDarkTheme()` 方法检测当前主题并应用相应的样式。

**问题**：如何调试插件中的错误？  
**解答**：查看 MGit 日志文件，使用日志模块记录详细信息：`from src.utils.logger import info, error`。也可以添加简单的调试输出到插件视图中。

**问题**：插件性能不佳，如何优化？  
**解答**：将耗时操作放在单独的线程中，使用 `QThread` 或 `concurrent.futures`。实现延迟加载和缓存机制。使用性能分析工具找出瓶颈。

**问题**：插件在某些操作系统上不工作？  
**解答**：确保使用跨平台的API和库。处理路径时使用 `os.path` 或 `pathlib`。测试不同操作系统上的行为，特别是文件系统和UI方面。

**问题**：插件的UI如何适应高DPI屏幕？  
**解答**：使用 Qt 的布局管理器而不是固定大小，避免使用硬编码的像素值。使用 `QIcon.fromTheme()` 获取系统图标，或提供多分辨率版本的图标。

**问题**：插件设置无法保存？  
**解答**：确保使用 `self.set_setting()` 方法保存设置，而不是直接修改属性。检查设置的类型是否可序列化。

**问题**：插件加载后没有出现在界面上？  
**解答**：确保正确实现了 `

## 插件开发故障排除指南

开发插件过程中可能会遇到各种问题。本节提供了常见问题的诊断和解决方案。

### 插件加载问题

#### 插件未被发现

**症状**：插件文件已放置在插件目录，但在插件管理器中未显示。

**可能原因**：
1. 文件名或路径不正确
2. 文件权限问题
3. 插件目录未被正确扫描

**解决方案**：
1. 确认插件文件已放在正确位置：`plugins/` 或 `~/.mgit/plugins/`
2. 文件名不应包含空格或特殊字符，推荐使用下划线命名法
3. 检查文件权限，确保文件可读
4. 重启应用程序，强制重新扫描插件目录
5. 检查日志文件中的相关错误信息

#### 导入错误

**症状**：插件被发现但加载失败，日志中显示 ImportError 或 ModuleNotFoundError。

**可能原因**：
1. 插件代码中导入了未安装的模块
2. 导入路径不正确
3. Python 路径配置问题

**解决方案**：
1. 确保所有导入的模块都已安装或在 `package_dependencies` 中声明
2. 检查导入语句的路径是否正确
3. 对于相对导入，确保包结构正确
4. 使用 `try-except` 处理可选依赖导入

#### 插件定义错误

**症状**：日志显示 "Missing Plugin class" 或类似错误。

**可能原因**：
1. 插件文件中没有定义 `Plugin` 类
2. `Plugin` 类没有继承自 `PluginBase` 或其子类
3. 类命名不是 `Plugin`

**解决方案**：
1. 确保插件文件中定义了名为 `Plugin` 的类
2. 确保 `Plugin` 类继承自 `PluginBase` 或适当的子类
3. 检查类名的大小写（必须是 `Plugin`，不能是 `plugin`）

#### 元数据缺失

**症状**：日志显示 "Missing required metadata" 或类似错误。

**可能原因**：
1. 未定义必需的元数据属性
2. 元数据格式不正确

**解决方案**：
1. 确保定义了所有必需的元数据：`name`, `version`, `author`, `description`, `plugin_type`
2. 检查元数据格式：
   - `name`: 字符串
   - `version`: 格式为 "X.Y.Z" 的字符串
   - `author`: 字符串
   - `description`: 字符串
   - `plugin_type`: 字符串，必须是有效的插件类型

#### 依赖安装失败

**症状**：插件加载，但功能不正常，日志中显示包导入错误。

**可能原因**：
1. 依赖包安装失败
2. 依赖包版本不兼容
3. 依赖包需要额外的系统依赖

**解决方案**：
1. 检查日志中的包安装错误信息
2. 手动安装缺失的依赖包进行测试
3. 确保依赖包与当前 Python 版本兼容
4. 对于含有 C 扩展的包，确保系统有必要的编译器和库
5. 考虑添加装备文档，说明特殊依赖要求

### 运行时问题

#### 插件初始化失败

**症状**：插件加载但初始化失败，功能不可用。

**可能原因**：
1. `initialize` 方法中的错误
2. 访问不存在的应用程序组件
3. 资源初始化失败

**解决方案**：
1. 在 `initialize` 方法中添加详细的日志和异常处理
2. 检查应用程序实例的可用性
3. 使用 `hasattr` 检查对象属性是否存在
4. 实现回退机制处理初始化失败

```python
def initialize(self, app):
    super().initialize(app)
    try:
        self.app = app
        
        # 安全地访问可能不存在的组件
        if hasattr(app, 'editor') and app.editor:
            # 访问编辑器
            pass
        else:
            warning("编辑器不可用，部分功能将受限")
            
        # ... 其余初始化代码 ...
            
    except Exception as e:
        error(f"插件初始化失败: {str(e)}")
        # 实现回退策略
        self._initialized_fully = False
```

#### UI 问题

**症状**：插件UI显示异常或未显示。

**可能原因**：
1. UI组件创建失败
2. 布局问题
3. 样式冲突
4. Qt版本不兼容

**解决方案**：
1. 使用 `QWidget.isVisible()` 检查组件可见性
2. 检查父子组件关系
3. 验证布局是否正确设置
4. 使用 Qt Designer 或 Qt Creator 预览和调试UI
5. 添加调试边框帮助可视化：
   ```python
   widget.setStyleSheet("border: 1px solid red;")  # 调试边框
   ```

#### 事件和钩子未触发

**症状**：插件注册的事件处理程序或钩子函数未被调用。

**可能原因**：
1. 事件或钩子名称拼写错误
2. 函数未正确注册
3. 函数抛出异常

**解决方案**：
1. 确认事件或钩子名称的拼写
2. 检查 `get_event_listeners` 和 `get_hooks` 方法的返回值
3. 添加日志验证函数是否注册：
   ```python
   def initialize(self, app):
       super().initialize(app)
       event_listeners = self.get_event_listeners()
       info(f"已注册的事件监听器: {list(event_listeners.keys())}")
   ```
4. 在事件处理函数中添加异常捕获：
   ```python
   def on_event(self, *args, **kwargs):
       try:
           info(f"事件触发: args={args}, kwargs={kwargs}")
           # 事件处理代码
       except Exception as e:
           error(f"事件处理失败: {str(e)}")
   ```

#### 设置问题

**症状**：插件设置未显示或无法保存。

**可能原因**：
1. 设置定义格式不正确
2. 设置类型不支持
3. 设置值序列化失败

**解决方案**：
1. 验证设置字典的格式
2. 确保使用支持的设置类型
3. 检查设置值是否可JSON序列化
4. 手动调用设置方法进行测试：
   ```python
   # 测试代码，不用于生产
   value = self.get_setting('key')
   info(f"当前设置值: {value}")
   self.set_setting('key', new_value)
   info(f"设置更新后: {self.get_setting('key')}")
   ```

#### 资源泄漏

**症状**：长时间运行后内存使用增加，或临时文件未清理。

**可能原因**：
1. 未关闭文件或连接
2. 未清理临时文件
3. 循环引用导致对象未释放
4. 信号连接未断开

**解决方案**：
1. 使用上下文管理器处理资源
2. 实现完整的 `cleanup` 方法
3. 使用 `weakref` 避免循环引用
4. 确保信号处理器在对象销毁前断开连接

```python
def cleanup(self):
    # 断开所有信号连接
    if hasattr(self, '_handler_connections'):
        for obj, signal, handler in self._handler_connections:
            try:
                getattr(obj, signal).disconnect(handler)
            except (TypeError, RuntimeError):
                pass  # 可能已断开
    
    # 清理临时文件
    if hasattr(self, '_temp_files'):
        for temp_file in self._temp_files:
            try:
                import os
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                error(f"清理临时文件失败: {str(e)}")
    
    super().cleanup()
```

### 调试技巧

#### 日志调试

为插件添加详细的日志记录，帮助诊断问题：

```python
from src.utils.logger import info, warning, error, debug

# 在关键操作前后添加日志
debug("开始处理文件...")
try:
    # 操作代码
    result = self._process_file(file_path)
    debug(f"处理完成，结果: {result}")
except Exception as e:
    error(f"处理文件时出错: {str(e)}")
```

查看日志文件位置：
- Windows: `%APPDATA%\MGit\logs\`
- macOS: `~/Library/Application Support/MGit/logs/`
- Linux: `~/.local/share/MGit/logs/`

#### 交互式调试

使用 `pdb` 或类似工具进行交互式调试：

```python
def problematic_method(self, arg):
    import pdb; pdb.set_trace()  # 调试断点
    # 问题代码...
```

#### 状态检查

添加状态检查方法，验证插件各组件状态：

```python
def _check_state(self):
    """检查并记录插件状态，帮助调试"""
    info("插件状态检查:")
    info(f"  已初始化: {hasattr(self, 'app')}")
    info(f"  已启用: {self.enabled}")
    info(f"  视图已创建: {self._view is not None}")
    info(f"  设置: {self.get_all_settings()}")
    # 检查特定组件...
```

#### 沙箱测试

在将插件集成到应用程序前，创建简单的测试脚本验证功能：

```python
# test_plugin.py
import sys
import os

# 添加必要路径
sys.path.append('/path/to/mgit')

# 创建模拟应用
class MockApp:
    def __init__(self):
        self.editor = None
        # 模拟其他必要组件...

# 导入插件
from plugins.my_plugin import Plugin

# 测试插件
plugin = Plugin()
app = MockApp()
plugin.initialize(app)
plugin.enable()

# 测试特定功能
result = plugin.some_method('test')
print(f"测试结果: {result}")

# 清理
plugin.disable()
plugin.cleanup()
```

### 常见错误模式与修复

#### 1. 竞态条件

**问题**：插件尝试访问尚未完全初始化的应用程序组件。

**示例**：
```python
def initialize(self, app):
    super().initialize(app)
    # 错误：应用可能尚未创建编辑器
    self.editor = app.editor
    self.editor.textChanged.connect(self.on_text_changed)
```

**修复**：
```python
def initialize(self, app):
    super().initialize(app)
    self.app = app
    # 正确：使用事件等待编辑器创建
    
def get_event_listeners(self):
    return {
        'editor_created': self.on_editor_created
    }
    
def on_editor_created(self, editor):
    self.editor = editor
    self.editor.textChanged.connect(self.on_text_changed)
```

#### 2. 资源泄漏

**问题**：未正确关闭文件句柄、网络连接等资源。

**示例**：
```python
def process_file(self, file_path):
    # 错误：文件未关闭
    f = open(file_path, 'r')
    content = f.read()
    return self._process_content(content)
```

**修复**：
```python
def process_file(self, file_path):
    # 正确：使用with语句自动关闭文件
    with open(file_path, 'r') as f:
        content = f.read()
    return self._process_content(content)
```

#### 3. 异常处理不足

**问题**：未捕获和处理可能的异常，导致插件崩溃。

**示例**：
```python
def on_file_opened(self, file_path):
    # 错误：缺少异常处理
    content = self._read_file(file_path)
    result = self._analyze_content(content)
    self._update_view(result)
```

**修复**：
```python
def on_file_opened(self, file_path):
    # 正确：添加异常处理
    try:
        content = self._read_file(file_path)
        result = self._analyze_content(content)
        self._update_view(result)
    except FileNotFoundError:
        warning(f"文件不存在: {file_path}")
    except UnicodeDecodeError:
        warning(f"文件编码不支持: {file_path}")
    except Exception as e:
        error(f"处理文件时出错: {str(e)}")
```

#### 4. 信号连接泄漏

**问题**：信号连接未在对象销毁前断开，导致悬空引用。

**示例**：
```python
def enable(self):
    super().enable()
    # 错误：没有跟踪信号连接
    self.app.editor.textChanged.connect(self.on_text_changed)

def disable(self):
    # 信号连接未断开
    super().disable()
```

**修复**：
```python
def enable(self):
    super().enable()
    if hasattr(self.app, 'editor') and self.app.editor:
        # 正确：跟踪连接以便后续断开
        self._connections = []
        self._connections.append(
            self.app.editor.textChanged.connect(self.on_text_changed)
        )

def disable(self):
    # 断开所有信号连接
    for connection in getattr(self, '_connections', []):
        try:
            connection.disconnect()
        except TypeError:
            pass  # 可能已断开
    self._connections = []
    super().disable()
```

#### 5. UI线程阻塞

**问题**：在UI线程中执行耗时操作，导致界面卡顿。

**示例**：
```python
def analyze_document(self):
    # 错误：在UI线程中执行耗时操作
    text = self.app.editor.toPlainText()
    result = self._complex_analysis(text)  # 耗时操作
    self._update_view(result)
```

**修复**：
```python
from PyQt5.QtCore import QThread, pyqtSignal

class AnalysisThread(QThread):
    result_ready = pyqtSignal(object)
    
    def __init__(self, text):
        super().__init__()
        self.text = text
        
    def run(self):
        from time import sleep
        result = self._complex_analysis(self.text)
        self.result_ready.emit(result)
        
    def _complex_analysis(self, text):
        # 复杂分析代码...
        return result

def analyze_document(self):
    # 正确：在单独线程中执行耗时操作
    text = self.app.editor.toPlainText()
    
    # 创建并启动分析线程
    self.analysis_thread = AnalysisThread(text)
    self.analysis_thread.result_ready.connect(self._on_analysis_complete)
    self.analysis_thread.start()
    
    # 显示进度指示
    self._show_progress("分析中...")

def _on_analysis_complete(self, result):
    # 在UI线程中更新界面
    self._hide_progress()
    self._update_view(result)
```

### 高级诊断工具

对于难以诊断的问题，可以使用以下高级工具：

1. **内存分析**：使用 `tracemalloc` 或 `objgraph` 追踪内存使用和泄漏
   ```python
   import tracemalloc
   tracemalloc.start()
   
   # 在问题点获取快照
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   for stat in top_stats[:10]:
       print(stat)
   ```

2. **性能分析**：使用 `cProfile` 分析代码性能
   ```python
   import cProfile
   
   def profile_method(self):
       profiler = cProfile.Profile()
       profiler.enable()
       
       # 要分析的代码
       self._process_large_file()
       
       profiler.disable()
       profiler.print_stats(sort='cumulative')
   ```

3. **Qt对象树检查**：分析Qt组件层次结构
   ```python
   def debug_widget_hierarchy(widget, level=0):
       """递归打印小部件层次结构"""
       print('  ' * level + widget.__class__.__name__)
       for child in widget.findChildren(QObject, '', Qt.FindDirectChildrenOnly):
           if isinstance(child, QWidget):
               debug_widget_hierarchy(child, level+1)
   
   # 使用方式
   debug_widget_hierarchy(self._view)
   ```

4. **信号追踪**：监控Qt信号发射
   ```python
   # 在PyQt5中监控信号
   def debug_signal(signal):
       """打印信号发射信息的装饰器"""
       original_connect = signal.connect
       
       def connect_wrapper(slot):
           def slot_wrapper(*args):
               print(f"Signal {signal.__name__} emitted with args: {args}")
               return slot(*args)
           return original_connect(slot_wrapper)
           
       signal.connect = connect_wrapper
       return signal
   
   # 使用方式
   debug_signal(self.app.editor.textChanged).connect(self.on_text_changed)
   ```

### 报告问题

如果无法解决问题，请提交详细的问题报告：

1. **问题描述**：清晰简洁地描述问题
2. **重现步骤**：详细列出重现问题的步骤
3. **期望行为**：描述正确情况下应有的行为
4. **环境信息**：
   - MGit 版本
   - 操作系统和版本
   - Python 版本
   - 插件版本
5. **日志文件**：附上相关日志文件
6. **屏幕截图**：如果适用，提供界面截图
7. **代码片段**：提供相关代码，特别是问题发生的部分

可以通过以下渠道提交问题：
- GitHub Issues
- 开发者社区论坛
- 电子邮件支持