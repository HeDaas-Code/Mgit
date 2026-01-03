#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copilot Manager - Central manager for all copilot features
"""

from typing import Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from .siliconflow_client import SiliconFlowClient
from src.utils.logger import info, warning, error
from src.utils.config_manager import ConfigManager

class CopilotManager(QObject):
    """
    Manager for copilot functionality
    Handles inline completion, edit mode, creation mode, conversation mode, and agent mode
    """
    
    # Signals
    completion_ready = pyqtSignal(str)  # Emitted when completion is ready
    chat_response = pyqtSignal(str)  # Emitted when chat response is received
    error_occurred = pyqtSignal(str)  # Emitted when an error occurs
    status_changed = pyqtSignal(str)  # Emitted when status changes
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.client = None
        self.enabled = False
        self.current_mode = 'none'  # none, inline, edit, creation, conversation, agent
        
        # Load configuration
        self._load_config()
        
    def _load_config(self):
        """Load copilot configuration"""
        try:
            api_key = self.config_manager.get('copilot.api_key', '')
            model = self.config_manager.get('copilot.model', SiliconFlowClient.DEFAULT_MODELS['chat'])
            self.enabled = self.config_manager.get('copilot.enabled', False)
            
            if api_key:
                self.client = SiliconFlowClient(api_key, model)
                info("Copilot client initialized")
            else:
                warning("Copilot API key not configured")
        except Exception as e:
            error(f"Failed to load copilot config: {str(e)}")
            
    def set_api_key(self, api_key: str, model: str = None):
        """
        Set or update API key
        
        Args:
            api_key: SiliconFlow API key
            model: Optional model name
        """
        self.config_manager.set('copilot.api_key', api_key)
        if model:
            self.config_manager.set('copilot.model', model)
        else:
            model = self.config_manager.get('copilot.model', SiliconFlowClient.DEFAULT_MODELS['chat'])
            
        self.client = SiliconFlowClient(api_key, model)
        self.enabled = True
        self.config_manager.set('copilot.enabled', True)
        info("Copilot API key updated")
        
    def is_enabled(self) -> bool:
        """Check if copilot is enabled"""
        return self.enabled and self.client is not None
        
    def set_enabled(self, enabled: bool):
        """Enable or disable copilot"""
        self.enabled = enabled
        self.config_manager.set('copilot.enabled', enabled)
        info(f"Copilot {'enabled' if enabled else 'disabled'}")
        
    def get_inline_completion(
        self, 
        context_before: str, 
        context_after: str = "",
        callback: Optional[Callable] = None
    ):
        """
        Get inline completion suggestion
        
        Args:
            context_before: Text before cursor
            context_after: Text after cursor
            callback: Optional callback function for completion
        """
        if not self.is_enabled():
            warning("Copilot is not enabled")
            return
            
        self.current_mode = 'inline'
        self.status_changed.emit("Generating completion...")
        
        # Create completion thread
        thread = CompletionThread(
            self.client,
            context_before,
            context_after
        )
        thread.completion_ready.connect(self._on_completion_ready)
        thread.error_occurred.connect(self._on_error)
        
        if callback:
            thread.completion_ready.connect(callback)
            
        thread.start()
        
    def edit_text(
        self,
        text: str,
        instruction: str,
        callback: Optional[Callable] = None
    ):
        """
        Edit text based on instruction
        
        Args:
            text: Original text
            instruction: Edit instruction
            callback: Optional callback function
        """
        if not self.is_enabled():
            warning("Copilot is not enabled")
            return
            
        self.current_mode = 'edit'
        self.status_changed.emit("Editing text...")
        
        thread = EditThread(self.client, text, instruction)
        thread.edit_ready.connect(self._on_edit_ready)
        thread.error_occurred.connect(self._on_error)
        
        if callback:
            thread.edit_ready.connect(callback)
            
        thread.start()
        
    def create_content(
        self,
        prompt: str,
        content_type: str = "markdown",
        callback: Optional[Callable] = None
    ):
        """
        Create new content from prompt
        
        Args:
            prompt: Creation prompt
            content_type: Type of content (markdown, article, outline, etc.)
            callback: Optional callback function
        """
        if not self.is_enabled():
            warning("Copilot is not enabled")
            return
            
        self.current_mode = 'creation'
        self.status_changed.emit("Creating content...")
        
        thread = CreationThread(self.client, prompt, content_type)
        thread.content_ready.connect(self._on_content_ready)
        thread.error_occurred.connect(self._on_error)
        
        if callback:
            thread.content_ready.connect(callback)
            
        thread.start()
        
    def chat(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        callback: Optional[Callable] = None
    ):
        """
        Chat with copilot
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
            callback: Optional callback function
        """
        if not self.is_enabled():
            warning("Copilot is not enabled")
            return
            
        self.current_mode = 'conversation'
        self.status_changed.emit("Thinking...")
        
        if conversation_history is None:
            conversation_history = []
            
        thread = ChatThread(self.client, message, conversation_history)
        thread.response_ready.connect(self._on_chat_response)
        thread.error_occurred.connect(self._on_error)
        
        if callback:
            thread.response_ready.connect(callback)
            
        thread.start()
        
    def _on_completion_ready(self, completion: str):
        """Handle completion ready"""
        self.completion_ready.emit(completion)
        self.status_changed.emit("Completion ready")
        self.current_mode = 'none'
        
    def _on_edit_ready(self, edited_text: str):
        """Handle edit ready"""
        self.completion_ready.emit(edited_text)
        self.status_changed.emit("Edit complete")
        self.current_mode = 'none'
        
    def _on_content_ready(self, content: str):
        """Handle content creation ready"""
        self.completion_ready.emit(content)
        self.status_changed.emit("Content created")
        self.current_mode = 'none'
        
    def _on_chat_response(self, response: str):
        """Handle chat response"""
        self.chat_response.emit(response)
        self.status_changed.emit("Ready")
        
    def _on_error(self, error_msg: str):
        """Handle error"""
        self.error_occurred.emit(error_msg)
        self.status_changed.emit("Error occurred")
        self.current_mode = 'none'
        error(f"Copilot error: {error_msg}")


class CompletionThread(QThread):
    """Thread for generating inline completions"""
    
    completion_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client: SiliconFlowClient, context_before: str, context_after: str):
        super().__init__()
        self.client = client
        self.context_before = context_before
        self.context_after = context_after
        
    def run(self):
        try:
            # Create prompt for completion
            prompt = f"""你是一个专业的写作助手。请根据上下文补全内容。

