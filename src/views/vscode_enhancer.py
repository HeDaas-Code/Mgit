#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强的主窗口类 - VSCode风格UI
为主窗口添加VSCode风格的UI增强功能
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt5.QtGui import QColor

from src.components.vscode_activity_bar import VSCodeActivityBar
from src.components.vscode_status_bar import VSCodeStatusBar


class VSCodeMainWindowEnhancer:
    """主窗口VSCode风格增强器
    
    将现有主窗口改造为VSCode风格的界面布局
    """
    
    def __init__(self, main_window):
        """初始化增强器
        
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
        self.dark_mode = True
        self.sidebar_visible = True
        self.panel_visible = False
        
        # 动画对象
        self.sidebar_animation = None
        self.panel_animation = None
        
    def enhance(self):
        """应用VSCode风格增强"""
        # 保存原有组件的引用
        original_layout = self.main_window.centralWidget().layout()
        
        # 创建新的布局结构
        self._createVSCodeLayout()
        
        # 重新组织现有组件
        self._reorganizeComponents()
        
        # 设置动画
        self._setupAnimations()
        
        # 连接信号
        self._connectSignals()
        
    def _createVSCodeLayout(self):
        """创建VSCode风格的布局结构"""
        # 创建主容器
        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建活动栏（最左侧）
        self.activity_bar = VSCodeActivityBar()
        main_layout.addWidget(self.activity_bar)
        
        # 创建内容区域
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 侧边栏容器（文件浏览器、Git面板等）
        self.sidebar_container = QWidget()
        self.sidebar_container.setMinimumWidth(200)
        self.sidebar_container.setMaximumWidth(400)
        sidebar_layout = QVBoxLayout(self.sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 编辑器区域容器
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加到内容布局
        content_layout.addWidget(self.sidebar_container)
        content_layout.addWidget(self.editor_container)
        
        main_layout.addWidget(content_widget)
        
        # 保存容器引用
        self.main_container = main_container
        self.content_widget = content_widget
        
    def _reorganizeComponents(self):
        """重新组织现有组件到新布局"""
        main_window = self.main_window
        
        # 将文件浏览器和文档导航器放入侧边栏
        if hasattr(main_window, 'leftSplitter'):
            sidebar_layout = self.sidebar_container.layout()
            # 移除leftSplitter的父组件
            left_splitter = main_window.leftSplitter
            left_splitter.setParent(None)
            sidebar_layout.addWidget(left_splitter)
        
        # 将编辑器和预览放入编辑器区域
        if hasattr(main_window, 'editorSplitter'):
            editor_layout = self.editor_container.layout()
            editor_splitter = main_window.editorSplitter
            editor_splitter.setParent(None)
            editor_layout.addWidget(editor_splitter)
        
        # 替换原有的中心部件
        main_window.centralWidget().setParent(None)
        
        # 创建新的中心部件
        new_central = QWidget()
        new_layout = QVBoxLayout(new_central)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(0)
        
        # 添加主容器
        new_layout.addWidget(self.main_container)
        
        # 创建并添加VSCode风格状态栏
        self.vscode_statusbar = VSCodeStatusBar()
        new_layout.addWidget(self.vscode_statusbar)
        
        # 设置新的中心部件
        main_window.setCentralWidget(new_central)
        
        # 隐藏原有状态栏（如果存在）
        if hasattr(main_window, 'statusBar'):
            original_statusbar = main_window.statusBar
            if original_statusbar:
                original_statusbar.hide()
        
    def _setupAnimations(self):
        """设置动画效果"""
        # 侧边栏展开/收起动画
        self.sidebar_animation = QPropertyAnimation(self.sidebar_container, b"maximumWidth")
        self.sidebar_animation.setDuration(200)
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 面板展开/收起动画（如果需要的话）
        # self.panel_animation = QPropertyAnimation(...)
        
    def _connectSignals(self):
        """连接信号与槽"""
        # 活动栏按钮信号
        self.activity_bar.explorerClicked.connect(self._onExplorerClicked)
        self.activity_bar.searchClicked.connect(self._onSearchClicked)
        self.activity_bar.sourceControlClicked.connect(self._onSourceControlClicked)
        self.activity_bar.debugClicked.connect(self._onDebugClicked)
        self.activity_bar.extensionsClicked.connect(self._onExtensionsClicked)
        self.activity_bar.settingsClicked.connect(self._onSettingsClicked)
        self.activity_bar.accountClicked.connect(self._onAccountClicked)
        
        # 状态栏信号
        self.vscode_statusbar.branchClicked.connect(self._onBranchClicked)
        self.vscode_statusbar.lineColumnClicked.connect(self._onLineColumnClicked)
        
        # 编辑器光标位置变化
        if hasattr(self.main_window, 'editor') and hasattr(self.main_window.editor, 'editor'):
            editor = self.main_window.editor.editor
            editor.cursorPositionChanged.connect(self._updateCursorPosition)
        
    def _onExplorerClicked(self):
        """处理资源管理器按钮点击"""
        # 切换到文件浏览器视图
        if hasattr(self.main_window, 'leftSplitter'):
            self.sidebar_container.show()
            self.activity_bar.setActiveView('explorer')
            # 确保文件浏览器可见
            if hasattr(self.main_window, 'fileExplorer'):
                self.main_window.fileExplorer.show()
        
    def _onSearchClicked(self):
        """处理搜索按钮点击"""
        # 可以实现全局搜索功能
        self.activity_bar.setActiveView('search')
        # TODO: 实现搜索界面
        
    def _onSourceControlClicked(self):
        """处理源代码管理按钮点击"""
        # 显示Git面板
        self.activity_bar.setActiveView('source_control')
        if hasattr(self.main_window, 'gitPanel'):
            # 将Git面板移到侧边栏
            self.main_window.gitPanel.show()
        
    def _onDebugClicked(self):
        """处理调试按钮点击"""
        self.activity_bar.setActiveView('debug')
        # TODO: 实现调试功能
        
    def _onExtensionsClicked(self):
        """处理扩展按钮点击"""
        self.activity_bar.setActiveView('extensions')
        # 显示插件管理器
        if hasattr(self.main_window, 'showPluginManager'):
            self.main_window.showPluginManager()
        
    def _onSettingsClicked(self):
        """处理设置按钮点击"""
        # 打开设置对话框
        # TODO: 实现设置对话框
        pass
        
    def _onAccountClicked(self):
        """处理账户按钮点击"""
        # 显示账户面板
        if hasattr(self.main_window, 'accountPanel'):
            self.main_window.accountPanel.show()
        
    def _onBranchClicked(self):
        """处理分支按钮点击"""
        # 打开分支管理器
        if hasattr(self.main_window, 'manageBranches'):
            self.main_window.manageBranches()
        
    def _onLineColumnClicked(self):
        """处理行列号按钮点击"""
        # 可以打开跳转到行对话框
        pass
        
    def _updateCursorPosition(self):
        """更新光标位置显示"""
        if hasattr(self.main_window, 'editor') and hasattr(self.main_window.editor, 'editor'):
            editor = self.main_window.editor.editor
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
            self.vscode_statusbar.setLineColumn(line, column)
        
    def toggleSidebar(self):
        """切换侧边栏显示/隐藏"""
        if self.sidebar_visible:
            # 隐藏侧边栏
            self.sidebar_animation.setStartValue(self.sidebar_container.width())
            self.sidebar_animation.setEndValue(0)
            self.sidebar_animation.finished.connect(lambda: self.sidebar_container.hide())
        else:
            # 显示侧边栏
            self.sidebar_container.show()
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(250)
            
        self.sidebar_animation.start()
        self.sidebar_visible = not self.sidebar_visible
        
    def applyTheme(self, dark_mode):
        """应用主题
        
        Args:
            dark_mode: 是否为深色主题
        """
        self.dark_mode = dark_mode
        
        # 应用到各个组件
        if hasattr(self, 'activity_bar'):
            self.activity_bar.applyTheme(dark_mode)
        
        if hasattr(self, 'vscode_statusbar'):
            self.vscode_statusbar.applyTheme(dark_mode)
            
    def updateGitInfo(self, branch_name=None, added=0, modified=0, deleted=0):
        """更新Git信息显示
        
        Args:
            branch_name: 分支名称
            added: 添加的文件数
            modified: 修改的文件数
            deleted: 删除的文件数
        """
        if hasattr(self, 'vscode_statusbar'):
            if branch_name:
                self.vscode_statusbar.setBranch(branch_name)
            self.vscode_statusbar.setGitStatus(added, modified, deleted)
