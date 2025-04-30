#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import FluentIcon, IconWidget, TransparentToolButton

class StatusBar(QWidget):
    """ 状态栏组件 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.current_file = ""
        self.current_repo = ""
        
    def initUI(self):
        """ 初始化UI """
        # 设置布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 创建文件信息标签
        self.fileLabel = QLabel("文件: 无")
        
        # 创建仓库信息标签
        self.repoLabel = QLabel("仓库: 无")
        
        # 创建分支信息标签
        self.branchLabel = QLabel("分支: 无")
        
        # 创建Git同步按钮
        self.syncBtn = TransparentToolButton(FluentIcon.SYNC)
        self.syncBtn.setToolTip("同步Git仓库")
        self.syncBtn.setFixedSize(16, 16)
        self.syncBtn.clicked.connect(self.onSyncClicked)
        
        # 添加小部件到布局
        layout.addWidget(self.fileLabel)
        layout.addStretch(1)
        layout.addWidget(self.repoLabel)
        layout.addWidget(self.branchLabel)
        layout.addWidget(self.syncBtn)
        
        # 设置固定高度
        self.setFixedHeight(30)
        
        # 设置默认样式 (浅色主题)
        self.updateTheme(is_dark_mode=False)
        
    def updateTheme(self, is_dark_mode=False):
        """ 根据主题更新样式 """
        if is_dark_mode:
            self.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                }
                
                StatusBar {
                    background-color: #3b3b3b;
                    border-top: 1px solid #4b5b6c;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 12px;
                }
                
                StatusBar {
                    background-color: #F5F5F5;
                    border-top: 1px solid #E0E0E0;
                }
            """)
        
    def setCurrentFile(self, file_path):
        """ 设置当前文件信息 """
        self.current_file = file_path if file_path else ""
        if file_path:
            file_name = os.path.basename(file_path)
            self.fileLabel.setText(f"文件: {file_name}")
        else:
            self.fileLabel.setText("文件: 无")
            
    def getCurrentFile(self):
        """ 获取当前文件路径 """
        return self.current_file
            
    def setCurrentRepository(self, repo_path):
        """ 设置当前仓库信息 """
        self.current_repo = repo_path if repo_path else ""
        if repo_path:
            repo_name = os.path.basename(repo_path)
            self.repoLabel.setText(f"仓库: {repo_name}")
            
            # 获取Git分支信息
            try:
                from src.utils.git_manager import GitManager
                git_manager = GitManager(repo_path)
                branch = git_manager.getCurrentBranch()
                self.branchLabel.setText(f"分支: {branch}")
                self.syncBtn.setEnabled(True)
            except:
                self.branchLabel.setText("分支: 无")
                self.syncBtn.setEnabled(False)
        else:
            self.repoLabel.setText("仓库: 无")
            self.branchLabel.setText("分支: 无")
            self.syncBtn.setEnabled(False)
            
    def getCurrentRepository(self):
        """ 获取当前仓库路径 """
        return self.current_repo
            
    def onSyncClicked(self):
        """ 处理同步按钮点击事件 """
        # 通知主窗口同步Git仓库
        # 注意：这里只是一个示例，实际应用中需要与主窗口连接
        parent = self.parent()
        if hasattr(parent, 'gitPanel') and parent.gitPanel:
            parent.gitPanel.refreshStatus() 