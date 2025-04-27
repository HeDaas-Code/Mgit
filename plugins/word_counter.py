#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
单词统计插件 - 为MGit添加单词统计功能
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                           QPushButton, QCheckBox, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt
from src.utils.plugin_base import PluginBase
import logging
import re

# Markdown标识符的正则表达式模式
MD_PATTERNS = [
    r'#+ ',                     # 标题 (# ## ###)
    r'^\s*[-*+]\s+',            # 无序列表项 (- * +)
    r'^\s*\d+\.\s+',            # 有序列表项 (1. 2.)
    r'^\s*>\s+',                # 引用 (> text)
    r'^\s*[-]{3,}\s*$',         # 水平线 (---)
    r'^\s*[*]{3,}\s*$',         # 水平线 (***)
    r'^\s*[_]{3,}\s*$',         # 水平线 (___)
]

# 需要保留内容的Markdown标记
MD_PATTERNS_WITH_CONTENT = [
    (r'\*\*(.*?)\*\*', r'\1'),         # 粗体 (**text**)
    (r'__(.*?)__', r'\1'),             # 粗体 (__text__)
    (r'\*(.*?)\*', r'\1'),             # 斜体 (*text*)
    (r'_(.*?)_', r'\1'),               # 斜体 (_text_)
    (r'~~(.*?)~~', r'\1'),             # 删除线 (~~text~~)
    (r'`(.*?)`', r'\1'),               # 行内代码 (`code`)
    (r'```[\s\S]*?```', r''),          # 代码块 (```code```) - 移除整个代码块
    (r'\[(.*?)\]\(.*?\)', r'\1'),      # 链接 ([text](url)) - 保留链接文本
    (r'!\[.*?\]\(.*?\)', r''),         # 图片 (![alt](url)) - 移除整个图片标记
    (r'\|(.*?)\|', r'\1'),             # 表格行 (|cell|cell|) - 保留单元格内容
]

