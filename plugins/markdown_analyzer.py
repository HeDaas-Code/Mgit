#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Markdown分析插件 - 为MGit添加Markdown文档分析功能
该插件提供了文档关键词提取和词云生成功能

注意: 本插件可以在没有安装所有依赖的情况下运行，但功能将受限:
- 如果没有安装jieba，将无法进行中文分词
- 如果没有安装nltk，将无法进行英文分词和停用词过滤
- 如果没有安装wordcloud或matplotlib，将无法生成词云
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
                           QPushButton, QTabWidget, QFileDialog, QApplication,
                           QDialog, QGridLayout, QLineEdit, QScrollArea, QMessageBox,
                           QCheckBox, QMenu)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QPalette, QIcon
import re
import io
import os
import sys
import platform
import tempfile
from collections import Counter

# 导入自定义的插件基类
from src.utils.plugin_base import PluginBase

# 尝试导入需要的第三方库，将每个库的导入放在单独的try-except块中
# NLTK相关库
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    nltk_available = True
except ImportError:
    nltk_available = False

# WordCloud相关库
try:
    import wordcloud
    from wordcloud import WordCloud
    wordcloud_available = True
except ImportError:
    wordcloud_available = False

# 数据处理相关库
try:
    import numpy as np
    numpy_available = True
except ImportError:
    numpy_available = False

# 图像处理相关库
try:
    from PIL import Image
    pillow_available = True
except ImportError:
    pillow_available = False

# matplotlib相关库
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    matplotlib_available = True
except ImportError:
    matplotlib_available = False

# 中文分词库
try:
    import jieba
    jieba_available = True
except ImportError:
    jieba_available = False

