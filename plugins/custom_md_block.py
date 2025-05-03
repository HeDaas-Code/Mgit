from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                          QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, 
                          QDialog, QFormLayout, QMessageBox, QTextEdit, QCheckBox)
from PyQt5.QtCore import Qt
from src.utils.plugin_base import PluginBase
import re
import json
import os
import pathlib

class CustomBlockSettingsWidget(QWidget):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.initUI()
        self.loadBlocks()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        titleLabel = QLabel("自定义Markdown语句块")
        titleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titleLabel)
        
        # 说明
        descLabel = QLabel("在这里定义自定义Markdown语句块的转换规则。当预览或导出时，自定义语句块将被转换为标准Markdown格式。")
        descLabel.setWordWrap(True)
        layout.addWidget(descLabel)
        
        # 表格
        self.blockTable = QTableWidget(0, 3)
        self.blockTable.setHorizontalHeaderLabels(["语句块标识", "描述", "操作"])
        self.blockTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.blockTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.blockTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.blockTable.setColumnWidth(2, 100)
        layout.addWidget(self.blockTable)
        
        # 添加按钮
        buttonLayout = QHBoxLayout()
        self.addButton = QPushButton("添加语句块")
        self.addButton.clicked.connect(self.showAddDialog)
        buttonLayout.addWidget(self.addButton)
        buttonLayout.addStretch()
        layout.addLayout(buttonLayout)
        
        # 帮助文本
        helpText = QTextEdit()
        helpText.setReadOnly(True)
        helpText.setMaximumHeight(150)
        helpText.setText("使用说明:\n"
                         "1. 自定义语句块使用 ```identifier 格式定义，与代码块类似\n"
                         "2. 语句块标识(identifier)是自定义语句块的唯一标识\n"
                         "3. 在「替换模板」中使用 {{content}} 表示语句块内容\n"
                         "4. 例如: 定义callout语句块，使用 ```callout 标题\n内容 ```，"
                         "替换模板为 > **{{title}}**\n> {{content}}")
        layout.addWidget(helpText)
    
    def loadBlocks(self):
        blocks = self.plugin.get_setting("custom_blocks", {})
        self.blockTable.setRowCount(0)
        
        for identifier, block_info in blocks.items():
            row = self.blockTable.rowCount()
            self.blockTable.insertRow(row)
            
            # 设置标识和描述
            self.blockTable.setItem(row, 0, QTableWidgetItem(identifier))
            self.blockTable.setItem(row, 1, QTableWidgetItem(block_info.get("description", "")))
            
            # 添加编辑和删除按钮
            buttonWidget = QWidget()
            buttonLayout = QHBoxLayout(buttonWidget)
            buttonLayout.setContentsMargins(0, 0, 0, 0)
            
            editButton = QPushButton("编辑")
            editButton.clicked.connect(lambda checked, i=identifier: self.showEditDialog(i))
            
            deleteButton = QPushButton("删除")
            deleteButton.clicked.connect(lambda checked, i=identifier: self.deleteBlock(i))
            
            buttonLayout.addWidget(editButton)
            buttonLayout.addWidget(deleteButton)
            self.blockTable.setCellWidget(row, 2, buttonWidget)
    
    def showAddDialog(self):
        dialog = BlockDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            identifier = dialog.identifierEdit.text().strip()
            description = dialog.descriptionEdit.text().strip()
            template = dialog.templateEdit.toPlainText().strip()
            requires_title = dialog.requiresTitleCheckbox.isChecked()
            
            # 保存到设置
            blocks = self.plugin.get_setting("custom_blocks", {})
            blocks[identifier] = {
                "description": description,
                "template": template,
                "requires_title": requires_title
            }
            self.plugin.set_setting("custom_blocks", blocks)
            # 保存到JSON文件
            self.plugin.save_config_to_json()
            self.loadBlocks()
    
    def showEditDialog(self, identifier):
        blocks = self.plugin.get_setting("custom_blocks", {})
        if identifier not in blocks:
            return
        
        block_info = blocks[identifier]
        dialog = BlockDialog(self)
        dialog.identifierEdit.setText(identifier)
        dialog.identifierEdit.setEnabled(False)  # 不允许修改标识符
        dialog.descriptionEdit.setText(block_info.get("description", ""))
        dialog.templateEdit.setPlainText(block_info.get("template", ""))
        dialog.requiresTitleCheckbox.setChecked(block_info.get("requires_title", False))
        
        if dialog.exec_() == QDialog.Accepted:
            description = dialog.descriptionEdit.text().strip()
            template = dialog.templateEdit.toPlainText().strip()
            requires_title = dialog.requiresTitleCheckbox.isChecked()
            
            # 更新设置
            blocks[identifier] = {
                "description": description,
                "template": template,
                "requires_title": requires_title
            }
            self.plugin.set_setting("custom_blocks", blocks)
            # 保存到JSON文件
            self.plugin.save_config_to_json()
            self.loadBlocks()
    
    def deleteBlock(self, identifier):
        reply = QMessageBox.question(self, "确认删除", 
                                     f"确定要删除语句块 '{identifier}' 吗？",
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            blocks = self.plugin.get_setting("custom_blocks", {})
            if identifier in blocks:
                del blocks[identifier]
                self.plugin.set_setting("custom_blocks", blocks)
                # 保存到JSON文件
                self.plugin.save_config_to_json()
                self.loadBlocks()

class BlockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("语句块设置")
        self.resize(400, 300)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        # 标识符
        self.identifierEdit = QLineEdit()
        formLayout.addRow("语句块标识:", self.identifierEdit)
        
        # 描述
        self.descriptionEdit = QLineEdit()
        formLayout.addRow("描述:", self.descriptionEdit)
        
        # 是否需要标题
        self.requiresTitleCheckbox = QCheckBox()
        self.requiresTitleCheckbox.setChecked(True)
        formLayout.addRow("需要标题:", self.requiresTitleCheckbox)
        
        layout.addLayout(formLayout)
        
        # 替换模板
        layout.addWidget(QLabel("替换模板:"))
        self.templateEdit = QTextEdit()
        self.templateEdit.setPlaceholderText("使用 {{title}} 表示标题，{{content}} 表示内容")
        layout.addWidget(self.templateEdit)
        
        # 按钮
        buttonLayout = QHBoxLayout()
        okButton = QPushButton("确定")
        okButton.clicked.connect(self.accept)
        cancelButton = QPushButton("取消")
        cancelButton.clicked.connect(self.reject)
        
        buttonLayout.addStretch()
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        layout.addLayout(buttonLayout)
    
    def accept(self):
        # 验证输入
        if not self.identifierEdit.text().strip():
            QMessageBox.warning(self, "输入错误", "语句块标识不能为空")
            return
        
        if not self.templateEdit.toPlainText().strip():
            QMessageBox.warning(self, "输入错误", "替换模板不能为空")
            return
            
        super().accept()

class Plugin(PluginBase):
    name = "自定义Markdown语句块"
    version = "1.0.0"
    author = "MGit"
    description = "允许用户自定义Markdown语句块，并在预览或导出时转换为标准Markdown格式"
    plugin_type = "编辑器"
    
    # 配置文件名
    CONFIG_FILENAME = "custom_blocks.json"
    
    # 默认设置
    settings = {
        "custom_blocks": {
            "type": "object",
            "default": {
                "callout": {
                    "description": "提示框",
                    "template": "> **{{title}}**\n> {{content}}",
                    "requires_title": True
                },
                "warning": {
                    "description": "警告框",
                    "template": "> **⚠️ 警告{{title}}**\n> {{content}}",
                    "requires_title": False
                }
            }
        }
    }
    
    def __init__(self):
        super().__init__()
        self.settings_widget = None
        self.config_loaded = False
    
    def initialize(self, app):
        super().initialize(app)
        # 确保配置目录存在
        self.ensure_config_dir()
        # 加载配置
        self.load_config_from_json()
    
    def get_config_dir(self):
        """获取插件配置目录路径"""
        # 获取用户主目录
        home_dir = str(pathlib.Path.home())
        # 创建 .mgit/plugins/custom_md_block 目录路径
        config_dir = os.path.join(home_dir, '.mgit', 'plugins', 'custom_md_block')
        return config_dir
    
    def get_config_file_path(self):
        """获取配置文件完整路径"""
        return os.path.join(self.get_config_dir(), self.CONFIG_FILENAME)
    
    def ensure_config_dir(self):
        """确保配置目录存在"""
        config_dir = self.get_config_dir()
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
                from src.utils.logger import info
                info(f"为自定义Markdown语句块插件创建配置目录: {config_dir}")
            except Exception as e:
                from src.utils.logger import error
                error(f"创建配置目录失败: {str(e)}")
    
    def save_config_to_json(self):
        """将当前配置保存到JSON文件"""
        try:
            config_file = self.get_config_file_path()
            blocks = self.get_setting("custom_blocks", {})
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(blocks, f, ensure_ascii=False, indent=2)
                
            from src.utils.logger import info
            info(f"自定义Markdown语句块配置已保存到: {config_file}")
            return True
        except Exception as e:
            from src.utils.logger import error
            error(f"保存配置文件失败: {str(e)}")
            return False
    
    def load_config_from_json(self):
        """从JSON文件加载配置"""
        if self.config_loaded:
            return
            
        config_file = self.get_config_file_path()
        if not os.path.exists(config_file):
            self.save_config_to_json()  # 保存默认配置
            self.config_loaded = True
            return
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                blocks = json.load(f)
                
            if blocks:
                # 更新插件设置
                self.set_setting("custom_blocks", blocks)
                
            from src.utils.logger import info
            info(f"已从 {config_file} 加载自定义Markdown语句块配置")
            self.config_loaded = True
        except Exception as e:
            from src.utils.logger import error
            error(f"加载配置文件失败: {str(e)}")
    
    def get_hooks(self):
        return {
            'modify_markdown': self.process_custom_blocks,
            'pre_save_file': self.process_save_file
        }
    
    def get_settings_widget(self):
        if not self.settings_widget:
            self.settings_widget = CustomBlockSettingsWidget(self)
        return self.settings_widget
    
    def process_custom_blocks(self, html_content, markdown_text):
        """处理Markdown预览时的自定义语句块"""
        # 处理已经渲染好的HTML内容不会改变，
        # 因为已经由原始的Markdown渲染器处理过了
        return html_content
    
    def process_save_file(self, file_path, content):
        """处理保存文件前的内容，转换自定义语句块"""
        if not file_path.lower().endswith(('.md', '.markdown')):
            return content
        
        # 获取自定义语句块定义
        custom_blocks = self.get_setting("custom_blocks", {})
        if not custom_blocks:
            return content
        
        # 定义正则表达式来匹配自定义语句块
        # 格式: ```identifier [title]
        #       content
        #       ```
        pattern = r'```({})(?:\s+(.+?))?\n(.*?)```'
        
        def replace_block(match):
            identifier = match.group(1)
            title = match.group(2) or ""
            content = match.group(3)
            
            if identifier not in custom_blocks:
                # 如果不是自定义语句块，则保持原样
                original = f"```{identifier}"
                if title:
                    original += f" {title}"
                original += f"\n{content}```"
                return original
            
            block_info = custom_blocks[identifier]
            template = block_info.get("template", "")
            requires_title = block_info.get("requires_title", False)
            
            # 如果需要标题但没有提供，使用默认标题
            if requires_title and not title:
                title = block_info.get("description", identifier)
            
            # 替换模板中的占位符
            result = template.replace("{{content}}", content)
            result = result.replace("{{title}}", title)
            
            return result
        
        # 执行替换
        identifiers = "|".join(re.escape(id) for id in custom_blocks.keys())
        pattern = pattern.format(identifiers)
        modified_content = re.sub(pattern, replace_block, content, flags=re.DOTALL)
        
        return modified_content 