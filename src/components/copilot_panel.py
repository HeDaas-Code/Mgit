#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copilot Panel - UI for copilot features
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTextEdit, QLineEdit, QPushButton, QComboBox,
                           QListWidget, QListWidgetItem,
                           QTabWidget, QMessageBox, QDialog, QFileDialog,
                           QFormLayout, QDialogButtonBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor
from qfluentwidgets import (PushButton, LineEdit, ComboBox, TextEdit, 
                           SubtitleLabel, BodyLabel)
from src.utils.logger import info, warning, error, debug, LogCategory
from src.copilot import PROVIDER_SILICONFLOW, PROVIDER_MODELSCOPE
from src.copilot.siliconflow_client import SiliconFlowClient
from src.copilot.modelscope_client import ModelScopeClient
from datetime import datetime


# Provider display name mapping
PROVIDER_DISPLAY_NAMES = {
    PROVIDER_SILICONFLOW: 'SiliconFlow',
    PROVIDER_MODELSCOPE: 'ModelScope'
}

PROVIDER_FROM_DISPLAY = {
    'SiliconFlow': PROVIDER_SILICONFLOW,
    'ModelScope': PROVIDER_MODELSCOPE
}


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
        
    def _on_mode_changed(self, index: int):
        """Handle mode change"""
        self.tab_widget.setCurrentIndex(index)
        
    def _on_chat_send(self):
        """Handle chat send"""
        message = self.chat_input.text().strip()
        if not message:
            warning("Empty chat message", category=LogCategory.UI)
            return
            
        info(f"Chat message sent: {message[:50]}...", category=LogCategory.UI)
        
        # Add to history display
        self._add_to_chat_history("You", message)
        
        # Clear input
        self.chat_input.clear()
        
        # Request chat response
        debug("Emitting chat_requested signal", category=LogCategory.UI)
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
            warning("Empty edit text or instruction", category=LogCategory.UI)
            QMessageBox.warning(self, "输入错误", "请输入原文和编辑指令")
            return
            
        info(f"Edit request: text length={len(text)}, instruction={instruction[:50]}...", category=LogCategory.UI)
        debug("Emitting edit_requested signal", category=LogCategory.UI)
        self.edit_requested.emit(text, instruction)
        
    def _on_create_execute(self):
        """Execute creation"""
        prompt = self.create_prompt.toPlainText().strip()
        
        if not prompt:
            warning("Empty creation prompt", category=LogCategory.UI)
            QMessageBox.warning(self, "输入错误", "请输入创作提示")
            return
            
        content_type = self.content_type.currentText()
        info(f"Creation request: type={content_type}, prompt={prompt[:50]}...", category=LogCategory.UI)
        debug("Emitting create_requested signal", category=LogCategory.UI)
        self.create_requested.emit(prompt, content_type)
        
    def _on_create_task(self):
        """Create a new agent task"""
        # Check if parent has agent mode initialized
        parent = self.parent()
        if not parent or not hasattr(parent, 'agentMode') or not parent.agentMode:
            QMessageBox.warning(
                self, 
                "代理模式未初始化", 
                "请先配置Copilot API密钥并打开一个Git仓库"
            )
            return
            
        dialog = TaskCreationDialog(self)
        if dialog.exec_():
            task_type, file_path, instruction = dialog.get_values()
            # Emit signal to parent to create task
            if parent and hasattr(parent, 'create_agent_task'):
                parent.create_agent_task(task_type, file_path, instruction)
            else:
                QMessageBox.warning(self, "错误", "无法创建任务")
    
    def _on_refresh_tasks(self):
        """Refresh task list"""
        # Signal parent to refresh
        parent = self.parent()
        if parent and hasattr(parent, 'refresh_agent_tasks'):
            parent.refresh_agent_tasks()
        
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
        
        # Validate input is iterable
        if not tasks or not isinstance(tasks, (list, tuple)):
            return
        
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
            # Signal parent to handle audit with error handling
            parent = self.parent()
            if parent is None or not hasattr(parent, "audit_task") or not callable(getattr(parent, "audit_task")):
                warning(f"CopilotPanel parent has no 'audit_task' method; cannot audit task {task_id}", category=LogCategory.UI)
                QMessageBox.warning(
                    self,
                    "审计失败",
                    "无法处理审计请求：未找到上级处理器。"
                )
                return
            try:
                parent.audit_task(task_id, approved, comment)
            except Exception as e:
                error(f"Error while auditing task {task_id}: {e}", category=LogCategory.ERROR)
                QMessageBox.critical(
                    self,
                    "审计错误",
                    "处理审计请求时发生错误，请查看日志。"
                )


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
        
    def _validate_comment(self, require_comment: bool = False):
        """Validate comment input
        
        Args:
            require_comment: Whether comment is required
            
        Returns:
            Comment text or None if invalid
        """
        comment_text = self.comment_edit.toPlainText().strip()
        if require_comment and not comment_text:
            QMessageBox.warning(self, "输入必需", "请填写审计意见后再继续。")
            return None
        return comment_text
    
    def _on_approve(self):
        """Handle approve"""
        # Comments optional for approvals
        comment_text = self._validate_comment(require_comment=False)
        if comment_text is None and self.comment_edit.toPlainText().strip():
            # User had text but validation failed somehow
            return
        self.approved = True
        self.comment = comment_text or ""
        self.accept()
        
    def _on_reject(self):
        """Handle reject"""
        # Comments required for rejections
        comment_text = self._validate_comment(require_comment=True)
        if comment_text is None:
            return
        self.approved = False
        self.comment = comment_text
        self.accept()
        
    def get_result(self):
        """Get audit result"""
        return self.approved, self.comment


