#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, 
                          QToolBar, QAction, QMenu, QToolButton, QComboBox, QFrame, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect, QEvent
from PyQt5.QtGui import (QFont, QTextCharFormat, QTextCursor, QColor, 
                       QPainter, QTextFormat, QSyntaxHighlighter, QKeySequence, QIcon)
from qfluentwidgets import (FluentIcon, LineEdit, PushButton, 
                          ToolTipFilter, ToolTipPosition, CardWidget, ComboBox)
import re
import tempfile
import os

class MarkdownHighlighter(QSyntaxHighlighter):
    """ Markdown语法高亮器 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = False
        self.initHighlightingRules()
        
    def initHighlightingRules(self):
        """ 初始化高亮规则 """
        self.highlightingRules = []
        
        # 使用浅色主题的颜色
        self.initThemeColors(dark_mode=False)
        
    def initThemeColors(self, dark_mode=False):
        """ 根据主题初始化颜色 """
        self.dark_mode = dark_mode
        self.highlightingRules = []
        
        # 根据主题选择合适的颜色
        if dark_mode:
            heading_color = "#58B2FF"  # 亮蓝色
            bold_color = "#FFFFFF"     # 白色
            italic_color = "#FFFFFF"   # 白色
            code_bg_color = "#2D2D2D"  # 深灰色
            code_fg_color = "#FF6B6B"  # 亮红色
            link_color = "#58ACFA"     # 亮蓝色
            image_color = "#56D6C9"    # 亮青色
            quote_fg_color = "#A0A0A0" # 浅灰色
            quote_bg_color = "#2A2A2A" # 深灰色
            hr_color = "#A0A0A0"       # 浅灰色
            list_color = "#BF8BFF"     # 浅紫色
            task_color = "#5AE485"     # 浅绿色
            table_color = "#FF9E64"    # 浅橙色
        else:
            heading_color = "#0078D7"  # 蓝色
            bold_color = "#000000"     # 黑色
            italic_color = "#000000"   # 黑色
            code_bg_color = "#F5F5F5"  # 浅灰色
            code_fg_color = "#D73A49"  # 红色
            link_color = "#0366D6"     # 蓝色
            image_color = "#56B6C2"    # 青色
            quote_fg_color = "#6A737D" # 灰色
            quote_bg_color = "#F6F8FA" # 浅灰色
            hr_color = "#6A737D"       # 灰色
            list_color = "#6F42C1"     # 紫色
            task_color = "#22863A"     # 绿色
            table_color = "#E36209"    # 橙色
        
        # 标题格式
        headingFormat = QTextCharFormat()
        headingFormat.setFontWeight(QFont.Bold)
        headingFormat.setForeground(QColor(heading_color))
        
        # 添加标题规则(# 标题)
        for i in range(6, 0, -1):
            pattern = f"^{'#' * i}\\s+.+$"
            self.highlightingRules.append((pattern, headingFormat))
            
        # 粗体格式
        boldFormat = QTextCharFormat()
        boldFormat.setFontWeight(QFont.Bold)
        boldFormat.setForeground(QColor(bold_color))
        self.highlightingRules.append((r"\*\*.*?\*\*", boldFormat))
        self.highlightingRules.append((r"__.*?__", boldFormat))
        
        # 斜体格式
        italicFormat = QTextCharFormat()
        italicFormat.setFontItalic(True)
        italicFormat.setForeground(QColor(italic_color))
        self.highlightingRules.append((r"\*.*?\*", italicFormat))
        self.highlightingRules.append((r"_.*?_", italicFormat))
        
        # 代码块格式
        codeBlockFormat = QTextCharFormat()
        codeBlockFormat.setFontFamily("Courier New")
        codeBlockFormat.setBackground(QColor(code_bg_color))
        codeBlockFormat.setForeground(QColor(code_fg_color))
        self.highlightingRules.append((r"```.*?```", codeBlockFormat))
        
        # 行内代码格式
        inlineCodeFormat = QTextCharFormat()
        inlineCodeFormat.setFontFamily("Courier New")
        inlineCodeFormat.setBackground(QColor(code_bg_color))
        inlineCodeFormat.setForeground(QColor(code_fg_color))
        self.highlightingRules.append((r"`.*?`", inlineCodeFormat))
        
        # 链接格式
        linkFormat = QTextCharFormat()
        linkFormat.setForeground(QColor(link_color))
        linkFormat.setFontUnderline(True)
        self.highlightingRules.append((r"\[.*?\]\(.*?\)", linkFormat))
        
        # 图片格式
        imageFormat = QTextCharFormat()
        imageFormat.setForeground(QColor(image_color))
        self.highlightingRules.append((r"!\[.*?\]\(.*?\)", imageFormat))
        
        # 引用格式
        quoteFormat = QTextCharFormat()
        quoteFormat.setForeground(QColor(quote_fg_color))
        quoteFormat.setBackground(QColor(quote_bg_color))
        self.highlightingRules.append((r"^\s*>.*$", quoteFormat))
        
        # 水平线格式
        hrFormat = QTextCharFormat()
        hrFormat.setForeground(QColor(hr_color))
        self.highlightingRules.append((r"^\s*[-*_]{3,}\s*$", hrFormat))
        
        # 列表格式
        listFormat = QTextCharFormat()
        listFormat.setForeground(QColor(list_color))
        listFormat.setFontWeight(QFont.Bold)
        self.highlightingRules.append((r"^\s*[\*\-\+]\s+.*$", listFormat))
        self.highlightingRules.append((r"^\s*\d+\.\s+.*$", listFormat))
        
        # 任务列表格式
        taskListFormat = QTextCharFormat()
        taskListFormat.setForeground(QColor(task_color))
        self.highlightingRules.append((r"^\s*[\*\-\+]\s+\[[ x]\]\s+.*$", taskListFormat))
        
        # 表格格式
        tableFormat = QTextCharFormat()
        tableFormat.setForeground(QColor(table_color))
        self.highlightingRules.append((r"^\|(.+\|)+$", tableFormat))
        self.highlightingRules.append((r"^(\|\s*:?-+:?\s*)+\|$", tableFormat))
        
    def setDarkMode(self, dark_mode):
        """ 设置是否使用深色模式 """
        if self.dark_mode != dark_mode:
            self.initThemeColors(dark_mode)
            self.rehighlight()
        
    def highlightBlock(self, text):
        """ 执行高亮 """
        for pattern, format in self.highlightingRules:
            expression = pattern
            index = text.find(expression)
            while index >= 0:
                length = len(expression)
                self.setFormat(index, length, format)
                index = text.find(expression, index + length)


class EnhancedTextEdit(QPlainTextEdit):
    """ 增强型文本编辑器，提供更多Markdown辅助功能 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabChangesFocus(False)
        
    def keyPressEvent(self, event):
        """ 处理键盘事件，提供智能输入 """
        # Tab键自动缩进
        if event.key() == Qt.Key_Tab:
            cursor = self.textCursor()
            # 如果有选中内容，增加所有选中行的缩进
            if cursor.hasSelection():
                # 获取选中的文本
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                
                # 移动到选中区域的开始
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfLine)
                
                # 保存起始位置
                start_block = cursor.block().blockNumber()
                
                # 移动到选中区域的结束
                cursor.setPosition(end)
                cursor.movePosition(QTextCursor.EndOfLine)
                end_block = cursor.block().blockNumber()
                
                # 设置为块选中模式
                cursor.setPosition(start)
                cursor.movePosition(QTextCursor.StartOfLine)
                
                # 对每一行增加缩进
                for _ in range(start_block, end_block + 1):
                    cursor.insertText("    ")  # 插入4个空格作为缩进
                    if not cursor.movePosition(QTextCursor.Down):
                        break
                    cursor.movePosition(QTextCursor.StartOfLine)
            else:
                # 没有选中内容，插入4个空格
                cursor.insertText("    ")
            return
            
        # 回车键自动延续列表和缩进
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            cursor = self.textCursor()
            current_line = cursor.block().text()
            
            # 匹配列表项
            list_match = re.match(r'^(\s*)([\*\-\+]|\d+\.)\s+(\[[ x]\])?\s*(.*)$', current_line)
            if list_match:
                indent, marker, task_marker, content = list_match.groups()
                
                # 如果当前行是空列表项，转换为普通行
                if not content and task_marker is None:
                    # 删除当前行，插入新行
                    cursor.movePosition(QTextCursor.StartOfLine)
                    cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    super().keyPressEvent(event)
                    return
                
                # 如果是数字列表，增加序号
                if re.match(r'\d+\.', marker):
                    number = int(marker[:-1])
                    marker = f"{number + 1}."
                
                # 创建新的列表项
                new_line = f"{indent}{marker} "
                if task_marker:
                    new_line += "[ ] "
                
                # 插入新行和列表标记
                super().keyPressEvent(event)
                self.textCursor().insertText(new_line)
                return
                
            # 匹配引用行
            quote_match = re.match(r'^(\s*>\s+)(.*)$', current_line)
            if quote_match:
                prefix, content = quote_match.groups()
                
                # 如果当前行是空引用，结束引用
                if not content:
                    # 删除当前行，插入新行
                    cursor.movePosition(QTextCursor.StartOfLine)
                    cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    super().keyPressEvent(event)
                    return
                
                # 插入新行和引用标记
                super().keyPressEvent(event)
                self.textCursor().insertText(prefix)
                return
                
            # 匹配代码块
            if current_line.strip() == "```" or current_line.startswith("```"):
                # 在代码块内按下回车，不自动闭合
                if not self.isLastLine(cursor):
                    super().keyPressEvent(event)
                    return
                
                # 如果是代码块开始，自动闭合
                super().keyPressEvent(event)
                cursor = self.textCursor()
                cursor.insertText("```")
                cursor.insertBlock()  # 再插入一个空行
                cursor.movePosition(QTextCursor.Up)
                self.setTextCursor(cursor)
                return
            
            # 保持缩进
            indent_match = re.match(r'^(\s+)', current_line)
            if indent_match:
                indent = indent_match.group(1)
                super().keyPressEvent(event)
                self.textCursor().insertText(indent)
                return
                
        # Shift+Enter 插入软换行（不会触发自动列表等功能）
        elif event.key() == Qt.Key_Return and event.modifiers() == Qt.ShiftModifier:
            super().keyPressEvent(event)
            return
            
        # Ctrl+B 粗体
        elif event.key() == Qt.Key_B and event.modifiers() == Qt.ControlModifier:
            self.insertMarkup("**", "**")
            return
            
        # Ctrl+I 斜体
        elif event.key() == Qt.Key_I and event.modifiers() == Qt.ControlModifier:
            self.insertMarkup("*", "*")
            return
            
        # Ctrl+K 链接
        elif event.key() == Qt.Key_K and event.modifiers() == Qt.ControlModifier:
            self.insertMarkup("[", "]()")
            return
            
        # Ctrl+` 行内代码
        elif event.key() == Qt.Key_QuoteLeft and event.modifiers() == Qt.ControlModifier:
            self.insertMarkup("`", "`")
            return
            
        # 默认处理
        super().keyPressEvent(event)
        
    def isLastLine(self, cursor):
        """ 检查是否为最后一行 """
        current_block = cursor.block()
        next_block = current_block.next()
        return not next_block.isValid()
        
    def insertMarkup(self, prefix, suffix):
        """ 插入Markdown标记 """
        print(f"插入标记: 前缀='{prefix}', 后缀='{suffix}'")
        try:
            self.editor.insertMarkup(prefix, suffix)
            print("标记插入成功")
        except Exception as e:
            print(f"插入标记时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 尝试直接使用textCursor插入
            try:
                cursor = self.textCursor()
                selected_text = cursor.selectedText()
                if selected_text:
                    cursor.insertText(prefix + selected_text + suffix)
                else:
                    cursor.insertText(prefix + suffix)
                    cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(suffix))
                self.setTextCursor(cursor)
                print("使用备用方法插入标记成功")
            except Exception as e2:
                print(f"备用插入方法也失败: {str(e2)}")
                QMessageBox.critical(self, "插入标记错误", f"无法插入标记: {str(e)}")
        
    def createStandardContextMenu(self):
        """ 创建标准右键菜单并添加Markdown特有选项 """
        menu = super().createStandardContextMenu()
        
        # 添加分隔符
        menu.addSeparator()
        
        # Markdown格式菜单
        format_menu = QMenu("Markdown格式", menu)
        
        # 添加常用格式选项
        bold_action = format_menu.addAction("粗体")
        bold_action.triggered.connect(lambda: self.insertMarkup("**", "**"))
        
        italic_action = format_menu.addAction("斜体")
        italic_action.triggered.connect(lambda: self.insertMarkup("*", "*"))
        
        code_action = format_menu.addAction("行内代码")
        code_action.triggered.connect(lambda: self.insertMarkup("`", "`"))
        
        link_action = format_menu.addAction("链接")
        link_action.triggered.connect(lambda: self.insertMarkup("[", "](url)"))
        
        menu.addMenu(format_menu)
        
        # 添加插入菜单
        insert_menu = QMenu("插入", menu)
        
        table_action = insert_menu.addAction("表格")
        table_action.triggered.connect(self.insertTable)
        
        image_action = insert_menu.addAction("图片")
        image_action.triggered.connect(lambda: self.insertMarkup("![alt text](", ")"))
        
        hr_action = insert_menu.addAction("水平线")
        hr_action.triggered.connect(lambda: self.insertPlainText("\n---\n"))
        
        tasklist_action = insert_menu.addAction("任务列表项")
        tasklist_action.triggered.connect(lambda: self.insertPlainText("- [ ] "))
        
        menu.addMenu(insert_menu)
        
        return menu
        
    def insertTable(self):
        """ 插入表格 """
        table_text = """
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容 | 内容 | 内容 |
| 内容 | 内容 | 内容 |
"""
        self.insertPlainText(table_text)
        
    def insertPlainText(self, text):
        """ 插入纯文本 """
        cursor = self.textCursor()
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.setFocus()
        
    def getCursorLineNumber(self):
        """ 获取光标所在行号 """
        cursor = self.textCursor()
        return cursor.blockNumber()
        
    def goToLine(self, line_number):
        """ 跳转到指定行 """
        if line_number < 0:
            return
            
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.NextBlock)
            
        # 将光标设置到目标行并滚动视图
        self.setTextCursor(cursor)
        self.centerCursor()  # 将光标位置居中显示
        self.setFocus()      # 设置焦点


