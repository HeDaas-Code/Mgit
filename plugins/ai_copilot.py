#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Copilot插件 - 基于SiliconFlow API的AI助手
提供文档自动化、智能写作辅助和AI对话功能

功能特性:
- 文档摘要生成
- 内容续写和生成
- 语法和写作改进建议
- Markdown格式化辅助
- 智能问答对话

安全措施:
- API密钥混淆存储(XOR+Base64编码,非加密)
- 输入验证和长度限制
- HTTPS强制
- 速率限制
"""

import json
import re
import os
import time
import base64
import hashlib
import threading
from typing import Optional, Dict, Any, List, Callable, Tuple
from functools import wraps

import requests

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QLineEdit, QComboBox, QGroupBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QScrollArea, QFrame, QSplitter,
    QMessageBox, QProgressBar, QTabWidget, QPlainTextEdit,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QTextCursor

from src.utils.plugin_base import PluginBase


# ============== 安全工具类 ==============

class SecurityUtils:
    """安全工具类 - 提供加密和验证功能"""
    
    @staticmethod
    def get_machine_id() -> str:
        """获取机器唯一标识用于密钥派生"""
        try:
            import platform
            import uuid
            machine_info = f"{platform.node()}-{uuid.getnode()}"
            return hashlib.sha256(machine_info.encode()).hexdigest()[:32]
        except Exception:
            return "default_key_mgit_copilot_2024"
    
    @staticmethod
    def encode_api_key(api_key: str) -> str:
        """编码API密钥(简单混淆,非加密)"""
        if not api_key:
            return ""
        try:
            # 使用base64编码和简单XOR混淆
            machine_id = SecurityUtils.get_machine_id()
            key_bytes = api_key.encode('utf-8')
            xor_key = machine_id.encode('utf-8')
            
            # XOR混淆
            xored = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(key_bytes))
            # Base64编码
            encoded = base64.b64encode(xored).decode('utf-8')
            return encoded
        except Exception:
            return base64.b64encode(api_key.encode()).decode()
    
    @staticmethod
    def decode_api_key(encoded_key: str) -> str:
        """解码API密钥"""
        if not encoded_key:
            return ""
        try:
            machine_id = SecurityUtils.get_machine_id()
            xor_key = machine_id.encode('utf-8')
            
            # Base64解码
            xored = base64.b64decode(encoded_key.encode('utf-8'))
            # XOR还原
            key_bytes = bytes(b ^ xor_key[i % len(xor_key)] for i, b in enumerate(xored))
            return key_bytes.decode('utf-8')
        except Exception:
            try:
                return base64.b64decode(encoded_key.encode()).decode()
            except Exception:
                return ""
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 100000) -> str:
        """清理和验证输入文本
        
        注意: 此函数主要用于长度限制和基本清理。
        由于文本将发送到AI API进行处理,不会执行本地代码,
        因此主要风险是超长输入导致的资源耗尽。
        
        Args:
            text: 输入文本
            max_length: 最大长度限制
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        # 限制长度防止资源耗尽
        text = text[:max_length]
        # 去除首尾空白
        return text.strip()
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key:
            return False
        # SiliconFlow API密钥通常是sk-开头的字符串
        # 但也接受其他格式
        if len(api_key) < 10:
            return False
        return True


# ============== API客户端 ==============

class SiliconFlowAPIError(Exception):
    """SiliconFlow API错误"""
    pass


class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        """初始化速率限制器
        
        Args:
            max_requests: 时间窗口内允许的最大请求数,默认30
            time_window: 时间窗口(秒),默认60
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self.lock = threading.Lock()
    
    def can_make_request(self) -> bool:
        """检查是否可以发起请求"""
        with self.lock:
            current_time = time.time()
            # 清理过期的请求记录
            self.requests = [t for t in self.requests if current_time - t < self.time_window]
            return len(self.requests) < self.max_requests
    
    def record_request(self):
        """记录一次请求"""
        with self.lock:
            self.requests.append(time.time())


class SiliconFlowClient:
    """SiliconFlow API客户端"""
    
    # 默认API端点
    DEFAULT_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    
    # 可用模型列表(使用元组使其不可变)
    AVAILABLE_MODELS: Tuple[str, ...] = (
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "deepseek-ai/DeepSeek-V2.5",
        "deepseek-ai/DeepSeek-V3",
        "THUDM/glm-4-9b-chat",
        "01-ai/Yi-1.5-9B-Chat",
        "internlm/internlm2_5-7b-chat",
    )
    
    def __init__(self, api_key: str = "", model: str = "Qwen/Qwen2.5-7B-Instruct"):
        self.api_key = api_key
        self.model = model
        self.api_url = self.DEFAULT_API_URL
        self.rate_limiter = RateLimiter(max_requests=30, time_window=60)
        self.timeout = 60
        self.max_retries = 3
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key = api_key
    
    def set_model(self, model: str):
        """设置模型"""
        if model in self.AVAILABLE_MODELS or model:
            self.model = model
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        调用聊天补全API
        
        Args:
            messages: 消息列表,格式为[{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数(0-2)
            max_tokens: 最大生成token数
            stream: 是否使用流式输出
            callback: 流式输出时的回调函数
            
        Returns:
            生成的文本内容
        """
        if not self.api_key:
            raise SiliconFlowAPIError("API密钥未设置")
        
        if not SecurityUtils.validate_api_key(self.api_key):
            raise SiliconFlowAPIError("API密钥格式无效")
        
        if not self.rate_limiter.can_make_request():
            raise SiliconFlowAPIError("请求过于频繁,请稍后再试")
        
        self.rate_limiter.record_request()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": max(0, min(2, temperature)),
            "max_tokens": max(1, min(4096, max_tokens)),
            "stream": stream
        }
        
        for attempt in range(self.max_retries):
            try:
                if stream and callback:
                    return self._stream_request(headers, payload, callback)
                else:
                    response = requests.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    elif response.status_code == 401:
                        raise SiliconFlowAPIError("API密钥无效或已过期")
                    elif response.status_code == 429:
                        raise SiliconFlowAPIError("API请求达到限制,请稍后再试")
                    elif response.status_code >= 500:
                        if attempt < self.max_retries - 1:
                            time.sleep(2 ** attempt)
                            continue
                        raise SiliconFlowAPIError(f"服务器错误: {response.status_code}")
                    else:
                        # 安全地解析错误响应
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("error", {}).get("message", response.text)
                        except (json.JSONDecodeError, ValueError):
                            error_msg = response.text
                        raise SiliconFlowAPIError(f"API错误: {error_msg}")
                        
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    continue
                raise SiliconFlowAPIError("请求超时,请检查网络连接")
            except requests.exceptions.ConnectionError:
                raise SiliconFlowAPIError("网络连接失败,请检查网络")
            except requests.exceptions.RequestException as e:
                raise SiliconFlowAPIError(f"请求失败: {str(e)}")
        
        raise SiliconFlowAPIError("请求失败,已达最大重试次数")
    
    def _stream_request(
        self, 
        headers: Dict, 
        payload: Dict, 
        callback: Callable[[str], None]
    ) -> str:
        """处理流式请求"""
        full_content = ""
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
            stream=True
        )
        
        if response.status_code != 200:
            error_msg = response.text
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", error_msg)
            except Exception:
                pass
            raise SiliconFlowAPIError(f"API错误: {error_msg}")
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content += content
                            callback(content)
                    except json.JSONDecodeError:
                        continue
        
        return full_content


