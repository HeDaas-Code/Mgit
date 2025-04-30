#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Dict, Any, List, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QListWidget, QListWidgetItem, QStackedWidget, QCheckBox,
                           QMessageBox, QFileDialog, QScrollArea, QFrame, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from qfluentwidgets import (SearchLineEdit, SwitchButton, InfoBar, InfoBarPosition, 
                          PrimaryPushButton, TransparentPushButton, FluentIcon,
                          SubtitleLabel, BodyLabel, CardWidget, MessageBox)

from src.utils.plugin_manager import get_plugin_manager
from src.utils.config_manager import ConfigManager
from src.utils.logger import info, warning, error, debug

class PluginItem(QWidget):
    """插件项小部件 - 显示单个插件的信息和控制"""
    
    enableChanged = pyqtSignal(str, bool)  # 插件名称和启用状态
    configureClicked = pyqtSignal(str)  # 插件名称
    
    def __init__(self, plugin_name: str, plugin_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.plugin_info = plugin_info
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        # 创建布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 插件信息区域
        infoLayout = QVBoxLayout()
        
        # 名称和版本 (粗体)
        nameLabel = SubtitleLabel(f"{self.plugin_info['name']} v{self.plugin_info['version']}")
        infoLayout.addWidget(nameLabel)
        
        # 类型和作者
        metaText = f"类型: {self.plugin_info['plugin_type']} | 作者: {self.plugin_info['author']}"
        metaLabel = BodyLabel(metaText)
        metaLabel.setObjectName("pluginMetaLabel")
        infoLayout.addWidget(metaLabel)
        
        # 描述
        descLabel = BodyLabel(self.plugin_info['description'])
        descLabel.setWordWrap(True)
        descLabel.setObjectName("pluginDescLabel")
        infoLayout.addWidget(descLabel)
        
        layout.addLayout(infoLayout, 1)  # 1是伸展因子，占据大部分空间
        
        # 控制区域
        controlLayout = QVBoxLayout()
        controlLayout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 启用/禁用开关
        self.enableSwitch = SwitchButton(self)
        self.enableSwitch.setChecked(self.plugin_info.get('enabled', True))
        self.enableSwitch.checkedChanged.connect(self.onEnableChanged)
        
        enableLayout = QHBoxLayout()
        enableLayout.addWidget(QLabel("启用"))
        enableLayout.addWidget(self.enableSwitch)
        controlLayout.addLayout(enableLayout)
        
        # 设置按钮 (如果插件有设置界面)
        if self.plugin_info.get('has_settings', False):
            self.settingsButton = TransparentPushButton("设置", self)
            self.settingsButton.setIcon(FluentIcon.SETTING)
            self.settingsButton.clicked.connect(self.onConfigureClicked)
            controlLayout.addWidget(self.settingsButton)
        
        layout.addLayout(controlLayout)
        
    def onEnableChanged(self, checked):
        """启用状态变更"""
        self.enableChanged.emit(self.plugin_name, checked)
        
    def onConfigureClicked(self):
        """设置按钮点击"""
        self.configureClicked.emit(self.plugin_name)
        
    def updateInfo(self, plugin_info):
        """更新插件信息"""
        self.plugin_info = plugin_info
        self.enableSwitch.setChecked(self.plugin_info.get('enabled', True))

class PluginManager(QWidget):
    """插件管理界面 - 管理所有插件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.plugin_manager = get_plugin_manager()
        self.initUI()
        self.loadPlugins()
        
    def initUI(self):
        """初始化UI"""
        self.setObjectName("pluginManagerWidget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 顶部标题和搜索区域
        topLayout = QHBoxLayout()
        
        title = SubtitleLabel("插件管理")
        title.setObjectName("pluginManagerTitle")
        topLayout.addWidget(title)
        
        # 添加搜索框
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText("搜索插件...")
        self.searchEdit.textChanged.connect(self.filterPlugins)
        topLayout.addWidget(self.searchEdit)
        
        layout.addLayout(topLayout)
        
        # 添加按钮区域
        buttonLayout = QHBoxLayout()
        
        # 导入插件按钮
        self.importButton = PrimaryPushButton("导入插件", self)
        self.importButton.setIcon(FluentIcon.ADD)
        self.importButton.clicked.connect(self.importPlugin)
        buttonLayout.addWidget(self.importButton)
        
        # 刷新按钮
        self.refreshButton = TransparentPushButton("刷新", self)
        self.refreshButton.setIcon(FluentIcon.SYNC)
        self.refreshButton.clicked.connect(self.refreshPlugins)
        buttonLayout.addWidget(self.refreshButton)
        
        buttonLayout.addStretch(1)  # 添加弹性空间
        
        # 全部启用/禁用按钮
        self.enableAllButton = TransparentPushButton("全部启用", self)
        self.enableAllButton.clicked.connect(self.enableAllPlugins)
        buttonLayout.addWidget(self.enableAllButton)
        
        self.disableAllButton = TransparentPushButton("全部禁用", self)
        self.disableAllButton.clicked.connect(self.disableAllPlugins)
        buttonLayout.addWidget(self.disableAllButton)
        
        layout.addLayout(buttonLayout)
        
        # 插件列表区域
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.NoFrame)
        
        self.pluginListWidget = QWidget()
        self.pluginListLayout = QVBoxLayout(self.pluginListWidget)
        self.pluginListLayout.setContentsMargins(0, 0, 0, 0)
        self.pluginListLayout.setSpacing(5)
        self.pluginListLayout.addStretch(1)  # 添加弹性空间使插件项靠上排列
        
        self.scrollArea.setWidget(self.pluginListWidget)
        layout.addWidget(self.scrollArea, 1)  # 1是伸展因子
        
        # 底部状态区域
        self.statusLabel = QLabel("找到 0 个插件")
        layout.addWidget(self.statusLabel)
        
    def loadPlugins(self):
        """加载所有插件"""
        # 清除现有插件列表
        self._clearPluginList()
        
        # 获取所有插件信息
        plugins_info = self.plugin_manager.plugin_info
        
        # 按类型分组
        plugins_by_type = {}
        for plugin_name, plugin_info in plugins_info.items():
            plugin_type = plugin_info.get('plugin_type', '通用')
            if plugin_type not in plugins_by_type:
                plugins_by_type[plugin_type] = []
            plugins_by_type[plugin_type].append((plugin_name, plugin_info))
        
        # 按类型添加插件
        for plugin_type, plugins in plugins_by_type.items():
            # 添加类型分组
            group_box = QGroupBox(plugin_type)
            group_layout = QVBoxLayout(group_box)
            group_layout.setContentsMargins(5, 15, 5, 5)
            group_layout.setSpacing(5)
            
            # 添加该类型的所有插件
            for plugin_name, plugin_info in plugins:
                # 检查插件是否有设置界面
                plugin = self.plugin_manager.get_plugin(plugin_name)
                has_settings = plugin and hasattr(plugin, 'get_settings_widget') and plugin.get_settings_widget() is not None
                plugin_info['has_settings'] = has_settings
                
                # 检查插件是否启用
                plugin_info['enabled'] = self.config_manager.is_plugin_enabled(plugin_name)
                
                # 创建插件项
                plugin_item = PluginItem(plugin_name, plugin_info, self)
                plugin_item.enableChanged.connect(self.onPluginEnableChanged)
                plugin_item.configureClicked.connect(self.onPluginConfigureClicked)
                
                # 添加到卡片中
                card = CardWidget(self)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(0, 0, 0, 0)
                card_layout.addWidget(plugin_item)
                
                group_layout.addWidget(card)
            
            # 添加到主布局
            self.pluginListLayout.insertWidget(self.pluginListLayout.count() - 1, group_box)
        
        # 更新状态栏
        self.statusLabel.setText(f"找到 {len(plugins_info)} 个插件")
    
    def _clearPluginList(self):
        """清除插件列表"""
        # 移除所有子项，但保留最后的弹性空间
        while self.pluginListLayout.count() > 1:
            item = self.pluginListLayout.itemAt(0)
            if item.widget():
                item.widget().deleteLater()
            self.pluginListLayout.removeItem(item)
    
    def filterPlugins(self, text):
        """按搜索文本过滤插件"""
        search_text = text.lower()
        
        # 遍历所有组
        for i in range(self.pluginListLayout.count() - 1):  # -1 是因为最后一项是弹性空间
            group_box = self.pluginListLayout.itemAt(i).widget()
            if not isinstance(group_box, QGroupBox):
                continue
                
            # 检查组内每个插件卡片
            group_visible = False
            group_layout = group_box.layout()
            
            for j in range(group_layout.count()):
                card = group_layout.itemAt(j).widget()
                if not isinstance(card, CardWidget):
                    continue
                    
                # 获取卡片内的插件项
                plugin_item = card.layout().itemAt(0).widget()
                if not isinstance(plugin_item, PluginItem):
                    continue
                
                # 检查是否匹配
                plugin_info = plugin_item.plugin_info
                match = (
                    search_text in plugin_info['name'].lower() or
                    search_text in plugin_info['description'].lower() or
                    search_text in plugin_info['author'].lower() or
                    search_text in plugin_info['plugin_type'].lower()
                )
                
                # 设置卡片可见性
                card.setVisible(match)
                if match:
                    group_visible = True
            
            # 设置组可见性
            group_box.setVisible(group_visible)
    
    def refreshPlugins(self):
        """刷新插件列表"""
        # 重新加载所有插件
        self.plugin_manager.load_all_plugins()
        self.loadPlugins()
        
        # 显示通知
        InfoBar.success(
            title="插件已刷新",
            content="已重新加载所有可用插件",
            orient=Qt.Horizontal,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def importPlugin(self):
        """导入插件"""
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "", "Python文件 (*.py);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        # 检查文件名作为插件名
        plugin_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 检查是否已存在同名插件
        plugins_dir = self.plugin_manager.user_plugin_dir
        target_path = os.path.join(plugins_dir, f"{plugin_name}.py")
        
        if os.path.exists(target_path):
            # 提示用户确认覆盖
            result = MessageBox(
                "确认覆盖",
                f"插件 '{plugin_name}' 已存在，是否覆盖?",
                self
            )
            if not result.exec_():
                return
        
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 复制插件文件
            import shutil
            shutil.copy2(file_path, target_path)
            
            # 尝试加载插件
            loaded = self.plugin_manager.load_plugin(plugin_name)
            
            if loaded:
                # 刷新列表
                self.loadPlugins()
                
                # 显示成功通知
                InfoBar.success(
                    title="插件导入成功",
                    content=f"插件 '{plugin_name}' 已成功导入",
                    orient=Qt.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                # 显示错误通知
                InfoBar.error(
                    title="插件加载失败",
                    content=f"插件 '{plugin_name}' 导入成功但无法加载，请检查插件格式是否正确",
                    orient=Qt.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                
        except Exception as e:
            # 显示错误通知
            InfoBar.error(
                title="插件导入失败",
                content=f"导入插件时出错: {str(e)}",
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            error(f"导入插件 '{plugin_name}' 失败: {str(e)}")
    
    def onPluginEnableChanged(self, plugin_name, enabled):
        """插件启用状态变更"""
        # 更新配置
        self.config_manager.set_plugin_enabled(plugin_name, enabled)
        
        # 获取插件实例
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if plugin:
            try:
                # 调用插件的启用/禁用方法
                if enabled:
                    plugin.enable()
                else:
                    plugin.disable()
                    
                # 提示成功
                action_text = "启用" if enabled else "禁用"
                InfoBar.success(
                    title=f"插件已{action_text}",
                    content=f"插件 '{plugin_name}' 已成功{action_text}",
                    orient=Qt.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                
            except Exception as e:
                error(f"插件 '{plugin_name}' {action_text}失败: {str(e)}")
                
                # 提示错误
                InfoBar.error(
                    title=f"插件{action_text}失败",
                    content=f"插件 '{plugin_name}' {action_text}时出错: {str(e)}",
                    orient=Qt.Horizontal,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def onPluginConfigureClicked(self, plugin_name):
        """插件设置按钮点击"""
        # 获取插件实例
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            return
            
        # 获取设置界面
        settings_widget = plugin.get_settings_widget()
        if not settings_widget:
            InfoBar.warning(
                title="无法配置插件",
                content=f"插件 '{plugin_name}' 没有提供设置界面",
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
            
        # 创建设置对话框
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{plugin.name} 设置")
        dialog.setMinimumWidth(400)
        
        dialog_layout = QVBoxLayout(dialog)
        
        # 添加设置界面
        dialog_layout.addWidget(settings_widget)
        
        # 添加确定/取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 如果用户点击了确定，可以在这里保存设置
            InfoBar.success(
                title="设置已保存",
                content=f"插件 '{plugin_name}' 的设置已更新",
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def enableAllPlugins(self):
        """启用所有插件"""
        count = 0
        for plugin_name in self.plugin_manager.plugins:
            if not self.config_manager.is_plugin_enabled(plugin_name):
                self.config_manager.set_plugin_enabled(plugin_name, True)
                plugin = self.plugin_manager.get_plugin(plugin_name)
                if plugin:
                    try:
                        plugin.enable()
                        count += 1
                    except:
                        pass
        
        # 刷新界面
        self.loadPlugins()
        
        # 提示成功
        InfoBar.success(
            title="已启用所有插件",
            content=f"成功启用了 {count} 个插件",
            orient=Qt.Horizontal,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def disableAllPlugins(self):
        """禁用所有插件"""
        count = 0
        for plugin_name in self.plugin_manager.plugins:
            if self.config_manager.is_plugin_enabled(plugin_name):
                self.config_manager.set_plugin_enabled(plugin_name, False)
                plugin = self.plugin_manager.get_plugin(plugin_name)
                if plugin:
                    try:
                        plugin.disable()
                        count += 1
                    except:
                        pass
        
        # 刷新界面
        self.loadPlugins()
        
        # 提示成功
        InfoBar.success(
            title="已禁用所有插件",
            content=f"成功禁用了 {count} 个插件",
            orient=Qt.Horizontal,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        ) 