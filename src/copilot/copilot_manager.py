#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copilot Manager - Central manager for all copilot features
"""

from typing import Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt
from .siliconflow_client import SiliconFlowClient
from src.utils.logger import info, warning, error, debug, LogCategory
from src.utils.config_manager import ConfigManager

# Configuration constants
# NOTE:
# The following limits are intentionally conservative defaults chosen to balance
# latency, cost, and response quality for typical interactive editor workflows.
# They are not currently exposed via the settings dialog, but can be adjusted
# by developers if different workloads require larger or smaller limits.
#
# MAX_TOKENS_* values limit how many tokens the model may generate per request.
# - COMPLETION: short inline completions so the editor stays responsive.
# - EDIT: larger edits that may rewrite bigger code snippets.
# - CREATION: long-form content generation (e.g. documentation or new files).
# - CHAT: multi-turn conversational replies without exhausting model limits.
MAX_TOKENS_COMPLETION = 500
MAX_TOKENS_EDIT = 2048
MAX_TOKENS_CREATION = 4096
MAX_TOKENS_CHAT = 2048
# Context window around the cursor, measured in characters rather than tokens.
# These values are tuned to provide enough local context for useful suggestions
# while keeping prompts compact to reduce latency and API usage.
MAX_CONTEXT_BEFORE = 500  # Characters of context before cursor
MAX_CONTEXT_AFTER = 100   # Characters of context after cursor

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
        self.current_threads = []  # Store active threads
        
        # Load configuration
        self._load_config()
        
    def _load_config(self):
        """Load copilot configuration"""
        try:
            api_key = self.config_manager.get_plugin_setting('copilot', 'api_key', '')
            model = self.config_manager.get_plugin_setting('copilot', 'model', SiliconFlowClient.DEFAULT_MODELS['chat'])
            self.enabled = self.config_manager.get_plugin_setting('copilot', 'enabled', False)
            
            if api_key:
                self.client = SiliconFlowClient(api_key, model)
                info("Copilot client initialized", category=LogCategory.API)
            else:
                warning("Copilot API key not configured", category=LogCategory.CONFIG)
        except Exception as e:
            error(f"Failed to load copilot config: {str(e)}", category=LogCategory.CONFIG)
            
    def reload_config(self):
        """Public method to reload copilot configuration"""
        self._load_config()
        info("Copilot configuration reloaded", category=LogCategory.CONFIG)
            
    def set_api_key(self, api_key: str, model: str = None):
        """
        Set or update API key
        
        Args:
            api_key: SiliconFlow API key
            model: Optional model name
        """
        self.config_manager.set_plugin_setting('copilot', 'api_key', api_key)
        if model:
            self.config_manager.set_plugin_setting('copilot', 'model', model)
        else:
            model = self.config_manager.get_plugin_setting('copilot', 'model', SiliconFlowClient.DEFAULT_MODELS['chat'])
            
        self.client = SiliconFlowClient(api_key, model)
        self.enabled = True
        self.config_manager.set_plugin_setting('copilot', 'enabled', True)
        info("Copilot API key updated", category=LogCategory.CONFIG)
        
    def is_enabled(self) -> bool:
        """Check if copilot is enabled"""
        return self.enabled and self.client is not None
        
    def set_enabled(self, enabled: bool):
        """Enable or disable copilot"""
        self.enabled = enabled
        self.config_manager.set_plugin_setting('copilot', 'enabled', enabled)
        info(f"Copilot {'enabled' if enabled else 'disabled'}", category=LogCategory.CONFIG)
        
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
            warning("Copilot is not enabled", category=LogCategory.API)
            return
            
        self.current_mode = 'inline'
        self.status_changed.emit("Generating completion...")
        debug("Starting inline completion request", category=LogCategory.API)
        
        # Create completion thread
        thread = CompletionThread(
            self.client,
            context_before,
            context_after
        )
        thread.completion_ready.connect(self._on_completion_ready)
        thread.error_occurred.connect(self._on_error)
        
        # Store thread reference and connect callback if provided
        self.current_threads.append(thread)
        if callback:
            # Use a one-shot connection
            thread.completion_ready.connect(callback, Qt.SingleShotConnection)
            
        thread.finished.connect(lambda: self._cleanup_thread(thread))
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
            warning("Copilot is not enabled", category=LogCategory.API)
            return
            
        self.current_mode = 'edit'
        self.status_changed.emit("Editing text...")
        debug(f"Starting edit request, text length: {len(text)}", category=LogCategory.API)
        
        thread = EditThread(self.client, text, instruction)
        thread.edit_ready.connect(self._on_edit_ready)
        thread.error_occurred.connect(self._on_error)
        
        # Store thread reference and connect callback if provided
        self.current_threads.append(thread)
        if callback:
            thread.edit_ready.connect(callback, Qt.SingleShotConnection)
            
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        info("Edit thread started", category=LogCategory.API)
        
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
            warning("Copilot is not enabled", category=LogCategory.API)
            return
            
        self.current_mode = 'creation'
        self.status_changed.emit("Creating content...")
        debug(f"Starting content creation: {content_type}", category=LogCategory.API)
        
        thread = CreationThread(self.client, prompt, content_type)
        thread.content_ready.connect(self._on_content_ready)
        thread.error_occurred.connect(self._on_error)
        
        # Store thread reference and connect callback if provided
        self.current_threads.append(thread)
        if callback:
            thread.content_ready.connect(callback, Qt.SingleShotConnection)
            
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        info("Creation thread started", category=LogCategory.API)
        
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
            warning("Copilot is not enabled", category=LogCategory.API)
            return
            
        self.current_mode = 'conversation'
        self.status_changed.emit("Thinking...")
        debug(f"Starting chat request, message length: {len(message)}", category=LogCategory.API)
        
        if conversation_history is None:
            conversation_history = []
            
        thread = ChatThread(self.client, message, conversation_history)
        thread.response_ready.connect(self._on_chat_response)
        thread.error_occurred.connect(self._on_error)
        
        # Store thread reference and connect callback if provided
        self.current_threads.append(thread)
        if callback:
            thread.response_ready.connect(callback, Qt.SingleShotConnection)
            
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        thread.start()
        info("Chat thread started", category=LogCategory.API)
        
    def _on_completion_ready(self, completion: str):
        """Handle completion ready"""
        self.completion_ready.emit(completion)
        self.status_changed.emit("Completion ready")
        self.current_mode = 'none'
        info(f"Completion ready, length: {len(completion)} chars", category=LogCategory.API)
        debug(f"Completion content: {completion[:100]}...", category=LogCategory.API)
        
    def _on_edit_ready(self, edited_text: str):
        """Handle edit ready"""
        self.completion_ready.emit(edited_text)
        self.status_changed.emit("Edit complete")
        self.current_mode = 'none'
        info(f"Edit complete, length: {len(edited_text)} chars", category=LogCategory.API)
        debug(f"Edited content: {edited_text[:100]}...", category=LogCategory.API)
        
    def _on_content_ready(self, content: str):
        """Handle content creation ready"""
        self.completion_ready.emit(content)
        self.status_changed.emit("Content created")
        self.current_mode = 'none'
        info(f"Content created, length: {len(content)} chars", category=LogCategory.API)
        debug(f"Created content: {content[:100]}...", category=LogCategory.API)
        
    def _on_chat_response(self, response: str):
        """Handle chat response"""
        self.chat_response.emit(response)
        self.status_changed.emit("Ready")
        info(f"Chat response received, length: {len(response)} chars", category=LogCategory.API)
        debug(f"Chat response: {response[:100]}...", category=LogCategory.API)
        
    def _on_error(self, error_msg: str):
        """Handle error"""
        self.error_occurred.emit(error_msg)
        self.status_changed.emit("Error occurred")
        self.current_mode = 'none'
        error(f"Copilot error: {error_msg}", category=LogCategory.ERROR)
        debug(f"Error details: {error_msg}", category=LogCategory.ERROR)
        
    def _cleanup_thread(self, thread: QThread):
        """Remove finished thread from active threads list"""
        if thread in self.current_threads:
            self.current_threads.remove(thread)
            debug(f"Cleaned up thread, {len(self.current_threads)} threads remaining", category=LogCategory.API)


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
            info("CompletionThread started", category=LogCategory.API)
            debug(f"Context before length: {len(self.context_before)}, after length: {len(self.context_after)}", category=LogCategory.API)
            
            # Create prompt for completion
            prompt = f"""你是一个专业的写作助手。请根据上下文补全内容。

