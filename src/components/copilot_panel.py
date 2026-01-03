#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copilot Panel - UI for copilot features
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QLineEdit, QPushButton, QComboBox,
                           QGroupBox, QListWidget, QListWidgetItem, QSplitter,
                           QTabWidget, QFrame, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
from qfluentwidgets import (PushButton, LineEdit, ComboBox, TextEdit, 
                           CardWidget, SubtitleLabel, BodyLabel, 
                           FluentIcon, IconWidget)
from src.utils.logger import info, warning, error
from src.copilot.agent_mode import AgentTask
from datetime import datetime


class CopilotPanel(QWidget):
    """Main copilot panel widget"""
    
    completion_requested = pyqtSignal(str, str)  # context_before, context_after
    edit_requested = pyqtSignal(str, str)  # text, instruction
    create_requested = pyqtSignal(str, str)  # prompt, content_type
    chat_requested = pyqtSignal(str)  # message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conversation_history = []
        self.initUI()
        
    def initUI(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = SubtitleLabel("AI Copilot")
        layout.addWidget(title)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(BodyLabel("模式:"))
        
        self.mode_combo = ComboBox()
        self.mode_combo.addItems([
            "对话模式",
            "编辑模式",
            "创作模式",
            "行内补全",
            "代理模式"
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        
        layout.addLayout(mode_layout)
        
        # Create tab widget for different modes
        self.tab_widget = QTabWidget()
        
        # Chat tab
        self.chat_widget = self._create_chat_widget()
        self.tab_widget.addTab(self.chat_widget, "对话")
        
        # Edit tab
        self.edit_widget = self._create_edit_widget()
        self.tab_widget.addTab(self.edit_widget, "编辑")
        
        # Create tab
        self.create_widget = self._create_creation_widget()
        self.tab_widget.addTab(self.create_widget, "创作")
        
        # Agent tab
        self.agent_widget = self._create_agent_widget()
        self.tab_widget.addTab(self.agent_widget, "代理")
        
        layout.addWidget(self.tab_widget)
        
        # Status label
        self.status_label = BodyLabel("就绪")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)
        
    def _create_chat_widget(self) -> QWidget:
        """Create chat mode widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("对话历史...")
        layout.addWidget(self.chat_history)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.chat_input = LineEdit()
        self.chat_input.setPlaceholderText("输入消息...")
        self.chat_input.returnPressed.connect(self._on_chat_send)
        input_layout.addWidget(self.chat_input)
        
        send_btn = PushButton("发送")
        send_btn.clicked.connect(self._on_chat_send)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = PushButton("清空对话")
        clear_btn.clicked.connect(self._on_clear_chat)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
        
    def _create_edit_widget(self) -> QWidget:
        """Create edit mode widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instruction input
        layout.addWidget(BodyLabel("编辑指令:"))
        self.edit_instruction = TextEdit()
        self.edit_instruction.setPlaceholderText("输入编辑指令，例如：润色文字、修正语法错误、调整语气为正式...")
        self.edit_instruction.setMaximumHeight(100)
        layout.addWidget(self.edit_instruction)
        
        # Text to edit
        layout.addWidget(BodyLabel("原文:"))
        self.edit_text = TextEdit()
        self.edit_text.setPlaceholderText("粘贴要编辑的文本...")
        layout.addWidget(self.edit_text)
        
        # Edit button
        edit_btn = PushButton("执行编辑")
        edit_btn.clicked.connect(self._on_edit_execute)
        layout.addWidget(edit_btn)
        
        return widget
        
    def _create_creation_widget(self) -> QWidget:
        """Create creation mode widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Content type
        type_layout = QHBoxLayout()
        type_layout.addWidget(BodyLabel("内容类型:"))
        
        self.content_type = ComboBox()
        self.content_type.addItems([
            "Markdown文档",
            "技术文章",
            "大纲",
            "笔记",
            "报告",
            "README"
        ])
        type_layout.addWidget(self.content_type)
        type_layout.addStretch()
        
        layout.addLayout(type_layout)
        
        # Prompt input
        layout.addWidget(BodyLabel("创作提示:"))
        self.create_prompt = TextEdit()
        self.create_prompt.setPlaceholderText("描述你想创作的内容，例如：写一篇关于Python装饰器的技术文章...")
        layout.addWidget(self.create_prompt)
        
        # Create button
        create_btn = PushButton("开始创作")
        create_btn.clicked.connect(self._on_create_execute)
        layout.addWidget(create_btn)
        
        return widget
        
    def _create_agent_widget(self) -> QWidget:
        """Create agent mode widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Task list
        layout.addWidget(BodyLabel("任务列表:"))
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        
        # Button bar
        btn_layout = QHBoxLayout()
        
        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._on_refresh_tasks)
        btn_layout.addWidget(refresh_btn)
        
        audit_btn = PushButton("审计任务")
        audit_btn.clicked.connect(self._on_audit_task)
        btn_layout.addWidget(audit_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
        
    def _on_mode_changed(self, index: int):
        """Handle mode change"""
        self.tab_widget.setCurrentIndex(index)
        
    def _on_chat_send(self):
        """Handle chat send"""
        message = self.chat_input.text().strip()
        if not message:
            return
            
        # Add to history display
        self._add_to_chat_history("You", message)
        
        # Clear input
        self.chat_input.clear()
        
        # Request chat response
        self.chat_requested.emit(message)
        
    def _on_clear_chat(self):
        """Clear chat history"""
        self.chat_history.clear()
        self.conversation_history = []
        info("Chat history cleared")
        
    def _on_edit_execute(self):
        """Execute edit"""
        text = self.edit_text.toPlainText().strip()
        instruction = self.edit_instruction.toPlainText().strip()
        
        if not text or not instruction:
            QMessageBox.warning(self, "输入错误", "请输入原文和编辑指令")
            return
            
        self.edit_requested.emit(text, instruction)
        
    def _on_create_execute(self):
        """Execute creation"""
        prompt = self.create_prompt.toPlainText().strip()
        
        if not prompt:
            QMessageBox.warning(self, "输入错误", "请输入创作提示")
            return
            
        content_type = self.content_type.currentText()
        self.create_requested.emit(prompt, content_type)
        
    def _on_refresh_tasks(self):
        """Refresh task list"""
        # Signal parent to refresh
        pass
        
    def _on_audit_task(self):
        """Audit selected task"""
        current_item = self.task_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "选择错误", "请选择一个任务")
            return
            
        # Show audit dialog
        task_id = current_item.data(Qt.UserRole)
        self._show_audit_dialog(task_id)
        
    def _add_to_chat_history(self, sender: str, message: str):
        """Add message to chat history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Add sender and timestamp
        cursor.insertText(f"\n[{timestamp}] {sender}:\n")
        cursor.insertText(f"{message}\n")
        
        self.chat_history.setTextCursor(cursor)
        self.chat_history.ensureCursorVisible()
        
    def add_chat_response(self, response: str):
        """Add AI response to chat"""
        self._add_to_chat_history("Copilot", response)
        
        # Update conversation history
        self.conversation_history.append({'role': 'assistant', 'content': response})
        
    def display_completion(self, completion: str):
        """Display completion result"""
        QMessageBox.information(self, "补全结果", completion)
        
    def display_edit_result(self, edited_text: str):
        """Display edit result"""
        self.edit_text.setPlainText(edited_text)
        QMessageBox.information(self, "编辑完成", "文本已更新")
        
    def display_creation_result(self, content: str):
        """Display creation result"""
        self.create_prompt.setPlainText(content)
        QMessageBox.information(self, "创作完成", "内容已生成")
        
    def update_status(self, status: str):
        """Update status label"""
        self.status_label.setText(status)
        
    def update_task_list(self, tasks: list):
        """Update task list"""
        self.task_list.clear()
        
        for task in tasks:
            if isinstance(task, AgentTask):
                item_text = f"[{task.status}] {task.description}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, task.task_id)
                self.task_list.addItem(item)
                
    def _show_audit_dialog(self, task_id: str):
        """Show audit dialog"""
        dialog = TaskAuditDialog(task_id, self)
        if dialog.exec_():
            approved, comment = dialog.get_result()
            # Signal parent to handle audit
            self.parent().audit_task(task_id, approved, comment)


class TaskAuditDialog(QDialog):
    """Dialog for auditing agent tasks"""
    
    def __init__(self, task_id: str, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.approved = False
        self.comment = ""
        self.initUI()
        
    def initUI(self):
        """Initialize UI"""
        self.setWindowTitle("任务审计")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # Task info
        layout.addWidget(QLabel(f"任务ID: {self.task_id}"))
        
        # Comment input
        layout.addWidget(QLabel("审计意见:"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("输入审计意见...")
        layout.addWidget(self.comment_edit)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        approve_btn = QPushButton("批准")
        approve_btn.clicked.connect(self._on_approve)
        btn_layout.addWidget(approve_btn)
        
        reject_btn = QPushButton("拒绝")
        reject_btn.clicked.connect(self._on_reject)
        btn_layout.addWidget(reject_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _on_approve(self):
        """Handle approve"""
        self.approved = True
        self.comment = self.comment_edit.toPlainText()
        self.accept()
        
    def _on_reject(self):
        """Handle reject"""
        self.approved = False
        self.comment = self.comment_edit.toPlainText()
        self.accept()
        
    def get_result(self):
        """Get audit result"""
        return self.approved, self.comment


class CopilotSettingsDialog(QDialog):
    """Dialog for copilot settings"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.initUI()
        
    def initUI(self):
        """Initialize UI"""
        self.setWindowTitle("Copilot 设置")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # API Key
        layout.addWidget(QLabel("SiliconFlow API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入API密钥...")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        
        current_key = self.config_manager.get('copilot.api_key', '')
        if current_key:
            self.api_key_edit.setText(current_key)
            
        layout.addWidget(self.api_key_edit)
        
        # Model selection
        layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "Qwen/Qwen2.5-32B-Instruct",
            "deepseek-ai/DeepSeek-V2.5",
            "meta-llama/Meta-Llama-3.1-8B-Instruct"
        ])
        
        current_model = self.config_manager.get('copilot.model', 'Qwen/Qwen2.5-7B-Instruct')
        index = self.model_combo.findText(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
            
        layout.addWidget(self.model_combo)
        
        # Enable checkbox
        from PyQt5.QtWidgets import QCheckBox
        self.enable_checkbox = QCheckBox("启用 Copilot")
        self.enable_checkbox.setChecked(
            self.config_manager.get('copilot.enabled', False)
        )
        layout.addWidget(self.enable_checkbox)
        
        # Info text
        info_text = QLabel(
            "获取API密钥: https://siliconflow.cn\n\n"
            "Copilot提供以下功能:\n"
            "• 行内补全 - 智能代码和文本补全\n"
            "• 编辑模式 - 根据指令编辑文本\n"
            "• 创作模式 - 从提示生成内容\n"
            "• 对话模式 - 与AI助手对话\n"
            "• 代理模式 - 自动执行任务（需审计）"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_text)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)
        
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self._on_test)
        btn_layout.addWidget(test_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _on_save(self):
        """Save settings"""
        api_key = self.api_key_edit.text().strip()
        model = self.model_combo.currentText()
        enabled = self.enable_checkbox.isChecked()
        
        if not api_key:
            QMessageBox.warning(self, "输入错误", "请输入API密钥")
            return
            
        self.config_manager.set('copilot.api_key', api_key)
        self.config_manager.set('copilot.model', model)
        self.config_manager.set('copilot.enabled', enabled)
        
        QMessageBox.information(self, "成功", "设置已保存")
        self.accept()
        
    def _on_test(self):
        """Test API connection"""
        api_key = self.api_key_edit.text().strip()
        model = self.model_combo.currentText()
        
        if not api_key:
            QMessageBox.warning(self, "输入错误", "请输入API密钥")
            return
            
        try:
            from src.copilot.siliconflow_client import SiliconFlowClient
            client = SiliconFlowClient(api_key, model)
            
            if client.test_connection():
                QMessageBox.information(self, "成功", "API连接成功！")
            else:
                QMessageBox.warning(self, "失败", "API连接失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试失败: {str(e)}")
