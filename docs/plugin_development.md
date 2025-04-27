# MGit 插件开发指南

## 简介

MGit 插件系统允许开发者通过编写自定义插件来扩展 MGit 的功能。本文档提供了创建和开发 MGit 插件的详细指南。

## 插件系统概述

MGit 的插件系统基于 PluginBase 库实现，提供了以下功能：

- 自动发现和加载插件
- 插件生命周期管理（加载、启用、禁用、卸载）
- 事件系统，允许插件响应应用程序事件
- 钩子系统，允许插件修改应用程序行为
- 插件设置管理
- 用户界面集成

## 插件类型

MGit 支持以下类型的插件：

1. **工具栏插件**：添加工具栏按钮和功能
2. **编辑器插件**：扩展编辑器功能
3. **主题插件**：自定义应用程序外观
4. **视图插件**：添加新的视图面板
5. **通用插件**：其他类型的功能扩展

## 创建新插件的步骤

### 1. 创建插件文件

在 `plugins` 目录中创建一个新的 Python 文件。文件名将成为插件的标识符。例如：`my_plugin.py`。

### 2. 导入必要的模块

```python
from src.utils.plugin_base import PluginBase
# 导入其他需要的模块
```

### 3. 创建插件类

每个插件必须包含一个名为 `Plugin` 的类，该类继承自 `PluginBase` 或其子类：

```python
class Plugin(PluginBase):
    # 插件元数据
    name = "我的插件"
    version = "1.0.0"
    author = "开发者名称"
    description = "插件描述"
    plugin_type = "通用"  # 可以是: 通用, 工具栏, 编辑器, 主题, 视图
    
    # 可选: 依赖的其他插件
    requires = []
    
    # 可选: 插件设置
    settings = {
        'setting1': {
            'type': 'bool',
            'default': True,
            'description': '设置1的描述'
        },
        'setting2': {
            'type': 'string',
            'default': 'default value',
            'description': '设置2的描述'
        },
    }
    
    def __init__(self):
        super().__init__()
        # 初始化插件状态
    
    def initialize(self, app):
        """初始化插件，当插件被加载时调用"""
        super().initialize(app)
        # 初始化代码
    
    def cleanup(self):
        """清理资源，当插件被卸载时调用"""
        # 清理代码
    
    def enable(self):
        """启用插件功能"""
        super().enable()
        # 启用代码
    
    def disable(self):
        """禁用插件功能"""
        super().disable()
        # 禁用代码
```

### 4. 实现插件功能

根据插件类型，实现相应的方法：

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

## 插件设置

插件可以定义设置项，这些设置会自动在插件管理界面中显示：

```python
settings = {
    'setting_key': {
        'type': 'bool',  # 可以是: bool, string, int, float, color, font, choice
        'default': True,
        'description': '设置描述'
    }
}
```

可以使用以下方法获取和设置插件设置：

```python
# 获取设置值
value = self.get_setting('setting_key', default_value)

# 设置设置值
self.set_setting('setting_key', new_value)
```

## 事件系统

插件可以监听应用程序事件：

```python
def get_event_listeners(self):
    return {
        'app_initialized': self.on_app_initialized,
        'file_opened': self.on_file_opened,
        'file_saved': self.on_file_saved,
        'editor_text_changed': self.on_text_changed,
        'repository_opened': self.on_repository_opened
    }

def on_app_initialized(self, app):
    # 应用初始化事件处理
    pass

def on_file_opened(self, file_path):
    # 文件打开事件处理
    pass
```

## 钩子系统

插件可以修改应用程序行为：

```python
def get_hooks(self):
    return {
        'pre_save_file': self.pre_save_hook,
        'post_save_file': self.post_save_hook,
        'modify_markdown': self.modify_markdown
    }

def pre_save_hook(self, file_path, content):
    # 修改保存内容
    return content

def modify_markdown(self, html_content, markdown_text):
    # 修改 Markdown 渲染结果
    return html_content
```

## 插件生命周期

1. **加载**：插件管理器发现并加载插件文件
2. **初始化**：调用 `initialize(app)` 方法
3. **启用/禁用**：用户可以启用或禁用插件，调用 `enable()` 或 `disable()` 方法
4. **卸载**：用户卸载插件，调用 `cleanup()` 方法

## 示例插件

以下是一个简单的单词计数器插件示例：

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

## 插件调试

1. 将插件文件放置在 `plugins` 目录中
2. 启动 MGit 应用程序
3. 日志系统会记录插件加载和错误信息
4. 在菜单中选择"插件" > "插件管理"查看和管理插件

## 最佳实践

1. **错误处理**：确保插件中的错误不会影响主应用程序
2. **资源管理**：在 `cleanup()` 方法中释放所有资源
3. **性能考虑**：避免在事件处理器中执行耗时操作
4. **兼容性**：考虑与其他插件的兼容性
5. **文档**：提供清晰的文档和注释
6. **配置**：使用设置系统而不是硬编码配置

## 可用的事件和钩子

### 事件

- `app_initialized`：应用程序初始化完成
- `file_opened`：打开文件
- `file_saved`：保存文件
- `editor_text_changed`：编辑器文本变化
- `repository_opened`：打开Git仓库
- `repository_closed`：关闭Git仓库
- `theme_changed`：主题变更
- `plugin_enabled`：插件启用
- `plugin_disabled`：插件禁用

### 钩子

- `pre_save_file`：文件保存前
- `post_save_file`：文件保存后
- `modify_markdown`：修改Markdown渲染结果
- `modify_status_bar`：修改状态栏内容
- `filter_file_list`：过滤文件列表

## 插件分发

开发完插件后，可以通过以下方式分发：

1. **直接分享文件**：用户可以将插件文件放置在其 `.mgit/plugins` 目录中
2. **打包分发**：将插件文件和文档打包为zip文件分发
3. **插件仓库**：未来我们可能提供插件仓库功能，方便用户查找和安装插件

## 注意事项

1. 插件系统处于积极开发中，API可能会有变化
2. 确保插件不包含恶意代码，尊重用户隐私
3. 尊重第三方库的许可证要求
4. 为插件提供适当的文档

## 常见问题

**问题**：插件无法加载，提示找不到模块？  
**解答**：确保插件文件在正确的目录中，并且导入的模块路径正确。

**问题**：如何在插件中使用第三方库？  
**解答**：尽量使用MGit已包含的库，如果需要额外的库，请在插件文档中说明。

**问题**：插件如何在不同主题下保持一致的外观？  
**解答**：使用qfluentwidgets提供的组件，它们会自动适应当前主题。

**问题**：如何调试插件中的错误？  
**解答**：查看MGit日志文件，使用日志模块记录详细信息：`from src.utils.logger import info, error`。 