上文：
{self.context_before}

下文：
{self.context_after}

请生成自然的补全内容（只返回补全内容，不要包含任何解释）："""

            messages = [{'role': 'user', 'content': prompt}]
            info("Sending completion request to API", category=LogCategory.API)
            response = self.client.chat_completion(messages, temperature=0.7, max_tokens=MAX_TOKENS_COMPLETION)
            
            if 'choices' in response and len(response['choices']) > 0:
                completion = response['choices'][0]['message']['content'].strip()
                info(f"Completion received, length: {len(completion)}", category=LogCategory.API)
                self.completion_ready.emit(completion)
            else:
                error_msg = "No completion generated"
                error(error_msg, category=LogCategory.ERROR)
                self.error_occurred.emit(error_msg)
        except Exception as e:
            error(f"CompletionThread error: {str(e)}", category=LogCategory.ERROR)
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
            info("EditThread started", category=LogCategory.API)
            debug(f"Text length: {len(self.text)}, instruction: {self.instruction[:50]}...", category=LogCategory.API)
            
            prompt = f"""你是一个专业的文本编辑助手。请根据指令编辑以下文本。

原文：
{self.text}

编辑指令：
{self.instruction}

请返回编辑后的文本（只返回编辑后的文本，不要包含任何解释）："""

            messages = [{'role': 'user', 'content': prompt}]
            info("Sending edit request to API", category=LogCategory.API)
            response = self.client.chat_completion(messages, temperature=0.5, max_tokens=MAX_TOKENS_EDIT)
            
            if 'choices' in response and len(response['choices']) > 0:
                edited = response['choices'][0]['message']['content'].strip()
                info(f"Edit received, length: {len(edited)}", category=LogCategory.API)
                self.edit_ready.emit(edited)
            else:
                error_msg = "No edit generated"
                error(error_msg, category=LogCategory.ERROR)
                self.error_occurred.emit(error_msg)
        except Exception as e:
            error(f"EditThread error: {str(e)}", category=LogCategory.ERROR)
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
            info("CreationThread started", category=LogCategory.API)
            debug(f"Content type: {self.content_type}, prompt: {self.prompt[:50]}...", category=LogCategory.API)
            
            system_prompt = f"""你是一个专业的写作助手，擅长创作各类文档。
