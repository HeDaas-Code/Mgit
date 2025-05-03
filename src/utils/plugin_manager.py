#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import importlib.util
import subprocess
import pkg_resources
from typing import Dict, List, Any, Type, Optional, Callable, Set
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
        
        # 已安装的插件依赖包
        self.installed_dependencies: Set[str] = set()
        
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
        
        # 如果有安装的依赖，更新requirements.txt
        if self.installed_dependencies:
            self._update_requirements_file()
            
        info(f"插件加载完成。成功加载 {loaded_count}/{len(plugin_names)} 个插件")
    
    def _check_package_installed(self, package_name: str) -> bool:
        """
        检查Python包是否已安装
        
        Args:
            package_name: 包名称，可以包含版本要求，如 'requests>=2.25.0'
            
        Returns:
            bool: 是否已安装且满足版本要求
        """
        try:
            if '>=' in package_name or '==' in package_name or '<=' in package_name:
                pkg_resources.require(package_name)
            else:
                pkg_resources.get_distribution(package_name)
            return True
        except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
            return False
    
    def _install_packages(self, packages):
        """
        安装Python包
        
        Args:
            packages: 包名列表，格式如 ["numpy>=1.19.0", "pandas"]
            
        Returns:
            bool: 是否成功安装所有包
        """
        if not packages:
            return True
            
        # 检查pip命令
        try:
            import subprocess
            import sys
            
            # 确定pip命令
            if getattr(sys, 'frozen', False):
                # 在PyInstaller环境中
                if sys.platform == 'win32':
                    pip_cmd = [sys.executable, "-m", "pip"]
                else:
                    pip_cmd = ["pip3"]
            else:
                # 在开发环境中
                if sys.platform == 'win32':
                    pip_cmd = [sys.executable, "-m", "pip"]
                else:
                    pip_cmd = ["pip3"]
            
            # 用pip安装包
            for package in packages:
                # 忽略已安装的包
                if self._check_package_installed(package):
                    continue
                    
                from src.utils.logger import info
                info(f"正在安装插件依赖: {package}")
                
                # 拼接安装命令
                install_cmd = pip_cmd + ["install", "--user", package]
                
                # 执行安装
                result = subprocess.run(
                    install_cmd, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 记录安装的包
                if result.returncode == 0:
                    pkg_name = package.split(">=")[0].split("==")[0].split("<=")[0].strip()
                    self.installed_dependencies.add(pkg_name)
                    info(f"包 {package} 安装成功")
                else:
                    from src.utils.logger import error
                    error(f"包 {package} 安装失败: {result.stderr}")
                    return False
                    
            return True
            
        except Exception as e:
            from src.utils.logger import error
            error(f"安装依赖包时出错: {str(e)}")
            return False
    
    def _update_requirements_file(self) -> None:
        """更新requirements.txt文件，添加插件所需的依赖包"""
        try:
            # 获取项目根目录的requirements.txt文件路径
            requirements_path = os.path.abspath(os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'requirements.txt'
            ))
            
            # 如果文件不存在，创建一个新文件
            if not os.path.exists(requirements_path):
                with open(requirements_path, 'w', encoding='utf-8') as f:
                    f.write("# MGit依赖包列表\n\n")
                    for package in sorted(self.installed_dependencies):
                        f.write(f"{package}\n")
                info(f"已创建新的requirements.txt文件并添加插件依赖")
                return
            
            # 读取现有的requirements.txt文件
            with open(requirements_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析现有的依赖包
            existing_packages = set()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and line not in existing_packages:
                    package = line.split('#')[0].strip()  # 移除注释
                    existing_packages.add(package)
            
            # 添加新的依赖包
            new_packages = self.installed_dependencies - existing_packages
            if not new_packages:
                debug("无需更新requirements.txt文件")
                return
            
            # 确定插件依赖部分
            plugin_section_start = -1
            for i, line in enumerate(lines):
                if "# 插件依赖" in line:
                    plugin_section_start = i
                    break
            
            # 如果没有找到插件依赖部分，添加一个
            if plugin_section_start == -1:
                lines.append("\n# 插件依赖\n")
                plugin_section_start = len(lines) - 1
            
            # 在插件依赖部分后添加新的依赖包
            for package in sorted(new_packages):
                lines.insert(plugin_section_start + 1, f"{package}\n")
                plugin_section_start += 1
            
            # 写回文件
            with open(requirements_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            info(f"已更新requirements.txt文件，添加了 {len(new_packages)} 个插件依赖")
            
        except Exception as e:
            error(f"更新requirements.txt文件时出错: {str(e)}")
    
    def _check_plugin_dependencies(self, plugin_name: str, dependencies: List[str]) -> bool:
        """
        检查并安装插件的Python包依赖
        
        Args:
            plugin_name: 插件名称
            dependencies: 依赖包列表
            
        Returns:
            bool: 是否所有依赖都已满足
        """
        if not dependencies:
            return True
            
        info(f"检查插件 '{plugin_name}' 的依赖: {dependencies}")
        
        # 检查每个依赖是否已安装
        missing_packages = []
        for dependency in dependencies:
            if not self._check_package_installed(dependency):
                missing_packages.append(dependency)
        
        # 如果有未安装的依赖，尝试安装
        if missing_packages:
            info(f"插件 '{plugin_name}' 缺少依赖: {missing_packages}")
            
            # 确认是否自动安装依赖
            should_install = True
            
            # 尝试获取配置管理器的设置
            try:
                from src.utils.config_manager import ConfigManager
                config = ConfigManager()
                auto_install = config.get_setting('auto_install_dependencies', True)
                
                # 如果禁用了自动安装，询问用户
                if not auto_install and hasattr(sys, 'exit') and 'PyQt5' in sys.modules:
                    from PyQt5.QtWidgets import QMessageBox, QApplication
                    app = QApplication.instance() or QApplication(sys.argv)
                    
                    response = QMessageBox.question(
                        None,
                        "安装插件依赖",
                        f"插件 '{plugin_name}' 需要安装以下依赖:\n" + 
                        "\n".join(missing_packages) + 
                        "\n\n是否允许安装这些依赖?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    should_install = response == QMessageBox.Yes
            except:
                # 如果无法获取配置或显示对话框，默认自动安装
                pass
            
            # 如果用户拒绝安装，返回False
            if not should_install:
                warning(f"用户拒绝安装插件 '{plugin_name}' 的依赖")
                return False
            
            # 尝试安装缺少的依赖
            info(f"正在安装插件 '{plugin_name}' 的缺少依赖: {missing_packages}")
            
            # 安装所有缺少的依赖包
            if not self._install_packages(missing_packages):
                warning(f"无法安装插件 '{plugin_name}' 的所有依赖")
                return False
            
            info(f"插件 '{plugin_name}' 的所有依赖已安装")
        
        return True
    
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
                'package_dependencies': getattr(plugin_instance, 'package_dependencies', []),
                'settings': getattr(plugin_instance, 'settings', {}),
                'enabled': True
            }
            
            # 检查插件依赖关系
            for dependency in plugin_info.get('requires', []):
                if dependency not in self.plugins:
                    warning(f"插件 '{plugin_name}' 依赖 '{dependency}' 未满足")
                    return False
            
            # 检查并安装Python包依赖
            package_dependencies = plugin_info.get('package_dependencies', [])
            if package_dependencies and not self._check_plugin_dependencies(plugin_name, package_dependencies):
                warning(f"插件 '{plugin_name}' 的Python包依赖未满足，无法加载")
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