# ============== AI工作线程 ==============

class AIWorkerThread(QThread):
    """AI请求工作线程"""
    
    # 信号定义
    chunk_received = pyqtSignal(str)  # 流式输出块
    completed = pyqtSignal(str)  # 完成
    error = pyqtSignal(str)  # 错误
    
    def __init__(self, client: SiliconFlowClient, messages: List[Dict], 
                 temperature: float = 0.7, max_tokens: int = 2048, 
                 stream: bool = True):
        super().__init__()
        self.client = client
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream
        self._is_cancelled = False
    
    def run(self):
        """执行请求"""
        try:
            if self.stream:
                result = self.client.chat_completion(
                    messages=self.messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True,
                    callback=self._on_chunk
                )
            else:
                result = self.client.chat_completion(
                    messages=self.messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=False
                )
            
            if not self._is_cancelled:
                self.completed.emit(result)
                
        except SiliconFlowAPIError as e:
            if not self._is_cancelled:
                self.error.emit(str(e))
        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"未知错误: {str(e)}")
    
    def _on_chunk(self, chunk: str):
        """处理流式输出块"""
        if not self._is_cancelled:
            self.chunk_received.emit(chunk)
    
    def cancel(self):
        """取消请求"""
        self._is_cancelled = True


# ============== UI组件 ==============

