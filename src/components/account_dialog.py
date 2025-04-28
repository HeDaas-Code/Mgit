#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QLineEdit, QListWidget, QListWidgetItem,
                           QTabWidget, QWidget, QMessageBox, QInputDialog,
                           QFormLayout, QCheckBox, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from qfluentwidgets import (PrimaryPushButton, TransparentToolButton, FluentIcon,
                           ToolTipFilter, ToolTipPosition, ComboBox,
                           InfoBarPosition, InfoBar, LineEdit)
from src.utils.account_manager import AccountManager
from src.utils.oauth_handler import OAuthHandler, OAuthBrowserDialog

class AccountDialog(QDialog):
    """ 账号管理对话框 """
    
    # 定义信号，当账号列表发生变化时触发
    accountsChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.accountManager = AccountManager()
        self.oauthHandler = OAuthHandler(self)
        self.initUI()
        
        # 连接信号
        self.accountManager.accountsChanged.connect(self.refreshAccountLists)
        self.oauthHandler.githubAuthSuccess.connect(self.handleGithubOAuthSuccess)
        self.oauthHandler.githubAuthFailed.connect(self.handleOAuthError)
        self.oauthHandler.giteeAuthSuccess.connect(self.handleGiteeOAuthSuccess)
        self.oauthHandler.giteeAuthFailed.connect(self.handleOAuthError)
        # self.oauthHandler.gitlabAuthSuccess.connect(self.handleGitlabOAuthSuccess)
        # self.oauthHandler.gitlabAuthFailed.connect(self.handleOAuthError)
        
    def initUI(self):
        """ 初始化UI """
        self.setWindowTitle("账号管理")
        self.resize(550, 450)
        
        # 主布局
        mainLayout = QVBoxLayout(self)
        
        # 创建标签页
        self.tabWidget = QTabWidget()
        self.githubTab = QWidget()
        self.giteeTab = QWidget()
        
        self.tabWidget.addTab(self.githubTab, "GitHub")
        self.tabWidget.addTab(self.giteeTab, "Gitee")
        
        # 初始化GitHub标签页
        self.initGithubTab()
        
        # 初始化Gitee标签页
        self.initGiteeTab()
        
        mainLayout.addWidget(self.tabWidget)
        
        # 底部按钮区域
        buttonLayout = QHBoxLayout()
        
        self.okButton = PrimaryPushButton("确定")
        self.okButton.clicked.connect(self.accept)
        
        self.cancelButton = QPushButton("取消")
        self.cancelButton.clicked.connect(self.reject)
        
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        
        mainLayout.addLayout(buttonLayout)
        
        # 加载初始数据
        self.refreshAccountLists()
        
    def initGithubTab(self):
        """ 初始化GitHub标签页 """
        layout = QVBoxLayout(self.githubTab)
        
        # 账号列表区域
        listGroupBox = QGroupBox("已添加的GitHub账号")
        listLayout = QVBoxLayout(listGroupBox)
        
        self.githubAccountList = QListWidget()
        listLayout.addWidget(self.githubAccountList)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        # 移除添加Token按钮，只保留OAuth登录按钮
        self.addGithubOAuthBtn = QPushButton("添加账号")
        self.addGithubOAuthBtn.clicked.connect(self.startGithubOAuth)
        
        self.removeGithubAccountBtn = QPushButton("删除账号")
        self.removeGithubAccountBtn.clicked.connect(self.removeGithubAccount)
        self.removeGithubAccountBtn.setEnabled(False)  # 初始禁用
        
        btnLayout.addWidget(self.addGithubOAuthBtn)
        btnLayout.addWidget(self.removeGithubAccountBtn)
        btnLayout.addStretch(1)
        
        listLayout.addLayout(btnLayout)
        
        # 连接选择变化信号
        self.githubAccountList.itemSelectionChanged.connect(self.onGithubSelectionChanged)
        
        layout.addWidget(listGroupBox)
        
    def initGiteeTab(self):
        """ 初始化Gitee标签页 """
        layout = QVBoxLayout(self.giteeTab)
        
        # 账号列表区域
        listGroupBox = QGroupBox("已添加的Gitee账号")
        listLayout = QVBoxLayout(listGroupBox)
        
        self.giteeAccountList = QListWidget()
        listLayout.addWidget(self.giteeAccountList)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        # 移除添加Token按钮，只保留OAuth登录按钮
        self.addGiteeOAuthBtn = QPushButton("添加账号")
        self.addGiteeOAuthBtn.clicked.connect(self.startGiteeOAuth)
        
        self.removeGiteeAccountBtn = QPushButton("删除账号")
        self.removeGiteeAccountBtn.clicked.connect(self.removeGiteeAccount)
        self.removeGiteeAccountBtn.setEnabled(False)  # 初始禁用
        
        btnLayout.addWidget(self.addGiteeOAuthBtn)
        btnLayout.addWidget(self.removeGiteeAccountBtn)
        btnLayout.addStretch(1)
        
        listLayout.addLayout(btnLayout)
        
        # 连接选择变化信号
        self.giteeAccountList.itemSelectionChanged.connect(self.onGiteeSelectionChanged)
        
        layout.addWidget(listGroupBox)
        
    def refreshAccountLists(self):
        """ 刷新账号列表 """
        # 清空现有列表
        self.githubAccountList.clear()
        self.giteeAccountList.clear()
        
        # 加载GitHub账号
        github_accounts = self.accountManager.get_github_accounts()
        for account in github_accounts:
            item = QListWidgetItem(f"{account['name']} ({account['username']})")
            item.setData(Qt.UserRole, account)
            self.githubAccountList.addItem(item)
            
        # 加载Gitee账号
        gitee_accounts = self.accountManager.get_gitee_accounts()
        for account in gitee_accounts:
            item = QListWidgetItem(f"{account['name']} ({account['username']})")
            item.setData(Qt.UserRole, account)
            self.giteeAccountList.addItem(item)
            
        # 发出账号更改信号
        self.accountsChanged.emit()
        
    def onGithubSelectionChanged(self):
        """ 处理GitHub账号列表选择变化 """
        self.removeGithubAccountBtn.setEnabled(len(self.githubAccountList.selectedItems()) > 0)
        
    def onGiteeSelectionChanged(self):
        """ 处理Gitee账号列表选择变化 """
        self.removeGiteeAccountBtn.setEnabled(len(self.giteeAccountList.selectedItems()) > 0)
        
    def removeGithubAccount(self):
        """ 移除所选GitHub账号 """
        selected_items = self.githubAccountList.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除GitHub账号 {account['username']} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.accountManager.remove_github_account(account['username']):
                InfoBar.success(
                    title="删除成功",
                    content=f"GitHub账号 {account['username']} 已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                QMessageBox.warning(self, "删除失败", "无法删除所选账号")
                
    def removeGiteeAccount(self):
        """ 移除所选Gitee账号 """
        selected_items = self.giteeAccountList.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除Gitee账号 {account['username']} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.accountManager.remove_gitee_account(account['username']):
                InfoBar.success(
                    title="删除成功",
                    content=f"Gitee账号 {account['username']} 已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                QMessageBox.warning(self, "删除失败", "无法删除所选账号")
                
    def getGithubAccounts(self):
        """ 获取所有GitHub账号 """
        return self.accountManager.get_github_accounts()
        
    def getGiteeAccounts(self):
        """ 获取所有Gitee账号 """
        return self.accountManager.get_gitee_accounts() 

    def startGithubOAuth(self):
        """ 启动GitHub OAuth授权流程 """
        # 检查OAuth配置
        if not self.oauthHandler.github_client_id or not self.oauthHandler.github_client_secret:
            # 显示更友好的提示信息
            QMessageBox.information(
                self,
                "设置OAuth",
                "为了保障账号安全，现在MGit已全面采用OAuth授权登录方式。\n\n"
                "您需要先配置GitHub OAuth应用信息才能登录。\n"
                "这是一次性设置，之后可以直接使用GitHub账号登录。\n\n"
                "点击确定进入设置页面。"
            )
            self.configureGithubOAuth()
            return
            
        # 开始OAuth流程
        self.oauthHandler.start_github_auth()
    
    def configureGithubOAuth(self):
        """ 配置GitHub OAuth """
        dialog = QDialog(self)
        dialog.setWindowTitle("配置GitHub OAuth")
        dialog.resize(450, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明信息
        infoLabel = QLabel(
            "为了使用OAuth登录，您需要在GitHub上创建一个OAuth应用。\n"
            "按照以下步骤操作：\n\n"
            "1. 访问 https://github.com/settings/developers\n"
            "2. 点击 'New OAuth App'\n"
            "3. 填写应用信息：\n"
            "   - Application name: MGit (或任意名称)\n"
            "   - Homepage URL: http://localhost\n"
            "   - Authorization callback URL: 使用下面显示的回调地址\n"
            "4. 创建后，将显示的Client ID和Client Secret填入下方"
        )
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 添加表单
        formLayout = QFormLayout()
        
        # 客户端ID输入
        clientIdEdit = LineEdit()
        clientIdEdit.setText(self.oauthHandler.github_client_id)
        clientIdEdit.setPlaceholderText("GitHub OAuth应用客户端ID")
        formLayout.addRow("Client ID:", clientIdEdit)
        
        # 客户端密钥输入
        clientSecretEdit = LineEdit()
        clientSecretEdit.setText(self.oauthHandler.github_client_secret)
        clientSecretEdit.setPlaceholderText("GitHub OAuth应用客户端密钥")
        clientSecretEdit.setEchoMode(QLineEdit.Password)
        formLayout.addRow("Client Secret:", clientSecretEdit)
        
        # 回调URL显示
        callbackLabel = QLabel(self.oauthHandler.github_redirect_uri)
        callbackLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        formLayout.addRow("回调URL:", callbackLabel)
        
        layout.addLayout(formLayout)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        saveBtn = PrimaryPushButton("保存并继续")
        cancelBtn = QPushButton("取消")
        openGithubBtn = QPushButton("打开GitHub开发者设置")
        
        openGithubBtn.clicked.connect(lambda: self.openGithubDeveloperSettings())
        
        btnLayout.addWidget(openGithubBtn)
        btnLayout.addStretch(1)
        btnLayout.addWidget(saveBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addLayout(btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        saveBtn.clicked.connect(lambda: self.saveGithubOAuthConfig(
            dialog, clientIdEdit.text(), clientSecretEdit.text()
        ))
        
        dialog.exec_()
        
    def openGithubDeveloperSettings(self):
        """打开GitHub开发者设置页面"""
        import webbrowser
        webbrowser.open("https://github.com/settings/developers")
    
    def saveGithubOAuthConfig(self, dialog, client_id, client_secret):
        """ 保存GitHub OAuth配置并开始认证 """
        if not client_id or not client_secret:
            QMessageBox.warning(dialog, "输入错误", "客户端ID和密钥不能为空")
            return
            
        # 更新配置
        self.oauthHandler.github_client_id = client_id
        self.oauthHandler.github_client_secret = client_secret
        
        # 创建环境变量（会话级别）
        os.environ["GITHUB_CLIENT_ID"] = client_id
        os.environ["GITHUB_CLIENT_SECRET"] = client_secret
        
        # 关闭配置对话框
        dialog.accept()
        
        # 开始认证流程
        self.startGithubOAuth()
    
    def handleGithubOAuthSuccess(self, code):
        """ 处理GitHub OAuth登录成功 """
        # 使用授权码完成账号添加
        if self.oauthHandler.github_client_id and self.oauthHandler.github_client_secret:
            # 添加账号
            if self.accountManager.add_github_account_oauth(
                code, 
                self.oauthHandler.github_client_id, 
                self.oauthHandler.github_client_secret
            ):
                InfoBar.success(
                    title="添加成功",
                    content="GitHub账号已成功添加",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                QMessageBox.warning(self, "添加失败", "无法通过OAuth验证添加GitHub账号")
    
    def handleOAuthError(self, error):
        """ 处理OAuth错误 """
        QMessageBox.warning(self, "认证失败", f"OAuth认证失败: {error}")
    
    def startGiteeOAuth(self):
        """ 启动Gitee OAuth授权流程 """
        # 检查OAuth配置
        if not self.oauthHandler.gitee_client_id or not self.oauthHandler.gitee_client_secret:
            # 显示更友好的提示信息
            QMessageBox.information(
                self,
                "设置OAuth",
                "为了保障账号安全，现在MGit已全面采用OAuth授权登录方式。\n\n"
                "您需要先配置Gitee OAuth应用信息才能登录。\n"
                "这是一次性设置，之后可以直接使用Gitee账号登录。\n\n"
                "点击确定进入设置页面。"
            )
            self.configureGiteeOAuth()
            return
            
        # 开始OAuth流程
        self.oauthHandler.start_gitee_auth()
        
    def configureGiteeOAuth(self):
        """ 配置Gitee OAuth """
        dialog = QDialog(self)
        dialog.setWindowTitle("配置Gitee OAuth")
        dialog.resize(450, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明信息
        infoLabel = QLabel(
            "为了使用OAuth登录，您需要在Gitee上创建一个OAuth应用。\n"
            "按照以下步骤操作：\n\n"
            "1. 访问 https://gitee.com/oauth/applications\n"
            "2. 点击 '创建应用'\n"
            "3. 填写应用信息：\n"
            "   - 应用名称: MGit (或任意名称)\n"
            "   - 应用主页: http://localhost\n"
            "   - 授权回调地址: 使用下面显示的回调地址\n"
            "   - 权限范围: 勾选 projects、pull_requests、issues\n"
            "4. 创建后，将显示的Client ID和Client Secret填入下方"
        )
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 添加表单
        formLayout = QFormLayout()
        
        # 客户端ID输入
        clientIdEdit = LineEdit()
        clientIdEdit.setText(self.oauthHandler.gitee_client_id)
        clientIdEdit.setPlaceholderText("Gitee OAuth应用客户端ID")
        formLayout.addRow("Client ID:", clientIdEdit)
        
        # 客户端密钥输入
        clientSecretEdit = LineEdit()
        clientSecretEdit.setText(self.oauthHandler.gitee_client_secret)
        clientSecretEdit.setPlaceholderText("Gitee OAuth应用客户端密钥")
        clientSecretEdit.setEchoMode(QLineEdit.Password)
        formLayout.addRow("Client Secret:", clientSecretEdit)
        
        # 回调URL显示
        callbackLabel = QLabel(self.oauthHandler.gitee_redirect_uri)
        callbackLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        formLayout.addRow("回调URL:", callbackLabel)
        
        layout.addLayout(formLayout)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        saveBtn = PrimaryPushButton("保存并继续")
        cancelBtn = QPushButton("取消")
        openGiteeBtn = QPushButton("打开Gitee OAuth应用管理")
        
        openGiteeBtn.clicked.connect(lambda: self.openGiteeApplicationsPage())
        
        btnLayout.addWidget(openGiteeBtn)
        btnLayout.addStretch(1)
        btnLayout.addWidget(saveBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addLayout(btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        saveBtn.clicked.connect(lambda: self.saveGiteeOAuthConfig(
            dialog, clientIdEdit.text(), clientSecretEdit.text()
        ))
        
        dialog.exec_()
        
    def openGiteeApplicationsPage(self):
        """打开Gitee OAuth应用管理页面"""
        import webbrowser
        webbrowser.open("https://gitee.com/oauth/applications")
    
    def saveGiteeOAuthConfig(self, dialog, client_id, client_secret):
        """ 保存Gitee OAuth配置并开始认证 """
        if not client_id or not client_secret:
            QMessageBox.warning(dialog, "输入错误", "客户端ID和密钥不能为空")
            return
            
        # 更新配置
        self.oauthHandler.gitee_client_id = client_id
        self.oauthHandler.gitee_client_secret = client_secret
        
        # 创建环境变量（会话级别）
        os.environ["GITEE_CLIENT_ID"] = client_id
        os.environ["GITEE_CLIENT_SECRET"] = client_secret
        
        # 关闭配置对话框
        dialog.accept()
        
        # 开始认证流程
        self.startGiteeOAuth()
        
    def handleGiteeOAuthSuccess(self, code):
        """ 处理Gitee OAuth登录成功 """
        # 使用授权码完成账号添加
        if self.oauthHandler.gitee_client_id and self.oauthHandler.gitee_client_secret:
            # 添加账号
            if self.accountManager.add_gitee_account_oauth(
                code, 
                self.oauthHandler.gitee_client_id, 
                self.oauthHandler.gitee_client_secret,
                self.oauthHandler.gitee_redirect_uri
            ):
                InfoBar.success(
                    title="添加成功",
                    content="Gitee账号已成功添加",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                QMessageBox.warning(self, "添加失败", "无法通过OAuth验证添加Gitee账号") 