class WordCounterWidget(QWidget):
    """单词计数器小部件"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 计数信息
        infoLayout = QVBoxLayout()
        
        self.wordCountLabel = QLabel("英文单词数: 0")
        self.chineseCharCountLabel = QLabel("中文字数: 0")
        self.mixedCountLabel = QLabel("混合字数: 0")
        self.charCountLabel = QLabel("总字符数: 0")
        self.lineCountLabel = QLabel("行数: 0")
        
        infoLayout.addWidget(self.wordCountLabel)
        infoLayout.addWidget(self.chineseCharCountLabel)
        infoLayout.addWidget(self.mixedCountLabel)
        infoLayout.addWidget(self.charCountLabel)
        infoLayout.addWidget(self.lineCountLabel)
        
        layout.addLayout(infoLayout)
        
        # 刷新按钮
        refreshButton = QPushButton("刷新统计")
        refreshButton.clicked.connect(self.updateCounts)
        layout.addWidget(refreshButton)
        
        # 保持简洁，只有必要UI
        layout.addStretch(1)
    
    def updateCounts(self):
        """更新计数"""
        # 获取主窗口
        main_window = self.plugin.app
        
        # 获取编辑器文本
        if hasattr(main_window, 'editor') and main_window.editor:
            text = main_window.editor.toPlainText()
            
            # 如果启用了MD标识符过滤，则先过滤
            if self.plugin.get_setting('filter_md_marks', True):
                filtered_text = self.plugin.filter_markdown_marks(text)
            else:
                filtered_text = text
            
            # 计算统计数据
            word_count = len(re.findall(r'\b[a-zA-Z]+\b', filtered_text))  # 英文单词
            chinese_char_count = len(re.findall(r'[\u4e00-\u9fa5]', filtered_text))  # 中文字符
            
            # 混合字数计算 (英文单词算一个字，中文字符各算一个字)
            mixed_count = len(re.findall(r'\b[a-zA-Z]+\b|[\u4e00-\u9fa5]', filtered_text))
            
            char_count = len(filtered_text)
            line_count = filtered_text.count('\n') + 1 if filtered_text else 0
            
            # 更新标签
            self.wordCountLabel.setText(f"英文单词数: {word_count}")
            self.chineseCharCountLabel.setText(f"中文字数: {chinese_char_count}")
            self.mixedCountLabel.setText(f"混合字数: {mixed_count}")
            self.charCountLabel.setText(f"总字符数: {char_count}")
            self.lineCountLabel.setText(f"行数: {line_count}")

class WordCounterSettingsWidget(QWidget):
    """单词计数器设置小部件"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 自动更新设置
        self.autoUpdateCheckbox = QCheckBox("实时更新统计")
        self.autoUpdateCheckbox.setChecked(self.plugin.get_setting('auto_update', True))
        self.autoUpdateCheckbox.toggled.connect(self.onAutoUpdateToggled)
        layout.addWidget(self.autoUpdateCheckbox)
        
        # Markdown过滤设置
        self.filterMdCheckbox = QCheckBox("过滤Markdown标识符")
        self.filterMdCheckbox.setChecked(self.plugin.get_setting('filter_md_marks', True))
        self.filterMdCheckbox.setToolTip("启用后，Markdown格式标记(如#、*、[])将不被计入字数")
        self.filterMdCheckbox.toggled.connect(self.onFilterMdToggled)
        layout.addWidget(self.filterMdCheckbox)
        
        # 状态栏设置组
        statusBarGroup = QGroupBox("状态栏显示设置")
        statusBarLayout = QVBoxLayout(statusBarGroup)
        
        # 显示在状态栏设置
        self.showInStatusBarCheckbox = QCheckBox("在状态栏显示字数")
        self.showInStatusBarCheckbox.setChecked(self.plugin.get_setting('show_in_status_bar', False))
        self.showInStatusBarCheckbox.toggled.connect(self.onShowInStatusBarToggled)
        statusBarLayout.addWidget(self.showInStatusBarCheckbox)
        
        # 状态栏显示模式
        statusModeLayout = QHBoxLayout()
        statusModeLayout.addWidget(QLabel("显示模式:"))
        
        self.statusModeCombo = QComboBox()
        self.statusModeCombo.addItem("英文单词数", "english")
        self.statusModeCombo.addItem("中文字数", "chinese")
        self.statusModeCombo.addItem("混合字数", "mixed")
        self.statusModeCombo.addItem("总字符数", "chars")
        
        # 设置当前选中项
        current_mode = self.plugin.get_setting('status_display_mode', 'mixed')
        index = self.statusModeCombo.findData(current_mode)
        if index >= 0:
            self.statusModeCombo.setCurrentIndex(index)
            
        self.statusModeCombo.currentIndexChanged.connect(self.onStatusModeChanged)
        self.statusModeCombo.setEnabled(self.showInStatusBarCheckbox.isChecked())
        statusModeLayout.addWidget(self.statusModeCombo)
        
        statusBarLayout.addLayout(statusModeLayout)
        layout.addWidget(statusBarGroup)
        
        layout.addStretch(1)
    
    def onAutoUpdateToggled(self, checked):
        """自动更新选项切换"""
        self.plugin.set_setting('auto_update', checked)
        
    def onFilterMdToggled(self, checked):
        """MD过滤选项切换"""
        self.plugin.set_setting('filter_md_marks', checked)
        # 如果视图已创建，重新统计
        if self.plugin.widget:
            self.plugin.widget.updateCounts()
        # 更新状态栏
        self.plugin.update_status_bar()
        
    def onShowInStatusBarToggled(self, checked):
        """状态栏显示选项切换"""
        self.plugin.set_setting('show_in_status_bar', checked)
        self.statusModeCombo.setEnabled(checked)
        
        # 更新状态栏显示
        self.plugin.update_status_bar()
        
    def onStatusModeChanged(self, index):
        """状态栏显示模式改变"""
        mode = self.statusModeCombo.itemData(index)
        self.plugin.set_setting('status_display_mode', mode)
        
        # 更新状态栏显示
        self.plugin.update_status_bar()

class Plugin(PluginBase):
    """单词计数器插件实现"""
    
    # 插件元数据
    name = "单词计数器"
    version = "1.2.0"
    author = "MGit团队"
    description = "统计文档中的单词数、字符数、中文字数和行数，支持过滤Markdown标识符"
    plugin_type = "编辑器"
    
    # 插件设置
    settings = {
        'auto_update': {
            'type': 'bool',
            'default': True,
            'description': '是否实时更新统计'
        },
        'filter_md_marks': {
            'type': 'bool',
            'default': True,
            'description': '是否过滤Markdown标识符'
        },
        'show_in_status_bar': {
            'type': 'bool',
            'default': False,
            'description': '是否在状态栏显示字数'
        },
        'status_display_mode': {
            'type': 'string',
            'default': 'mixed',
            'description': '状态栏显示模式(english/chinese/mixed/chars)'
        }
    }
    
    def __init__(self):
        super().__init__()
        self.widget = None
        self.status_widget = None
        self.logger = logging.getLogger('Plugin.WordCounter')
    
    def filter_markdown_marks(self, text):
        """过滤Markdown标识符
        
        Args:
            text: 要过滤的文本
            
        Returns:
            过滤后的文本
        """
        filtered_text = text
        
        # 应用所有直接移除的MD模式
        for pattern in MD_PATTERNS:
            # 使用正则表达式搜索和替换
            if pattern.startswith(r'^\s*'):
                # 多行模式下替换行首匹配的模式
                filtered_text = re.sub(pattern, '', filtered_text, flags=re.MULTILINE)
            else:
                # 普通替换
                filtered_text = re.sub(pattern, '', filtered_text)
        
        # 应用需要保留内容的MD模式
        for pattern, replacement in MD_PATTERNS_WITH_CONTENT:
            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.DOTALL)
        
        return filtered_text
    
    def initialize(self, app):
        """初始化插件
        
        Args:
            app: 应用程序实例（主窗口）
        """
        super().initialize(app)
        
        # 创建小部件
        self.widget = WordCounterWidget(self)
        
        # 如果启用了自动更新，连接编辑器的文本变化信号
        if self.get_setting('auto_update', True) and hasattr(app, 'editor'):
            app.editor.textChanged.connect(self.on_text_changed)
        
        # 如果启用了状态栏显示，创建状态栏小部件
        if self.get_setting('show_in_status_bar', False):
            self.create_status_widget()
    
    def create_status_widget(self):
        """创建状态栏小部件"""
        if not self.app or not hasattr(self.app, 'statusBar'):
            return
        
        if self.status_widget:
            return
            
        # 创建状态栏标签
        self.status_widget = QLabel("统计: 0")
        
        # 使用自定义方法添加到状态栏
        try:
            # 因为StatusBar是自定义的，我们直接修改其布局
            statusBar = self.app.statusBar
            if hasattr(statusBar, 'layout'):
                # 插入到布局倒数第二个位置（在同步按钮之前）
                statusBar.layout().insertWidget(statusBar.layout().count()-1, self.status_widget)
        except Exception as e:
            self.logger.error(f"无法添加状态栏小部件: {str(e)}")
            self.status_widget = None
            return
        
        # 初始更新
        self.update_status_bar()
    
    def remove_status_widget(self):
        """移除状态栏小部件"""
        if not self.app or not hasattr(self.app, 'statusBar') or not self.status_widget:
            return
        
        try:
            # 从布局中移除
            statusBar = self.app.statusBar
            if hasattr(statusBar, 'layout'):
                statusBar.layout().removeWidget(self.status_widget)
                self.status_widget.setParent(None)
                self.status_widget.deleteLater()
                self.status_widget = None
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"无法移除状态栏小部件: {str(e)}")
    
    def update_status_bar(self):
        """更新状态栏显示"""
        if not self.get_setting('show_in_status_bar', False):
            if self.status_widget:
                self.remove_status_widget()
            return
            
        # 确保状态栏小部件存在
        if not self.status_widget:
            self.create_status_widget()
            if not self.status_widget:
                return
        
        # 获取编辑器文本
        if hasattr(self.app, 'editor') and self.app.editor:
            text = self.app.editor.toPlainText()
            
            # 如果启用了MD标识符过滤，则先过滤
            if self.get_setting('filter_md_marks', True):
                text = self.filter_markdown_marks(text)
            
            # 获取显示模式
            mode = self.get_setting('status_display_mode', 'mixed')
            
            # 根据模式计算不同的统计数据
            if mode == 'english':
                count = len(re.findall(r'\b[a-zA-Z]+\b', text))
                label = "单词"
            elif mode == 'chinese':
                count = len(re.findall(r'[\u4e00-\u9fa5]', text))
                label = "汉字"
            elif mode == 'chars':
                count = len(text)
                label = "字符"
            else:  # mixed
                count = len(re.findall(r'\b[a-zA-Z]+\b|[\u4e00-\u9fa5]', text))
                label = "字数"
            
            # 更新标签
            self.status_widget.setText(f"{label}: {count}")
    
    def on_text_changed(self):
        """编辑器文本变化时的回调"""
        # 如果启用了自动更新，则更新计数
        if self.get_setting('auto_update', True) and self.widget:
            self.widget.updateCounts()
        
        # 更新状态栏
        if self.get_setting('show_in_status_bar', False) and self.status_widget:
            self.update_status_bar()
    
    def get_view(self):
        """获取插件视图
        
        Returns:
            QWidget: 插件视图小部件
        """
        if not self.widget:
            self.widget = WordCounterWidget(self)
        return self.widget
    
    def get_settings_widget(self):
        """获取设置界面
        
        Returns:
            QWidget: 设置界面小部件
        """
        return WordCounterSettingsWidget(self)
    
    def get_event_listeners(self):
        """获取事件监听器
        
        Returns:
            dict: 事件监听器字典
        """
        return {
            'editor_text_changed': self.on_text_changed
        }
    
    def enable(self):
        """启用插件"""
        super().enable()
        
        # 连接编辑器信号
        if hasattr(self.app, 'editor'):
            self.app.editor.textChanged.connect(self.on_text_changed)
        
        # 如果设置为在状态栏显示，则创建状态栏小部件
        if self.get_setting('show_in_status_bar', False):
            self.create_status_widget()
    
    def disable(self):
        """禁用插件"""
        super().disable()
        
        # 断开编辑器信号
        if hasattr(self.app, 'editor'):
            try:
                self.app.editor.textChanged.disconnect(self.on_text_changed)
            except:
                pass
        
        # 移除状态栏小部件
        if self.status_widget:
            self.remove_status_widget()
    
    def cleanup(self):
        """清理插件资源"""
        self.disable()
        
        # 清理小部件
        if self.widget:
            self.widget.deleteLater()
            self.widget = None 