class MarkdownAnalyzerWidget(QWidget):
    """Markdown分析器小部件"""
    
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        # 保存主窗口引用
        self.main_window = parent if parent else (plugin.app if hasattr(plugin, 'app') else None)
        self.setWindowTitle("Markdown分析器")  # 设置窗口标题
        self.setAttribute(Qt.WA_DeleteOnClose, True)  # 关闭时删除窗口
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        # 主布局
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        
        # 添加标题栏
        titleBar = QWidget()
        titleBar.setStyleSheet("background-color: #4B6EAF; color: white;")
        titleBar.setFixedHeight(40)  # 固定高度
        titleBarLayout = QHBoxLayout(titleBar)
        titleBarLayout.setContentsMargins(10, 0, 10, 0)
        
        # 插件菜单按钮
        self.pluginMenuButton = QPushButton("插件")
        self.pluginMenuButton.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.pluginMenuButton.clicked.connect(self.showPluginMenu)
        titleBarLayout.addWidget(self.pluginMenuButton)
        
        # 帮助菜单按钮
        self.helpButton = QPushButton("帮助")
        self.helpButton.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.helpButton.clicked.connect(self.showHelpMenu)
        titleBarLayout.addWidget(self.helpButton)
        
        # 标题标签
        titleLabel = QLabel("Markdown文档分析器")
        titleLabel.setStyleSheet("font-size: 14px; font-weight: bold;")
        titleBarLayout.addWidget(titleLabel)
        
        # 占位空间
        titleBarLayout.addStretch(1)
        
        # 设置按钮
        self.settingsButton = QPushButton("设置")
        self.settingsButton.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.settingsButton.clicked.connect(self.showSettings)
        titleBarLayout.addWidget(self.settingsButton)
        
        # 添加到主布局
        mainLayout.addWidget(titleBar)
        
        # 内容区域
        contentWidget = QWidget()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部控制按钮
        buttonLayout = QHBoxLayout()
        
        self.analyzeButton = QPushButton("分析当前文档")
        self.analyzeButton.clicked.connect(self.analyzeCurrentDocument)
        buttonLayout.addWidget(self.analyzeButton)
        
        self.saveButton = QPushButton("保存分析结果")
        self.saveButton.clicked.connect(self.saveResults)
        self.saveButton.setEnabled(False)  # 初始禁用
        buttonLayout.addWidget(self.saveButton)
        
        contentLayout.addLayout(buttonLayout)
        
        # 创建选项卡小部件
        self.tabs = QTabWidget()
        self.keywordTab = QWidget()
        self.wordcloudTab = QWidget()
        
        self.tabs.addTab(self.keywordTab, "关键词分析")
        self.tabs.addTab(self.wordcloudTab, "词云生成")
        
        self.setupKeywordTab()
        self.setupWordcloudTab()
        
        contentLayout.addWidget(self.tabs)
        
        # 添加状态标签
        self.statusLabel = QLabel("准备就绪。点击\"分析当前文档\"按钮开始分析。")
        self.statusLabel.setStyleSheet("color: gray; margin-top: 5px;")
        contentLayout.addWidget(self.statusLabel)
        
        # 将内容区域添加到主布局
        mainLayout.addWidget(contentWidget)
        
        # 设置合适的大小
        self.resize(650, 500)
    
    def setupKeywordTab(self):
        """设置关键词分析选项卡"""
        layout = QVBoxLayout(self.keywordTab)
        
        # 关键词列表标签
        self.keywordLabel = QLabel("文档关键词:")
        layout.addWidget(self.keywordLabel)
        
        # 关键词结果区域
        self.keywordResultLabel = QLabel("分析结果将显示在这里")
        self.keywordResultLabel.setAlignment(Qt.AlignCenter)
        self.keywordResultLabel.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        self.keywordResultLabel.setWordWrap(True)
        layout.addWidget(self.keywordResultLabel)
        
        layout.addStretch(1)
    
    def setupWordcloudTab(self):
        """设置词云生成选项卡"""
        layout = QVBoxLayout(self.wordcloudTab)
        
        # 词云图像显示区域
        self.wordcloudLabel = QLabel("词云将显示在这里")
        self.wordcloudLabel.setAlignment(Qt.AlignCenter)
        self.wordcloudLabel.setMinimumHeight(300)
        self.wordcloudLabel.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.wordcloudLabel)
        
        # 调整按钮布局
        optionsLayout = QHBoxLayout()
        
        self.regenerateButton = QPushButton("重新生成")
        self.regenerateButton.clicked.connect(self.regenerateWordcloud)
        self.regenerateButton.setEnabled(False)  # 初始禁用
        optionsLayout.addWidget(self.regenerateButton)
        
        layout.addLayout(optionsLayout)
        layout.addStretch(1)
    
    def analyzeCurrentDocument(self):
        """分析当前文档内容"""
        try:
            # 更新状态
            self.statusLabel.setText("正在分析文档...")
            self.statusLabel.setStyleSheet("color: blue;")
            
            # 使用插件的getCurrentEditorContent方法获取当前编辑器内容
            from src.utils.logger import info
            text = None
            
            # 先尝试通过插件获取
            text = self.plugin.getCurrentEditorContent()
            
            # 如果失败，通过自身保存的main_window引用尝试获取
            if not text and hasattr(self, 'main_window') and self.main_window:
                info("通过widget自身的main_window引用尝试获取编辑器内容")
                # 直接使用main_window进行查找
                if hasattr(self.main_window, 'getCurrentMarkdownContent'):
                    text = self.main_window.getCurrentMarkdownContent()
                    info("通过main_window.getCurrentMarkdownContent获取到内容")
                # 尝试其他可能的方法...
                elif hasattr(self.main_window, 'editor'):
                    editor = self.main_window.editor
                    if editor and hasattr(editor, 'toPlainText'):
                        text = editor.toPlainText()
                        info("通过main_window.editor.toPlainText获取到内容")
            
            # 如果仍然失败，尝试从应用实例获取所有顶级窗口
            if not text:
                try:
                    from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPlainTextEdit
                    # 尝试找到应用程序中的所有主窗口
                    for widget in QApplication.instance().topLevelWidgets():
                        if isinstance(widget, QMainWindow):
                            info(f"发现主窗口: {type(widget).__name__}")
                            # 尝试从中央widget中查找文本编辑器
                            central = widget.centralWidget()
                            if central:
                                # 在MainWindow的centralWidget中查找编辑器组件
                                text_edit = central.findChild(QTextEdit)
                                if text_edit:
                                    text = text_edit.toPlainText()
                                    info(f"找到QTextEdit编辑器，获取内容成功")
                                    break
                                
                                plain_text_edit = central.findChild(QPlainTextEdit)
                                if plain_text_edit:
                                    text = plain_text_edit.toPlainText()
                                    info(f"找到QPlainTextEdit编辑器，获取内容成功")
                                    break
                except Exception as e:
                    info(f"通过QApplication查找顶级窗口失败: {str(e)}")
            
            # 检查是否获取到了文本
            if not text:
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                # 通知用户找不到编辑器
                QMessageBox.information(
                    self, 
                    "找不到当前编辑器", 
                    "无法获取当前编辑器内容。将提示您选择一个Markdown文件进行分析。"
                )
                
                # 提示用户选择文件
                self.statusLabel.setText("找不到当前编辑器，请选择一个Markdown文件...")
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择Markdown文件", "", "Markdown文件 (*.md *.markdown);;所有文件 (*.*)"
                )
                
                if file_path:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        # 显示正在分析的文件路径
                        self.statusLabel.setText(f"正在分析文件: {os.path.basename(file_path)}...")
                    except Exception as file_e:
                        self.statusLabel.setText(f"读取文件失败: {str(file_e)}")
                        self.statusLabel.setStyleSheet("color: red;")
                        return
                else:
                    self.statusLabel.setText("操作取消，未选择文件")
                    self.statusLabel.setStyleSheet("color: orange;")
                    return
            
            if not text.strip():
                self.statusLabel.setText("错误：文档为空，无法分析")
                self.statusLabel.setStyleSheet("color: red;")
                return
            
            # 以下是原有的文档分析逻辑
            # 更新状态
            self.statusLabel.setText("正在过滤Markdown标记...")
            
            # 过滤Markdown标记
            filtered_text = self.plugin.filter_markdown_marks(text)
            
            # 更新状态
            self.statusLabel.setText("正在进行关键词分析...")
            
            # 检查是否可以进行关键词分析
            if nltk_available or jieba_available:
                # 进行关键词分析
                self.performKeywordAnalysis(filtered_text)
            else:
                self.keywordResultLabel.setText("无法进行关键词分析：缺少必要的依赖库（NLTK或jieba）")
                self.statusLabel.setText("警告：无法进行完整分析，缺少必要的依赖库")
                self.statusLabel.setStyleSheet("color: orange;")
            
            # 更新状态
            self.statusLabel.setText("正在生成词云...")
            
            # 检查是否可以生成词云
            if wordcloud_available and matplotlib_available:
                # 生成词云
                self.generateWordcloud(filtered_text)
            else:
                self.wordcloudLabel.setText("无法生成词云：缺少必要的依赖库（WordCloud或matplotlib）")
                self.statusLabel.setText("警告：无法生成词云，缺少必要的依赖库")
                self.statusLabel.setStyleSheet("color: orange;")
            
            # 启用保存按钮，但仅当至少有一个功能可用时
            if (nltk_available or jieba_available) or (wordcloud_available and matplotlib_available):
                self.saveButton.setEnabled(True)
                self.regenerateButton.setEnabled(wordcloud_available and matplotlib_available)
            
            # 更新状态
            if not (nltk_available or jieba_available) and not (wordcloud_available and matplotlib_available):
                self.statusLabel.setText("警告：所有分析功能不可用，请安装必要的依赖库")
                self.statusLabel.setStyleSheet("color: red;")
            else:
                self.statusLabel.setText("分析完成! 部分功能可能不可用。")
                self.statusLabel.setStyleSheet("color: green;")
        except Exception as e:
            from src.utils.logger import error
            error(f"文档分析失败: {str(e)}")
            import traceback
            error(traceback.format_exc())
            self.statusLabel.setText(f"分析失败: {str(e)}")
            self.statusLabel.setStyleSheet("color: red;")
            
            # 提示用户选择文件
            from PyQt5.QtWidgets import QMessageBox, QFileDialog
            reply = QMessageBox.question(
                self, 
                "分析失败", 
                "分析当前文档失败。是否要手动选择一个Markdown文件进行分析？",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择Markdown文件", "", "Markdown文件 (*.md *.markdown);;所有文件 (*.*)"
                )
                
                if file_path:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        
                        # 重新尝试分析
                        filtered_text = self.plugin.filter_markdown_marks(text)
                        
                        # 进行关键词分析
                        if nltk_available or jieba_available:
                            self.performKeywordAnalysis(filtered_text)
                        
                        # 生成词云
                        if wordcloud_available and matplotlib_available:
                            self.generateWordcloud(filtered_text)
                        
                        # 启用保存按钮
                        if (nltk_available or jieba_available) or (wordcloud_available and matplotlib_available):
                            self.saveButton.setEnabled(True)
                            self.regenerateButton.setEnabled(wordcloud_available and matplotlib_available)
                        
                        self.statusLabel.setText("文件分析完成!")
                        self.statusLabel.setStyleSheet("color: green;")
                    except Exception as e2:
                        self.statusLabel.setText(f"分析文件失败: {str(e2)}")
                        self.statusLabel.setStyleSheet("color: red;")
                else:
                    self.statusLabel.setText("操作取消，未选择文件")
                    self.statusLabel.setStyleSheet("color: orange;")
    
    def performKeywordAnalysis(self, text):
        """执行关键词分析"""
        try:
            # 检查必要的依赖
            if not nltk_available and not jieba_available:
                self.keywordResultLabel.setText("无法进行关键词分析：缺少必要的依赖库（NLTK和jieba）")
                return
            
            # 确保nltk资源已下载，如果可用
            if nltk_available:
                self.plugin.ensure_nltk_resources()
            
            # 检测语言（简单判断，中文字符比例）
            chinese_char_count = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            is_chinese_doc = chinese_char_count > len(text) * 0.1  # 如果中文字符超过10%，认为是中文文档
            
            if is_chinese_doc and jieba_available:
                # 使用jieba进行中文分词
                words = jieba.lcut(text)
                # 过滤停用词
                cn_stopwords = self.plugin.get_chinese_stopwords()
                filtered_words = [word for word in words 
                                 if len(word.strip()) > 1 
                                 and word not in cn_stopwords]
            elif nltk_available:
                # 英文分词
                tokens = word_tokenize(text.lower())
                # 过滤掉英文停用词
                try:
                    stop_words = set(stopwords.words('english'))
                except:
                    # 如果无法加载停用词，使用空集合
                    stop_words = set()
                filtered_words = [word for word in tokens 
                                 if word.isalpha() 
                                 and word not in stop_words 
                                 and len(word) > 1]
            else:
                # 简单分词（使用空格分割，作为后备选项）
                words = text.split()
                filtered_words = [word for word in words if len(word.strip()) > 1]
            
            # 计算词频
            word_counts = Counter(filtered_words)
            
            # 获取最常见的15个词
            common_words = word_counts.most_common(15)
            
            # 更新UI
            if common_words:
                result_text = "文档关键词 (频次):\n\n"
                for word, count in common_words:
                    result_text += f"{word}: {count}\n"
                self.keywordResultLabel.setText(result_text)
            else:
                self.keywordResultLabel.setText("未找到有意义的关键词")
                
        except Exception as e:
            self.keywordResultLabel.setText(f"分析失败: {str(e)}")
            from src.utils.logger import error
            error(f"关键词分析失败: {str(e)}")
            import traceback
            error(traceback.format_exc())
    
    def generateWordcloud(self, text):
        """生成词云"""
        try:
            # 检查必要的依赖
            if not wordcloud_available or not matplotlib_available:
                self.wordcloudLabel.setText("无法生成词云：缺少必要的依赖库（WordCloud或matplotlib）")
                return
            
            # 检测是否包含中文
            chinese_char_count = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            is_chinese_doc = chinese_char_count > len(text) * 0.1
            
            if is_chinese_doc and jieba_available:
                # 中文分词
                text_with_spaces = ' '.join(jieba.lcut(text))
                font_path = self.plugin.get_font_path()
                # 如果没有设置字体，使用一个合适的中文字体
                if not font_path or not os.path.exists(font_path):
                    font_path = None
                    try:
                        # 尝试使用资源管理器获取系统字体
                        from plugins.resources.markdown_analyzer.resource_manager import get_resource_manager
                        resource_manager = get_resource_manager()
                        font_path = resource_manager.get_system_font()
                    except:
                        pass
                
                # 创建词云对象（中文），如果有字体的话
                if font_path:
                    wc = WordCloud(
                        width=800, 
                        height=400,
                        background_color='white',
                        max_words=100,
                        contour_width=1,
                        contour_color='steelblue',
                        font_path=font_path  # 使用支持中文的字体
                    )
                else:
                    # 无法显示中文字符，显示英文或发出警告
                    self.wordcloudLabel.setText("警告：未找到支持中文的字体，词云可能无法正确显示中文。")
                    wc = WordCloud(
                        width=800, 
                        height=400,
                        background_color='white',
                        max_words=100,
                        contour_width=1,
                        contour_color='steelblue'
                    )
                
                # 生成词云
                try:
                    wordcloud_image = wc.generate(text_with_spaces)
                except Exception as e:
                    # 如果生成失败，尝试使用英文文本或简单文本
                    if "font" in str(e).lower():
                        self.wordcloudLabel.setText("无法使用中文字体生成词云，请在设置中指定有效的字体文件。")
                        return
                    else:
                        # 尝试使用普通英文文本生成
                        try:
                            wordcloud_image = wc.generate(text)
                        except:
                            self.wordcloudLabel.setText(f"生成词云失败: {str(e)}")
                            return
            else:
                # 英文词云生成
                # 创建词云对象
                try:
                    wc = WordCloud(
                        width=800, 
                        height=400,
                        background_color='white',
                        max_words=100,
                        contour_width=1,
                        contour_color='steelblue'
                    )
                    
                    # 生成词云
                    wordcloud_image = wc.generate(text)
                except Exception as e:
                    self.wordcloudLabel.setText(f"生成词云失败: {str(e)}")
                    return
            
            # 转换为QPixmap并显示
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud_image, interpolation='bilinear')
            plt.axis("off")
            
            # 将matplotlib图形转换为QPixmap
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            
            # 创建QImage和QPixmap
            image = QImage.fromData(buf.getvalue())
            pixmap = QPixmap.fromImage(image)
            
            # 调整大小以适应标签
            pixmap = pixmap.scaled(self.wordcloudLabel.width(), 300, 
                                  Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 显示在标签上
            self.wordcloudLabel.setPixmap(pixmap)
            self.wordcloudLabel.setAlignment(Qt.AlignCenter)
            
            # 关闭matplotlib图形
            plt.close()
            
        except Exception as e:
            self.wordcloudLabel.setText(f"词云生成失败: {str(e)}")
            from src.utils.logger import error
            error(f"词云生成失败: {str(e)}")
            import traceback
            error(traceback.format_exc())
    
    def regenerateWordcloud(self):
        """重新生成词云，使用不同的样式"""
        try:
            # 使用插件的getCurrentEditorContent方法获取当前编辑器内容
            from src.utils.logger import info
            text = None
            
            # 先尝试通过插件获取
            text = self.plugin.getCurrentEditorContent()
            
            # 如果失败，通过自身保存的main_window引用尝试获取
            if not text and hasattr(self, 'main_window') and self.main_window:
                info("通过widget自身的main_window引用尝试获取编辑器内容")
                # 直接使用main_window进行查找
                if hasattr(self.main_window, 'getCurrentMarkdownContent'):
                    text = self.main_window.getCurrentMarkdownContent()
                    info("通过main_window.getCurrentMarkdownContent获取到内容")
                # 尝试其他可能的方法...
                elif hasattr(self.main_window, 'editor'):
                    editor = self.main_window.editor
                    if editor and hasattr(editor, 'toPlainText'):
                        text = editor.toPlainText()
                        info("通过main_window.editor.toPlainText获取到内容")
            
            # 如果仍然失败，尝试从应用实例获取所有顶级窗口
            if not text:
                try:
                    from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPlainTextEdit
                    # 尝试找到应用程序中的所有主窗口
                    for widget in QApplication.instance().topLevelWidgets():
                        if isinstance(widget, QMainWindow):
                            info(f"发现主窗口: {type(widget).__name__}")
                            # 尝试从中央widget中查找文本编辑器
                            central = widget.centralWidget()
                            if central:
                                # 在MainWindow的centralWidget中查找编辑器组件
                                text_edit = central.findChild(QTextEdit)
                                if text_edit:
                                    text = text_edit.toPlainText()
                                    info(f"找到QTextEdit编辑器，获取内容成功")
                                    break
                                
                                plain_text_edit = central.findChild(QPlainTextEdit)
                                if plain_text_edit:
                                    text = plain_text_edit.toPlainText()
                                    info(f"找到QPlainTextEdit编辑器，获取内容成功")
                                    break
                except Exception as e:
                    info(f"通过QApplication查找顶级窗口失败: {str(e)}")
            
            # 检查是否获取到了文本
            if not text:
                from PyQt5.QtWidgets import QFileDialog, QMessageBox
                # 通知用户找不到编辑器
                reply = QMessageBox.question(
                    self, 
                    "找不到当前编辑器", 
                    "无法获取当前编辑器内容。是否要手动选择一个Markdown文件重新生成词云？",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    file_path, _ = QFileDialog.getOpenFileName(
                        self, "选择Markdown文件", "", "Markdown文件 (*.md *.markdown);;所有文件 (*.*)"
                    )
                    
                    if file_path:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                text = f.read()
                            # 显示正在分析的文件路径
                            self.statusLabel.setText(f"正在处理文件: {os.path.basename(file_path)}...")
                        except Exception as file_e:
                            self.statusLabel.setText(f"读取文件失败: {str(file_e)}")
                            self.statusLabel.setStyleSheet("color: red;")
                            return
                    else:
                        self.statusLabel.setText("操作取消，未选择文件")
                        self.statusLabel.setStyleSheet("color: orange;")
                        return
                else:
                    self.statusLabel.setText("操作取消")
                    self.statusLabel.setStyleSheet("color: orange;")
                    return
            
            # 过滤Markdown标记
            filtered_text = self.plugin.filter_markdown_marks(text)
            
            # 检测是否包含中文
            chinese_char_count = len([c for c in filtered_text if '\u4e00' <= c <= '\u9fff'])
            is_chinese_doc = chinese_char_count > len(filtered_text) * 0.1
            
            if not wordcloud_available or not matplotlib_available:
                self.statusLabel.setText("无法生成词云：缺少必要的依赖库（WordCloud或matplotlib）")
                self.statusLabel.setStyleSheet("color: orange;")
                return
            
            # 更新状态
            self.statusLabel.setText("正在重新生成词云...")
            
            # 获取字体路径
            font_path = self.plugin.get_font_path()
            if not font_path or not os.path.exists(font_path):
                try:
                    from plugins.resources.markdown_analyzer.resource_manager import get_resource_manager
                    resource_manager = get_resource_manager()
                    font_path = resource_manager.get_system_font()
                except:
                    font_path = None
            
            if is_chinese_doc:
                # 中文分词
                if not jieba_available:
                    self.statusLabel.setText("无法处理中文文档：缺少jieba库")
                    self.statusLabel.setStyleSheet("color: orange;")
                    return
                    
                text_with_spaces = ' '.join(jieba.lcut(filtered_text))
                
                # 创建词云对象，使用不同参数
                wc = wordcloud.WordCloud(
                    width=800, 
                    height=400,
                    background_color='black',
                    max_words=100,
                    contour_width=0,
                    colormap='viridis',
                    font_path=font_path
                )
                
                # 生成词云
                wordcloud_image = wc.generate(text_with_spaces)
            else:
                # 创建词云对象，使用不同参数
                wc = wordcloud.WordCloud(
                    width=800, 
                    height=400,
                    background_color='black',
                    max_words=100,
                    contour_width=0,
                    colormap='viridis',
                    font_path=font_path
                )
                
                # 生成词云
                wordcloud_image = wc.generate(filtered_text)
            
            # 转换为QPixmap并显示
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud_image, interpolation='bilinear')
            plt.axis("off")
            
            # 将matplotlib图形转换为QPixmap
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            
            # 创建QImage和QPixmap
            image = QImage.fromData(buf.getvalue())
            pixmap = QPixmap.fromImage(image)
            
            # 调整大小以适应标签
            pixmap = pixmap.scaled(self.wordcloudLabel.width(), 300, 
                                  Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 显示在标签上
            self.wordcloudLabel.setPixmap(pixmap)
            self.wordcloudLabel.setAlignment(Qt.AlignCenter)
            
            # 关闭matplotlib图形
            plt.close()
            
            # 更新状态
            self.statusLabel.setText("词云已重新生成！")
            self.statusLabel.setStyleSheet("color: green;")
            
        except Exception as e:
            self.wordcloudLabel.setText(f"词云重新生成失败: {str(e)}")
            from src.utils.logger import error
            error(f"词云重新生成失败: {str(e)}")
            import traceback
            error(traceback.format_exc())
    
    def saveResults(self):
        """保存分析结果"""
        # 获取当前选项卡
        current_tab = self.tabs.currentWidget()
        
        if current_tab == self.keywordTab:
            # 保存关键词分析结果为文本文件
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "保存关键词分析结果",
                "",
                "文本文件 (*.txt)"
            )
            
            if filepath:
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(self.keywordResultLabel.text())
                except Exception as e:
                    self.plugin.app.show_status_message(f"保存失败: {str(e)}", 5000)
                    return
                
                self.plugin.app.show_status_message("关键词分析结果已保存", 3000)
                
        elif current_tab == self.wordcloudTab:
            # 保存词云为图片
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "保存词云图像",
                "",
                "PNG图像 (*.png);;JPEG图像 (*.jpg *.jpeg)"
            )
            
            if filepath:
                try:
                    # 获取QPixmap并保存
                    pixmap = self.wordcloudLabel.pixmap()
                    if pixmap and not pixmap.isNull():
                        pixmap.save(filepath)
                    else:
                        raise ValueError("无可用的词云图像")
                except Exception as e:
                    self.plugin.app.show_status_message(f"保存失败: {str(e)}", 5000)
                    return
                
                self.plugin.app.show_status_message("词云图像已保存", 3000)
    
    def showPluginMenu(self):
        """显示插件菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #aaa;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """)
        
        refreshAction = menu.addAction("刷新分析")
        refreshAction.triggered.connect(self.analyzeCurrentDocument)
        
        menu.addSeparator()
        
        exportAction = menu.addAction("导出结果")
        exportAction.triggered.connect(self.saveResults)
        
        menu.addSeparator()
        
        if hasattr(self.plugin, 'app') and hasattr(self.plugin.app, 'get_plugins'):
            # 添加其他插件的菜单项
            otherPluginsMenu = menu.addMenu("其他插件")
            try:
                plugins = self.plugin.app.get_plugins()
                for plugin_name, plugin in plugins.items():
                    if plugin_name != self.plugin.name and hasattr(plugin, 'show_view'):
                        action = otherPluginsMenu.addAction(plugin_name)
                        action.triggered.connect(lambda _, p=plugin: p.show_view())
            except Exception as e:
                from src.utils.logger import error
                error(f"获取其他插件列表失败: {str(e)}")
        
        # 显示菜单
        menu.exec_(self.pluginMenuButton.mapToGlobal(self.pluginMenuButton.rect().bottomLeft()))
    
    def showHelpMenu(self):
        """显示帮助菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #aaa;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """)
        
        aboutAction = menu.addAction("关于")
        aboutAction.triggered.connect(self.showAbout)
        
        helpAction = menu.addAction("使用帮助")
        helpAction.triggered.connect(self.showHelp)
        
        # 显示菜单
        menu.exec_(self.helpButton.mapToGlobal(self.helpButton.rect().bottomLeft()))
    
    def showSettings(self):
        """显示设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Markdown分析器设置")
        layout = QVBoxLayout(dialog)
        
        formLayout = QGridLayout()
        
        # 字体路径设置
        fontPathEdit = QLineEdit(self.plugin.get_setting('font_path', ''))
        formLayout.addWidget(QLabel("词云字体路径:"), 0, 0)
        formLayout.addWidget(fontPathEdit, 0, 1)
        
        # 最大词数设置
        maxWordsEdit = QLineEdit(str(self.plugin.get_setting('max_words', 100)))
        formLayout.addWidget(QLabel("词云最大显示词数:"), 1, 0)
        formLayout.addWidget(maxWordsEdit, 1, 1)
        
        # 启用英文分析
        enableEnglishCheck = QCheckBox()
        enableEnglishCheck.setChecked(bool(self.plugin.get_setting('enable_english', True)))
        formLayout.addWidget(QLabel("启用英文分析:"), 2, 0)
        formLayout.addWidget(enableEnglishCheck, 2, 1)
        
        # 启用中文分析
        enableChineseCheck = QCheckBox()
        enableChineseCheck.setChecked(bool(self.plugin.get_setting('enable_chinese', True)))
        formLayout.addWidget(QLabel("启用中文分析:"), 3, 0)
        formLayout.addWidget(enableChineseCheck, 3, 1)
        
        layout.addLayout(formLayout)
        
        # 按钮
        buttonLayout = QHBoxLayout()
        saveButton = QPushButton("保存")
        saveButton.clicked.connect(lambda: self.saveSettings(fontPathEdit.text(), maxWordsEdit.text(), enableEnglishCheck.isChecked(), enableChineseCheck.isChecked(), dialog))
        buttonLayout.addWidget(saveButton)
        
        cancelButton = QPushButton("取消")
        cancelButton.clicked.connect(dialog.reject)
        buttonLayout.addWidget(cancelButton)
        
        layout.addLayout(buttonLayout)
        
        dialog.setLayout(layout)
        dialog.resize(400, 200)
        dialog.exec_()
    
    def saveSettings(self, font_path, max_words, enable_english, enable_chinese, dialog):
        """保存设置"""
        self.plugin.set_setting('font_path', font_path)
        self.plugin.set_setting('max_words', int(max_words))
        self.plugin.set_setting('enable_english', enable_english)
        self.plugin.set_setting('enable_chinese', enable_chinese)
        dialog.accept()
        self.statusLabel.setText("设置已保存")
        self.statusLabel.setStyleSheet("color: green;")
    
    def showAbout(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于Markdown分析器", 
                         f"<h3>Markdown分析器</h3>"
                         f"<p>版本: {self.plugin.version}</p>"
                         f"<p>作者: {self.plugin.author}</p>"
                         f"<p>{self.plugin.description}</p>"
                         f"<p>基于NLTK和WordCloud库构建</p>")
    
    def showHelp(self):
        """显示帮助信息"""
        help_text = (
            "<h3>Markdown分析器使用指南</h3>"
            "<p><b>基本步骤:</b></p>"
            "<ol>"
            "<li>打开一个Markdown文档</li>"
            "<li>点击\"分析当前文档\"按钮</li>"
            "<li>查看\"关键词分析\"和\"词云生成\"标签页中的结果</li>"
            "<li>可选择\"保存分析结果\"保存结果</li>"
            "</ol>"
            "<p><b>词云生成:</b> 支持重新生成不同风格的词云</p>"
            "<p><b>设置:</b> 可以在设置中指定自定义字体</p>"
        )
        
        QMessageBox.information(self, "使用帮助", help_text)

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 通知插件窗口已关闭，清理引用
        try:
            from src.utils.logger import info
            info("Markdown分析器：窗口关闭")
            
            # 如果插件还持有此窗口的引用，将引用设为None
            if hasattr(self, 'plugin') and self.plugin and hasattr(self.plugin, 'widget'):
                if self.plugin.widget == self:
                    self.plugin.widget = None
        except Exception as e:
            from src.utils.logger import warning
            warning(f"Markdown分析器：窗口关闭事件处理失败: {str(e)}")
        
        # 继续处理关闭事件
        event.accept()

class Plugin(PluginBase):
    """Markdown分析器插件实现"""
    
    name = "Markdown分析器"
    version = "1.1.0"
    author = "MGit团队"
    description = "提供Markdown文档关键词提取和词云生成功能，支持中英文"
    plugin_type = "视图"  # 改为视图类型，确保能够作为视图加载
    
    # 指定菜单类别
    menu_category = "插件"
    
    # 插件依赖的Python包（标记为可选）
    package_dependencies = [
        # 依赖库列表，所有依赖均为可选
        "nltk>=3.6.0",  # 可选，用于英文分词和停用词
        "wordcloud>=1.8.1",  # 可选，用于生成词云
        "matplotlib>=3.4.0",  # 可选，用于显示词云
        "numpy>=1.20.0",  # 可选，用于数据处理
        "Pillow>=8.2.0",  # 可选，用于图像处理
        "jieba>=0.42.1"  # 可选，用于中文分词
    ]
    
    # 插件设置
    settings = {
        'font_path': {
            'type': 'string',
            'default': '',
            'description': '词云字体路径(留空使用系统默认字体)'
        },
        'max_words': {
            'type': 'int',
            'default': 100,
            'description': '词云最大显示词数'
        },
        'enable_english': {
            'type': 'bool',
            'default': True,
            'description': '启用英文分析'
        },
        'enable_chinese': {
            'type': 'bool',
            'default': True,
            'description': '启用中文分析'
        }
    }
    
    def __init__(self, plugin_manager=None):
        """初始化插件"""
        super().__init__()
        # 确保保存plugin_manager引用，以便后续可以获取最新的main_window
        self.plugin_manager = plugin_manager
        # 同时保存当前main_window引用作为备用
        self.app = getattr(plugin_manager, 'main_window', None) if plugin_manager else None
        self.widget = None
        self.nltk_resources_checked = False
        self.chinese_stopwords = None
        self.is_loaded = False
    
    def filter_markdown_marks(self, text):
        """过滤Markdown标记，保留纯文本内容"""
        # 正则表达式模式列表
        md_patterns = [
            (r'#+ .*$', ''),                    # 标题
            (r'!\[.*?\]\(.*?\)', ''),           # 图片
            (r'\[([^\]]+)\]\([^)]+\)', r'\1'),  # 链接，保留链接文本
            (r'`{3}[\s\S]*?`{3}', ''),          # 代码块
            (r'`.*?`', ''),                     # 行内代码
            (r'\*\*(.*?)\*\*', r'\1'),          # 粗体
            (r'__(.*?)__', r'\1'),              # 粗体
            (r'\*(.*?)\*', r'\1'),              # 斜体
            (r'_(.*?)_', r'\1'),                # 斜体
            (r'~~(.*?)~~', r'\1'),              # 删除线
            (r'^\s*[-*+]\s+', ''),              # 无序列表
            (r'^\s*\d+\.\s+', ''),              # 有序列表
            (r'^\s*>\s+', ''),                  # 引用
            (r'^\s*[-]{3,}\s*$', ''),           # 水平线(---)
            (r'^\s*[*]{3,}\s*$', ''),           # 水平线(***)
            (r'^\s*[_]{3,}\s*$', ''),           # 水平线(___)
            (r'\|.*?\|', ' '),                  # 表格
        ]
        
        # 依次应用所有模式
        filtered_text = text
        for pattern, replacement in md_patterns:
            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.MULTILINE)
        
        return filtered_text
    
    def ensure_nltk_resources(self):
        """确保NLTK资源可用"""
        try:
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context

            # 检查punkt分词器
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                try:
                    nltk.download('punkt', quiet=True)
                except Exception as e:
                    print(f"下载NLTK punkt资源失败: {str(e)}")

            # 检查stopwords
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                try:
                    nltk.download('stopwords', quiet=True)
                except Exception as e:
                    print(f"下载NLTK stopwords资源失败: {str(e)}")
        except Exception as e:
            print(f"确保NLTK资源时出错: {str(e)}")
    
    def get_chinese_stopwords(self):
        """获取中文停用词"""
        # 使用资源管理器获取停用词
        try:
            from plugins.resources.markdown_analyzer.resource_manager import get_resource_manager
            resource_manager = get_resource_manager()
            return resource_manager.get_chinese_stopwords()
        except Exception as e:
            print(f"获取中文停用词失败: {str(e)}")
            return set()
    
    def get_font_path(self):
        """获取适合的字体路径"""
        # 优先使用用户设置的字体
        try:
            if self.plugin_manager:
                font_path = self.plugin_manager.get_setting(self.name, 'font_path', '')
                if font_path and os.path.exists(font_path):
                    return font_path
        except:
            pass
        
        # 使用资源管理器获取字体
        try:
            from plugins.resources.markdown_analyzer.resource_manager import get_resource_manager
            resource_manager = get_resource_manager()
            font_path = resource_manager.get_system_font()
            if font_path:
                return font_path
        except Exception as e:
            print(f"获取系统字体失败: {str(e)}")
        
        # 返回默认字体（如果没有找到合适的字体）
        return None
    
    def tokenize_text(self, text):
        """对文本进行分词处理"""
        words = []
        
        # 中文分词
        try:
            import jieba
            chinese_words = jieba.lcut(text)
            words.extend(chinese_words)
        except Exception as e:
            print(f"中文分词出错: {str(e)}")
        
        # 英文分词
        try:
            from nltk.tokenize import word_tokenize
            english_words = word_tokenize(text)
            words.extend([word for word in english_words if re.match(r'^[a-zA-Z]+$', word)])
        except Exception as e:
            print(f"英文分词出错: {str(e)}")
        
        return words
    
    def initialize(self, app):
        """初始化插件"""
        try:
            if hasattr(app, 'add_plugin_widget'):
                app.add_plugin_widget(self.name, MarkdownAnalyzerWidget(self, app))
                self.is_loaded = True
                return True
            elif hasattr(app, 'add_plugin_view'):
                app.add_plugin_view(self.name, MarkdownAnalyzerWidget(self, app))
                self.is_loaded = True
                return True
            else:
                print(f"无法加载插件，应用不支持插件视图: {self.name}")
                return False
        except Exception as e:
            print(f"初始化Markdown分析器插件时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    def check_resources(self):
        """检查资源是否可用，输出调试信息"""
        try:
            print("正在检查Markdown分析器资源...")
            
            # 测试资源管理器
            from plugins.resources.markdown_analyzer.resource_manager import get_resource_manager
            resource_manager = get_resource_manager()
            
            # 检查停用词
            cn_stopwords = resource_manager.get_chinese_stopwords()
            en_stopwords = resource_manager.get_english_stopwords()
            print(f"中文停用词数量: {len(cn_stopwords)}")
            print(f"英文停用词数量: {len(en_stopwords)}")
            
            # 检查字体
            font_path = resource_manager.get_system_font()
            print(f"选择的字体路径: {font_path}")
            
            # 检查自定义字体目录
            fonts = resource_manager.get_available_fonts()
            print(f"可用自定义字体: {fonts}")
            
            return True
        except Exception as e:
            print(f"检查资源时出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
            
    def load(self):
        """加载插件"""
        if self.is_loaded:
            return True
        
        # 检查资源
        try:
            self.check_resources()
        except Exception as e:
            print(f"检查资源时出错: {str(e)}，但将继续加载插件")
        
        # 确保NLTK资源可用
        try:
            if nltk_available:
                self.ensure_nltk_resources()
        except Exception as e:
            print(f"加载NLTK资源时出错: {str(e)}，但将继续加载插件")
        
        # 检查依赖库可用性
        missing_deps = []
        
        if not nltk_available:
            missing_deps.append("nltk")
        if not wordcloud_available:
            missing_deps.append("wordcloud")
        if not matplotlib_available:
            missing_deps.append("matplotlib")
        if not numpy_available:
            missing_deps.append("numpy")
        if not pillow_available:
            missing_deps.append("Pillow")
        if not jieba_available:
            missing_deps.append("jieba")
        
        if missing_deps:
            print(f"警告：以下依赖库不可用: {', '.join(missing_deps)}")
            print("插件将以有限功能模式运行")
            
            # 确定哪些功能可用
            keyword_analysis_available = nltk_available or jieba_available
            wordcloud_generation_available = wordcloud_available and matplotlib_available
            
            if not keyword_analysis_available and not wordcloud_generation_available:
                print("警告：所有主要功能都不可用，插件将以最小功能模式运行")
        
        # 无论依赖情况如何，都返回成功加载
        return True
    
    def get_view(self):
        """获取插件视图"""
        if not self.widget:
            self.widget = MarkdownAnalyzerWidget(self)
        return self.widget
    
    def cleanup(self):
        """清理插件资源"""
        try:
            if self.widget:
                # 关闭窗口并删除它
                if hasattr(self.widget, 'close'):
                    self.widget.close()
                
                # 确保widget被销毁
                if hasattr(self.widget, 'deleteLater'):
                    self.widget.deleteLater()
                
                # 清除引用
                self.widget = None
                
            from src.utils.logger import info
            info("Markdown分析器：清理完成")
        except Exception as e:
            from src.utils.logger import warning
            warning(f"Markdown分析器：清理资源时出错: {str(e)}")
    
    def get_menu_items(self):
        """返回插件的菜单项"""
        return [
            {
                'name': '打开Markdown分析器',
                'callback': self.show_analyzer,
                'shortcut': 'Ctrl+Shift+A',
                'icon': 'text_description',  # 可选：使用图标
                'category': '插件'  # 指定菜单类别
            }
        ]
    
    def get_menu_category(self):
        """返回插件菜单类别"""
        return "插件"
        
    def get_plugin_menu(self):
        """返回插件专用菜单的定义"""
        return {
            'name': '分析工具',
            'items': [
                {
                    'name': 'Markdown文档分析',
                    'callback': self.show_analyzer,
                    'shortcut': 'Ctrl+Shift+A',
                    'icon': 'text_description'
                },
                {
                    'name': '批量文档分析',
                    'callback': self.show_batch_analyzer,
                    'icon': 'folder_open'
                },
                {
                    'name': '导出分析结果',
                    'callback': self.export_results,
                    'icon': 'save'
                }
            ]
        }
    
    def show_analyzer(self):
        """显示分析器面板"""
        try:
            # 检查widget是否已被删除或无效
            if self.widget is None or not hasattr(self.widget, 'isVisible') or not self.widget.isVisible():
                # 如果widget已被删除或无效，重新创建
                if self.widget is None or not hasattr(self.widget, 'isVisible'):
                    from src.utils.logger import info
                    info("Markdown分析器：窗口已被删除，重新创建...")
                    # 确保传递主窗口引用
                    self.widget = MarkdownAnalyzerWidget(self, self.app)
                
                # 显示为独立窗口
                self._show_standalone_window()
        except RuntimeError as e:
            # 捕获C++对象已删除的错误
            from src.utils.logger import warning
            warning(f"Markdown分析器：窗口对象已失效 ({str(e)})，重新创建...")
            # 确保传递主窗口引用
            self.widget = MarkdownAnalyzerWidget(self, self.app)
            self._show_standalone_window()
        except Exception as e:
            # 捕获其他可能的错误
            from src.utils.logger import error
            error(f"Markdown分析器：显示窗口时出错: {str(e)}")
            import traceback
            error(traceback.format_exc())
    
    def show_batch_analyzer(self):
        """显示批量分析窗口"""
        # 在此版本中不实现实际功能，只显示提示信息
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            None, 
            "功能预告", 
            "批量文档分析功能将在下一版本中推出，敬请期待！"
        )
    
    def export_results(self):
        """导出分析结果"""
        try:
            # 检查widget是否已被删除或无效
            widget_valid = self.widget is not None and hasattr(self.widget, 'isVisible')
            
            # 如果分析器窗口不存在、已失效或未显示，则提示用户先进行分析
            if not widget_valid or not self.widget.isVisible():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    None,
                    "提示",
                    "请先打开分析器并进行文档分析，然后再导出结果。"
                )
                
                # 如果widget已失效，创建一个新的，并显示它
                if not widget_valid:
                    from src.utils.logger import info
                    info("Markdown分析器：导出时发现窗口已被删除，重新创建...")
                    self.widget = MarkdownAnalyzerWidget(self)
                    self.show_analyzer()
            else:
                # 调用保存结果方法
                self.widget.saveResults()
        except RuntimeError as e:
            # 捕获C++对象已删除的错误
            from src.utils.logger import warning
            from PyQt5.QtWidgets import QMessageBox
            
            warning(f"Markdown分析器：导出时窗口对象已失效 ({str(e)})，重新创建...")
            QMessageBox.information(
                None,
                "提示",
                "请先打开分析器并进行文档分析，然后再导出结果。"
            )
            
            # 重新创建窗口并显示
            self.widget = MarkdownAnalyzerWidget(self)
            self.show_analyzer()
        except Exception as e:
            # 捕获其他可能的错误
            from src.utils.logger import error
            error(f"Markdown分析器：导出结果时出错: {str(e)}")
            import traceback
            error(traceback.format_exc())
    
    def get_view_name(self):
        """获取视图名称，用于在视图菜单中显示"""
        return "Markdown分析器"

    def _show_standalone_window(self):
        """显示独立窗口"""
        if not self.widget:
            # 确保把app引用正确传递给新窗口
            self.widget = MarkdownAnalyzerWidget(self, self.app)
        
        # 设置合适的窗口属性
        self.widget.setWindowTitle('MGit - Markdown分析器')
        
        # 适当调整大小
        try:
            from PyQt5.QtWidgets import QApplication
            desktop = QApplication.desktop().availableGeometry()
            width = min(800, desktop.width() * 0.7)
            height = min(600, desktop.height() * 0.7)
            self.widget.resize(int(width), int(height))
            
            # 居中显示
            self.widget.move((desktop.width() - self.widget.width()) // 2,
                           (desktop.height() - self.widget.height()) // 2)
        except Exception as e:
            from src.utils.logger import warning
            warning(f"调整窗口大小时出错: {str(e)}，使用默认大小")
            self.widget.resize(800, 600)
        
        # 显示窗口
        self.widget.show()

    def get_setting(self, key, default=None):
        """获取插件设置"""
        try:
            if self.plugin_manager and hasattr(self.plugin_manager, 'get_plugin_setting'):
                return self.plugin_manager.get_plugin_setting(self.name, key, default)
            elif key in self.settings:
                # 从默认设置返回
                return self.settings[key].get('default', default)
            return default
        except Exception as e:
            from src.utils.logger import warning
            warning(f"获取设置 {key} 失败: {str(e)}，使用默认值: {default}")
            return default
            
    def set_setting(self, key, value):
        """设置插件设置"""
        try:
            if self.plugin_manager and hasattr(self.plugin_manager, 'set_plugin_setting'):
                self.plugin_manager.set_plugin_setting(self.name, key, value)
            else:
                # 如果没有plugin_manager，可以添加一个临时存储
                if not hasattr(self, '_temp_settings'):
                    self._temp_settings = {}
                self._temp_settings[key] = value
        except Exception as e:
            from src.utils.logger import warning
            warning(f"保存设置 {key} 失败: {str(e)}")

    def getCurrentEditorContent(self):
        """获取当前编辑器内容的辅助方法"""
        # 尝试获取最新的主窗口引用，而不是使用可能已过期的self.app
        if self.plugin_manager and hasattr(self.plugin_manager, 'main_window'):
            main_window = self.plugin_manager.main_window
        else:
            main_window = self.app  # 回退到原始引用
        
        if main_window is None:
            from src.utils.logger import warning
            warning("无法获取主窗口，返回空内容")
            
            # 尝试查找可能的主窗口
            try:
                from PyQt5.QtWidgets import QApplication
                for widget in QApplication.instance().topLevelWidgets():
                    from src.utils.logger import info
                    widget_type = type(widget).__name__
                    info(f"发现顶级窗口: {widget_type}")
                    # 检查是否是主窗口
                    if 'Main' in widget_type or 'App' in widget_type or hasattr(widget, 'tabManager'):
                        info(f"发现可能的主窗口: {widget_type}")
                        main_window = widget
                        break
            except Exception as e:
                from src.utils.logger import warning
                warning(f"尝试查找主窗口失败: {str(e)}")
            
            if main_window is None:
                return None
        
        from src.utils.logger import info, warning
        text = None
        
        # 记录对象属性以帮助调试
        info(f"主窗口类型: {type(main_window).__name__}")
        
        # MGit专用方法，最高优先级
        # 通过Main Window的getCurrentMarkdownContent方法直接获取内容（如果存在）
        if hasattr(main_window, 'getCurrentMarkdownContent') and callable(main_window.getCurrentMarkdownContent):
            try:
                content = main_window.getCurrentMarkdownContent()
                if content:
                    info("通过getCurrentMarkdownContent方法获取到当前Markdown内容")
                    return content
            except Exception as e:
                warning(f"通过getCurrentMarkdownContent方法获取内容失败: {str(e)}")
        
        # MGit专用方法：从tabManager获取当前文档
        if hasattr(main_window, 'tabManager'):
            tab_manager = main_window.tabManager
            info(f"找到tabManager: {type(tab_manager).__name__}")
            
            # 尝试从tabManager获取当前标签和内容
            if hasattr(tab_manager, 'currentWidget') and callable(tab_manager.currentWidget):
                current_tab = tab_manager.currentWidget()
                if current_tab:
                    info(f"找到currentTab: {type(current_tab).__name__}")
                    
                    # 如果标签是编辑器
                    if hasattr(current_tab, 'toPlainText') and callable(current_tab.toPlainText):
                        text = current_tab.toPlainText()
                        info("通过tabManager.currentWidget.toPlainText获取编辑器内容成功")
                        return text
                    
                    # 如果标签有editor属性
                    if hasattr(current_tab, 'editor'):
                        editor = current_tab.editor
                        if editor and hasattr(editor, 'toPlainText'):
                            text = editor.toPlainText()
                            info("通过tabManager.currentWidget.editor.toPlainText获取编辑器内容成功")
                            return text
                    
                    # 检查标签是否有contentChanged信号（MGit文档标签的特征）
                    if hasattr(current_tab, 'contentChanged'):
                        info("检测到当前标签有contentChanged信号，这可能是一个MGit文档标签")
                        # 尝试找到编辑器组件
                        if hasattr(current_tab, 'findChild'):
                            from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                            # 尝试查找文本编辑器组件
                            text_edit = current_tab.findChild(QTextEdit)
                            if text_edit:
                                text = text_edit.toPlainText()
                                info("在当前标签中找到QTextEdit并获取内容成功")
                                return text
                            
                            plain_text_edit = current_tab.findChild(QPlainTextEdit)
                            if plain_text_edit:
                                text = plain_text_edit.toPlainText()
                                info("在当前标签中找到QPlainTextEdit并获取内容成功")
                                return text
                    
                    # 尝试查找子部件
                    if hasattr(current_tab, 'findChild'):
                        from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                        # 尝试查找子部件
                        text_edit = current_tab.findChild(QTextEdit)
                        if text_edit:
                            text = text_edit.toPlainText()
                            info("在当前标签中找到QTextEdit并获取内容成功")
                            return text
                        
                        plain_text_edit = current_tab.findChild(QPlainTextEdit)
                        if plain_text_edit:
                            text = plain_text_edit.toPlainText()
                            info("在当前标签中找到QPlainTextEdit并获取内容成功")
                            return text
            
            # 尝试从当前文档管理器获取内容
            if hasattr(tab_manager, 'getCurrentDocument') and callable(tab_manager.getCurrentDocument):
                doc = tab_manager.getCurrentDocument()
                if doc:
                    info(f"找到currentDocument: {type(doc).__name__}")
                    # 尝试访问文档的内容
                    if hasattr(doc, 'content'):
                        text = doc.content
                        info("通过tabManager.getCurrentDocument.content获取内容成功")
                        return text
                    # 尝试访问文档的getText方法
                    if hasattr(doc, 'getText') and callable(doc.getText):
                        text = doc.getText()
                        info("通过tabManager.getCurrentDocument.getText获取内容成功")
                        return text
                    # 尝试访问文档的文件路径
                    if hasattr(doc, 'filePath') and doc.filePath and os.path.exists(doc.filePath):
                        try:
                            with open(doc.filePath, 'r', encoding='utf-8') as f:
                                text = f.read()
                            info(f"通过读取文档的文件路径获取内容成功: {doc.filePath}")
                            return text
                        except Exception as e:
                            warning(f"通过文档文件路径读取内容失败: {str(e)}")
        
        # MGit专用：检查文档面板系统（documentPanel）
        if hasattr(main_window, 'documentPanel'):
            doc_panel = main_window.documentPanel
            info(f"找到documentPanel: {type(doc_panel).__name__}")
            
            # 尝试获取当前文档
            if hasattr(doc_panel, 'currentDocument') and callable(doc_panel.currentDocument):
                doc = doc_panel.currentDocument()
                if doc:
                    info(f"找到documentPanel.currentDocument: {type(doc).__name__}")
                    # 尝试获取文档内容
                    if hasattr(doc, 'content'):
                        text = doc.content
                        info("通过documentPanel.currentDocument.content获取内容成功")
                        return text
                    # 尝试通过getText方法获取
                    if hasattr(doc, 'getText') and callable(doc.getText):
                        text = doc.getText()
                        info("通过documentPanel.currentDocument.getText获取内容成功")
                        return text
                    # 尝试通过文件路径读取
                    if hasattr(doc, 'filePath') and doc.filePath and os.path.exists(doc.filePath):
                        try:
                            with open(doc.filePath, 'r', encoding='utf-8') as f:
                                text = f.read()
                            info(f"通过documentPanel.currentDocument.filePath读取内容成功: {doc.filePath}")
                            return text
                        except Exception as e:
                            warning(f"通过documentPanel文件路径读取内容失败: {str(e)}")
        
        # 尝试从当前活动标签获取内容（通用）
        if hasattr(main_window, 'currentTabWidget') and callable(main_window.currentTabWidget):
            tab_widget = main_window.currentTabWidget()
            if tab_widget:
                info(f"获取到currentTabWidget: {type(tab_widget).__name__}")
                # 如果标签是文本编辑器
                if hasattr(tab_widget, 'toPlainText') and callable(tab_widget.toPlainText):
                    text = tab_widget.toPlainText()
                    info("通过currentTabWidget.toPlainText获取编辑器内容成功")
                    return text
                # 如果标签有编辑器属性
                elif hasattr(tab_widget, 'editor'):
                    if tab_widget.editor and hasattr(tab_widget.editor, 'toPlainText'):
                        text = tab_widget.editor.toPlainText()
                        info("通过currentTabWidget.editor.toPlainText获取编辑器内容成功")
                        return text
        
        # 方法1：通过editor属性
        if hasattr(main_window, 'editor') and main_window.editor:
            if hasattr(main_window.editor, 'toPlainText') and callable(main_window.editor.toPlainText):
                text = main_window.editor.toPlainText()
                info("通过editor属性获取编辑器内容成功")
                return text
        
        # 方法2：通过getCurrentEditor方法
        if hasattr(main_window, 'getCurrentEditor') and callable(main_window.getCurrentEditor):
            editor = main_window.getCurrentEditor()
            if editor and hasattr(editor, 'toPlainText') and callable(editor.toPlainText):
                text = editor.toPlainText()
                info("通过getCurrentEditor方法获取编辑器内容成功")
                return text
        
        # 方法3：通过active_editor属性
        if hasattr(main_window, 'active_editor') and main_window.active_editor:
            if hasattr(main_window.active_editor, 'toPlainText') and callable(main_window.active_editor.toPlainText):
                text = main_window.active_editor.toPlainText()
                info("通过active_editor属性获取编辑器内容成功")
                return text
        
        # 方法4：通过editor_manager
        if hasattr(main_window, 'editor_manager') and main_window.editor_manager:
            info("找到editor_manager")
            if hasattr(main_window.editor_manager, 'active_editor') and main_window.editor_manager.active_editor:
                if hasattr(main_window.editor_manager.active_editor, 'toPlainText') and callable(main_window.editor_manager.active_editor.toPlainText):
                    text = main_window.editor_manager.active_editor.toPlainText()
                    info("通过editor_manager.active_editor获取编辑器内容成功")
                    return text
            if hasattr(main_window.editor_manager, 'getCurrentEditor') and callable(main_window.editor_manager.getCurrentEditor):
                editor = main_window.editor_manager.getCurrentEditor()
                if editor and hasattr(editor, 'toPlainText') and callable(editor.toPlainText):
                    text = editor.toPlainText()
                    info("通过editor_manager.getCurrentEditor获取编辑器内容成功")
                    return text
            if hasattr(main_window.editor_manager, 'currentEditor') and callable(main_window.editor_manager.currentEditor):
                editor = main_window.editor_manager.currentEditor()
                if editor and hasattr(editor, 'toPlainText') and callable(editor.toPlainText):
                    text = editor.toPlainText()
                    info("通过editor_manager.currentEditor获取编辑器内容成功")
                    return text
        
        # 方法5：通过document_manager
        if hasattr(main_window, 'document_manager') and main_window.document_manager:
            info("找到document_manager")
            if hasattr(main_window.document_manager, 'current_document') and main_window.document_manager.current_document:
                doc = main_window.document_manager.current_document
                if hasattr(doc, 'content'):
                    text = doc.content
                    info("通过document_manager.current_document.content获取编辑器内容成功")
                    return text
                if hasattr(doc, 'getText') and callable(doc.getText):
                    text = doc.getText()
                    info("通过document_manager.current_document.getText获取编辑器内容成功")
                    return text
                if hasattr(doc, 'editor') and doc.editor:
                    if hasattr(doc.editor, 'toPlainText') and callable(doc.editor.toPlainText):
                        text = doc.editor.toPlainText()
                        info("通过document_manager.current_document.editor.toPlainText获取编辑器内容成功")
                        return text
        
        # 方法6：通过中央widget
        if hasattr(main_window, 'centralWidget') and callable(main_window.centralWidget):
            central = main_window.centralWidget()
            if central:
                info(f"找到centralWidget: {type(central).__name__}")
                # 尝试通过中央widget查找当前tab
                if hasattr(central, 'currentWidget') and callable(central.currentWidget):
                    current = central.currentWidget()
                    if current:
                        info(f"找到currentWidget: {type(current).__name__}")
                        # 尝试从当前widget获取文本
                        if hasattr(current, 'toPlainText') and callable(current.toPlainText):
                            text = current.toPlainText()
                            info("通过centralWidget.currentWidget.toPlainText获取编辑器内容成功")
                            return text
                        # 如果当前widget是容器，尝试递归查找文本编辑器
                        if hasattr(current, 'findChild'):
                            from PyQt5.QtWidgets import QTextEdit, QPlainTextEdit
                            text_edit = current.findChild(QTextEdit)
                            if text_edit:
                                text = text_edit.toPlainText()
                                info("通过findChild(QTextEdit)获取编辑器内容成功")
                                return text
                            plain_text_edit = current.findChild(QPlainTextEdit)
                            if plain_text_edit:
                                text = plain_text_edit.toPlainText()
                                info("通过findChild(QPlainTextEdit)获取编辑器内容成功")
                                return text
        
        # 方法7：MGit特定方法 - 通过currentFilePath获取文件内容
        if hasattr(main_window, 'currentFilePath') and callable(main_window.currentFilePath):
            file_path = main_window.currentFilePath()
            if file_path and os.path.exists(file_path):
                info(f"找到当前文件路径: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    info("通过文件路径读取内容成功")
                    return text
                except Exception as e:
                    warning(f"通过文件路径读取内容失败: {str(e)}")
        
        # 方法8：如果主窗口是QMainWindow，尝试通过其菜单栏找到文件操作
        if hasattr(main_window, 'menuBar') and callable(main_window.menuBar):
            menu_bar = main_window.menuBar()
            if menu_bar:
                info("找到menuBar")
                # 打印所有菜单项，用于调试
                if hasattr(menu_bar, 'actions'):
                    actions = menu_bar.actions()
                    for action in actions:
                        if action.text() == "文件" or action.text() == "File":
                            file_menu = action.menu()
                            if file_menu:
                                info("找到文件菜单")
                                for file_action in file_menu.actions():
                                    info(f"文件菜单项: {file_action.text()}")
        
        # 如果最终无法获取编辑器内容，输出更多调试信息
        warning("无法通过任何方式获取当前编辑器内容")
        debug_info = "主窗口属性: "
        for attr in dir(main_window):
            if not attr.startswith('__'):
                try:
                    value = getattr(main_window, attr)
                    if callable(value):
                        debug_info += f"{attr}(函数), "
                    else:
                        debug_info += f"{attr}, "
                except:
                    debug_info += f"{attr}(无法获取), "
        info(debug_info)
        
        return text