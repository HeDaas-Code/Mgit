#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
开发者工具插件 - 为MGit添加开发者工具功能
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                           QPushButton, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem,
                           QSplitter, QGroupBox, QCheckBox, QComboBox, QTableWidget,
                           QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout, 
                           QLineEdit, QDialogButtonBox, QAbstractItemView, QListWidget, QSpinBox,
                           QFileDialog, QInputDialog, QTextBrowser, QTabWidget, QProgressBar,
                           QStackedWidget, QPlainTextEdit, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QProcess, QByteArray, QUrl, QUrlQuery, QObject, QSettings, QDateTime, QThread, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QIcon, QColor
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition
from src.utils.plugin_base import PluginBase
import sys
import os
import platform
import json
import re
import importlib
import pkg_resources
import traceback
import gc
import psutil
import cProfile
import pstats
import io
import unittest
import requests
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
import threading
import time
import fnmatch
import inspect
import datetime
from PyQt5.QtWidgets import QApplication
import subprocess
import logging
import shlex
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtCore import QByteArray, QUrl, QUrlQuery
import tempfile
import sip

class LogHandlerWithSignal(logging.Handler, QObject):
    """带有信号的日志处理器，用于在GUI中显示日志"""
    new_log = pyqtSignal(str)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
    def emit(self, record):
        log_entry = self.format(record)
        self.new_log.emit(log_entry)

