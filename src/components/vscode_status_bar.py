#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VSCode风格状态栏组件
实现类似VSCode的底部状态栏，显示各种状态信息
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                            QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor
from qfluentwidgets import FluentIcon


class VSCodeStatusBar(QWidget):
    """VSCode风格的状态栏组件"""
    
    # 信号
    branchClicked = pyqtSignal()
    lineColumnClicked = pyqtSignal()
    encodingClicked = pyqtSignal()
    eolClicked = pyqtSignal()
    languageClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = True
        self.initUI()
        self.setupAnimation()
        
    def initUI(self):
        """初始化UI"""
        self.setFixedHeight(26)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(12)
        
        # 左侧区域
        # Git分支信息
        self.branchButton = self._createStatusButton("", FluentIcon.CODE)
        self.branchButton.clicked.connect(self.branchClicked.emit)
        layout.addWidget(self.branchButton)
        
        # Git状态（添加、修改、删除文件数）
        self.gitStatusLabel = QLabel("")
        self.gitStatusLabel.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.gitStatusLabel)
        
        # 错误和警告
        self.errorWarningLabel = QLabel("")
        self.errorWarningLabel.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.errorWarningLabel)
        
        # 弹性空间
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # 右侧区域
        # 行列号
        self.lineColumnButton = self._createStatusButton("行 1, 列 1")
        self.lineColumnButton.clicked.connect(self.lineColumnClicked.emit)
        layout.addWidget(self.lineColumnButton)
        
        # 缩进信息
        self.indentLabel = QLabel("空格: 4")
        self.indentLabel.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.indentLabel)
        
        # 编码
        self.encodingButton = self._createStatusButton("UTF-8")
        self.encodingButton.clicked.connect(self.encodingClicked.emit)
        layout.addWidget(self.encodingButton)
        
        # 换行符
        self.eolButton = self._createStatusButton("LF")
        self.eolButton.clicked.connect(self.eolClicked.emit)
        layout.addWidget(self.eolButton)
        
        # 语言模式
        self.languageButton = self._createStatusButton("Markdown")
        self.languageButton.clicked.connect(self.languageClicked.emit)
        layout.addWidget(self.languageButton)
        
        # 反馈按钮
        self.feedbackButton = self._createStatusButton("", FluentIcon.FEEDBACK)
        layout.addWidget(self.feedbackButton)
        
        # 通知按钮
        self.notificationButton = self._createStatusButton("", FluentIcon.MESSAGE)
        layout.addWidget(self.notificationButton)
        
        # 应用样式
        self.applyTheme(self.dark_mode)
        
    def _createStatusButton(self, text, icon=None):
        """创建状态栏按钮
        
        Args:
            text: 按钮文本
            icon: 可选的图标
            
        Returns:
            QPushButton: 创建的按钮
        """
        button = QPushButton()
        if icon:
            button.setIcon(icon.icon())
        if text:
            button.setText(text)
        button.setFont(QFont("Segoe UI", 11))
        button.setFlat(True)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 2px 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        return button
        
    def setupAnimation(self):
        """设置动画效果"""
        # 用于淡入淡出效果的动画
        self.fadeAnimation = QPropertyAnimation(self, b"windowOpacity")
        self.fadeAnimation.setDuration(200)
        self.fadeAnimation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def applyTheme(self, dark_mode):
        """应用主题
        
        Args:
            dark_mode: 是否为深色主题
        """
        self.dark_mode = dark_mode
        
        if dark_mode:
            bg_color = "#007ACC"  # VSCode蓝色状态栏
            text_color = "#FFFFFF"
        else:
            bg_color = "#007ACC"
            text_color = "#FFFFFF"
            
        self.setStyleSheet(f"""
            VSCodeStatusBar {{
                background-color: {bg_color};
                border-top: 1px solid rgba(0, 0, 0, 0.2);
            }}
            QLabel {{
                color: {text_color};
                background-color: transparent;
                padding: 0 4px;
            }}
        """)
        
        # 更新按钮样式
        button_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 2px 8px;
                border-radius: 3px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.25);
            }}
        """
        
        # 使用列表推导式应用样式到所有按钮
        all_buttons = [
            self.branchButton, self.lineColumnButton, self.encodingButton,
            self.eolButton, self.languageButton, self.feedbackButton,
            self.notificationButton
        ]
        for button in all_buttons:
            button.setStyleSheet(button_style)
    
    def setBranch(self, branch_name):
        """设置当前分支名称
        
        Args:
            branch_name: 分支名称
        """
        if branch_name:
            self.branchButton.setText(f"  {branch_name}")
            self.branchButton.setVisible(True)
        else:
            self.branchButton.setVisible(False)
    
    def setGitStatus(self, added=0, modified=0, deleted=0):
        """设置Git状态
        
        Args:
            added: 添加的文件数
            modified: 修改的文件数
            deleted: 删除的文件数
        """
        status_parts = []
        if added > 0:
            status_parts.append(f"✚ {added}")
        if modified > 0:
            status_parts.append(f"~ {modified}")
        if deleted > 0:
            status_parts.append(f"✖ {deleted}")
            
        if status_parts:
            self.gitStatusLabel.setText(" ".join(status_parts))
            self.gitStatusLabel.setVisible(True)
        else:
            self.gitStatusLabel.setVisible(False)
    
    def setErrorWarning(self, errors=0, warnings=0):
        """设置错误和警告数量
        
        Args:
            errors: 错误数量
            warnings: 警告数量
        """
        status_parts = []
        if errors > 0:
            status_parts.append(f"✖ {errors}")
        if warnings > 0:
            status_parts.append(f"⚠ {warnings}")
            
        if status_parts:
            self.errorWarningLabel.setText(" ".join(status_parts))
            self.errorWarningLabel.setVisible(True)
        else:
            self.errorWarningLabel.setVisible(False)
    
    def setLineColumn(self, line, column):
        """设置行列号
        
        Args:
            line: 行号
            column: 列号
        """
        self.lineColumnButton.setText(f"行 {line}, 列 {column}")
    
    def setIndent(self, indent_type, size):
        """设置缩进信息
        
        Args:
            indent_type: 缩进类型（'spaces' 或 'tabs'）
            size: 缩进大小
        """
        if indent_type == 'spaces':
            self.indentLabel.setText(f"空格: {size}")
        else:
            self.indentLabel.setText(f"制表符: {size}")
    
    def setEncoding(self, encoding):
        """设置文件编码
        
        Args:
            encoding: 编码名称
        """
        self.encodingButton.setText(encoding.upper())
    
    def setEOL(self, eol_type):
        """设置换行符类型
        
        Args:
            eol_type: 换行符类型（'LF', 'CRLF', 'CR'）
        """
        self.eolButton.setText(eol_type)
    
    def setLanguage(self, language):
        """设置语言模式
        
        Args:
            language: 语言名称
        """
        self.languageButton.setText(language)
    
    def showMessage(self, message, duration=3000):
        """显示临时消息
        
        Args:
            message: 消息文本
            duration: 显示时长（毫秒）
        """
        # 可以添加一个临时标签来显示消息
        pass
