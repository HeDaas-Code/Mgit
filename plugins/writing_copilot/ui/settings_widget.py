#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Settings widget for Writing Copilot plugin
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                           QGroupBox, QFormLayout)
from qfluentwidgets import (LineEdit, ComboBox, SwitchButton, SpinBox,
                          BodyLabel, PushButton, FluentIcon)


class CopilotSettingsWidget(QWidget):
    """写作Copilot设置界面"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
        self.loadSettings()
    
    def initUI(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # API设置组
        api_group = QGroupBox("API设置")
        api_layout = QFormLayout(api_group)
        
        # API基础URL
        self.api_url_input = LineEdit()
        self.api_url_input.setPlaceholderText("https://api.siliconflow.cn/v1")
        api_layout.addRow("API基础URL:", self.api_url_input)
        
        # API密钥
        self.api_key_input = LineEdit()
        self.api_key_input.setEchoMode(LineEdit.Password)
        self.api_key_input.setPlaceholderText("输入您的API密钥")
        api_layout.addRow("API密钥:", self.api_key_input)
        
        # 模型选择
        self.model_combo = ComboBox()
        self.model_combo.addItems([
            'DeepSeek V2.5',
            'Qwen2.5 7B',
            'GLM-4 9B',
            'Llama 3.1 8B',
        ])
        self.model_combo.setCurrentIndex(0)
        api_layout.addRow("模型:", self.model_combo)
        
        layout.addWidget(api_group)
        
        # 功能设置组
        feature_group = QGroupBox("功能设置")
        feature_layout = QFormLayout(feature_group)
        
        # 启用行内补全
        self.enable_completion_switch = SwitchButton()
        feature_layout.addRow("启用行内补全:", self.enable_completion_switch)
        
        # 补全触发方式
        self.trigger_combo = ComboBox()
        self.trigger_combo.addItems(['自动触发', '手动触发', '两者都启用'])
        self.trigger_combo.setCurrentIndex(0)
        feature_layout.addRow("补全触发方式:", self.trigger_combo)
        
        # 自动补全延迟
        self.delay_spin = SpinBox()
        self.delay_spin.setRange(500, 5000)
        self.delay_spin.setSingleStep(100)
        self.delay_spin.setSuffix(" 毫秒")
        feature_layout.addRow("自动补全延迟:", self.delay_spin)
        
        layout.addWidget(feature_group)
        
        # 代理设置组
        agent_group = QGroupBox("代理设置")
        agent_layout = QFormLayout(agent_group)
        
        # 启用任务审查
        self.enable_review_switch = SwitchButton()
        agent_layout.addRow("启用任务审查:", self.enable_review_switch)
        
        layout.addWidget(agent_group)
        
        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        # 最大上下文长度
        self.context_length_spin = SpinBox()
        self.context_length_spin.setRange(1000, 8000)
        self.context_length_spin.setSingleStep(500)
        self.context_length_spin.setSuffix(" 字符")
        advanced_layout.addRow("最大上下文长度:", self.context_length_spin)
        
        layout.addWidget(advanced_group)
        
        # 提示信息
        hint_label = BodyLabel("注意：API密钥仅在界面中隐藏显示，不会加密存储。")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        # 添加按钮行
        button_layout = QHBoxLayout()
        
        # 测试连接按钮
        self.test_button = PushButton("测试API连接")
        self.test_button.setIcon(FluentIcon.SYNC)
        self.test_button.clicked.connect(self.testConnection)
        button_layout.addWidget(self.test_button)
        
        # 应用设置按钮
        self.apply_button = PushButton("应用设置")
        self.apply_button.setIcon(FluentIcon.SAVE)
        self.apply_button.clicked.connect(self.applySettings)
        button_layout.addWidget(self.apply_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
    
    def loadSettings(self):
        """加载设置"""
        # API设置
        self.api_url_input.setText(self.plugin.get_setting('api_base_url', 'https://api.siliconflow.cn/v1'))
        self.api_key_input.setText(self.plugin.get_setting('api_key', ''))
        
        # 模型映射
        model_map = {
            'deepseek-ai/DeepSeek-V2.5': 0,
            'Qwen/Qwen2.5-7B-Instruct': 1,
            'THUDM/glm-4-9b-chat': 2,
            'meta-llama/Meta-Llama-3.1-8B-Instruct': 3,
        }
        model_name = self.plugin.get_setting('model_name', 'deepseek-ai/DeepSeek-V2.5')
        self.model_combo.setCurrentIndex(model_map.get(model_name, 0))
        
        # 功能设置
        self.enable_completion_switch.setChecked(self.plugin.get_setting('enable_inline_completion', True))
        
        trigger_map = {'auto': 0, 'manual': 1, 'both': 2}
        trigger = self.plugin.get_setting('completion_trigger', 'auto')
        self.trigger_combo.setCurrentIndex(trigger_map.get(trigger, 0))
        
        self.delay_spin.setValue(self.plugin.get_setting('auto_completion_delay', 1000))
        
        # 代理设置
        self.enable_review_switch.setChecked(self.plugin.get_setting('enable_task_review', True))
        
        # 高级设置
        self.context_length_spin.setValue(self.plugin.get_setting('max_context_length', 4000))
    
    def saveSettings(self):
        """保存设置"""
        # API设置
        self.plugin.set_setting('api_base_url', self.api_url_input.text())
        self.plugin.set_setting('api_key', self.api_key_input.text())
        
        # 模型映射
        model_names = [
            'deepseek-ai/DeepSeek-V2.5',
            'Qwen/Qwen2.5-7B-Instruct',
            'THUDM/glm-4-9b-chat',
            'meta-llama/Meta-Llama-3.1-8B-Instruct',
        ]
        self.plugin.set_setting('model_name', model_names[self.model_combo.currentIndex()])
        
        # 功能设置
        self.plugin.set_setting('enable_inline_completion', self.enable_completion_switch.isChecked())
        
        trigger_values = ['auto', 'manual', 'both']
        self.plugin.set_setting('completion_trigger', trigger_values[self.trigger_combo.currentIndex()])
        
        self.plugin.set_setting('auto_completion_delay', self.delay_spin.value())
        
        # 代理设置
        self.plugin.set_setting('enable_task_review', self.enable_review_switch.isChecked())
        
        # 高级设置
        self.plugin.set_setting('max_context_length', self.context_length_spin.value())
        
        # 重新初始化LLM客户端
        self.plugin._init_llm_client()
        
        # 重新设置补全定时器
        if self.plugin.get_setting('enable_inline_completion'):
            self.plugin._setup_completion_timer()
    
    def applySettings(self):
        """应用设置"""
        from PyQt5.QtWidgets import QMessageBox
        try:
            self.saveSettings()
            QMessageBox.information(self, "成功", "设置已应用！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"应用设置时出错: {str(e)}")
    
    def testConnection(self):
        """测试API连接"""
        from PyQt5.QtWidgets import QMessageBox
        
        api_key = self.api_key_input.text()
        if not api_key:
            QMessageBox.warning(self, "错误", "请先输入API密钥")
            return
        
        # 使用临时配置测试连接，不保存到插件设置
        try:
            from langchain_openai import ChatOpenAI
            
            # 获取当前输入的配置
            api_url = self.api_url_input.text()
            model_names = [
                'deepseek-ai/DeepSeek-V2.5',
                'Qwen/Qwen2.5-7B-Instruct',
                'THUDM/glm-4-9b-chat',
                'meta-llama/Meta-Llama-3.1-8B-Instruct',
            ]
            model_name = model_names[self.model_combo.currentIndex()]
            
            # 创建临时客户端测试
            test_client = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=api_url,
                temperature=0.7,
                timeout=30
            )
            
            # 测试简单调用
            from langchain.schema import HumanMessage
            response = test_client.invoke([HumanMessage(content="测试")])
            
            if response:
                QMessageBox.information(self, "成功", "API连接测试成功！\n您可以点击\"应用设置\"保存配置。")
            else:
                QMessageBox.warning(self, "失败", "API连接测试失败，未收到响应。")
        except Exception as e:
            error_msg = str(e)
            # 清理可能包含敏感信息的错误
            if 'api' in error_msg.lower() and 'key' in error_msg.lower():
                error_msg = "API认证失败，请检查API密钥是否正确"
            QMessageBox.warning(self, "失败", f"API连接测试失败：{error_msg}")
    
    def showEvent(self, event):
        """窗口显示时重新加载设置"""
        super().showEvent(event)
        self.loadSettings()
    
    def hideEvent(self, event):
        """窗口隐藏时保存设置"""
        super().hideEvent(event)
        # Don't save on hide, only on explicit save or dialog accept
        
    def closeEvent(self, event):
        """窗口关闭时保存设置"""
        # This will be called when dialog is closed
        # We save settings when parent dialog is accepted
        super().closeEvent(event)
