#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

class ConfigManager(QObject):
    """ 配置管理类，用于保存和加载配置 """
    
    # 定义信号
    recentRepositoriesChanged = pyqtSignal()  # 最近仓库列表变化信号
    editorConfigChanged = pyqtSignal()  # 编辑器配置变化信号
    pluginSettingsChanged = pyqtSignal(str)  # 插件设置变更信号，参数为插件名
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file=None):
        """ 初始化配置管理器 
        Args:
            config_file: 配置文件路径，默认为用户目录下的.mgit/config.json
        """
        # 始终调用父类的__init__方法
        super().__init__()
        
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._initialized = True
        
        if config_file is None:
            # 默认配置文件位置
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, '.mgit')
            
            # 确保目录存在
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            self.config_file = os.path.join(config_dir, 'config.json')
        else:
            self.config_file = config_file
            
        # 默认配置
        self.config = {
            'recent_repositories': [],
            'max_recent_count': 10,
            'editor': {
                'auto_save_on_focus_change': True,  # 焦点变化时自动保存
                'auto_save_interval': 60  # 自动保存间隔（秒）
            },
            'plugins': {
                'enabled': [],  # 已启用的插件列表
                'disabled': [],  # 已禁用的插件列表
                'settings': {}  # 插件设置 {plugin_name: {setting_key: value}}
            },
            'appearance': {
                'theme': 'auto'  # 主题设置: 'light', 'dark', 'auto'(跟随系统)
            }
        }
        
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """ 从文件加载配置 """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    # 更新配置，但保留默认值
                    self._update_nested_dict(self.config, loaded_config)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            
    def _update_nested_dict(self, d, u):
        """ 递归更新嵌套字典 """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
                
    def save_config(self):
        """ 保存配置到文件 """
        try:
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            
    def add_recent_repository(self, repo_path):
        """ 添加最近使用的仓库 
        Args:
            repo_path: 仓库路径
        """
        # 确保路径是绝对路径
        repo_path = os.path.abspath(repo_path)
        
        # 如果路径已经在列表中，则移除
        if repo_path in self.config['recent_repositories']:
            self.config['recent_repositories'].remove(repo_path)
            
        # 添加到列表开头
        self.config['recent_repositories'].insert(0, repo_path)
        
        # 限制列表长度
        max_count = self.config.get('max_recent_count', 10)
        if len(self.config['recent_repositories']) > max_count:
            self.config['recent_repositories'] = self.config['recent_repositories'][:max_count]
            
        # 保存配置
        self.save_config()
        
        # 发出信号通知仓库列表已更新
        self.recentRepositoriesChanged.emit()
        
    def get_recent_repositories(self):
        """ 获取最近使用的仓库列表 
        Returns:
            List[str]: 仓库路径列表
        """
        # 过滤不存在的路径
        valid_repos = [
            repo for repo in self.config['recent_repositories'] 
            if os.path.exists(repo) and os.path.isdir(repo)
        ]
        
        # 更新配置，如果有无效路径被过滤掉
        if len(valid_repos) != len(self.config['recent_repositories']):
            self.config['recent_repositories'] = valid_repos
            self.save_config()
            
        return valid_repos
        
    def clear_recent_repositories(self):
        """ 清空最近使用的仓库列表 """
        self.config['recent_repositories'] = []
        self.save_config()
        
        # 发出信号通知仓库列表已清空
        self.recentRepositoriesChanged.emit()
        
    def set_auto_save_on_focus_change(self, enabled):
        """设置失去焦点时是否自动保存
        Args:
            enabled: 是否启用
        """
        if 'editor' not in self.config:
            self.config['editor'] = {}
        self.config['editor']['auto_save_on_focus_change'] = enabled
        self.save_config()
        self.editorConfigChanged.emit()
        
    def get_auto_save_on_focus_change(self):
        """获取失去焦点时是否自动保存
        Returns:
            bool: 是否启用
        """
        if 'editor' not in self.config or 'auto_save_on_focus_change' not in self.config['editor']:
            return True  # 默认启用
        return self.config['editor']['auto_save_on_focus_change']
        
    def set_auto_save_interval(self, seconds):
        """设置自动保存间隔
        Args:
            seconds: 间隔秒数
        """
        if 'editor' not in self.config:
            self.config['editor'] = {}
        self.config['editor']['auto_save_interval'] = max(5, seconds)  # 最小5秒
        self.save_config()
        self.editorConfigChanged.emit()
        
    def get_auto_save_interval(self):
        """获取自动保存间隔
        Returns:
            int: 间隔秒数
        """
        if 'editor' not in self.config or 'auto_save_interval' not in self.config['editor']:
            return 60  # 默认60秒
        return self.config['editor']['auto_save_interval']
    
    def get_theme(self):
        """获取当前主题设置
        Returns:
            str: 主题设置，可能的值: 'light', 'dark', 'auto'
        """
        if 'appearance' not in self.config or 'theme' not in self.config['appearance']:
            return 'auto'  # 默认跟随系统
        return self.config['appearance']['theme']
    
    def set_theme(self, theme):
        """设置当前主题
        Args:
            theme: 主题名称，可选值: 'light', 'dark', 'auto'
        """
        if theme not in ['light', 'dark', 'auto']:
            theme = 'auto'  # 非法值默认为auto
            
        if 'appearance' not in self.config:
            self.config['appearance'] = {}
            
        self.config['appearance']['theme'] = theme
        self.save_config()
    
    def enable_plugin(self, plugin_name: str) -> None:
        """启用插件
        
        Args:
            plugin_name: 插件名称
        """
        disabled_list = self.config['plugins'].get('disabled', [])
        enabled_list = self.config['plugins'].get('enabled', [])
        
        # 从禁用列表中移除
        if plugin_name in disabled_list:
            disabled_list.remove(plugin_name)
        
        # 添加到启用列表
        if plugin_name not in enabled_list:
            enabled_list.append(plugin_name)
        
        self.save_config()
    
    def disable_plugin(self, plugin_name: str) -> None:
        """禁用插件
        
        Args:
            plugin_name: 插件名称
        """
        disabled_list = self.config['plugins'].get('disabled', [])
        enabled_list = self.config['plugins'].get('enabled', [])
        
        # 从启用列表中移除
        if plugin_name in enabled_list:
            enabled_list.remove(plugin_name)
        
        # 添加到禁用列表
        if plugin_name not in disabled_list:
            disabled_list.append(plugin_name)
        
        self.save_config()
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """检查插件是否启用
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否启用
        """
        enabled_list = self.config['plugins'].get('enabled', [])
        disabled_list = self.config['plugins'].get('disabled', [])
        
        # 如果在禁用列表中，则明确禁用
        if plugin_name in disabled_list:
            return False
        
        # 如果在启用列表中，则明确启用
        if plugin_name in enabled_list:
            return True
        
        # 如果两个列表都没有，则默认启用
        return True
    
    def get_plugin_settings(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件设置
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Dict[str, Any]]: 插件设置，如果不存在则返回None
        """
        settings = self.config['plugins'].get('settings', {})
        return settings.get(plugin_name)
    
    def set_plugin_settings(self, plugin_name: str, settings: Dict[str, Any]) -> None:
        """设置插件设置
        
        Args:
            plugin_name: 插件名称
            settings: 设置字典
        """
        if 'settings' not in self.config['plugins']:
            self.config['plugins']['settings'] = {}
        
        self.config['plugins']['settings'][plugin_name] = settings
        self.save_config()
        
        # 发送信号
        self.pluginSettingsChanged.emit(plugin_name)
    
    def set_plugin_setting(self, plugin_name: str, key: str, value: Any) -> None:
        """设置插件单个设置项
        
        Args:
            plugin_name: 插件名称
            key: 设置键
            value: 设置值
        """
        if 'settings' not in self.config['plugins']:
            self.config['plugins']['settings'] = {}
        
        if plugin_name not in self.config['plugins']['settings']:
            self.config['plugins']['settings'][plugin_name] = {}
        
        self.config['plugins']['settings'][plugin_name][key] = value
        self.save_config()
        
        # 发送信号
        self.pluginSettingsChanged.emit(plugin_name)
        
    def get_plugin_setting(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """获取插件单个设置项
        
        Args:
            plugin_name: 插件名称
            key: 设置键
            default: 默认值
            
        Returns:
            Any: 设置值
        """
        settings = self.get_plugin_settings(plugin_name)
        if settings is None:
            return default
        
        return settings.get(key, default) 