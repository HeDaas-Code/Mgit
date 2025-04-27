#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import importlib.util
from typing import Dict, List, Any, Type, Optional, Callable
from pluginbase import PluginBase

from src.utils.logger import info, warning, error, debug

class PluginManager:
    """
    插件管理器类 - 负责插件的加载、注册和管理
    
    插件管理器使用PluginBase库实现插件的加载和管理，允许应用程序动态地
    加载和使用第三方插件，以扩展应用功能，而无需修改核心代码。
    """
    
    # 单例模式
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, app=None):
        # 避免重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        self.app = app  # 应用程序实例
        
        # 插件基础目录
        self.plugin_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'plugins'
        ))
        
        # 为便携版本考虑可能的替代路径
        if not os.path.exists(self.plugin_dir) and hasattr(sys, '_MEIPASS'):
            self.plugin_dir = os.path.join(sys._MEIPASS, 'plugins')
        
        # 用户插件目录（在用户主目录中）
        self.user_plugin_dir = os.path.join(os.path.expanduser('~'), '.mgit', 'plugins')
        
        # 确保插件目录存在
        os.makedirs(self.plugin_dir, exist_ok=True)
        os.makedirs(self.user_plugin_dir, exist_ok=True)
        
        # 创建插件源
        self.plugin_base = PluginBase(package='plugins')
        
        # 创建插件源，并提供插件搜索目录
        self.plugin_source = self.plugin_base.make_plugin_source(
            searchpath=[self.plugin_dir, self.user_plugin_dir],
            identifier='plugins'
        )
        
        # 已加载的插件字典 {plugin_name: plugin_instance}
        self.plugins: Dict[str, Any] = {}
        
        # 插件信息字典 {plugin_name: {name, version, author, description, etc}}
        self.plugin_info: Dict[str, Dict[str, Any]] = {}
        
        # 按类型组织的插件字典 {plugin_type: [plugin_name1, plugin_name2, ...]}
        self.plugin_types: Dict[str, List[str]] = {}
        
        # 插件事件监听器字典 {event_name: [callback1, callback2, ...]}
        self.event_listeners: Dict[str, List[Callable]] = {}
        
        # 钩子函数字典 {hook_name: [callback1, callback2, ...]}
        self.hooks: Dict[str, List[Callable]] = {}
        
        info(f"插件管理器初始化完成。系统插件目录: {self.plugin_dir}, 用户插件目录: {self.user_plugin_dir}")
    
    def load_all_plugins(self) -> None:
        """加载所有可用的插件"""
        info("开始加载所有插件...")
        
        # 获取所有插件名称（不包括以_开头的文件）
        plugin_names = [name for name in self.plugin_source.list_plugins() 
                       if not name.startswith('_')]
        
        loaded_count = 0
        for plugin_name in plugin_names:
            try:
                if self.load_plugin(plugin_name):
                    loaded_count += 1
            except Exception as e:
                error(f"加载插件 '{plugin_name}' 时出错: {str(e)}")
        
        info(f"插件加载完成。成功加载 {loaded_count}/{len(plugin_names)} 个插件")
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        加载单个插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功加载
        """
        if plugin_name in self.plugins:
            debug(f"插件 '{plugin_name}' 已经加载")
            return True
        
        try:
            # 从插件源加载插件模块
            plugin_module = self.plugin_source.load_plugin(plugin_name)
            
            # 获取插件类（约定是插件模块中的Plugin类）
            if not hasattr(plugin_module, 'Plugin'):
                warning(f"插件 '{plugin_name}' 格式无效: 缺少Plugin类")
                return False
            
            plugin_class = getattr(plugin_module, 'Plugin')
            
            # 实例化插件
            plugin_instance = plugin_class()
            
            # 获取插件信息
            plugin_info = {
                'name': getattr(plugin_instance, 'name', plugin_name),
                'version': getattr(plugin_instance, 'version', '0.1.0'),
                'author': getattr(plugin_instance, 'author', '未知'),
                'description': getattr(plugin_instance, 'description', '无描述'),
                'plugin_type': getattr(plugin_instance, 'plugin_type', '通用'),
                'requires': getattr(plugin_instance, 'requires', []),
                'settings': getattr(plugin_instance, 'settings', {}),
                'enabled': True
            }
            
            # 检查依赖关系
            for dependency in plugin_info.get('requires', []):
                if dependency not in self.plugins:
                    warning(f"插件 '{plugin_name}' 依赖 '{dependency}' 未满足")
                    return False
            
            # 保存插件信息和实例
            self.plugins[plugin_name] = plugin_instance
            self.plugin_info[plugin_name] = plugin_info
            
            # 按类型组织
            plugin_type = plugin_info['plugin_type']
            if plugin_type not in self.plugin_types:
                self.plugin_types[plugin_type] = []
            self.plugin_types[plugin_type].append(plugin_name)
            
            # 初始化插件
            if hasattr(plugin_instance, 'initialize'):
                plugin_instance.initialize(self.app)
            
            # 注册插件的事件监听器
            if hasattr(plugin_instance, 'get_event_listeners'):
                listeners = plugin_instance.get_event_listeners()
                for event_name, callback in listeners.items():
                    self.register_event_listener(event_name, callback)
            
            # 注册插件的钩子函数
            if hasattr(plugin_instance, 'get_hooks'):
                hooks = plugin_instance.get_hooks()
                for hook_name, callback in hooks.items():
                    self.register_hook(hook_name, callback)
            
            info(f"插件 '{plugin_info['name']}' v{plugin_info['version']} 加载成功")
            return True
            
        except Exception as e:
            error(f"加载插件 '{plugin_name}' 时出错: {str(e)}")
            import traceback
            error(traceback.format_exc())
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功卸载
        """
        if plugin_name not in self.plugins:
            warning(f"插件 '{plugin_name}' 未加载，无法卸载")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            plugin_info = self.plugin_info[plugin_name]
            
            # 调用插件的清理方法
            if hasattr(plugin, 'cleanup'):
                plugin.cleanup()
            
            # 从类型列表中移除
            plugin_type = plugin_info['plugin_type']
            if plugin_type in self.plugin_types and plugin_name in self.plugin_types[plugin_type]:
                self.plugin_types[plugin_type].remove(plugin_name)
            
            # 移除事件监听器
            self._remove_plugin_event_listeners(plugin_name)
            
            # 移除钩子函数
            self._remove_plugin_hooks(plugin_name)
            
            # 从字典中删除
            del self.plugins[plugin_name]
            del self.plugin_info[plugin_name]
            
            info(f"插件 '{plugin_name}' 已成功卸载")
            return True
            
        except Exception as e:
            error(f"卸载插件 '{plugin_name}' 时出错: {str(e)}")
            return False
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 操作是否成功
        """
        if plugin_name not in self.plugins:
            warning(f"插件 '{plugin_name}' 未加载，无法启用")
            return False
        
        plugin = self.plugins[plugin_name]
        if hasattr(plugin, 'enable'):
            try:
                plugin.enable()
                self.plugin_info[plugin_name]['enabled'] = True
                info(f"插件 '{plugin_name}' 已启用")
                return True
            except Exception as e:
                error(f"启用插件 '{plugin_name}' 时出错: {str(e)}")
                return False
        else:
            # 默认情况下，如果插件没有实现enable方法，则简单地标记为启用
            self.plugin_info[plugin_name]['enabled'] = True
            info(f"插件 '{plugin_name}' 已标记为启用")
            return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 操作是否成功
        """
        if plugin_name not in self.plugins:
            warning(f"插件 '{plugin_name}' 未加载，无法禁用")
            return False
        
        plugin = self.plugins[plugin_name]
        if hasattr(plugin, 'disable'):
            try:
                plugin.disable()
                self.plugin_info[plugin_name]['enabled'] = False
                info(f"插件 '{plugin_name}' 已禁用")
                return True
            except Exception as e:
                error(f"禁用插件 '{plugin_name}' 时出错: {str(e)}")
                return False
        else:
            # 默认情况下，如果插件没有实现disable方法，则简单地标记为禁用
            self.plugin_info[plugin_name]['enabled'] = False
            info(f"插件 '{plugin_name}' 已标记为禁用")
            return True
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """
        获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例，如果不存在则返回None
        """
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: str) -> List[str]:
        """
        获取指定类型的所有插件名称
        
        Args:
            plugin_type: 插件类型
            
        Returns:
            List[str]: 插件名称列表
        """
        return self.plugin_types.get(plugin_type, [])
    
    def register_event_listener(self, event_name: str, callback: Callable) -> None:
        """
        注册事件监听器
        
        Args:
            event_name: 事件名称
            callback: 回调函数
        """
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        
        if callback not in self.event_listeners[event_name]:
            self.event_listeners[event_name].append(callback)
            debug(f"已注册事件监听器: {event_name}")
    
    def trigger_event(self, event_name: str, *args, **kwargs) -> None:
        """
        触发事件，通知所有监听该事件的插件
        
        Args:
            event_name: 事件名称
            *args, **kwargs: 传递给回调函数的参数
        """
        if event_name not in self.event_listeners:
            return
        
        debug(f"触发事件: {event_name}，监听器数量: {len(self.event_listeners[event_name])}")
        
        for callback in self.event_listeners[event_name]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                error(f"执行事件 '{event_name}' 的回调函数时出错: {str(e)}")
    
    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """
        注册钩子函数
        
        Args:
            hook_name: 钩子名称
            callback: 回调函数
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        if callback not in self.hooks[hook_name]:
            self.hooks[hook_name].append(callback)
            debug(f"已注册钩子: {hook_name}")
    
    def apply_hook(self, hook_name: str, value: Any, *args, **kwargs) -> Any:
        """
        应用钩子函数链处理数据
        
        Args:
            hook_name: 钩子名称
            value: 初始值
            *args, **kwargs: 额外参数
            
        Returns:
            Any: 经过处理的值
        """
        if hook_name not in self.hooks:
            return value
        
        result = value
        for callback in self.hooks[hook_name]:
            try:
                result = callback(result, *args, **kwargs)
            except Exception as e:
                error(f"执行钩子 '{hook_name}' 的回调函数时出错: {str(e)}")
        
        return result
    
    def _remove_plugin_event_listeners(self, plugin_name: str) -> None:
        """移除指定插件的所有事件监听器"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return
        
        if not hasattr(plugin, 'get_event_listeners'):
            return
        
        listeners = plugin.get_event_listeners()
        for event_name, callback in listeners.items():
            if event_name in self.event_listeners and callback in self.event_listeners[event_name]:
                self.event_listeners[event_name].remove(callback)
    
    def _remove_plugin_hooks(self, plugin_name: str) -> None:
        """移除指定插件的所有钩子函数"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return
        
        if not hasattr(plugin, 'get_hooks'):
            return
        
        hooks = plugin.get_hooks()
        for hook_name, callback in hooks.items():
            if hook_name in self.hooks and callback in self.hooks[hook_name]:
                self.hooks[hook_name].remove(callback)

# 全局插件管理器实例
plugin_manager = None

def init_plugin_manager(app=None):
    """初始化全局插件管理器"""
    global plugin_manager
    if plugin_manager is None:
        plugin_manager = PluginManager(app)
    return plugin_manager

def get_plugin_manager():
    """获取全局插件管理器实例"""
    global plugin_manager
    if plugin_manager is None:
        plugin_manager = PluginManager()
    return plugin_manager 