请根据用户的需求创作{self.content_type}格式的内容。
内容应该结构清晰、逻辑严谨、语言流畅。"""

            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': self.prompt}
            ]
            info("Sending creation request to API", category=LogCategory.API)
            response = self.client.chat_completion(messages, temperature=0.8, max_tokens=MAX_TOKENS_CREATION)
            
            if 'choices' in response and len(response['choices']) > 0:
                content = response['choices'][0]['message']['content'].strip()
                info(f"Content created, length: {len(content)}", category=LogCategory.API)
                self.content_ready.emit(content)
            else:
                error_msg = "No content generated"
                error(error_msg, category=LogCategory.ERROR)
                self.error_occurred.emit(error_msg)
        except Exception as e:
            error(f"CreationThread error: {str(e)}", category=LogCategory.ERROR)
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
            info("ChatThread started", category=LogCategory.API)
            debug(f"Message: {self.message[:50]}..., history length: {len(self.history)}", category=LogCategory.API)
            
            # Build messages from history
            messages = self.history.copy()
            messages.append({'role': 'user', 'content': self.message})
            
            info("Sending chat request to API", category=LogCategory.API)
            response = self.client.chat_completion(messages, temperature=0.7, max_tokens=MAX_TOKENS_CHAT)
            
            if 'choices' in response and len(response['choices']) > 0:
                reply = response['choices'][0]['message']['content'].strip()
                info(f"Chat response received, length: {len(reply)}", category=LogCategory.API)
                self.response_ready.emit(reply)
            else:
                error_msg = "No response generated"
                error(error_msg, category=LogCategory.ERROR)
                self.error_occurred.emit(error_msg)
        except Exception as e:
            error(f"ChatThread error: {str(e)}", category=LogCategory.ERROR)
            self.error_occurred.emit(str(e))
