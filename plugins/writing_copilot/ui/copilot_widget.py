#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Writing Copilot Widget - Main UI for the copilot plugin
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTextEdit, QTabWidget, QSplitter,
                           QListWidget, QListWidgetItem, QMessageBox, QLineEdit,
                           QTextBrowser, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QTextCursor
from qfluentwidgets import (PushButton, LineEdit, TextEdit, FluentIcon,
                          CardWidget, BodyLabel, SubtitleLabel, StrongBodyLabel)
from src.utils.logger import info, warning, error, debug

import json
from typing import Optional, Dict, List


class CompletionWorker(QThread):
    """后台完成工作线程"""
    completed = pyqtSignal(str)
    failed = pyqtSignal(str)
    
    def __init__(self, llm_client, prompt, parent=None):
        super().__init__(parent)
        self.llm_client = llm_client
        self.prompt = prompt
    
    def run(self):
        try:
            if not self.llm_client:
                self.failed.emit("LLM客户端未初始化")
                return
            
            # 调用LLM生成补全
            from langchain.schema import HumanMessage
            
            messages = [HumanMessage(content=self.prompt)]
            response = self.llm_client.invoke(messages)
            
            completion = response.content if hasattr(response, 'content') else str(response)
            self.completed.emit(completion)
            
        except Exception as e:
            self.failed.emit(f"生成失败: {str(e)}")


class ChatWorker(QThread):
    """聊天工作线程"""
    responded = pyqtSignal(str)
    failed = pyqtSignal(str)
    
    def __init__(self, llm_client, message, context, parent=None):
        super().__init__(parent)
        self.llm_client = llm_client
        self.message = message
        self.context = context
    
    def run(self):
        try:
            if not self.llm_client:
                self.failed.emit("LLM客户端未初始化")
                return
            
            from langchain.schema import HumanMessage, SystemMessage
            
            # 构建消息列表
            messages = []
            
            # 添加系统消息
            system_msg = "你是一个专业的写作助手，帮助用户改进和创作文档内容。"
            if self.context:
                system_msg += f"\n\n当前文档内容:\n{self.context[:2000]}"
            
            messages.append(SystemMessage(content=system_msg))
            messages.append(HumanMessage(content=self.message))
            
            # 调用LLM
            response = self.llm_client.invoke(messages)
            reply = response.content if hasattr(response, 'content') else str(response)
            
            self.responded.emit(reply)
            
        except Exception as e:
            self.failed.emit(f"对话失败: {str(e)}")


class AgentWorker(QThread):
    """代理工作线程"""
    completed = pyqtSignal(str, dict)
    failed = pyqtSignal(str)
    
    def __init__(self, agent_executor, task, parent=None):
        super().__init__(parent)
        self.agent_executor = agent_executor
        self.task = task
    
    def run(self):
        try:
            if not self.agent_executor:
                self.failed.emit("代理执行器未初始化")
                return
            
            # 执行代理任务
            result = self.agent_executor.invoke({"input": self.task})
            
            # 提取结果
            output = result.get('output', str(result))
            
            # 收集任务信息
            task_info = {
                'task': self.task,
                'output': output,
                'intermediate_steps': result.get('intermediate_steps', [])
            }
            
            self.completed.emit(output, task_info)
            
        except Exception as e:
            error(f"代理任务执行失败: {str(e)}")
            self.failed.emit(f"执行失败: {str(e)}")