class ChatWidget(QWidget):
    """聊天界面组件"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.conversation_history = []
        self.current_worker = None
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 聊天历史显示区域
        self.chatDisplay = QTextEdit()
        self.chatDisplay.setReadOnly(True)
        self.chatDisplay.setFont(QFont("Consolas", 10))
        self.chatDisplay.setPlaceholderText("与AI助手对话...\n\n提示：可以询问关于写作、编程、Markdown格式等问题")
        layout.addWidget(self.chatDisplay, stretch=1)
        
        # 输入区域
        inputLayout = QHBoxLayout()
        
        self.inputEdit = QPlainTextEdit()
        self.inputEdit.setMaximumHeight(80)
        self.inputEdit.setPlaceholderText("输入您的问题... (Ctrl+Enter发送)")
        inputLayout.addWidget(self.inputEdit, stretch=1)
        
        # 发送按钮
        btnLayout = QVBoxLayout()
        self.sendBtn = QPushButton("发送")
        self.sendBtn.clicked.connect(self.sendMessage)
        self.sendBtn.setMinimumWidth(60)
        btnLayout.addWidget(self.sendBtn)
        
        self.clearBtn = QPushButton("清空")
        self.clearBtn.clicked.connect(self.clearConversation)
        self.clearBtn.setMinimumWidth(60)
        btnLayout.addWidget(self.clearBtn)
        
        btnLayout.addStretch()
        inputLayout.addLayout(btnLayout)
        
        layout.addLayout(inputLayout)
        
        # 状态栏
        self.statusLabel = QLabel("就绪")
        self.statusLabel.setStyleSheet("color: gray;")
        layout.addWidget(self.statusLabel)
        
        # 快捷键
        self.inputEdit.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理快捷键"""
        from PyQt5.QtCore import QEvent
        from PyQt5.QtGui import QKeyEvent
        
        if obj == self.inputEdit and event.type() == QEvent.KeyPress:
            key_event = event
            if key_event.key() == Qt.Key_Return and key_event.modifiers() == Qt.ControlModifier:
                self.sendMessage()
                return True
        return super().eventFilter(obj, event)
    
    def sendMessage(self):
        """发送消息"""
        text = self.inputEdit.toPlainText().strip()
        if not text:
            return
        
        # 检查API密钥
        if not self.plugin.get_api_key():
            QMessageBox.warning(self, "提示", "请先在设置中配置API密钥")
            return
        
        # 清空输入
        self.inputEdit.clear()
        
        # 添加用户消息到显示
        self.appendMessage("用户", text)
        
        # 添加到历史
        self.conversation_history.append({"role": "user", "content": text})
        
        # 构建消息列表(包含系统提示)
        system_prompt = self.plugin.get_setting('system_prompt', 
            "你是一个专业的AI写作助手,擅长帮助用户撰写和改进文档、回答问题、提供写作建议。请用中文回复。")
        
        messages = [{"role": "system", "content": system_prompt}]
        # 保留最近10轮对话(每轮包含用户+助手消息,共20条)
        messages.extend(self.conversation_history[-20:])
        
        # 禁用发送按钮
        self.sendBtn.setEnabled(False)
        self.statusLabel.setText("AI正在思考...")
        self.statusLabel.setStyleSheet("color: blue;")
        
        # 添加AI响应占位
        self.appendMessage("AI助手", "", is_streaming=True)
        
        # 创建工作线程
        client = self.plugin.get_client()
        self.current_worker = AIWorkerThread(
            client=client,
            messages=messages,
            temperature=self.plugin.get_setting('temperature', 0.7),
            max_tokens=self.plugin.get_setting('max_tokens', 2048),
            stream=self.plugin.get_setting('stream_output', True)
        )
        
        self.current_worker.chunk_received.connect(self.onChunkReceived)
        self.current_worker.completed.connect(self.onCompleted)
        self.current_worker.error.connect(self.onError)
        self.current_worker.start()
    
    def appendMessage(self, role: str, content: str, is_streaming: bool = False):
        """添加消息到显示区域"""
        cursor = self.chatDisplay.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if role == "用户":
            cursor.insertHtml(f'<p style="color: #2196F3;"><b>🧑 {role}:</b></p>')
        else:
            cursor.insertHtml(f'<p style="color: #4CAF50;"><b>🤖 {role}:</b></p>')
        
        if content:
            cursor.insertHtml(f'<p style="margin-left: 20px; white-space: pre-wrap;">{content}</p>')
        
        cursor.insertHtml('<br>')
        
        self.chatDisplay.setTextCursor(cursor)
        self.chatDisplay.ensureCursorVisible()
    
    def onChunkReceived(self, chunk: str):
        """处理流式输出块"""
        cursor = self.chatDisplay.textCursor()
        cursor.movePosition(QTextCursor.End)
        # 转义HTML特殊字符但保留换行
        escaped = chunk.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped = escaped.replace('\n', '<br>')
        cursor.insertHtml(escaped)
        self.chatDisplay.setTextCursor(cursor)
        self.chatDisplay.ensureCursorVisible()
    
    def onCompleted(self, result: str):
        """处理完成"""
        # 保存到历史
        self.conversation_history.append({"role": "assistant", "content": result})
        
        # 更新状态
        self.sendBtn.setEnabled(True)
        self.statusLabel.setText("完成")
        self.statusLabel.setStyleSheet("color: green;")
        
        self.current_worker = None
    
    def onError(self, error_msg: str):
        """处理错误"""
        cursor = self.chatDisplay.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(f'<p style="color: red;">❌ 错误: {error_msg}</p><br>')
        self.chatDisplay.setTextCursor(cursor)
        
        self.sendBtn.setEnabled(True)
        self.statusLabel.setText(f"错误: {error_msg}")
        self.statusLabel.setStyleSheet("color: red;")
        
        self.current_worker = None
    
    def clearConversation(self):
        """清空对话"""
        self.conversation_history.clear()
        self.chatDisplay.clear()
        self.statusLabel.setText("对话已清空")
        self.statusLabel.setStyleSheet("color: gray;")


