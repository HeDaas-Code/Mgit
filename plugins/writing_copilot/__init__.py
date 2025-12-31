#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Writing Copilot Plugin - AI-powered writing assistant for MGit
Provides inline completion, editing, creation, chat, and agent modes
Uses SiliconFlow API and Langchain for agent development
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QTextCursor
from qfluentwidgets import FluentIcon
from src.utils.plugin_base import EditorPlugin
from src.utils.logger import info, warning, error, debug

import os
from typing import Optional


class Plugin(EditorPlugin):
    """Writing Copilot Plugin for MGit"""
    
    # 插件元数据
    name = "写作Copilot"
    version = "1.0.0"
    author = "MGit Team"
    description = "AI驱动的写作助手，提供行内补全、编辑、创作、对话和代理模式"
    plugin_type = "编辑器"
    
    # 插件依赖
    package_dependencies = [
        "langchain>=0.1.0",
        "langchain-community>=0.0.20",
        "langchain-openai>=0.0.5",
        "openai>=1.0.0",
        "requests>=2.28.0",
    ]
    
    # 插件设置
    settings = {
        'api_base_url': {
            'type': 'string',
            'default': 'https://api.siliconflow.cn/v1',
            'description': 'SiliconFlow API基础URL',
            'group': 'API设置'
        },
        'api_key': {
            'type': 'string',
            'default': '',
            'description': 'API密钥（敏感信息，仅在界面中隐藏显示）',
            'password': True,
            'group': 'API设置'
        },
        'model_name': {
            'type': 'choice',
            'default': 'deepseek-ai/DeepSeek-V2.5',
            'options': [
                'deepseek-ai/DeepSeek-V2.5',
                'Qwen/Qwen2.5-7B-Instruct',
                'THUDM/glm-4-9b-chat',
                'meta-llama/Meta-Llama-3.1-8B-Instruct',
            ],
            'labels': [
                'DeepSeek V2.5',
                'Qwen2.5 7B',
                'GLM-4 9B',
                'Llama 3.1 8B',
            ],
            'description': '使用的模型',
            'group': 'API设置'
        },
        'enable_inline_completion': {
            'type': 'bool',
            'default': True,
            'description': '启用行内补全',
            'group': '功能设置'
        },
        'completion_trigger': {
            'type': 'choice',
            'default': 'auto',
            'options': ['auto', 'manual', 'both'],
            'labels': ['自动触发', '手动触发', '两者都启用'],
            'description': '补全触发方式',
            'group': '功能设置'
        },
        'auto_completion_delay': {
            'type': 'int',
            'default': 1000,
            'min': 500,
            'max': 5000,
            'description': '自动补全延迟（毫秒）',
            'group': '功能设置'
        },
        'enable_task_review': {
            'type': 'bool',
            'default': True,
            'description': '启用代理任务审查',
            'group': '代理设置'
        },
        'max_context_length': {
            'type': 'int',
            'default': 4000,
            'min': 1000,
            'max': 8000,
            'description': '最大上下文长度',
            'group': '高级设置'
        },
    }
    
    def __init__(self):
        super().__init__()
        self.copilot_widget = None
        self.completion_timer = None
        self.llm_client = None
        self.agent_executor = None
        self._initialized_fully = False
        
    def initialize(self, app):
        """初始化插件"""
        super().initialize(app)
        self.app = app
        
        try:
            # 初始化LLM客户端
            self._init_llm_client()
            
            # 创建主界面
            self._create_copilot_widget()
            
            # 设置自动补全定时器
            if self.get_setting('enable_inline_completion'):
                self._setup_completion_timer()
            
            # 初始化代理工具
            self._init_agent_tools()
            
            self._initialized_fully = True
            info(f"{self.name} 插件初始化完成")
            
        except Exception as e:
            error(f"{self.name} 初始化失败: {str(e)}")
            self._initialized_fully = False
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            api_key = self.get_setting('api_key', '')
            if not api_key:
                warning("未设置API密钥，部分功能将不可用")
                return
            
            api_base = self.get_setting('api_base_url', 'https://api.siliconflow.cn/v1')
            model_name = self.get_setting('model_name', 'deepseek-ai/DeepSeek-V2.5')
            
            # 延迟导入，避免在未安装依赖时报错
            from langchain_community.llms import OpenAI
            from langchain_community.chat_models import ChatOpenAI
            
            # 创建LLM客户端
            self.llm_client = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=api_base,
                temperature=0.7,
                max_tokens=2000,
            )
            
            info(f"LLM客户端初始化完成: {model_name}")
            
        except ImportError as e:
            warning(f"Langchain库未安装，请安装依赖: {str(e)}")
            self.llm_client = None
        except Exception as e:
            error(f"初始化LLM客户端失败: {str(e)}")
            self.llm_client = None
    
    def _init_agent_tools(self):
        """初始化代理工具"""
        try:
            if not self.llm_client:
                return
            
            from .tools.document_tools import (
                create_document_tools,
                create_git_tools
            )
            
            # 创建文档和Git工具
            doc_tools = create_document_tools(self.app)
            git_tools = create_git_tools(self.app)
            
            # 延迟导入Langchain代理
            from langchain.agents import initialize_agent, AgentType
            
            # 创建代理执行器
            all_tools = doc_tools + git_tools
            self.agent_executor = initialize_agent(
                tools=all_tools,
                llm=self.llm_client,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                handle_parsing_errors=True,
            )
            
            info("代理工具初始化完成")
            
        except ImportError:
            warning("Langchain代理库未完全安装")
            self.agent_executor = None
        except Exception as e:
            error(f"初始化代理工具失败: {str(e)}")
            self.agent_executor = None
    
    def _create_copilot_widget(self):
        """创建Copilot主界面"""
        from .ui.copilot_widget import WritingCopilotWidget
        
        self.copilot_widget = WritingCopilotWidget(self, self.app)
    
    def _setup_completion_timer(self):
        """设置自动补全定时器"""
        if not hasattr(self.app, 'editor') or not self.app.editor:
            return
        
        delay = self.get_setting('auto_completion_delay', 1000)
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.setInterval(delay)
        self.completion_timer.timeout.connect(self._trigger_inline_completion)
        
        # 连接编辑器文本变化信号，避免重复连接
        try:
            self.app.editor.textChanged.disconnect(self._on_text_changed)
        except TypeError:
            # 如果之前未连接，则忽略断开错误
            pass
        self.app.editor.textChanged.connect(self._on_text_changed)
    
    def _on_text_changed(self):
        """编辑器文本变化时触发"""
        trigger_mode = self.get_setting('completion_trigger', 'auto')
        
        if trigger_mode in ['auto', 'both'] and self.completion_timer:
            # 重置定时器
            self.completion_timer.stop()
            self.completion_timer.start()
    
    def _trigger_inline_completion(self):
        """触发行内补全"""
        if not self._initialized_fully or not self.llm_client:
            return
        
        try:
            # 获取编辑器内容和光标位置
            if not hasattr(self.app, 'editor') or not self.app.editor:
                return
            
            editor = self.app.editor
            cursor = editor.textCursor()
            position = cursor.position()
            
            # 获取当前行的内容
            cursor.select(QTextCursor.LineUnderCursor)
            current_line = cursor.selectedText()
            
            # 获取上下文
            full_text = editor.toPlainText()
            before_cursor = full_text[:position]
            
            # 生成补全
            if self.copilot_widget:
                self.copilot_widget.generate_inline_completion(before_cursor, current_line)
                
        except Exception as e:
            error(f"触发补全失败: {str(e)}")
    
    def get_view(self):
        """获取插件视图"""
        return self.copilot_widget
    
    def get_view_name(self):
        """获取视图名称"""
        return "写作Copilot"
    
    def get_settings_widget(self):
        """获取设置界面"""
        from .ui.settings_widget import CopilotSettingsWidget
        return CopilotSettingsWidget(self)
    
    def get_context_menu_items(self):
        """获取编辑器上下文菜单项"""
        return [
            {
                'name': '打开写作Copilot',
                'icon': FluentIcon.ROBOT,
                'callback': self._show_copilot_panel
            },
            {
                'name': '补全当前行',
                'icon': FluentIcon.EDIT,
                'callback': self._trigger_manual_completion
            },
        ]
    
    def _show_copilot_panel(self):
        """显示Copilot面板"""
        if self.copilot_widget:
            self.copilot_widget.setVisible(True)
            self.copilot_widget.raise_()
            info("写作Copilot面板已打开")
    
    def _trigger_manual_completion(self):
        """手动触发补全"""
        if self.copilot_widget:
            self.copilot_widget._manual_trigger_completion()
    
    def get_event_listeners(self):
        """获取事件监听器"""
        return {
            'editor_created': self.on_editor_created,
            'file_saved': self.on_file_saved,
        }
    
    def on_editor_created(self, editor):
        """编辑器创建时调用"""
        if self.get_setting('enable_inline_completion'):
            self._setup_completion_timer()
    
    def on_file_saved(self, file_path):
        """文件保存时调用"""
        debug(f"文件已保存: {file_path}")
    
    def enable(self):
        """启用插件"""
        if self.enabled:
            return
        
        super().enable()
        
        if self.copilot_widget:
            self.copilot_widget.setVisible(True)
        
        info(f"{self.name} 已启用")
    
    def disable(self):
        """禁用插件"""
        if not self.enabled:
            return
        
        # 停止定时器
        if self.completion_timer:
            self.completion_timer.stop()
        
        # 隐藏界面
        if self.copilot_widget:
            self.copilot_widget.setVisible(False)
        
        super().disable()
        info(f"{self.name} 已禁用")
    
    def cleanup(self):
        """清理资源"""
        # 停止定时器
        if self.completion_timer:
            self.completion_timer.stop()
            self.completion_timer = None
        
        # 断开信号连接
        if hasattr(self.app, 'editor') and self.app.editor:
            try:
                self.app.editor.textChanged.disconnect(self._on_text_changed)
            except TypeError:
                # 信号可能已经断开；在清理阶段忽略此错误
                debug("textChanged signal disconnect raised TypeError; it may have been already disconnected.")
        
        # 清理界面
        if self.copilot_widget:
            self.copilot_widget.deleteLater()
            self.copilot_widget = None
        
        # 清理LLM客户端
        self.llm_client = None
        self.agent_executor = None
        
        super().cleanup()
        info(f"{self.name} 清理完成")