class LineNumberArea(QWidget):
    """ 行号区域 """
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedWidth(50)  # 初始宽度
        
        # 连接信号，处理文档变化和滚动
        self.editor.blockCountChanged.connect(self.updateWidth)
        self.editor.updateRequest.connect(self.updateContents)
        
        # 初始化行号区域宽度
        self.updateWidth(0)
        
    def updateWidth(self, newBlockCount):
        """ 更新行号区域宽度 """
        width = self.fontMetrics().horizontalAdvance('9') * max(3, len(str(self.editor.blockCount()))) + 10
        if width != self.width():
            self.setFixedWidth(width)
            self.editor.setViewportMargins(width, 0, 0, 0)
    
    def updateContents(self, rect, dy):
        """ 滚动时更新内容 """
        if dy:
            self.scroll(0, dy)
        else:
            self.update(0, rect.y(), self.width(), rect.height())
            
        if rect.contains(self.editor.viewport().rect()):
            self.updateWidth(0)
        
    def paintEvent(self, event):
        # 绘制行号区域的背景
        painter = QPainter(self)
        
        # 安全地获取深色模式状态
        dark_mode = False
        md_editor = self.get_markdown_editor()
        if md_editor and hasattr(md_editor, 'dark_mode'):
            dark_mode = md_editor.dark_mode
        
        # 根据主题设置颜色
        bg_color = QColor("#F0F0F0") if not dark_mode else QColor("#2D2D2D")
        painter.fillRect(event.rect(), bg_color)
        
        # 获取可见区域
        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.editor.blockBoundingGeometry(block).translated(
            self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()
        
        # 行号颜色
        text_color = QColor("#888888") if not dark_mode else QColor("#AAAAAA")
        current_line = self.editor.textCursor().blockNumber()
        
        # 设置字体
        painter.setFont(QFont("Consolas", 9))
        
        # 绘制行号
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # 当前行高亮
                if block_number == current_line:
                    painter.setPen(QColor("#333333") if not dark_mode else QColor("#FFFFFF"))
                else:
                    painter.setPen(text_color)
                    
                # 绘制行号，注意将top转为整数
                painter.drawText(0, int(top), self.width() - 5, self.editor.fontMetrics().height(),
                                Qt.AlignRight, str(block_number + 1))
            
            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1
            
    def get_markdown_editor(self):
        """ 向上查找获取MarkdownEditor实例 """
        parent = self.parent()
        while parent:
            if isinstance(parent, MarkdownEditor):
                return parent
            parent = parent.parent()
        return None


class MarkdownEditor(QWidget):
    """ Markdown编辑器组件 """
    
    textChanged = pyqtSignal()  # 文本变化信号
    documentChanged = pyqtSignal(str)  # 文档内容变化信号
    cursorPositionChanged = pyqtSignal(int)  # 光标位置变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_mode = False  # 默认使用浅色模式
        self.currentFilePath = None  # 当前文件路径
        self.initUI()
        self.connectSignals()
        self.setupAutoSave()
        
    def initUI(self):
        """ 初始化UI """
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建工具栏
        self.toolbar = QToolBar()
        self.setupToolbar()
        layout.addWidget(self.toolbar)
        
        # 创建编辑器
        self.editor = EnhancedTextEdit()
        self.editor.setFrameShape(QFrame.NoFrame)
        
        # 配置编辑器样式
        self.editor.setStyleSheet("""
            EnhancedTextEdit {
                background-color: #F8F9FA;
                color: #333333;
                border: none;
                padding: 10px;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 14px;
            }
        """)
        
        # 设置语法高亮器
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 设置行号区域
        self.lineNumberArea = LineNumberArea(self.editor)
        
        # 添加编辑器到布局
        layout.addWidget(self.editor)
        
        # 确保行号区域工作正常
        self.editor.installEventFilter(self)
        self.editor.viewport().installEventFilter(self)
        
    def eventFilter(self, obj, event):
        """ 事件过滤器，处理窗口大小变化以更新行号区域 """
        if obj == self.editor or obj == self.editor.viewport():
            if event.type() == QEvent.Resize:
                rect = self.editor.contentsRect()
                self.lineNumberArea.setGeometry(QRect(rect.left(), rect.top(), 
                                                self.lineNumberArea.width(), rect.height()))
                
        return super().eventFilter(obj, event)
        
    def setupAutoSave(self):
        """ 设置自动保存功能 """
        self.autoSaveEnabled = True  # 是否启用自动保存
        self.autoSaveInterval = 60000  # 自动保存间隔（毫秒）
        
        # 创建自动保存定时器
        self.autoSaveTimer = QTimer(self)
        self.autoSaveTimer.timeout.connect(self.performAutoSave)
        
        # 设置自动保存路径
        self.autoSavePath = os.path.join(tempfile.gettempdir(), "mgit_autosave.md")
        
        # 启动自动保存
        self.autoSaveTimer.start(self.autoSaveInterval)
        
    def performAutoSave(self):
        """ 执行自动保存 """
        if not self.autoSaveEnabled:
            return
            
        # 仅在编辑器内容被修改且不为空时保存
        if not self.editor.document().isModified() or not self.editor.toPlainText().strip():
            return
            
        try:
            # 保存到临时文件
            with open(self.autoSavePath, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            print(f"Auto-saved to {self.autoSavePath}")  # 仅在控制台输出，不打扰用户
        except Exception as e:
            print(f"Auto-save failed: {str(e)}")
            
    def recoverFromAutoSave(self):
        """ 从自动保存文件恢复 """
        if os.path.exists(self.autoSavePath):
            try:
                with open(self.autoSavePath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 如果有内容，询问用户是否恢复
                if content.strip():
                    reply = QMessageBox.question(
                        self, "恢复自动保存", 
                        "发现未保存的内容，是否恢复？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.editor.setPlainText(content)
                        return True
            except Exception as e:
                print(f"Recovery failed: {str(e)}")
                
        return False
        
    def setAutoSaveEnabled(self, enabled):
        """ 启用或禁用自动保存 """
        self.autoSaveEnabled = enabled
        if enabled:
            self.autoSaveTimer.start(self.autoSaveInterval)
        else:
            self.autoSaveTimer.stop()
            
    def setAutoSaveInterval(self, interval_ms):
        """ 设置自动保存间隔（毫秒） """
        self.autoSaveInterval = max(5000, interval_ms)  # 至少5秒
        if self.autoSaveEnabled:
            self.autoSaveTimer.setInterval(self.autoSaveInterval)
        
    def connectSignals(self):
        """ 连接信号 """
        self.editor.textChanged.connect(self.onTextChanged)
        self.editor.cursorPositionChanged.connect(self.onCursorPositionChanged)
        
    def onTextChanged(self):
        """ 处理文本变化 """
        self.textChanged.emit()
        self.documentChanged.emit(self.editor.toPlainText())
        
    def onCursorPositionChanged(self):
        """ 处理光标位置变化 """
        line_number = self.editor.getCursorLineNumber()
        self.cursorPositionChanged.emit(line_number)
        
    def toPlainText(self):
        """ 获取编辑器的纯文本内容 """
        if hasattr(self, 'editor'):
            return self.editor.toPlainText()
        return ""
        
    def setPlainText(self, text):
        """ 设置纯文本内容 """
        self.editor.setPlainText(text)
        
    def clearText(self):
        """ 清空编辑器内容 """
        if hasattr(self, 'editor'):
            self.editor.clear()
            # 清除修改标记
            self.editor.document().setModified(False)
        
    def goToLine(self, line_number):
        """ 跳转到指定行 """
        self.editor.goToLine(line_number)
        
    def updateTheme(self, dark_mode=False):
        """ 更新主题 """
        self.dark_mode = dark_mode
        
        # 更新编辑器样式
        if dark_mode:
            self.editor.setStyleSheet("""
                EnhancedTextEdit {
                    background-color: #2D2D2D;
                    color: #EFEFEF;
                    border: none;
                    padding: 10px;
                    font-family: "Consolas", "Courier New", monospace;
                    font-size: 14px;
                }
            """)
        else:
            self.editor.setStyleSheet("""
                EnhancedTextEdit {
                    background-color: #F8F9FA;
                    color: #333333;
                    border: none;
                    padding: 10px;
                    font-family: "Consolas", "Courier New", monospace;
                    font-size: 14px;
                }
            """)
            
        # 更新语法高亮
        if hasattr(self, 'highlighter'):
            self.highlighter.setDarkMode(dark_mode)
            
        # 强制重绘行号区域
        if hasattr(self, 'lineNumberArea'):
            self.lineNumberArea.update()

    def setupToolbar(self):
        """ 设置工具栏 """
        self.toolbar.setIconSize(QSize(16, 16))
        
        # 标题下拉菜单
        self.headingCombo = ComboBox()
        self.headingCombo.addItem("标题", None)
        self.headingCombo.addItem("标题 1", "# ")
        self.headingCombo.addItem("标题 2", "## ")
        self.headingCombo.addItem("标题 3", "### ")
        self.headingCombo.addItem("标题 4", "#### ")
        self.headingCombo.addItem("标题 5", "##### ")
        self.headingCombo.addItem("标题 6", "###### ")
        self.headingCombo.setFixedWidth(100)
        
        # 验证数据是否正确设置
        for i in range(self.headingCombo.count()):
            print(f"ComboBox 项 {i}: 文本={self.headingCombo.itemText(i)}, 数据={self.headingCombo.itemData(i)}")
            
        self.headingCombo.currentIndexChanged.connect(self.onHeadingSelected)
        self.toolbar.addWidget(self.headingCombo)
        
        # 添加分隔符
        self.toolbar.addSeparator()
        
        # 常用格式按钮
        self.boldAction = self.addToolButton(FluentIcon.FONT_SIZE, "粗体 (Ctrl+B)", lambda: self.insertMarkup("**", "**"))
        self.italicAction = self.addToolButton(FluentIcon.FONT, "斜体 (Ctrl+I)", lambda: self.insertMarkup("*", "*"))
        self.codeAction = self.addToolButton(FluentIcon.CODE, "代码 (Ctrl+`)", lambda: self.insertMarkup("`", "`"))
        
        # 添加分隔符
        self.toolbar.addSeparator()
        
        # 列表按钮
        self.bulletListAction = self.addToolButton(FluentIcon.CHECKBOX, "项目符号列表", lambda: self.insertMarkup("- ", ""))
        self.numberedListAction = self.addToolButton(FluentIcon.ADD, "编号列表", lambda: self.insertMarkup("1. ", ""))
        self.taskListAction = self.addToolButton(FluentIcon.COMPLETED, "任务列表", lambda: self.insertMarkup("- [ ] ", ""))
        
        # 添加分隔符
        self.toolbar.addSeparator()
        
        # 其他常用元素
        self.linkAction = self.addToolButton(FluentIcon.LINK, "链接 (Ctrl+K)", lambda: self.insertMarkup("[链接文本](", ")"))
        self.imageAction = self.addToolButton(FluentIcon.CAMERA, "图片", lambda: self.insertMarkup("![图片描述](", ")"))
        self.quoteAction = self.addToolButton(FluentIcon.CHAT, "引用", lambda: self.insertMarkup("> ", ""))
        self.hlineAction = self.addToolButton(FluentIcon.REMOVE, "水平线", lambda: self.insertPlainText("\n---\n"))
        self.tableAction = self.addToolButton(FluentIcon.VIEW, "表格", self.insertTable)
        
    def addToolButton(self, icon, tooltip, slot):
        """ 添加工具栏按钮 """
        button = QToolButton()
        button.setIcon(icon.icon())
        button.setToolTip(tooltip)
        button.clicked.connect(slot)
        self.toolbar.addWidget(button)
        return button
        
    def onHeadingSelected(self, index):
        """ 处理标题选择 """
        try:
            print(f"选择的标题级别索引: {index}")
            
            # 不再使用itemData，直接根据索引确定标题前缀
            heading_prefix = None
            if index == 1:
                heading_prefix = "# "
            elif index == 2:
                heading_prefix = "## "
            elif index == 3:
                heading_prefix = "### "
            elif index == 4:
                heading_prefix = "#### "
            elif index == 5:
                heading_prefix = "##### "
            elif index == 6:
                heading_prefix = "###### "
            
            print(f"使用标题前缀: '{heading_prefix}'")
            
            if heading_prefix:
                # 获取当前行
                cursor = self.editor.textCursor()
                cursor.beginEditBlock()  # 开始编辑块，使操作成为单一的撤销步骤
                
                # 移动到行首
                cursor.movePosition(QTextCursor.StartOfLine)
                line_start_pos = cursor.position()
                
                # 移动到行尾并选择整行
                cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
                line_text = cursor.selectedText()
                print(f"当前行文本: '{line_text}'")
                
                # 移除可能存在的标题标记
                clean_text = re.sub(r'^#+\s*', '', line_text).strip()
                print(f"清理后的文本: '{clean_text}'")
                
                # 插入新的标题标记和清理后的文本
                cursor.removeSelectedText()
                new_text = heading_prefix + clean_text
                print(f"要插入的新文本: '{new_text}'")
                cursor.insertText(new_text)
                
                # 恢复光标位置或设置到适当位置
                cursor.setPosition(line_start_pos + len(new_text))
                self.editor.setTextCursor(cursor)
                
                cursor.endEditBlock()  # 结束编辑块
                print("标题应用完成")
            else:
                print("未获取到标题前缀，无法应用")
            
            # 重置下拉框
            self.headingCombo.setCurrentIndex(0)
        except Exception as e:
            print(f"标题选择功能错误: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "标题功能错误", f"设置标题时发生错误: {str(e)}")
    
    def insertMarkup(self, prefix, suffix):
        """ 插入Markdown标记 """
        print(f"插入标记: 前缀='{prefix}', 后缀='{suffix}'")
        try:
            self.editor.insertMarkup(prefix, suffix)
            print("标记插入成功")
        except Exception as e:
            print(f"插入标记时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 尝试直接使用textCursor插入
            try:
                cursor = self.editor.textCursor()
                selected_text = cursor.selectedText()
                if selected_text:
                    cursor.insertText(prefix + selected_text + suffix)
                else:
                    cursor.insertText(prefix + suffix)
                    cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, len(suffix))
                self.editor.setTextCursor(cursor)
                print("使用备用方法插入标记成功")
            except Exception as e2:
                print(f"备用插入方法也失败: {str(e2)}")
                QMessageBox.critical(self, "插入标记错误", f"无法插入标记: {str(e)}")
         
    def insertPlainText(self, text):
        """ 插入纯文本 """
        self.editor.insertPlainText(text)
        
    def insertTable(self):
        """ 插入表格 """
        self.editor.insertTable()
        
    def saveFile(self):
        """ 保存文件 """
        # 如果没有当前文件路径，执行另存为操作
        if not self.currentFilePath:
            return self.saveAsFile()
            
        try:
            # 获取编辑器内容
            text = self.editor.toPlainText()
            
            # 写入文件
            with open(self.currentFilePath, 'w', encoding='utf-8') as f:
                f.write(text)
                
            # 清除修改标记
            self.editor.document().setModified(False)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存文件时发生错误: {str(e)}")
            return False
    
    def saveAsFile(self):
        """ 另存为 """
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getSaveFileName(
            self, "另存为", self.currentFilePath or "",
            "Markdown文件 (*.md);;所有文件 (*)", options=options
        )
        
        if not filePath:
            return False  # 用户取消
            
        # 确保文件有.md扩展名
        if not filePath.lower().endswith('.md'):
            filePath += '.md'
            
        # 保存当前文件路径
        self.currentFilePath = filePath
        
        # 调用保存方法
        return self.saveFile() 