class DeveloperToolsWindow(QWidget):
    """开发者工具窗口"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setWindowTitle("MGit 开发者工具")
        self.resize(1000, 500)  # 调整默认大小为宽度更大，高度更小
        
        self.tabWidget = QTabWidget()
        
        # 初始化网络线程和管理器
        self.networkThread = QThread()
        self.networkManager = None
        self.responseProcessor = None
        
        # 创建各个选项卡
        self.sysInfoTab = QWidget()
        self.pluginDevTab = QWidget()
        self.dependenciesTab = QWidget()
        self.logsTab = QWidget()
        self.performanceTab = QWidget()  # 性能检测选项卡
        self.testRunnerTab = QWidget()   # 测试运行选项卡
        
        # 设置各个选项卡
        self.setupSysInfoTab()
        self.setupPluginDevTab()
        self.setupDependenciesTab()
        self.setupLogsTab()
        self.setupPerformanceTab()
        self.testRunnerTab = self.setupTestRunnerTab()
        
        # 设置网络测试选项卡
        self.networkTestTab = self.setupNetworkTestTab()
        
        # 添加选项卡到QTabWidget
        self.tabWidget.addTab(self.sysInfoTab, "系统信息")
        self.tabWidget.addTab(self.pluginDevTab, "插件开发")
        self.tabWidget.addTab(self.dependenciesTab, "依赖库")
        self.tabWidget.addTab(self.logsTab, "应用日志")
        self.tabWidget.addTab(self.performanceTab, "性能检测")
        self.tabWidget.addTab(self.testRunnerTab, "测试运行器")
        self.tabWidget.addTab(self.networkTestTab, "网络测试")
        
        # 创建抓包管理器
        self.packetCaptureManager = PacketCaptureManager(self)
        self.packetCaptureManager.packetCaptured.connect(self.onPacketCaptured)
        
        # 主布局
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        mainLayout.setSpacing(5)  # 减小间距
        mainLayout.addWidget(self.tabWidget)
        
        # 添加自定义状态栏
        self.statusLabel = QLabel()
        self.statusLabel.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.statusLabel.setAlignment(Qt.AlignLeft)
        self.statusLabel.setMinimumHeight(20)
        mainLayout.addWidget(self.statusLabel)
        
        # 底部按钮区域
        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(0, 0, 0, 0)  # 减小边距
        refreshButton = QPushButton("刷新")
        refreshButton.clicked.connect(self.refreshCurrentTab)
        buttonLayout.addWidget(refreshButton)
        
        closeButton = QPushButton("关闭")
        closeButton.clicked.connect(self.close)
        buttonLayout.addWidget(closeButton)
        
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        
        # 初始化日志监听
        self.log_handler = LogHandlerWithSignal()
        self.log_handler.new_log.connect(self.appendLog)
        logging.getLogger().addHandler(self.log_handler)
        
        # 系统信息定时更新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateSysInfo)
        self.timer.start(2000)  # 每2秒更新一次
        
        # 初始化成员变量
        self.currentRequest = None
        self.requestHistoryCount = 0
        self.request_start_time = 0
        
        # 初始化后尝试获取插件管理器
        plugin_manager = self.findPluginManager()
        if plugin_manager:
            print(f"窗口初始化: 获取到插件管理器，已加载{len(plugin_manager.plugins) if hasattr(plugin_manager, 'plugins') else 0}个插件")
    
    # 内部类定义
    class CreatePluginDialog(QDialog):
        """创建插件对话框"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("创建新插件")
            self.resize(700, 500)
            
            # 主布局
            layout = QVBoxLayout(self)
            
            # 表单部分
            formLayout = QFormLayout()
            
            self.nameEdit = QLineEdit()
            self.nameEdit.setPlaceholderText("例如: 我的插件")
            formLayout.addRow("插件名称:", self.nameEdit)
            
            self.fileNameEdit = QLineEdit()
            self.fileNameEdit.setPlaceholderText("例如: my_plugin.py")
            formLayout.addRow("文件名:", self.fileNameEdit)
            
            self.authorEdit = QLineEdit()
            self.authorEdit.setPlaceholderText("例如: 张三")
            formLayout.addRow("作者:", self.authorEdit)
            
            self.versionEdit = QLineEdit()
            self.versionEdit.setText("1.0.0")
            formLayout.addRow("版本:", self.versionEdit)
            
            self.descriptionEdit = QLineEdit()
            self.descriptionEdit.setPlaceholderText("插件的简短描述")
            formLayout.addRow("描述:", self.descriptionEdit)
            
            layout.addLayout(formLayout)
            
            # 代码编辑区域
            layout.addWidget(QLabel("插件代码:"))
            
            self.codeEdit = QTextEdit()
            self.codeEdit.setFont(QFont("Courier New", 10))
            layout.addWidget(self.codeEdit)
            
            # 使用模板代码填充代码编辑器
            self.loadTemplateCode()
            
            # 底部按钮
            buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttonBox.accepted.connect(self.accept)
            buttonBox.rejected.connect(self.reject)
            layout.addWidget(buttonBox)
            
            # 连接信号
            self.nameEdit.textChanged.connect(self.updateTemplateCode)
            self.authorEdit.textChanged.connect(self.updateTemplateCode)
            self.versionEdit.textChanged.connect(self.updateTemplateCode)
            self.descriptionEdit.textChanged.connect(self.updateTemplateCode)
            
        def loadTemplateCode(self):
            """加载模板代码"""
            template = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
{name} - {description}
"""

from src.utils.plugin_base import PluginBase
from qfluentwidgets import FluentIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class Plugin(PluginBase):
    """MGit插件类"""
    
    def __init__(self):
        super().__init__()
        self.name = "{name}"
        self.version = "{version}"
        self.author = "{author}"
        self.description = "{description}"
        self.view = None
        
    def get_view(self):
        """获取视图"""
        if not self.view:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            # 在这里添加自定义UI组件
            title = QLabel("{name}")
            title.setStyleSheet("font-size: 18px; font-weight: bold;")
            layout.addWidget(title)
            
            description = QLabel("{description}")
            layout.addWidget(description)
            
            button = QPushButton("点击我")
            button.clicked.connect(self.on_button_clicked)
            layout.addWidget(button)
            
            # 设置视图信息
            self.view = {{
                'name': '{name}',
                'icon': FluentIcon.GITHUB,  # 可以更改为其他图标
                'widget': widget
            }}
            
        return self.view
        
    def on_button_clicked(self):
        """按钮点击处理"""
        print("按钮被点击了!")
        
    def enable(self):
        """启用插件"""
        return True
        
    def disable(self):
        """禁用插件"""
        return True
'''
            self.codeEdit.setText(template)
            self.updateTemplateCode()
            
        def updateTemplateCode(self):
            """根据用户输入更新模板代码"""
            current_code = self.codeEdit.toPlainText()
            
            # 获取用户输入的值
            name = self.nameEdit.text() or "我的插件"
            author = self.authorEdit.text() or "未知作者"
            version = self.versionEdit.text() or "1.0.0"
            description = self.descriptionEdit.text() or "一个MGit插件"
            
            # 替换模板代码中的占位符
            updated_code = current_code.format(
                name=name,
                author=author,
                version=version,
                description=description
            )
            
            # 只有当代码实际变化时才更新，以避免光标位置重置
            if updated_code != current_code:
                cursor_position = self.codeEdit.textCursor().position()
                self.codeEdit.setText(updated_code)
                
                # 尝试恢复光标位置
                cursor = self.codeEdit.textCursor()
                cursor.setPosition(min(cursor_position, len(updated_code)))
                self.codeEdit.setTextCursor(cursor)
            
        def getPluginData(self):
            """获取插件数据"""
            name = self.nameEdit.text()
            file_name = self.fileNameEdit.text()
            
            # 确保文件名以.py结尾
            if file_name and not file_name.endswith('.py'):
                file_name += '.py'
                
            return {
                'name': name,
                'file_name': file_name,
                'author': self.authorEdit.text(),
                'version': self.versionEdit.text(),
                'description': self.descriptionEdit.text(),
                'code': self.codeEdit.toPlainText()
            }

    def setupSysInfoTab(self):
        """设置系统信息标签页"""
        # 使用滚动区域来显示系统信息，避免窗口过高
        infoScrollArea = QScrollArea()
        infoScrollArea.setWidgetResizable(True)
        infoScrollArea.setFrameShape(QFrame.NoFrame)
        
        # 内容容器
        infoContainer = QWidget()
        infoLayout = QVBoxLayout(infoContainer)
        infoLayout.setContentsMargins(3, 3, 3, 3)
        infoLayout.setSpacing(3)
        
        # 系统信息显示区
        self.sysInfoText = QTextBrowser()
        self.sysInfoText.setReadOnly(True)
        self.sysInfoText.setOpenExternalLinks(True)  # 允许打开链接
        
        # 添加一些初始化内容
        self.sysInfoText.setHtml("<h2>系统信息</h2><p>加载中...</p>")
        
        infoLayout.addWidget(self.sysInfoText)
        
        # 设置刷新按钮
        refreshButton = QPushButton("刷新系统信息")
        refreshButton.clicked.connect(self.updateSystemInfo)
        infoLayout.addWidget(refreshButton)
        
        # 放入滚动区域
        infoScrollArea.setWidget(infoContainer)
        
        # 主布局
        mainLayout = QVBoxLayout(self.sysInfoTab)
        mainLayout.setContentsMargins(3, 3, 3, 3)
        mainLayout.addWidget(infoScrollArea)
        
        # 初始加载系统信息
        self.updateSystemInfo()
    
    def setupPluginDevTab(self):
        """设置插件开发选项卡"""
        layout = QVBoxLayout(self.pluginDevTab)
        
        # 插件开发帮助
        helpGroup = QGroupBox("插件开发指南")
        helpLayout = QVBoxLayout(helpGroup)
        
        helpText = QTextBrowser()
        helpText.setOpenExternalLinks(True)
        
        # 从plugin_development.md加载内容
        try:
            docs_path = os.path.join(os.getcwd(), 'docs', 'plugin_development.md')
            if os.path.exists(docs_path):
                with open(docs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 使用QTextBrowser的markdown支持直接渲染
                    helpText.setMarkdown(content)
            else:
                helpText.setHtml("<p>找不到插件开发文档。请查看 docs/plugin_development.md</p>")
        except Exception as e:
            helpText.setHtml(f"<p>加载开发文档时出错: {str(e)}</p>")
        
        helpLayout.addWidget(helpText)
        
        layout.addWidget(helpGroup)
        
        # 插件工具
        toolsGroup = QGroupBox("插件工具")
        toolsLayout = QHBoxLayout(toolsGroup)
        
        createPluginBtn = QPushButton("创建新插件")
        createPluginBtn.clicked.connect(self.createNewPlugin)
        toolsLayout.addWidget(createPluginBtn)
        
        reloadPluginsBtn = QPushButton("重新加载插件")
        reloadPluginsBtn.clicked.connect(self.reloadPlugins)
        toolsLayout.addWidget(reloadPluginsBtn)
        
        layout.addWidget(toolsGroup)
        
        # 当前已加载的插件
        pluginsGroup = QGroupBox("已加载插件")
        pluginsLayout = QVBoxLayout(pluginsGroup)
        
        self.pluginsTable = QTableWidget()
        self.pluginsTable.setColumnCount(5)
        self.pluginsTable.setHorizontalHeaderLabels(["名称", "版本", "类型", "作者", "状态"])
        self.pluginsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        pluginsLayout.addWidget(self.pluginsTable)
        
        layout.addWidget(pluginsGroup)
        
        # 加载插件数据
        self.updatePluginsTable()
    
    def setupDependenciesTab(self):
        """设置依赖库选项卡"""
        layout = QVBoxLayout(self.dependenciesTab)
        
        # 依赖库表格
        self.dependenciesTable = QTableWidget()
        self.dependenciesTable.setColumnCount(3)
        self.dependenciesTable.setHorizontalHeaderLabels(["包名", "版本", "位置"])
        self.dependenciesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.dependenciesTable)
        
        # 加载依赖库信息
        self.updateDependencies()
    
    def setupLogsTab(self):
        """设置日志选项卡"""
        layout = QVBoxLayout(self.logsTab)
        
        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        self.logText.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont("Courier New", 9)
        self.logText.setFont(font)
        layout.addWidget(self.logText)
        
        buttonLayout = QHBoxLayout()
        clearButton = QPushButton("清除日志")
        clearButton.clicked.connect(self.clearLogs)
        buttonLayout.addWidget(clearButton)
        
        refreshLogButton = QPushButton("刷新日志")
        refreshLogButton.clicked.connect(self.updateLogs)
        buttonLayout.addWidget(refreshLogButton)
        
        layout.addLayout(buttonLayout)
        
        # 加载日志
        self.updateLogs()
    
    def updateSystemInfo(self):
        """更新系统信息"""
        info = []
        
        # 尝试读取开发信息文件
        dev_info_path = os.path.join(os.path.expanduser("~"), ".mgit", "dev_info.json")
        
        if os.path.exists(dev_info_path):
            try:
                with open(dev_info_path, 'r', encoding='utf-8') as f:
                    dev_info = json.load(f)
                
                # Python信息
                info.append("<h3>Python环境</h3>")
                info.append(f"<p>Python版本: {dev_info['system']['python_version']}</p>")
                info.append(f"<p>Python实现: {platform.python_implementation()}</p>")
                info.append(f"<p>Python编译器: {platform.python_compiler()}</p>")
                info.append(f"<p>Python路径: {sys.executable}</p>")
                
                # 操作系统信息
                info.append("<h3>操作系统</h3>")
                info.append(f"<p>系统: {dev_info['system']['os']}</p>")
                info.append(f"<p>平台: {dev_info['system']['platform']}</p>")
                info.append(f"<p>主机名: {dev_info['system']['hostname']}</p>")
                
                # MGit信息
                info.append("<h3>MGit应用</h3>")
                info.append(f"<p>版本: {dev_info['version']['string']}</p>")
                info.append(f"<p>构建类型: {dev_info['app']['build_type']}</p>")
                info.append(f"<p>启动时间: {dev_info['app']['launch_time']}</p>")
                
                # 路径信息
                info.append("<h3>路径信息</h3>")
                info.append(f"<p>应用目录: {dev_info['paths']['app_dir']}</p>")
                info.append(f"<p>用户目录: {dev_info['paths']['user_home']}</p>")
                info.append(f"<p>应用数据: {dev_info['paths']['app_data']}</p>")
                info.append(f"<p>插件目录: {dev_info['paths']['plugins_dir']}</p>")
                info.append(f"<p>用户插件目录: {dev_info['paths']['user_plugins_dir']}</p>")
                
            except Exception as e:
                logging.error(f"读取开发信息文件出错: {str(e)}")
                # 如果读取失败，使用原始方法
                self.updateSystemInfoFallback(info)
        else:
            # 开发信息文件不存在，使用原始方法
            self.updateSystemInfoFallback(info)
        
        self.sysInfoText.setHtml("".join(info))
    
    def updateSystemInfoFallback(self, info):
        """系统信息的备用获取方法"""
        # Python信息
        info.append("<h3>Python环境</h3>")
        info.append(f"<p>Python版本: {platform.python_version()}</p>")
        info.append(f"<p>Python实现: {platform.python_implementation()}</p>")
        info.append(f"<p>Python编译器: {platform.python_compiler()}</p>")
        info.append(f"<p>Python路径: {sys.executable}</p>")
        
        # 操作系统信息
        info.append("<h3>操作系统</h3>")
        info.append(f"<p>系统: {platform.system()}</p>")
        info.append(f"<p>版本: {platform.version()}</p>")
        info.append(f"<p>架构: {platform.machine()}</p>")
        
        # MGit信息
        info.append("<h3>MGit应用</h3>")
        try:
            from src.utils.version import VERSION
            info.append(f"<p>版本: {VERSION}</p>")
        except ImportError:
            info.append("<p>版本: 未知</p>")
            
        # 路径信息
        info.append("<h3>路径信息</h3>")
        info.append(f"<p>工作目录: {os.getcwd()}</p>")
        
        # 检查plugin_manager是否存在
        if hasattr(self.plugin, 'plugin_manager') and self.plugin.plugin_manager is not None:
            info.append(f"<p>插件目录: {self.plugin.plugin_manager.plugin_dir}</p>")
            info.append(f"<p>用户插件目录: {self.plugin.plugin_manager.user_plugin_dir}</p>")
        else:
            info.append("<p>插件目录: 未知</p>")
            info.append("<p>用户插件目录: 未知</p>")
        
    def updatePluginsTable(self):
        """更新插件表格"""
        self.pluginsTable.setRowCount(0)
        
        # 尝试获取插件管理器
        plugin_manager = self.findPluginManager()
        
        # 打印调试信息
        print(f"updatePluginsTable: plugin_manager = {plugin_manager}")
        
        # 检查plugin_manager是否存在
        if plugin_manager is None:
            # 显示一行提示信息
            self.pluginsTable.insertRow(0)
            info_item = QTableWidgetItem("插件管理器尚未初始化")
            self.pluginsTable.setItem(0, 0, info_item)
            for i in range(1, 5):
                self.pluginsTable.setItem(0, i, QTableWidgetItem("-"))
            return
            
        # 检查plugins属性是否存在
        if not hasattr(plugin_manager, 'plugins') or plugin_manager.plugins is None:
            self.pluginsTable.insertRow(0)
            info_item = QTableWidgetItem("没有加载任何插件")
            self.pluginsTable.setItem(0, 0, info_item)
            for i in range(1, 5):
                self.pluginsTable.setItem(0, i, QTableWidgetItem("-")) 
            return
        
        # 打印已加载的插件
        print(f"已加载插件: {list(plugin_manager.plugins.keys())}")
        
        row = 0
        
        for plugin_name, plugin_instance in plugin_manager.plugins.items():
            self.pluginsTable.insertRow(row)
            
            # 插件名称
            name = getattr(plugin_instance, 'name', plugin_name)
            name_item = QTableWidgetItem(name)
            self.pluginsTable.setItem(row, 0, name_item)
            
            # 版本
            version = getattr(plugin_instance, 'version', "未知")
            version_item = QTableWidgetItem(str(version))
            self.pluginsTable.setItem(row, 1, version_item)
            
            # 类型
            plugin_type = getattr(plugin_instance, 'plugin_type', "未知")
            type_item = QTableWidgetItem(str(plugin_type))
            self.pluginsTable.setItem(row, 2, type_item)
            
            # 作者
            author = getattr(plugin_instance, 'author', "未知")
            author_item = QTableWidgetItem(str(author))
            self.pluginsTable.setItem(row, 3, author_item)
            
            # 状态
            enabled = getattr(plugin_instance, 'enabled', False)
            status_text = "已启用" if enabled else "已禁用"
            status_item = QTableWidgetItem(status_text)
            self.pluginsTable.setItem(row, 4, status_item)
            
            row += 1
    
    def updateDependencies(self):
        """更新依赖库信息"""
        self.dependenciesTable.setRowCount(0)
        
        installed_packages = list(pkg_resources.working_set)
        installed_packages.sort(key=lambda x: x.key)
        
        for i, package in enumerate(installed_packages):
            self.dependenciesTable.insertRow(i)
            
            # 包名
            name_item = QTableWidgetItem(package.key)
            self.dependenciesTable.setItem(i, 0, name_item)
            
            # 版本
            version_item = QTableWidgetItem(package.version)
            self.dependenciesTable.setItem(i, 1, version_item)
            
            # 位置
            location_item = QTableWidgetItem(package.location)
            self.dependenciesTable.setItem(i, 2, location_item)
    
    def updateLogs(self):
        """更新日志内容"""
        try:
            log_file = os.path.join(os.path.expanduser('~'), '.mgit', 'logs', 'mgit.log')
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    # 读取最后100行日志
                    lines = f.readlines()
                    last_lines = lines[-100:] if len(lines) > 100 else lines
                    self.logText.setText("".join(last_lines))
                    # 滚动到底部
                    self.logText.moveCursor(self.logText.textCursor().End)
            else:
                self.logText.setText("日志文件不存在")
        except Exception as e:
            self.logText.setText(f"无法读取日志: {str(e)}")
    
    def clearLogs(self):
        """清除日志文本框"""
        self.logText.clear()
    
    def refreshCurrentTab(self):
        """刷新当前选项卡"""
        try:
            # 验证tabWidget是否有效
            if not hasattr(self, 'tabWidget') or self.tabWidget is None or sip.isdeleted(self.tabWidget):
                print("refreshCurrentTab: tabWidget不可用")
                return
                
            # 获取当前选项卡
            current_tab = self.tabWidget.currentWidget()
            if current_tab is None:
                print("refreshCurrentTab: 无当前选项卡")
                return
            
            # 根据不同的标签页执行不同的刷新操作
            if current_tab == self.sysInfoTab:
                if hasattr(self, 'updateSystemInfo') and callable(self.updateSystemInfo):
                    self.updateSystemInfo()
            elif current_tab == self.pluginDevTab:
                # 在更新插件表前尝试重新获取插件管理器
                plugin_manager = self.findPluginManager()
                if plugin_manager:
                    print(f"refreshCurrentTab: 找到插件管理器，包含{len(plugin_manager.plugins) if hasattr(plugin_manager, 'plugins') else 0}个插件")
                else:
                    print("refreshCurrentTab: 未找到插件管理器")
                
                if hasattr(self, 'updatePluginsTable') and callable(self.updatePluginsTable):
                    self.updatePluginsTable()
            elif current_tab == self.dependenciesTab:
                if hasattr(self, 'updateDependencies') and callable(self.updateDependencies):
                    self.updateDependencies()
            elif current_tab == self.logsTab:
                if hasattr(self, 'updateLogs') and callable(self.updateLogs):
                    self.updateLogs()
            elif current_tab == self.networkTestTab:
                # 安全地清除响应区域
                try:
                    if hasattr(self, 'clearResponse') and callable(self.clearResponse):
                        self.clearResponse()
                except Exception as e:
                    print(f"refreshCurrentTab: 清除响应时出错: {str(e)}")
                
                # 安全地重置网络管理器
                try:
                    if hasattr(self, 'networkManager') and self.networkManager is not None:
                        self.networkManager.deleteLater()
                        self.networkManager = None
                except Exception as e:
                    print(f"refreshCurrentTab: 重置网络管理器时出错: {str(e)}")
        except Exception as e:
            print(f"refreshCurrentTab: 刷新选项卡时出错: {str(e)}")
    
    def createNewPlugin(self):
        """创建新插件"""
        try:
            # 检查plugin_manager是否存在
            if not hasattr(self.plugin, 'plugin_manager') or self.plugin.plugin_manager is None:
                QMessageBox.warning(self, "警告", "插件管理器尚未初始化")
                return
                
            # 检查用户插件目录是否存在
            if not hasattr(self.plugin.plugin_manager, 'user_plugin_dir'):
                QMessageBox.warning(self, "警告", "找不到用户插件目录")
                return
                
            # 创建并显示对话框
            dialog = self.CreatePluginDialog(self)
            if dialog.exec_():
                # 获取插件数据
                plugin_data = dialog.getPluginData()
                
                # 验证数据
                if not plugin_data['name'] or not plugin_data['file_name']:
                    QMessageBox.warning(self, "创建失败", "插件名称和文件名不能为空")
                    return
                
                try:
                    # 确定插件文件路径
                    plugin_path = os.path.join(self.plugin.plugin_manager.user_plugin_dir, plugin_data['file_name'])
                    
                    # 检查文件是否已存在
                    if os.path.exists(plugin_path):
                        reply = QMessageBox.question(
                            self, "文件已存在", 
                            f"文件 {plugin_data['file_name']} 已存在，是否覆盖？",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
                    
                    # 写入文件
                    with open(plugin_path, 'w', encoding='utf-8') as f:
                        f.write(plugin_data['code'])
                    
                    QMessageBox.information(
                        self, "创建成功", 
                        f"插件 {plugin_data['name']} 已创建在 {plugin_path}。\n\n"
                        "重启应用程序后插件将被加载。"
                    )
                    
                except Exception as e:
                    QMessageBox.critical(self, "创建失败", f"创建插件时出错：{str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开创建插件对话框：{str(e)}")
    
    def reloadPlugins(self):
        """重新加载插件"""
        try:
            # 检查app和refreshPlugins方法是否可用
            if not hasattr(self.plugin, 'app') or self.plugin.app is None:
                QMessageBox.warning(self, "警告", "应用程序实例尚未初始化")
                return
                
            if not hasattr(self.plugin.app, 'refreshPlugins'):
                QMessageBox.warning(self, "警告", "应用程序不支持刷新插件功能")
                return
                
            # 调用插件管理器的刷新方法
            self.plugin.app.refreshPlugins()
            self.updatePluginsTable()
            QMessageBox.information(self, "成功", "插件已重新加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重新加载插件时出错：{str(e)}")

    def setupPerformanceTab(self):
        """设置性能检测选项卡"""
        # 创建主布局
        perfTab = QWidget()
        mainLayout = QVBoxLayout(perfTab)
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.setSpacing(5)
        
        # 创建顶部标题和控制区域
        topBarWidget = QWidget()
        topBarLayout = QHBoxLayout(topBarWidget)
        topBarLayout.setContentsMargins(0, 0, 0, 0)
        
        titleLabel = QLabel("<b>系统性能监控面板</b>")
        titleLabel.setFont(QFont("Microsoft YaHei", 10))
        
        self.resetChartBtn = QPushButton("重置图表")
        self.resetChartBtn.setFixedWidth(80)
        self.resetChartBtn.clicked.connect(self.resetPerformanceCharts)
        
        topBarLayout.addWidget(titleLabel)
        topBarLayout.addStretch()
        topBarLayout.addWidget(self.resetChartBtn)
        
        mainLayout.addWidget(topBarWidget)
        
        # 信息显示区域
        infoWidget = QWidget()
        infoLayout = QHBoxLayout(infoWidget)
        infoLayout.setContentsMargins(0, 0, 0, 0)
        
        # CPU信息
        self.cpuLabel = QLabel("CPU使用率: 0.0%")
        self.cpuLabel.setFont(QFont("Microsoft YaHei", 9))
        self.cpuLabel.setStyleSheet("color: #0066cc; font-weight: bold;")
        self.cpuProcLabel = QLabel("进程CPU: 0.0%")
        self.cpuProcLabel.setFont(QFont("Microsoft YaHei", 9))
        
        # 内存信息
        self.memLabel = QLabel("内存使用率: 0.0%")
        self.memLabel.setFont(QFont("Microsoft YaHei", 9))
        self.memLabel.setStyleSheet("color: #cc0066; font-weight: bold;")
        self.memProcLabel = QLabel("进程内存: 0.0 MB")
        self.memProcLabel.setFont(QFont("Microsoft YaHei", 9))
        
        cpuInfoLayout = QVBoxLayout()
        cpuInfoLayout.addWidget(self.cpuLabel)
        cpuInfoLayout.addWidget(self.cpuProcLabel)
        
        memInfoLayout = QVBoxLayout()
        memInfoLayout.addWidget(self.memLabel)
        memInfoLayout.addWidget(self.memProcLabel)
        
        infoLayout.addLayout(cpuInfoLayout)
        infoLayout.addStretch()
        infoLayout.addLayout(memInfoLayout)
        
        mainLayout.addWidget(infoWidget)
        
        # 图表区域 - 创建单个图表展示两个指标
        chartFrame = QFrame()
        chartFrame.setFrameShape(QFrame.StyledPanel)
        chartFrame.setMinimumHeight(350)  # 固定最小高度
        chartLayout = QVBoxLayout(chartFrame)
        chartLayout.setContentsMargins(10, 10, 10, 10)
        
        # 创建单个图表，双Y轴显示CPU和内存
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumHeight(300)  # 确保图表有足够高度
        
        # 设置子图边距，避免使用tight_layout()
        self.figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        
        # 创建主坐标轴用于CPU数据
        self.ax1 = self.figure.add_subplot(111)
        # 创建次坐标轴用于内存数据，共享x轴
        self.ax2 = self.ax1.twinx()
        
        # 配置坐标轴
        self.ax1.set_title("系统资源使用情况", fontproperties="Microsoft YaHei")
        self.ax1.set_xlabel("时间 (秒)", fontproperties="Microsoft YaHei")
        self.ax1.set_ylabel("CPU使用率 (%)", color="#0066cc", fontproperties="Microsoft YaHei")
        self.ax1.tick_params(axis="y", labelcolor="#0066cc")
        self.ax1.set_ylim(0, 100)
        self.ax1.grid(True, linestyle="-.", alpha=0.3, which="both")
        
        self.ax2.set_ylabel("内存使用 (MB)", color="#cc0066", fontproperties="Microsoft YaHei")
        self.ax2.tick_params(axis="y", labelcolor="#cc0066")
        
        # 添加线条并直接在图表上添加图例
        self.cpu_line, = self.ax1.plot([], [], "b-", linewidth=1.5, label="CPU使用率 (%)")
        self.memory_line, = self.ax2.plot([], [], "r-", linewidth=1.5, label="内存使用 (MB)")
        
        # 手动创建简单的图例标记
        cpu_label = QLabel("■ CPU使用率 (%)")
        cpu_label.setStyleSheet("color: #0066cc;")
        cpu_label.setFont(QFont("Microsoft YaHei", 9))
        
        mem_label = QLabel("■ 内存使用 (MB)")
        mem_label.setStyleSheet("color: #cc0066;")
        mem_label.setFont(QFont("Microsoft YaHei", 9))
        
        legendWidget = QWidget()
        legendLayout = QHBoxLayout(legendWidget)
        legendLayout.setContentsMargins(0, 0, 0, 0)
        legendLayout.addWidget(cpu_label)
        legendLayout.addSpacing(15)
        legendLayout.addWidget(mem_label)
        legendLayout.addStretch()
        
        chartLayout.addWidget(self.canvas)
        chartLayout.addWidget(legendWidget)
        mainLayout.addWidget(chartFrame)
        
        # 性能分析控制区域
        profilingGroup = QGroupBox("性能分析")
        profilingGroup.setFont(QFont("Microsoft YaHei", 9))
        profilingLayout = QVBoxLayout(profilingGroup)
        
        # 函数选择
        funcLayout = QHBoxLayout()
        
        funcLabel = QLabel("函数路径:")
        funcLabel.setFont(QFont("Microsoft YaHei", 9))
        self.funcPathEdit = QLineEdit()
        self.funcPathEdit.setPlaceholderText("例如: src.utils.file_manager.save_file")
        self.funcPathEdit.setFont(QFont("Microsoft YaHei", 9))
        
        funcLayout.addWidget(funcLabel)
        funcLayout.addWidget(self.funcPathEdit, 1)
        
        profilingLayout.addLayout(funcLayout)
        
        # 分析按钮区域
        btnLayout = QHBoxLayout()
        
        self.funcProfileBtn = QPushButton("函数分析")
        self.funcProfileBtn.setFont(QFont("Microsoft YaHei", 9))
        self.funcProfileBtn.clicked.connect(self.startFunctionProfiling)
        btnLayout.addWidget(self.funcProfileBtn)
        
        self.cpuProfileBtn = QPushButton("CPU分析")
        self.cpuProfileBtn.setFont(QFont("Microsoft YaHei", 9))
        self.cpuProfileBtn.clicked.connect(self.startCpuProfiling)
        btnLayout.addWidget(self.cpuProfileBtn)
        
        self.memProfileBtn = QPushButton("内存分析")
        self.memProfileBtn.setFont(QFont("Microsoft YaHei", 9))
        self.memProfileBtn.clicked.connect(self.startMemoryProfiling)
        btnLayout.addWidget(self.memProfileBtn)
        
        self.stopProfileBtn = QPushButton("停止分析")
        self.stopProfileBtn.setFont(QFont("Microsoft YaHei", 9))
        self.stopProfileBtn.clicked.connect(self.stopProfiling)
        self.stopProfileBtn.setEnabled(False)
        btnLayout.addWidget(self.stopProfileBtn)
        
        btnLayout.addStretch()
        profilingLayout.addLayout(btnLayout)
        
        mainLayout.addWidget(profilingGroup)
        
        # 性能分析结果
        resultGroup = QGroupBox("分析结果")
        resultGroup.setFont(QFont("Microsoft YaHei", 9))
        resultLayout = QVBoxLayout(resultGroup)
        
        self.profilingResultText = QTextEdit()
        self.profilingResultText.setReadOnly(True)
        self.profilingResultText.setFont(QFont("Consolas", 9))
        self.profilingResultText.setMinimumHeight(150)
        
        resultLayout.addWidget(self.profilingResultText)
        mainLayout.addWidget(resultGroup)
        
        # 数据存储
        self.time_data = []
        self.cpu_data = []
        self.memory_data = []
        self.max_points = 60  # 最多显示60个数据点
        
        # 创建性能数据定时器
        self.perfTimer = QTimer(self)
        self.perfTimer.timeout.connect(self.updatePerformanceData)
        self.perfTimer.start(1000)  # 每秒更新一次
        
        # 布局比例设置
        mainLayout.setStretch(0, 0)  # 顶部标题区
        mainLayout.setStretch(1, 0)  # 信息显示区
        mainLayout.setStretch(2, 3)  # 图表区
        mainLayout.setStretch(3, 1)  # 控制区
        mainLayout.setStretch(4, 2)  # 结果区
        
        self.performanceTab = perfTab
        return perfTab

    def resetPerformanceCharts(self):
        """重置性能图表数据"""
        self.time_data = []
        self.cpu_data = []
        self.memory_data = []
        
        # 清除数据
        self.cpu_line.set_data([], [])
        self.memory_line.set_data([], [])
        
        # 重设坐标轴
        self.ax1.set_xlim(0, 60)
        self.ax1.set_ylim(0, 100)
        self.ax2.set_ylim(0, 1000)  # 内存坐标轴默认设置
        
        # 刷新图表 - 不使用tight_layout避免警告
        self.canvas.draw()
        
        # 更新状态栏
        self.statusBar().showMessage("性能监控图表已重置", 3000)

    def updatePerformanceData(self):
        """更新性能监控数据"""
        try:
            # 获取系统性能数据
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)  # 转换为MB
            
            # 获取当前进程数据
            process = psutil.Process()
            process_cpu = process.cpu_percent() / psutil.cpu_count()
            process_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # 更新信息标签
            self.cpuLabel.setText(f"CPU使用率: {cpu_percent:.1f}%")
            self.cpuProcLabel.setText(f"进程CPU: {process_cpu:.1f}%")
            self.memLabel.setText(f"内存使用率: {memory_percent:.1f}%")
            self.memProcLabel.setText(f"进程内存: {process_memory:.1f} MB")
            
            # 更新图表数据
            current_time = time.time()
            if not self.time_data:
                start_time = current_time
            else:
                start_time = self.time_data[0]
            
            # 计算相对时间（秒）
            time_point = current_time - start_time
            
            # 添加新数据点
            self.time_data.append(time_point)
            self.cpu_data.append(cpu_percent)
            self.memory_data.append(memory_used_mb)
            
            # 限制数据点数量
            if len(self.time_data) > self.max_points:
                self.time_data = self.time_data[-self.max_points:]
                self.cpu_data = self.cpu_data[-self.max_points:]
                self.memory_data = self.memory_data[-self.max_points:]
            
            # 更新图表
            self._updateCombinedChart(process_cpu, process_memory)
            
        except Exception as e:
            logging.error(f"更新性能数据时出错: {str(e)}")

    def _updateCombinedChart(self, process_cpu, process_memory):
        """更新合并的CPU和内存图表"""
        try:
            if not self.time_data:
                return
            
            # 设置动态X轴范围，显示最近60秒的数据
            max_time = max(self.time_data)
            min_time = max(0, max_time - 60)
            self.ax1.set_xlim(min_time, max(min_time + 60, max_time + 1))
            
            # 更新CPU数据
            self.cpu_line.set_data(self.time_data, self.cpu_data)
            
            # 更新内存数据和Y轴范围
            self.memory_line.set_data(self.time_data, self.memory_data)
            
            # 动态调整内存Y轴范围
            if self.memory_data:
                mem_min = min(self.memory_data)
                mem_max = max(self.memory_data)
                
                if mem_max > mem_min:
                    # 添加10%的边距
                    y_range = mem_max - mem_min
                    y_min = max(0, mem_min - y_range * 0.1)
                    y_max = mem_max + y_range * 0.1
                    
                    # 设置Y轴范围
                    self.ax2.set_ylim(y_min, y_max)
            
            # 更新标题
            self.ax1.set_title(f"系统资源使用情况 - CPU: {process_cpu:.1f}% | 内存: {process_memory:.1f} MB", 
                              fontproperties="Microsoft YaHei")
            
            # 刷新图表 - 不使用tight_layout避免警告
            self.canvas.draw()
        
        except Exception as e:
            logging.error(f"更新图表时出错: {str(e)}")

    def startFunctionProfiling(self):
        """启动函数性能分析"""
        func_path = self.funcPathEdit.text().strip()
        if not func_path:
            QMessageBox.warning(self, "警告", "请输入要分析的函数路径")
            return
        
        self.profilingResultText.clear()
        self.profilingResultText.append(f"开始分析函数: {func_path}\n")
        
        try:
            # 解析函数路径
            parts = func_path.split('.')
            module_path = '.'.join(parts[:-1])
            func_name = parts[-1]
            
            # 导入模块
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            
            # 记录开始时间
            self.profilingResultText.append("正在分析函数执行时间，请等待...\n")
            
            # 创建性能分析器并启动
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            
            # 设置按钮状态
            self.toggleProfilingButtons(False)
            
            # 启动线程执行函数，避免UI冻结
            self.profile_thread = threading.Thread(target=self._runFunctionProfile, args=(func,))
            self.profile_thread.daemon = True
            self.profile_thread.start()
            
        except Exception as e:
            self.profilingResultText.append(f"启动分析失败: {str(e)}\n{traceback.format_exc()}")
            self.toggleProfilingButtons(True)

    def startCpuProfiling(self):
        """启动CPU性能分析"""
        self.profilingResultText.clear()
        self.profilingResultText.append("开始CPU性能分析...\n")
        
        try:
            # 初始化分析器
            self.profiler = cProfile.Profile()
            self.profiler.enable()
            
            # 设置按钮状态
            self.toggleProfilingButtons(False)
            
            # 记录开始时间
            self.profile_start_time = time.time()
            
            # 通知用户
            self.profilingResultText.append("CPU分析正在进行中...\n")
            self.profilingResultText.append("请继续使用应用程序，然后点击'停止分析'按钮结束分析。\n")
            
        except Exception as e:
            self.profilingResultText.append(f"启动CPU分析失败: {str(e)}\n{traceback.format_exc()}")
            self.toggleProfilingButtons(True)

    def startMemoryProfiling(self):
        """启动内存性能分析"""
        self.profilingResultText.clear()
        self.profilingResultText.append("开始内存性能分析...\n")
        
        try:
            # 设置按钮状态
            self.toggleProfilingButtons(False)
            
            # 进行垃圾回收
            gc.collect()
            
            # 记录初始对象计数
            self.initial_obj_count = {}
            for obj_type in self._getSignificantTypes():
                self.initial_obj_count[obj_type] = len(gc.get_objects())
            
            # 记录开始时间
            self.profile_start_time = time.time()
            
            # 通知用户
            self.profilingResultText.append("内存分析正在进行中...\n")
            self.profilingResultText.append("请继续使用应用程序，然后点击'停止分析'按钮结束分析。\n")
            
        except Exception as e:
            self.profilingResultText.append(f"启动内存分析失败: {str(e)}\n{traceback.format_exc()}")
            self.toggleProfilingButtons(True)

    def stopProfiling(self):
        """停止性能分析"""
        try:
            # 停止CPU分析
            if hasattr(self, 'profiler'):
                self.profiler.disable()
                
                # 创建一个字符串流来捕获输出
                s = io.StringIO()
                
                # 将性能分析结果写入字符串流
                stats = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
                stats.print_stats(30)  # 只显示前30个结果
                
                # 将结果添加到文本框
                self.profilingResultText.append("\n===== 性能分析结果 =====\n")
                self.profilingResultText.append(s.getvalue())
                
                # 删除分析器引用
                delattr(self, 'profiler')
            
            # 停止内存分析
            if hasattr(self, 'initial_obj_count'):
                # 进行垃圾回收
                gc.collect()
                
                # 获取当前对象数量
                final_obj_count = {}
                for obj_type in self._getSignificantTypes():
                    final_obj_count[obj_type] = len(gc.get_objects())
                
                # 计算差异
                self.profilingResultText.append("\n===== 内存分析结果 =====\n")
                self.profilingResultText.append("对象数量变化:\n")
                
                for obj_type in self.initial_obj_count:
                    initial = self.initial_obj_count[obj_type]
                    final = final_obj_count.get(obj_type, 0)
                    diff = final - initial
                    
                    if diff != 0:
                        self.profilingResultText.append(f"{obj_type}: {diff:+d}\n")
                
                # 删除引用
                delattr(self, 'initial_obj_count')
            
            # 显示分析持续时间
            if hasattr(self, 'profile_start_time'):
                duration = time.time() - self.profile_start_time
                self.profilingResultText.append(f"\n分析持续时间: {duration:.2f} 秒\n")
                delattr(self, 'profile_start_time')
            
            self.profilingResultText.append("\n分析已完成。\n")
            
        except Exception as e:
            self.profilingResultText.append(f"停止分析时出错: {str(e)}\n{traceback.format_exc()}")
        finally:
            # 重置按钮状态
            self.toggleProfilingButtons(True)

    def toggleProfilingButtons(self, enabled):
        """切换性能分析按钮状态"""
        self.funcProfileBtn.setEnabled(enabled)
        self.cpuProfileBtn.setEnabled(enabled)
        self.memProfileBtn.setEnabled(enabled)
        self.stopProfileBtn.setEnabled(not enabled)

    def _getSignificantTypes(self):
        """返回需要跟踪的重要对象类型"""
        return [
            "QWidget", "QLabel", "QPushButton", "QLineEdit", "QTextEdit",
            "QVBoxLayout", "QHBoxLayout", "list", "dict", "tuple", "set",
            "function", "module"
        ]

    def _runFunctionProfile(self, func):
        """在后台线程中运行函数分析"""
        try:
            # 调用函数
            result = func()
            
            # 停止分析并显示结果
            QMetaObject.invokeMethod(self, "stopProfiling", Qt.QueuedConnection)
            
        except Exception as e:
            # 在UI线程中显示错误
            error_msg = f"函数执行失败: {str(e)}\n{traceback.format_exc()}"
            try:
                QMetaObject.invokeMethod(
                    self.profilingResultText, 
                    "append", 
                    Qt.QueuedConnection,
                    Q_ARG(str, error_msg))
                
                # 重置按钮状态
                QMetaObject.invokeMethod(
                    self, 
                    "toggleProfilingButtons", 
                    Qt.QueuedConnection,
                    Q_ARG(bool, True))
            except Exception as invoke_error:
                print(f"Error invoking method: {invoke_error}")

    def setupTestRunnerTab(self):
        """设置测试运行器标签页"""
        # 创建主布局
        testTab = QWidget()
        mainLayout = QVBoxLayout(testTab)
        mainLayout.setContentsMargins(3, 3, 3, 3)
        mainLayout.setSpacing(3)
        
        # 使用分割器将控制区域和结果区域分开
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # === 控制区域 ===
        controlWidget = QWidget()
        controlLayout = QVBoxLayout(controlWidget)
        controlLayout.setContentsMargins(3, 3, 3, 3)
        controlLayout.setSpacing(3)
        
        # 测试目录选择
        dirLayout = QHBoxLayout()
        dirLayout.setSpacing(3)
        
        dirLabel = QLabel("测试目录:")
        self.testDirEdit = QLineEdit()
        self.testDirEdit.setPlaceholderText("选择或输入测试文件/目录路径")
        
        browseDirBtn = QPushButton("浏览...")
        browseDirBtn.clicked.connect(self.browseTestDir)
        
        dirLayout.addWidget(dirLabel)
        dirLayout.addWidget(self.testDirEdit, 1)
        dirLayout.addWidget(browseDirBtn)
        
        controlLayout.addLayout(dirLayout)
        
        # 测试模式和选项
        optionsLayout = QHBoxLayout()
        optionsLayout.setSpacing(3)
        
        # 测试模式选择
        modeLayout = QHBoxLayout()
        modeLayout.setSpacing(3)
        
        modeLabel = QLabel("测试模式:")
        self.testModeCombo = QComboBox()
        self.testModeCombo.addItems(["unittest", "pytest", "自定义"])
        self.testModeCombo.currentIndexChanged.connect(self.updateTestMode)
        
        modeLayout.addWidget(modeLabel)
        modeLayout.addWidget(self.testModeCombo)
        
        # 自定义命令输入
        customCmdLabel = QLabel("自定义命令:")
        self.customCmdEdit = QLineEdit()
        self.customCmdEdit.setPlaceholderText("例如: python -m pytest -xvs")
        self.customCmdEdit.setEnabled(False)  # 初始禁用
        
        modeLayout.addWidget(customCmdLabel)
        modeLayout.addWidget(self.customCmdEdit, 1)
        
        optionsLayout.addLayout(modeLayout)
        
        # 测试过滤
        filterLayout = QHBoxLayout()
        filterLayout.setSpacing(3)
        
        filterLabel = QLabel("过滤器:")
        self.testFilterEdit = QLineEdit()
        self.testFilterEdit.setPlaceholderText("输入测试名称过滤 (例如: test_specific_function)")
        
        filterLayout.addWidget(filterLabel)
        filterLayout.addWidget(self.testFilterEdit)
        
        optionsLayout.addLayout(filterLayout)
        
        controlLayout.addLayout(optionsLayout)
        
        # 测试选项复选框
        optionsCheckLayout = QHBoxLayout()
        optionsCheckLayout.setSpacing(10)  # 增加复选框间距
        
        self.verboseCheck = QCheckBox("详细输出")
        self.verboseCheck.setChecked(True)
        
        self.failFastCheck = QCheckBox("快速失败")
        
        self.coverageCheck = QCheckBox("显示覆盖率")
        
        optionsCheckLayout.addWidget(self.verboseCheck)
        optionsCheckLayout.addWidget(self.failFastCheck)
        optionsCheckLayout.addWidget(self.coverageCheck)
        optionsCheckLayout.addStretch()
        
        controlLayout.addLayout(optionsCheckLayout)
        
        # 控制按钮
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(3)
        
        self.runTestBtn = QPushButton("运行测试")
        self.runTestBtn.clicked.connect(self.runTests)
        
        self.stopTestBtn = QPushButton("停止测试")
        self.stopTestBtn.clicked.connect(self.stopTests)
        self.stopTestBtn.setEnabled(False)
        
        self.clearTestBtn = QPushButton("清除结果")
        self.clearTestBtn.clicked.connect(lambda: self.testOutputText.clear())
        
        buttonLayout.addWidget(self.runTestBtn)
        buttonLayout.addWidget(self.stopTestBtn)
        buttonLayout.addWidget(self.clearTestBtn)
        buttonLayout.addStretch()
        
        controlLayout.addLayout(buttonLayout)
        
        # === 结果区域 ===
        resultWidget = QWidget()
        resultLayout = QHBoxLayout(resultWidget)
        resultLayout.setContentsMargins(3, 3, 3, 3)
        
        # 创建水平分割器 - 左侧显示输出，右侧显示历史
        resultSplitter = QSplitter(Qt.Horizontal)
        resultSplitter.setChildrenCollapsible(False)
        
        # 测试输出区域
        outputWidget = QWidget()
        outputLayout = QVBoxLayout(outputWidget)
        outputLayout.setContentsMargins(3, 3, 3, 3)
        
        outputLabel = QLabel("测试输出:")
        self.testOutputText = QTextEdit()
        self.testOutputText.setReadOnly(True)
        self.testOutputText.setFont(QFont("Consolas", 9))  # 使用等宽字体
        
        outputLayout.addWidget(outputLabel)
        outputLayout.addWidget(self.testOutputText)
        
        # 测试历史记录
        historyWidget = QWidget()
        historyLayout = QVBoxLayout(historyWidget)
        historyLayout.setContentsMargins(3, 3, 3, 3)
        
        historyLabel = QLabel("测试历史:")
        self.testHistoryList = QListWidget()
        self.testHistoryList.itemDoubleClicked.connect(self.loadTestHistory)
        
        historyLayout.addWidget(historyLabel)
        historyLayout.addWidget(self.testHistoryList)
        
        # 添加到结果分割器
        resultSplitter.addWidget(outputWidget)
        resultSplitter.addWidget(historyWidget)
        resultSplitter.setSizes([700, 300])  # 输出区域占更多空间
        
        resultLayout.addWidget(resultSplitter)
        
        # 添加主要部件到分割器
        splitter.addWidget(controlWidget)
        splitter.addWidget(resultWidget)
        splitter.setSizes([200, 300])  # 结果区域占更多空间
        
        # 将分割器添加到主布局
        mainLayout.addWidget(splitter)
        
        # 初始化测试进程
        self.test_process = None
        
        # 修改此处，不再重复添加标签页
        # self.tabWidget.addTab(testTab, "测试运行器")
        return testTab

    def browseTestDir(self):
        """浏览并选择测试目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择测试目录", "")
        if directory:
            self.testDirEdit.setText(directory)
            
    def updateTestMode(self, index):
        """更新测试模式"""
        # 仅当选择"自定义"时启用自定义命令输入
        self.customCmdEdit.setEnabled(index == 2)  # "自定义"选项的索引为2
        
    def runTests(self):
        """运行测试"""
        test_dir = self.testDirEdit.text().strip()
        if not test_dir:
            QMessageBox.warning(self, "警告", "请选择测试目录或文件")
            return
            
        if not os.path.exists(test_dir):
            QMessageBox.warning(self, "警告", f"测试路径不存在: {test_dir}")
            return
            
        # 获取测试配置
        test_mode = self.testModeCombo.currentText()
        test_filter = self.testFilterEdit.text().strip()
        verbose = self.verboseCheck.isChecked()
        fail_fast = self.failFastCheck.isChecked()
        show_coverage = self.coverageCheck.isChecked()
        
        # 构建测试命令
        command = []
        
        if test_mode == "unittest":
            command = ["python", "-m", "unittest"]
            if verbose:
                command.append("-v")
            if test_filter:
                command.append(test_filter)
            else:
                command.append("discover")
                command.append(test_dir)
                
        elif test_mode == "pytest":
            command = ["python", "-m", "pytest"]
            if verbose:
                command.append("-v")
            if fail_fast:
                command.append("-x")
            if show_coverage:
                command.extend(["--cov", test_dir])
            if test_filter:
                command.append(test_filter)
            else:
                command.append(test_dir)
                
        elif test_mode == "自定义":
            custom_command = self.customCmdEdit.text().strip()
            if not custom_command:
                QMessageBox.warning(self, "警告", "请输入自定义测试命令")
                return
                
            custom_command = custom_command.replace("{path}", test_dir)
            command = shlex.split(custom_command)
            
        # 清空输出区域并显示命令
        self.testOutputText.clear()
        command_str = " ".join(command)
        self.testOutputText.append(f"执行命令: {command_str}\n")
        self.testOutputText.append("-" * 80 + "\n")
        
        # 添加到历史记录
        self.testRunCount += 1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_item = f"测试 #{self.testRunCount} ({timestamp}): {command_str}"
        self.testHistoryList.insertItem(0, history_item)
        
        # 更新按钮状态
        self.runTestBtn.setEnabled(False)
        self.stopTestBtn.setEnabled(True)
        
        # 创建测试进程
        try:
            self.test_process = QProcess()
            self.test_process.readyReadStandardOutput.connect(self.onTestStdout)
            self.test_process.readyReadStandardError.connect(self.onTestStderr)
            self.test_process.finished.connect(self.onTestFinished)
            
            # 启动进程
            self.test_process.start(command[0], command[1:])
            
        except Exception as e:
            self.testOutputText.append(f"启动测试进程时出错: {str(e)}\n")
            self.resetTestButtons()
            
    def onTestStdout(self):
        """处理测试标准输出"""
        output = bytes(self.test_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.testOutputText.append(output)
        
    def onTestStderr(self):
        """处理测试标准错误输出"""
        output = bytes(self.test_process.readAllStandardError()).decode("utf-8", errors="replace")
        self.testOutputText.append(f'<span style="color:red">{output}</span>')
        
    def onTestFinished(self, exit_code, exit_status):
        """处理测试完成事件"""
        # 根据退出代码添加结果状态
        if exit_code == 0:
            self.testOutputText.append('\n<span style="color:green; font-weight:bold">测试完成: 所有测试通过</span>')
        else:
            self.testOutputText.append(f'\n<span style="color:red; font-weight:bold">测试完成: 存在失败测试 (退出代码: {exit_code})</span>')
        
        # 保存测试历史
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        test_dir = self.testDirEdit.text().strip()
        test_mode = self.testModeCombo.currentText()
        history_item = QListWidgetItem(f"{timestamp} - {test_mode} - {test_dir}")
        history_item.setData(Qt.UserRole, {
            'test_dir': test_dir,
            'test_mode': test_mode,
            'test_filter': self.testFilterEdit.text().strip(),
            'verbose': self.verboseCheck.isChecked(),
            'fail_fast': self.failFastCheck.isChecked(),
            'show_coverage': self.coverageCheck.isChecked(),
            'custom_command': self.customCmdEdit.text().strip() if test_mode == "自定义" else None
        })
        self.testHistoryList.insertItem(0, history_item)
        
        # 重置按钮状态
        self.resetTestButtons()
    
    def stopTests(self):
        """停止正在运行的测试"""
        if self.test_process and self.test_process.state() == QProcess.Running:
            self.test_process.terminate()
            # 给进程一些时间来终止
            if not self.test_process.waitForFinished(1000):
                self.test_process.kill()  # 如果无法正常终止，强制结束
                
        self.resetTestButtons()
        
    def resetTestButtons(self):
        """重置测试按钮状态"""
        self.runTestBtn.setEnabled(True)
        self.stopTestBtn.setEnabled(False)
        
    def loadTestHistory(self, item):
        """从历史记录加载测试"""
        history_text = item.text()
        command_match = re.search(r": (.+)$", history_text)
        if command_match:
            command = command_match.group(1)
            # 显示确认对话框
            reply = QMessageBox.question(
                self, 
                "重新运行测试", 
                f"是否要重新运行以下测试命令？\n\n{command}",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 将命令分解为列表
                command_list = shlex.split(command)
                
                # 清空输出并显示命令
                self.testOutputText.clear()
                self.testOutputText.append(f"执行命令: {command}\n")
                self.testOutputText.append("-" * 80 + "\n")
                
                # 更新按钮状态
                self.runTestBtn.setEnabled(False)
                self.stopTestBtn.setEnabled(True)
                
                # 启动测试进程
                try:
                    self.test_process = QProcess()
                    self.test_process.readyReadStandardOutput.connect(self.onTestStdout)
                    self.test_process.readyReadStandardError.connect(self.onTestStderr)
                    self.test_process.finished.connect(self.onTestFinished)
                    
                    # 启动进程
                    self.test_process.start(command_list[0], command_list[1:])
                    
                except Exception as e:
                    self.testOutputText.append(f"启动测试进程时出错: {str(e)}\n")
                    self.resetTestButtons()

    def setupNetworkTestTab(self):
        """设置网络测试标签页"""
        self.networkTestTab = QWidget()
        
        # 创建布局
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(3, 3, 3, 3)  # 减小边距
        mainLayout.setSpacing(3)  # 减小间距
        self.networkTestTab.setLayout(mainLayout)

        # 创建水平分割器 - 上面是抓包，下面是请求/响应
        mainSplitter = QSplitter(Qt.Vertical)
        mainSplitter.setChildrenCollapsible(False)  # 防止分割区域完全折叠
        
        # === 抓包部分 ===
        packetCaptureWidget = QWidget()
        packetCaptureLayout = QVBoxLayout(packetCaptureWidget)
        packetCaptureLayout.setContentsMargins(3, 3, 3, 3)
        
        # 抓包按钮区域
        packetButtonsLayout = QHBoxLayout()
        packetButtonsLayout.setSpacing(3)
        
        self.captureButton = QPushButton("开始抓包")
        self.captureButton.clicked.connect(self.togglePacketCapture)
        
        self.clearCaptureButton = QPushButton("清除抓包")
        self.clearCaptureButton.clicked.connect(self.clearPacketCapture)
        
        self.exportCaptureButton = QPushButton("导出抓包")
        self.exportCaptureButton.clicked.connect(self.exportPacketCapture)
        
        self.importCaptureButton = QPushButton("导入抓包")
        self.importCaptureButton.clicked.connect(self.importPacketCapture)
        
        packetButtonsLayout.addWidget(self.captureButton)
        packetButtonsLayout.addWidget(self.clearCaptureButton)
        packetButtonsLayout.addWidget(self.exportCaptureButton)
        packetButtonsLayout.addWidget(self.importCaptureButton)
        packetButtonsLayout.addStretch()
        
        packetCaptureLayout.addLayout(packetButtonsLayout)
        
        # 抓包列表
        self.packetListTable = QTableWidget()
        self.packetListTable.setColumnCount(5)
        self.packetListTable.setHorizontalHeaderLabels(["ID", "时间", "方法", "URL", "状态"])
        self.packetListTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.packetListTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.packetListTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.packetListTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.packetListTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.packetListTable.itemSelectionChanged.connect(self.onPacketSelected)
        self.packetListTable.setMaximumHeight(150)  # 限制高度
        
        packetCaptureLayout.addWidget(self.packetListTable)
        
        # === 请求/响应部分 ===
        reqResWidget = QWidget()
        reqResLayout = QHBoxLayout(reqResWidget)
        reqResLayout.setContentsMargins(3, 3, 3, 3)
        
        # 请求和响应的水平分割器
        reqResSplitter = QSplitter(Qt.Horizontal)
        reqResSplitter.setChildrenCollapsible(False)
        
        # 请求部分
        requestWidget = QWidget()
        requestLayout = QVBoxLayout(requestWidget)
        requestLayout.setContentsMargins(3, 3, 3, 3)
        requestLayout.setSpacing(3)
        
        # URL 输入和按钮行
        urlLayout = QHBoxLayout()
        urlLayout.setSpacing(3)
        
        urlLabel = QLabel("URL:")
        self.urlEdit = QLineEdit()
        self.urlEdit.setPlaceholderText("https://example.com/api")
        
        methodLabel = QLabel("方法:")
        self.methodCombo = QComboBox()
        self.methodCombo.addItems(["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        
        sendButton = QPushButton("发送")
        sendButton.clicked.connect(self.sendRequest)
        
        urlLayout.addWidget(urlLabel)
        urlLayout.addWidget(self.urlEdit, 1)  # URL输入框占据更多空间
        urlLayout.addWidget(methodLabel)
        urlLayout.addWidget(self.methodCombo)
        urlLayout.addWidget(sendButton)
        
        requestLayout.addLayout(urlLayout)
        
        # 请求头和请求体的标签页
        requestTabs = QTabWidget()
        requestTabs.setDocumentMode(True)  # 使标签页更紧凑
        
        # 请求头标签页
        headersTab = QWidget()
        headersLayout = QVBoxLayout(headersTab)
        headersLayout.setContentsMargins(3, 3, 3, 3)
        
        self.headersEdit = QTextEdit()
        self.headersEdit.setPlaceholderText("Content-Type: application/json\nAuthorization: Bearer token")
        
        headersLayout.addWidget(self.headersEdit)
        
        # 请求体标签页
        bodyTab = QWidget()
        bodyLayout = QVBoxLayout(bodyTab)
        bodyLayout.setContentsMargins(3, 3, 3, 3)
        
        bodyTypeLayout = QHBoxLayout()
        bodyTypeLayout.setSpacing(3)
        
        bodyTypeLabel = QLabel("内容类型:")
        self.bodyTypeCombo = QComboBox()
        self.bodyTypeCombo.addItems(["application/json", "application/xml", "application/x-www-form-urlencoded", "text/plain"])
        self.bodyTypeCombo.currentTextChanged.connect(self.updateBodyEditor)
        
        bodyTypeLayout.addWidget(bodyTypeLabel)
        bodyTypeLayout.addWidget(self.bodyTypeCombo)
        bodyTypeLayout.addStretch()
        
        self.bodyEdit = QTextEdit()
        self.bodyEdit.setPlaceholderText('{\n    "key": "value"\n}')
        
        bodyLayout.addLayout(bodyTypeLayout)
        bodyLayout.addWidget(self.bodyEdit)
        
        # 添加标签页
        requestTabs.addTab(headersTab, "请求头")
        requestTabs.addTab(bodyTab, "请求体")
        
        requestLayout.addWidget(requestTabs)
        
        # 响应部分
        responseWidget = QWidget()
        responseLayout = QVBoxLayout(responseWidget)
        responseLayout.setContentsMargins(3, 3, 3, 3)
        responseLayout.setSpacing(3)
        
        # 状态和耗时
        statusLayout = QHBoxLayout()
        statusLayout.setSpacing(3)
        
        self.statusLabel = QLabel("状态: -")
        self.timeLabel = QLabel("耗时: -")
        
        statusLayout.addWidget(self.statusLabel)
        statusLayout.addWidget(self.timeLabel)
        statusLayout.addStretch()
        
        responseLayout.addLayout(statusLayout)
        
        # 响应标签页
        responseTabs = QTabWidget()
        responseTabs.setDocumentMode(True)  # 使标签页更紧凑
        
        # 响应头标签页
        responseHeadersTab = QWidget()
        responseHeadersLayout = QVBoxLayout(responseHeadersTab)
        responseHeadersLayout.setContentsMargins(3, 3, 3, 3)
        
        self.responseHeadersText = QTextEdit()
        self.responseHeadersText.setReadOnly(True)
        
        responseHeadersLayout.addWidget(self.responseHeadersText)
        
        # 响应体标签页
        responseBodyTab = QWidget()
        responseBodyLayout = QVBoxLayout(responseBodyTab)
        responseBodyLayout.setContentsMargins(3, 3, 3, 3)
        
        self.responseBodyText = QTextEdit()
        self.responseBodyText.setReadOnly(True)
        
        responseBodyLayout.addWidget(self.responseBodyText)
        
        # 添加标签页
        responseTabs.addTab(responseHeadersTab, "响应头")
        responseTabs.addTab(responseBodyTab, "响应体")
        
        responseLayout.addWidget(responseTabs)
        
        # 添加请求和响应部件到分割器
        reqResSplitter.addWidget(requestWidget)
        reqResSplitter.addWidget(responseWidget)
        reqResSplitter.setSizes([500, 500])  # 初始大小均等
        
        reqResLayout.addWidget(reqResSplitter)
        
        # 添加到主分割器
        mainSplitter.addWidget(packetCaptureWidget)
        mainSplitter.addWidget(reqResWidget)
        mainSplitter.setSizes([150, 350])  # 初始分配更多空间给请求/响应部分
        
        mainLayout.addWidget(mainSplitter)
        
        return self.networkTestTab

    def togglePacketCapture(self):
        """切换抓包状态"""
        if self.captureButton.text() == "开始抓包":
            if self.packetCaptureManager.start_capture():
                self.captureButton.setText("停止抓包")
                self.statusBar().showMessage("抓包已启动", 3000)
        else:
            if self.packetCaptureManager.stop_capture():
                self.captureButton.setText("开始抓包")
                self.statusBar().showMessage("抓包已停止", 3000)

    def clearPacketCapture(self):
        """清除抓包数据"""
        if self.packetCaptureManager.clear_packets():
            self.packetListTable.setRowCount(0)
            self.statusBar().showMessage("抓包数据已清除", 3000)

    def exportPacketCapture(self):
        """导出抓包数据"""
        if not self.packetCaptureManager.get_packets():
            QMessageBox.information(self, "导出抓包", "没有可导出的抓包数据")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出抓包数据", "", "JSON 文件 (*.json)"
        )
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
                
            if self.packetCaptureManager.export_packets(file_path):
                self.statusBar().showMessage(f"抓包数据已导出到: {file_path}", 5000)
            else:
                QMessageBox.warning(self, "导出抓包", "导出抓包数据失败")

    def importPacketCapture(self):
        """导入抓包数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入抓包数据", "", "JSON 文件 (*.json)"
        )
        
        if file_path:
            if self.packetCaptureManager.import_packets(file_path):
                self.refreshPacketList()
                self.statusBar().showMessage(f"抓包数据已从 {file_path} 导入", 5000)
            else:
                QMessageBox.warning(self, "导入抓包", "导入抓包数据失败")

    def refreshPacketList(self):
        """刷新抓包列表"""
        self.packetListTable.setRowCount(0)
        
        packets = self.packetCaptureManager.get_packets()
        for packet in packets:
            row = self.packetListTable.rowCount()
            self.packetListTable.insertRow(row)
            
            # ID
            self.packetListTable.setItem(row, 0, QTableWidgetItem(str(packet['id'])))
            
            # 时间
            timestamp = packet['timestamp']
            if isinstance(timestamp, datetime.datetime):
                time_str = timestamp.strftime('%H:%M:%S')
            else:
                time_str = str(timestamp)
            self.packetListTable.setItem(row, 1, QTableWidgetItem(time_str))
            
            # 方法
            self.packetListTable.setItem(row, 2, QTableWidgetItem(packet['method']))
            
            # URL
            url_item = QTableWidgetItem(packet['url'])
            url_item.setToolTip(packet['url'])
            self.packetListTable.setItem(row, 3, url_item)
            
            # 状态
            if packet['response']:
                status = str(packet['response']['status_code'])
                status_item = QTableWidgetItem(status)
                
                # 设置状态码颜色
                if 200 <= packet['response']['status_code'] < 300:
                    status_item.setForeground(Qt.green)
                elif 300 <= packet['response']['status_code'] < 400:
                    status_item.setForeground(Qt.blue)
                elif 400 <= packet['response']['status_code'] < 500:
                    status_item.setForeground(Qt.red)
                elif 500 <= packet['response']['status_code'] < 600:
                    status_item.setForeground(Qt.darkRed)
                    
                self.packetListTable.setItem(row, 4, status_item)
            else:
                self.packetListTable.setItem(row, 4, QTableWidgetItem("等待响应"))
        
        # 调整列宽
        self.packetListTable.resizeColumnsToContents()
        self.packetListTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def onPacketCaptured(self, packet):
        """处理新捕获的数据包"""
        self.refreshPacketList()

    def onPacketSelected(self):
        """显示选中的数据包详情"""
        selected_items = self.packetListTable.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        packet_id = int(self.packetListTable.item(row, 0).text())
        
        packet = self.packetCaptureManager.get_packet(packet_id)
        if not packet:
            return
            
        # 填充请求详情
        self.urlEdit.setText(packet['url'])
        self.methodCombo.setCurrentText(packet['method'])
        
        # 请求头
        headers_text = ""
        for key, value in packet['headers'].items():
            headers_text += f"{key}: {value}\n"
        self.headersEdit.setText(headers_text)
        
        # 请求体
        if packet['body']:
            # 尝试检测内容类型
            content_type = None
            if 'headers' in packet and packet['headers']:
                for key, value in packet['headers'].items():
                    if key.lower() == 'content-type':
                        content_type = value
                        break
            
            if content_type:
                for i in range(self.bodyTypeCombo.count()):
                    if content_type in self.bodyTypeCombo.itemText(i):
                        self.bodyTypeCombo.setCurrentIndex(i)
                        break
            
            self.bodyEdit.setText(packet['body'])
        else:
            self.bodyEdit.clear()
        
        # 填充响应详情
        if packet['response']:
            # 状态和耗时
            self.statusLabel.setText(f"状态: {packet['response']['status_code']}")
            
            # 计算耗时
            if 'timestamp' in packet and 'timestamp' in packet['response']:
                delta = packet['response']['timestamp'] - packet['timestamp']
                ms = delta.total_seconds() * 1000
                self.timeLabel.setText(f"耗时: {ms:.0f} ms")
            else:
                self.timeLabel.setText("耗时: -")
            
            # 响应头
            headers_text = ""
            for key, value in packet['response']['headers'].items():
                headers_text += f"{key}: {value}\n"
            self.responseHeadersText.setText(headers_text)
            
            # 响应体
            if packet['response']['body']:
                self.responseBodyText.setText(packet['response']['body'])
            else:
                self.responseBodyText.clear()
        else:
            self.statusLabel.setText("状态: -")
            self.timeLabel.setText("耗时: -")
            self.responseHeadersText.clear()
            self.responseBodyText.clear()

    def updateBodyEditor(self, content_type):
        """根据内容类型更新请求体编辑器"""
        if "json" in content_type.lower():
            self.bodyEdit.setPlaceholderText('{\n    "key": "value"\n}')
        elif "xml" in content_type.lower():
            self.bodyEdit.setPlaceholderText('<root>\n    <item>value</item>\n</root>')
        elif "form" in content_type.lower():
            self.bodyEdit.setPlaceholderText('key1=value1&key2=value2')
        else:
            self.bodyEdit.setPlaceholderText('Enter request body here')

    def sendRequest(self):
        """发送网络请求"""
        url = self.urlEdit.text().strip()
        if not url:
            self.statusBar().showMessage("请输入URL", 3000)
            return
            
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'http://' + url
            self.urlEdit.setText(url)
    
        method = self.methodCombo.currentText()
        
        # 解析请求头
        headers = {}
        for line in self.headersEdit.toPlainText().strip().split('\n'):
            if line.strip():
                parts = line.split(':', 1)
                if len(parts) == 2:
                    headers[parts[0].strip()] = parts[1].strip()
        
        # 添加内容类型
        content_type = self.bodyTypeCombo.currentText()
        if content_type and 'content-type' not in map(str.lower, headers.keys()):
            headers['Content-Type'] = content_type
        
        # 请求体
        body = None
        if method in ['POST', 'PUT', 'PATCH']:
            body = self.bodyEdit.toPlainText()
        
        # 清空之前的响应
        self.statusLabel.setText("状态: -")
        self.timeLabel.setText("耗时: -")
        self.responseHeadersText.clear()
        self.responseBodyText.clear()
        
        # 捕获请求
        request_id = None
        if self.packetCaptureManager.is_capturing:
            request_id = self.packetCaptureManager.capture_request(url, method, headers, body)
        
        # 创建网络管理器
        if self.networkManager:
            self.networkManager.deleteLater()
        
        self.networkManager = NetworkManager()
        self.networkManager.requestFinished.connect(
            lambda response: self.handleNetworkResponse(response, request_id)
        )
        
        # 直接在当前线程发送请求而不使用QMetaObject
        self.networkManager.sendRequest(url, method, headers, body if body else "")
        
        self.statusBar().showMessage(f"正在发送 {method} 请求到 {url}", 3000)

    def handleNetworkResponse(self, response, request_id=None):
        """处理网络响应"""
        start_time = response.get('start_time', 0)
        end_time = response.get('end_time', 0)
        elapsed_ms = (end_time - start_time) * 1000 if start_time and end_time else 0
        
        status_code = response.get('status_code', 0)
        headers = response.get('headers', {})
        body = response.get('body', '')
        error = response.get('error', None)
        
        # 更新UI
        self.statusLabel.setText(f"状态: {status_code}")
        self.timeLabel.setText(f"耗时: {elapsed_ms:.0f} ms")
        
        # 显示响应头
        headers_text = ""
        for key, value in headers.items():
            headers_text += f"{key}: {value}\n"
        self.responseHeadersText.setText(headers_text)
        
        # 获取内容类型
        content_type = ""
        for key, value in headers.items():
            if key.lower() == 'content-type':
                content_type = value
                break
        
        # 处理响应体
        if body:
            # 使用ResponseProcessor异步处理响应体
            if self.responseProcessor:
                self.responseProcessor.wait()
                self.responseProcessor.deleteLater()
            
            self.responseProcessor = ResponseProcessor(body, content_type)
            self.responseProcessor.processingCompleted.connect(self.onResponseProcessed)
            self.responseProcessor.processingError.connect(self.onResponseProcessError)
            self.responseProcessor.start()
        else:
            self.responseBodyText.clear()
        
        # 捕获响应
        if request_id is not None and self.packetCaptureManager.is_capturing:
            self.packetCaptureManager.capture_response(
                request_id, status_code, headers, body, error
            )
        
        # 更新状态栏
        if error:
            self.statusBar().showMessage(f"请求错误: {error}", 5000)
        else:
            self.statusBar().showMessage(f"请求完成 (状态码: {status_code})", 3000)

    def updateSysInfo(self):
        """更新系统信息定时更新"""
        self.updateSystemInfo()

    def updateSystemInfoFallback(self, info):
        """系统信息的备用获取方法"""
        # Python信息
        info.append("<h3>Python环境</h3>")
        info.append(f"<p>Python版本: {platform.python_version()}</p>")
        info.append(f"<p>Python实现: {platform.python_implementation()}</p>")
        info.append(f"<p>Python编译器: {platform.python_compiler()}</p>")
        info.append(f"<p>Python路径: {sys.executable}</p>")
        
        # 操作系统信息
        info.append("<h3>操作系统</h3>")
        info.append(f"<p>系统: {platform.system()}</p>")
        info.append(f"<p>版本: {platform.version()}</p>")
        info.append(f"<p>架构: {platform.machine()}</p>")
        
        # MGit信息
        info.append("<h3>MGit应用</h3>")
        try:
            from src.utils.version import VERSION
            info.append(f"<p>版本: {VERSION}</p>")
        except ImportError:
            info.append("<p>版本: 未知</p>")
            
        # 路径信息
        info.append("<h3>路径信息</h3>")
        info.append(f"<p>工作目录: {os.getcwd()}</p>")
        
        # 检查plugin_manager是否存在
        if hasattr(self.plugin, 'plugin_manager') and self.plugin.plugin_manager is not None:
            info.append(f"<p>插件目录: {self.plugin.plugin_manager.plugin_dir}</p>")
            info.append(f"<p>用户插件目录: {self.plugin.plugin_manager.user_plugin_dir}</p>")
        else:
            info.append("<p>插件目录: 未知</p>")
            info.append("<p>用户插件目录: 未知</p>")
        
    def appendLog(self, log_entry):
        """处理新日志"""
        self.logText.append(log_entry)

    def get_event_listeners(self):
        """获取事件监听器"""
        return {
            'app_initialized': self.on_app_initialized
        }

    def on_app_initialized(self, app):
        """应用初始化完成后的处理"""
        # 这里可以添加一些初始化逻辑
        pass

    def get_view(self):
        if not self.widget:
            self.widget = QWidget()
            layout = QVBoxLayout(self.widget)
            layout.addWidget(self.tabWidget)
        return self.widget

    def enable(self):
        """启用插件"""
        super().enable()

    def disable(self):
        """禁用插件"""
        if self.window:
            self.window.close()
        return True
    
    def cleanup(self):
        """清理插件资源"""
        if self.window:
            self.window.close()
            self.window = None

    def clearResponse(self):
        """清除响应数据"""
        try:
            # 检查各个UI组件是否存在并有效，再进行操作
            if hasattr(self, 'statusLabel') and self.statusLabel is not None and not sip.isdeleted(self.statusLabel):
                self.statusLabel.setText("状态: -")
                
            if hasattr(self, 'timeLabel') and self.timeLabel is not None and not sip.isdeleted(self.timeLabel):
                self.timeLabel.setText("耗时: -")
                
            if hasattr(self, 'sizeLabel') and self.sizeLabel is not None and not sip.isdeleted(self.sizeLabel):
                self.sizeLabel.setText("大小: -")
                
            if hasattr(self, 'responseBodyEdit') and self.responseBodyEdit is not None and not sip.isdeleted(self.responseBodyEdit):
                self.responseBodyEdit.clear()
                
            if hasattr(self, 'responseHeadersEdit') and self.responseHeadersEdit is not None and not sip.isdeleted(self.responseHeadersEdit):
                self.responseHeadersEdit.clear()
                
            # 清除存储的二进制数据和内容类型
            if hasattr(self, 'binary_response_data'):
                self.binary_response_data = None
                
            if hasattr(self, 'content_type'):
                self.content_type = None
        except Exception as e:
            print(f"清除响应时出错: {str(e)}")

    def formatSize(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def updateBodyEditor(self, index):
        """根据选择的请求体类型更新编辑器"""
        if hasattr(self, 'bodyStack') and self.bodyStack is not None and not sip.isdeleted(self.bodyStack):
            self.bodyStack.setCurrentIndex(index)
        
    def updateResponseView(self, index):
        """根据选择的响应视图类型更新视图"""
        # 此方法不再需要，因为我们没有在UI中创建responseBodyStack组件
        pass
    
    def addRequestHeader(self):
        """添加请求头"""
        row = self.headersTable.rowCount()
        self.headersTable.insertRow(row)
        self.headersTable.setItem(row, 0, QTableWidgetItem(""))
        self.headersTable.setItem(row, 1, QTableWidgetItem(""))
        
    def removeRequestHeader(self):
        """删除选定的请求头"""
        selected_rows = set(index.row() for index in self.headersTable.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.headersTable.removeRow(row)
            
    def addFormItem(self):
        """添加表单字段"""
        row = self.formTable.rowCount()
        self.formTable.insertRow(row)
        self.formTable.setItem(row, 0, QTableWidgetItem(""))
        self.formTable.setItem(row, 1, QTableWidgetItem(""))
        
    def removeFormItem(self):
        """删除选定的表单字段"""
        selected_rows = set(index.row() for index in self.formTable.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.formTable.removeRow(row)
            
    def clearRequest(self):
        """清除当前请求"""
        try:
            # 检查每个UI组件是否有效
            if hasattr(self, 'urlEdit') and not sip.isdeleted(self.urlEdit):
                self.urlEdit.clear()
                
            if hasattr(self, 'headersTable') and not sip.isdeleted(self.headersTable):
                self.headersTable.setRowCount(0)
                
            if hasattr(self, 'bodyTypeCombo') and not sip.isdeleted(self.bodyTypeCombo):
                self.bodyTypeCombo.setCurrentIndex(0)
                
            if hasattr(self, 'jsonBodyEdit') and not sip.isdeleted(self.jsonBodyEdit):
                self.jsonBodyEdit.clear()
                
            if hasattr(self, 'formTable') and not sip.isdeleted(self.formTable):
                self.formTable.setRowCount(0)
                
            if hasattr(self, 'rawBodyEdit') and not sip.isdeleted(self.rawBodyEdit):
                self.rawBodyEdit.clear()
                
            # 安全地调用clearResponse
            try:
                if hasattr(self, 'clearResponse') and callable(self.clearResponse):
                    self.clearResponse()
            except Exception as e:
                print(f"clearRequest: 调用clearResponse时出错: {str(e)}")
        except Exception as e:
            print(f"clearRequest: 清除请求时出错: {str(e)}")

    def loadRequestFromHistory(self, item):
        """从历史记录列表加载请求"""
        # 这里仅根据URL和方法重新发送请求
        # 实际应用中可能需要保存完整的请求配置
        try:
            history_text = item.text()
            method_match = re.search(r'\[(.*?)\]', history_text)
            url_match = re.search(r'\] (.*?) \(', history_text)
            
            if method_match and url_match:
                method = method_match.group(1)
                url = url_match.group(1)
                
                # 询问用户是否要加载此请求
                reply = QMessageBox.question(
                    self, 
                    "加载请求", 
                    f"是否要重新加载以下请求？\n\n方法: {method}\nURL: {url}",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 设置URL和方法
                    self.urlEdit.setText(url)
                    index = self.methodCombo.findText(method)
                    if index >= 0:
                        self.methodCombo.setCurrentIndex(index)
                        
                    # 发送请求
                    self.sendRequest()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载请求时出错: {str(e)}")

    def findPluginManager(self):
        """尝试从多个可能的来源获取插件管理器"""
        # 首先尝试从插件对象获取
        if hasattr(self.plugin, 'plugin_manager') and self.plugin.plugin_manager is not None:
            return self.plugin.plugin_manager
            
        # 尝试从app对象获取
        if hasattr(self.plugin, 'app') and self.plugin.app is not None:
            app = self.plugin.app
            if hasattr(app, 'plugin_manager') and app.plugin_manager is not None:
                # 更新plugin对象的引用
                self.plugin.plugin_manager = app.plugin_manager
                print("开发者工具窗口: 从app获取到插件管理器")
                return app.plugin_manager
                
        # 尝试从全局导入获取
        try:
            # 这可能依赖于应用程序的具体实现
            from src.utils.plugin_manager import plugin_manager
            if plugin_manager:
                self.plugin.plugin_manager = plugin_manager
                print("开发者工具窗口: 从全局导入获取到插件管理器")
                return plugin_manager
        except ImportError:
            pass
            
        print("开发者工具窗口: 无法找到插件管理器")
        return None

    def loadHistoryFromCombo(self, index):
        """从下拉框加载历史请求"""
        if index <= 0:  # 跳过第一项 "选择历史请求..."
            return
            
        history_text = self.historyCombo.currentText()
        self.historyCombo.setCurrentIndex(0)  # 重置选择
        
        # 解析历史记录文本
        match = re.search(r'#\d+ \[(.*?)\] (.*?) \(', history_text)
        if match:
            method = match.group(1)
            url = match.group(2)
            
            # 设置URL和方法
            self.urlEdit.setText(url)
            index = self.methodCombo.findText(method)
            if index >= 0:
                self.methodCombo.setCurrentIndex(index)
                
            # 发送请求
            self.sendRequest()

    def clearRequestHistory(self):
        """清除请求历史记录"""
        self.historyList.clear()
        # 清空下拉框，保留第一个选择提示项
        while self.historyCombo.count() > 1:
            self.historyCombo.removeItem(1)
        self.requestHistoryCount = 0

    def addToRequestHistory(self, url, method):
        """添加请求到历史记录"""
        self.requestHistoryCount += 1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_item = f"#{self.requestHistoryCount} [{method}] {url} ({timestamp})"
        self.historyList.insertItem(0, history_item)
        # 添加到下拉框
        self.historyCombo.insertItem(1, history_item)  # 插入到选择提示项之后

    def exportRequestHistory(self):
        """导出请求历史到文件"""
        try:
            if self.historyList.count() == 0:
                QMessageBox.information(self, "导出历史", "没有可导出的请求历史")
                return
                
            # 获取保存文件路径
            export_path, _ = QFileDialog.getSaveFileName(
                self, "导出历史", "", "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if export_path:
                history_items = []
                for i in range(self.historyList.count()):
                    history_items.append(self.historyList.item(i).text())
                
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(history_items, f, ensure_ascii=False, indent=2)
                    
                QMessageBox.information(self, "导出成功", f"请求历史已导出到 {export_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出请求历史时出错: {str(e)}")

    def saveRequest(self):
        """保存当前请求设置为一个命名请求"""
        try:
            name, ok = QInputDialog.getText(self, "保存请求", "请求名称:")
            if ok and name:
                request = {
                    'name': name,
                    'url': self.urlEdit.text(),
                    'method': self.methodCombo.currentText(),
                    'headers': self.getTableContents(self.headersTable),
                    'body': self.getCurrentBodyContent(),
                    'timeout': self.timeoutSpinner.value(),
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.historyList.addItem(f"{request['method']} - {name}")
                InfoBar.success(
                    title="保存成功",
                    content=f"请求 '{name}' 已保存到历史记录",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
        except Exception as e:
            self.showError(f"保存请求时出错: {str(e)}")

    def showError(self, message):
        """显示错误信息"""
        InfoBar.error(
            title="错误",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
    
    def getTableContents(self, table):
        """获取表格内容为字典格式"""
        result = {}
        for row in range(table.rowCount()):
            key = table.item(row, 0).text().strip()
            value = table.item(row, 1).text().strip()
            if key:
                result[key] = value
        return result
    
    def getCurrentBodyContent(self):
        """获取当前请求体内容"""
        body_type_index = self.bodyTypeCombo.currentIndex()
        
        if body_type_index == 0:  # 无
            return ""
        elif body_type_index == 1:  # JSON
            return self.jsonBodyEdit.toPlainText().strip()
        elif body_type_index == 2:  # 表单数据
            result = {}
            for row in range(self.formTable.rowCount()):
                key = self.formTable.item(row, 0).text().strip()
                value = self.formTable.item(row, 1).text().strip()
                if key:
                    result[key] = value
            return result
        elif body_type_index == 3:  # 原始文本
            return self.rawBodyEdit.toPlainText().strip()
        
        return ""

    def addResponseToHistory(self, status_code, response_data):
        """将响应添加到历史记录"""
        try:
            # 获取当前时间作为时间戳
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 获取当前URL和请求方法
            url = self.urlEdit.text()
            method = self.methodCombo.currentText()
            
            # 将响应大小格式化为易读格式
            size = self.formatSize(len(response_data))
            
            # 创建历史记录项
            history_item = f"[{method}] {url} - {status_code} ({size}) - {timestamp}"
            
            # 将响应添加到响应历史列表中（如果存在该列表）
            if hasattr(self, 'responseHistoryList') and self.responseHistoryList:
                # 在列表顶部插入新的历史记录
                self.responseHistoryList.insertItem(0, history_item)
                
                # 保存响应数据供以后使用
                item = self.responseHistoryList.item(0)
                if item:
                    # 使用setData存储响应数据，方便后续查看
                    item.setData(Qt.UserRole, {
                        'url': url,
                        'method': method,
                        'status_code': status_code,
                        'response_data': response_data,
                        'timestamp': timestamp
                    })
        except Exception as e:
            print(f"添加响应到历史记录时出错: {str(e)}")

    def loadResponseFromHistory(self, item):
        """从响应历史记录加载响应"""
        try:
            # 获取与列表项关联的数据
            data = item.data(Qt.UserRole)
            if not data:
                return
                
            # 显示响应数据在响应区域
            if 'response_data' in data:
                response_data = data['response_data']
                
                # 尝试将响应数据解码为文本
                try:
                    response_text = response_data.decode('utf-8', errors='replace')
                    
                    # 使用ResponseProcessor处理响应
                    self.response_processor = ResponseProcessor(response_text, None)
                    self.response_processor.processingCompleted.connect(self.onResponseProcessed)
                    self.response_processor.processingError.connect(self.onResponseProcessError)
                    self.response_processor.start()
                    
                    # 更新状态信息
                    if 'status_code' in data:
                        self.statusLabel.setText(f"状态: {data['status_code']}")
                    if 'url' in data and 'method' in data:
                        InfoBar.info(
                            title="加载历史响应",
                            content=f"已加载 [{data['method']}] {data['url']} 的响应",
                            parent=self,
                            position=InfoBarPosition.TOP,
                            duration=2000
                        )
                except Exception as e:
                    # 处理二进制数据或解码失败的情况
                    size = len(response_data)
                    InfoBar.warning(
                        title="二进制数据",
                        content=f"加载的响应为二进制数据，大小：{self.formatSize(size)}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
        except Exception as e:
            InfoBar.error(
                title="加载历史响应失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def clearHistory(self):
        """清除所有历史记录"""
        # 询问用户是否确定清除所有历史
        reply = QMessageBox.question(
            self, 
            "清除历史", 
            "确定要清除所有请求和响应历史记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清除请求历史
            self.clearRequestHistory()
            
            # 清除响应历史
            if hasattr(self, 'responseHistoryList') and self.responseHistoryList:
                self.responseHistoryList.clear()
                
            InfoBar.success(
                title="历史已清除",
                content="所有历史记录已清除",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
    
    def exportHistory(self):
        """导出所有历史记录"""
        try:
            # 检查是否有历史记录
            if (self.historyList.count() == 0 and 
                (not hasattr(self, 'responseHistoryList') or self.responseHistoryList.count() == 0)):
                InfoBar.information(
                    title="导出历史",
                    content="没有可导出的历史记录",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                return
                
            # 获取保存文件路径
            export_path, _ = QFileDialog.getSaveFileName(
                self, "导出历史", "", "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if export_path:
                export_data = {
                    "requests": [],
                    "responses": []
                }
                
                # 导出请求历史
                for i in range(self.historyList.count()):
                    export_data["requests"].append(self.historyList.item(i).text())
                
                # 导出响应历史
                if hasattr(self, 'responseHistoryList') and self.responseHistoryList:
                    for i in range(self.responseHistoryList.count()):
                        item = self.responseHistoryList.item(i)
                        export_data["responses"].append({
                            "text": item.text(),
                            "data": str(item.data(Qt.UserRole)) if item.data(Qt.UserRole) else None
                        })
                
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                    
                InfoBar.success(
                    title="导出成功",
                    content=f"历史记录已导出到 {export_path}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
        except Exception as e:
            InfoBar.error(
                title="导出失败",
                content=f"导出历史记录时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def loadHistoryRequest(self, item):
        """从历史记录列表加载请求"""
        # 这里仅根据URL和方法重新发送请求
        try:
            history_text = item.text()
            method_match = re.search(r'\[(.*?)\]', history_text)
            url_match = re.search(r'\] (.*?) \(', history_text)
            
            if method_match and url_match:
                method = method_match.group(1)
                url = url_match.group(1)
                
                # 询问用户是否要加载此请求
                reply = QMessageBox.question(
                    self, 
                    "加载请求", 
                    f"是否要重新加载以下请求？\n\n方法: {method}\nURL: {url}",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 设置URL和方法
                    self.urlEdit.setText(url)
                    index = self.methodCombo.findText(method)
                    if index >= 0:
                        self.methodCombo.setCurrentIndex(index)
                        
                    # 发送请求
                    self.sendRequest()
        except Exception as e:
            InfoBar.error(
                title="加载请求失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def addCommonHeaders(self):
        """添加常用的HTTP请求头"""
        common_headers = [
            ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"),
            ("Accept", "application/json, text/plain, */*"),
            ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8"),
            ("Content-Type", "application/json"),
            ("Connection", "keep-alive")
        ]
        
        # 询问用户是否要添加这些常用头
        msg = "是否要添加以下常用HTTP头部？\n\n"
        for key, value in common_headers:
            msg += f"• {key}: {value}\n"
            
        reply = QMessageBox.question(
            self, 
            "添加常用HTTP头部", 
            msg,
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清除现有头部
            current_rows = self.headersTable.rowCount()
            if current_rows > 0:
                reply = QMessageBox.question(
                    self,
                    "清除现有头部",
                    "是否要清除现有头部信息？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.headersTable.setRowCount(0)
                    current_rows = 0
            
            # 添加新头部
            for i, (key, value) in enumerate(common_headers):
                row = current_rows + i
                self.headersTable.insertRow(row)
                self.headersTable.setItem(row, 0, QTableWidgetItem(key))
                self.headersTable.setItem(row, 1, QTableWidgetItem(value))
                
            InfoBar.success(
                title="添加成功",
                content="已添加常用HTTP头部",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )

    def formatResponse(self, format_type):
        """格式化响应内容"""
        try:
            # 获取当前响应文本
            response_text = self.responseBodyEdit.toPlainText()
            if not response_text:
                InfoBar.warning(
                    title="无响应内容",
                    content="没有可格式化的响应内容",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                return
            
            formatted_text = ""
            
            # 根据不同类型格式化
            if format_type == "json":
                try:
                    # 解析JSON并格式化输出
                    parsed_json = json.loads(response_text)
                    formatted_text = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                except json.JSONDecodeError as e:
                    InfoBar.error(
                        title="JSON格式错误",
                        content=f"无法解析JSON: {str(e)}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                    return
                    
            elif format_type == "xml":
                try:
                    from xml.dom.minidom import parseString
                    formatted_text = parseString(response_text).toprettyxml(indent="  ")
                except Exception as e:
                    InfoBar.error(
                        title="XML格式错误",
                        content=f"无法解析XML: {str(e)}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                    return
                    
            elif format_type == "html":
                try:
                    # 尝试使用BeautifulSoup美化HTML
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response_text, 'html.parser')
                        formatted_text = soup.prettify()
                    except ImportError:
                        # 如果没有BeautifulSoup，尝试简单格式化
                        InfoBar.warning(
                            title="缺少依赖",
                            content="未安装BeautifulSoup，将使用简单格式化",
                            parent=self,
                            position=InfoBarPosition.TOP,
                            duration=2000
                        )
                        formatted_text = response_text
                except Exception as e:
                    InfoBar.error(
                        title="HTML格式错误",
                        content=f"格式化HTML时出错: {str(e)}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                    return
            
            # 更新响应显示
            if formatted_text:
                self.responseBodyEdit.setPlainText(formatted_text)
                InfoBar.success(
                    title="格式化成功",
                    content=f"已成功格式化为{format_type.upper()}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                
        except Exception as e:
            InfoBar.error(
                title="格式化错误",
                content=f"格式化响应时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def copyResponseToClipboard(self):
        """复制响应内容到剪贴板"""
        try:
            # 获取当前响应文本
            response_text = self.responseBodyEdit.toPlainText()
            if not response_text:
                InfoBar.warning(
                    title="无响应内容",
                    content="没有可复制的响应内容",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                return
                
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(response_text)
            
            InfoBar.success(
                title="复制成功",
                content="响应内容已复制到剪贴板",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title="复制错误",
                content=f"复制响应时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def saveResponseToFile(self):
        """保存响应内容到文件"""
        try:
            # 检查是否有二进制数据需要保存
            has_binary_data = hasattr(self, 'binary_response_data') and self.binary_response_data
            
            # 如果是文本数据，获取当前响应文本
            if not has_binary_data:
                response_text = ""
                if hasattr(self, 'responseBodyEdit') and self.responseBodyEdit is not None and not sip.isdeleted(self.responseBodyEdit):
                    response_text = self.responseBodyEdit.toPlainText()
                    
                if not response_text:
                    InfoBar.warning(
                        title="无响应内容",
                        content="没有可保存的响应内容",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=2000
                    )
                    return
            
            # 构建文件过滤器，根据内容类型提供适当的过滤器
            file_filter = "所有文件 (*)"
            default_suffix = ""
            
            if has_binary_data and hasattr(self, 'content_type') and self.content_type:
                if "image/jpeg" in self.content_type:
                    file_filter = "JPEG图像 (*.jpg *.jpeg);;所有文件 (*)"
                    default_suffix = ".jpg"
                elif "image/png" in self.content_type:
                    file_filter = "PNG图像 (*.png);;所有文件 (*)"
                    default_suffix = ".png"
                elif "image/gif" in self.content_type:
                    file_filter = "GIF图像 (*.gif);;所有文件 (*)"
                    default_suffix = ".gif"
                elif "application/pdf" in self.content_type:
                    file_filter = "PDF文档 (*.pdf);;所有文件 (*)"
                    default_suffix = ".pdf"
                elif "audio/" in self.content_type:
                    file_filter = "音频文件 (*.mp3 *.wav *.ogg);;所有文件 (*)"
                    default_suffix = ".mp3"
                elif "video/" in self.content_type:
                    file_filter = "视频文件 (*.mp4 *.avi *.mkv);;所有文件 (*)"
                    default_suffix = ".mp4"
                elif "application/zip" in self.content_type:
                    file_filter = "ZIP压缩文件 (*.zip);;所有文件 (*)"
                    default_suffix = ".zip"
                elif "application/json" in self.content_type:
                    file_filter = "JSON文件 (*.json);;所有文件 (*)"
                    default_suffix = ".json"
                elif "application/xml" in self.content_type or "text/xml" in self.content_type:
                    file_filter = "XML文件 (*.xml);;所有文件 (*)"
                    default_suffix = ".xml"
                elif "text/html" in self.content_type:
                    file_filter = "HTML文件 (*.html);;所有文件 (*)"
                    default_suffix = ".html"
                elif "text/plain" in self.content_type:
                    file_filter = "文本文件 (*.txt);;所有文件 (*)"
                    default_suffix = ".txt"
            elif not has_binary_data:
                # 文本响应的默认过滤器
                file_filter = "文本文件 (*.txt);;JSON文件 (*.json);;XML文件 (*.xml);;HTML文件 (*.html);;所有文件 (*)"
                
            # 获取保存文件路径
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "保存响应内容",
                f"response{default_suffix}",  # 默认文件名
                file_filter
            )
            
            if file_path:
                # 确保文件有正确的扩展名
                if default_suffix and not file_path.endswith(default_suffix) and "所有文件" not in selected_filter:
                    file_path += default_suffix
                
                # 根据数据类型使用不同的写入模式
                if has_binary_data:
                    with open(file_path, 'wb') as f:
                        f.write(self.binary_response_data)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    
                InfoBar.success(
                    title="保存成功",
                    content=f"响应内容已保存到 {file_path}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
        except Exception as e:
            InfoBar.error(
                title="保存错误",
                content=f"保存响应时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def stopRequest(self):
        """停止当前网络请求"""
        try:
            if self.currentReply and self.currentReply.isRunning():
                # 中止请求
                self.currentReply.abort()
                
                # 显示提示
                InfoBar.info(
                    title="请求已停止",
                    content="网络请求已被用户手动停止",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
                
            # 恢复UI状态
            if hasattr(self, 'sendButton') and self.sendButton is not None and not sip.isdeleted(self.sendButton):
                self.sendButton.setEnabled(True)
                self.sendButton.setText("发送请求")
                
            if hasattr(self, 'stopButton') and self.stopButton is not None and not sip.isdeleted(self.stopButton):
                self.stopButton.setEnabled(False)
                
            if hasattr(self, 'requestProgressBar') and self.requestProgressBar is not None and not sip.isdeleted(self.requestProgressBar):
                self.requestProgressBar.setVisible(False)
                
        except Exception as e:
            InfoBar.error(
                title="停止请求错误",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def onResponseProcessed(self, processed_data):
        """处理响应格式化完成的结果"""
        raw_text, formatted_text = processed_data
        
        # 更新响应体显示
        self.responseBodyText.setText(formatted_text)
    
    def onResponseProcessError(self, error_message):
        """处理响应处理过程中的错误"""
        self.responseBodyText.setText(f"格式化响应时出错:\n{error_message}")
        self.statusBar().showMessage(f"响应格式化错误: {error_message}", 3000)

    def statusBar(self):
        """自定义状态栏方法，模拟QMainWindow.statusBar()方法"""
        class StatusBarWrapper:
            def __init__(self, label):
                self.label = label
                self.message_timer = QTimer()
                self.message_timer.setSingleShot(True)
                self.message_timer.timeout.connect(self.clearMessage)
                
            def showMessage(self, message, timeout=0):
                self.label.setText(message)
                if timeout > 0:
                    self.message_timer.start(timeout)
                    
            def clearMessage(self):
                self.label.clear()
        
        return StatusBarWrapper(self.statusLabel)

class DeveloperToolsPlugin(PluginBase):
    """开发者工具插件类"""
    
    def __init__(self):
        super().__init__()
        self.view = None
        self.app = None
        self.name = "开发者工具"
        self.version = "1.0.0"
        self.author = "MGit Team"
        self.description = "为MGit添加开发者工具功能"
        self.window = None
        self.plugin_manager = None
        
    def get_event_listeners(self):
        """获取事件监听器"""
        return {
            'app_initialized': self.on_app_initialized
        }
        
    def on_app_initialized(self, app):
        """应用程序初始化完成时的回调"""
        self.app = app
        # 获取并保存插件管理器引用
        if hasattr(app, 'plugin_manager'):
            self.plugin_manager = app.plugin_manager
            print(f"开发者工具: 已获取插件管理器，已加载 {len(self.plugin_manager.plugins) if hasattr(self.plugin_manager, 'plugins') else 0} 个插件")
            
            # 如果窗口已经创建，更新窗口的插件管理器引用
            if self.window:
                self.window.plugin.plugin_manager = self.plugin_manager
                print("开发者工具: 已更新窗口插件管理器引用")
    
    def get_view(self):
        """获取视图"""
        if not self.view:
            # 延迟创建窗口，以确保app_initialized已经被调用
            self.window = DeveloperToolsWindow(self)
            self.view = {
                'name': '开发者工具',
                'icon': FluentIcon.DEVELOPER_TOOLS,
                'widget': self.window
            }
        return self.view
        
    def open_dev_tools(self):
        """打开开发者工具窗口"""
        if not self.window:
            self.window = DeveloperToolsWindow(self)
            
            # 如果已经获取了插件管理器，确保传递给窗口
            if self.plugin_manager:
                self.window.plugin.plugin_manager = self.plugin_manager
                print("开发者工具: 窗口创建时注入插件管理器")
        
        if self.window.isHidden():
            self.window.show()
        else:
            self.window.activateWindow()
            self.window.raise_()
            
        # 强制刷新插件表格 
        self.window.updatePluginsTable()
        return self.window
        
    def enable(self):
        """启用插件"""
        return True
        
    def disable(self):
        """禁用插件"""
        if self.window:
            self.window.close()
        return True
    
    def cleanup(self):
        """清理插件资源"""
        if self.window:
            self.window.close()
            self.window = None
            
# MGit插件系统需要一个名为Plugin的类
class Plugin(DeveloperToolsPlugin):
    """MGit插件入口类"""
    def __init__(self):
        super().__init__()
        # plugin_manager会由主程序调用set_plugin_manager方法设置
        
    def set_plugin_manager(self, plugin_manager):
        """外部设置插件管理器方法，由主程序调用"""
        self.plugin_manager = plugin_manager
        # 使实例化的窗口也能获取到插件管理器
        if self.window:
            self.window.plugin.plugin_manager = plugin_manager
            print("开发者工具: Plugin类外部设置了插件管理器，已更新窗口引用")

class ResponseProcessor(QThread):
    """响应处理线程，用于处理大型响应数据而不阻塞UI"""
    processingCompleted = pyqtSignal(tuple)  # 发送包含 (raw_text, formatted_text) 的元组
    processingError = pyqtSignal(str)        # 发送错误消息
    
    def __init__(self, response_data, content_type=None, parent=None):
        super().__init__(parent)
        self.response_data = response_data
        self.content_type = content_type
        
    def run(self):
        """执行响应处理"""
        try:
            # 默认情况下，原始文本和格式化文本相同
            raw_text = self.response_data
            formatted_text = self.response_data
            
            # 根据内容类型处理数据
            if self.content_type:
                content_type_lower = self.content_type.lower()
                
                # 处理JSON格式
                if 'json' in content_type_lower or self._looks_like_json(raw_text):
                    try:
                        # 尝试解析并格式化JSON
                        parsed_json = json.loads(raw_text)
                        formatted_text = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                    except json.JSONDecodeError as e:
                        # JSON解析失败，报告错误但仍使用原始数据
                        formatted_text = f"JSON解析错误 (使用原始数据显示):\n{str(e)}\n\n{raw_text}"
                
                # 处理XML格式
                elif 'xml' in content_type_lower or self._looks_like_xml(raw_text):
                    try:
                        from xml.dom.minidom import parseString
                        formatted_text = parseString(raw_text).toprettyxml(indent="  ")
                    except Exception as e:
                        formatted_text = f"XML格式化错误 (使用原始数据显示):\n{str(e)}\n\n{raw_text}"
                
                # 处理HTML格式
                elif 'html' in content_type_lower or self._looks_like_html(raw_text):
                    try:
                        # 如果有BeautifulSoup，使用它来格式化HTML
                        try:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(raw_text, 'html.parser')
                            formatted_text = soup.prettify()
                        except ImportError:
                            # 如果没有BeautifulSoup，尝试使用XML解析器
                            from xml.dom.minidom import parseString
                            formatted_text = parseString(raw_text).toprettyxml(indent="  ")
                    except Exception as e:
                        formatted_text = f"HTML格式化错误 (使用原始数据显示):\n{str(e)}\n\n{raw_text}"
            
            # 如果没有内容类型，尝试根据内容自动检测并格式化
            else:
                # 尝试按JSON处理
                if self._looks_like_json(raw_text):
                    try:
                        parsed_json = json.loads(raw_text)
                        formatted_text = json.dumps(parsed_json, indent=4, ensure_ascii=False)
                    except:
                        pass
                # 尝试按XML处理
                elif self._looks_like_xml(raw_text):
                    try:
                        from xml.dom.minidom import parseString
                        formatted_text = parseString(raw_text).toprettyxml(indent="  ")
                    except:
                        pass
                # 尝试按HTML处理
                elif self._looks_like_html(raw_text):
                    try:
                        try:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(raw_text, 'html.parser')
                            formatted_text = soup.prettify()
                        except ImportError:
                            from xml.dom.minidom import parseString
                            formatted_text = parseString(raw_text).toprettyxml(indent="  ")
                    except:
                        pass
            
            # 发送处理完成的信号
            self.processingCompleted.emit((raw_text, formatted_text))
            
        except Exception as e:
            # 处理过程中的任何异常
            self.processingError.emit(f"处理响应时出错: {str(e)}")
    
    def _looks_like_json(self, text):
        """检查文本是否像JSON格式"""
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))
    
    def _looks_like_xml(self, text):
        """检查文本是否像XML格式"""
        text = text.strip()
        return text.startswith('<?xml') or \
               (text.startswith('<') and text.endswith('>') and '</' in text)
    
    def _looks_like_html(self, text):
        """检查文本是否像HTML格式"""
        text = text.lower().strip()
        return text.startswith('<!doctype html') or \
               text.startswith('<html') or \
               ('<html' in text and '</html>' in text) or \
               ('<head' in text and '</body>' in text)

class PacketCaptureManager(QObject):
    """网络数据包捕获管理器"""
    
    packetCaptured = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_capturing = False
        self.packets = []
        self.next_id = 1
        
    def start_capture(self):
        """开始捕获网络数据包"""
        self.is_capturing = True
        return True
        
    def stop_capture(self):
        """停止捕获网络数据包"""
        self.is_capturing = False
        return True
        
    def clear_packets(self):
        """清除所有捕获的数据包"""
        self.packets = []
        self.next_id = 1
        return True
        
    def capture_request(self, url, method, headers, body=None):
        """捕获请求数据"""
        if not self.is_capturing:
            return None
            
        packet_id = self.next_id
        self.next_id += 1
        
        packet = {
            'id': packet_id,
            'timestamp': datetime.datetime.now(),
            'url': url,
            'method': method,
            'headers': headers,
            'body': body,
            'response': None
        }
        
        self.packets.append(packet)
        self.packetCaptured.emit(packet)
        
        return packet_id
        
    def capture_response(self, request_id, status_code, headers, body=None, error=None):
        """捕获响应数据"""
        if not self.is_capturing:
            return False
            
        for packet in self.packets:
            if packet['id'] == request_id:
                packet['response'] = {
                    'timestamp': datetime.datetime.now(),
                    'status_code': status_code,
                    'headers': headers,
                    'body': body,
                    'error': error
                }
                self.packetCaptured.emit(packet)
                return True
                
        return False
        
    def get_packets(self):
        """获取所有捕获的数据包"""
        return self.packets
        
    def get_packet(self, packet_id):
        """根据ID获取特定的数据包"""
        for packet in self.packets:
            if packet['id'] == packet_id:
                return packet
        return None
        
    def export_packets(self, file_path):
        """导出捕获的数据包到文件"""
        try:
            # 转换数据包为可序列化的格式
            serializable_packets = []
            
            for packet in self.packets:
                serializable_packet = {
                    'id': packet['id'],
                    'timestamp': packet['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'url': packet['url'],
                    'method': packet['method'],
                    'headers': packet['headers'],
                    'body': packet['body'],
                    'response': None
                }
                
                if packet['response']:
                    serializable_packet['response'] = {
                        'timestamp': packet['response']['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f'),
                        'status_code': packet['response']['status_code'],
                        'headers': packet['response']['headers'],
                        'body': packet['response']['body'],
                        'error': packet['response']['error']
                    }
                    
                serializable_packets.append(serializable_packet)
                
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_packets, f, indent=2, ensure_ascii=False)
                
            return True
        except Exception as e:
            logging.error(f"导出抓包数据失败: {str(e)}")
            return False
            
    def import_packets(self, file_path):
        """从文件导入捕获的数据包"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                serialized_packets = json.load(f)
                
            self.packets = []
            max_id = 0
            
            for serialized_packet in serialized_packets:
                packet = {
                    'id': serialized_packet['id'],
                    'timestamp': datetime.datetime.strptime(serialized_packet['timestamp'], '%Y-%m-%d %H:%M:%S.%f'),
                    'url': serialized_packet['url'],
                    'method': serialized_packet['method'],
                    'headers': serialized_packet['headers'],
                    'body': serialized_packet['body'],
                    'response': None
                }
                
                if serialized_packet['response']:
                    packet['response'] = {
                        'timestamp': datetime.datetime.strptime(serialized_packet['response']['timestamp'], '%Y-%m-%d %H:%M:%S.%f'),
                        'status_code': serialized_packet['response']['status_code'],
                        'headers': serialized_packet['response']['headers'],
                        'body': serialized_packet['response']['body'],
                        'error': serialized_packet['response']['error']
                    }
                    
                self.packets.append(packet)
                max_id = max(max_id, packet['id'])
                
            self.next_id = max_id + 1
            return True
        except Exception as e:
            logging.error(f"导入抓包数据失败: {str(e)}")
            return False

class NetworkManager(QObject):
    """异步网络请求管理器"""
    
    requestFinished = pyqtSignal(dict)
    requestError = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = None
        self.current_reply = None
        
    def sendRequest(self, url, method, headers, body):
        """发送网络请求"""
        try:
            # 清理之前的管理器
            if self.network_manager:
                self.network_manager.deleteLater()
                
            # 创建新的管理器
            self.network_manager = QNetworkAccessManager()
            self.network_manager.finished.connect(self._handleResponse)
            
            # 创建请求对象
            request = QNetworkRequest(QUrl(url))
            
            # 添加请求头
            for key, value in headers.items():
                request.setRawHeader(key.encode(), value.encode())
                
            # 记录开始时间
            self.start_time = time.time()
            
            # 发送请求
            body_data = QByteArray(body.encode()) if body else QByteArray()
            
            if method == "GET":
                self.current_reply = self.network_manager.get(request)
            elif method == "POST":
                self.current_reply = self.network_manager.post(request, body_data)
            elif method == "PUT":
                self.current_reply = self.network_manager.put(request, body_data)
            elif method == "DELETE":
                self.current_reply = self.network_manager.deleteResource(request)
            elif method == "HEAD":
                self.current_reply = self.network_manager.head(request)
            elif method == "OPTIONS":
                self.current_reply = self.network_manager.sendCustomRequest(request, b"OPTIONS")
            elif method == "PATCH":
                self.current_reply = self.network_manager.sendCustomRequest(request, b"PATCH", body_data)
            else:
                self.requestError.emit(f"不支持的HTTP方法: {method}")
                return
                
            # 连接错误信号
            self.current_reply.error.connect(self._handleError)
            
        except Exception as e:
            self.requestError.emit(f"发送请求失败: {str(e)}")
            
    def _handleResponse(self, reply):
        """处理网络响应"""
        try:
            # 记录结束时间
            end_time = time.time()
            
            # 获取状态码
            status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
            if status_code is None:
                status_code = 0
                
            # 读取响应头
            headers = {}
            for header in reply.rawHeaderList():
                header_name = bytes(header).decode()
                header_value = bytes(reply.rawHeader(header)).decode()
                headers[header_name] = header_value
                
            # 读取响应体
            body = reply.readAll().data().decode(errors='replace')
            
            # 处理错误
            error = None
            if reply.error() != QNetworkReply.NoError:
                error = reply.errorString()
                
            # 构建响应数据
            response = {
                'start_time': self.start_time,
                'end_time': end_time,
                'status_code': status_code,
                'headers': headers,
                'body': body,
                'error': error
            }
            
            # 发送完成信号
            self.requestFinished.emit(response)
            
            # 清理
            reply.deleteLater()
            self.current_reply = None
            
        except Exception as e:
            self.requestError.emit(f"处理响应失败: {str(e)}")
            
    def _handleError(self, error_code):
        """处理网络错误"""
        if self.current_reply:
            error_msg = self.current_reply.errorString()
            self.requestError.emit(f"网络错误: {error_msg} (代码: {error_code})")
            
    def abort(self):
        """中止当前请求"""
        if self.current_reply and not self.current_reply.isFinished():
            self.current_reply.abort()
            self.current_reply = None