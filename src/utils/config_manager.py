#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any, List, Optional

class ConfigManager(QObject):
    """ 配置管理类，用于保存和加载配置 """
    
    # 定义信号，当最近仓库列表更新时触发
    recentRepositoriesChanged = pyqtSignal()
    # 定义信号，当编辑器配置更新时触发
    editorConfigChanged = pyqtSignal()
    # 定义信号，当插件设置更新时触发
    pluginSettingsChanged = pyqtSignal(str)  # 参数为插件名称
    # 定义信号，当启用/禁用插件时触发
    pluginStatusChanged = pyqtSignal(str, bool)  # 参数为插件名称和状态
    
    # 单例模式
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_file=None):
        """ 初始化配置管理器 
        Args:
            config_file: 配置文件路径，默认为用户目录下的.mgit/config.json
        """
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        super().__init__()
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
            'theme': 'auto',
            'max_recent_count': 10,
            'editor': {
                'auto_save_on_focus_change': True,  # 焦点变化时自动保存
                'auto_save_interval': 60  # 自动保存间隔（秒）
            },
            'plugins': {
                'enabled': [],  # 已启用的插件列表
                'disabled': [],  # 已禁用的插件列表
                'settings': {}  # 插件设置 {plugin_name: {setting_key: value}}
            }
        }
        
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """ 加载配置 """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    # 递归更新配置，保留默认值和结构
                    self._update_config_recursive(self.config, loaded_config)
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
    
    def _update_config_recursive(self, target, source):
        """递归更新配置，保留目标字典的结构
        
        Args:
            target: 目标字典（默认配置）
            source: 源字典（加载的配置）
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config_recursive(target[key], value)
            else:
                target[key] = value
        
    def save_config(self):
        """ 保存配置 """
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")
            
    def add_recent_repository(self, repo_path):
        """ 添加最近使用的仓库 
        Args:
            repo_path: 仓库路径
        """
        # 确保路径格式一致
        repo_path = os.path.normpath(repo_path)
        
        # 如果已经是第一个仓库，不做任何操作
        if self.config['recent_repositories'] and self.config['recent_repositories'][0] == repo_path:
            return
            
        # 检查是否已经在列表中
        if repo_path in self.config['recent_repositories']:
            # 如果已经存在，移除旧的
            self.config['recent_repositories'].remove(repo_path)
            
        # 添加到列表开头
        self.config['recent_repositories'].insert(0, repo_path)
        
        # 限制数量
        max_count = self.config['max_recent_count']
        if len(self.config['recent_repositories']) > max_count:
            self.config['recent_repositories'] = self.config['recent_repositories'][:max_count]
            
        # 保存配置
        self.save_config()
        
        # 发出信号通知仓库列表已更新
        self.recentRepositoriesChanged.emit()
        
    def get_recent_repositories(self):
        """ 获取最近使用的仓库列表 
        Returns:
            list: 仓库路径列表
        """
        # 过滤掉不存在的仓库
        valid_repos = [repo for repo in self.config['recent_repositories'] 
                      if os.path.exists(repo) and os.path.exists(os.path.join(repo, '.git'))]
        
        # 更新配置
        if len(valid_repos) != len(self.config['recent_repositories']):
            self.config['recent_repositories'] = valid_repos
            self.save_config()
            # 如果有无效仓库被过滤，发出信号
            self.recentRepositoriesChanged.emit()
            
        return valid_repos
        
    def clear_recent_repositories(self):
        """ 清空最近使用的仓库列表 """
        self.config['recent_repositories'] = []
        self.save_config()
        
        # 发出信号通知仓库列表已清空
        self.recentRepositoriesChanged.emit()
        
    def set_theme(self, theme):
        """ 设置主题 
        Args:
            theme: 主题名称，可选值：'light', 'dark', 'auto'
        """
        self.config['theme'] = theme
        self.save_config()
        
    def get_theme(self):
        """ 获取主题 
        Returns:
            str: 主题名称
        """
        return self.config['theme']

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
    
    # 插件相关方法
    
    def get_enabled_plugins(self) -> List[str]:
        """获取已启用的插件列表
        
        Returns:
            List[str]: 插件名称列表
        """
        return self.config['plugins'].get('enabled', [])
    
    def get_disabled_plugins(self) -> List[str]:
        """获取已禁用的插件列表
        
        Returns:
            List[str]: 插件名称列表
        """
        return self.config['plugins'].get('disabled', [])
    
    def set_plugin_enabled(self, plugin_name: str, enabled: bool) -> None:
        """设置插件启用状态
        
        Args:
            plugin_name: 插件名称
            enabled: 是否启用
        """
        enabled_list = self.config['plugins'].get('enabled', [])
        disabled_list = self.config['plugins'].get('disabled', [])
        
        # 从两个列表中都移除
        if plugin_name in enabled_list:
            enabled_list.remove(plugin_name)
        if plugin_name in disabled_list:
            disabled_list.remove(plugin_name)
        
        # 添加到正确的列表
        if enabled:
            enabled_list.append(plugin_name)
        else:
            disabled_list.append(plugin_name)
        
        # 更新配置
        self.config['plugins']['enabled'] = enabled_list
        self.config['plugins']['disabled'] = disabled_list
        self.save_config()
        
        # 发送信号
        self.pluginStatusChanged.emit(plugin_name, enabled)
    
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