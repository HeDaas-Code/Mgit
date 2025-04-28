#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import markdown
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from qfluentwidgets import Theme, isDarkTheme

class MarkdownPreview(QWidget):
    """ Markdown预览组件 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        """ 初始化UI """
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建预览视图
        self.webView = QWebEngineView()
        self.webView.setContextMenuPolicy(Qt.NoContextMenu)  # 禁用右键菜单
        
        # 设置初始内容
        self.setMarkdown("")
        
        # 添加到布局
        layout.addWidget(self.webView)
        
    def setMarkdown(self, text):
        """ 设置Markdown内容并渲染 """
        # 转换Markdown为HTML
        html_content = self.convertMarkdownToHtml(text)
        
        # 获取样式
        style = self.getPreviewStyle()
        
        # 组合完整的HTML文档
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                {style}
            </style>
        </head>
        <body>
            <div class="markdown-body">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        # 显示HTML
        self.webView.setHtml(full_html)
        
    def convertMarkdownToHtml(self, text):
        """ 将Markdown文本转换为HTML """
        # 定义Markdown扩展
        extensions = [
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.attr_list',
            'markdown.extensions.def_list',
            'markdown.extensions.abbr',
            'markdown.extensions.footnotes',
            'markdown.extensions.md_in_html'
        ]
        
        # 转换并返回
        html = markdown.markdown(text, extensions=extensions)
        return html
        
    def getPreviewStyle(self):
        """ 获取预览样式 """
        # 总是使用浅色主题，忽略系统设置
        is_dark = False
        
        # 基础样式
        base_style = """
        .markdown-body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            word-wrap: break-word;
            padding: 16px;
        }
        
        .markdown-body a:hover {
            text-decoration: underline;
        }
        
        .markdown-body h1, .markdown-body h2 {
            padding-bottom: 0.3em;
        }
        
        .markdown-body h1 {
            font-size: 2em;
        }
        
        .markdown-body h2 {
            font-size: 1.5em;
        }
        
        .markdown-body h3 {
            font-size: 1.25em;
        }
        
        .markdown-body h4 {
            font-size: 1em;
        }
        
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
            border-radius: 3px;
        }
        
        .markdown-body code {
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
        }
        
        .markdown-body pre > code {
            padding: 0;
            margin: 0;
            font-size: 100%;
            word-break: normal;
            white-space: pre;
            background: transparent;
            border: 0;
        }
        
        .markdown-body blockquote {
            padding: 0 1em;
            margin: 0 0 16px 0;
        }
        
        .markdown-body table {
            display: block;
            width: 100%;
            overflow: auto;
            border-spacing: 0;
            border-collapse: collapse;
        }
        
        .markdown-body table th {
            font-weight: 600;
        }
        
        .markdown-body table th, .markdown-body table td {
            padding: 6px 13px;
        }
        
        .markdown-body table tr {
            border-top: 1px solid;
        }
        
        .markdown-body img {
            max-width: 100%;
            box-sizing: content-box;
        }
        
        .markdown-body ul, .markdown-body ol {
            padding-left: 2em;
        }
        
        .markdown-body li+li {
            margin-top: 0.25em;
        }
        """
        
        # 样式 - 无论是否深色模式，都使用相同的亮色样式
        style = """
        .markdown-body {
            color: #000000;
            background-color: #ffffff;
        }
        
        .markdown-body a {
            color: #0366d6;
            text-decoration: none;
        }
        
        .markdown-body h1, .markdown-body h2 {
            border-bottom: 1px solid #eaecef;
        }
        
        .markdown-body pre {
            background-color: #f6f8fa;
        }
        
        .markdown-body code {
            background-color: rgba(27,31,35,0.05);
            color: #24292e;
        }
        
        .markdown-body blockquote {
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
        }
        
        .markdown-body table th, .markdown-body table td {
            border: 1px solid #dfe2e5;
        }
        
        .markdown-body table tr {
            background-color: #fff;
        }
        
        .markdown-body table tr:nth-child(2n) {
            background-color: #f6f8fa;
        }
        
        .markdown-body img {
            background-color: #fff;
        }
        """
        
        return base_style + style 