class DocumentAssistantWidget(QWidget):
    """文档助手界面"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.current_worker = None
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 功能选择
        funcGroup = QGroupBox("文档处理功能")
        funcLayout = QHBoxLayout(funcGroup)
        
        self.summarizeBtn = QPushButton("📝 生成摘要")
        self.summarizeBtn.clicked.connect(lambda: self.processDocument("summarize"))
        funcLayout.addWidget(self.summarizeBtn)
        
        self.continueBtn = QPushButton("✍️ 续写内容")
        self.continueBtn.clicked.connect(lambda: self.processDocument("continue"))
        funcLayout.addWidget(self.continueBtn)
        
        self.improveBtn = QPushButton("🔧 改进写作")
        self.improveBtn.clicked.connect(lambda: self.processDocument("improve"))
        funcLayout.addWidget(self.improveBtn)
        
        self.formatBtn = QPushButton("📋 格式优化")
        self.formatBtn.clicked.connect(lambda: self.processDocument("format"))
        funcLayout.addWidget(self.formatBtn)
        
        layout.addWidget(funcGroup)
        
        # 分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 输入区域
        inputGroup = QGroupBox("输入文本 (可直接粘贴或从编辑器获取)")
        inputLayout = QVBoxLayout(inputGroup)
        
        inputBtnLayout = QHBoxLayout()
        self.getEditorBtn = QPushButton("从编辑器获取")
        self.getEditorBtn.clicked.connect(self.getEditorContent)
        inputBtnLayout.addWidget(self.getEditorBtn)
        
        self.getSelectedBtn = QPushButton("获取选中文本")
        self.getSelectedBtn.clicked.connect(self.getSelectedContent)
        inputBtnLayout.addWidget(self.getSelectedBtn)
        
        inputBtnLayout.addStretch()
        inputLayout.addLayout(inputBtnLayout)
        
        self.inputText = QTextEdit()
        self.inputText.setPlaceholderText("在此粘贴或输入要处理的文本...")
        inputLayout.addWidget(self.inputText)
        
        splitter.addWidget(inputGroup)
        
        # 输出区域
        outputGroup = QGroupBox("处理结果")
        outputLayout = QVBoxLayout(outputGroup)
        
        outputBtnLayout = QHBoxLayout()
        self.copyBtn = QPushButton("复制结果")
        self.copyBtn.clicked.connect(self.copyResult)
        outputBtnLayout.addWidget(self.copyBtn)
        
        self.insertBtn = QPushButton("插入到编辑器")
        self.insertBtn.clicked.connect(self.insertToEditor)
        outputBtnLayout.addWidget(self.insertBtn)
        
        self.replaceBtn = QPushButton("替换编辑器内容")
        self.replaceBtn.clicked.connect(self.replaceEditorContent)
        outputBtnLayout.addWidget(self.replaceBtn)
        
        outputBtnLayout.addStretch()
        outputLayout.addLayout(outputBtnLayout)
        
        self.outputText = QTextEdit()
        self.outputText.setReadOnly(True)
        self.outputText.setPlaceholderText("处理结果将显示在这里...")
        outputLayout.addWidget(self.outputText)
        
        splitter.addWidget(outputGroup)
        
        layout.addWidget(splitter, stretch=1)
        
        # 状态栏
        statusLayout = QHBoxLayout()
        self.statusLabel = QLabel("就绪")
        self.statusLabel.setStyleSheet("color: gray;")
        statusLayout.addWidget(self.statusLabel)
        
        self.progressBar = QProgressBar()
        self.progressBar.setMaximumWidth(150)
        self.progressBar.setVisible(False)
        statusLayout.addWidget(self.progressBar)
        
        layout.addLayout(statusLayout)
    
    def getEditorContent(self):
        """从编辑器获取内容"""
        content = self.plugin.getCurrentEditorContent()
        if content:
            self.inputText.setPlainText(content)
            self.statusLabel.setText("已获取编辑器内容")
        else:
            QMessageBox.information(self, "提示", "无法获取编辑器内容")
    
    def getSelectedContent(self):
        """获取选中的文本"""
        content = self.plugin.getSelectedText()
        if content:
            self.inputText.setPlainText(content)
            self.statusLabel.setText("已获取选中文本")
        else:
            QMessageBox.information(self, "提示", "没有选中的文本")
    
    def copyResult(self):
        """复制结果到剪贴板"""
        text = self.outputText.toPlainText()
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.statusLabel.setText("已复制到剪贴板")
    
    def insertToEditor(self):
        """将结果插入到编辑器"""
        text = self.outputText.toPlainText()
        if text:
            if self.plugin.insertToEditor(text):
                self.statusLabel.setText("已插入到编辑器")
            else:
                QMessageBox.warning(self, "提示", "无法插入到编辑器")
    
    def replaceEditorContent(self):
        """替换编辑器内容"""
        text = self.outputText.toPlainText()
        if text:
            reply = QMessageBox.question(
                self, "确认", 
                "确定要替换编辑器中的全部内容吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if self.plugin.replaceEditorContent(text):
                    self.statusLabel.setText("已替换编辑器内容")
                else:
                    QMessageBox.warning(self, "提示", "无法替换编辑器内容")
    
    def processDocument(self, action: str):
        """处理文档"""
        text = self.inputText.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入或获取要处理的文本")
            return
        
        # 检查API密钥
        if not self.plugin.get_api_key():
            QMessageBox.warning(self, "提示", "请先在设置中配置API密钥")
            return
        
        # 构建提示词
        prompts = {
            "summarize": f"""请为以下文档生成一个简洁的摘要,突出关键信息和主要观点:

{text}

请用中文回复,摘要应该简洁明了,不超过原文长度的1/3。""",
            
            "continue": f"""请根据以下文档的内容和风格,继续写作:

{text}

请保持与原文一致的语言风格、格式和主题,自然地续写内容。如果是Markdown格式,请保持格式一致。""",
            
            "improve": f"""请改进以下文档的写作质量,包括:
- 修正语法和拼写错误
- 改进句子结构和表达
- 提高文章的逻辑性和连贯性
- 保持原文的核心意思不变

原文:
{text}

请直接给出改进后的版本,不需要解释修改了什么。""",
            
            "format": f"""请优化以下文档的Markdown格式,使其更加规范和美观:
- 添加适当的标题层级
- 优化列表格式
- 添加代码块格式(如果有代码)
- 优化段落分隔
- 保持内容不变,只优化格式

原文:
{text}