class WritingCopilotWidget(QWidget):
    """写作Copilot主界面"""
    
    def __init__(self, plugin, app, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.app = app
        self.current_worker = None
        self.chat_history = []
        self.pending_tasks = []
        
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title = SubtitleLabel("写作Copilot")
        layout.addWidget(title)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 补全标签页
        self.completion_tab = self._create_completion_tab()
        self.tab_widget.addTab(self.completion_tab, "补全")
        
        # 编辑标签页
        self.edit_tab = self._create_edit_tab()
        self.tab_widget.addTab(self.edit_tab, "编辑")
        
        # 创作标签页
        self.create_tab = self._create_create_tab()
        self.tab_widget.addTab(self.create_tab, "创作")
        
        # 对话标签页
        self.chat_tab = self._create_chat_tab()
        self.tab_widget.addTab(self.chat_tab, "对话")
        
        # 代理标签页
        self.agent_tab = self._create_agent_tab()
        self.tab_widget.addTab(self.agent_tab, "代理")
        
        # 审查标签页
        self.review_tab = self._create_review_tab()
        self.tab_widget.addTab(self.review_tab, "任务审查")
        
        layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.status_label = BodyLabel("就绪")
        layout.addWidget(self.status_label)
    
    def _create_completion_tab(self):
        """创建补全标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = BodyLabel("行内补全会在您输入时自动触发，也可以手动触发。")
        layout.addWidget(info_label)
        
        # 手动触发按钮
        trigger_btn = PushButton("手动触发补全")
        trigger_btn.setIcon(FluentIcon.EDIT)
        trigger_btn.clicked.connect(self._manual_trigger_completion)
        layout.addWidget(trigger_btn)
        
        # 补全预览
        preview_group = QGroupBox("补全预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self.completion_preview = QTextBrowser()
        self.completion_preview.setMaximumHeight(200)
        preview_layout.addWidget(self.completion_preview)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        accept_btn = PushButton("接受")
        accept_btn.setIcon(FluentIcon.ACCEPT)
        accept_btn.clicked.connect(self._accept_completion)
        
        reject_btn = PushButton("拒绝")
        reject_btn.setIcon(FluentIcon.CANCEL)
        reject_btn.clicked.connect(self._reject_completion)
        
        btn_layout.addWidget(accept_btn)
        btn_layout.addWidget(reject_btn)
        btn_layout.addStretch()
        
        preview_layout.addLayout(btn_layout)
        layout.addWidget(preview_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_edit_tab(self):
        """创建编辑标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = BodyLabel("选择文本并选择编辑操作。")
        layout.addWidget(info_label)
        
        # 编辑操作按钮
        btn_layout = QVBoxLayout()
        
        operations = [
            ("改进写作", "improve", "提升文本质量和可读性"),
            ("修正语法", "grammar", "修正语法和拼写错误"),
            ("扩展内容", "expand", "扩展和详细化选定内容"),
            ("简化内容", "simplify", "简化和精简内容"),
            ("重写", "rewrite", "用不同方式重写内容"),
        ]
        
        for name, operation, description in operations:
            btn = PushButton(name)
            btn.setToolTip(description)
            btn.clicked.connect(lambda checked, op=operation: self._perform_edit(op))
            btn_layout.addWidget(btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return widget
    
    def _create_create_tab(self):
        """创建创作标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = BodyLabel("基于提示生成新内容。")
        layout.addWidget(info_label)
        
        # 提示输入
        prompt_label = StrongBodyLabel("创作提示:")
        layout.addWidget(prompt_label)
        
        self.create_prompt = TextEdit()
        self.create_prompt.setPlaceholderText("输入您想要创作的内容描述...")
        self.create_prompt.setMaximumHeight(150)
        layout.addWidget(self.create_prompt)
        
        # 生成按钮
        generate_btn = PushButton("生成内容")
        generate_btn.setIcon(FluentIcon.ADD)
        generate_btn.clicked.connect(self._generate_content)
        layout.addWidget(generate_btn)
        
        # 结果预览
        result_label = StrongBodyLabel("生成结果:")
        layout.addWidget(result_label)
        
        self.create_result = QTextBrowser()
        layout.addWidget(self.create_result)
        
        # 插入按钮
        insert_btn = PushButton("插入到文档")
        insert_btn.setIcon(FluentIcon.EDIT)
        insert_btn.clicked.connect(self._insert_generated_content)
        layout.addWidget(insert_btn)
        
        return widget
    
    def _create_chat_tab(self):
        """创建对话标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 对话历史
        self.chat_display = QTextBrowser()
        layout.addWidget(self.chat_display)
        
        # 输入区域
        input_layout = QHBoxLayout()
        
        self.chat_input = LineEdit()
        self.chat_input.setPlaceholderText("输入您的问题...")
        self.chat_input.returnPressed.connect(self._send_chat_message)
        
        send_btn = PushButton("发送")
        send_btn.setIcon(FluentIcon.SEND)
        send_btn.clicked.connect(self._send_chat_message)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # 清除按钮
        clear_btn = PushButton("清除历史")
        clear_btn.clicked.connect(self._clear_chat_history)
        layout.addWidget(clear_btn)
        
        return widget
    
    def _create_agent_tab(self):
        """创建代理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = BodyLabel("代理可以使用工具自动完成复杂任务，如创建分支、编辑多个文档等。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 任务输入
        task_label = StrongBodyLabel("任务描述:")
        layout.addWidget(task_label)
        
        self.agent_task = TextEdit()
        self.agent_task.setPlaceholderText("描述您希望代理完成的任务...")
        self.agent_task.setMaximumHeight(150)
        layout.addWidget(self.agent_task)
        
        # 执行按钮
        execute_btn = PushButton("执行任务")
        execute_btn.setIcon(FluentIcon.PLAY)
        execute_btn.clicked.connect(self._execute_agent_task)
        layout.addWidget(execute_btn)
        
        # 执行日志
        log_label = StrongBodyLabel("执行日志:")
        layout.addWidget(log_label)
        
        self.agent_log = QTextBrowser()
        layout.addWidget(self.agent_log)
        
        return widget
    
    def _create_review_tab(self):
        """创建任务审查标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = BodyLabel("审查代理完成的任务，决定是否应用更改。")
        layout.addWidget(info_label)
        
        # 待审查任务列表
        tasks_label = StrongBodyLabel("待审查任务:")
        layout.addWidget(tasks_label)
        
        self.review_list = QListWidget()
        self.review_list.itemClicked.connect(self._show_task_details)
        layout.addWidget(self.review_list)
        
        # 任务详情
        details_label = StrongBodyLabel("任务详情:")
        layout.addWidget(details_label)
        
        self.task_details = QTextBrowser()
        self.task_details.setMaximumHeight(200)
        layout.addWidget(self.task_details)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        approve_btn = PushButton("批准并应用")
        approve_btn.setIcon(FluentIcon.ACCEPT)
        approve_btn.clicked.connect(self._approve_task)
        
        reject_btn = PushButton("拒绝")
        reject_btn.setIcon(FluentIcon.CANCEL)
        reject_btn.clicked.connect(self._reject_task)
        
        btn_layout.addWidget(approve_btn)
        btn_layout.addWidget(reject_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    # 补全相关方法
    def generate_inline_completion(self, context, current_line):
        """生成行内补全"""
        if self.current_worker and self.current_worker.isRunning():
            return
        
        self.status_label.setText("生成补全中...")
        
        prompt = f"""基于以下上下文，继续写作。只输出续写的内容，不要重复已有内容。

上下文:
{context[-1000:]}

当前行: {current_line}

续写:"""
        
        self.current_worker = CompletionWorker(self.plugin.llm_client, prompt)
        self.current_worker.completed.connect(self._on_completion_ready)
        self.current_worker.failed.connect(self._on_completion_failed)
        self.current_worker.start()
    
    def _manual_trigger_completion(self):
        """手动触发补全"""
        if not hasattr(self.app, 'editor') or not self.app.editor:
            QMessageBox.warning(self, "错误", "未打开任何文档")
            return
        
        editor = self.app.editor
        cursor = editor.textCursor()
        position = cursor.position()
        
        full_text = editor.toPlainText()
        before_cursor = full_text[:position]
        
        cursor.select(cursor.LineUnderCursor)
        current_line = cursor.selectedText()
        
        self.generate_inline_completion(before_cursor, current_line)
    
    def _on_completion_ready(self, completion):
        """补全准备就绪"""
        self.completion_preview.setPlainText(completion)
        self.status_label.setText("补全已生成")
        self.current_worker = None
    
    def _on_completion_failed(self, error_msg):
        """补全失败"""
        self.completion_preview.setPlainText(f"生成失败: {error_msg}")
        self.status_label.setText("补全失败")
        self.current_worker = None
    
    def _accept_completion(self):
        """接受补全"""
        completion = self.completion_preview.toPlainText()
        if not completion or "生成失败" in completion:
            return
        
        if hasattr(self.app, 'editor') and self.app.editor:
            cursor = self.app.editor.textCursor()
            cursor.insertText(completion)
            self.completion_preview.clear()
            self.status_label.setText("补全已应用")
    
    def _reject_completion(self):
        """拒绝补全"""
        self.completion_preview.clear()
        self.status_label.setText("补全已拒绝")
    
    # 编辑相关方法
    def _perform_edit(self, operation):
        """执行编辑操作"""
        if not hasattr(self.app, 'editor') or not self.app.editor:
            QMessageBox.warning(self, "错误", "未打开任何文档")
            return
        
        editor = self.app.editor
        cursor = editor.textCursor()
        
        if not cursor.hasSelection():
            QMessageBox.information(self, "提示", "请先选择要编辑的文本")
            return
        
        selected_text = cursor.selectedText()
        
        # 构建提示
        operation_prompts = {
            'improve': "改进以下文本，提升质量和可读性:",
            'grammar': "修正以下文本的语法和拼写错误:",
            'expand': "扩展以下文本，添加更多细节和说明:",
            'simplify': "简化以下文本，使其更加简洁:",
            'rewrite': "用不同方式重写以下文本:",
        }
        
        prompt = f"{operation_prompts.get(operation, '处理以下文本:')}\n\n{selected_text}"
        
        self.status_label.setText(f"执行{operation}操作中...")
        
        self.current_worker = CompletionWorker(self.plugin.llm_client, prompt)
        self.current_worker.completed.connect(
            lambda result: self._on_edit_completed(result, cursor)
        )
        self.current_worker.failed.connect(self._on_completion_failed)
        self.current_worker.start()
    
    def _on_edit_completed(self, result, cursor):
        """编辑完成"""
        cursor.insertText(result)
        self.status_label.setText("编辑已应用")
        self.current_worker = None
    
    # 创作相关方法
    def _generate_content(self):
        """生成内容"""
        prompt = self.create_prompt.toPlainText()
        if not prompt:
            QMessageBox.information(self, "提示", "请输入创作提示")
            return
        
        self.status_label.setText("生成内容中...")
        
        full_prompt = f"根据以下要求创作内容:\n\n{prompt}"
        
        self.current_worker = CompletionWorker(self.plugin.llm_client, full_prompt)
        self.current_worker.completed.connect(self._on_create_completed)
        self.current_worker.failed.connect(self._on_completion_failed)
        self.current_worker.start()
    
    def _on_create_completed(self, result):
        """创作完成"""
        self.create_result.setPlainText(result)
        self.status_label.setText("内容已生成")
        self.current_worker = None
    
    def _insert_generated_content(self):
        """插入生成的内容"""
        content = self.create_result.toPlainText()
        if not content:
            return
        
        if hasattr(self.app, 'editor') and self.app.editor:
            cursor = self.app.editor.textCursor()
            cursor.insertText(content)
            self.status_label.setText("内容已插入")
    
    # 对话相关方法
    def _send_chat_message(self):
        """发送聊天消息"""
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # 添加到历史
        self.chat_history.append(("user", message))
        self._update_chat_display()
        
        self.chat_input.clear()
        self.status_label.setText("等待回复...")
        
        # 获取上下文
        context = ""
        if hasattr(self.app, 'editor') and self.app.editor:
            context = self.app.editor.toPlainText()
        
        self.current_worker = ChatWorker(self.plugin.llm_client, message, context)
        self.current_worker.responded.connect(self._on_chat_response)
        self.current_worker.failed.connect(self._on_completion_failed)
        self.current_worker.start()
    
    def _on_chat_response(self, response):
        """收到聊天回复"""
        self.chat_history.append(("assistant", response))
        self._update_chat_display()
        self.status_label.setText("就绪")
        self.current_worker = None
    
    def _update_chat_display(self):
        """更新聊天显示"""
        html = "<div style='font-family: sans-serif;'>"
        for role, content in self.chat_history:
            if role == "user":
                html += f"<div style='margin: 10px; padding: 10px; background: #E3F2FD; border-radius: 5px;'><strong>您:</strong><br>{content}</div>"
            else:
                html += f"<div style='margin: 10px; padding: 10px; background: #F5F5F5; border-radius: 5px;'><strong>助手:</strong><br>{content}</div>"
        html += "</div>"
        
        self.chat_display.setHtml(html)
        # 滚动到底部
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _clear_chat_history(self):
        """清除聊天历史"""
        self.chat_history.clear()
        self.chat_display.clear()
    
    # 代理相关方法
    def _execute_agent_task(self):
        """执行代理任务"""
        task = self.agent_task.toPlainText()
        if not task:
            QMessageBox.information(self, "提示", "请输入任务描述")
            return
        
        if not self.plugin.agent_executor:
            QMessageBox.warning(self, "错误", "代理执行器未初始化")
            return
        
        self.status_label.setText("执行代理任务中...")
        self.agent_log.clear()
        self.agent_log.append(f"开始执行任务: {task}\n")
        
        self.current_worker = AgentWorker(self.plugin.agent_executor, task)
        self.current_worker.completed.connect(self._on_agent_completed)
        self.current_worker.failed.connect(self._on_agent_failed)
        self.current_worker.start()
    
    def _on_agent_completed(self, output, task_info):
        """代理任务完成"""
        self.agent_log.append(f"\n任务完成!\n\n结果:\n{output}")
        self.status_label.setText("任务已完成")
        
        # 如果启用了审查，添加到待审查列表
        if self.plugin.get_setting('enable_task_review', True):
            self.pending_tasks.append(task_info)
            self._update_review_list()
            self.agent_log.append("\n\n任务已添加到审查队列")
        
        self.current_worker = None
    
    def _on_agent_failed(self, error_msg):
        """代理任务失败"""
        self.agent_log.append(f"\n\n任务失败: {error_msg}")
        self.status_label.setText("任务失败")
        self.current_worker = None
    
    # 审查相关方法
    def _update_review_list(self):
        """更新审查列表"""
        self.review_list.clear()
        for i, task in enumerate(self.pending_tasks):
            item = QListWidgetItem(f"任务 {i+1}: {task['task'][:50]}...")
            item.setData(Qt.UserRole, i)
            self.review_list.addItem(item)
    
    def _show_task_details(self, item):
        """显示任务详情"""
        index = item.data(Qt.UserRole)
        if 0 <= index < len(self.pending_tasks):
            task = self.pending_tasks[index]
            
            details = f"任务: {task['task']}\n\n"
            details += f"输出:\n{task['output']}\n\n"
            
            if task.get('intermediate_steps'):
                details += "执行步骤:\n"
                for step in task['intermediate_steps']:
                    details += f"- {step}\n"
            
            self.task_details.setPlainText(details)
    
    def _approve_task(self):
        """批准任务"""
        current_item = self.review_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请选择要批准的任务")
            return
        
        index = current_item.data(Qt.UserRole)
        if 0 <= index < len(self.pending_tasks):
            task = self.pending_tasks.pop(index)
            self._update_review_list()
            self.task_details.clear()
            
            QMessageBox.information(self, "成功", "任务已批准并应用")
            info(f"任务已批准: {task['task']}")
    
    def _reject_task(self):
        """拒绝任务"""
        current_item = self.review_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "提示", "请选择要拒绝的任务")
            return
        
        index = current_item.data(Qt.UserRole)
        if 0 <= index < len(self.pending_tasks):
            task = self.pending_tasks.pop(index)
            self._update_review_list()
            self.task_details.clear()
            
            QMessageBox.information(self, "已拒绝", "任务已被拒绝")
            info(f"任务已拒绝: {task['task']}")
