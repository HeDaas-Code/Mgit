#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VSCode风格活动栏组件
实现类似VSCode左侧的垂直图标导航栏
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolButton, 
                            QSpacerItem, QSizePolicy, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QColor
from qfluentwidgets import FluentIcon


class ActivityBarButton(QToolButton):
    """活动栏按钮"""
    
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setIcon(icon.icon() if hasattr(icon, 'icon') else icon)
        self.setToolTip(text)
        self.setIconSize(QSize(28, 28))
        self.setFixedSize(48, 48)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # 活动指示器
        self.indicator = QWidget(self)
        self.indicator.setFixedSize(2, 48)
        self.indicator.hide()
        
    def setChecked(self, checked):
        """设置选中状态"""
        super().setChecked(checked)
        if checked:
            self.indicator.show()
        else:
            self.indicator.hide()
            
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)


class VSCodeActivityBar(QWidget):
    """VSCode风格的活动栏"""
    
    # 信号定义
    explorerClicked = pyqtSignal()
    searchClicked = pyqtSignal()
    sourceControlClicked = pyqtSignal()
    debugClicked = pyqtSignal()
    extensionsClicked = pyqtSignal()
    settingsClicked = pyqtSignal()
    accountClicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = True
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        self.setFixedWidth(48)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)
        
        # 创建按钮
        self.explorerBtn = self._createButton(FluentIcon.FOLDER, "资源管理器 (Ctrl+Shift+E)")
        self.explorerBtn.clicked.connect(self.explorerClicked.emit)
        self.explorerBtn.setChecked(True)
        
        self.searchBtn = self._createButton(FluentIcon.SEARCH, "搜索 (Ctrl+Shift+F)")
        self.searchBtn.clicked.connect(self.searchClicked.emit)
        
        self.sourceControlBtn = self._createButton(FluentIcon.CODE, "源代码管理 (Ctrl+Shift+G)")
        self.sourceControlBtn.clicked.connect(self.sourceControlClicked.emit)
        
        self.debugBtn = self._createButton(FluentIcon.PLAY, "运行和调试 (Ctrl+Shift+D)")
        self.debugBtn.clicked.connect(self.debugClicked.emit)
        
        self.extensionsBtn = self._createButton(FluentIcon.APPLICATION, "扩展 (Ctrl+Shift+X)")
        self.extensionsBtn.clicked.connect(self.extensionsClicked.emit)
        
        # 添加上部按钮
        layout.addWidget(self.explorerBtn)
        layout.addWidget(self.searchBtn)
        layout.addWidget(self.sourceControlBtn)
        layout.addWidget(self.debugBtn)
        layout.addWidget(self.extensionsBtn)
        
        # 弹性空间
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # 底部按钮
        self.accountBtn = self._createButton(FluentIcon.PEOPLE, "账户")
        self.accountBtn.clicked.connect(self.accountClicked.emit)
        
        self.settingsBtn = self._createButton(FluentIcon.SETTING, "设置 (Ctrl+,)")
        self.settingsBtn.clicked.connect(self.settingsClicked.emit)
        
        layout.addWidget(self.accountBtn)
        layout.addWidget(self.settingsBtn)
        
        # 应用主题
        self.applyTheme(self.dark_mode)
        
        # 按钮组管理（互斥选择）
        self.buttons = [
            self.explorerBtn,
            self.searchBtn,
            self.sourceControlBtn,
            self.debugBtn,
            self.extensionsBtn
        ]
        
        for btn in self.buttons:
            btn.clicked.connect(lambda checked, b=btn: self._onButtonClicked(b))
            
    def _createButton(self, icon, tooltip):
        """创建活动栏按钮
        
        Args:
            icon: 图标
            tooltip: 工具提示
            
        Returns:
            ActivityBarButton: 按钮实例
        """
        return ActivityBarButton(icon, tooltip, self)
        
    def _onButtonClicked(self, button):
        """处理按钮点击
        
        Args:
            button: 被点击的按钮
        """
        # 取消其他按钮的选中状态
        for btn in self.buttons:
            if btn != button:
                btn.setChecked(False)
                
    def applyTheme(self, dark_mode):
        """应用主题
        
        Args:
            dark_mode: 是否为深色主题
        """
        self.dark_mode = dark_mode
        
        if dark_mode:
            bg_color = "#333333"
            hover_bg = "#2A2A2A"
            active_bg = "#094771"
            border_color = "#454545"
            indicator_color = "#007ACC"
        else:
            bg_color = "#2C2C2C"
            hover_bg = "#383838"
            active_bg = "#0078D4"
            border_color = "#E5E5E5"
            indicator_color = "#0078D4"
            
        self.setStyleSheet(f"""
            VSCodeActivityBar {{
                background-color: {bg_color};
                border-right: 1px solid {border_color};
            }}
            ActivityBarButton {{
                background-color: transparent;
                border: none;
                border-radius: 0;
            }}
            ActivityBarButton:hover {{
                background-color: {hover_bg};
            }}
            ActivityBarButton:checked {{
                background-color: transparent;
            }}
            ActivityBarButton:pressed {{
                background-color: {active_bg};
            }}
        """)
        
        # 更新指示器样式
        for btn in self.buttons + [self.accountBtn, self.settingsBtn]:
            if hasattr(btn, 'indicator'):
                btn.indicator.setStyleSheet(f"""
                    background-color: {indicator_color};
                """)
                btn.indicator.move(0, 0)
    
    def setActiveView(self, view_name):
        """设置活动视图
        
        Args:
            view_name: 视图名称 ('explorer', 'search', 'source_control', 'debug', 'extensions')
        """
        view_map = {
            'explorer': self.explorerBtn,
            'search': self.searchBtn,
            'source_control': self.sourceControlBtn,
            'debug': self.debugBtn,
            'extensions': self.extensionsBtn
        }
        
        if view_name in view_map:
            button = view_map[view_name]
            for btn in self.buttons:
                btn.setChecked(btn == button)
