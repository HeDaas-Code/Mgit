#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, Callable, List, Any, Optional
from PyQt5.QtWidgets import QWidget

class PluginBase:
    """
    插件基类 - 所有插件应继承此类
    
    插件是MGit应用程序的扩展点，通过实现此基类，开发者可以创建
    自定义功能，并将其集成到MGit应用程序中，而无需修改核心代码。
    
    基本使用:
    ```python
    from src.utils.plugin_base import PluginBase
    
    class Plugin(PluginBase):
        # 插件元数据
        name = "我的插件"
        version = "1.0.0"
        author = "开发者名称"
        description = "插件描述"
        plugin_type = "工具"  # 可以是: 工具, 主题, 编辑器, 视图, 通用 等
        
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
        
        def initialize(self, app):
            # 插件初始化代码
            self.app = app
            # ...
            
        def get_event_listeners(self):
            # 返回事件监听器字典
            return {
                'event_name': self.on_event,
                'another_event': self.on_another_event
            }
            
        def get_hooks(self):
            # 返回钩子函数字典
            return {
                'hook_name': self.apply_hook
            }
            
        def get_settings_widget(self):
            # 返回插件设置界面
            return MySettingsWidget()
    ```
    """
    
    # 插件元数据（子类应覆盖这些属性）
    name = "Base Plugin"
    version = "0.1.0"
    author = "Unknown"
    description = "Base plugin class"
    plugin_type = "General"  # 可以是: Tool, Theme, Editor, View, General 等
    
    # 依赖的其他插件 (可选)
    requires: List[str] = []
    
    # 插件设置 (可选)
    settings: Dict[str, Dict[str, Any]] = {}
    
    # 插件是否启用
    enabled = True
    
    def __init__(self):
        """初始化插件实例"""
        self.app = None  # 将在initialize方法中设置
    
    def initialize(self, app: Any) -> None:
        """
        初始化插件，当插件被加载时调用
        
        Args:
            app: 应用程序实例
        """
        self.app = app
    
    def cleanup(self) -> None:
        """
        清理插件资源，当插件被卸载时调用
        子类可以覆盖此方法以释放资源
        """
        pass
    
    def enable(self) -> None:
        """
        启用插件功能
        子类可以覆盖此方法以执行启用逻辑
        """
        self.enabled = True
    
    def disable(self) -> None:
        """
        禁用插件功能
        子类可以覆盖此方法以执行禁用逻辑
        """
        self.enabled = False
    
    def get_event_listeners(self) -> Dict[str, Callable]:
        """
        获取事件监听器
        
        Returns:
            Dict[str, Callable]: 事件名称到回调函数的映射
        """
        return {}
    
    def get_hooks(self) -> Dict[str, Callable]:
        """
        获取钩子函数
        
        Returns:
            Dict[str, Callable]: 钩子名称到回调函数的映射
        """
        return {}
    
    def get_settings_widget(self) -> Optional[QWidget]:
        """
        获取插件设置界面
        
        Returns:
            Optional[QWidget]: 设置界面，如果没有则返回None
        """
        return None
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        获取插件设置值
        
        Args:
            key: 设置键名
            default: 默认值，如果设置不存在
            
        Returns:
            Any: 设置值或默认值
        """
        if key not in self.settings:
            return default
        
        # 尝试从配置管理器获取设置值
        try:
            from src.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            plugin_settings = config_manager.get_plugin_settings(self.name)
            if plugin_settings and key in plugin_settings:
                return plugin_settings[key]
        except:
            pass
        
        # 如果无法从配置获取，则返回默认值
        return self.settings[key].get('default', default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        设置插件设置值
        
        Args:
            key: 设置键名
            value: 设置值
        """
        if key not in self.settings:
            return
        
        # 保存到配置管理器
        try:
            from src.utils.config_manager import ConfigManager
            config_manager = ConfigManager()
            plugin_settings = config_manager.get_plugin_settings(self.name) or {}
            plugin_settings[key] = value
            config_manager.set_plugin_settings(self.name, plugin_settings)
        except:
            pass

class ToolbarPlugin(PluginBase):
    """
    工具栏插件基类 - 在工具栏中添加功能
    """
    
    plugin_type = "工具栏"
    
    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """
        获取工具栏项目列表
        
        Returns:
            List[Dict[str, Any]]: 工具栏项目列表，每个项目包含:
                {
                    'name': 项目名称,
                    'icon': 图标 (FluentIcon 或 QIcon),
                    'tooltip': 工具提示,
                    'callback': 点击回调函数
                }
        """
        return []

class EditorPlugin(PluginBase):
    """
    编辑器插件基类 - 扩展编辑器功能
    """
    
    plugin_type = "编辑器"
    
    def on_editor_created(self, editor) -> None:
        """
        当编辑器创建时调用
        
        Args:
            editor: 编辑器实例
        """
        pass
    
    def get_context_menu_items(self) -> List[Dict[str, Any]]:
        """
        获取编辑器上下文菜单项
        
        Returns:
            List[Dict[str, Any]]: 菜单项列表，每个项目包含:
                {
                    'name': 菜单项名称,
                    'icon': 图标 (可选),
                    'callback': 点击回调函数
                }
        """
        return []

class ThemePlugin(PluginBase):
    """
    主题插件基类 - 提供自定义主题
    """
    
    plugin_type = "主题"
    
    def apply_theme(self) -> None:
        """应用主题"""
        pass
    
    def get_style_sheet(self) -> str:
        """
        获取样式表
        
        Returns:
            str: CSS样式表
        """
        return ""

class ViewPlugin(PluginBase):
    """
    视图插件基类 - 添加自定义视图
    """
    
    plugin_type = "视图"
    
    def get_view(self) -> Optional[QWidget]:
        """
        获取自定义视图
        
        Returns:
            Optional[QWidget]: 视图小部件
        """
        return None
    
    def get_view_name(self) -> str:
        """
        获取视图名称
        
        Returns:
            str: 视图名称
        """
        return self.name 