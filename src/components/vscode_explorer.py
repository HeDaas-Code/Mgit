#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VSCode风格文件浏览器扩展
为文件浏览器添加VSCode风格的视觉效果
"""

from PyQt5.QtWidgets import QTreeView, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor


def apply_vscode_style_to_explorer(explorer_widget, dark_mode=True):
    """为文件浏览器应用VSCode风格
    
    Args:
        explorer_widget: 文件浏览器组件
        dark_mode: 是否为深色主题
    """
    if dark_mode:
        bg_color = "#252526"
        text_color = "#CCCCCC"
        hover_bg = "#2A2D2E"
        selected_bg = "#094771"
        border_color = "#454545"
    else:
        bg_color = "#F3F3F3"
        text_color = "#000000"
        hover_bg = "#F0F0F0"
        selected_bg = "#D6EBFF"
        border_color = "#E5E5E5"
    
    style = f"""
    QTreeView {{
        background-color: {bg_color};
        color: {text_color};
        border: none;
        border-right: 1px solid {border_color};
        outline: none;
        show-decoration-selected: 1;
        font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
        font-size: 13px;
    }}
    
    QTreeView::item {{
        padding: 4px 8px;
        border-radius: 4px;
        margin: 1px 4px;
    }}
    
    QTreeView::item:hover {{
        background-color: {hover_bg};
    }}
    
    QTreeView::item:selected {{
        background-color: {selected_bg};
        color: {text_color};
    }}
    
    QTreeView::item:selected:active {{
        background-color: {selected_bg};
    }}
    
    QTreeView::item:selected:!active {{
        background-color: {hover_bg};
    }}
    
    QTreeView::branch {{
        background: transparent;
    }}
    
    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children:has-siblings {{
        border-image: none;
        image: url(:/qfluentwidgets/images/icons/ChevronRight_white.svg);
    }}
    
    QTreeView::branch:open:has-children:!has-siblings,
    QTreeView::branch:open:has-children:has-siblings {{
        border-image: none;
        image: url(:/qfluentwidgets/images/icons/ChevronDown_white.svg);
    }}
    
    QHeaderView::section {{
        background-color: {bg_color};
        color: {text_color};
        border: none;
        padding: 4px 8px;
        font-weight: 600;
    }}
    """
    
    explorer_widget.setStyleSheet(style)


def create_vscode_explorer_header(title="资源管理器", dark_mode=True):
    """创建VSCode风格的浏览器标题栏
    
    Args:
        title: 标题文本
        dark_mode: 是否为深色主题
        
    Returns:
        QWidget: 标题栏组件
    """
    header = QWidget()
    layout = QHBoxLayout(header)
    layout.setContentsMargins(12, 8, 12, 8)
    
    # 标题标签
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
    
    layout.addWidget(title_label)
    layout.addStretch()
    
    # 应用样式
    if dark_mode:
        bg_color = "#252526"
        text_color = "#CCCCCC"
        border_color = "#454545"
    else:
        bg_color = "#F3F3F3"
        text_color = "#000000"
        border_color = "#E5E5E5"
    
    header.setStyleSheet(f"""
        QWidget {{
            background-color: {bg_color};
            border-bottom: 1px solid {border_color};
        }}
        QLabel {{
            color: {text_color};
            background-color: transparent;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    """)
    
    return header


class VSCodeExplorerEnhancer:
    """文件浏览器VSCode风格增强器"""
    
    def __init__(self, explorer_widget):
        """初始化增强器
        
        Args:
            explorer_widget: 文件浏览器组件
        """
        self.explorer = explorer_widget
        self.dark_mode = True
        
    def enhance(self):
        """应用VSCode风格增强"""
        # 应用样式
        apply_vscode_style_to_explorer(self.explorer, self.dark_mode)
        
        # 添加标题栏（如果还没有）
        if self.explorer.layout() and self.explorer.layout().count() > 0:
            # 获取树视图
            tree_view = None
            for i in range(self.explorer.layout().count()):
                item = self.explorer.layout().itemAt(i)
                if item and isinstance(item.widget(), QTreeView):
                    tree_view = item.widget()
                    break
            
            if tree_view:
                # 创建新布局
                header = create_vscode_explorer_header("资源管理器", self.dark_mode)
                
                # 重组布局
                old_layout = self.explorer.layout()
                new_layout = QVBoxLayout()
                new_layout.setContentsMargins(0, 0, 0, 0)
                new_layout.setSpacing(0)
                
                new_layout.addWidget(header)
                new_layout.addWidget(tree_view)
                
                # 替换布局（需要先清空旧布局）
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        item.widget().setParent(None)
                
                self.explorer.setLayout(new_layout)
    
    def apply_theme(self, dark_mode):
        """应用主题
        
        Args:
            dark_mode: 是否为深色主题
        """
        self.dark_mode = dark_mode
        apply_vscode_style_to_explorer(self.explorer, dark_mode)
