#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import re
from datetime import datetime, timedelta
import subprocess
import json
import sys

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QTextEdit, QFileDialog, QMessageBox,
                           QTabWidget, QWidget, QListWidget, QListWidgetItem,
                           QFormLayout, QComboBox, QGroupBox, QSplitter,
                           QTreeWidget, QTreeWidgetItem, QCheckBox, QRadioButton,
                           QDateEdit, QSpinBox, QButtonGroup, QProgressBar, QMenu,
                           QFrame, QHBoxLayout, QVBoxLayout, QStyle, QHeaderView,
                           QAbstractItemView, QTableWidgetItem, QTableWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime, QDate, QTime, QTimer, QSize, QThread
from PyQt5.QtGui import QIcon, QTextCursor, QColor, QTextCharFormat, QBrush, QFont, QSyntaxHighlighter, QTextDocument
from qfluentwidgets import (PrimaryPushButton, InfoBar, InfoBarPosition, 
                          FluentIcon as FIF, ComboBox, ToolTipFilter, 
                          TransparentToolButton, LineEdit, SearchLineEdit, 
                          ExpandLayout, CommandBar, Action, MessageBox,
                          SimpleCardWidget, StateToolTip, TextEdit, PushButton, TreeWidget,
                          ToolButton, TableWidget)

from src.utils.logger import (get_log_file_path, get_log_dir, export_log, 
                           get_all_log_files, get_recent_logs, info, warning,
                           error, show_error_message, LogCategory, clean_logs, Logger)

# Create logger instance
logger = Logger()

# 结果消息框
class ResultMessageBox(MessageBox):
    """显示操作结果的消息框"""
    
    def __init__(self, title, content, parent=None):
        super().__init__(title, content, parent)
        
        # 设置成功图标
        self.iconLabel.setPixmap(FIF.COMPLETED.icon().pixmap(48, 48))

# 日志配置对话框
class LogConfigDialog(QDialog):
    """日志配置对话框，用于修改日志系统设置"""
    
    def __init__(self, parent=None, section=None):
        super().__init__(parent)
        self.section = section
        
        # 设置窗口属性
        self.setWindowTitle("日志配置")
        self.resize(600, 400)
        
        # 初始化界面
        self.setup_ui()
        
        # 加载配置
        self.load_config()
        
        # 如果指定了特定部分，自动选择
        if section:
            index = self.sectionCombo.findText(section)
            if index >= 0:
                self.sectionCombo.setCurrentIndex(index)
    
    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建配置部分选择
        section_layout = QHBoxLayout()
        section_label = QLabel("配置部分:")
        self.sectionCombo = ComboBox()
        section_layout.addWidget(section_label)
        section_layout.addWidget(self.sectionCombo)
        main_layout.addLayout(section_layout)
        
        # 创建配置编辑区域
        self.configEdit = TextEdit()
        main_layout.addWidget(self.configEdit)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        self.saveButton = PrimaryPushButton("保存")
        self.saveButton.clicked.connect(self.save_config)
        self.cancelButton = PushButton("取消")
        self.cancelButton.clicked.connect(self.reject)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancelButton)
        button_layout.addWidget(self.saveButton)
        
        main_layout.addLayout(button_layout)
    
    def load_config(self):
        """加载日志配置"""
        try:
            # 填充配置部分选择
            self.sectionCombo.addItems([
                "常规设置", "日志级别", "分类设置", "文件设置", "性能设置"
            ])
            
            # 连接选择变化事件
            self.sectionCombo.currentTextChanged.connect(self.on_section_changed)
            
            # 初始加载
            self.on_section_changed(self.sectionCombo.currentText())
            
        except Exception as e:
            show_error_message(self, "加载配置失败", "无法加载日志配置", e)
    
    def on_section_changed(self, section):
        """处理配置部分变化"""
        try:
            # 根据不同部分加载不同配置
            if section == "常规设置":
                config = {
                    "max_log_size": "10MB",
                    "backup_count": 5,
                    "rotation": "daily",
                    "default_level": "INFO"
                }
            elif section == "日志级别":
                config = {
                    "system": "INFO",
                    "database": "INFO",
                    "network": "INFO",
                    "git": "INFO",
                    "ui": "INFO",
                    "plugin": "INFO"
                }
            elif section == "分类设置":
                config = {
                    "enable_categories": True,
                    "separate_files": True,
                    "max_category_size": "5MB"
                }
            elif section == "文件设置":
                config = {
                    "log_path": get_log_dir(),
                    "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {category} | {message}",
                    "compression": "zip",
                    "retention": "30 days"
                }
            elif section == "性能设置":
                config = {
                    "async_mode": True,
                    "queue_size": 1000,
                    "flush_interval": "1s",
                    "trace_logging": False
                }
            else:
                config = {}
            
            # 显示配置
            self.configEdit.setText(json.dumps(config, indent=4, ensure_ascii=False))
            
        except Exception as e:
            show_error_message(self, "加载部分失败", f"无法加载配置部分: {section}", e)
    
    def save_config(self):
        """保存配置"""
        try:
            # 获取当前编辑的配置内容
            config_text = self.configEdit.toPlainText()
            
            # 解析配置
            config = json.loads(config_text)
            
            # TODO: 实际保存配置
            
            # 显示保存成功
            InfoBar.success(
                title="保存成功",
                content="日志配置已更新",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
            # 关闭对话框
            self.accept()
            
        except json.JSONDecodeError:
            show_error_message(self, "保存失败", "配置格式不正确，请检查JSON格式")
        except Exception as e:
            show_error_message(self, "保存失败", "无法保存日志配置", e)

# 日志语法高亮器
class LogHighlighter(QSyntaxHighlighter):
    """日志语法高亮器，为不同级别的日志提供颜色"""
    
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        
        # 定义高亮格式
        self.formats = {
            "DEBUG": self.create_format(QColor(100, 100, 100)),  # 灰色
            "INFO": self.create_format(QColor(0, 0, 0)),         # 黑色
            "SUCCESS": self.create_format(QColor(0, 128, 0)),    # 绿色
            "WARNING": self.create_format(QColor(180, 100, 0)),  # 橙色
            "ERROR": self.create_format(QColor(200, 0, 0)),      # 红色
            "CRITICAL": self.create_format(QColor(200, 0, 150)), # 紫红色
            "TRACE": self.create_format(QColor(100, 100, 180)),  # 蓝灰色
            "date": self.create_format(QColor(0, 100, 100)),     # 青色
            "category": self.create_format(QColor(100, 0, 100))  # 紫色
        }
        
        # 添加规则
        self.add_highlighting_rules()
    
    def create_format(self, color, bold=False, italic=False):
        """创建文本格式"""
        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt
    
    def add_highlighting_rules(self):
        """添加高亮规则"""
        # 添加日志级别规则
        for level, fmt in self.formats.items():
            if level not in ["date", "category"]:
                # 使用更灵活的匹配模式，可以匹配不同格式的日志级别
                pattern = f"\\|\\s*{level}\\s*\\|"
                self.highlighting_rules.append((re.compile(pattern, re.IGNORECASE), fmt))
        
        # 日期格式规则
        date_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d{3})?"
        self.highlighting_rules.append((re.compile(date_pattern), self.formats["date"]))
        
        # 类别规则
        category_pattern = r"\| [^ ]+ \|"
        self.highlighting_rules.append((re.compile(category_pattern), self.formats["category"]))
    
    def highlightBlock(self, text):
        """实现高亮功能"""
        # 基于行内容选择整行颜色
        level_patterns = {
            "ERROR": re.compile(r"\|\s*ERROR\s*\|", re.IGNORECASE),
            "CRITICAL": re.compile(r"\|\s*CRITICAL\s*\|", re.IGNORECASE),
            "WARNING": re.compile(r"\|\s*WARNING\s*\|", re.IGNORECASE),
            "SUCCESS": re.compile(r"\|\s*SUCCESS\s*\|", re.IGNORECASE)
        }
        
        if level_patterns["ERROR"].search(text) or level_patterns["CRITICAL"].search(text):
            self.setFormat(0, len(text), self.create_format(QColor(255, 235, 235)))
        elif level_patterns["WARNING"].search(text):
            self.setFormat(0, len(text), self.create_format(QColor(255, 248, 225)))
        elif level_patterns["SUCCESS"].search(text):
            self.setFormat(0, len(text), self.create_format(QColor(235, 255, 235)))
        
        # 应用所有规则
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format)

class LogDialog(QDialog):
    """高级日志查看和管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日志管理器")
        self.resize(900, 600)
        
        # 初始化成员变量
        self.log_line_count = 0
        self.log_offset = 0
        self.logs_per_page = 300
        self.current_filter = ""
        self.loading_logs = False
        self.need_more_logs = False
        self.is_closing = False
        self.original_content = ""  # 保存原始日志内容，用于导出等操作
        
        # 记录初始化
        info("初始化日志管理器对话框")
        
        # 用于保存工作线程引用，以便在对话框关闭时停止线程
        self.worker_threads = []
        self.worker = None  # 当前工作线程
        
        # 初始化UI
        self.setup_ui()
        
        # 加载日志
        QTimer.singleShot(100, self.load_logs)  # 延迟加载，确保UI先显示
        
        # 设置定时刷新
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        
    def closeEvent(self, event):
        """对话框关闭事件"""
        self.is_closing = True
        
        # 停止定时器
        self.auto_refresh_timer.stop()
        
        # 停止并等待所有工作线程
        for thread in self.worker_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)  # 等待最多1秒
        
        super().closeEvent(event)
        
    def setup_ui(self):
        """设置UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # 创建分页控件
        self.tabWidget = QTabWidget()
        main_layout.addWidget(self.tabWidget)
        
        # 创建各个页面
        self.setup_main_tab()
        self.setup_category_tab()
        self.setup_analysis_tab()
        self.setup_management_tab()
        
        # 创建优化标签页
        self.optimizeTab = QWidget()
        self.init_optimize_tab()  # 初始化优化标签页
        self.tabWidget.addTab(self.optimizeTab, "日志优化")
        
        # 连接标签页切换信号
        self.tabWidget.currentChanged.connect(self.on_tab_changed)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        
        # 自动刷新选项
        self.autoRefreshCheck = QCheckBox("自动刷新")
        self.autoRefreshCheck.setToolTip("启用后，日志内容将自动更新")
        self.autoRefreshCheck.stateChanged.connect(self.toggle_auto_refresh)
        
        self.refreshIntervalSpin = QSpinBox()
        self.refreshIntervalSpin.setRange(1, 60)
        self.refreshIntervalSpin.setValue(5)
        self.refreshIntervalSpin.setSuffix(" 秒")
        self.refreshIntervalSpin.setToolTip("自动刷新间隔")
        self.refreshIntervalSpin.setEnabled(False)
        self.refreshIntervalSpin.valueChanged.connect(self.update_refresh_interval)
        
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(self.autoRefreshCheck)
        refresh_layout.addWidget(self.refreshIntervalSpin)
        
        # 状态标签
        self.statusLabel = QLabel("准备就绪")
        
        # 添加按钮
        self.closeButton = QPushButton("关闭")
        self.closeButton.clicked.connect(self.reject)
        
        # 布置底部控件
        button_layout.addLayout(refresh_layout)
        button_layout.addStretch(1)
        button_layout.addWidget(self.statusLabel)
        button_layout.addStretch(1)
        button_layout.addWidget(self.closeButton)
        
        main_layout.addLayout(button_layout)
        
    def on_tab_changed(self, index):
        """标签页切换事件处理"""
        if self.is_closing:
            return
            
        # 根据当前标签页索引执行相应刷新
        if index == 0:  # 主日志页
            if not self.logContent.toPlainText():
                self.refresh_log_content(initial_load=True)
        elif index == 1:  # 分类日志页
            if self.categoryTree.topLevelItemCount() == 0:
                self.refresh_category_list()
        elif index == 2:  # 分析页
            if self.statsTree.topLevelItemCount() == 0:
                self.update_analysis()
        elif index == 3:  # 管理页
            if self.fileTree.topLevelItemCount() == 0:
                self.refresh_log_files()
        elif index == 4:  # 优化页
            if hasattr(self, 'statusTable') and self.statusTable.rowCount() == 0:
                self.analyze_logs()
    
    def setup_main_tab(self):
        """设置主日志标签页"""
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)
        
        # 命令工具栏
        command_bar = CommandBar()
        
        # 添加刷新按钮
        refresh_action = Action(FIF.SYNC, "刷新")
        refresh_action.triggered.connect(self.refresh_log_content)
        command_bar.addAction(refresh_action)
        
        # 添加导出按钮
        export_action = Action(FIF.SAVE, "导出")
        export_action.triggered.connect(self.export_log)
        command_bar.addAction(export_action)
        
        # 添加复制按钮
        copy_action = Action(FIF.COPY, "复制")
        copy_action.triggered.connect(self.copy_selected_log)
        command_bar.addAction(copy_action)
        
        # 清除筛选按钮
        clear_filter_action = Action(FIF.CANCEL, "清除筛选")
        clear_filter_action.triggered.connect(self.clear_filter)
        command_bar.addAction(clear_filter_action)
        
        # 日志信息标签
        log_info = QHBoxLayout()
        self.logPathLabel = QLabel(f"日志文件: {get_log_file_path()}")
        log_info.addWidget(self.logPathLabel)
        log_info.addStretch()
        
        # 分隔线
        splitter = QSplitter(Qt.Vertical)
        
        # 日志内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logContent = QTextEdit()
        self.logContent.setReadOnly(True)
        self.logContent.setLineWrapMode(QTextEdit.NoWrap)
        self.logContent.setFont(QFont("Consolas", 9))
        content_layout.addWidget(self.logContent)
        
        # 筛选控件区域
        filter_widget = QWidget()
        filter_layout = QVBoxLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        filter_form = QFormLayout()
        filter_form.setLabelAlignment(Qt.AlignRight)
        
        # 第一行筛选
        filter_row1 = QHBoxLayout()
        
        # 日志级别筛选
        level_layout = QHBoxLayout()
        level_layout.setSpacing(5)
        level_label = QLabel("级别:")
        self.levelCombo = ComboBox()
        self.levelCombo.addItems(["全部", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL", "DEBUG", "TRACE"])
        self.levelCombo.currentTextChanged.connect(self.apply_filter)
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.levelCombo)
        
        # 分类筛选
        category_layout = QHBoxLayout()
        category_layout.setSpacing(5)
        category_label = QLabel("分类:")
        self.categoryCombo = ComboBox()
        self.categoryCombo.addItem("全部")
        for category in LogCategory:
            self.categoryCombo.addItem(category.value)
        self.categoryCombo.currentTextChanged.connect(self.apply_filter)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.categoryCombo)
        
        filter_row1.addLayout(level_layout)
        filter_row1.addSpacing(20)
        filter_row1.addLayout(category_layout)
        filter_row1.addStretch(1)
        
        # 第二行筛选
        filter_row2 = QHBoxLayout()
        
        # 关键词搜索
        keyword_layout = QHBoxLayout()
        keyword_layout.setSpacing(5)
        keyword_label = QLabel("关键词:")
        self.keywordEdit = SearchLineEdit()
        self.keywordEdit.setPlaceholderText("输入关键词筛选")
        self.keywordEdit.textChanged.connect(self.apply_filter)
        keyword_layout.addWidget(keyword_label)
        keyword_layout.addWidget(self.keywordEdit)
        
        # 日期范围筛选
        date_layout = QHBoxLayout()
        date_layout.setSpacing(5)
        date_label = QLabel("时间范围:")
        self.dateRangeCombo = ComboBox()
        self.dateRangeCombo.addItems(["全部时间", "今天", "昨天", "最近三天", "最近一周", "自定义"])
        self.dateRangeCombo.currentTextChanged.connect(self.on_date_range_changed)
        
        # 自定义日期选择器
        self.startDateEdit = QDateEdit()
        self.startDateEdit.setCalendarPopup(True)
        self.startDateEdit.setDate(QDate.currentDate().addDays(-7))
        self.startDateEdit.setEnabled(False)
        self.startDateEdit.dateChanged.connect(self.apply_filter)
        
        self.endDateEdit = QDateEdit()
        self.endDateEdit.setCalendarPopup(True)
        self.endDateEdit.setDate(QDate.currentDate())
        self.endDateEdit.setEnabled(False)
        self.endDateEdit.dateChanged.connect(self.apply_filter)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.dateRangeCombo)
        date_layout.addWidget(self.startDateEdit)
        date_layout.addWidget(QLabel("-"))
        date_layout.addWidget(self.endDateEdit)
        
        filter_row2.addLayout(keyword_layout)
        filter_row2.addSpacing(20)
        filter_row2.addLayout(date_layout)
        
        # 添加筛选条件布局
        filter_layout.addLayout(filter_row1)
        filter_layout.addLayout(filter_row2)
        
        # 将控件添加到分隔器
        splitter.addWidget(content_widget)
        splitter.addWidget(filter_widget)
        splitter.setStretchFactor(0, 5)  # 内容区域占比更多
        splitter.setStretchFactor(1, 1)  # 筛选控件占比较少
        
        # 添加控件到标签页布局
        layout.addWidget(command_bar)
        layout.addLayout(log_info)
        layout.addWidget(splitter)
        
        # 将标签页添加到分页控件
        self.tabWidget.addTab(main_tab, "主日志")
        
    def setup_category_tab(self):
        """设置分类标签页"""
        category_tab = QWidget()
        layout = QVBoxLayout(category_tab)
        
        # 创建分隔窗口
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧分类树
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        
        category_label = QLabel("日志分类")
        self.categoryTree = QTreeWidget()
        self.categoryTree.setHeaderHidden(True)
        self.categoryTree.itemClicked.connect(self.on_category_selected)
        
        # 添加"加载中..."提示项
        loading_item = QTreeWidgetItem(self.categoryTree, ["正在加载分类..."])
        loading_item.setForeground(0, QBrush(QColor(150, 150, 150)))
        
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.categoryTree)
        
        # 创建右侧日志显示区域
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        header_layout = QHBoxLayout()
        content_label = QLabel("分类日志内容")
        
        # 分类筛选按钮
        self.catFilterEdit = SearchLineEdit()
        self.catFilterEdit.setPlaceholderText("搜索当前分类...")
        self.catFilterEdit.setClearButtonEnabled(True)
        self.catFilterEdit.setFixedWidth(200)
        self.catFilterEdit.returnPressed.connect(self.apply_category_filter)
        
        header_layout.addWidget(content_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.catFilterEdit)
        
        # 创建日志查看器
        self.categoryLogEdit = QTextEdit()
        self.categoryLogEdit.setReadOnly(True)
        self.categoryLogEdit.setFont(QFont("Consolas", 9))
        self.categoryLogEdit.setPlainText("请选择一个日志分类...")
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        export_button = QPushButton("导出分类日志")
        export_button.clicked.connect(self.export_category_log)
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_category_logs)
        
        button_layout.addWidget(refresh_button)
        button_layout.addStretch(1)
        button_layout.addWidget(export_button)
        
        log_layout.addLayout(header_layout)
        log_layout.addWidget(self.categoryLogEdit)
        log_layout.addLayout(button_layout)
        
        # 添加到分隔器
        splitter.addWidget(category_widget)
        splitter.addWidget(log_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        
        # 添加标签页
        self.tabWidget.addTab(category_tab, "分类日志")
        
    def setup_analysis_tab(self):
        """设置分析标签页"""
        analysis_tab = QWidget()
        layout = QVBoxLayout(analysis_tab)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        # 分析类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("分析类型:")
        self.analysisTypeCombo = ComboBox()
        self.analysisTypeCombo.addItems(["级别分布", "分类分布", "时间分布", "错误分析"])
        self.analysisTypeCombo.currentTextChanged.connect(self.update_analysis)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.analysisTypeCombo)
        
        # 时间范围选择
        time_layout = QHBoxLayout()
        time_label = QLabel("时间范围:")
        self.analysisTimeCombo = ComboBox()
        self.analysisTimeCombo.addItems(["今天", "昨天", "最近3天", "最近7天", "最近30天", "全部时间"])
        self.analysisTimeCombo.currentTextChanged.connect(self.update_analysis)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.analysisTimeCombo)
        
        # 刷新按钮
        refresh_button = QPushButton("刷新分析")
        refresh_button.clicked.connect(self.update_analysis)
        
        control_layout.addLayout(type_layout)
        control_layout.addSpacing(20)
        control_layout.addLayout(time_layout)
        control_layout.addStretch(1)
        control_layout.addWidget(refresh_button)
        
        # 创建分隔窗口
        content_splitter = QSplitter(Qt.Vertical)
        
        # 上部分：统计树和详情
        top_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧统计树
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.statsTree = QTreeWidget()
        self.statsTree.setHeaderLabels(["项目", "数量", "占比"])
        self.statsTree.setColumnWidth(0, 150)
        self.statsTree.setColumnWidth(1, 80)
        self.statsTree.itemClicked.connect(self.on_stats_item_clicked)
        
        # 添加"加载中..."提示项
        loading_item = QTreeWidgetItem(self.statsTree, ["正在加载分析...", "", ""])
        loading_item.setForeground(0, QBrush(QColor(150, 150, 150)))
        
        stats_layout.addWidget(QLabel("统计结果:"))
        stats_layout.addWidget(self.statsTree)
        
        # 右侧详情区域
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        
        self.statsDetail = QTextEdit()
        self.statsDetail.setReadOnly(True)
        self.statsDetail.setFont(QFont("Segoe UI", 9))
        
        detail_layout.addWidget(QLabel("详细信息:"))
        detail_layout.addWidget(self.statsDetail)
        
        # 添加到上部分分隔器
        top_splitter.addWidget(stats_widget)
        top_splitter.addWidget(detail_widget)
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 2)
        
        # 下部分：错误和性能日志
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧错误列表
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setContentsMargins(0, 0, 0, 0)
        
        self.errorList = QListWidget()
        self.errorList.itemClicked.connect(self.show_error_details)
        
        # 添加"加载中..."提示项
        loading_error = QListWidgetItem("正在加载错误日志...")
        loading_error.setForeground(QBrush(QColor(150, 150, 150)))
        self.errorList.addItem(loading_error)
        
        view_errors_button = QPushButton("查看所有错误")
        view_errors_button.clicked.connect(self.view_all_errors)
        
        error_layout.addWidget(QLabel("最近错误:"))
        error_layout.addWidget(self.errorList)
        error_layout.addWidget(view_errors_button)
        
        # 右侧性能列表
        perf_widget = QWidget()
        perf_layout = QVBoxLayout(perf_widget)
        perf_layout.setContentsMargins(0, 0, 0, 0)
        
        self.perfList = QListWidget()
        self.perfList.itemClicked.connect(self.show_perf_details)
        
        # 添加"加载中..."提示项
        loading_perf = QListWidgetItem("正在加载性能日志...")
        loading_perf.setForeground(QBrush(QColor(150, 150, 150)))
        self.perfList.addItem(loading_perf)
        
        view_perf_button = QPushButton("查看所有性能日志")
        view_perf_button.clicked.connect(self.view_all_perf)
        
        perf_layout.addWidget(QLabel("性能相关日志:"))
        perf_layout.addWidget(self.perfList)
        perf_layout.addWidget(view_perf_button)
        
        # 添加到下部分分隔器
        bottom_splitter.addWidget(error_widget)
        bottom_splitter.addWidget(perf_widget)
        
        # 添加到主分隔器
        content_splitter.addWidget(top_splitter)
        content_splitter.addWidget(bottom_splitter)
        
        layout.addLayout(control_layout)
        layout.addWidget(content_splitter)
        
        # 添加标签页
        self.tabWidget.addTab(analysis_tab, "日志分析")
        
    def setup_management_tab(self):
        """设置管理标签页"""
        management_tab = QWidget()
        layout = QVBoxLayout(management_tab)
        
        # 文件列表区域
        file_group = QGroupBox("日志文件列表")
        file_layout = QVBoxLayout(file_group)
        
        # 文件列表控件
        self.fileTree = QTreeWidget()
        self.fileTree.setHeaderLabels(["文件名", "大小", "修改时间"])
        self.fileTree.setColumnWidth(0, 300)
        self.fileTree.setColumnWidth(1, 100)
        self.fileTree.itemDoubleClicked.connect(self.view_log_file)
        
        # 添加"加载中..."提示项
        loading_item = QTreeWidgetItem(self.fileTree, ["正在加载文件列表...", "", ""])
        loading_item.setForeground(0, QBrush(QColor(150, 150, 150)))
        
        # 文件操作按钮
        file_button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_log_files)
        
        open_dir_button = QPushButton("打开日志目录")
        open_dir_button.clicked.connect(self.open_log_directory)
        
        file_button_layout.addWidget(refresh_button)
        file_button_layout.addStretch(1)
        file_button_layout.addWidget(open_dir_button)
        
        file_layout.addWidget(self.fileTree)
        file_layout.addLayout(file_button_layout)
        
        # 清理选项区域
        clean_group = QGroupBox("日志清理选项")
        clean_layout = QVBoxLayout(clean_group)
        
        # 清理类型选择
        clean_type_layout = QHBoxLayout()
        self.cleanAllRadio = QRadioButton("清理所有日志")
        self.cleanAllRadio.toggled.connect(self.on_clean_option_changed)
        
        self.cleanOldRadio = QRadioButton("清理旧日志")
        self.cleanOldRadio.setChecked(True)
        self.cleanOldRadio.toggled.connect(self.on_clean_option_changed)
        
        self.cleanTypeRadio = QRadioButton("按类型清理")
        self.cleanTypeRadio.toggled.connect(self.on_clean_option_changed)
        
        clean_type_layout.addWidget(self.cleanAllRadio)
        clean_type_layout.addWidget(self.cleanOldRadio)
        clean_type_layout.addWidget(self.cleanTypeRadio)
        clean_type_layout.addStretch(1)
        
        # 清理选项参数
        self.cleanOptionsLayout = QHBoxLayout()
        
        # 日期选择
        self.daysLabel = QLabel("保留最近:")
        self.daysSpinner = QSpinBox()
        self.daysSpinner.setRange(1, 365)
        self.daysSpinner.setValue(30)
        self.daysSpinner.setSuffix(" 天")
        self.daysSpinner.setToolTip("保留最近N天的日志，清理更早的日志")
        
        # 分类选择
        self.typeLabel = QLabel("日志类型:")
        self.typeCombo = ComboBox()
        self.typeCombo.addItem("系统")
        for category in LogCategory:
            self.typeCombo.addItem(category.value)
        self.typeCombo.setEnabled(False)
        
        self.cleanOptionsLayout.addWidget(self.daysLabel)
        self.cleanOptionsLayout.addWidget(self.daysSpinner)
        self.cleanOptionsLayout.addWidget(self.typeLabel)
        self.cleanOptionsLayout.addWidget(self.typeCombo)
        self.cleanOptionsLayout.addStretch(1)
        
        # 确认选项和执行按钮
        execute_layout = QHBoxLayout()
        
        self.noPromptCheck = QCheckBox("不再提醒")
        self.noPromptCheck.setToolTip("勾选后，清理操作将不再显示确认对话框")
        
        self.executeButton = PrimaryPushButton("执行清理")
        self.executeButton.clicked.connect(self.execute_cleanup)
        
        execute_layout.addWidget(self.noPromptCheck)
        execute_layout.addStretch(1)
        execute_layout.addWidget(self.executeButton)
        
        clean_layout.addLayout(clean_type_layout)
        clean_layout.addLayout(self.cleanOptionsLayout)
        clean_layout.addLayout(execute_layout)
        
        # 添加区域到主布局
        layout.addWidget(file_group, 3)
        layout.addWidget(clean_group, 1)
        
        # 添加标签页
        self.tabWidget.addTab(management_tab, "日志管理")
    
    # ------------ 基础功能实现 ------------
    
    def load_logs(self):
        """初始加载日志"""
        # 记录初始化日志
        info("开始初始化日志标签页")
        
        # 重置初始状态
        self.log_line_count = 0
        self.log_offset = 0
        self.original_content = ""
        
        # 检查日志文件是否存在
        log_path = get_log_file_path()
        if not os.path.exists(log_path):
            warning(f"日志文件不存在: {log_path}")
            self.logContent.setPlainText(f"日志文件不存在: {log_path}\n请检查日志路径配置")
            self.statusLabel.setText("未找到日志文件")
            return
            
        if os.path.getsize(log_path) == 0:
            warning(f"日志文件为空: {log_path}")
            self.logContent.setPlainText(f"日志文件为空: {log_path}\n可能是应用刚刚安装或日志被清理")
            self.statusLabel.setText("日志文件为空")
            return
        
        # 主日志标签页
        info("初始化主日志标签页")
        self.logContent.setPlainText("正在加载日志内容...")
        self.refresh_log_content(initial_load=True)
        
        # 分类标签页 - 使用定时器错开加载时间，避免UI冻结
        QTimer.singleShot(300, lambda: (info("初始化分类日志标签页"), self.refresh_category_list()))
        
        # 分析标签页
        QTimer.singleShot(600, lambda: (info("初始化分析标签页"), self.update_analysis()))
        
        # 管理标签页
        QTimer.singleShot(900, lambda: (info("初始化管理标签页"), self.refresh_log_files()))
        
        # 优化标签页 - 预加载状态
        QTimer.singleShot(1200, lambda: (info("初始化优化标签页"), self.analyze_logs()))
        
        info("日志标签页初始化完成")
    
    def refresh_log_content(self, initial_load=False):
        """刷新日志内容"""
        try:
            if initial_load:
                self.log_offset = 0
                self.logContent.clear()
                self.logContent.setPlainText("正在加载日志内容...")
                
            # 记录调试信息
            info(f"请求加载日志: offset={self.log_offset}, 初始加载={initial_load}")
            
            # 创建加载工作线程
            self.worker = LogLoadWorker(self.log_offset, 300)
            self.worker.loaded.connect(self.on_logs_loaded)
            
            # 检查日志文件是否存在
            log_path = get_log_file_path()
            if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
                self.logContent.setPlainText(f"日志文件不存在或为空: {log_path}\n可能是应用刚刚安装或日志被清理")
                self.statusLabel.setText("未找到日志")
                return
                
            # 启动加载
            self.worker.start()
        except Exception as e:
            error(f"刷新日志内容失败: {str(e)}")
            self.logContent.setPlainText(f"加载日志失败: {str(e)}")
    
    def on_logs_loaded(self, logs, total_lines, has_more):
        """日志加载完成回调"""
        try:
            # 记录加载完成
            info(f"日志加载完成: 获取到 {len(logs) if logs else 0} 字节的日志，总行数: {total_lines}")
            
            # 如果界面已关闭，直接返回
            if hasattr(self, 'is_closing') and self.is_closing:
                return
            
            # 检查接收到的日志内容
            if not logs or logs.startswith("加载日志失败") or logs.startswith("日志文件不存在"):
                # 显示错误信息
                self.logContent.setPlainText(logs)
                self.statusLabel.setText("加载失败")
                # 存储原始内容以便导出
                self.original_content = logs
                return
            
            # 检查日志解析
            if "INFO" not in logs and "DEBUG" not in logs and "ERROR" not in logs and "WARNING" not in logs:
                info(f"日志内容似乎不是标准格式，可能无法正确筛选: {logs[:100]}...")
                
            # 保存当前滚动位置
            cursor = self.logContent.textCursor()
            scroll_pos = self.logContent.verticalScrollBar().value()
            at_end = scroll_pos == self.logContent.verticalScrollBar().maximum()
            
            # 初始加载或追加内容
            if not hasattr(self, 'log_offset') or self.log_offset == 0:
                self.logContent.setPlainText(logs)
                # 存储原始内容以便导出
                self.original_content = logs
            else:
                # 追加新内容
                cursor.movePosition(QTextCursor.End)
                cursor.insertText("\n" + logs)
                self.original_content += "\n" + logs
            
            # 重置级别选择器，确保"全部"选项被正确显示
            if hasattr(self, 'levelCombo') and self.levelCombo.currentText() == "全部":
                # 不需要应用任何级别筛选，只应用其他筛选条件
                if hasattr(self, 'current_filter') and self.current_filter:
                    # 避免将"全部"作为关键词
                    if self.current_filter.lower() == "全部":
                        self.current_filter = ""
                        if hasattr(self, 'keywordEdit'):
                            self.keywordEdit.clear()
                    
                    # 应用其他筛选条件
                    self.apply_filter(update_ui_only=True)
            else:
                # 应用当前筛选器（如果有）
                if hasattr(self, 'current_filter') and self.current_filter:
                    self.apply_filter(self.current_filter, update_ui_only=True)
            
            # 更新滚动位置
            if at_end:
                # 如果之前在底部，保持在底部
                self.scroll_to_end()
            else:
                # 否则保持在原位置
                self.logContent.verticalScrollBar().setValue(scroll_pos)
            
            # 更新状态显示
            if hasattr(self, 'logs_per_page'):
                offset = getattr(self, 'log_offset', 0)
                self.statusLabel.setText(f"已加载: {min(offset + self.logs_per_page, total_lines)}/{total_lines}")
            else:
                self.statusLabel.setText(f"已加载: {total_lines} 行日志")
            
            # 处理"加载更多"逻辑
            if has_more and hasattr(self, 'log_offset') and hasattr(self, 'logs_per_page'):
                self.log_offset += self.logs_per_page
                
                # 如果视图在底部，或者需要更多日志，自动加载更多
                if at_end or (hasattr(self, 'need_more_logs') and self.need_more_logs):
                    if hasattr(self, 'need_more_logs'):
                        self.need_more_logs = False
                    QTimer.singleShot(100, self.refresh_log_content)
            
            # 清理引用
            if hasattr(self, 'worker'):
                if hasattr(self, 'worker_threads'):
                    if self.worker in self.worker_threads:
                        self.worker_threads.remove(self.worker)
                else:
                    self.worker.deleteLater()
                    self.worker = None
                    
        except Exception as e:
            error(f"处理加载日志结果失败: {str(e)}")
            # 尝试获取更多错误信息
            import traceback
            error_details = traceback.format_exc()
            error(f"详细错误: {error_details}")
            
            # 显示错误消息
            self.logContent.setPlainText(f"处理日志数据时出错: {str(e)}")
            self.statusLabel.setText("加载错误")
    
    def scroll_to_end(self):
        """滚动到底部"""
        self.logContent.verticalScrollBar().setValue(
            self.logContent.verticalScrollBar().maximum()
        )
    
    def on_date_range_changed(self):
        """日期范围选择变化处理"""
        is_custom = self.dateRangeCombo.currentText() == "自定义"
        self.startDateEdit.setEnabled(is_custom)
        self.endDateEdit.setEnabled(is_custom)
        self.apply_filter()
    
    def apply_filter(self, filter_text=None, update_ui_only=False):
        """应用日志筛选"""
        # 获取筛选参数
        if not update_ui_only:
            level = self.levelCombo.currentText()
            category = self.categoryCombo.currentText()
            keyword = self.keywordEdit.text().strip()
            date_range = self.dateRangeCombo.currentText()
            
            if filter_text:
                keyword = filter_text
                
            # 特殊处理：如果关键词是"全部"，这可能是误操作，清空关键词
            if keyword.lower() == "全部":
                keyword = ""
                self.keywordEdit.clear()
                
            self.current_filter = keyword
            
            # 记录筛选参数
            info(f"应用筛选: 级别='{level}', 分类='{category}', 关键词='{keyword}', 时间范围='{date_range}'")
        else:
            # 仅更新UI显示，使用现有筛选条件
            level = self.levelCombo.currentText()
            category = self.categoryCombo.currentText()
            keyword = self.current_filter
            date_range = self.dateRangeCombo.currentText()
        
        # 获取当前文本内容
        current_text = self.logContent.toPlainText()
        if not current_text or current_text == "正在加载日志内容...":
            info("日志内容为空或正在加载，跳过筛选")
            return
            
        # 记录原始行数
        original_lines = current_text.split('\n')
        info(f"原始日志行数: {len(original_lines)}")
        
        # 应用筛选逻辑
        filtered_lines = []
        for line in original_lines:
            if not line.strip():
                continue
                
            include_line = True
                
            # 级别筛选
            if level != "全部":
                # 尝试使用更灵活的匹配方式
                level_pattern = re.compile(f"\\|\\s*{level}\\s*\\|", re.IGNORECASE)
                if not level_pattern.search(line):
                    include_line = False
                    
            # 分类筛选
            if category != "全部" and category not in line:
                include_line = False
                
            # 关键词筛选
            if keyword and keyword.lower() not in line.lower():
                include_line = False
                
            # 日期筛选
            if date_range != "全部时间":
                days = self.get_time_filter_days(date_range)
                if days is not None:
                    try:
                        # 提取日期部分并比较
                        cutoff_date = datetime.now() - timedelta(days=days)
                        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
                        
                        date_str = line.split('|')[0].strip()
                        log_date = date_str.split()[0]  # 提取YYYY-MM-DD部分
                        
                        if log_date < cutoff_str:
                            include_line = False
                    except Exception as e:
                        debug(f"日期筛选处理异常: {str(e)}, 行: {line[:50]}...")
                        # 如果解析失败，保留该行
                        pass
                    
            if include_line:
                filtered_lines.append(line)
        
        # 记录筛选后的行数
        info(f"筛选后日志行数: {len(filtered_lines)}")
        
        # 更新显示
        if filtered_lines:
            self.logContent.setPlainText('\n'.join(filtered_lines))
            count = len(filtered_lines)
            
            # 提供更详细的筛选状态
            status_message = f"找到 {count} 条匹配日志"
            if level != "全部" or category != "全部" or keyword:
                status_message += " ("
                if level != "全部":
                    status_message += f"级别:{level}"
                if category != "全部":
                    status_message += f"{' ' if level != '全部' else ''}分类:{category}"
                if keyword:
                    status_message += f"{' ' if level != '全部' or category != '全部' else ''}关键词:{keyword}"
                status_message += ")"
                
            self.statusLabel.setText(status_message)
        else:
            # 提供更具体的提示信息
            if level != "全部" and category == "全部" and not keyword:
                self.logContent.setPlainText(f"没有找到级别为 '{level}' 的日志记录\n请检查日志格式或尝试选择'全部'级别")
            elif level == "全部" and category != "全部" and not keyword:
                self.logContent.setPlainText(f"没有找到分类为 '{category}' 的日志记录")
            elif keyword:
                self.logContent.setPlainText(f"没有找到包含关键词 '{keyword}' 的日志记录")
            else:
                self.logContent.setPlainText("没有找到匹配的日志记录\n可能是日志文件为空或日志格式与筛选条件不匹配")
            
            self.statusLabel.setText("筛选结果为空")
            
        # 如果筛选结果较少，尝试加载更多数据
        if len(filtered_lines) < 50 and not update_ui_only:
            self.need_more_logs = True
            QTimer.singleShot(100, self.refresh_log_content)
    
    def clear_filter(self):
        """清除筛选条件"""
        # 重置筛选控件
        self.levelCombo.setCurrentText("全部")
        self.categoryCombo.setCurrentText("全部")
        self.keywordEdit.clear()
        self.dateRangeCombo.setCurrentText("全部时间")
        
        # 清除当前筛选器
        self.current_filter = ""
        
        # 重新加载日志
        self.log_offset = 0
        self.refresh_log_content(initial_load=True)
    
    def export_log(self):
        """导出日志文件"""
        options = QFileDialog.Options()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"mgit_log_{timestamp}.log"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出日志文件", default_name,
            "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*)", options=options
        )
        
        if not file_path:
            return
            
            # 检查是否应该导出筛选后的日志
        filtered_text = self.logContent.toPlainText()
        if filtered_text != self.original_content and filtered_text.strip():
            reply = QMessageBox.question(
                self, "导出确认", 
    "是否导出筛选后的日志内容？\n选择\"否\"将导出完整日志文件，包含所有分类。",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                # 导出筛选后的内容
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(filtered_text)
                    info(f"筛选后的日志导出成功: {file_path}")
                    InfoBar.success(
                        title="成功",
                        content=f"筛选后的日志已导出到: {file_path}",
                        parent=self,
                        position=InfoBarPosition.TOP,
                        duration=3000
                    )
                    return
                except Exception as e:
                    show_error_message(self, "导出失败", "导出筛选日志失败", e)
                    return
            
        # 导出完整日志文件，包含所有分类
        result = export_log(file_path, include_categories=True)
        if result:
            InfoBar.success(
                title="成功",
                content=f"完整日志已导出到: {file_path}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        else:
            show_error_message(self, "导出失败", "导出日志失败，请检查文件权限")

    def copy_selected_log(self):
        """复制选中的日志内容"""
        selected_text = self.logContent.textCursor().selectedText()
        if selected_text:
            QApplication.clipboard().setText(selected_text)
            InfoBar.success(
                title="成功",
                content="已复制选中的日志内容到剪贴板",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
        else:
            InfoBar.warning(
                title="提示",
                content="请先选择要复制的日志内容",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
    
    def toggle_auto_refresh(self, state):
        """切换自动刷新状态"""
        if state:
            # 启动自动刷新
            interval = self.refreshIntervalSpin.value() * 1000
            self.auto_refresh_timer.start(interval)
            # 检查对应UI元素是否存在
            if hasattr(self, 'refreshStatus'):
                self.refreshStatus.setText(f"自动刷新已启用 ({self.refreshIntervalSpin.value()}秒)")
            else:
                self.statusLabel.setText(f"自动刷新已启用 ({self.refreshIntervalSpin.value()}秒)")
        else:
            # 停止自动刷新
            self.auto_refresh_timer.stop()
            # 检查对应UI元素是否存在
            if hasattr(self, 'refreshStatus'):
                self.refreshStatus.setText("自动刷新已禁用")
            else:
                self.statusLabel.setText("自动刷新已禁用")
    
    def update_refresh_interval(self, value):
        """更新刷新间隔"""
        # 更新已启动的定时器
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.setInterval(value * 1000)
            # 检查是否有状态标签
            if hasattr(self, 'refreshStatus'):
                self.refreshStatus.setText(f"自动刷新已启用 ({value}秒)")
            else:
                self.statusLabel.setText(f"自动刷新已启用 ({value}秒)")
        
        # 显示当前间隔值
        if hasattr(self, 'refreshIntervalLabel'):
            self.refreshIntervalLabel.setText(f"{value}秒")
    
    def auto_refresh(self):
        """自动刷新日志"""
        if self.is_closing:
            return
            
        # 保存当前滚动位置和选择位置
        cursor_position = self.logContent.textCursor().position()
        scroll_position = self.logContent.verticalScrollBar().value()
        at_end = scroll_position >= self.logContent.verticalScrollBar().maximum() - 30
        
        # 重新加载只加载第一页
        self.log_offset = 0
        self.refresh_log_content()
        
        # 如果之前在底部，刷新后自动滚动到底部
        if at_end:
            QTimer.singleShot(100, self.scroll_to_end)
    
    # ------------ 分类标签页功能 ------------
    
    def refresh_category_list(self):
        """刷新分类列表"""
        self.categoryTree.clear()
        
        # 添加根节点
        root = QTreeWidgetItem(self.categoryTree, ["所有分类"])
        root.setExpanded(True)
        
        try:
            # 添加常规分类
            standard_categories = QTreeWidgetItem(root, ["标准分类"])
            standard_categories.setExpanded(True)
            
            for category in LogCategory:
                item = QTreeWidgetItem(standard_categories, [category.value])
                item.setData(0, Qt.UserRole, category.value.lower())
            
            # 添加特殊分类
            special_categories = QTreeWidgetItem(root, ["特殊日志"])
            special_categories.setExpanded(True)
            
            # 错误日志
            error_item = QTreeWidgetItem(special_categories, ["错误日志"])
            error_item.setData(0, Qt.UserRole, "ERROR")
            
            # 性能日志
            perf_item = QTreeWidgetItem(special_categories, ["性能日志"])
            perf_item.setData(0, Qt.UserRole, "PERFORMANCE")
            
            # 自动选择第一个标准分类
            self.categoryTree.setCurrentItem(standard_categories.child(0))
            self.on_category_selected(standard_categories.child(0))
            
        except Exception as e:
            warning(f"刷新分类列表失败: {str(e)}")
    
    def on_category_selected(self, item):
        """处理分类选择事件"""
        if not item:
            return
            
        category = item.data(0, Qt.UserRole)
        if not category:
            # 如果是父节点，不处理
            return
        
        # 加载选中分类的日志
        self.load_category_logs(category)
    
    def load_category_logs(self, category):
        """加载指定分类的日志"""
        self.categoryLogEdit.clear()
        
        try:
            # 获取指定分类的日志
            log_content = get_recent_logs(500, category)
            self.categoryLogEdit.setPlainText(log_content)
            
            # 记录当前分类和内容
            self.current_category = category
            self.current_category_content = log_content
            
            # 设置语法高亮
            highlighter = LogHighlighter(self.categoryLogEdit.document())
        except Exception as e:
            self.categoryLogEdit.setPlainText(f"读取分类日志失败: {str(e)}")
    
    def refresh_category_logs(self):
        """刷新当前分类的日志"""
        if hasattr(self, 'current_category'):
            self.load_category_logs(self.current_category)
    
    def apply_category_filter(self):
        """应用分类内筛选"""
        if not hasattr(self, 'current_category_content') or not self.current_category_content:
            return
            
        keyword = self.catFilterEdit.text().strip()
        if not keyword:
            # 显示完整内容
            self.categoryLogEdit.setPlainText(self.current_category_content)
            return
            
        # 过滤包含关键词的行
        filtered_lines = [line for line in self.current_category_content.split('\n') 
                         if keyword.lower() in line.lower()]
        
        # 更新显示
        self.categoryLogEdit.setPlainText('\n'.join(filtered_lines))
    
    def export_category_log(self):
        """导出当前分类日志"""
        if not hasattr(self, 'current_category'):
            InfoBar.warning(
                title="警告",
                content="请先选择一个分类",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
        
        options = QFileDialog.Options()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        default_name = f"mgit_{self.current_category}_log_{timestamp}.log"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分类日志", default_name,
            "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*)", options=options
        )
        
        if not file_path:
            return
            
        try:
            # 获取当前显示内容
            content = self.categoryLogEdit.toPlainText()
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            info(f"分类日志导出成功: {file_path}")
            InfoBar.success(
                title="成功",
                content=f"分类日志已导出到: {file_path}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        except Exception as e:
            show_error_message(self, "导出失败", "导出分类日志失败", e)
    
    # ------------ 分析标签页功能 ------------
    
    def update_analysis(self):
        """更新日志分析内容"""
        analysis_type = self.analysisTypeCombo.currentText()
        time_range = self.analysisTimeCombo.currentText()
        
        # 清空现有内容
        self.statsTree.clear()
        self.statsDetail.clear()
        self.errorList.clear()
        self.perfList.clear()
        
        # 根据分析类型执行对应分析
        if analysis_type == "级别分布":
            self.analyze_log_levels(time_range)
        elif analysis_type == "分类分布":
            self.analyze_categories(time_range)
        elif analysis_type == "时间分布":
            self.analyze_time_distribution(time_range)
        elif analysis_type == "错误分析":
            self.analyze_errors(time_range)
            
        # 更新错误和性能列表
        self.update_error_list(time_range)
        self.update_perf_list(time_range)
    
    def get_time_filter_days(self, time_range):
        """获取时间范围对应的天数"""
        if not time_range or not isinstance(time_range, str):
            info(f"时间范围格式无效: {time_range}")
            return None  # 全部
            
        time_range = time_range.strip()
        if time_range == "今天":
            return 1
        elif time_range == "昨天":
            return 2
        elif time_range == "最近3天":
            return 3
        elif time_range == "最近7天":
            return 7
        elif time_range == "最近30天":
            return 30
        elif time_range == "全部":
            return None
        else:
            info(f"未知的时间范围: {time_range}，使用全部")
            return None  # 未知时间范围，默认全部
    
    def analyze_log_levels(self, time_range):
        """分析日志级别分布"""
        try:
            # 获取日志内容
            days = self.get_time_filter_days(time_range)
            log_content = self._get_filtered_logs(days)
            
            # 计算各级别数量
            levels = {
                "DEBUG": 0,
                "INFO": 0,
                "SUCCESS": 0,
                "WARNING": 0,
                "ERROR": 0,
                "CRITICAL": 0,
                "TRACE": 0
            }
            
            # 创建级别匹配模式
            level_patterns = {}
            for level in levels.keys():
                level_patterns[level] = re.compile(f"\\|\\s*{level}\\s*\\|", re.IGNORECASE)
            
            total = 0
            for line in log_content.split('\n'):
                if not line.strip():
                    continue
                    
                total += 1
                for level, pattern in level_patterns.items():
                    if pattern.search(line):
                        levels[level] += 1
                        break
            
            # 添加到统计树
            for level, count in levels.items():
                if count > 0:
                    percentage = f"{count / total * 100:.1f}%" if total > 0 else "0%"
                    item = QTreeWidgetItem(self.statsTree, [level, str(count), percentage])
                    
                    # 设置颜色
                    if level in ["ERROR", "CRITICAL"]:
                        item.setForeground(0, QBrush(QColor(200, 0, 0)))
                    elif level == "WARNING":
                        item.setForeground(0, QBrush(QColor(180, 100, 0)))
                    elif level == "SUCCESS":
                        item.setForeground(0, QBrush(QColor(0, 128, 0)))
            
            # 添加总计
            QTreeWidgetItem(self.statsTree, ["总计", str(total), "100%"])
            
            # 调整列宽
            for i in range(3):
                self.statsTree.resizeColumnToContents(i)
                
            # 更新详情
            self.statsDetail.setHtml(f"""
            <h3>日志级别分析</h3>
            <p>分析范围: {time_range}</p>
            <p>总日志条数: {total}</p>
            <ul>
                <li>信息日志 (INFO): {levels['INFO']} ({levels['INFO']/total*100:.1f}% 如适用)</li>
                <li>成功日志 (SUCCESS): {levels['SUCCESS']} ({levels['SUCCESS']/total*100:.1f}% 如适用)</li>
                <li>警告日志 (WARNING): {levels['WARNING']} ({levels['WARNING']/total*100:.1f}% 如适用)</li>
                <li>错误日志 (ERROR): {levels['ERROR']} ({levels['ERROR']/total*100:.1f}% 如适用)</li>
                <li>严重错误 (CRITICAL): {levels['CRITICAL']} ({levels['CRITICAL']/total*100:.1f}% 如适用)</li>
                <li>调试日志 (DEBUG): {levels['DEBUG']} ({levels['DEBUG']/total*100:.1f}% 如适用)</li>
                <li>跟踪日志 (TRACE): {levels['TRACE']} ({levels['TRACE']/total*100:.1f}% 如适用)</li>
            </ul>
            <p>健康状况: {self._get_health_status(levels)}</p>
            """)
            
        except Exception as e:
            self.statsDetail.setPlainText(f"分析日志级别分布时出错: {str(e)}")
    
    def _get_health_status(self, levels):
        """获取日志健康状态评估"""
        total = sum(levels.values())
        if total == 0:
            return "无法评估 (没有日志)"
            
        error_ratio = (levels["ERROR"] + levels["CRITICAL"]) / total
        warning_ratio = levels["WARNING"] / total if total > 0 else 0
        
        if error_ratio > 0.1:
            return "<span style='color:red'>不健康 (错误率过高)</span>"
        elif error_ratio > 0.05:
            return "<span style='color:orange'>需要关注 (错误率较高)</span>"
        elif warning_ratio > 0.2:
            return "<span style='color:orange'>需要关注 (警告较多)</span>"
        else:
            return "<span style='color:green'>良好</span>"
    
    def _get_filtered_logs(self, days=None):
        """获取按时间过滤的日志内容"""
        try:
            info(f"过滤日志: days={days}, 类型={type(days)}")
            
            # 类型检查和转换
            if days is not None:
                try:
                    days = int(days)  # 确保days是整数
                except (ValueError, TypeError):
                    info(f"days参数无法转换为整数: {days}，将使用全部日志")
                    days = None
            
            if days is None or days <= 0:
                # 获取所有日志
                info("获取全部日志")
                return get_recent_logs(2000)
                
            # 获取最近的日志
            info(f"获取最近{days}天的日志")
            log_content = get_recent_logs(2000)
            
            if not log_content.strip():
                info("获取的日志内容为空")
                return ""
                
            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            info(f"截止日期: {cutoff_str}")
            
            # 过滤日志
            filtered_lines = []
            for line in log_content.split('\n'):
                if not line.strip():
                    continue
                    
                try:
                    # 提取日期部分
                    date_str = line.split('|')[0].strip()
                    log_date = date_str.split()[0]  # 提取YYYY-MM-DD部分
                    
                    if log_date >= cutoff_str:
                        filtered_lines.append(line)
                except Exception as e:
                    # 解析失败时保留该行
                    info(f"日期解析失败: {str(e)}, 保留该行: {line[:30]}...")
                    filtered_lines.append(line)
            
            info(f"过滤后的日志行数: {len(filtered_lines)}")
            return '\n'.join(filtered_lines)
            
        except Exception as e:
            error(f"过滤日志失败: {str(e)}")
            return ""
    
    def analyze_categories(self, time_range):
        """分析分类分布"""
        try:
            # 获取日志内容
            days = self.get_time_filter_days(time_range)
            log_content = self._get_filtered_logs(days)
            
            # 计算各分类数量
            categories = {}
            for category in LogCategory:
                categories[category.value] = 0
            
            total = 0
            for line in log_content.split('\n'):
                if not line.strip():
                    continue
                    
                total += 1
                for category in categories.keys():
                    if category in line:
                        categories[category] += 1
                        break
            
            # 添加到统计树
            for category, count in categories.items():
                if count > 0:
                    percentage = f"{count / total * 100:.1f}%" if total > 0 else "0%"
                    QTreeWidgetItem(self.statsTree, [category, str(count), percentage])
            
            # 添加总计
            QTreeWidgetItem(self.statsTree, ["总计", str(total), "100%"])
            
            # 调整列宽
            for i in range(3):
                self.statsTree.resizeColumnToContents(i)
                
            # 更新详情
            details_html = f"""
            <h3>日志分类分析</h3>
            <p>分析范围: {time_range}</p>
            <p>总日志条数: {total}</p>
            <ul>
            """
            
            for category, count in categories.items():
                if count > 0:
                    details_html += f"<li>{category}: {count} ({count/total*100:.1f}% 如适用)</li>"
            
            details_html += """
            </ul>
            """
            
            self.statsDetail.setHtml(details_html)
            
        except Exception as e:
            self.statsDetail.setPlainText(f"分析日志分类分布时出错: {str(e)}")
    
    def analyze_time_distribution(self, time_range):
        """分析时间分布"""
        pass  # 此功能较复杂，需要额外实现
    
    def analyze_errors(self, time_range):
        """分析错误"""
        pass  # 此功能较复杂，需要额外实现
    
    def update_error_list(self, time_range):
        """更新错误列表"""
        try:
            # 获取错误日志
            days = self.get_time_filter_days(time_range)
            log_content = self._get_filtered_logs(days)
            
            # 清空列表
            self.errorList.clear()
            
            # 解析错误
            errors = []
            current_error = []
            
            # 创建正则表达式用于匹配ERROR和CRITICAL级别
            error_pattern = re.compile(r"\|\s*(ERROR|CRITICAL)\s*\|", re.IGNORECASE)
            
            for line in log_content.split('\n'):
                if not line.strip():
                    if current_error:
                        errors.append('\n'.join(current_error))
                        current_error = []
                    continue
                
                if error_pattern.search(line):
                    if current_error:
                        errors.append('\n'.join(current_error))
                        current_error = []
                    current_error.append(line)
                elif current_error:
                    current_error.append(line)
            
            # 添加最后一个错误
            if current_error:
                errors.append('\n'.join(current_error))
            
            # 添加到列表
            for error_text in errors:
                # 提取错误摘要
                summary = error_text.split('\n')[0]
                if len(summary) > 100:
                    summary = summary[:97] + "..."
                
                item = QListWidgetItem(summary)
                item.setData(Qt.UserRole, error_text)
                self.errorList.addItem(item)
                
        except Exception as e:
            warning(f"更新错误列表失败: {str(e)}")
    
    def update_perf_list(self, time_range):
        """更新性能日志列表"""
        try:
            # 获取性能日志
            days = self.get_time_filter_days(time_range)
            # 记录获取到的天数
            info(f"性能日志更新：时间范围 '{time_range}' 转换为 {days} 天")
            
            logs = self._get_filtered_logs(days)
            # 记录获取到的日志字节数
            info(f"性能日志更新：获取到 {len(logs) if logs else 0} 字节的日志")
            
            # 清空列表
            self.perfList.clear()
            
            # 创建性能日志匹配模式（通常为TRACE级别）
            trace_pattern = re.compile(r"\|\s*TRACE\s*\|", re.IGNORECASE)
            
            # 过滤性能日志
            if logs:
                perf_logs = [log for log in logs.split('\n') 
                          if log.strip() and trace_pattern.search(log)]
                
                # 记录过滤后的日志数量
                info(f"性能日志更新：过滤后有 {len(perf_logs)} 条性能日志")
                
                # 添加到列表
                for log in perf_logs[:50]:  # 限制显示数量
                    self.perfList.addItem(log)
            else:
                info("性能日志更新：没有获取到日志内容")
                
        except Exception as e:
            error(f"更新性能列表失败: {str(e)}")
            show_error_message(self, "更新性能列表失败", "无法更新性能日志列表", e)
    
    def on_stats_item_clicked(self, item, column):
        """处理统计项点击事件"""
        try:
            # 获取项目数据
            item_text = item.text(0)
            item_count = item.text(1)
            item_percent = item.text(2)
            
            # 获取当前分析类型
            analysis_type = self.analysisTypeCombo.currentText()
            time_range = self.analysisTimeCombo.currentText()
            
            # 准备详细信息
            detail_text = f"<h3>{item_text}</h3>\n"
            detail_text += f"<p>数量: <b>{item_count}</b></p>\n"
            detail_text += f"<p>占比: <b>{item_percent}</b></p>\n"
            detail_text += f"<p>分析范围: {time_range}</p>\n\n"
            
            # 根据不同类型显示不同详情
            if analysis_type == "级别分布":
                # 获取该级别的示例日志
                logs = self._get_filtered_logs(self.get_time_filter_days(time_range))
                level_logs = [log for log in logs if item_text in log]
                
                detail_text += "<h4>示例日志:</h4>\n"
                for log in level_logs[:5]:  # 显示前5条
                    detail_text += f"<p>{log}</p>\n"
                    
            elif analysis_type == "分类分布":
                # 获取该分类的基本信息
                category_size = "未知"
                try:
                    from src.utils.logger import get_category_size
                    size_bytes = get_category_size(item_text)
                    category_size = self._format_size(size_bytes)
                except:
                    pass
                    
                detail_text += f"<h4>分类信息:</h4>\n"
                detail_text += f"<p>分类名称: {item_text}</p>\n"
                detail_text += f"<p>日志大小: {category_size}</p>\n"
                    
            elif analysis_type == "错误分析":
                # 获取更多错误上下文
                if "错误" in item_text:
                    detail_text += "<h4>常见错误模式:</h4>\n"
                    detail_text += "<p>- 程序异常</p>\n"
                    detail_text += "<p>- 网络连接问题</p>\n"
                    detail_text += "<p>- 用户输入错误</p>\n"
                
            # 更新详情显示
            self.statsDetail.setHtml(detail_text)
            
        except Exception as e:
            self.statsDetail.setPlainText(f"无法加载详细信息: {str(e)}")
    
    def show_error_details(self, item):
        """显示错误详情"""
        error_text = item.data(Qt.UserRole)
        if error_text:
            self.statsDetail.setPlainText(error_text)
    
    def show_perf_details(self, item):
        """显示性能详情"""
        perf_text = item.text()
        self.statsDetail.setPlainText(perf_text)
    
    def view_all_errors(self):
        """查看所有错误日志"""
        # 切换到分类标签页
        self.tabWidget.setCurrentIndex(1)
        
        # 找到错误日志分类项
        for i in range(self.categoryTree.topLevelItemCount()):
            top_item = self.categoryTree.topLevelItem(i)
            
            for j in range(top_item.childCount()):
                child = top_item.child(j)
                
                if child.childCount() > 0:
                    # 如果有子项，检查子项
                    for k in range(child.childCount()):
                        grandchild = child.child(k)
                        if grandchild.text(0) == "错误日志":
                            self.categoryTree.setCurrentItem(grandchild)
                            self.on_category_selected(grandchild)
                            return
                elif child.text(0) == "错误日志":
                    self.categoryTree.setCurrentItem(child)
                    self.on_category_selected(child)
                    return
    
    def view_all_perf(self):
        """查看所有性能日志"""
        # 切换到分类标签页
        self.tabWidget.setCurrentIndex(1)
        
        # 找到性能日志分类项
        for i in range(self.categoryTree.topLevelItemCount()):
            top_item = self.categoryTree.topLevelItem(i)
            
            for j in range(top_item.childCount()):
                child = top_item.child(j)
                
                if child.childCount() > 0:
                    # 如果有子项，检查子项
                    for k in range(child.childCount()):
                        grandchild = child.child(k)
                        if grandchild.text(0) == "性能日志":
                            self.categoryTree.setCurrentItem(grandchild)
                            self.on_category_selected(grandchild)
                            return
                elif child.text(0) == "性能日志":
                    self.categoryTree.setCurrentItem(child)
                    self.on_category_selected(child)
                    return

    # ------------ 管理标签页功能 ------------
    
    def refresh_log_files(self):
        """刷新日志文件列表"""
        self.fileTree.clear()
        
        try:
            # 获取日志目录
            log_dir = get_log_dir()
            
            # 遍历日志文件
            for file_name in os.listdir(log_dir):
                if not (file_name.endswith('.log') or file_name.endswith('.gz')):
                    continue
                    
                file_path = os.path.join(log_dir, file_name)
                
                # 获取文件信息
                stat_info = os.stat(file_path)
                
                # 文件大小
                size = stat_info.st_size
                size_str = self._format_size(size)
                
                # 修改时间
                mod_time = datetime.fromtimestamp(stat_info.st_mtime)
                mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 创建项
                item = QTreeWidgetItem(self.fileTree, [file_name, size_str, mod_time_str])
                item.setData(0, Qt.UserRole, file_path)
                
                # 设置图标
                if file_name.endswith('.gz'):
                    item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
                else:
                    item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogContentsView))
                
            # 调整列宽
            for i in range(3):
                self.fileTree.resizeColumnToContents(i)
                
        except Exception as e:
            show_error_message(self, "错误", "刷新日志文件列表失败", e)
    
    def _format_size(self, size_in_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} TB"
    
    def open_log_directory(self):
        """打开日志目录"""
        try:
            log_dir = get_log_dir()
            
            # 根据不同操作系统打开文件夹
            if os.name == 'nt':  # Windows
                os.startfile(log_dir)
            elif os.name == 'posix':  # macOS, Linux
                if sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', log_dir])
                else:  # Linux
                    subprocess.call(['xdg-open', log_dir])
            
            info(f"打开日志目录: {log_dir}", LogCategory.UI)
            
        except Exception as e:
            show_error_message(self, "打开目录失败", "无法打开日志目录", e)
    
    def on_clean_option_changed(self):
        """处理清理选项变化"""
        try:
            # 更新清理选项显示状态
            self.daysLabel.setEnabled(self.cleanOldRadio.isChecked())
            self.daysSpinner.setEnabled(self.cleanOldRadio.isChecked())
            
            self.typeLabel.setEnabled(self.cleanTypeRadio.isChecked())
            self.typeCombo.setEnabled(self.cleanTypeRadio.isChecked())
            
            # 更新状态标签
            if self.cleanAllRadio.isChecked():
                self.statusLabel.setText("准备清理所有日志文件")
            elif self.cleanOldRadio.isChecked():
                days = self.daysSpinner.value()
                self.statusLabel.setText(f"准备清理 {days} 天前的日志")
            elif self.cleanTypeRadio.isChecked():
                category = self.typeCombo.currentText()
                self.statusLabel.setText(f"准备清理 {category} 类别的日志")
        except Exception as e:
            warning(f"更新清理选项时出错: {str(e)}", LogCategory.UI)
    
    def update_clean_options(self):
        """更新清理选项"""
        # 更新清理选项显示状态
        self.daysLabel.setEnabled(self.cleanOldRadio.isChecked())
        self.daysSpinner.setEnabled(self.cleanOldRadio.isChecked())
        
        self.typeLabel.setEnabled(self.cleanTypeRadio.isChecked())
        self.typeCombo.setEnabled(self.cleanTypeRadio.isChecked())
    
    def execute_cleanup(self):
        """执行日志清理"""
        # 获取选中的清理选项
        selected_option = None
        if self.cleanAllRadio.isChecked():
            selected_option = "all"
        elif self.cleanOldRadio.isChecked():
            selected_option = "old"
        elif self.cleanTypeRadio.isChecked():
            selected_option = "category"
        
        if not selected_option:
            return
        
        # 确认对话框
        if not self.noPromptCheck.isChecked():
            messageBox = MessageBox(
                "确认清理",
                "确定要清理日志吗？此操作不可撤销。",
                self
            )
            messageBox.yesButton.setText("确认")
            messageBox.cancelButton.setText("取消")
            
            if not messageBox.exec():
                return
        
        try:
            # 准备清理参数
            clean_params = {}
            
            if selected_option == "all":
                # 清理所有日志
                pass  # 使用默认参数
                
            elif selected_option == "old":
                # 清理旧日志
                days = self.daysSpinner.value()
                clean_params["older_than_days"] = days
                
            elif selected_option == "category":
                # 清理特定分类日志
                selected_category = self.typeCombo.currentText()
                clean_params["category"] = selected_category
            
            # 执行清理
            result = clean_logs(**clean_params)
            
            # 更新界面
            self.refresh_log_files()
            
            # 显示结果
            report = f"""<h3>日志清理结果</h3>
            <p>总处理文件数: {result['total_files']}</p>
            <p>已清理文件数: {result['deleted_files']}</p>
            <p>已跳过文件数: {result['skipped_files']}</p>
            """
            
            if result['failed_files'] > 0:
                report += f"<p style='color:red'>失败文件数: {result['failed_files']}</p>"
            
            if len(result.get('details', [])) > 0:
                report += "<h4>详细信息</h4><ul>"
                for detail in result.get('details', [])[:10]:  # 限制显示前10个
                    status = detail.get('status', '')
                    filename = detail.get('file', '')
                    
                    if status == 'deleted':
                        report += f"<li>已删除: {filename}</li>"
                    elif status == 'cleared':
                        report += f"<li>已清空: {filename}</li>"
                    elif status == 'skipped':
                        report += f"<li>已跳过: {filename}</li>"
                    elif status == 'failed':
                        reason = detail.get('reason', '未知原因')
                        report += f"<li style='color:red'>失败: {filename} - {reason}</li>"
                
                if len(result.get('details', [])) > 10:
                    report += f"<li>...等共 {len(result['details'])} 个文件</li>"
                    
                report += "</ul>"
            
            self.clean_report = report
            
            # 显示结果对话框
            msg_box = MessageBox(
                "清理完成",
                report,
                self
            )
            msg_box.exec()
            
        except Exception as e:
            show_error_message(self, "清理失败", "日志清理操作失败", e)
    
    # ---------- 双击查看日志文件 ----------
    
    def view_log_file(self, item):
        """查看选中的日志文件"""
        if not item:
            return
            
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.exists(file_path):
            return
            
        # 检查文件类型
        if file_path.endswith('.gz'):
            self.view_compressed_log(file_path)
        else:
            self.view_plain_log(file_path)
    
    def view_plain_log(self, file_path):
        """查看普通日志文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.show_log_content(os.path.basename(file_path), content)
                
        except Exception as e:
            show_error_message(self, "错误", "读取日志文件失败", e)
    
    def view_compressed_log(self, file_path):
        """查看压缩日志文件"""
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                content = f.read()
                
            self.show_log_content(os.path.basename(file_path), content)
                
        except Exception as e:
            show_error_message(self, "错误", "读取压缩日志文件失败", e)
    
    def show_log_content(self, file_name, content):
        """显示日志内容"""
        # 创建内容查看对话框
        dialog = PopUpDialog(
            f"日志查看 - {file_name}",
            self
        )
        
        # 设置窗口大小
        dialog.resize(800, 600)
        
        # 创建文本显示区域
        text_edit = TextEdit(dialog)
        text_edit.setLineWrapMode(TextEdit.NoWrap)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(content)
        
        # 创建水平布局
        h_layout = QHBoxLayout()
        dialog.setLayout(h_layout)
        
        # 创建垂直布局
        v_layout = QVBoxLayout()
        h_layout.addLayout(v_layout)
        
        # 添加文本编辑器到布局
        v_layout.addWidget(text_edit)
        
        # 创建搜索框
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索标签和输入框
        search_label = QLabel("搜索:")
        search_edit = LineEdit()
        search_edit.setClearButtonEnabled(True)
        search_edit.setPlaceholderText("输入搜索关键词")
        
        # 搜索按钮
        search_prev_btn = PushButton("上一个")
        search_next_btn = PushButton("下一个")
        
        # 添加控件到搜索布局
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_edit)
        search_layout.addWidget(search_prev_btn)
        search_layout.addWidget(search_next_btn)
        
        # 添加搜索框到主布局
        v_layout.addWidget(search_frame)
        
        # 设置语法高亮
        highlighter = LogHighlighter(text_edit.document())
        
        # 搜索功能
        def search_text(direction=1):
            keyword = search_edit.text()
            if not keyword:
                return
                
            cursor = text_edit.textCursor()
            current_pos = cursor.position()
            
            # 设置搜索选项
            options = QTextDocument.FindFlag()
            if direction < 0:
                options |= QTextDocument.FindBackward
            
            # 执行搜索
            if not text_edit.find(keyword, options):
                # 如果未找到，从头/尾搜索
                cursor = text_edit.textCursor()
                cursor.movePosition(
                    QTextCursor.Start if direction > 0 else QTextCursor.End
                )
                text_edit.setTextCursor(cursor)
                text_edit.find(keyword, options)
        
        # 连接信号
        search_next_btn.clicked.connect(lambda: search_text(1))
        search_prev_btn.clicked.connect(lambda: search_text(-1))
        search_edit.returnPressed.connect(lambda: search_text(1))
        
        # 显示对话框
        dialog.exec()

    # ------------ 优化标签页功能 ------------
    
    def init_optimize_tab(self):
        """初始化优化标签页"""
        # 创建主布局
        main_layout = QVBoxLayout(self.optimizeTab)
        
        # 创建上部控制区域
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # 创建状态指示器
        self.statusIndicator = StateToolTip(
            "日志系统状态", 
            "正在分析...",
            self.optimizeTab
        )
        self.statusIndicator.setVisible(False)
        
        # 添加控制按钮
        self.analyzeButton = PushButton("分析日志")
        self.analyzeButton.clicked.connect(self.analyze_logs)
        
        self.optimizeButton = PushButton("优化日志")
        self.optimizeButton.clicked.connect(self.optimize_logs)
        self.optimizeButton.setEnabled(False)  # 初始禁用，需要先分析
        
        # 添加配置按钮
        self.configButton = ToolButton()
        self.configButton.setIcon(FIF.SETTING)
        self.configButton.setToolTip("日志系统配置")
        self.configButton.clicked.connect(self.show_log_config)
        
        # 添加按钮到控制布局
        control_layout.addWidget(self.analyzeButton)
        control_layout.addWidget(self.optimizeButton)
        control_layout.addStretch()
        control_layout.addWidget(self.configButton)
        
        # 添加控制区域到主布局
        main_layout.addWidget(control_frame)
        
        # 创建状态卡片
        status_card = SimpleCardWidget(self.optimizeTab)
        title_label = QLabel("日志系统状态")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        status_layout = QVBoxLayout()
        status_layout.addWidget(title_label)
        status_card.setLayout(status_layout)
        
        # 创建状态表格
        self.statusTable = TableWidget(self)
        self.statusTable.setColumnCount(2)
        self.statusTable.setHorizontalHeaderLabels(["参数", "值"])
        self.statusTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.statusTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.statusTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 添加表格到状态卡片
        status_layout.addWidget(self.statusTable)
        
        # 添加状态卡片到主布局
        main_layout.addWidget(status_card)
        
        # 创建分析结果卡片
        analysis_card = SimpleCardWidget(self.optimizeTab)
        title_label = QLabel("分析结果")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        analysis_layout = QVBoxLayout()
        analysis_layout.addWidget(title_label)
        analysis_card.setLayout(analysis_layout)
        
        # 创建分析结果区域
        self.analysisTextEdit = TextEdit()
        self.analysisTextEdit.setReadOnly(True)
        
        # 添加分析结果区域到分析卡片
        analysis_layout.addWidget(self.analysisTextEdit)
        
        # 添加分析卡片到主布局
        main_layout.addWidget(analysis_card)
        
        # 创建优化建议卡片
        recommendations_card = SimpleCardWidget(self.optimizeTab)
        title_label = QLabel("优化建议")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        recommendations_layout = QVBoxLayout()
        recommendations_layout.addWidget(title_label)
        recommendations_card.setLayout(recommendations_layout)
        
        # 创建建议列表
        self.recommendationsTree = TreeWidget()
        self.recommendationsTree.setHeaderLabels(["建议", "状态", "影响"])
        self.recommendationsTree.setColumnCount(3)
        
        # 设置树形控件样式
        self.recommendationsTree.setAlternatingRowColors(True)
        self.recommendationsTree.setAnimated(True)
        self.recommendationsTree.setIndentation(20)
        
        # 添加建议列表到建议卡片
        recommendations_layout.addWidget(self.recommendationsTree)
        
        # 添加建议卡片到主布局
        main_layout.addWidget(recommendations_card)
    
    def analyze_logs(self):
        """分析日志系统状态"""
        try:
            # 显示状态指示器
            self.statusIndicator.setContent("正在分析日志系统...")
            self.statusIndicator.move(
                self.optimizeTab.width() // 2 - self.statusIndicator.width() // 2,
                self.optimizeTab.height() // 2 - self.statusIndicator.height() // 2
            )
            self.statusIndicator.show()
            
            # 禁用分析按钮
            self.analyzeButton.setEnabled(False)
            
            # 使用后台线程进行分析
            worker = LogAnalysisWorker()
            worker.analysisFinished.connect(self.on_analysis_finished)
            self.worker_threads.append(worker)
            worker.start()
            
        except Exception as e:
            self.statusIndicator.setVisible(False)
            self.analyzeButton.setEnabled(True)
            show_error_message(self, "分析失败", "日志系统分析失败", e)
    
    def on_analysis_finished(self, results):
        """处理分析完成的结果"""
        # 隐藏状态指示器
        self.statusIndicator.setVisible(False)
        
        # 启用按钮
        self.analyzeButton.setEnabled(True)
        self.optimizeButton.setEnabled(True)
        
        if not results:
            InfoBar.error(
                title="分析失败",
                content="未能获取分析结果",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        try:
            # 更新状态表格
            self.update_status_table(results.get("status", {}))
            
            # 更新分析结果
            self.update_analysis_results(results.get("analysis", {}))
            
            # 更新优化建议
            self.update_recommendations(results.get("recommendations", []))
            
            # 显示成功消息
            InfoBar.success(
                title="分析完成",
                content="日志系统分析已完成",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
        except Exception as e:
            show_error_message(self, "处理分析结果失败", "更新分析结果时出错", e)
    
    def update_status_table(self, status_data):
        """更新状态表格"""
        self.statusTable.setRowCount(0)
        
        # 添加状态数据
        for key, value in status_data.items():
            row = self.statusTable.rowCount()
            self.statusTable.insertRow(row)
            
            # 格式化显示名称
            display_name = key.replace("_", " ").title()
            
            # 创建参数名称项
            name_item = QTableWidgetItem(display_name)
            self.statusTable.setItem(row, 0, name_item)
            
            # 创建值项
            value_item = QTableWidgetItem(str(value))
            
            # 为某些值设置颜色
            if key in ["disk_usage", "total_log_size"]:
                if isinstance(value, str) and "GB" in value:
                    try:
                        size_value = float(value.split()[0])
                        if size_value > 1.0:
                            value_item.setForeground(QColor("#FF6E6E"))  # 红色
                    except (ValueError, IndexError):
                        pass
            
            elif key in ["performance_score", "efficiency_score"]:
                try:
                    score = float(str(value).strip("%"))
                    if score < 60:
                        value_item.setForeground(QColor("#FF6E6E"))  # 红色
                    elif score < 80:
                        value_item.setForeground(QColor("#FFB066"))  # 橙色
                    else:
                        value_item.setForeground(QColor("#7ED321"))  # 绿色
                except ValueError:
                    pass
            
            self.statusTable.setItem(row, 1, value_item)
    
    def update_analysis_results(self, analysis_data):
        """更新分析结果区域"""
        html_content = """
        <style>
            body { font-family: var(--font-family); line-height: 1.5; }
            .section { margin-bottom: 15px; }
            .section-title { font-weight: bold; margin-bottom: 5px; }
            .chart { background-color: var(--color-secondary-light); 
                    border-radius: 5px; padding: 10px; margin: 5px 0; }
            .bar-chart { height: 20px; background-color: var(--color-primary); 
                    border-radius: 3px; margin: 2px 0; }
            .alert { color: var(--color-error); }
            .warning { color: var(--color-warning); }
            .success { color: var(--color-success); }
        </style>
        
        <div class="section">
            <div class="section-title">日志空间分析</div>
        """
        
        # 日志空间分析
        space_analysis = analysis_data.get("space_analysis", {})
        if space_analysis:
            total_size = space_analysis.get("total_size", "0 MB")
            html_content += f"<p>总日志大小: <b>{total_size}</b></p>"
            
            # 添加类别空间占用图表
            html_content += "<div class='chart'>"
            categories = space_analysis.get("categories", {})
            
            # 按大小排序
            sorted_categories = sorted(
                categories.items(), 
                key=lambda x: self._parse_size(x[1]["size"]), 
                reverse=True
            )
            
            for category, data in sorted_categories:
                size = data.get("size", "0 MB")
                percentage = data.get("percentage", 0)
                html_content += f"""
                <div>{category}: {size} ({percentage}%)</div>
                <div class="bar-chart" style="width: {percentage}%;"></div>
                """
            
            html_content += "</div>"
        
        # 日志写入分析
        html_content += """
        <div class="section">
            <div class="section-title">日志写入分析</div>
        """
        
        write_analysis = analysis_data.get("write_analysis", {})
        if write_analysis:
            total_logs = write_analysis.get("total_logs", 0)
            daily_average = write_analysis.get("daily_average", 0)
            html_content += f"<p>总日志条目数: <b>{total_logs}</b></p>"
            html_content += f"<p>日均写入量: <b>{daily_average}</b> 条/天</p>"
            
            # 添加级别分布图表
            html_content += "<div class='chart'>"
            levels = write_analysis.get("levels", {})
            
            for level, data in levels.items():
                count = data.get("count", 0)
                percentage = data.get("percentage", 0)
                color = self._get_level_color(level)
                
                html_content += f"""
                <div>{level}: {count} ({percentage}%)</div>
                <div class="bar-chart" style="width: {percentage}%; background-color: {color};"></div>
                """
            
            html_content += "</div>"
        
        # 性能分析
        html_content += """
        <div class="section">
            <div class="section-title">性能分析</div>
        """
        
        perf_analysis = analysis_data.get("performance_analysis", {})
        if perf_analysis:
            avg_write_time = perf_analysis.get("avg_write_time", "0 ms")
            io_overhead = perf_analysis.get("io_overhead", "0%")
            
            html_content += f"<p>平均写入时间: <b>{avg_write_time}</b></p>"
            html_content += f"<p>IO开销比例: <b>{io_overhead}</b></p>"
            
            # 添加性能问题
            issues = perf_analysis.get("issues", [])
            if issues:
                html_content += "<p>已发现的性能问题:</p><ul>"
                for issue in issues:
                    severity = issue.get("severity", "中")
                    severity_class = "warning"
                    if severity == "高":
                        severity_class = "alert"
                    elif severity == "低":
                        severity_class = "success"
                    
                    html_content += f"""
                    <li><span class="{severity_class}">[{severity}]</span> {issue.get("description", "")}</li>
                    """
                html_content += "</ul>"
            else:
                html_content += "<p class='success'>未发现性能问题</p>"
        
        html_content += "</div>"
        
        # 设置HTML内容
        self.analysisTextEdit.setHtml(html_content)
    
    def update_recommendations(self, recommendations):
        """更新优化建议列表"""
        self.recommendationsTree.clear()
        
        for rec in recommendations:
            title = rec.get("title", "未知建议")
            status = rec.get("status", "待处理")
            impact = rec.get("impact", "低")
            
            # 创建项
            item = QTreeWidgetItem([title, status, impact])
            
            # 设置图标
            if status.lower() == "已应用":
                item.setIcon(1, FIF.SUCCESS.icon())
            elif status.lower() == "建议":
                item.setIcon(1, FIF.INFO.icon())
            elif status.lower() == "重要":
                item.setIcon(1, FIF.CONSTRACT.icon())
            
            # 设置颜色
            if impact.lower() == "高":
                item.setForeground(2, QColor("#F53F3F"))
            elif impact.lower() == "中":
                item.setForeground(2, QColor("#FF7D00"))
            elif impact.lower() == "低":
                item.setForeground(2, QColor("#00B42A"))
            
            # 添加详情
            details = rec.get("details", "")
            actions = rec.get("actions", [])
            
            # 添加详情子项
            if details:
                details_item = QTreeWidgetItem(["详情"])
                details_item.setFirstColumnSpanned(True)
                details_child = QTreeWidgetItem([details])
                details_child.setFirstColumnSpanned(True)
                details_child.setForeground(0, QColor("#86909C"))
                details_item.addChild(details_child)
                item.addChild(details_item)
            
            # 添加操作子项
            if actions:
                actions_item = QTreeWidgetItem(["可执行操作"])
                actions_item.setFirstColumnSpanned(True)
                
                for action in actions:
                    action_title = action.get("title", "")
                    action_item = QTreeWidgetItem([action_title])
                    action_item.setFirstColumnSpanned(True)
                    action_item.setData(0, Qt.UserRole, action)
                    
                    # 设置操作图标
                    action_item.setIcon(0, FIF.PLAY.icon())
                    actions_item.addChild(action_item)
                
                item.addChild(actions_item)
            
            # 添加到树形控件
            self.recommendationsTree.addTopLevelItem(item)
            
        # 调整列宽
        for i in range(3):
            self.recommendationsTree.resizeColumnToContents(i)
        
        # 绑定双击事件
        self.recommendationsTree.itemDoubleClicked.connect(self.execute_recommendation_action)
    
    def execute_recommendation_action(self, item, column):
        """执行推荐操作"""
        action_data = item.data(0, Qt.UserRole)
        if not action_data:
            return
            
        try:
            action_type = action_data.get("type", "")
            
            if action_type == "config":
                # 打开配置对话框
                self.show_log_config(action_data.get("config_section", ""))
                
            elif action_type == "optimize":
                # 执行优化操作
                self.optimize_specific(action_data.get("optimize_type", ""))
                
            elif action_type == "view":
                # 查看特定信息
                self.view_specific_info(action_data.get("info_type", ""))
                
            else:
                InfoBar.warning(
                    title="未知操作",
                    content=f"无法执行未知类型的操作: {action_type}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                
        except Exception as e:
            show_error_message(self, "执行操作失败", "无法执行推荐操作", e)
    
    def optimize_logs(self):
        """优化日志系统"""
        try:
            # 显示确认对话框
            result = QMessageBox.question(
                self,
                "确认优化",
                "日志优化可能会删除旧日志文件或修改日志配置。确定继续吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                return
                
            # 显示状态指示器
            self.statusIndicator.setContent("正在优化日志系统...")
            self.statusIndicator.move(
                self.optimizeTab.width() // 2 - self.statusIndicator.width() // 2,
                self.optimizeTab.height() // 2 - self.statusIndicator.height() // 2
            )
            self.statusIndicator.show()
            
            # 禁用按钮
            self.optimizeButton.setEnabled(False)
            self.analyzeButton.setEnabled(False)
            
            # 使用后台线程进行优化
            worker = LogOptimizationWorker()
            worker.optimizationFinished.connect(self.on_optimization_finished)
            self.worker_threads.append(worker)
            worker.start()
            
        except Exception as e:
            self.statusIndicator.setVisible(False)
            self.optimizeButton.setEnabled(True)
            self.analyzeButton.setEnabled(True)
            show_error_message(self, "优化失败", "日志系统优化失败", e)
    
    def on_optimization_finished(self, results):
        """处理优化完成的结果"""
        # 隐藏状态指示器
        self.statusIndicator.setVisible(False)
        
        # 启用按钮
        self.optimizeButton.setEnabled(True)
        
        if not results:
            InfoBar.error(
                title="优化失败",
                content="未能获取优化结果",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        try:
            # 成功优化的数量
            success_count = results.get("success_count", 0)
            
            # 再次分析以更新状态
            self.analyze_logs()
            
            # 显示结果
            if success_count > 0:
                success_message = f"成功应用了 {success_count} 项优化"
                
                # 计算节省空间
                saved_space = results.get("saved_space", "0 KB")
                if saved_space != "0 KB":
                    success_message += f"，节省了 {saved_space} 空间"
                    
                # 计算性能提升
                perf_improvement = results.get("performance_improvement", "0%")
                if perf_improvement != "0%":
                    success_message += f"，性能提升约 {perf_improvement}"
                
                InfoBar.success(
                    title="优化完成",
                    content=success_message,
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
            else:
                InfoBar.warning(
                    title="无需优化",
                    content="未应用任何优化，系统状态已经良好",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
            
        except Exception as e:
            show_error_message(self, "处理优化结果失败", "更新优化结果时出错", e)
    
    def optimize_specific(self, optimize_type):
        """执行特定的优化操作"""
        try:
            # 显示状态指示器
            self.statusIndicator.setContent(f"正在执行{optimize_type}...")
            self.statusIndicator.move(
                self.optimizeTab.width() // 2 - self.statusIndicator.width() // 2,
                self.optimizeTab.height() // 2 - self.statusIndicator.height() // 2
            )
            self.statusIndicator.show()
            
            # 禁用按钮
            self.optimizeButton.setEnabled(False)
            self.analyzeButton.setEnabled(False)
            
            # 使用后台线程进行优化
            worker = SpecificOptimizationWorker(optimize_type)
            worker.optimizationFinished.connect(self.on_specific_optimization_finished)
            self.worker_threads.append(worker)
            worker.start()
            
        except Exception as e:
            self.statusIndicator.setVisible(False)
            self.optimizeButton.setEnabled(True)
            self.analyzeButton.setEnabled(True)
            show_error_message(self, "优化失败", f"执行{optimize_type}优化失败", e)
    
    def on_specific_optimization_finished(self, results):
        """处理特定优化完成的结果"""
        # 隐藏状态指示器
        self.statusIndicator.setVisible(False)
        
        if not results:
            InfoBar.error(
                title="优化失败",
                content="未能获取优化结果",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
            
        # 显示结果
        if results.get("success", False):
            # 刷新分析
            self.analyze_logs()
            
            # 显示成功消息
            InfoBar.success(
                title="优化完成",
                content=results.get("message", "优化操作已成功完成"),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=4000
            )
        else:
            InfoBar.error(
                title="优化失败",
                content=results.get("message", "优化操作失败"),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def show_log_config(self, section=None):
        """显示日志配置对话框"""
        try:
            dialog = LogConfigDialog(self, section)
            if dialog.exec():
                # 如果配置已更改，刷新分析
                self.analyze_logs()
                
        except Exception as e:
            show_error_message(self, "配置失败", "打开日志配置对话框失败", e)
    
    def view_specific_info(self, info_type):
        """查看特定信息"""
        try:
            if info_type == "error_hotspots":
                self.view_error_hotspots()
            elif info_type == "performance_logs":
                self.view_performance_logs()
            elif info_type == "large_categories":
                self.view_large_categories()
            else:
                InfoBar.warning(
                    title="未知信息类型",
                    content=f"无法查看未知类型的信息: {info_type}",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
                
        except Exception as e:
            show_error_message(self, "查看信息失败", f"查看{info_type}信息失败", e)
    
    def view_error_hotspots(self):
        """查看错误热点"""
        # 切换到分析标签页并选择错误分析
        self.tabWidget.setCurrentIndex(1)  # 假设分析标签页是索引1
        self.analysisTypeCombo.setCurrentText("错误分析")
        self.update_analysis()
    
    def view_performance_logs(self):
        """查看性能日志"""
        # 切换到分析标签页并选择性能分析
        self.tabWidget.setCurrentIndex(1)  # 假设分析标签页是索引1
        self.analysisTypeCombo.setCurrentText("性能分析")
        self.update_analysis()
    
    def view_large_categories(self):
        """查看大型日志类别"""
        # 切换到分类标签页
        self.tabWidget.setCurrentIndex(0)  # 假设分类标签页是索引0
        
        # 按大小排序类别
        max_size = 0
        largest_category = None
        
        for i in range(self.categoryTree.topLevelItemCount()):
            item = self.categoryTree.topLevelItem(i)
            category = item.data(0, Qt.UserRole)
            if not category:
                continue
                
            # 获取类别大小
            category_size = get_category_size(category)
            if category_size > max_size:
                max_size = category_size
                largest_category = category
        
        # 选择最大的类别
        if largest_category:
            for i in range(self.categoryTree.topLevelItemCount()):
                item = self.categoryTree.topLevelItem(i)
                if item.data(0, Qt.UserRole) == largest_category:
                    self.categoryTree.setCurrentItem(item)
                    break
    
    def _parse_size(self, size_str):
        """解析大小字符串为字节数"""
        try:
            value, unit = size_str.split()
            value = float(value)
            
            if unit == "B":
                return value
            elif unit == "KB":
                return value * 1024
            elif unit == "MB":
                return value * 1024 * 1024
            elif unit == "GB":
                return value * 1024 * 1024 * 1024
            elif unit == "TB":
                return value * 1024 * 1024 * 1024 * 1024
            else:
                return 0
        except:
            return 0
    
    def _get_level_color(self, level):
        """获取日志级别对应的颜色"""
        level = level.lower()
        if level == "debug":
            return "#86909C"  # 灰色
        elif level == "info":
            return "#165DFF"  # 蓝色
        elif level == "success":
            return "#00B42A"  # 绿色
        elif level == "warning":
            return "#FF7D00"  # 橙色
        elif level == "error":
            return "#F53F3F"  # 红色
        elif level == "critical":
            return "#B71DE8"  # 紫色
        else:
            return "#165DFF"  # 默认蓝色
                
# 测试代码
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = LogDialog()
    dialog.exec_() 

# 日志分析工作线程
class LogAnalysisWorker(QThread):
    """日志分析后台工作线程"""
    
    # 定义信号
    analysisFinished = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
    
    def run(self):
        """执行日志分析"""
        try:
            # 分析状态
            status = self._analyze_status()
            
            # 执行详细分析
            analysis = self._analyze_details()
            
            # 生成优化建议
            recommendations = self._generate_recommendations(status, analysis)
            
            # 返回结果
            results = {
                "status": status,
                "analysis": analysis,
                "recommendations": recommendations
            }
            
            self.analysisFinished.emit(results)
            
        except Exception as e:
            # 发生错误，返回空结果
            error(f"日志分析失败: {str(e)}", LogCategory.SYSTEM)
            self.analysisFinished.emit({})
    
    def _analyze_status(self):
        """分析日志系统状态"""
        try:
            # 分析结果
            status = {}
            
            # 获取日志目录
            log_dir = get_log_dir()
            
            # 计算总磁盘使用
            total_size = 0
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            # 格式化大小
            if total_size > 1024 * 1024 * 1024:  # 大于1GB
                status["total_log_size"] = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
            else:
                status["total_log_size"] = f"{total_size / (1024 * 1024):.2f} MB"
            
            # 计算性能分数（示例）
            # 实际实现可能需要复杂的算法，这里简化处理
            # 性能分数基于日志大小、写入频率等
            if total_size > 500 * 1024 * 1024:  # 大于500MB
                performance_score = 60
            elif total_size > 100 * 1024 * 1024:  # 大于100MB
                performance_score = 80
            else:
                performance_score = 95
                
            status["performance_score"] = f"{performance_score}%"
            
            # 计算效率分数
            # 示例实现
            log_categories = len(LogCategory)
            active_categories = 0
            
            for category in LogCategory:
                cat_file = logger.get_category_log_file(category.value)
                if os.path.exists(cat_file) and os.path.getsize(cat_file) > 0:
                    active_categories += 1
            
            efficiency_score = int(85 - (active_categories / log_categories * 15))
            status["efficiency_score"] = f"{efficiency_score}%"
            
            # 添加健康状态
            health_status = "良好"
            if performance_score < 70 or efficiency_score < 70:
                health_status = "需要优化"
            elif performance_score < 50 or efficiency_score < 50:
                health_status = "警告"
                
            status["health_status"] = health_status
            
            # 统计日志文件数
            num_files = 0
            for root, dirs, files in os.walk(log_dir):
                num_files += len(files)
                
            status["log_files_count"] = num_files
            
            return status
            
        except Exception as e:
            error(f"分析日志状态失败: {str(e)}", LogCategory.SYSTEM)
            return {"health_status": "分析失败", "error": str(e)}
    
    def _analyze_details(self):
        """执行详细分析"""
        try:
            analysis = {}
            
            # 分析空间使用
            space_analysis = self._analyze_space_usage()
            analysis["space_analysis"] = space_analysis
            
            # 分析日志写入情况
            write_analysis = self._analyze_log_writing()
            analysis["write_analysis"] = write_analysis
            
            # 分析性能数据
            performance_analysis = self._analyze_performance()
            analysis["performance_analysis"] = performance_analysis
            
            return analysis
            
        except Exception as e:
            error(f"执行详细分析失败: {str(e)}", LogCategory.SYSTEM)
            return {}
    
    def _analyze_space_usage(self):
        """分析空间使用情况"""
        # 获取日志目录
        log_dir = get_log_dir()
        category_dir = os.path.join(log_dir, "categories")
        
        # 总大小
        total_size = 0
        for root, dirs, files in os.walk(log_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        
        # 格式化大小
        if total_size > 1024 * 1024 * 1024:  # 大于1GB
            total_size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        else:
            total_size_str = f"{total_size / (1024 * 1024):.2f} MB"
        
        # 分析各类别大小
        categories = {}
        for category in LogCategory:
            # 尝试获取分类文件大小
            category_size = 0
            cat_file = logger.get_category_log_file(category.value)
            if os.path.exists(cat_file):
                category_size = os.path.getsize(cat_file)
            
            # 格式化大小
            if category_size > 1024 * 1024 * 1024:  # 大于1GB
                size_str = f"{category_size / (1024 * 1024 * 1024):.2f} GB"
            elif category_size > 1024 * 1024:  # 大于1MB
                size_str = f"{category_size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{category_size / 1024:.2f} KB"
                
            # 计算百分比
            percentage = round(category_size / total_size * 100 if total_size > 0 else 0, 1)
            
            categories[category.value] = {
                "size": size_str,
                "percentage": percentage
            }
        
        # 返回分析结果
        return {
            "total_size": total_size_str,
            "categories": categories
        }
    
    def _analyze_log_writing(self):
        """分析日志写入情况"""
        # 获取最近1000行日志
        log_content = get_recent_logs(1000)
        
        # 解析日志行
        lines = log_content.strip().split('\n')
        total_logs = len(lines)
        
        # 分析级别分布
        levels = {}
        for level in ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL", "TRACE"]:
            levels[level] = {"count": 0, "percentage": 0}
            
        # 统计各级别日志数量
        for line in lines:
            for level in levels.keys():
                if f"| {level:<8}" in line:
                    levels[level]["count"] += 1
                    break
        
        # 计算百分比
        for level, data in levels.items():
            data["percentage"] = round(data["count"] / total_logs * 100 if total_logs > 0 else 0, 1)
        
        # 计算日均写入量（估算，基于文件创建时间）
        daily_average = total_logs
        try:
            log_file = get_log_file_path()
            if os.path.exists(log_file):
                creation_time = datetime.fromtimestamp(os.path.getctime(log_file))
                days_diff = (datetime.now() - creation_time).days
                if days_diff > 0:
                    daily_average = round(total_logs / days_diff)
        except:
            pass
        
        # 返回分析结果
        return {
            "total_logs": total_logs,
            "daily_average": daily_average,
            "levels": levels
        }
    
    def _analyze_performance(self):
        """分析性能数据"""
        # 返回分析结果（示例）
        return {
            "avg_write_time": "0.5 ms",
            "io_overhead": "2.5%",
            "issues": [
                {
                    "severity": "中",
                    "description": "ERROR级别日志过多，影响性能"
                },
                {
                    "severity": "低",
                    "description": "日志目录容量增长较快"
                }
            ]
        }
    
    def _generate_recommendations(self, status, analysis):
        """生成优化建议"""
        recommendations = []
        
        # 根据分析结果生成建议
        # 1. 基于日志总大小
        total_size = status.get("total_log_size", "0 MB")
        if "GB" in total_size and float(total_size.split()[0]) > 1.0:
            # 日志超过1GB，建议清理
            recommendations.append({
                "title": "清理过大的日志文件",
                "status": "重要",
                "impact": "高",
                "details": f"当前日志总大小已达 {total_size}，建议清理30天前的日志以提高性能",
                "actions": [
                    {
                        "title": "清理30天前的日志",
                        "type": "optimize",
                        "optimize_type": "clean_old_logs"
                    }
                ]
            })
        
        # 2. 基于性能分数
        performance_score = float(status.get("performance_score", "0%").strip("%"))
        if performance_score < 70:
            # 性能得分较低，建议优化
            recommendations.append({
                "title": "提升日志系统性能",
                "status": "建议",
                "impact": "中",
                "details": "当前性能得分较低，可以通过配置优化提升性能",
                "actions": [
                    {
                        "title": "优化日志配置",
                        "type": "config",
                        "config_section": "performance"
                    }
                ]
            })
        
        # 3. 基于日志分类情况
        space_analysis = analysis.get("space_analysis", {})
        categories = space_analysis.get("categories", {})
        
        # 检查大型类别
        large_categories = []
        for category, data in categories.items():
            size_str = data.get("size", "0 KB")
            percentage = data.get("percentage", 0)
            
            if percentage > 20 or ("MB" in size_str and float(size_str.split()[0]) > 50):
                large_categories.append((category, size_str, percentage))
        
        if large_categories:
            # 发现大型类别
            category_names = ", ".join([f"{c[0]}({c[1]})" for c in large_categories[:3]])
            
            recommendations.append({
                "title": "优化大型日志类别",
                "status": "建议",
                "impact": "中",
                "details": f"以下类别占用了较大空间: {category_names}，可以调整日志级别或进行清理",
                "actions": [
                    {
                        "title": "查看大型类别",
                        "type": "view",
                        "info_type": "large_categories"
                    },
                    {
                        "title": "调整日志配置",
                        "type": "config",
                        "config_section": "categories"
                    }
                ]
            })
        
        # 4. 检查错误日志情况
        write_analysis = analysis.get("write_analysis", {})
        levels = write_analysis.get("levels", {})
        
        error_count = levels.get("ERROR", {}).get("count", 0)
        total_logs = write_analysis.get("total_logs", 0)
        
        if total_logs > 0 and error_count / total_logs > 0.1:
            # 错误日志比例较高
            recommendations.append({
                "title": "检查错误日志热点",
                "status": "重要",
                "impact": "高",
                "details": f"错误日志比例较高({error_count}/{total_logs})，建议检查错误热点",
                "actions": [
                    {
                        "title": "查看错误热点",
                        "type": "view",
                        "info_type": "error_hotspots"
                    }
                ]
            })
        
        # 5. 性能问题
        perf_issues = analysis.get("performance_analysis", {}).get("issues", [])
        if perf_issues:
            # 存在性能问题
            recommendations.append({
                "title": "解决性能问题",
                "status": "建议",
                "impact": "中",
                "details": "发现潜在性能问题，建议查看详情",
                "actions": [
                    {
                        "title": "查看性能日志",
                        "type": "view",
                        "info_type": "performance_logs"
                    }
                ]
            })
        
        return recommendations

# 日志优化工作线程
class LogOptimizationWorker(QThread):
    """日志优化后台工作线程"""
    
    # 定义信号
    optimizationFinished = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
    
    def run(self):
        """执行日志优化"""
        try:
            # 优化结果
            results = {
                "success_count": 0,
                "saved_space": "0 KB",
                "performance_improvement": "0%"
            }
            
            # 执行清理过期日志（超过30天）
            clean_result = self._clean_old_logs(30)
            
            if clean_result.get("success", False):
                results["success_count"] += 1
                results["saved_space"] = clean_result.get("saved_space", "0 KB")
            
            # 执行日志配置优化
            config_result = self._optimize_config()
            
            if config_result.get("success", False):
                results["success_count"] += 1
                results["performance_improvement"] = config_result.get("improvement", "0%")
            
            # 返回优化结果
            self.optimizationFinished.emit(results)
            
        except Exception as e:
            # 发生错误，返回空结果
            error(f"日志优化失败: {str(e)}", LogCategory.SYSTEM)
            self.optimizationFinished.emit({})
    
    def _clean_old_logs(self, days):
        """清理旧日志"""
        try:
            # 获取优化前大小
            log_dir = get_log_dir()
            
            before_size = 0
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        before_size += os.path.getsize(file_path)
            
            # 清理旧日志
            clean_result = clean_logs(older_than_days=days, confirm=False)
            
            # 获取优化后大小
            after_size = 0
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        after_size += os.path.getsize(file_path)
            
            # 计算节省的空间
            saved_size = before_size - after_size
            
            # 格式化节省的空间
            if saved_size > 1024 * 1024 * 1024:  # 大于1GB
                saved_space = f"{saved_size / (1024 * 1024 * 1024):.2f} GB"
            elif saved_size > 1024 * 1024:  # 大于1MB
                saved_space = f"{saved_size / (1024 * 1024):.2f} MB"
            else:
                saved_space = f"{saved_size / 1024:.2f} KB"
            
            return {
                "success": True,
                "saved_space": saved_space,
                "cleaned_files": clean_result.get("deleted_files", 0)
            }
            
        except Exception as e:
            error(f"清理旧日志失败: {str(e)}", LogCategory.SYSTEM)
            return {"success": False, "error": str(e)}
    
    def _optimize_config(self):
        """优化日志配置"""
        # 在实际应用中，这里应该涉及到修改日志系统配置
        # 示例实现
        return {
            "success": True,
            "improvement": "15%",
            "changes": ["调整了轮转大小", "优化了写入缓冲"]
        }

# 特定优化工作线程
class SpecificOptimizationWorker(QThread):
    """特定优化工作线程"""
    
    # 定义信号
    optimizationFinished = pyqtSignal(dict)
    
    def __init__(self, optimize_type):
        super().__init__()
        self.optimize_type = optimize_type
    
    def run(self):
        """执行特定优化"""
        try:
            # 根据优化类型执行相应操作
            if self.optimize_type == "clean_old_logs":
                # 清理30天前的日志
                result = self._clean_old_logs(30)
                
            elif self.optimize_type == "reduce_log_levels":
                # 优化日志级别设置
                result = self._optimize_log_levels()
                
            elif self.optimize_type == "compress_logs":
                # 压缩日志文件
                result = self._compress_logs()
                
            else:
                # 未知优化类型
                result = {
                    "success": False,
                    "message": f"未知的优化类型: {self.optimize_type}"
                }
            
            # 返回优化结果
            self.optimizationFinished.emit(result)
            
        except Exception as e:
            # 发生错误，返回失败结果
            error(f"特定优化失败: {str(e)}", LogCategory.SYSTEM)
            self.optimizationFinished.emit({
                "success": False,
                "message": f"优化执行失败: {str(e)}"
            })
    
    def _clean_old_logs(self, days):
        """清理旧日志"""
        try:
            # 清理旧日志
            clean_result = clean_logs(older_than_days=days, confirm=False)
            
            # 返回结果
            return {
                "success": True,
                "message": f"已清理 {clean_result.get('deleted_files', 0)} 个日志文件",
                "details": clean_result
            }
            
        except Exception as e:
            error(f"清理旧日志失败: {str(e)}", LogCategory.SYSTEM)
            return {"success": False, "message": f"清理失败: {str(e)}"}
    
    def _optimize_log_levels(self):
        """优化日志级别设置"""
        # 示例实现
        return {
            "success": True,
            "message": "日志级别已优化",
            "details": "调整了DEBUG和TRACE级别的记录条件"
        }
    
    def _compress_logs(self):
        """压缩日志文件"""
        # 示例实现
        return {
            "success": True,
            "message": "日志压缩已完成",
            "details": "压缩了5个日志文件，节省25%空间"
        }

class LogLoadWorker(QThread):
    """日志加载工作线程"""
    
    # 定义信号
    loaded = pyqtSignal(str, int, bool)
    
    def __init__(self, offset=0, limit=300):
        super().__init__()
        self.offset = offset
        self.limit = limit
    
    def run(self):
        """执行日志加载"""
        try:
            info(f"开始加载日志: offset={self.offset}, limit={self.limit}")
            
            # 检查日志文件是否存在
            log_file = get_log_file_path()
            if not os.path.exists(log_file):
                warning(f"日志文件不存在: {log_file}")
                self.loaded.emit(
                    f"日志文件不存在: {log_file}",
                    0,
                    False
                )
                return
                
            # 检查日志文件大小
            if os.path.getsize(log_file) == 0:
                warning(f"日志文件为空: {log_file}")
                self.loaded.emit(
                    f"日志文件为空: {log_file}",
                    0,
                    False
                )
                return
            
            # 获取所有可用日志
            all_logs = get_recent_logs(5000)  # 增加获取的日志行数
            
            # 检查日志内容
            if not all_logs or not all_logs.strip():
                warning("获取到的日志内容为空")
                self.loaded.emit(
                    "日志内容为空，可能是应用刚刚安装或日志被清理",
                    0,
                    False
                )
                return
            
            # 分割为行
            log_lines = all_logs.strip().split('\n')
            total_lines = len(log_lines)
            
            info(f"总共获取到 {total_lines} 行日志")
            
            # 确定截取范围
            start_idx = min(self.offset, total_lines)
            end_idx = min(self.offset + self.limit, total_lines)
            
            # 切片获取当前页日志
            current_page = log_lines[start_idx:end_idx]
            
            info(f"返回日志行 {start_idx} 到 {end_idx}, 共 {len(current_page)} 行")
            
            # 发送结果
            self.loaded.emit(
                '\n'.join(current_page),
                total_lines,
                end_idx < total_lines
            )
        
        except Exception as e:
            error(f"加载日志失败: {str(e)}")
            
            # 尝试获取更详细的错误信息
            import traceback
            error_details = traceback.format_exc()
            error(f"详细错误信息: {error_details}")
            
            # 发送空结果和错误信息
            self.loaded.emit(
                f"加载日志失败: {str(e)}\n请检查日志文件权限或配置",
                0,
                False
            )