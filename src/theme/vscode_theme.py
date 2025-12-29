#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VSCode风格主题
定义了仿照VSCode的深色和浅色主题配色方案
"""

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

# VSCode深色主题配色
class VSCodeDarkTheme:
    """VSCode深色主题配色方案"""
    
    # 主要背景色
    EDITOR_BG = "#1E1E1E"              # 编辑器背景
    SIDEBAR_BG = "#252526"             # 侧边栏背景
    ACTIVITYBAR_BG = "#333333"         # 活动栏背景
    STATUSBAR_BG = "#007ACC"           # 状态栏背景
    TITLEBAR_BG = "#3C3C3C"            # 标题栏背景
    PANEL_BG = "#1E1E1E"               # 面板背景
    
    # 边框和分隔线
    BORDER = "#454545"                 # 边框颜色
    SEPARATOR = "#454545"              # 分隔线颜色
    
    # 文本颜色
    TEXT_PRIMARY = "#CCCCCC"           # 主要文本
    TEXT_SECONDARY = "#858585"         # 次要文本
    TEXT_DISABLED = "#656565"          # 禁用文本
    TEXT_LINK = "#3794FF"              # 链接文本
    
    # 选择和高亮
    SELECTION_BG = "#264F78"           # 选中背景
    SELECTION_INACTIVE = "#3A3D41"     # 非活动选中
    HIGHLIGHT = "#007ACC"              # 高亮色
    HIGHLIGHT_HOVER = "#094771"        # 悬停高亮
    
    # 按钮
    BUTTON_BG = "#0E639C"              # 按钮背景
    BUTTON_HOVER = "#1177BB"           # 按钮悬停
    BUTTON_ACTIVE = "#007ACC"          # 按钮按下
    BUTTON_TEXT = "#FFFFFF"            # 按钮文本
    
    # 输入框
    INPUT_BG = "#3C3C3C"               # 输入框背景
    INPUT_BORDER = "#3C3C3C"           # 输入框边框
    INPUT_BORDER_FOCUS = "#007ACC"     # 输入框聚焦边框
    
    # 列表和树
    LIST_HOVER_BG = "#2A2D2E"          # 列表项悬停
    LIST_ACTIVE_BG = "#094771"         # 列表项激活
    LIST_FOCUS_BG = "#062F4A"          # 列表项聚焦
    
    # 滚动条
    SCROLLBAR_BG = "#1E1E1E"           # 滚动条背景
    SCROLLBAR_THUMB = "#424242"        # 滚动条滑块
    SCROLLBAR_THUMB_HOVER = "#4F4F4F"  # 滚动条滑块悬停
    
    # 错误和警告
    ERROR = "#F48771"                  # 错误色
    WARNING = "#CCA700"                # 警告色
    INFO = "#75BEFF"                   # 信息色
    SUCCESS = "#89D185"                # 成功色
    
    # Git颜色
    GIT_ADDED = "#587C0C"              # Git添加
    GIT_MODIFIED = "#895503"           # Git修改
    GIT_DELETED = "#AD0707"            # Git删除
    GIT_UNTRACKED = "#007ACC"          # Git未跟踪
    GIT_IGNORED = "#8C8C8C"            # Git忽略
    
    # 语法高亮
    SYNTAX_KEYWORD = "#569CD6"         # 关键字
    SYNTAX_STRING = "#CE9178"          # 字符串
    SYNTAX_COMMENT = "#6A9955"         # 注释
    SYNTAX_FUNCTION = "#DCDCAA"        # 函数
    SYNTAX_NUMBER = "#B5CEA8"          # 数字
    SYNTAX_VARIABLE = "#9CDCFE"        # 变量
    SYNTAX_TYPE = "#4EC9B0"            # 类型


# VSCode浅色主题配色
class VSCodeLightTheme:
    """VSCode浅色主题配色方案"""
    
    # 主要背景色
    EDITOR_BG = "#FFFFFF"              # 编辑器背景
    SIDEBAR_BG = "#F3F3F3"             # 侧边栏背景
    ACTIVITYBAR_BG = "#2C2C2C"         # 活动栏背景
    STATUSBAR_BG = "#007ACC"           # 状态栏背景
    TITLEBAR_BG = "#DDDDDD"            # 标题栏背景
    PANEL_BG = "#FFFFFF"               # 面板背景
    
    # 边框和分隔线
    BORDER = "#E5E5E5"                 # 边框颜色
    SEPARATOR = "#E5E5E5"              # 分隔线颜色
    
    # 文本颜色
    TEXT_PRIMARY = "#000000"           # 主要文本
    TEXT_SECONDARY = "#6A6A6A"         # 次要文本
    TEXT_DISABLED = "#AEAEAE"          # 禁用文本
    TEXT_LINK = "#0066BF"              # 链接文本
    
    # 选择和高亮
    SELECTION_BG = "#ADD6FF"           # 选中背景
    SELECTION_INACTIVE = "#E4E6F1"     # 非活动选中
    HIGHLIGHT = "#0078D4"              # 高亮色
    HIGHLIGHT_HOVER = "#B3D6FC"        # 悬停高亮
    
    # 按钮
    BUTTON_BG = "#007ACC"              # 按钮背景
    BUTTON_HOVER = "#0098FF"           # 按钮悬停
    BUTTON_ACTIVE = "#005A9E"          # 按钮按下
    BUTTON_TEXT = "#FFFFFF"            # 按钮文本
    
    # 输入框
    INPUT_BG = "#FFFFFF"               # 输入框背景
    INPUT_BORDER = "#CECECE"           # 输入框边框
    INPUT_BORDER_FOCUS = "#007ACC"     # 输入框聚焦边框
    
    # 列表和树
    LIST_HOVER_BG = "#F0F0F0"          # 列表项悬停
    LIST_ACTIVE_BG = "#0078D4"         # 列表项激活
    LIST_FOCUS_BG = "#D6EBFF"          # 列表项聚焦
    
    # 滚动条
    SCROLLBAR_BG = "#F5F5F5"           # 滚动条背景
    SCROLLBAR_THUMB = "#C2C2C2"        # 滚动条滑块
    SCROLLBAR_THUMB_HOVER = "#A6A6A6"  # 滚动条滑块悬停
    
    # 错误和警告
    ERROR = "#E51400"                  # 错误色
    WARNING = "#BF8803"                # 警告色
    INFO = "#1A85FF"                   # 信息色
    SUCCESS = "#388A34"                # 成功色
    
    # Git颜色
    GIT_ADDED = "#587C0C"              # Git添加
    GIT_MODIFIED = "#895503"           # Git修改
    GIT_DELETED = "#AD0707"            # Git删除
    GIT_UNTRACKED = "#007ACC"          # Git未跟踪
    GIT_IGNORED = "#8C8C8C"            # Git忽略
    
    # 语法高亮
    SYNTAX_KEYWORD = "#0000FF"         # 关键字
    SYNTAX_STRING = "#A31515"          # 字符串
    SYNTAX_COMMENT = "#008000"         # 注释
    SYNTAX_FUNCTION = "#795E26"        # 函数
    SYNTAX_NUMBER = "#098658"          # 数字
    SYNTAX_VARIABLE = "#001080"        # 变量
    SYNTAX_TYPE = "#267F99"            # 类型


def apply_vscode_dark_theme(app: QApplication):
    """应用VSCode深色主题
    
    Args:
        app: QApplication实例
    """
    # 首先应用PyQt-Fluent-Widgets的深色主题作为基础
    setTheme(Theme.DARK)
    
    # 创建自定义调色板
    palette = QPalette()
    
    # 设置主背景色
    palette.setColor(QPalette.Window, QColor(VSCodeDarkTheme.EDITOR_BG))
    palette.setColor(QPalette.Base, QColor(VSCodeDarkTheme.EDITOR_BG))
    palette.setColor(QPalette.AlternateBase, QColor(VSCodeDarkTheme.SIDEBAR_BG))
    
    # 设置文本颜色
    palette.setColor(QPalette.WindowText, QColor(VSCodeDarkTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.Text, QColor(VSCodeDarkTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.BrightText, QColor(VSCodeDarkTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.PlaceholderText, QColor(VSCodeDarkTheme.TEXT_SECONDARY))
    
    # 设置按钮颜色
    palette.setColor(QPalette.Button, QColor(VSCodeDarkTheme.BUTTON_BG))
    palette.setColor(QPalette.ButtonText, QColor(VSCodeDarkTheme.BUTTON_TEXT))
    
    # 设置选择高亮
    palette.setColor(QPalette.Highlight, QColor(VSCodeDarkTheme.SELECTION_BG))
    palette.setColor(QPalette.HighlightedText, QColor(VSCodeDarkTheme.TEXT_PRIMARY))
    
    # 设置链接颜色
    palette.setColor(QPalette.Link, QColor(VSCodeDarkTheme.TEXT_LINK))
    palette.setColor(QPalette.LinkVisited, QColor(VSCodeDarkTheme.TEXT_LINK))
    
    # 应用调色板
    app.setPalette(palette)
    
    # 设置全局样式表
    app.setStyleSheet(get_vscode_dark_stylesheet())


def apply_vscode_light_theme(app: QApplication):
    """应用VSCode浅色主题
    
    Args:
        app: QApplication实例
    """
    # 首先应用PyQt-Fluent-Widgets的浅色主题作为基础
    setTheme(Theme.LIGHT)
    
    # 创建自定义调色板
    palette = QPalette()
    
    # 设置主背景色
    palette.setColor(QPalette.Window, QColor(VSCodeLightTheme.EDITOR_BG))
    palette.setColor(QPalette.Base, QColor(VSCodeLightTheme.EDITOR_BG))
    palette.setColor(QPalette.AlternateBase, QColor(VSCodeLightTheme.SIDEBAR_BG))
    
    # 设置文本颜色
    palette.setColor(QPalette.WindowText, QColor(VSCodeLightTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.Text, QColor(VSCodeLightTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.BrightText, QColor(VSCodeLightTheme.TEXT_PRIMARY))
    palette.setColor(QPalette.PlaceholderText, QColor(VSCodeLightTheme.TEXT_SECONDARY))
    
    # 设置按钮颜色
    palette.setColor(QPalette.Button, QColor(VSCodeLightTheme.BUTTON_BG))
    palette.setColor(QPalette.ButtonText, QColor(VSCodeLightTheme.BUTTON_TEXT))
    
    # 设置选择高亮
    palette.setColor(QPalette.Highlight, QColor(VSCodeLightTheme.SELECTION_BG))
    palette.setColor(QPalette.HighlightedText, QColor(VSCodeLightTheme.TEXT_PRIMARY))
    
    # 设置链接颜色
    palette.setColor(QPalette.Link, QColor(VSCodeLightTheme.TEXT_LINK))
    palette.setColor(QPalette.LinkVisited, QColor(VSCodeLightTheme.TEXT_LINK))
    
    # 应用调色板
    app.setPalette(palette)
    
    # 设置全局样式表
    app.setStyleSheet(get_vscode_light_stylesheet())


def get_vscode_dark_stylesheet() -> str:
    """获取VSCode深色主题样式表
    
    Returns:
        str: CSS样式表字符串
    """
    return f"""
    /* 全局样式 */
    QWidget {{
        background-color: {VSCodeDarkTheme.EDITOR_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        font-family: "Segoe UI", "Microsoft YaHei", "微软雅黑", sans-serif;
        font-size: 13px;
    }}
    
    /* 菜单栏 */
    QMenuBar {{
        background-color: {VSCodeDarkTheme.TITLEBAR_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: none;
        padding: 2px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {VSCodeDarkTheme.LIST_HOVER_BG};
    }}
    
    QMenuBar::item:pressed {{
        background-color: {VSCodeDarkTheme.LIST_ACTIVE_BG};
    }}
    
    /* 菜单 */
    QMenu {{
        background-color: {VSCodeDarkTheme.SIDEBAR_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeDarkTheme.BORDER};
        border-radius: 4px;
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {VSCodeDarkTheme.LIST_HOVER_BG};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {VSCodeDarkTheme.SEPARATOR};
        margin: 4px 0px;
    }}
    
    /* 工具栏 */
    QToolBar {{
        background-color: {VSCodeDarkTheme.TITLEBAR_BG};
        border: none;
        spacing: 4px;
        padding: 4px;
    }}
    
    QToolButton {{
        background-color: transparent;
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: none;
        border-radius: 4px;
        padding: 4px;
    }}
    
    QToolButton:hover {{
        background-color: {VSCodeDarkTheme.LIST_HOVER_BG};
    }}
    
    QToolButton:pressed {{
        background-color: {VSCodeDarkTheme.LIST_ACTIVE_BG};
    }}
    
    /* 按钮 */
    QPushButton {{
        background-color: {VSCodeDarkTheme.BUTTON_BG};
        color: {VSCodeDarkTheme.BUTTON_TEXT};
        border: none;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: {VSCodeDarkTheme.BUTTON_HOVER};
    }}
    
    QPushButton:pressed {{
        background-color: {VSCodeDarkTheme.BUTTON_ACTIVE};
    }}
    
    QPushButton:disabled {{
        background-color: {VSCodeDarkTheme.INPUT_BG};
        color: {VSCodeDarkTheme.TEXT_DISABLED};
    }}
    
    /* 输入框 */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {VSCodeDarkTheme.INPUT_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeDarkTheme.INPUT_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: {VSCodeDarkTheme.SELECTION_BG};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {VSCodeDarkTheme.INPUT_BORDER_FOCUS};
    }}
    
    /* 下拉框 */
    QComboBox {{
        background-color: {VSCodeDarkTheme.INPUT_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeDarkTheme.INPUT_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {VSCodeDarkTheme.INPUT_BORDER_FOCUS};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: url(:/qfluentwidgets/images/icons/ChevronDown_white.svg);
        width: 12px;
        height: 12px;
    }}
    
    /* 列表视图 */
    QListView, QTreeView {{
        background-color: {VSCodeDarkTheme.EDITOR_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: none;
        outline: none;
    }}
    
    QListView::item, QTreeView::item {{
        padding: 4px;
        border-radius: 4px;
    }}
    
    QListView::item:hover, QTreeView::item:hover {{
        background-color: {VSCodeDarkTheme.LIST_HOVER_BG};
    }}
    
    QListView::item:selected, QTreeView::item:selected {{
        background-color: {VSCodeDarkTheme.LIST_ACTIVE_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
    }}
    
    /* 滚动条 */
    QScrollBar:vertical {{
        background-color: {VSCodeDarkTheme.SCROLLBAR_BG};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {VSCodeDarkTheme.SCROLLBAR_THUMB};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {VSCodeDarkTheme.SCROLLBAR_THUMB_HOVER};
    }}
    
    QScrollBar:horizontal {{
        background-color: {VSCodeDarkTheme.SCROLLBAR_BG};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {VSCodeDarkTheme.SCROLLBAR_THUMB};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {VSCodeDarkTheme.SCROLLBAR_THUMB_HOVER};
    }}
    
    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
    }}
    
    /* 分割器 */
    QSplitter::handle {{
        background-color: {VSCodeDarkTheme.BORDER};
    }}
    
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    
    /* 标签页 */
    QTabWidget::pane {{
        border: 1px solid {VSCodeDarkTheme.BORDER};
        background-color: {VSCodeDarkTheme.EDITOR_BG};
    }}
    
    QTabBar::tab {{
        background-color: {VSCodeDarkTheme.TITLEBAR_BG};
        color: {VSCodeDarkTheme.TEXT_SECONDARY};
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    
    QTabBar::tab:selected {{
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border-bottom: 2px solid {VSCodeDarkTheme.HIGHLIGHT};
    }}
    
    QTabBar::tab:hover {{
        background-color: {VSCodeDarkTheme.LIST_HOVER_BG};
    }}
    
    /* 状态栏 */
    QStatusBar {{
        background-color: {VSCodeDarkTheme.STATUSBAR_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: none;
    }}
    
    /* 工具提示 */
    QToolTip {{
        background-color: {VSCodeDarkTheme.SIDEBAR_BG};
        color: {VSCodeDarkTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeDarkTheme.BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """


def get_vscode_light_stylesheet() -> str:
    """获取VSCode浅色主题样式表
    
    Returns:
        str: CSS样式表字符串
    """
    return f"""
    /* 全局样式 */
    QWidget {{
        background-color: {VSCodeLightTheme.EDITOR_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        font-family: "Segoe UI", "Microsoft YaHei", "微软雅黑", sans-serif;
        font-size: 13px;
    }}
    
    /* 菜单栏 */
    QMenuBar {{
        background-color: {VSCodeLightTheme.TITLEBAR_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: none;
        padding: 2px;
    }}
    
    QMenuBar::item {{
        background-color: transparent;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {VSCodeLightTheme.LIST_HOVER_BG};
    }}
    
    QMenuBar::item:pressed {{
        background-color: {VSCodeLightTheme.LIST_ACTIVE_BG};
        color: {VSCodeLightTheme.BUTTON_TEXT};
    }}
    
    /* 菜单 */
    QMenu {{
        background-color: {VSCodeLightTheme.EDITOR_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeLightTheme.BORDER};
        border-radius: 4px;
        padding: 4px;
    }}
    
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {VSCodeLightTheme.LIST_HOVER_BG};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {VSCodeLightTheme.SEPARATOR};
        margin: 4px 0px;
    }}
    
    /* 工具栏 */
    QToolBar {{
        background-color: {VSCodeLightTheme.SIDEBAR_BG};
        border: none;
        spacing: 4px;
        padding: 4px;
    }}
    
    QToolButton {{
        background-color: transparent;
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: none;
        border-radius: 4px;
        padding: 4px;
    }}
    
    QToolButton:hover {{
        background-color: {VSCodeLightTheme.LIST_HOVER_BG};
    }}
    
    QToolButton:pressed {{
        background-color: {VSCodeLightTheme.LIST_ACTIVE_BG};
    }}
    
    /* 按钮 */
    QPushButton {{
        background-color: {VSCodeLightTheme.BUTTON_BG};
        color: {VSCodeLightTheme.BUTTON_TEXT};
        border: none;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: {VSCodeLightTheme.BUTTON_HOVER};
    }}
    
    QPushButton:pressed {{
        background-color: {VSCodeLightTheme.BUTTON_ACTIVE};
    }}
    
    QPushButton:disabled {{
        background-color: {VSCodeLightTheme.SIDEBAR_BG};
        color: {VSCodeLightTheme.TEXT_DISABLED};
    }}
    
    /* 输入框 */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {VSCodeLightTheme.INPUT_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeLightTheme.INPUT_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: {VSCodeLightTheme.SELECTION_BG};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {VSCodeLightTheme.INPUT_BORDER_FOCUS};
    }}
    
    /* 下拉框 */
    QComboBox {{
        background-color: {VSCodeLightTheme.INPUT_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeLightTheme.INPUT_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {VSCodeLightTheme.INPUT_BORDER_FOCUS};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: url(:/qfluentwidgets/images/icons/ChevronDown_black.svg);
        width: 12px;
        height: 12px;
    }}
    
    /* 列表视图 */
    QListView, QTreeView {{
        background-color: {VSCodeLightTheme.SIDEBAR_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: none;
        outline: none;
    }}
    
    QListView::item, QTreeView::item {{
        padding: 4px;
        border-radius: 4px;
    }}
    
    QListView::item:hover, QTreeView::item:hover {{
        background-color: {VSCodeLightTheme.LIST_HOVER_BG};
    }}
    
    QListView::item:selected, QTreeView::item:selected {{
        background-color: {VSCodeLightTheme.LIST_FOCUS_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
    }}
    
    /* 滚动条 */
    QScrollBar:vertical {{
        background-color: {VSCodeLightTheme.SCROLLBAR_BG};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {VSCodeLightTheme.SCROLLBAR_THUMB};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {VSCodeLightTheme.SCROLLBAR_THUMB_HOVER};
    }}
    
    QScrollBar:horizontal {{
        background-color: {VSCodeLightTheme.SCROLLBAR_BG};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {VSCodeLightTheme.SCROLLBAR_THUMB};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {VSCodeLightTheme.SCROLLBAR_THUMB_HOVER};
    }}
    
    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
    }}
    
    /* 分割器 */
    QSplitter::handle {{
        background-color: {VSCodeLightTheme.BORDER};
    }}
    
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    
    /* 标签页 */
    QTabWidget::pane {{
        border: 1px solid {VSCodeLightTheme.BORDER};
        background-color: {VSCodeLightTheme.EDITOR_BG};
    }}
    
    QTabBar::tab {{
        background-color: {VSCodeLightTheme.SIDEBAR_BG};
        color: {VSCodeLightTheme.TEXT_SECONDARY};
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    
    QTabBar::tab:selected {{
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border-bottom: 2px solid {VSCodeLightTheme.HIGHLIGHT};
    }}
    
    QTabBar::tab:hover {{
        background-color: {VSCodeLightTheme.LIST_HOVER_BG};
    }}
    
    /* 状态栏 */
    QStatusBar {{
        background-color: {VSCodeLightTheme.STATUSBAR_BG};
        color: {VSCodeLightTheme.BUTTON_TEXT};
        border: none;
    }}
    
    /* 工具提示 */
    QToolTip {{
        background-color: {VSCodeLightTheme.SIDEBAR_BG};
        color: {VSCodeLightTheme.TEXT_PRIMARY};
        border: 1px solid {VSCodeLightTheme.BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """
