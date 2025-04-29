#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from qfluentwidgets import setTheme, Theme

# 用户定义的深色主题颜色
DARK_BG_COLOR = "#1f1f1f"       # 背景颜色
DARK_SECONDARY_BG = "#3b3b3b"   # 次级背景颜色
DARK_MENU_BAR_COLOR = "#4b5b6c" # 菜单栏颜色
DARK_FONT_COLOR = "#ffffff"     # 字体颜色 (修改为白色)
DARK_BUTTON_COLOR = "#6d7e8d"   # 按钮颜色
DARK_EDITOR_BG = "#2c3e50"      # 输入框背景色 (灰蓝色)

def apply_custom_dark_theme(app):
    """应用自定义深色主题

    Args:
        app: QApplication 实例
    """
    # 首先应用PyQt-Fluent-Widgets的深色主题
    setTheme(Theme.DARK)
    
    # 创建全局调色板
    palette = QPalette()
    
    # 设置主背景色
    palette.setColor(QPalette.Window, QColor(DARK_BG_COLOR))
    palette.setColor(QPalette.Base, QColor(DARK_BG_COLOR))
    
    # 设置次级背景色
    palette.setColor(QPalette.AlternateBase, QColor(DARK_SECONDARY_BG))
    palette.setColor(QPalette.ToolTipBase, QColor(DARK_SECONDARY_BG))
    
    # 设置文字颜色
    palette.setColor(QPalette.WindowText, QColor(DARK_FONT_COLOR))
    palette.setColor(QPalette.Text, QColor(DARK_FONT_COLOR))
    palette.setColor(QPalette.ToolTipText, QColor(DARK_FONT_COLOR))
    
    # 设置按钮颜色
    palette.setColor(QPalette.Button, QColor(DARK_BUTTON_COLOR))
    palette.setColor(QPalette.ButtonText, QColor(DARK_FONT_COLOR))
    
    # 设置高亮颜色
    palette.setColor(QPalette.Highlight, QColor(DARK_MENU_BAR_COLOR))
    palette.setColor(QPalette.HighlightedText, QColor(DARK_FONT_COLOR))
    
    # 应用调色板
    app.setPalette(palette)
    
    # 添加全局SVG图标颜色过滤器，使黑色图标变为白色
    app.setStyleSheet(f"""
        QToolButton QIcon {{
            color: {DARK_FONT_COLOR};
        }}
        
        QToolBar QToolButton {{
            color: {DARK_FONT_COLOR};
        }}
        
        QToolButton:disabled {{
            color: #888888;
        }}
        
        /* 确保SVG图标显示为白色 */
        QPushButton, QToolButton {{
            qproperty-iconColor: {DARK_FONT_COLOR};
        }}
    """)
    
    # 返回全局QSS样式
    return get_dark_qss()

def get_dark_qss():
    """获取深色主题的QSS样式表"""
    
    return f"""
    /* 全局样式 */
    QWidget {{
        background-color: {DARK_BG_COLOR};
        color: {DARK_FONT_COLOR};
    }}
    
    /* 菜单栏样式 */
    QMenuBar {{
        background-color: {DARK_MENU_BAR_COLOR};
        color: {DARK_FONT_COLOR};
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 10px;
    }}
    
    QMenuBar::item:selected {{
        background-color: #5c6b7c;
    }}
    
    /* 菜单样式 */
    QMenu {{
        background-color: {DARK_SECONDARY_BG};
        border: 1px solid #2d2d2d;
        color: {DARK_FONT_COLOR};
    }}
    
    QMenu::item {{
        padding: 5px 25px 5px 20px;
        background-color: transparent;
    }}
    
    QMenu::item:selected {{
        background-color: {DARK_MENU_BAR_COLOR};
    }}
    
    /* 对话框样式 */
    QDialog {{
        background-color: {DARK_BG_COLOR};
    }}
    
    /* 按钮样式 */
    QPushButton {{
        background-color: {DARK_BUTTON_COLOR};
        color: {DARK_FONT_COLOR};
        border: none;
        padding: 5px 15px;
        border-radius: 4px;
    }}
    
    QPushButton:hover {{
        background-color: #7d8e9d;
    }}
    
    QPushButton:pressed {{
        background-color: #5d6e7d;
    }}
    
    /* 工具栏样式 */
    QToolBar {{
        background-color: {DARK_SECONDARY_BG};
        border: none;
        spacing: 3px;
    }}
    
    /* 工具栏按钮样式 */
    QToolButton {{
        background-color: transparent;
        border: none;
    }}
    
    QToolButton:hover {{
        background-color: {DARK_MENU_BAR_COLOR};
        border-radius: 3px;
    }}
    
    QToolButton:pressed {{
        background-color: #5d6e7d;
    }}
    
    /* 确保工具栏图标为白色 */
    QToolButton QIcon {{
        color: {DARK_FONT_COLOR};
    }}
    
    /* 输入框和编辑器样式 */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {DARK_EDITOR_BG};
        color: {DARK_FONT_COLOR};
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 2px;
    }}
    
    /* 下拉框样式 */
    QComboBox {{
        background-color: {DARK_SECONDARY_BG};
        color: {DARK_FONT_COLOR};
        border: 1px solid #555555;
        padding: 1px 18px 1px 3px;
        border-radius: 3px;
    }}
    
    QComboBox:editable {{
        background-color: {DARK_SECONDARY_BG};
    }}
    
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left: 1px solid #555555;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {DARK_SECONDARY_BG};
        color: {DARK_FONT_COLOR};
        selection-background-color: {DARK_MENU_BAR_COLOR};
    }}
    
    /* 标签页样式 */
    QTabWidget::pane {{
        border: 1px solid #555555;
        background-color: {DARK_BG_COLOR};
    }}
    
    QTabBar::tab {{
        background-color: {DARK_SECONDARY_BG};
        color: {DARK_FONT_COLOR};
        padding: 5px 10px;
        border: 1px solid #555555;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {DARK_MENU_BAR_COLOR};
    }}
    
    /* 滚动条样式 */
    QScrollBar:vertical {{
        background-color: {DARK_BG_COLOR};
        width: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {DARK_SECONDARY_BG};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {DARK_MENU_BAR_COLOR};
    }}
    
    QScrollBar:horizontal {{
        background-color: {DARK_BG_COLOR};
        height: 12px;
        margin: 0px;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {DARK_SECONDARY_BG};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {DARK_MENU_BAR_COLOR};
    }}
    
    /* 去除滚动条上下按钮 */
    QScrollBar::add-line, QScrollBar::sub-line {{
        background: none;
        border: none;
    }}
    
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: none;
    }}
    
    /* 分割线样式 */
    QSplitter::handle {{
        background-color: {DARK_SECONDARY_BG};
    }}
    
    /* 状态栏样式 */
    QStatusBar {{
        background-color: {DARK_SECONDARY_BG};
        color: {DARK_FONT_COLOR};
    }}
    
    /* 文本框样式 */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {DARK_EDITOR_BG};
        color: {DARK_FONT_COLOR};
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 2px;
    }}
    
    /* 列表和树形视图 */
    QListView, QTreeView, QTableView {{
        background-color: {DARK_EDITOR_BG};
        alternate-background-color: {DARK_SECONDARY_BG};
        color: {DARK_FONT_COLOR};
        border: 1px solid #555555;
    }}
    
    QListView::item:selected, QTreeView::item:selected, QTableView::item:selected {{
        background-color: {DARK_MENU_BAR_COLOR};
    }}
    """ 