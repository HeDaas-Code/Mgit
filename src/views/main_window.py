#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QSplitter, QMessageBox, 
                           QStackedWidget, QFileDialog, QMenuBar, QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QColor, QTextCharFormat, QTextCursor

from qfluentwidgets import (NavigationInterface, NavigationItemPosition, 
                          FluentIcon, SubtitleLabel, setTheme, Theme, 
                          FluentStyleSheet, InfoBar, InfoBarPosition)

# 导入自定义组件
from src.components.editor import MarkdownEditor
from src.components.explorer import FileExplorer
from src.components.preview import MarkdownPreview
from src.components.git_panel import GitPanel
from src.components.status_bar import StatusBar
from src.utils.git_manager import GitManager
from src.utils.config_manager import ConfigManager
from src.components.log_dialog import LogDialog
from src.utils.logger import info, warning, error, critical, show_error_message

# 导入插件管理器
from src.utils.plugin_manager import init_plugin_manager, get_plugin_manager
from src.components.plugin_settings import PluginManager as PluginManagerWidget

class MainWindow(QMainWindow):
    """ 主窗口类 """
    
    repoChanged = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.configManager = ConfigManager()
        
        # 初始化插件管理器
        self.pluginManager = init_plugin_manager(self)
        
        # 初始化Git管理器为None
        self.gitManager = None
        
        # 窗口设置
        self.setWindowTitle("MGit - Markdown笔记与Git版本控制")
        self.resize(1200, 800)
        
        # 设置窗口图标
        try:
            # 尝试获取应用图标路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icon_path = os.path.join(base_dir, 'app.ico')
            
            # 也考虑PyInstaller打包环境
            if not os.path.exists(icon_path) and hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'app.ico')
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            warning(f"设置窗口图标出错: {str(e)}")
        
        # 初始化UI
        self.initUI()
        
        # 创建菜单
        self.createMenus()
        
        # 连接信号与槽
        self.connectSignals()
        
        # 设置默认主题
        setTheme(Theme.LIGHT)
        
        # 添加快捷键
        self.setupShortcuts()
        
        # 检查自动保存恢复
        QTimer.singleShot(500, self.checkAutoSaveRecovery)
        
        # 加载插件
        self._loadPlugins()
        
    def _loadPlugins(self):
        """加载插件系统"""
        info("开始加载插件系统...")
        try:
            # 加载所有插件
            self.pluginManager.load_all_plugins()
            
            # 触发应用初始化事件，通知插件
            self.pluginManager.trigger_event('app_initialized', self)
            
            info("插件系统加载完成")
        except Exception as e:
            error(f"加载插件系统时出错: {str(e)}")
            import traceback
            error(traceback.format_exc())
        
    def initUI(self):
        """ 初始化用户界面 """
        # 创建中心窗口部件
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.centralLayout = QVBoxLayout(self.centralWidget)
        self.centralLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建主分割器
        self.mainSplitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧文件浏览器
        self.fileExplorer = FileExplorer(self)
        
        # 创建文档导航器
        from src.components.document_navigator import DocumentNavigator
        self.documentNavigator = DocumentNavigator(self)
        
        # 创建包含文件浏览器和文档导航器的左侧区域
        leftPanel = QWidget()
        leftLayout = QVBoxLayout(leftPanel)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧切换分割器
        self.leftSplitter = QSplitter(Qt.Vertical)
        self.leftSplitter.addWidget(self.fileExplorer)
        self.leftSplitter.addWidget(self.documentNavigator)
        self.leftSplitter.setSizes([400, 400])
        
        leftLayout.addWidget(self.leftSplitter)
        
        # 创建中间编辑器和预览区分割器
        self.editorSplitter = QSplitter(Qt.Horizontal)
        
        # 创建Markdown编辑器（传入配置管理器）
        self.editor = MarkdownEditor(self, config_manager=self.configManager)
        
        # 创建Markdown预览面板
        self.preview = MarkdownPreview(self)
        
        # 创建Git面板
        self.gitPanel = GitPanel(self)
        
        # 添加组件到分割器
        self.editorSplitter.addWidget(self.editor)
        self.editorSplitter.addWidget(self.preview)
        self.editorSplitter.setSizes([500, 500])
        
        # 添加组件到主分割器
        self.mainSplitter.addWidget(leftPanel)
        self.mainSplitter.addWidget(self.editorSplitter)
        self.mainSplitter.addWidget(self.gitPanel)
        self.mainSplitter.setSizes([250, 700, 250])
        
        # 将主分割器添加到中央布局
        self.centralLayout.addWidget(self.mainSplitter)
        
        # 创建并添加状态栏
        self.statusBar = StatusBar(self)
        self.centralLayout.addWidget(self.statusBar)
    
    def createMenus(self):
        """ 创建菜单栏 """
        menuBar = self.menuBar()
        
        # 文件菜单
        fileMenu = menuBar.addMenu("文件")
        
        # 新建文件动作
        newFileAction = QAction("新建文件", self)
        newFileAction.setIcon(FluentIcon.ADD.icon())
        newFileAction.setShortcut(QKeySequence.New)
        newFileAction.triggered.connect(self.createNewFile)
        fileMenu.addAction(newFileAction)
        
        # 打开文件动作
        openFileAction = QAction("打开文件", self)
        openFileAction.setIcon(FluentIcon.FOLDER.icon())
        openFileAction.setShortcut(QKeySequence.Open)
        openFileAction.triggered.connect(self.openFile)
        fileMenu.addAction(openFileAction)
        
        # 保存文件动作
        saveFileAction = QAction("保存文件", self)
        saveFileAction.setIcon(FluentIcon.SAVE.icon())
        saveFileAction.setShortcut(QKeySequence.Save)
        saveFileAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveFileAction)
        
        # 另存为动作
        saveAsAction = QAction("另存为", self)
        saveAsAction.setIcon(FluentIcon.SAVE_AS.icon())
        saveAsAction.setShortcut(QKeySequence.SaveAs)
        saveAsAction.triggered.connect(self.saveFileAs)
        fileMenu.addAction(saveAsAction)
        
        fileMenu.addSeparator()
        
        # 打开仓库动作
        openRepoAction = QAction("打开仓库", self)
        openRepoAction.setIcon(FluentIcon.GITHUB.icon())
        openRepoAction.triggered.connect(self.openRepository)
        fileMenu.addAction(openRepoAction)
        
        # 克隆仓库动作
        cloneRepoAction = QAction("克隆仓库", self)
        cloneRepoAction.setIcon(FluentIcon.DOWNLOAD.icon())
        cloneRepoAction.triggered.connect(self.cloneRepository)
        fileMenu.addAction(cloneRepoAction)
        
        # 最近打开的仓库子菜单
        self.recentReposMenu = QMenu("最近的仓库", self)
        self.recentReposMenu.setIcon(FluentIcon.HISTORY.icon())
        fileMenu.addMenu(self.recentReposMenu)
        
        # 清空最近仓库历史
        clearRecentAction = QAction("清空历史记录", self)
        clearRecentAction.setIcon(FluentIcon.DELETE.icon())
        clearRecentAction.triggered.connect(self.clearRecentRepositories)
        self.recentReposMenu.addAction(clearRecentAction)
        
        # 更新最近仓库菜单
        self.updateRecentRepositoriesMenu()
        
        fileMenu.addSeparator()
        
        # 退出动作
        exitAction = QAction("退出", self)
        exitAction.setIcon(FluentIcon.CLOSE.icon())
        exitAction.setShortcut(QKeySequence.Quit)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)
        
        # 编辑菜单
        editMenu = menuBar.addMenu("编辑")
        
        # 撤销动作
        undoAction = QAction("撤销", self)
        undoAction.setIcon(FluentIcon.RETURN.icon())
        undoAction.setShortcut(QKeySequence.Undo)
        undoAction.triggered.connect(self.undoEdit)
        editMenu.addAction(undoAction)
        
        # 重做动作
        redoAction = QAction("重做", self)
        redoAction.setIcon(FluentIcon.RETURN.icon())
        redoAction.setShortcut(QKeySequence.Redo)
        redoAction.triggered.connect(self.redoEdit)
        editMenu.addAction(redoAction)
        
        editMenu.addSeparator()
        
        # 剪切动作
        cutAction = QAction("剪切", self)
        cutAction.setIcon(FluentIcon.CUT.icon())
        cutAction.setShortcut(QKeySequence.Cut)
        cutAction.triggered.connect(lambda: self.editor.editor.cut() if hasattr(self, 'editor') else None)
        editMenu.addAction(cutAction)
        
        # 复制动作
        copyAction = QAction("复制", self)
        copyAction.setIcon(FluentIcon.COPY.icon())
        copyAction.setShortcut(QKeySequence.Copy)
        copyAction.triggered.connect(lambda: self.editor.editor.copy() if hasattr(self, 'editor') else None)
        editMenu.addAction(copyAction)
        
        # 粘贴动作
        pasteAction = QAction("粘贴", self)
        pasteAction.setIcon(FluentIcon.PASTE.icon())
        pasteAction.setShortcut(QKeySequence.Paste)
        pasteAction.triggered.connect(lambda: self.editor.editor.paste() if hasattr(self, 'editor') else None)
        editMenu.addAction(pasteAction)
        
        editMenu.addSeparator()
        
        # 查找动作
        findAction = QAction("查找", self)
        findAction.setIcon(FluentIcon.SEARCH.icon())
        findAction.setShortcut(QKeySequence.Find)
        findAction.triggered.connect(self.showFindDialog)
        editMenu.addAction(findAction)
        
        # 替换动作
        replaceAction = QAction("替换", self)
        replaceAction.setIcon(FluentIcon.EDIT.icon())
        replaceAction.setShortcut(QKeySequence.Replace)
        replaceAction.triggered.connect(self.showReplaceDialog)
        editMenu.addAction(replaceAction)
        
        # 视图菜单
        viewMenu = menuBar.addMenu("视图")
        
        # 显示/隐藏文件资源管理器
        self.toggleExplorerAction = QAction("文件资源管理器", self)
        self.toggleExplorerAction.setCheckable(True)
        self.toggleExplorerAction.setChecked(True)
        self.toggleExplorerAction.triggered.connect(self.toggleExplorer)
        viewMenu.addAction(self.toggleExplorerAction)
        
        # 显示/隐藏预览
        self.togglePreviewAction = QAction("Markdown预览", self)
        self.togglePreviewAction.setCheckable(True)
        self.togglePreviewAction.setChecked(True)
        self.togglePreviewAction.triggered.connect(self.togglePreview)
        viewMenu.addAction(self.togglePreviewAction)
        
        # 显示/隐藏Git面板
        self.toggleGitPanelAction = QAction("Git面板", self)
        self.toggleGitPanelAction.setCheckable(True)
        self.toggleGitPanelAction.setChecked(True)
        self.toggleGitPanelAction.triggered.connect(self.toggleGitPanel)
        viewMenu.addAction(self.toggleGitPanelAction)
        
        viewMenu.addSeparator()
        
        # 显示日志对话框
        showLogDialogAction = QAction("查看日志", self)
        showLogDialogAction.setIcon(FluentIcon.DOCUMENT.icon())
        showLogDialogAction.triggered.connect(self.showLogDialog)
        viewMenu.addAction(showLogDialogAction)
        
        # Git菜单
        gitMenu = menuBar.addMenu("Git")
        
        # 提交更改
        commitAction = QAction("提交更改", self)
        commitAction.setIcon(FluentIcon.ACCEPT.icon())
        commitAction.triggered.connect(self.commitChanges)
        gitMenu.addAction(commitAction)
        
        # 推送更改
        pushAction = QAction("推送更改", self)
        pushAction.setIcon(FluentIcon.UP.icon())
        pushAction.triggered.connect(self.pushChanges)
        gitMenu.addAction(pushAction)
        
        # 拉取更改
        pullAction = QAction("拉取更改", self)
        pullAction.setIcon(FluentIcon.DOWN.icon())
        pullAction.triggered.connect(self.pullChanges)
        gitMenu.addAction(pullAction)
        
        gitMenu.addSeparator()
        
        # 管理分支
        branchesAction = QAction("管理分支", self)
        branchesAction.setIcon(FluentIcon.FOLDER.icon())
        branchesAction.triggered.connect(self.manageBranches)
        gitMenu.addAction(branchesAction)
        
        # 查看历史
        historyAction = QAction("查看历史", self)
        historyAction.setIcon(FluentIcon.HISTORY.icon())
        historyAction.triggered.connect(self.viewHistory)
        gitMenu.addAction(historyAction)
        
        # 插件菜单
        pluginsMenu = menuBar.addMenu("插件")
        
        # 插件管理器
        managePluginsAction = QAction("插件管理器", self)
        managePluginsAction.setIcon(FluentIcon.SETTING.icon())
        managePluginsAction.triggered.connect(self.showPluginManager)
        pluginsMenu.addAction(managePluginsAction)
        
        # 刷新插件动作
        refreshPluginsAction = QAction("刷新插件", self)
        refreshPluginsAction.setIcon(FluentIcon.SYNC.icon())
        refreshPluginsAction.triggered.connect(self.refreshPlugins)
        pluginsMenu.addAction(refreshPluginsAction)
        
        pluginsMenu.addSeparator()
        
        # 插件子菜单 - 将在插件加载后更新
        self.pluginsSubMenu = QMenu("已安装插件", self)
        self.pluginsSubMenu.setIcon(FluentIcon.LIBRARY.icon())
        pluginsMenu.addMenu(self.pluginsSubMenu)
        
        # 在插件加载后更新插件菜单
        QTimer.singleShot(1000, self.updatePluginsMenu)
        
        # 设置菜单
        settingsMenu = menuBar.addMenu("设置")
        
        # 自动保存设置
        autoSaveMenu = QMenu("自动保存", self)
        
        # 焦点变化时自动保存
        self.autoSaveOnFocusAction = QAction("失去焦点时自动保存", self)
        self.autoSaveOnFocusAction.setCheckable(True)
        self.autoSaveOnFocusAction.setChecked(self.configManager.get_auto_save_on_focus_change())
        self.autoSaveOnFocusAction.triggered.connect(
            lambda checked: self.configManager.set_auto_save_on_focus_change(checked)
        )
        autoSaveMenu.addAction(self.autoSaveOnFocusAction)
        
        # 自动保存间隔选择
        autoSaveIntervalMenu = QMenu("自动保存间隔", self)
        
        # 添加不同的自动保存间隔选项
        for seconds in [30, 60, 120, 300, 600]:
            intervalAction = QAction(f"{seconds//60}分钟" if seconds >= 60 else f"{seconds}秒", self)
            intervalAction.setCheckable(True)
            intervalAction.setChecked(self.configManager.get_auto_save_interval() == seconds)
            intervalAction.triggered.connect(
                lambda checked, s=seconds: self.configManager.set_auto_save_interval(s)
            )
            autoSaveIntervalMenu.addAction(intervalAction)
            
        autoSaveMenu.addMenu(autoSaveIntervalMenu)
        
        settingsMenu.addMenu(autoSaveMenu)
        
        # 帮助菜单
        helpMenu = menuBar.addMenu("帮助")
        
        # 关于
        aboutAction = QAction("关于", self)
        aboutAction.setIcon(FluentIcon.INFO.icon())
        aboutAction.triggered.connect(self.showAboutDialog)
        helpMenu.addAction(aboutAction)
        
        # 检查更新
        checkUpdateAction = QAction("检查更新", self)
        checkUpdateAction.setIcon(FluentIcon.UPDATE.icon())
        checkUpdateAction.triggered.connect(self.checkForUpdates)
        helpMenu.addAction(checkUpdateAction)
        
        helpMenu.addSeparator()
        
        # 开发者工具
        devToolsAction = QAction("开发者工具", self)
        devToolsAction.setIcon(FluentIcon.CODE.icon())
        devToolsAction.triggered.connect(self.openDevTools)
        helpMenu.addAction(devToolsAction)
    
    def _setupPluginMenus(self, menuBar):
        """设置插件菜单项
        
        Args:
            menuBar: 菜单栏
        """
        # 此方法将在插件加载后被调用，以允许插件添加自己的菜单项
        pass
    
    def updatePluginsMenu(self):
        """更新插件菜单"""
        # 清空现有菜单项
        self.pluginsSubMenu.clear()
        
        # 获取所有可用插件
        plugins_info = self.pluginManager.plugin_info
        
        # 按类型组织
        plugins_by_type = {}
        for plugin_name, plugin_info in plugins_info.items():
            plugin_type = plugin_info.get('plugin_type', '通用')
            if plugin_type not in plugins_by_type:
                plugins_by_type[plugin_type] = []
            plugins_by_type[plugin_type].append((plugin_name, plugin_info))
        
        # 为每种类型创建子菜单
        for plugin_type, plugins in plugins_by_type.items():
            type_menu = QMenu(plugin_type, self)
            
            for plugin_name, plugin_info in plugins:
                # 创建插件动作
                plugin_action = QAction(plugin_info['name'], self)
                enabled = self.configManager.is_plugin_enabled(plugin_name)
                plugin_action.setCheckable(True)
                plugin_action.setChecked(enabled)
                
                # 连接到启用/禁用函数
                plugin_action.triggered.connect(
                    lambda checked, name=plugin_name: self.togglePlugin(name, checked)
                )
                
                type_menu.addAction(plugin_action)
            
            self.pluginsSubMenu.addMenu(type_menu)
        
        # 如果没有插件，添加一个禁用的项目
        if not plugins_info:
            no_plugins_action = QAction("未安装插件", self)
            no_plugins_action.setEnabled(False)
            self.pluginsSubMenu.addAction(no_plugins_action)
        
    def togglePlugin(self, plugin_name, enabled):
        """切换插件启用状态
        
        Args:
            plugin_name: 插件名称
            enabled: 是否启用
        """
        try:
            # 更新配置
            self.configManager.set_plugin_enabled(plugin_name, enabled)
            
            # 获取插件实例
            plugin = self.pluginManager.get_plugin(plugin_name)
            if plugin:
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
            error(f"切换插件 '{plugin_name}' 状态失败: {str(e)}")
    
    def showPluginManager(self):
        """显示插件管理界面"""
        # 创建插件管理对话框
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("插件管理")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # 创建插件管理器界面
        plugin_manager_widget = PluginManagerWidget(dialog)
        layout.addWidget(plugin_manager_widget)
        
        # 添加关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 显示对话框
        dialog.exec_()
        
        # 更新插件菜单
        self.updatePluginsMenu()
    
    def refreshPlugins(self):
        """刷新插件"""
        try:
            # 重新加载所有插件
            self.pluginManager.load_all_plugins()
            
            # 更新插件菜单
            self.updatePluginsMenu()
            
            # 提示成功
            InfoBar.success(
                title="插件已刷新",
                content="已重新加载所有可用插件",
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            error(f"刷新插件失败: {str(e)}")
            
            # 提示错误
            InfoBar.error(
                title="刷新插件失败",
                content=f"刷新插件时出错: {str(e)}",
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
    def updateRecentRepositoriesMenu(self):
        """ 更新最近仓库菜单 """
        # 清空除了最后一项（清空历史记录）外的所有菜单项
        clearAction = None
        if self.recentReposMenu.actions():
            clearAction = self.recentReposMenu.actions()[-1]
            
        self.recentReposMenu.clear()
        
        # 获取最近仓库列表
        recentRepos = self.configManager.get_recent_repositories()
        
        # 添加最近仓库到菜单
        for repo in recentRepos:
            repoName = os.path.basename(repo)
            action = QAction(f"{repoName} ({repo})", self)
            action.triggered.connect(lambda checked, path=repo: self.openRepository(path))
            self.recentReposMenu.addAction(action)
        
        # 如果没有最近仓库，添加提示信息
        if not recentRepos:
            emptyAction = QAction("没有最近打开的仓库", self)
            emptyAction.setEnabled(False)
            self.recentReposMenu.addAction(emptyAction)
            
        # 添加分隔符和清空历史记录动作
        self.recentReposMenu.addSeparator()
        if clearAction:
            self.recentReposMenu.addAction(clearAction)
        else:
            clearRecentAction = QAction("清空历史记录", self)
            clearRecentAction.triggered.connect(self.clearRecentRepositories)
            self.recentReposMenu.addAction(clearRecentAction)
        
    def clearRecentRepositories(self):
        """ 清空最近仓库历史记录 """
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空最近仓库历史记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.configManager.clear_recent_repositories()
            # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
            
            InfoBar.success(
                title="清空成功",
                content="已清空最近仓库历史记录",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def connectSignals(self):
        """ 连接信号与槽 """
        # 编辑器内容改变时，更新预览
        self.editor.textChanged.connect(self.updatePreview)
        
        # 编辑器文档内容变化时，更新导航
        self.editor.documentChanged.connect(self.updateDocumentNavigation)
        
        # 编辑器光标位置变化时，更新导航中的当前项
        self.editor.cursorPositionChanged.connect(self.onCursorPositionChanged)
        
        # 导航项被点击时，将编辑器跳转到对应位置
        self.documentNavigator.headingSelected.connect(self.editor.goToLine)
        
        # 文件浏览器选择文件时，加载文件
        self.fileExplorer.fileSelected.connect(self.loadFile)
        
        # 仓库改变时，通知各组件
        self.repoChanged.connect(self.fileExplorer.setRootPath)
        self.repoChanged.connect(self.gitPanel.setRepository)
        
        # 连接GitPanel的信号
        self.gitPanel.repositoryInitialized.connect(self.onRepositoryInitialized)
        self.gitPanel.repositoryOpened.connect(self.onRepositoryOpened)
        
        # 连接ConfigManager的仓库列表更新信号，实时更新菜单
        self.configManager.recentRepositoriesChanged.connect(self.updateRecentRepositoriesMenu)
        # 同时也通知Git面板更新最近仓库列表
        self.configManager.recentRepositoriesChanged.connect(self.gitPanel.updateRecentRepositories)
        
    def updatePreview(self):
        """ 更新Markdown预览 """
        content = self.editor.toPlainText()
        self.preview.setMarkdown(content)
    
    def createNewFile(self):
        """ 创建新文件 """
        # 这里可以实现新建文件的逻辑
        self.editor.clearText()
        self.statusBar.setCurrentFile("")
    
    def openFile(self):
        """ 打开文件对话框 """
        filePath, _ = QFileDialog.getOpenFileName(
            self, "打开Markdown文件", "", "Markdown Files (*.md *.markdown);;All Files (*)"
        )
        if filePath:
            self.loadFile(filePath)
    
    def saveFile(self):
        """ 保存当前文件 
        Returns:
            bool: 是否成功保存
        """
        currentFile = self.statusBar.getCurrentFile()
        
        # 如果没有当前文件，执行另存为操作
        if not currentFile:
            print("MainWindow.saveFile: No current file, trying saveFileAs")
            return self.saveFileAs()
            
        try:
            # 设置编辑器当前文件路径
            print(f"MainWindow.saveFile: Setting editor.currentFilePath to {currentFile}")
            self.editor.currentFilePath = currentFile
            
            # 使用编辑器的保存方法
            print("MainWindow.saveFile: Calling editor.saveFile()")
            success = self.editor.saveFile()
            
            if success:
                # 更新状态栏
                self.statusBar.setCurrentFile(currentFile)
                print(f"MainWindow.saveFile: Updated statusBar with {currentFile}")
                
                # 显示成功消息
                InfoBar.success(
                    title="保存成功",
                    content=f"文件已保存: {os.path.basename(currentFile)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            
            return success
        except Exception as e:
            import traceback
            print(f"MainWindow.saveFile failed: {str(e)}")
            print(traceback.format_exc())
            show_error_message(self, "保存失败", "保存文件时发生错误", e)
            return False
            
    def saveFileAs(self):
        """ 另存为文件 
        Returns:
            bool: 是否成功保存
        """
        currentFile = self.statusBar.getCurrentFile()
        print(f"MainWindow.saveFileAs: Current file is {currentFile}")
        
        # 设置起始目录
        if currentFile:
            self.editor.currentFilePath = currentFile
            print(f"MainWindow.saveFileAs: Set editor.currentFilePath to {currentFile}")
        
        # 使用编辑器的另存为方法
        print("MainWindow.saveFileAs: Calling editor.saveAsFile()")
        success = self.editor.saveAsFile()
        
        if success and self.editor.currentFilePath:
            # 更新状态栏
            newPath = self.editor.currentFilePath
            self.statusBar.setCurrentFile(newPath)
            print(f"MainWindow.saveFileAs: Updated statusBar with new path: {newPath}")
            
            # 显示成功消息
            InfoBar.success(
                title="保存成功",
                content=f"文件已保存: {os.path.basename(newPath)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
        return success
    
    def openRepository(self, path):
        """ 打开Git仓库 """
        # 检查是否为有效的Git仓库
        try:
            gitManager = GitManager(path)
            if gitManager.isValidRepo():
                self.repoChanged.emit(path)
                self.statusBar.setCurrentRepository(path)
                
                # 添加到最近仓库列表
                self.configManager.add_recent_repository(path)
                # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
                
                return True
            else:
                InfoBar.warning(
                    title="无效仓库",
                    content="所选路径不是有效的Git仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return False
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            return False
    
    def onRepositoryInitialized(self, repo_path):
        """ 处理仓库初始化完成事件 """
        self.repoChanged.emit(repo_path)
        self.statusBar.setCurrentRepository(repo_path)
        
        # 添加到最近仓库列表
        self.configManager.add_recent_repository(repo_path)
        # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
    
    def onRepositoryOpened(self, repo_path):
        """ 处理仓库打开事件 """
        # 简单的防止重复更新的逻辑
        # 检查这个仓库是否已经是最近的第一个仓库
        recent_repos = self.configManager.get_recent_repositories()
        if recent_repos and recent_repos[0] == repo_path:
            # 如果已经是最近的第一个仓库，只更新UI即可，不需要触发一次完整的添加流程
            self.repoChanged.emit(repo_path)
            self.statusBar.setCurrentRepository(repo_path)
            return
            
        # 添加到最近仓库列表并更新UI
        self.configManager.add_recent_repository(repo_path)
        # 不需要手动调用updateRecentRepositoriesMenu，信号连接会自动触发更新
        
        # 更新UI
        self.repoChanged.emit(repo_path)
        self.statusBar.setCurrentRepository(repo_path)
        
    def updateDocumentNavigation(self, document_text):
        """ 更新文档导航 """
        self.documentNavigator.parseDocument(document_text)
        
    def onCursorPositionChanged(self, line_number):
        """ 处理光标位置变化 """
        # 在这里可以更新状态栏显示当前行列信息
        pass 

    def checkAutoSaveRecovery(self):
        """ 检查是否有自动保存文件需要恢复 """
        if hasattr(self, 'editor') and hasattr(self.editor, 'recoverFromAutoSave'):
            recovered = self.editor.recoverFromAutoSave()
            if recovered:
                InfoBar.success(
                    title="恢复成功",
                    content="已从自动保存文件恢复内容",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                ) 

    def closeEvent(self, event):
        """ 在关闭窗口前检查是否有未保存的更改 """
        if hasattr(self, 'editor') and hasattr(self.editor, 'editor') and self.editor.editor.document().isModified():
            reply = QMessageBox.question(
                self, "保存更改", 
                "文档有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                # 尝试保存
                saved = self.saveFile()
                if not saved:
                    # 如果保存失败且用户取消了另存为，则取消关闭
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                # 取消关闭
                event.ignore()
                return
        
        # 停止自动保存定时器
        if hasattr(self, 'editor') and hasattr(self.editor, 'autoSaveTimer'):
            self.editor.autoSaveTimer.stop()
            
        # 移除自动保存文件
        if hasattr(self, 'editor') and hasattr(self.editor, 'autoSavePath'):
            try:
                import os
                if os.path.exists(self.editor.autoSavePath):
                    os.remove(self.editor.autoSavePath)
            except:
                pass
        
        # 接受关闭事件
        event.accept() 

    def showLogDialog(self):
        """ 显示日志管理对话框 """
        dialog = LogDialog(self)
        dialog.exec_() 

    def setupShortcuts(self):
        """ 设置全局快捷键 """
        from PyQt5.QtWidgets import QShortcut
        
        # 保存快捷键
        saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        saveShortcut.activated.connect(self.saveFile)
        
        # 另存为快捷键
        saveAsShortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        saveAsShortcut.activated.connect(self.saveFileAs)

    def showAboutDialog(self):
        """ 显示关于对话框 """
        from PyQt5.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "关于 MGit",
            "<h3>MGit - Markdown笔记与Git版本控制</h3>"
            "<p>一个专为Markdown笔记设计的Git版本控制工具</p>"
            "<p>版本: 1.0.0</p>"
            "<p>© 2025 MGit 团队</p>"
        )

    def openRepositoryDialog(self):
        """打开仓库对话框"""
        from PyQt5.QtWidgets import QFileDialog
        
        dir_path = QFileDialog.getExistingDirectory(self, "选择Git仓库目录")
        if dir_path:
            self.openRepository(dir_path)
            
    def undoEdit(self):
        """撤销编辑操作"""
        if hasattr(self, 'editor') and hasattr(self.editor, 'editor'):
            self.editor.editor.undo()
            
    def redoEdit(self):
        """重做编辑操作"""
        if hasattr(self, 'editor') and hasattr(self.editor, 'editor'):
            self.editor.editor.redo()
            
    def showFindDialog(self):
        """显示查找对话框"""
        if hasattr(self, 'editor') and hasattr(self.editor, 'showFindDialog'):
            self.editor.showFindDialog()
            
    def showReplaceDialog(self):
        """显示替换对话框"""
        if hasattr(self, 'editor') and hasattr(self.editor, 'showReplaceDialog'):
            self.editor.showReplaceDialog()
            
    def toggleExplorer(self):
        """切换文件资源管理器显示状态"""
        if hasattr(self, 'fileExplorer') and hasattr(self, 'leftSplitter'):
            visible = self.toggleExplorerAction.isChecked()
            if not visible:
                # 保存当前大小
                self.fileExplorerSize = self.leftSplitter.sizes()[0]
                # 隐藏
                sizes = self.leftSplitter.sizes()
                self.leftSplitter.setSizes([0, sizes[1]])
            else:
                # 显示并恢复大小
                sizes = self.leftSplitter.sizes()
                if hasattr(self, 'fileExplorerSize'):
                    self.leftSplitter.setSizes([self.fileExplorerSize, sizes[1]])
                else:
                    self.leftSplitter.setSizes([200, sizes[1]])
                    
    def togglePreview(self):
        """切换Markdown预览显示状态"""
        if hasattr(self, 'preview') and hasattr(self, 'editorSplitter'):
            visible = self.togglePreviewAction.isChecked()
            sizes = self.editorSplitter.sizes()
            if not visible:
                # 保存当前大小
                self.previewSize = sizes[1]
                # 隐藏
                self.editorSplitter.setSizes([sizes[0] + sizes[1], 0])
            else:
                # 显示并恢复大小
                if hasattr(self, 'previewSize') and self.previewSize:
                    self.editorSplitter.setSizes([sizes[0], self.previewSize])
                else:
                    # 默认分配大小
                    total = sum(sizes)
                    self.editorSplitter.setSizes([total // 2, total // 2])
                    
    def toggleGitPanel(self):
        """切换Git面板显示状态"""
        if hasattr(self, 'gitPanel') and hasattr(self, 'mainSplitter'):
            visible = self.toggleGitPanelAction.isChecked()
            if not visible:
                # 保存当前大小
                sizes = self.mainSplitter.sizes()
                self.gitPanelSize = sizes[2]
                # 隐藏
                self.mainSplitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            else:
                # 显示并恢复大小
                sizes = self.mainSplitter.sizes()
                if hasattr(self, 'gitPanelSize') and self.gitPanelSize:
                    self.mainSplitter.setSizes([sizes[0], sizes[1] - self.gitPanelSize, self.gitPanelSize])
                else:
                    # 默认分配大小
                    self.mainSplitter.setSizes([sizes[0], sizes[1] - 250, 250])
            
    def commitChanges(self):
        """提交变更"""
        if hasattr(self, 'gitPanel'):
            self.gitPanel.commitChanges()
            
    def pushChanges(self):
        """推送变更"""
        if hasattr(self, 'gitPanel'):
            self.gitPanel.pushChanges()
            
    def pullChanges(self):
        """拉取变更"""
        if hasattr(self, 'gitPanel'):
            self.gitPanel.pullChanges()
            
    def manageBranches(self):
        """管理分支"""
        if hasattr(self, 'gitPanel'):
            self.gitPanel.manageBranches()
            
    def viewHistory(self):
        """查看历史"""
        if hasattr(self, 'gitPanel'):
            self.gitPanel.viewHistory()
            
    def checkForUpdates(self):
        """检查应用更新"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "检查更新", 
            "当前版本已是最新版本。"
        )
        
    def openDevTools(self):
        """打开开发者工具"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "开发者工具", 
            "此功能尚未实现。"
        )
    
    def loadFile(self, file_path):
        """加载文件到编辑器
        
        Args:
            file_path: 文件路径
        """
        if hasattr(self, 'editor'):
            try:
                # 检查是否为文本文件
                import os
                _, ext = os.path.splitext(file_path)
                text_exts = ['.txt', '.md', '.markdown', '.py', '.js', '.html', '.css', '.json', '.xml', '.yml', '.yaml']
                
                if ext.lower() in text_exts:
                    # 加载文件内容到编辑器
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.editor.setPlainText(content)
                    self.editor.currentFilePath = file_path
                    self.statusBar.setCurrentFile(file_path)
                    
                    # 如果是Markdown文件，更新预览
                    if ext.lower() in ['.md', '.markdown']:
                        self.updatePreview()
                else:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "不支持的文件类型", f"不支持编辑 {ext} 类型的文件")
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "打开文件失败", f"无法打开文件: {str(e)}")
    
    def cloneRepository(self):
        """克隆远程仓库"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit, QFileDialog
        
        # 获取远程仓库URL
        url, ok = QInputDialog.getText(
            self, "克隆仓库", "请输入远程仓库URL:",
            QLineEdit.Normal, "")
        
        if ok and url:
            # 选择克隆目标目录
            target_dir = QFileDialog.getExistingDirectory(self, "选择克隆目标目录")
            
            if target_dir:
                try:
                    # 使用GitPanel的克隆功能
                    self.gitPanel.cloneRepository(url, target_dir)
                except Exception as e:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "克隆失败", f"无法克隆仓库: {str(e)}")
    
    def updateDocumentNavigation(self, document_text):
        """ 更新文档导航 """
        self.documentNavigator.parseDocument(document_text)
        
    def onCursorPositionChanged(self, line_number):
        """ 处理光标位置变化 """
        # 在这里可以更新状态栏显示当前行列信息
        pass 