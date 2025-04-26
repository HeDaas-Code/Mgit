#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import threading
import time
import git
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                          QLabel, QLineEdit, QComboBox, QProgressBar,
                          QListWidget, QListWidgetItem, QMessageBox, QMenu,
                          QAction, QSplitter, QDialog, QFormLayout, QCheckBox, QFileDialog,
                          QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QCursor, QFont
from qfluentwidgets import (PrimaryPushButton, TransparentToolButton, ToolButton, 
                           FluentIcon, ComboBox, InfoBar, InfoBarPosition, 
                           LineEdit, TitleLabel, CardWidget)

from src.utils.enhanced_account_manager import EnhancedAccountManager
from src.utils.git_manager import GitManager
from src.utils.git_thread import GitThread
from src.utils.config_manager import ConfigManager
from src.utils.logger import info, warning, error, debug
from src.components.loading_mask import LoadingMask
from src.components.account_panel import AccountPanel

class GitPanel(QWidget):
    """ Git面板组件 """
    
    # 信号
    repositoryInitialized = pyqtSignal(str)
    repositoryOpened = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gitManager = None
        self.currentPath = ""
        self.configManager = ConfigManager()
        self.recentReposList = []
        
        # 创建Git线程
        self.gitThread = GitThread(self)
        self.gitThread.operationStarted.connect(self.onGitOperationStarted)
        self.gitThread.operationFinished.connect(self.onGitOperationFinished)
        self.gitThread.progressUpdate.connect(self.onGitProgressUpdate)
        
        # 创建账号管理器实例（放在这里以确保所有地方使用同一个实例）
        self.accountManager = EnhancedAccountManager()
        
        # 初始化UI
        self.initUI()
        
        # 创建加载遮罩 - 在UI初始化之后创建，确保正确的父子关系和Z顺序
        self.loadingMask = LoadingMask(self)
        
        # 初始加载最近仓库列表
        self.updateRecentRepositories()
        
        # 禁用一些初始按钮
        self.commitBtn.setEnabled(False)
        self.pushBtn.setEnabled(False)
        self.pullBtn.setEnabled(False)
        self.stashBtn.setEnabled(False)
        self.branchBtn.setEnabled(False)
        self.remoteBtn.setEnabled(False)
        self.branchCombo.setEnabled(False)
        self.syncBtn.setEnabled(False)
        
    def initUI(self):
        """ 初始化UI """
        # 设置布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 添加账号面板（新增）
        # 传递accountManager确保使用同一个账号管理器实例
        self.accountPanel = AccountPanel(self, account_manager=self.accountManager)
        self.accountPanel.accountChanged.connect(self.onAccountChanged)
        layout.addWidget(self.accountPanel)
        
        # 标题卡片
        titleCard = CardWidget(self)
        titleCardLayout = QVBoxLayout(titleCard)
        titleCardLayout.setContentsMargins(10, 5, 10, 5)
        titleCardLayout.setSpacing(0)
        
        # 标题区域
        titleBarLayout = QHBoxLayout()
        titleBarLayout.setContentsMargins(0, 0, 0, 0)
        
        self.titleLabel = TitleLabel("Git操作")
        titleBarLayout.addWidget(self.titleLabel)
        
        # 添加打开仓库按钮
        self.openBtn = TransparentToolButton(FluentIcon.FOLDER)
        self.openBtn.setToolTip("打开仓库")
        self.openBtn.clicked.connect(self.openRepository)
        titleBarLayout.addWidget(self.openBtn)
        
        # 添加初始化仓库按钮
        self.initRepoBtn = TransparentToolButton(FluentIcon.ADD)
        self.initRepoBtn.setToolTip("创建仓库")
        self.initRepoBtn.clicked.connect(self.initializeRepository)
        titleBarLayout.addWidget(self.initRepoBtn)
        
        # 添加刷新按钮
        self.refreshBtn = TransparentToolButton(FluentIcon.SYNC)
        self.refreshBtn.setToolTip("刷新状态")
        self.refreshBtn.clicked.connect(self.refreshStatus)
        titleBarLayout.addWidget(self.refreshBtn)
        
        titleCardLayout.addLayout(titleBarLayout)
        
        # 状态显示
        self.statusLabel = QLabel("未连接到任何Git仓库")
        titleCardLayout.addWidget(self.statusLabel)
        
        # 最近仓库下拉框
        recentRepoLayout = QHBoxLayout()
        recentRepoLayout.setContentsMargins(0, 5, 0, 0)
        
        recentRepoLabel = QLabel("最近仓库:")
        recentRepoLayout.addWidget(recentRepoLabel)
        
        self.recentRepoCombo = ComboBox()
        self.recentRepoCombo.setPlaceholderText("选择最近打开的仓库")
        self.recentRepoCombo.setMinimumWidth(200)
        self.recentRepoCombo.currentIndexChanged.connect(self.onRecentRepoSelected)
        recentRepoLayout.addWidget(self.recentRepoCombo)
        
        titleCardLayout.addLayout(recentRepoLayout)
        
        # 分支与远程操作区域
        branchRemoteLayout = QHBoxLayout()
        branchRemoteLayout.setContentsMargins(0, 5, 0, 0)
        
        # 分支选择下拉框
        self.branchCombo = ComboBox()
        self.branchCombo.setPlaceholderText("当前分支")
        self.branchCombo.currentIndexChanged.connect(self.onBranchSelected)
        branchRemoteLayout.addWidget(self.branchCombo)
        
        # 分支操作按钮
        self.branchBtn = TransparentToolButton(FluentIcon.MENU)
        self.branchBtn.setToolTip("分支操作")
        self.branchBtn.clicked.connect(self.showBranchMenu)
        branchRemoteLayout.addWidget(self.branchBtn)
        
        # 远程操作按钮
        self.remoteBtn = TransparentToolButton(FluentIcon.LINK)
        self.remoteBtn.setToolTip("远程仓库操作")
        self.remoteBtn.clicked.connect(self.showRemoteMenu)
        branchRemoteLayout.addWidget(self.remoteBtn)
        
        titleCardLayout.addLayout(branchRemoteLayout)
        
        # 添加组件到布局
        layout.addWidget(titleCard)
        
        # 外部仓库卡片（新增）
        externalCard = CardWidget(self)
        externalCardLayout = QVBoxLayout(externalCard)
        externalCardLayout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        externalCardLayout.addWidget(QLabel("外部仓库操作"))
        
        # 按钮布局
        externalBtnLayout = QHBoxLayout()
        
        # 克隆远程仓库按钮
        self.cloneBtn = PrimaryPushButton("克隆远程仓库")
        self.cloneBtn.setIcon(FluentIcon.COPY.icon())
        self.cloneBtn.clicked.connect(self.cloneExternalRepo)
        externalBtnLayout.addWidget(self.cloneBtn)
        
        # 从GitHub导入按钮
        self.importGitHubBtn = PrimaryPushButton("从GitHub导入")
        self.importGitHubBtn.setIcon(FluentIcon.LINK.icon())
        self.importGitHubBtn.clicked.connect(self.importFromGitHub)
        externalBtnLayout.addWidget(self.importGitHubBtn)
        
        externalCardLayout.addLayout(externalBtnLayout)
        
        # 同步按钮
        self.syncBtn = PrimaryPushButton("同步远程仓库")
        self.syncBtn.setIcon(FluentIcon.SYNC.icon())
        self.syncBtn.clicked.connect(self.syncWithRemote)
        self.syncBtn.setEnabled(False)
        externalCardLayout.addWidget(self.syncBtn)
        
        layout.addWidget(externalCard)
        
        # 操作区卡片
        operationCard = CardWidget(self)
        operationCardLayout = QVBoxLayout(operationCard)
        operationCardLayout.setContentsMargins(10, 10, 10, 10)
        
        # 提交信息输入框
        operationCardLayout.addWidget(QLabel("提交信息:"))
        self.commitMsgEdit = LineEdit()
        self.commitMsgEdit.setPlaceholderText("输入提交信息...")
        operationCardLayout.addWidget(self.commitMsgEdit)
        
        # 变更文件列表
        operationCardLayout.addWidget(QLabel("变更文件:"))
        
        self.changesList = QListWidget()
        self.changesList.setSelectionMode(QListWidget.ExtendedSelection)
        operationCardLayout.addWidget(self.changesList)
        
        # 操作按钮区域
        buttonLayout = QHBoxLayout()
        
        # 保存暂存
        self.stashBtn = ToolButton(FluentIcon.SAVE)
        self.stashBtn.setToolTip("创建/应用储藏")
        self.stashBtn.clicked.connect(self.showStashMenu)
        buttonLayout.addWidget(self.stashBtn)
        
        # 暂存变更按钮
        self.stageBtn = PrimaryPushButton("暂存所选")
        self.stageBtn.setIcon(FluentIcon.ADD.icon())
        self.stageBtn.clicked.connect(self.stageSelected)
        buttonLayout.addWidget(self.stageBtn)
        
        # 取消暂存按钮
        self.unstageBtn = PrimaryPushButton("取消暂存")
        self.unstageBtn.setIcon(FluentIcon.REMOVE.icon())
        self.unstageBtn.clicked.connect(self.unstageSelected)
        buttonLayout.addWidget(self.unstageBtn)
        
        # 丢弃变更按钮
        self.discardBtn = PrimaryPushButton("丢弃所选")
        self.discardBtn.setIcon(FluentIcon.DELETE.icon())
        self.discardBtn.clicked.connect(self.discardSelected)
        buttonLayout.addWidget(self.discardBtn)
        
        operationCardLayout.addLayout(buttonLayout)
        
        # 提交按钮
        self.commitBtn = PrimaryPushButton("提交变更")
        self.commitBtn.setIcon(FluentIcon.ACCEPT.icon())
        self.commitBtn.clicked.connect(self.commitChanges)
        operationCardLayout.addWidget(self.commitBtn)
        
        # 拉取和推送按钮区域
        pullPushLayout = QHBoxLayout()
        
        # 拉取按钮
        self.pullBtn = PrimaryPushButton("拉取")
        self.pullBtn.setIcon(FluentIcon.DOWN.icon())
        self.pullBtn.clicked.connect(self.pullChanges)
        pullPushLayout.addWidget(self.pullBtn)
        
        # 推送按钮
        self.pushBtn = PrimaryPushButton("推送")
        self.pushBtn.setIcon(FluentIcon.UP.icon())
        self.pushBtn.clicked.connect(self.pushChanges)
        pullPushLayout.addWidget(self.pushBtn)
        
        operationCardLayout.addLayout(pullPushLayout)
        
        # 添加操作卡片到主布局
        layout.addWidget(operationCard)
        
    def onAccountChanged(self, account):
        """账号变更处理函数"""
        info(f"账号变更: {account}")
        
        # 根据账号状态更新界面元素
        if account:
            # 启用与远程相关的按钮
            self.importGitHubBtn.setEnabled(True)
            
            # 如果当前已连接到仓库，启用推送和拉取
            if self.gitManager and self.gitManager.isValidRepo():
                # 检查当前远程仓库，如果需要可以更新远程仓库设置
                self.refreshStatus()
                
                # 如果推送按钮原本是启用的，保持启用
                if self.pushBtn.isEnabled():
                    self.syncBtn.setEnabled(True)
        else:
            # 禁用与远程账号相关的操作
            # 但保持本地Git操作可用
            pass
        
    def stageSelected(self):
        """暂存选中的文件"""
        if not self.gitManager:
            return
            
        selected_items = self.changesList.selectedItems()
        if not selected_items:
            InfoBar.warning(
                title="未选择文件",
                content="请选择要暂存的文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        files_to_stage = []
        for item in selected_items:
            # 获取文件路径
            file_status, file_path = item.data(Qt.UserRole)
            
            # 只暂存未跟踪或已修改的文件
            if file_status in ["未跟踪", "已修改", "已删除"]:
                files_to_stage.append(file_path)
                
        if files_to_stage:
            try:
                self.gitManager.stage(files_to_stage)
                self.refreshStatus()
                
                InfoBar.success(
                    title="暂存成功",
                    content=f"已暂存 {len(files_to_stage)} 个文件",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                error(f"暂存文件失败: {str(e)}")
                QMessageBox.warning(self, "暂存失败", f"暂存文件时出错: {str(e)}")
                
    def unstageSelected(self):
        """取消暂存选中的文件"""
        if not self.gitManager:
            return
            
        selected_items = self.changesList.selectedItems()
        if not selected_items:
            InfoBar.warning(
                title="未选择文件",
                content="请选择要取消暂存的文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        files_to_unstage = []
        for item in selected_items:
            # 获取文件路径
            file_status, file_path = item.data(Qt.UserRole)
            
            # 只取消暂存已暂存的文件
            if "已暂存" in file_status:
                files_to_unstage.append(file_path)
                
        if files_to_unstage:
            try:
                self.gitManager.unstage(files_to_unstage)
                self.refreshStatus()
                
                InfoBar.success(
                    title="取消暂存成功",
                    content=f"已取消暂存 {len(files_to_unstage)} 个文件",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                error(f"取消暂存文件失败: {str(e)}")
                QMessageBox.warning(self, "取消暂存失败", f"取消暂存文件时出错: {str(e)}")
                
    def discardSelected(self):
        """丢弃选中文件的变更"""
        if not self.gitManager:
            return
            
        selected_items = self.changesList.selectedItems()
        if not selected_items:
            InfoBar.warning(
                title="未选择文件",
                content="请选择要丢弃变更的文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 确认丢弃变更
        reply = QMessageBox.warning(
            self,
            "丢弃变更",
            "确定要丢弃所选文件的变更吗？此操作无法撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        files_to_discard = []
        for item in selected_items:
            # 获取文件路径
            file_status, file_path = item.data(Qt.UserRole)
            files_to_discard.append(file_path)
            
        if files_to_discard:
            try:
                # 先取消暂存，再丢弃变更
                self.gitManager.unstage(files_to_discard)
                self.gitManager.discard(files_to_discard)
                self.refreshStatus()
                
                InfoBar.success(
                    title="丢弃变更成功",
                    content=f"已丢弃 {len(files_to_discard)} 个文件的变更",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                error(f"丢弃变更失败: {str(e)}")
                QMessageBox.warning(self, "丢弃变更失败", f"丢弃变更时出错: {str(e)}")
                
    def resizeEvent(self, event):
        """处理窗口大小变更事件"""
        super().resizeEvent(event)
        
        # 更新加载遮罩的位置和大小
        if hasattr(self, 'loadingMask'):
            self.loadingMask.resize(self.size())
        
    def updateRecentRepositories(self):
        """ 更新最近仓库下拉框 """
        # 保存当前选中的索引
        currentIndex = self.recentRepoCombo.currentIndex()
        
        # 暂时阻断信号以防止循环
        self.recentRepoCombo.blockSignals(True)
        
        try:
            # 清空下拉框
            self.recentRepoCombo.clear()
            self.recentRepoCombo.addItem("选择最近仓库...")
            
            # 重新获取最新的仓库列表（不使用缓存）
            self.recentReposList = self.configManager.get_recent_repositories()
            for repo in self.recentReposList:
                repoName = os.path.basename(repo)
                self.recentRepoCombo.addItem(f"{repoName} ({repo})")
            
            # 如果先前有选择，尝试恢复选中状态
            if currentIndex > 0 and currentIndex <= len(self.recentReposList):
                self.recentRepoCombo.setCurrentIndex(currentIndex)
            else:
                self.recentRepoCombo.setCurrentIndex(0)
        finally:
            # 确保信号一定会被重新启用
            self.recentRepoCombo.blockSignals(False)
    
    def onRecentRepoSelected(self, index):
        """ 处理选择最近仓库 """
        if index <= 0:
            return
            
        # 使用临时变量存储当前索引，避免在更新过程中触发更多事件
        selectedIndex = index
        
        # 先重置下拉框状态，阻断可能的事件循环
        self.recentRepoCombo.blockSignals(True)
        self.recentRepoCombo.setCurrentIndex(0)
        self.recentRepoCombo.blockSignals(False)
            
        # 使用索引从列表中获取仓库路径
        if 0 < selectedIndex <= len(self.recentReposList):
            repoPath = self.recentReposList[selectedIndex-1]
            if repoPath and os.path.exists(repoPath):
                try:
                    self.setRepository(repoPath)
                    # 发送信号前临时阻断更新
                    self.repositoryOpened.emit(repoPath)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            else:
                InfoBar.warning(
                    title="无效仓库路径",
                    content=f"路径 '{repoPath}' 不存在或无效",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        
    def openRepository(self):
        """ 打开仓库 """
        repoPath = QFileDialog.getExistingDirectory(
            self, "选择Git仓库", ""
        )
        if repoPath:
            try:
                self.setRepository(repoPath)
                self.repositoryOpened.emit(repoPath)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            
    def setRepository(self, path):
        """ 设置Git仓库路径 """
        if not path or not os.path.exists(path):
            return
            
        try:
            self.gitManager = GitManager(path)
            if self.gitManager.isValidRepo():
                self.statusLabel.setText(f"当前仓库: {os.path.basename(path)}")
                
                # 检查是否有远程仓库，根据结果启用或禁用相关按钮
                remotes = self.gitManager.getRemotes()
                has_remotes = len(remotes) > 0
                
                # 始终启用的按钮
                self.commitBtn.setEnabled(True)
                self.branchBtn.setEnabled(True)
                self.remoteBtn.setEnabled(True)
                self.branchCombo.setEnabled(True)
                self.stashBtn.setEnabled(True)
                
                # 只有当存在远程仓库时才启用的按钮
                self.pushBtn.setEnabled(has_remotes)
                self.pullBtn.setEnabled(has_remotes)
                self.syncBtn.setEnabled(has_remotes)
                
                # 如果没有远程仓库，显示提示信息
                if not has_remotes:
                    InfoBar.info(
                        title="没有远程仓库",
                        content="当前仓库没有配置远程仓库，部分功能将被禁用",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                
                self.refreshStatus()
                
                # 更新最近仓库列表
                self.updateRecentRepositories()
            else:
                self.statusLabel.setText("无效的Git仓库")
                self.gitManager = None
                self.commitBtn.setEnabled(False)
                self.pushBtn.setEnabled(False)
                self.pullBtn.setEnabled(False)
                self.stashBtn.setEnabled(False)
                self.branchBtn.setEnabled(False)
                self.remoteBtn.setEnabled(False)
                self.branchCombo.setEnabled(False)
                self.syncBtn.setEnabled(False)
                
                InfoBar.warning(
                    title="无效仓库",
                    content="所选路径不是有效的Git仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开仓库失败: {str(e)}")
            self.gitManager = None
            self.commitBtn.setEnabled(False)
            self.pushBtn.setEnabled(False)
            self.pullBtn.setEnabled(False)
            self.stashBtn.setEnabled(False)
            self.branchBtn.setEnabled(False)
            self.remoteBtn.setEnabled(False)
            self.branchCombo.setEnabled(False)
            
    def initializeRepository(self):
        """ 初始化新仓库 """
        # 选择目录
        repoPath = QFileDialog.getExistingDirectory(
            self, "选择创建仓库的位置", ""
        )
        
        if not repoPath:
            return
            
        # 确保路径是绝对路径
        repoPath = os.path.abspath(repoPath)
        info(f"GitPanel - 选择的仓库位置: {repoPath}")
            
        # 输入仓库名称
        repoName, ok = QInputDialog.getText(
            self, "创建仓库", "请输入仓库名称:"
        )
        
        if not ok or not repoName:
            return
            
        info(f"GitPanel - 仓库名称: {repoName}")
            
        # 完整的仓库路径
        fullRepoPath = os.path.join(repoPath, repoName)
        fullRepoPath = os.path.abspath(fullRepoPath)
        info(f"GitPanel - 完整的仓库路径: {fullRepoPath}")
        
        # 检查路径是否已存在
        if os.path.exists(fullRepoPath) and os.listdir(fullRepoPath):
            reply = QMessageBox.question(
                self, "确认覆盖", 
                f"目录 {fullRepoPath} 已存在且不为空，是否继续？\n（不会删除现有文件，但会将此目录初始化为Git仓库）",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # 询问是否同时创建远程仓库
        createRemote = QMessageBox.question(
            self, "创建远程仓库",
            "是否同时在GitHub/GitLab上创建远程仓库？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes
        
        try:
            info(f"GitPanel - 开始初始化仓库: {fullRepoPath}")
            
            # 使用Git线程执行初始化操作
            self.gitThread.setup(
                operation='init',
                git_manager=None,  # 不再需要GitManager实例
                path=fullRepoPath,
                initial_branch="main"
            )
            self.gitThread.start()
            
            # 这个方法会在Git操作完成后在onGitOperationFinished中调用
            def on_init_finished(success, op, msg):
                if success:
                    info(f"GitPanel - 仓库初始化成功: {fullRepoPath}")
                    # 尝试打开新创建的仓库
                    try:
                        # 初始化成功，创建远程仓库（如果需要）
                        local_repo = git.Repo(fullRepoPath)
                        if createRemote:
                            self.createRemoteRepository(local_repo, fullRepoPath, repoName)
                        
                        # 设置为当前仓库
                        self.setRepository(fullRepoPath)
                        
                        # 发出信号通知其他组件
                        self.repositoryInitialized.emit(fullRepoPath)
                    except Exception as e:
                        error(f"GitPanel - 仓库创建成功但打开失败: {str(e)}")
                        QMessageBox.information(
                            self, 
                            "仓库创建成功", 
                            f"仓库已创建成功，但打开时出错: {str(e)}\n仓库路径: {fullRepoPath}"
                        )
                else:
                    error(f"GitPanel - 仓库初始化失败: {msg}")
                
                # 移除临时连接
                self.gitThread.operationFinished.disconnect(on_init_finished)
            
            # 临时连接，只处理一次初始化完成的回调
            self.gitThread.operationFinished.connect(on_init_finished)
            
        except Exception as e:
            error(f"GitPanel - 初始化仓库失败: {str(e)}, 路径: {fullRepoPath}")
            QMessageBox.critical(self, "错误", f"初始化仓库失败: {str(e)}")

    def createRemoteRepository(self, local_repo, repo_path, repo_name):
        """ 创建远程仓库并关联
        Args:
            local_repo: 本地仓库对象
            repo_path: 本地仓库路径
            repo_name: 仓库名称
        """
        # 使用类的账号管理器实例
        current_account = self.accountManager.get_current_account()
        
        # 调试输出当前账号信息
        debug(f"当前登录账号信息: {current_account}")
        
        # 如果存在当前登录的账号，直接使用该账号
        if current_account and isinstance(current_account, dict) and 'type' in current_account and 'data' in current_account:
            platform = current_account["type"]
            account_data = current_account["data"]
            
            debug(f"使用{platform}账号创建远程仓库，用户名: {account_data.get('username', '未知')}")
            
            # 询问是否创建为私有仓库
            is_private = QMessageBox.question(
                self, "仓库隐私设置",
                "是否创建为私有仓库？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            ) == QMessageBox.Yes
            
            try:
                remote_url = None
                if platform == "github":
                    # 创建GitHub远程仓库
                    token = account_data["token"]
                    username = account_data["username"]
                    
                    # GitHub API请求
                    import requests
                    headers = {"Authorization": f"token {token}"}
                    data = {
                        "name": repo_name,
                        "description": f"由MGit创建的仓库 - {repo_name}",
                        "private": is_private,
                        # 设置不创建任何初始文件：README, .gitignore等
                        "auto_init": False,
                        "gitignore_template": None,
                        "license_template": None
                    }
                    
                    response = requests.post(
                        "https://api.github.com/user/repos",
                        headers=headers,
                        json=data,
                        verify=False
                    )
                    
                    if response.status_code in [201, 200]:
                        result = response.json()
                        remote_url = result["clone_url"]
                        info(f"GitHub远程仓库创建成功: {remote_url}")
                    else:
                        error(f"GitHub远程仓库创建失败: {response.status_code} - {response.text}")
                        QMessageBox.critical(self, "错误", "GitHub远程仓库创建失败，请检查网络和账号设置")
                        return
                        
                elif platform == "gitee":
                    # 创建Gitee远程仓库
                    token = account_data["token"]
                    username = account_data["username"]
                    
                    # Gitee API请求
                    import requests
                    data = {
                        "access_token": token,
                        "name": repo_name,
                        "description": f"由MGit创建的仓库 - {repo_name}",
                        "private": 1 if is_private else 0,
                        # 设置不创建任何初始文件
                        "auto_init": False,
                        "gitignore_template": "",
                        "license_template": ""
                    }
                    
                    response = requests.post(
                        "https://gitee.com/api/v5/user/repos",
                        data=data,
                        verify=False
                    )
                    
                    if response.status_code in [201, 200]:
                        result = response.json()
                        remote_url = result["html_url"]
                        info(f"Gitee远程仓库创建成功: {remote_url}")
                    else:
                        error(f"Gitee远程仓库创建失败: {response.status_code} - {response.text}")
                        QMessageBox.critical(self, "错误", "Gitee远程仓库创建失败，请检查网络和账号设置")
                        return
                        
                elif platform == "gitlab":
                    # 创建GitLab远程仓库
                    token = account_data["token"]
                    url = account_data["url"]
                    
                    # 确保URL格式正确
                    if not url.endswith('/'):
                        url += '/'
                    
                    # GitLab API请求
                    import requests
                    headers = {"Private-Token": token}
                    data = {
                        "name": repo_name,
                        "description": f"由MGit创建的仓库 - {repo_name}",
                        "visibility": "private" if is_private else "public",
                        # 设置不创建任何初始文件
                        "initialize_with_readme": False,
                        "lfs_enabled": False
                    }
                    
                    response = requests.post(
                        f"{url}api/v4/projects",
                        headers=headers,
                        json=data,
                        verify=False
                    )
                    
                    if response.status_code in [201, 200]:
                        result = response.json()
                        remote_url = result["http_url_to_repo"]
                        info(f"GitLab远程仓库创建成功: {remote_url}")
                    else:
                        error(f"GitLab远程仓库创建失败: {response.status_code} - {response.text}")
                        QMessageBox.critical(self, "错误", "GitLab远程仓库创建失败，请检查网络和账号设置")
                        return
                
                # 将远程仓库与本地仓库关联并推送内容
                if remote_url:
                    # 设置远程仓库
                    debug(f"正在关联本地仓库与远程仓库: {remote_url}")
                    try:
                        if 'origin' in [remote.name for remote in local_repo.remotes]:
                            # 如果origin已存在，则设置URL
                            local_repo.remote('origin').set_url(remote_url)
                        else:
                            # 创建新的远程引用
                            local_repo.create_remote('origin', remote_url)
                        
                        # 修改远程仓库URL以包含token（用于推送时身份验证）
                        authenticated_url = remote_url
                        if platform == "github":
                            authenticated_url = remote_url.replace('https://', f'https://{account_data["username"]}:{account_data["token"]}@')
                        elif platform == "gitlab":
                            authenticated_url = remote_url.replace('https://', f'https://oauth2:{account_data["token"]}@')
                        elif platform == "gitee":
                            authenticated_url = remote_url.replace('https://', f'https://{account_data["token"]}@')
                        
                        # 推送本地内容到远程仓库
                        info(f"正在将本地仓库推送至远程: {remote_url}")
                        local_repo.git.push('--set-upstream', authenticated_url, 'main')
                        
                        info(f"成功推送本地仓库至远程仓库: {remote_url}")
                        return True
                    except Exception as e:
                        error(f"无法关联或推送至远程仓库: {str(e)}")
                        QMessageBox.warning(
                            self, 
                            "远程仓库关联警告", 
                            f"远程仓库已创建，但无法推送本地内容:\n{str(e)}\n\n" +
                            f"您需要手动执行推送操作。远程仓库URL: {remote_url}"
                        )
            except Exception as e:
                error(f"创建远程仓库时发生错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"创建远程仓库时发生错误: {str(e)}")
            return
        
        # 如果没有当前登录的账号，提示用户登录
        reply = QMessageBox.question(
            self, "未登录账号",
            "创建远程仓库需要先登录GitHub、GitLab或Gitee账号。\n是否前往账号面板登录？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 显示账号面板登录区域
            info("用户选择登录账号")
            # 通过点击accountPanel的登录按钮以显示登录菜单
            self.accountPanel.loginBtn.click()
            
            # 提示用户登录后重试
            QMessageBox.information(
                self,
                "登录提示",
                "请登录账号后，再次尝试创建远程仓库。"
            )

    def refreshStatus(self):
        """ 刷新Git状态 """
        if not self.gitManager:
            return
            
        try:
            # 获取变更文件
            changes = self.gitManager.getChangedFiles()
            
            # 清空列表
            self.changesList.clear()
            
            # 添加变更文件到列表
            for status, path in changes:
                item = QListWidgetItem()
                
                # 创建一个包含复选框的小部件
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 0, 5, 0)
                
                checkbox = QCheckBox()
                checkbox.setChecked(True)
                
                statusLabel = QLabel(status)
                statusLabel.setFixedWidth(80)
                
                pathLabel = QLabel(path)
                
                layout.addWidget(checkbox)
                layout.addWidget(statusLabel)
                layout.addWidget(pathLabel)
                
                item.setSizeHint(widget.sizeHint())
                self.changesList.addItem(item)
                self.changesList.setItemWidget(item, widget)
                
            # 更新分支下拉框
            self.updateBranchCombo()
            
            # 检查远程仓库状态并更新UI
            remotes = self.gitManager.getRemotes()
            has_remotes = len(remotes) > 0
            
            # 根据是否有远程仓库来启用或禁用相关按钮
            self.pushBtn.setEnabled(has_remotes)
            self.pullBtn.setEnabled(has_remotes)
            self.syncBtn.setEnabled(has_remotes)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新状态失败: {str(e)}")
            
    def updateBranchCombo(self):
        """ 更新分支下拉框 """
        if not self.gitManager:
            return
            
        try:
            # 获取当前分支
            currentBranch = self.gitManager.getCurrentBranch()
            
            # 获取所有分支
            branches = self.gitManager.getBranches()
            
            # 记住选中的索引
            previousIndex = self.branchCombo.currentIndex()
            
            # 清空下拉框
            self.branchCombo.clear()
            
            # 添加分支到下拉框
            for branch in branches:
                self.branchCombo.addItem(branch)
                
            # 选中当前分支
            index = self.branchCombo.findText(currentBranch)
            if index >= 0:
                self.branchCombo.setCurrentIndex(index)
            elif previousIndex >= 0 and previousIndex < self.branchCombo.count():
                self.branchCombo.setCurrentIndex(previousIndex)
                
        except Exception as e:
            print(f"更新分支下拉框失败: {e}")
            
    def onBranchSelected(self, index):
        """ 处理选择分支 """
        if index < 0 or not self.gitManager:
            return
            
        selectedBranch = self.branchCombo.currentText()
        currentBranch = self.gitManager.getCurrentBranch()
        
        if selectedBranch != currentBranch:
            try:
                reply = QMessageBox.question(
                    self, "切换分支", 
                    f"确定要切换到分支 '{selectedBranch}' 吗？\n这将丢弃所有未提交的更改。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.gitManager.checkoutBranch(selectedBranch)
                    self.refreshStatus()
                    
                    InfoBar.success(
                        title="切换分支成功",
                        content=f"已切换到分支 '{selectedBranch}'",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
                else:
                    # 恢复选中当前分支
                    index = self.branchCombo.findText(currentBranch)
                    if index >= 0:
                        self.branchCombo.setCurrentIndex(index)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"切换分支失败: {str(e)}")
                
                # 恢复选中当前分支
                index = self.branchCombo.findText(currentBranch)
                if index >= 0:
                    self.branchCombo.setCurrentIndex(index)
                
    def showBranchMenu(self):
        """ 显示分支菜单 """
        if not self.gitManager:
            return
            
        # 创建菜单
        menu = QMenu(self)
        
        # 创建新分支动作
        createBranchAction = menu.addAction("创建新分支")
        createBranchAction.triggered.connect(self.createNewBranch)
        
        # 合并分支动作
        mergeBranchAction = menu.addAction("合并分支")
        mergeBranchAction.triggered.connect(self.mergeBranch)
        
        # 删除分支动作
        deleteBranchAction = menu.addAction("删除分支")
        deleteBranchAction.triggered.connect(self.deleteBranch)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def createNewBranch(self):
        """ 创建新分支 """
        if not self.gitManager:
            return
            
        # 输入分支名称
        branchName, ok = QInputDialog.getText(
            self, "创建分支", "请输入新分支名称:"
        )
        
        if not ok or not branchName:
            return
            
        try:
            # 创建分支
            self.gitManager.createBranch(branchName)
            
            # 询问是否切换到新分支
            reply = QMessageBox.question(
                self, "切换分支", 
                f"是否切换到新创建的分支 '{branchName}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.gitManager.checkoutBranch(branchName)
                
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="创建分支成功",
                content=f"已成功创建分支 '{branchName}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建分支失败: {str(e)}")
            
    def mergeBranch(self):
        """ 合并分支 """
        if not self.gitManager:
            return
            
        # 获取所有分支
        branches = self.gitManager.getBranches()
        currentBranch = self.gitManager.getCurrentBranch()
        
        # 从分支列表中移除当前分支
        if currentBranch in branches:
            branches.remove(currentBranch)
            
        if not branches:
            InfoBar.warning(
                title="无可合并分支",
                content="没有其他分支可合并到当前分支",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 选择要合并的分支
        branchName, ok = QInputDialog.getItem(
            self, "合并分支", 
            f"选择要合并到 '{currentBranch}' 的分支:",
            branches, 0, False
        )
        
        if not ok or not branchName:
            return
            
        try:
            # 合并分支
            self.gitManager.mergeBranch(branchName)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="合并分支成功",
                content=f"已成功将 '{branchName}' 合并到 '{currentBranch}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合并分支失败: {str(e)}")
            
    def deleteBranch(self):
        """ 删除分支 """
        if not self.gitManager:
            return
            
        # 获取所有分支
        branches = self.gitManager.getBranches()
        currentBranch = self.gitManager.getCurrentBranch()
        
        # 从分支列表中移除当前分支
        if currentBranch in branches:
            branches.remove(currentBranch)
            
        if not branches:
            InfoBar.warning(
                title="无可删除分支",
                content="没有其他分支可删除",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
            
        # 选择要删除的分支
        branchName, ok = QInputDialog.getItem(
            self, "删除分支", 
            "选择要删除的分支:",
            branches, 0, False
        )
        
        if not ok or not branchName:
            return
            
        # 询问是否强制删除
        reply = QMessageBox.question(
            self, "删除分支", 
            f"是否强制删除分支 '{branchName}'?\n强制删除可能导致未合并的更改丢失。",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Cancel:
            return
            
        forceDelete = (reply == QMessageBox.Yes)
        
        try:
            # 删除分支
            self.gitManager.deleteBranch(branchName, forceDelete)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="删除分支成功",
                content=f"已成功删除分支 '{branchName}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除分支失败: {str(e)}")
            
    def showRemoteMenu(self):
        """ 显示远程仓库菜单 """
        if not self.gitManager:
            return
            
        # 创建菜单
        menu = QMenu(self)
        
        # 添加远程仓库动作
        addRemoteAction = menu.addAction("添加远程仓库")
        addRemoteAction.triggered.connect(self.addRemote)
        
        # 查看远程仓库动作
        viewRemoteAction = menu.addAction("查看远程仓库")
        viewRemoteAction.triggered.connect(self.viewRemotes)
        
        # 删除远程仓库动作
        removeRemoteAction = menu.addAction("删除远程仓库")
        removeRemoteAction.triggered.connect(self.removeRemote)
        
        # 添加分隔符
        menu.addSeparator()
        
        # 从GitHub导入动作
        importGitHubAction = menu.addAction("从GitHub导入")
        importGitHubAction.triggered.connect(self.importFromGitHub)
        
        # 克隆远程仓库动作
        cloneRepoAction = menu.addAction("克隆远程仓库")
        cloneRepoAction.triggered.connect(self.cloneExternalRepo)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def addRemote(self):
        """ 添加远程仓库 """
        if not self.gitManager:
            return
            
        # 输入远程仓库名称
        remoteName, ok = QInputDialog.getText(
            self, "添加远程仓库", "请输入远程仓库名称 (例如: origin):"
        )
        
        if not ok or not remoteName:
            return
            
        # 检查远程仓库名称是否已存在
        try:
            existing_remotes = self.gitManager.getRemotes()
            if remoteName in existing_remotes:
                reply = QMessageBox.question(
                    self, "远程仓库已存在", 
                    f"远程仓库名称 '{remoteName}' 已存在，是否更新URL?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
        except Exception:
            # 如果获取远程仓库列表失败，继续尝试添加
            pass
            
        # 输入远程仓库URL
        remoteUrl, ok = QInputDialog.getText(
            self, "添加远程仓库", 
            "请输入远程仓库URL (例如: https://github.com/username/repo.git):"
        )
        
        if not ok or not remoteUrl:
            return
            
        try:
            # 尝试清理URL
            remoteUrl = self.gitManager.sanitize_url(remoteUrl)
            
            # 添加或更新远程仓库
            existing_remotes = self.gitManager.getRemotes()
            if remoteName in existing_remotes:
                # 更新已存在的远程仓库URL
                self.gitManager.repo.git.remote('set-url', remoteName, remoteUrl)
                message = f"已更新远程仓库 '{remoteName}' 的URL"
            else:
                # 添加新的远程仓库
                self.gitManager.addRemote(remoteName, remoteUrl)
                message = f"已成功添加远程仓库 '{remoteName}'"
                
            # 刷新状态并更新UI
            self.refreshStatus()
            
            InfoBar.success(
                title="操作成功",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加远程仓库失败: {str(e)}")
            
    def viewRemotes(self):
        """ 查看远程仓库 """
        if not self.gitManager:
            return
            
        try:
            # 获取远程仓库详情
            remotes = self.gitManager.getRemoteDetails()
            
            if not remotes:
                InfoBar.info(
                    title="无远程仓库",
                    content="当前仓库没有配置远程仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 显示远程仓库信息
            remoteInfo = "远程仓库列表:\n\n"
            for remote in remotes:
                remoteInfo += f"名称: {remote['name']}\n"
                remoteInfo += f"URL: {remote['url']}\n\n"
                
            QMessageBox.information(self, "远程仓库信息", remoteInfo)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取远程仓库信息失败: {str(e)}")
            
    def removeRemote(self):
        """ 删除远程仓库 """
        if not self.gitManager:
            return
            
        try:
            # 获取远程仓库详情
            remotes = self.gitManager.getRemoteDetails()
            
            if not remotes:
                InfoBar.info(
                    title="无远程仓库",
                    content="当前仓库没有配置远程仓库",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 获取远程仓库名称列表
            remoteNames = [remote['name'] for remote in remotes]
            
            # 选择要删除的远程仓库
            remoteName, ok = QInputDialog.getItem(
                self, "删除远程仓库", 
                "选择要删除的远程仓库:",
                remoteNames, 0, False
            )
            
            if not ok or not remoteName:
                return
                
            # 确认删除
            reply = QMessageBox.question(
                self, "删除远程仓库", 
                f"确定要删除远程仓库 '{remoteName}' 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 删除远程仓库
            self.gitManager.removeRemote(remoteName)
            
            InfoBar.success(
                title="删除远程仓库成功",
                content=f"已成功删除远程仓库 '{remoteName}'",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除远程仓库失败: {str(e)}")
            
    def showStashMenu(self):
        """ 显示存储菜单 """
        if not self.gitManager:
            return
            
        # 创建菜单
        menu = QMenu(self)
        
        # 创建存储动作
        createStashAction = menu.addAction("存储更改")
        createStashAction.triggered.connect(self.stashChanges)
        
        # 应用存储动作
        applyStashAction = menu.addAction("应用存储")
        applyStashAction.triggered.connect(self.applyStash)
        
        # 查看存储列表动作
        viewStashAction = menu.addAction("查看存储列表")
        viewStashAction.triggered.connect(self.viewStashList)
        
        # 删除存储动作
        dropStashAction = menu.addAction("删除存储")
        dropStashAction.triggered.connect(self.dropStash)
        
        # 清空存储动作
        clearStashAction = menu.addAction("清空所有存储")
        clearStashAction.triggered.connect(self.clearStash)
        
        # 显示菜单
        menu.exec_(QCursor.pos())
        
    def stashChanges(self):
        """ 存储更改 """
        if not self.gitManager:
            return
            
        # 输入存储消息
        message, ok = QInputDialog.getText(
            self, "存储更改", "请输入存储描述 (可选):"
        )
        
        if not ok:
            return
            
        try:
            # 存储更改
            self.gitManager.stashChanges(message if message else None)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="存储更改成功",
                content="已成功存储工作区更改",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"存储更改失败: {str(e)}")
            
    def applyStash(self):
        """ 应用存储 """
        if not self.gitManager:
            return
            
        try:
            # 获取存储列表
            stashes = self.gitManager.getStashList()
            
            if not stashes:
                InfoBar.info(
                    title="无存储记录",
                    content="没有可用的存储记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 选择要应用的存储
            stash, ok = QInputDialog.getItem(
                self, "应用存储", 
                "选择要应用的存储:",
                stashes, 0, False
            )
            
            if not ok or not stash:
                return
                
            # 获取存储ID
            stash_id = int(stash.split(':')[0].split('@')[1])
            
            # 应用存储
            self.gitManager.applyStash(stash_id)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="应用存储成功",
                content="已成功应用存储的更改",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用存储失败: {str(e)}")
            
    def viewStashList(self):
        """ 查看存储列表 """
        if not self.gitManager:
            return
            
        try:
            # 获取存储列表
            stashes = self.gitManager.getStashList()
            
            if not stashes:
                InfoBar.info(
                    title="无存储记录",
                    content="没有可用的存储记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 显示存储列表
            stashInfo = "存储列表:\n\n"
            for stash in stashes:
                stashInfo += f"{stash}\n"
                
            QMessageBox.information(self, "存储列表", stashInfo)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取存储列表失败: {str(e)}")
            
    def dropStash(self):
        """ 删除存储 """
        if not self.gitManager:
            return
            
        try:
            # 获取存储列表
            stashes = self.gitManager.getStashList()
            
            if not stashes:
                InfoBar.info(
                    title="无存储记录",
                    content="没有可用的存储记录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
                
            # 选择要删除的存储
            stash, ok = QInputDialog.getItem(
                self, "删除存储", 
                "选择要删除的存储:",
                stashes, 0, False
            )
            
            if not ok or not stash:
                return
                
            # 获取存储ID
            stash_id = int(stash.split(':')[0].split('@')[1])
            
            # 删除存储
            self.gitManager.dropStash(stash_id)
            
            InfoBar.success(
                title="删除存储成功",
                content="已成功删除存储",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除存储失败: {str(e)}")
            
    def clearStash(self):
        """ 清空所有存储 """
        if not self.gitManager:
            return
            
        try:
            # 确认清空
            reply = QMessageBox.question(
                self, "清空存储", 
                "确定要清空所有存储吗? 此操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 清空存储
            self.gitManager.clearStash()
            
            InfoBar.success(
                title="清空存储成功",
                content="已成功清空所有存储",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"清空存储失败: {str(e)}")
            
    def commitChanges(self):
        """ 提交更改 """
        if not self.gitManager:
            return
            
        # 获取更改文件列表
        changed_files = self.gitManager.getChangedFiles()
        
        if not changed_files:
            QMessageBox.information(self, "提示", "没有需要提交的更改")
            return
            
        # 显示确认对话框，让用户选择要提交的文件和输入提交消息
        dialog = QDialog(self)
        dialog.setWindowTitle("提交更改")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 提示标签
        layout.addWidget(QLabel("请选择要提交的文件:"))
        
        # 文件列表
        fileListWidget = QListWidget()
        fileListWidget.setSelectionMode(QListWidget.MultiSelection)
        
        for status, file_path in changed_files:
            item = QListWidgetItem(f"{status}: {file_path}")
            item.setData(Qt.UserRole, file_path)
            fileListWidget.addItem(item)
            item.setSelected(True)  # 默认选择所有文件
            
        layout.addWidget(fileListWidget)
        
        # 提交消息输入
        layout.addWidget(QLabel("提交消息:"))
        commitMessageEdit = LineEdit()
        layout.addWidget(commitMessageEdit)
        
        # 按钮
        btnLayout = QHBoxLayout()
        commitBtn = PrimaryPushButton("提交")
        cancelBtn = QPushButton("取消")
        
        btnLayout.addStretch(1)
        btnLayout.addWidget(commitBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addLayout(btnLayout)
        
        # 连接信号
        commitBtn.clicked.connect(dialog.accept)
        cancelBtn.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec_() != QDialog.Accepted:
            return
            
        # 获取选择的文件
        selected_files = []
        for i in range(fileListWidget.count()):
            item = fileListWidget.item(i)
            if item.isSelected():
                file_path = item.data(Qt.UserRole)
                selected_files.append(file_path)
                
        # 获取提交消息
        commit_message = commitMessageEdit.text()
        if not commit_message:
            commit_message = "提交更改"
            
        # 检查是否有选择的文件
        if not selected_files:
            QMessageBox.warning(self, "警告", "没有选择要提交的文件")
            return
        
        # 使用Git线程执行提交操作
        self.gitThread.setup(
            operation='commit',
            git_manager=self.gitManager,
            file_paths=selected_files,
            message=commit_message
        )
        self.gitThread.start()

    def pushChanges(self):
        """ 推送更改 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("推送"):
            return
            
        # 获取远程仓库列表
        remotes = self.gitManager.getRemotes()
        
        remote_name = None
        # 如果有多个远程仓库，让用户选择
        if len(remotes) > 1:
            remote_items = [remote for remote in remotes]
            remote_name, ok = QInputDialog.getItem(
                self, "选择远程仓库", 
                "请选择要推送到的远程仓库:",
                remote_items, 0, False
            )
            
            if not ok or not remote_name:
                return
        else:
            remote_name = remotes[0]
        
        # 获取当前分支
        branch = self.gitManager.getCurrentBranch()
        
        # 询问是否设置上游分支
        set_upstream = False
        try:
            # 检查是否需要设置上游分支
            # 通过检查git rev-parse命令的输出来判断
            self.gitManager.repo.git.rev_parse(f'{remote_name}/{branch}')
        except:
            # 异常表示远程没有对应分支，询问是否设置上游
            reply = QMessageBox.question(
                self, "设置上游分支", 
                f"远程仓库 {remote_name} 没有 {branch} 分支。\n是否要设置为上游分支？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            set_upstream = (reply == QMessageBox.Yes)
        
        # 使用Git线程执行推送操作
        self.gitThread.setup(
            operation='push',
            git_manager=self.gitManager,
            remote_name=remote_name,
            branch=branch,
            set_upstream=set_upstream
        )
        self.gitThread.start()

    def pullChanges(self):
        """ 拉取更改 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("拉取"):
            return
            
        # 获取远程仓库列表
        remotes = self.gitManager.getRemotes()
        
        remote_name = None
        # 如果有多个远程仓库，让用户选择
        if len(remotes) > 1:
            remote_items = [remote for remote in remotes]
            remote_name, ok = QInputDialog.getItem(
                self, "选择远程仓库", 
                "请选择要拉取的远程仓库:",
                remote_items, 0, False
            )
            
            if not ok or not remote_name:
                return
        else:
            remote_name = remotes[0]
        
        # 获取当前分支
        branch = self.gitManager.getCurrentBranch()
        
        # 使用Git线程执行拉取操作
        self.gitThread.setup(
            operation='pull',
            git_manager=self.gitManager,
            remote_name=remote_name,
            branch=branch
        )
        self.gitThread.start()

    def importFromGitHub(self):
        """ 从GitHub导入仓库 """
        if not self.gitManager:
            return
            
        # 输入GitHub仓库URL或快捷方式
        url, ok = QInputDialog.getText(
            self, "从GitHub导入", 
            "请输入GitHub仓库URL或快捷方式:\n" +
            "(例如: https://github.com/username/repo.git)\n" +
            "(或输入: username/repo)"
        )
        
        if not ok or not url:
            return
            
        # 处理快捷方式
        if not url.startswith("http") and "/" in url and not url.startswith("git@"):
            # 将username/repo转换为完整URL
            if url.count("/") == 1:  # 确保只有一个斜杠
                url = f"https://github.com/{url}.git"
        
        # 确保URL格式正确（移除可能导致问题的部分）
        if ":" in url and not url.startswith("git@"):
            # 检查是否有不正确的端口指定
            parts = url.split(":")
            if len(parts) > 1 and not parts[0].endswith("//"):
                # 修正格式为标准https URL
                domain_parts = parts[0].split("//")
                if len(domain_parts) > 1:
                    protocol = domain_parts[0] + "//"
                    domain = domain_parts[1]
                    url = protocol + domain + "/" + "/".join(parts[1:])
                    # 移除URL中可能的端口指定
                    url = url.replace(":github.com", "github.com")
        
        # 询问是否作为远程仓库添加
        reply = QMessageBox.question(
            self, "添加方式", 
            "如何添加该仓库?\n\n选择'是'将其添加为远程仓库\n选择'否'直接拉取并合并内容",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            return
            
        as_remote = (reply == QMessageBox.Yes)
        
        # 如果作为远程仓库添加，询问远程仓库名称
        remote_name = "origin"
        if as_remote:
            name, ok = QInputDialog.getText(
                self, "远程仓库名称", 
                "请输入远程仓库名称:",
                text="origin"
            )
            if ok and name:
                remote_name = name
            
        try:
            # 导入外部仓库
            self.gitManager.importExternalRepo(url, as_remote, remote_name)
            
            # 如果添加为远程仓库，询问是否拉取
            if as_remote:
                reply = QMessageBox.question(
                    self, "拉取更改", 
                    f"是否立即从远程仓库 '{remote_name}' 拉取更改?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.gitManager.pull(remote_name)
            
            # 刷新状态
            self.refreshStatus()
            
            InfoBar.success(
                title="导入成功",
                content=f"已成功从GitHub导入仓库" + (" 并添加为远程仓库" if as_remote else ""),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"从GitHub导入失败: {str(e)}")
            
    def cloneExternalRepo(self):
        """ 克隆外部仓库 """
        # 输入仓库URL或快捷方式
        url, ok = QInputDialog.getText(
            self, "克隆远程仓库", 
            "请输入远程仓库URL或快捷方式:\n" +
            "(例如: https://github.com/username/repo.git)\n" +
            "(或输入GitHub快捷方式: username/repo)"
        )
        
        if not ok or not url:
            return
            
        # 处理快捷方式
        if not url.startswith("http") and "/" in url and not url.startswith("git@"):
            # 将username/repo转换为完整URL
            if url.count("/") == 1:  # 确保只有一个斜杠
                url = f"https://github.com/{url}.git"
                
        # 确保URL格式正确（移除可能导致问题的部分）
        if ":" in url and not url.startswith("git@"):
            # 检查是否有不正确的端口指定
            parts = url.split(":")
            if len(parts) > 1 and not parts[0].endswith("//"):
                # 修正格式为标准https URL
                domain_parts = parts[0].split("//")
                if len(domain_parts) > 1:
                    protocol = domain_parts[0] + "//"
                    domain = domain_parts[1]
                    url = protocol + domain + "/" + "/".join(parts[1:])
                    # 移除URL中可能的端口指定
                    url = url.replace(":github.com", "github.com")
        
        # 选择目标路径
        target_path = QFileDialog.getExistingDirectory(
            self, "选择克隆目标位置", ""
        )
        
        if not target_path:
            return
            
        # 输入仓库名称
        repo_name, ok = QInputDialog.getText(
            self, "仓库名称", 
            "请输入本地仓库名称(留空使用默认名称):"
        )
        
        if not ok:
            return
            
        # 如果用户输入了仓库名称，使用该名称创建目标路径
        if repo_name:
            target_path = os.path.join(target_path, repo_name)
        else:
            # 从URL中提取仓库名称
            repo_name = os.path.basename(url)
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            target_path = os.path.join(target_path, repo_name)
            
        # 如果目标路径已存在，确认是否覆盖
        if os.path.exists(target_path) and os.listdir(target_path):
            reply = QMessageBox.question(
                self, "确认覆盖", 
                f"目录 {target_path} 已存在且不为空，是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
        # 询问是否以递归方式克隆（包含子模块）
        recursive = QMessageBox.question(
            self, "克隆子模块", 
            "是否以递归方式克隆（包含子模块）？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes
        
        # 询问是否指定分支
        branch_reply = QMessageBox.question(
            self, "指定分支", 
            "是否要克隆特定分支？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        branch = None
        if branch_reply == QMessageBox.Yes:
            branch, ok = QInputDialog.getText(
                self, "分支名称", 
                "请输入要克隆的分支名称:",
                text="main"
            )
            
            if not ok or not branch:
                branch = None
        
        try:
            # 使用异步方式克隆仓库
            self.cloneRepositoryAsync(url, target_path, branch, None, recursive)
            
            # 显示加载状态（加载状态会在操作完成后自动隐藏）
            self.loadingMask.showLoading("正在克隆仓库", f"正在从 {url} 克隆仓库到 {target_path}...")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"克隆仓库失败: {str(e)}")

    def syncWithRemote(self):
        """ 同步远程仓库 """
        if not self.gitManager:
            return
            
        # 确保存在远程仓库
        if not self.ensureRemoteExists("同步"):
            return
            
        # 获取当前分支
        currentBranch = self.gitManager.getCurrentBranch()
        
        # 获取远程仓库列表
        remotes = self.gitManager.getRemotes()
        
        remote_name = None
        # 如果有多个远程仓库，让用户选择
        if len(remotes) > 1:
            remote_items = [remote for remote in remotes]
            remote_name, ok = QInputDialog.getItem(
                self, "选择远程仓库", 
                "请选择要同步的远程仓库:",
                remote_items, 0, False
            )
            
            if not ok or not remote_name:
                return
        else:
            remote_name = remotes[0]
            
        # 确认对话框
        reply = QMessageBox.question(
            self, "确认同步", 
            f"确定要与远程仓库 {remote_name} 同步 {currentBranch} 分支吗?\n" +
            "这将执行 fetch+pull+push 操作。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 使用Git线程执行同步操作
            self.gitThread.setup(
                operation='sync',
                git_manager=self.gitManager,
                remote_name=remote_name,
                branch=currentBranch
            )
            self.gitThread.start()

    def ensureRemoteExists(self, operation_name="操作"):
        """ 确保远程仓库存在，如果不存在则提示用户添加 
        Args:
            operation_name: 操作名称，用于错误提示
        Returns:
            bool: 是否存在远程仓库
        """
        if not self.gitManager:
            return False
            
        try:
            remotes = self.gitManager.getRemotes()
            if not remotes:
                reply = QMessageBox.question(
                    self, f"无法{operation_name}", 
                    f"当前仓库没有配置远程仓库，无法{operation_name}。\n是否现在添加远程仓库?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.addRemote()
                return False
            return True
        except Exception:
            return False

    def onGitOperationStarted(self, operation):
        """Git操作开始时的回调
        
        Args:
            operation: 操作类型
        """
        # 构建操作标题映射
        operation_titles = {
            'pull': '正在拉取远程更新',
            'push': '正在推送本地更改',
            'fetch': '正在获取远程更新',
            'commit': '正在提交更改',
            'sync': '正在同步仓库',
            'init': '正在初始化仓库',
            'clone': '正在克隆仓库',
        }
        
        # 获取操作标题或使用默认文本
        title = operation_titles.get(operation, f'正在执行Git操作: {operation}')
        description = f"请稍候，正在处理中..."
        
        try:
            # 确保遮罩大小与父窗口一致
            if self.loadingMask.parent():
                self.loadingMask.resize(self.size())
                self.loadingMask.move(0, 0)
            
            # 显示加载遮罩并保证是最顶层
            self.loadingMask.showLoading(title, description)
            self.loadingMask.setWindowFlags(self.loadingMask.windowFlags() | Qt.WindowStaysOnTopHint)
            self.loadingMask.raise_()
            self.loadingMask.activateWindow()
            self.loadingMask.repaint()  # 强制重绘，确保立即显示
        except Exception as e:
            # 记录异常但不中断操作
            error(f"显示加载遮罩时出错: {str(e)}")

    def onGitOperationFinished(self, success, operation, message):
        """Git操作完成时的回调
        
        Args:
            success: 是否成功
            operation: 操作类型
            message: 结果消息
        """
        try:
            # 隐藏加载遮罩
            self.loadingMask.hideLoading()
            
            # 刷新状态
            self.refreshStatus()
            
            # 显示操作结果
            if success:
                InfoBar.success(
                    title=f"{operation}成功",
                    content=message,
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                QMessageBox.critical(self, f"{operation}失败", message)
        except Exception as e:
            error(f"Git操作完成回调出错: {str(e)}")
            # 确保UI更新，即使有错误
            self.refreshStatus()

    def onGitProgressUpdate(self, progress, message):
        """Git操作进度更新的回调
        
        Args:
            progress: 进度值（0-100）
            message: 进度消息
        """
        self.loadingMask.updateProgress(progress, message)

    def cloneRepositoryAsync(self, url, target_path, branch=None, depth=None, recursive=False):
        """异步克隆仓库
        
        Args:
            url: 仓库URL
            target_path: 目标路径
            branch: 分支名称
            depth: 克隆深度
            recursive: 是否递归克隆子模块
        """
        # 使用Git线程执行克隆操作，直接使用静态方法而不创建临时GitManager
        from src.utils.git_manager import GitManager
        
        # 使用Git线程执行克隆操作
        self.gitThread.setup(
            operation='clone',
            git_manager=None,  # 不使用临时GitManager
            url=url,
            target_path=target_path,
            branch=branch,
            depth=depth,
            recursive=recursive
        )
        
        # 定义克隆完成的回调
        def on_clone_finished(success, op, msg):
            if success:
                # 克隆成功，打开新仓库
                try:
                    self.setRepository(target_path)
                    
                    # 发出信号通知其他组件
                    self.repositoryOpened.emit(target_path)
                except Exception as e:
                    error(f"克隆成功但打开仓库失败: {str(e)}")
                    QMessageBox.information(
                        self, 
                        "克隆成功", 
                        f"仓库已克隆成功，但打开时出错: {str(e)}\n仓库路径: {target_path}"
                    )
            
            # 移除临时连接
            self.gitThread.operationFinished.disconnect(on_clone_finished)
        
        # 临时连接，只处理一次克隆完成的回调
        self.gitThread.operationFinished.connect(on_clone_finished)
        
        # 开始克隆
        self.gitThread.start()

    def resizeEvent(self, event):
        """窗口大小改变事件，确保遮罩能够覆盖整个窗口"""
        super().resizeEvent(event)
        
        # 如果遮罩显示中，调整其大小
        if self.loadingMask and self.loadingMask.isVisible():
            self.loadingMask.resize(self.size())
            self.loadingMask.move(0, 0) 