请直接给出格式优化后的版本。"""
        }
        
        prompt = prompts.get(action, prompts["improve"])
        
        # 清空输出
        self.outputText.clear()
        
        # 禁用按钮
        self.setButtonsEnabled(False)
        self.statusLabel.setText("正在处理...")
        self.statusLabel.setStyleSheet("color: blue;")
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)  # 无限进度条
        
        # 创建工作线程
        client = self.plugin.get_client()
        messages = [
            {"role": "system", "content": "你是一个专业的文档编辑助手。请直接给出处理结果,不需要额外解释。"},
            {"role": "user", "content": prompt}
        ]
        
        self.current_worker = AIWorkerThread(
            client=client,
            messages=messages,
            temperature=self.plugin.get_setting('temperature', 0.7),
            max_tokens=self.plugin.get_setting('max_tokens', 2048),
            stream=self.plugin.get_setting('stream_output', True)
        )
        
        self.current_worker.chunk_received.connect(self.onChunkReceived)
        self.current_worker.completed.connect(self.onCompleted)
        self.current_worker.error.connect(self.onError)
        self.current_worker.start()
    
    def setButtonsEnabled(self, enabled: bool):
        """设置按钮启用状态"""
        self.summarizeBtn.setEnabled(enabled)
        self.continueBtn.setEnabled(enabled)
        self.improveBtn.setEnabled(enabled)
        self.formatBtn.setEnabled(enabled)
    
    def onChunkReceived(self, chunk: str):
        """处理流式输出块"""
        cursor = self.outputText.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        self.outputText.setTextCursor(cursor)
        self.outputText.ensureCursorVisible()
    
    def onCompleted(self, result: str):
        """处理完成"""
        self.setButtonsEnabled(True)
        self.statusLabel.setText("处理完成")
        self.statusLabel.setStyleSheet("color: green;")
        self.progressBar.setVisible(False)
        self.current_worker = None
    
    def onError(self, error_msg: str):
        """处理错误"""
        self.outputText.setPlainText(f"错误: {error_msg}")
        self.setButtonsEnabled(True)
        self.statusLabel.setText(f"错误: {error_msg}")
        self.statusLabel.setStyleSheet("color: red;")
        self.progressBar.setVisible(False)
        self.current_worker = None


class SettingsWidget(QWidget):
    """设置界面"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scrollContent = QWidget()
        scrollLayout = QVBoxLayout(scrollContent)
        
        # API设置组
        apiGroup = QGroupBox("API配置")
        apiLayout = QVBoxLayout(apiGroup)
        
        # API密钥
        keyLayout = QHBoxLayout()
        keyLayout.addWidget(QLabel("API密钥:"))
        self.apiKeyEdit = QLineEdit()
        self.apiKeyEdit.setEchoMode(QLineEdit.Password)
        self.apiKeyEdit.setPlaceholderText("输入SiliconFlow API密钥 (sk-...)")
        keyLayout.addWidget(self.apiKeyEdit)
        
        self.showKeyBtn = QPushButton("显示")
        self.showKeyBtn.setCheckable(True)
        self.showKeyBtn.toggled.connect(self.toggleKeyVisibility)
        keyLayout.addWidget(self.showKeyBtn)
        
        apiLayout.addLayout(keyLayout)
        
        # 模型选择
        modelLayout = QHBoxLayout()
        modelLayout.addWidget(QLabel("模型:"))
        self.modelCombo = QComboBox()
        for model in SiliconFlowClient.AVAILABLE_MODELS:
            self.modelCombo.addItem(model)
        modelLayout.addWidget(self.modelCombo, stretch=1)
        apiLayout.addLayout(modelLayout)
        
        # 自定义模型
        customModelLayout = QHBoxLayout()
        customModelLayout.addWidget(QLabel("自定义模型:"))
        self.customModelEdit = QLineEdit()
        self.customModelEdit.setPlaceholderText("留空使用上方选择的模型")
        customModelLayout.addWidget(self.customModelEdit, stretch=1)
        apiLayout.addLayout(customModelLayout)
        
        scrollLayout.addWidget(apiGroup)
        
        # 生成参数组
        paramGroup = QGroupBox("生成参数")
        paramLayout = QVBoxLayout(paramGroup)
        
        # Temperature
        tempLayout = QHBoxLayout()
        tempLayout.addWidget(QLabel("温度 (Temperature):"))
        self.tempSpin = QDoubleSpinBox()
        self.tempSpin.setRange(0.0, 2.0)
        self.tempSpin.setSingleStep(0.1)
        self.tempSpin.setValue(0.7)
        self.tempSpin.setToolTip("控制生成的随机性,越高越有创意,越低越确定性")
        tempLayout.addWidget(self.tempSpin)
        tempLayout.addStretch()
        paramLayout.addLayout(tempLayout)
        
        # Max tokens
        tokensLayout = QHBoxLayout()
        tokensLayout.addWidget(QLabel("最大Token数:"))
        self.tokensSpin = QSpinBox()
        self.tokensSpin.setRange(100, 4096)
        self.tokensSpin.setSingleStep(100)
        self.tokensSpin.setValue(2048)
        self.tokensSpin.setToolTip("生成内容的最大长度")
        tokensLayout.addWidget(self.tokensSpin)
        tokensLayout.addStretch()
        paramLayout.addLayout(tokensLayout)
        
        # 流式输出
        self.streamCheck = QCheckBox("启用流式输出 (实时显示生成内容)")
        self.streamCheck.setChecked(True)
        paramLayout.addWidget(self.streamCheck)
        
        scrollLayout.addWidget(paramGroup)
        
        # 系统提示词
        promptGroup = QGroupBox("系统提示词")
        promptLayout = QVBoxLayout(promptGroup)
        
        self.systemPromptEdit = QTextEdit()
        self.systemPromptEdit.setMaximumHeight(100)
        self.systemPromptEdit.setPlaceholderText("自定义AI助手的行为...")
        promptLayout.addWidget(self.systemPromptEdit)
        
        resetPromptBtn = QPushButton("重置为默认")
        resetPromptBtn.clicked.connect(self.resetSystemPrompt)
        promptLayout.addWidget(resetPromptBtn)
        
        scrollLayout.addWidget(promptGroup)
        
        # 安全设置
        securityGroup = QGroupBox("安全设置")
        securityLayout = QVBoxLayout(securityGroup)
        
        self.encryptKeyCheck = QCheckBox("加密存储API密钥 (推荐)")
        self.encryptKeyCheck.setChecked(True)
        securityLayout.addWidget(self.encryptKeyCheck)
        
        securityLayout.addWidget(QLabel(
            "⚠️ 注意: API密钥存储在本地配置文件中。\n"
            "请勿在公共计算机上保存密钥。"
        ))
        
        scrollLayout.addWidget(securityGroup)
        
        scrollLayout.addStretch()
        
        scroll.setWidget(scrollContent)
        layout.addWidget(scroll)
        
        # 保存按钮
        btnLayout = QHBoxLayout()
        btnLayout.addStretch()
        
        self.testBtn = QPushButton("测试连接")
        self.testBtn.clicked.connect(self.testConnection)
        btnLayout.addWidget(self.testBtn)
        
        self.saveBtn = QPushButton("保存设置")
        self.saveBtn.clicked.connect(self.saveSettings)
        btnLayout.addWidget(self.saveBtn)
        
        layout.addLayout(btnLayout)
        
        # 加载当前设置
        self.loadSettings()
    
    def toggleKeyVisibility(self, show: bool):
        """切换密钥可见性"""
        if show:
            self.apiKeyEdit.setEchoMode(QLineEdit.Normal)
            self.showKeyBtn.setText("隐藏")
        else:
            self.apiKeyEdit.setEchoMode(QLineEdit.Password)
            self.showKeyBtn.setText("显示")
    
    def loadSettings(self):
        """加载设置"""
        # API密钥
        api_key = self.plugin.get_api_key()
        if api_key:
            self.apiKeyEdit.setText(api_key)
        
        # 模型
        model = self.plugin.get_setting('model', 'Qwen/Qwen2.5-7B-Instruct')
        index = self.modelCombo.findText(model)
        if index >= 0:
            self.modelCombo.setCurrentIndex(index)
        else:
            self.customModelEdit.setText(model)
        
        # 参数
        self.tempSpin.setValue(self.plugin.get_setting('temperature', 0.7))
        self.tokensSpin.setValue(self.plugin.get_setting('max_tokens', 2048))
        self.streamCheck.setChecked(self.plugin.get_setting('stream_output', True))
        
        # 系统提示词
        default_prompt = "你是一个专业的AI写作助手,擅长帮助用户撰写和改进文档、回答问题、提供写作建议。请用中文回复。"
        self.systemPromptEdit.setPlainText(
            self.plugin.get_setting('system_prompt', default_prompt)
        )
        
        # 安全设置
        self.encryptKeyCheck.setChecked(self.plugin.get_setting('encrypt_key', True))
    
    def saveSettings(self):
        """保存设置"""
        # API密钥
        api_key = self.apiKeyEdit.text().strip()
        encrypt = self.encryptKeyCheck.isChecked()
        
        if api_key:
            if encrypt:
                encoded_key = SecurityUtils.encode_api_key(api_key)
                self.plugin.set_setting('api_key_encoded', encoded_key)
                self.plugin.set_setting('api_key', '')  # 清除明文
            else:
                self.plugin.set_setting('api_key', api_key)
                self.plugin.set_setting('api_key_encoded', '')
        
        # 模型
        custom_model = self.customModelEdit.text().strip()
        if custom_model:
            self.plugin.set_setting('model', custom_model)
        else:
            self.plugin.set_setting('model', self.modelCombo.currentText())
        
        # 参数
        self.plugin.set_setting('temperature', self.tempSpin.value())
        self.plugin.set_setting('max_tokens', self.tokensSpin.value())
        self.plugin.set_setting('stream_output', self.streamCheck.isChecked())
        self.plugin.set_setting('encrypt_key', encrypt)
        
        # 系统提示词
        self.plugin.set_setting('system_prompt', self.systemPromptEdit.toPlainText())
        
        QMessageBox.information(self, "成功", "设置已保存")
    
    def resetSystemPrompt(self):
        """重置系统提示词"""
        default_prompt = "你是一个专业的AI写作助手,擅长帮助用户撰写和改进文档、回答问题、提供写作建议。请用中文回复。"
        self.systemPromptEdit.setPlainText(default_prompt)
    
    def testConnection(self):
        """测试API连接"""
        api_key = self.apiKeyEdit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入API密钥")
            return
        
        self.testBtn.setEnabled(False)
        self.testBtn.setText("测试中...")
        
        # 创建临时客户端进行测试
        client = SiliconFlowClient(api_key=api_key)
        
        custom_model = self.customModelEdit.text().strip()
        if custom_model:
            client.set_model(custom_model)
        else:
            client.set_model(self.modelCombo.currentText())
        
        try:
            # 发送简单测试消息
            result = client.chat_completion(
                messages=[{"role": "user", "content": "Hello, please respond with 'OK' only."}],
                max_tokens=10,
                temperature=0.1
            )
            
            if result:
                QMessageBox.information(self, "成功", f"API连接成功!\n响应: {result[:100]}")
            else:
                QMessageBox.warning(self, "警告", "API返回空响应")
                
        except SiliconFlowAPIError as e:
            QMessageBox.critical(self, "错误", f"API连接失败:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"连接失败:\n{str(e)}")
        finally:
            self.testBtn.setEnabled(True)
            self.testBtn.setText("测试连接")


class CopilotMainWidget(QWidget):
    """AI Copilot主界面"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题栏
        titleBar = QWidget()
        titleBar.setStyleSheet("background-color: #673AB7; color: white;")
        titleBar.setFixedHeight(40)
        titleLayout = QHBoxLayout(titleBar)
        titleLayout.setContentsMargins(10, 0, 10, 0)
        
        titleLabel = QLabel("🤖 AI Copilot - 智能写作助手")
        titleLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        titleLayout.addWidget(titleLabel)
        
        titleLayout.addStretch()
        
        layout.addWidget(titleBar)
        
        # 选项卡
        self.tabs = QTabWidget()
        
        # 聊天标签
        self.chatWidget = ChatWidget(self.plugin)
        self.tabs.addTab(self.chatWidget, "💬 AI对话")
        
        # 文档助手标签
        self.docWidget = DocumentAssistantWidget(self.plugin)
        self.tabs.addTab(self.docWidget, "📄 文档助手")
        
        # 设置标签
        self.settingsWidget = SettingsWidget(self.plugin)
        self.tabs.addTab(self.settingsWidget, "⚙️ 设置")
        
        layout.addWidget(self.tabs)


# ============== 插件主类 ==============

class Plugin(PluginBase):
    """AI Copilot插件 - 基于SiliconFlow API的智能写作助手"""
    
    # 插件元数据
    name = "AI Copilot"
    version = "1.0.0"
    author = "MGit团队"
    description = "基于SiliconFlow API的AI智能写作助手,支持文档摘要、续写、改进和格式优化等功能"
    plugin_type = "视图"
    
    # 菜单类别
    menu_category = "插件"
    
    # 插件设置定义
    settings = {
        'api_key': {
            'type': 'string',
            'default': '',
            'description': 'SiliconFlow API密钥(明文,不推荐)'
        },
        'api_key_encoded': {
            'type': 'string',
            'default': '',
            'description': 'SiliconFlow API密钥(编码)'
        },
        'model': {
            'type': 'choice',
            'default': 'Qwen/Qwen2.5-7B-Instruct',
            'options': list(SiliconFlowClient.AVAILABLE_MODELS),
            'description': '使用的AI模型'
        },
        'temperature': {
            'type': 'float',
            'default': 0.7,
            'min': 0.0,
            'max': 2.0,
            'description': '生成温度(0-2)'
        },
        'max_tokens': {
            'type': 'int',
            'default': 2048,
            'min': 100,
            'max': 4096,
            'description': '最大生成Token数'
        },
        'stream_output': {
            'type': 'bool',
            'default': True,
            'description': '启用流式输出'
        },
        'system_prompt': {
            'type': 'string',
            'default': '你是一个专业的AI写作助手,擅长帮助用户撰写和改进文档、回答问题、提供写作建议。请用中文回复。',
            'description': '系统提示词'
        },
        'encrypt_key': {
            'type': 'bool',
            'default': True,
            'description': '加密存储API密钥'
        }
    }
    
    def __init__(self, plugin_manager=None):
        """初始化插件"""
        super().__init__()
        self.plugin_manager = plugin_manager
        self.app = getattr(plugin_manager, 'main_window', None) if plugin_manager else None
        self.widget = None
        self._client = None
    
    def initialize(self, app):
        """初始化插件"""
        super().initialize(app)
        self.app = app
        
        from src.utils.logger import info
        info(f"{self.name} 插件初始化")
    
    def get_view(self):
        """获取插件视图"""
        if not self.widget:
            self.widget = CopilotMainWidget(self)
        return self.widget
    
    def get_view_name(self):
        """获取视图名称"""
        return "AI Copilot"
    
    def get_menu_items(self):
        """返回插件菜单项"""
        return [
            {
                'name': '打开AI Copilot',
                'callback': self.show_copilot,
                'shortcut': 'Ctrl+Shift+C',
                'icon': 'chat',
                'category': '插件'
            }
        ]
    
    def show_copilot(self):
        """显示Copilot窗口"""
        try:
            if self.widget is None or not hasattr(self.widget, 'isVisible'):
                self.widget = CopilotMainWidget(self, self.app)
            
            self.widget.setWindowTitle('MGit - AI Copilot')
            
            # 调整窗口大小
            try:
                from PyQt5.QtWidgets import QApplication
                desktop = QApplication.desktop().availableGeometry()
                width = min(900, int(desktop.width() * 0.6))
                height = min(700, int(desktop.height() * 0.7))
                self.widget.resize(width, height)
                
                # 居中显示
                self.widget.move(
                    (desktop.width() - width) // 2,
                    (desktop.height() - height) // 2
                )
            except Exception:
                self.widget.resize(900, 700)
            
            self.widget.show()
            self.widget.raise_()
            self.widget.activateWindow()
            
        except Exception as e:
            from src.utils.logger import error
            error(f"显示AI Copilot窗口失败: {str(e)}")
    
    def get_client(self) -> SiliconFlowClient:
        """获取API客户端"""
        if self._client is None:
            self._client = SiliconFlowClient()
        
        # 更新设置
        api_key = self.get_api_key()
        if api_key:
            self._client.set_api_key(api_key)
        
        model = self.get_setting('model', 'Qwen/Qwen2.5-7B-Instruct')
        self._client.set_model(model)
        
        return self._client
    
    def get_api_key(self) -> str:
        """获取API密钥(自动解码)"""
        # 优先尝试编码的密钥
        encoded_key = self.get_setting('api_key_encoded', '')
        if encoded_key:
            return SecurityUtils.decode_api_key(encoded_key)
        
        # 回退到明文密钥
        return self.get_setting('api_key', '')
    
    def getCurrentEditorContent(self) -> Optional[str]:
        """获取当前编辑器内容"""
        if not self.app:
            return None
        
        try:
            # 尝试多种方式获取编辑器内容
            if hasattr(self.app, 'getCurrentMarkdownContent'):
                content = self.app.getCurrentMarkdownContent()
                if content:
                    return content
            
            if hasattr(self.app, 'editor') and self.app.editor:
                if hasattr(self.app.editor, 'toPlainText'):
                    return self.app.editor.toPlainText()
            
            if hasattr(self.app, 'tabManager'):
                tab_manager = self.app.tabManager
                if hasattr(tab_manager, 'currentWidget'):
                    current_tab = tab_manager.currentWidget()
                    if current_tab:
                        if hasattr(current_tab, 'toPlainText'):
                            return current_tab.toPlainText()
                        if hasattr(current_tab, 'editor'):
                            editor = current_tab.editor
                            if editor and hasattr(editor, 'toPlainText'):
                                return editor.toPlainText()
                        # 查找子编辑器
                        from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                        text_edit = current_tab.findChild(QTextEdit)
                        if text_edit:
                            return text_edit.toPlainText()
                        plain_edit = current_tab.findChild(QPlainTextEdit)
                        if plain_edit:
                            return plain_edit.toPlainText()
        except Exception as e:
            from src.utils.logger import warning
            warning(f"获取编辑器内容失败: {str(e)}")
        
        return None
    
    def getSelectedText(self) -> Optional[str]:
        """获取选中的文本"""
        if not self.app:
            return None
        
        try:
            if hasattr(self.app, 'editor') and self.app.editor:
                if hasattr(self.app.editor, 'textCursor'):
                    cursor = self.app.editor.textCursor()
                    if cursor.hasSelection():
                        return cursor.selectedText()
            
            if hasattr(self.app, 'tabManager'):
                tab_manager = self.app.tabManager
                if hasattr(tab_manager, 'currentWidget'):
                    current_tab = tab_manager.currentWidget()
                    if current_tab:
                        from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                        for edit_type in [QTextEdit, QPlainTextEdit]:
                            edit = current_tab.findChild(edit_type)
                            if edit:
                                cursor = edit.textCursor()
                                if cursor.hasSelection():
                                    return cursor.selectedText()
        except Exception as e:
            from src.utils.logger import warning
            warning(f"获取选中文本失败: {str(e)}")
        
        return None
    
    def insertToEditor(self, text: str) -> bool:
        """将文本插入到编辑器光标位置"""
        if not self.app or not text:
            return False
        
        try:
            if hasattr(self.app, 'editor') and self.app.editor:
                if hasattr(self.app.editor, 'textCursor'):
                    cursor = self.app.editor.textCursor()
                    cursor.insertText(text)
                    return True
            
            if hasattr(self.app, 'tabManager'):
                tab_manager = self.app.tabManager
                if hasattr(tab_manager, 'currentWidget'):
                    current_tab = tab_manager.currentWidget()
                    if current_tab:
                        from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                        for edit_type in [QTextEdit, QPlainTextEdit]:
                            edit = current_tab.findChild(edit_type)
                            if edit:
                                cursor = edit.textCursor()
                                cursor.insertText(text)
                                return True
        except Exception as e:
            from src.utils.logger import warning
            warning(f"插入文本失败: {str(e)}")
        
        return False
    
    def replaceEditorContent(self, text: str) -> bool:
        """替换编辑器全部内容"""
        if not self.app or not text:
            return False
        
        try:
            if hasattr(self.app, 'editor') and self.app.editor:
                if hasattr(self.app.editor, 'setPlainText'):
                    self.app.editor.setPlainText(text)
                    return True
            
            if hasattr(self.app, 'tabManager'):
                tab_manager = self.app.tabManager
                if hasattr(tab_manager, 'currentWidget'):
                    current_tab = tab_manager.currentWidget()
                    if current_tab:
                        from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                        for edit_type in [QTextEdit, QPlainTextEdit]:
                            edit = current_tab.findChild(edit_type)
                            if edit:
                                edit.setPlainText(text)
                                return True
        except Exception as e:
            from src.utils.logger import warning
            warning(f"替换内容失败: {str(e)}")
        
        return False
    
    def cleanup(self):
        """清理插件资源"""
        try:
            if self.widget:
                self.widget.close()
                self.widget.deleteLater()
                self.widget = None
            
            self._client = None
            
            from src.utils.logger import info
            info(f"{self.name} 插件已清理")
        except Exception as e:
            from src.utils.logger import warning
            warning(f"清理插件资源时出错: {str(e)}")
    
    def enable(self):
        """启用插件"""
        super().enable()
        from src.utils.logger import info
        info(f"{self.name} 插件已启用")
    
    def disable(self):
        """禁用插件"""
        super().disable()
        from src.utils.logger import info
        info(f"{self.name} 插件已禁用")