class TaskCreationDialog(QDialog):
    """Dialog for creating agent tasks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建代理任务")
        self.setMinimumWidth(500)
        self.initUI()
        
    def initUI(self):
        """Initialize UI"""
        layout = QFormLayout(self)
        
        # Task type
        self.task_type = QComboBox()
        self.task_type.addItems(["编辑文档", "创建文档", "提交更改"])
        layout.addRow("任务类型:", self.task_type)
        
        # File path
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("文件路径...")
        file_layout.addWidget(self.file_path)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addRow("文件路径:", file_layout)
        
        # Instruction
        self.instruction = QTextEdit()
        self.instruction.setPlaceholderText("输入任务指令，例如：将所有TODO注释转换为GitHub Issues...")
        self.instruction.setMinimumHeight(100)
        layout.addRow("任务指令:", self.instruction)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
    def _browse_file(self):
        """Browse for file"""
        task_type_text = self.task_type.currentText()
        if task_type_text == "编辑文档":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", "All Files (*.*)"
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "选择文件", "", "All Files (*.*)"
            )
        
        if file_path:
            self.file_path.setText(file_path)
            
    def _on_accept(self):
        """Validate and accept"""
        if not self.file_path.text().strip():
            QMessageBox.warning(self, "输入错误", "请输入文件路径")
            return
            
        if not self.instruction.toPlainText().strip():
            QMessageBox.warning(self, "输入错误", "请输入任务指令")
            return
            
        self.accept()
        
    def get_values(self):
        """Get dialog values"""
        task_types = {
            "编辑文档": "edit",
            "创建文档": "create",
            "提交更改": "commit"
        }
        task_type = task_types[self.task_type.currentText()]
        file_path = self.file_path.text().strip()
        instruction = self.instruction.toPlainText().strip()
        
        return task_type, file_path, instruction


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
        self.resize(600, 450)
        
        layout = QVBoxLayout(self)
        
        # Provider selection
        layout.addWidget(QLabel("服务提供商:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(PROVIDER_DISPLAY_NAMES.values()))
        
        current_provider = self.config_manager.get_plugin_setting('copilot', 'provider', PROVIDER_SILICONFLOW)
        display_name = PROVIDER_DISPLAY_NAMES.get(current_provider, 'SiliconFlow')
        provider_index = self.provider_combo.findText(display_name)
        if provider_index >= 0:
            self.provider_combo.setCurrentIndex(provider_index)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        
        layout.addWidget(self.provider_combo)
        
        # API Key
        self.api_key_label = QLabel("API Key:")
        layout.addWidget(self.api_key_label)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入API密钥...")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        
        current_key = self.config_manager.get_plugin_setting('copilot', 'api_key', '')
        if current_key:
            self.api_key_edit.setText(current_key)
            
        layout.addWidget(self.api_key_edit)
        
        # Model selection
        layout.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        
        # Initialize model list based on current provider
        self._update_model_list()
        
        current_model = self.config_manager.get_plugin_setting('copilot', 'model', '')
        if current_model:
            index = self.model_combo.findText(current_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
            
        layout.addWidget(self.model_combo)
        
        # Enable checkbox
        self.enable_checkbox = QCheckBox("启用 Copilot")
        self.enable_checkbox.setChecked(
            self.config_manager.get_plugin_setting('copilot', 'enabled', False)
        )
        layout.addWidget(self.enable_checkbox)
        
        # Info text
        self.info_text = QLabel()
        self._update_info_text()
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.info_text)
        
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
    
    def _on_provider_changed(self):
        """Handle provider selection change"""
        self._update_model_list()
        self._update_info_text()
    
    def _update_model_list(self):
        """Update model list based on selected provider"""
        self.model_combo.clear()
        
        provider = self.provider_combo.currentText()
        if provider == "SiliconFlow":
            self.model_combo.addItems([
                "Qwen/Qwen2.5-7B-Instruct",
                "Qwen/Qwen2.5-14B-Instruct",
                "Qwen/Qwen2.5-32B-Instruct",
                "deepseek-ai/DeepSeek-V2.5",
                "meta-llama/Meta-Llama-3.1-8B-Instruct"
            ])
        else:  # ModelScope
            self.model_combo.addItems([
                "qwen/Qwen2.5-7B-Instruct",
                "qwen/Qwen2.5-14B-Instruct",
                "qwen/Qwen2.5-32B-Instruct"
            ])
    
    def _update_info_text(self):
        """Update info text based on selected provider"""
        provider = self.provider_combo.currentText()
        if provider == "SiliconFlow":
            info = (
                "获取API密钥: https://siliconflow.cn\n"
                "文档: https://docs.siliconflow.cn\n\n"
            )
        else:  # ModelScope
            info = (
                "获取API密钥: https://www.modelscope.cn\n"
                "文档: https://www.modelscope.cn/docs/model-service/API-Inference/intro\n\n"
            )
        
        info += (
            "Copilot提供以下功能:\n"
            "• 行内补全 - 智能代码和文本补全\n"
            "• 编辑模式 - 根据指令编辑文本\n"
            "• 创作模式 - 从提示生成内容\n"
            "• 对话模式 - 与AI助手对话\n"
            "• 代理模式 - 自动执行任务（需审计）"
        )
        self.info_text.setText(info)
        
    def _on_save(self):
        """Save settings"""
        api_key = self.api_key_edit.text().strip()
        model = self.model_combo.currentText()
        enabled = self.enable_checkbox.isChecked()
        provider_display = self.provider_combo.currentText()
        provider = PROVIDER_FROM_DISPLAY.get(provider_display, PROVIDER_SILICONFLOW)
        
        if not api_key:
            QMessageBox.warning(self, "输入错误", "请输入API密钥")
            return
            
        self.config_manager.set_plugin_setting('copilot', 'api_key', api_key)
        self.config_manager.set_plugin_setting('copilot', 'model', model)
        self.config_manager.set_plugin_setting('copilot', 'enabled', enabled)
        self.config_manager.set_plugin_setting('copilot', 'provider', provider)
        
        QMessageBox.information(self, "成功", "设置已保存")
        self.accept()
        
    def _on_test(self):
        """Test API connection"""
        api_key = self.api_key_edit.text().strip()
        model = self.model_combo.currentText()
        provider_display = self.provider_combo.currentText()
        
        if not api_key:
            QMessageBox.warning(self, "输入错误", "请输入API密钥")
            return
            
        try:
            if provider_display == "SiliconFlow":
                client = SiliconFlowClient(api_key, model)
            else:  # ModelScope
                client = ModelScopeClient(api_key, model)
            
            if client.test_connection():
                QMessageBox.information(self, "成功", f"{provider_display} API连接成功！")
            else:
                QMessageBox.warning(self, "失败", f"{provider_display} API连接失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"测试失败: {str(e)}")