上文：
{self.context_before}

下文：
{self.context_after}

请生成自然的补全内容（只返回补全内容，不要包含任何解释）："""

            messages = [{'role': 'user', 'content': prompt}]
            response = self.client.chat_completion(messages, temperature=0.7, max_tokens=500)
            
            if 'choices' in response and len(response['choices']) > 0:
                completion = response['choices'][0]['message']['content'].strip()
                self.completion_ready.emit(completion)
            else:
                self.error_occurred.emit("No completion generated")
        except Exception as e:
            self.error_occurred.emit(str(e))


class EditThread(QThread):
    """Thread for editing text"""
    
    edit_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client: SiliconFlowClient, text: str, instruction: str):
        super().__init__()
        self.client = client
        self.text = text
        self.instruction = instruction
        
    def run(self):
        try:
            prompt = f"""你是一个专业的文本编辑助手。请根据指令编辑以下文本。

原文：
{self.text}

编辑指令：
{self.instruction}

请返回编辑后的文本（只返回编辑后的文本，不要包含任何解释）："""

            messages = [{'role': 'user', 'content': prompt}]
            response = self.client.chat_completion(messages, temperature=0.5, max_tokens=2048)
            
            if 'choices' in response and len(response['choices']) > 0:
                edited = response['choices'][0]['message']['content'].strip()
                self.edit_ready.emit(edited)
            else:
                self.error_occurred.emit("No edit generated")
        except Exception as e:
            self.error_occurred.emit(str(e))


class CreationThread(QThread):
    """Thread for creating content"""
    
    content_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client: SiliconFlowClient, prompt: str, content_type: str):
        super().__init__()
        self.client = client
        self.prompt = prompt
        self.content_type = content_type
        
    def run(self):
        try:
            system_prompt = f"""你是一个专业的写作助手，擅长创作各类文档。
请根据用户的需求创作{self.content_type}格式的内容。
内容应该结构清晰、逻辑严谨、语言流畅。"""

            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': self.prompt}
            ]
            response = self.client.chat_completion(messages, temperature=0.8, max_tokens=4096)
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content'].strip()
                self.content_ready.emit(content)
            else:
                self.error_occurred.emit("No content generated")
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChatThread(QThread):
    """Thread for chat conversation"""
    
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client: SiliconFlowClient, message: str, history: List[Dict[str, str]]):
        super().__init__()
        self.client = client
        self.message = message
        self.history = history
        
    def run(self):
        try:
            # Build messages from history
            messages = self.history.copy()
            messages.append({'role': 'user', 'content': self.message})
            
            response = self.client.chat_completion(messages, temperature=0.7, max_tokens=2048)
            
            if 'choices' in response and len(response['choices']) > 0:
                reply = response['choices'][0]['message']['content'].strip()
                self.response_ready.emit(reply)
            else:
                self.error_occurred.emit("No response generated")
        except Exception as e:
            self.error_occurred.emit(str(e))
