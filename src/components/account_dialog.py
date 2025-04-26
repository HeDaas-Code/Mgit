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
        self.gitlabTab = QWidget()
        
        self.tabWidget.addTab(self.githubTab, "GitHub")
        self.tabWidget.addTab(self.gitlabTab, "GitLab")
        
        # 初始化GitHub标签页
        self.initGithubTab()
        
        # 初始化GitLab标签页
        self.initGitlabTab()
        
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
        
        self.addGithubAccountBtn = QPushButton("添加Token")
        self.addGithubAccountBtn.clicked.connect(self.showAddGithubAccountDialog)
        
        self.addGithubOAuthBtn = QPushButton("通过Web登录")
        self.addGithubOAuthBtn.clicked.connect(self.startGithubOAuth)
        
        self.removeGithubAccountBtn = QPushButton("删除账号")
        self.removeGithubAccountBtn.clicked.connect(self.removeGithubAccount)
        self.removeGithubAccountBtn.setEnabled(False)  # 初始禁用
        
        btnLayout.addWidget(self.addGithubAccountBtn)
        btnLayout.addWidget(self.addGithubOAuthBtn)
        btnLayout.addWidget(self.removeGithubAccountBtn)
        btnLayout.addStretch(1)
        
        listLayout.addLayout(btnLayout)
        
        # 连接选择变化信号
        self.githubAccountList.itemSelectionChanged.connect(self.onGithubSelectionChanged)
        
        layout.addWidget(listGroupBox)
        
    def initGitlabTab(self):
        """ 初始化GitLab标签页 """
        layout = QVBoxLayout(self.gitlabTab)
        
        # 账号列表区域
        listGroupBox = QGroupBox("已添加的GitLab账号")
        listLayout = QVBoxLayout(listGroupBox)
        
        self.gitlabAccountList = QListWidget()
        listLayout.addWidget(self.gitlabAccountList)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        self.addGitlabAccountBtn = QPushButton("添加Token")
        self.addGitlabAccountBtn.clicked.connect(self.showAddGitlabAccountDialog)
        
        self.addGitlabOAuthBtn = QPushButton("通过Web登录")
        self.addGitlabOAuthBtn.clicked.connect(self.startGitlabOAuth)
        
        self.removeGitlabAccountBtn = QPushButton("删除账号")
        self.removeGitlabAccountBtn.clicked.connect(self.removeGitlabAccount)
        self.removeGitlabAccountBtn.setEnabled(False)  # 初始禁用
        
        btnLayout.addWidget(self.addGitlabAccountBtn)
        btnLayout.addWidget(self.addGitlabOAuthBtn)
        btnLayout.addWidget(self.removeGitlabAccountBtn)
        btnLayout.addStretch(1)
        
        listLayout.addLayout(btnLayout)
        
        # 连接选择变化信号
        self.gitlabAccountList.itemSelectionChanged.connect(self.onGitlabSelectionChanged)
        
        layout.addWidget(listGroupBox)
        
    def refreshAccountLists(self):
        """ 刷新账号列表 """
        # 清空现有列表
        self.githubAccountList.clear()
        self.gitlabAccountList.clear()
        
        # 加载GitHub账号
        github_accounts = self.accountManager.get_github_accounts()
        for account in github_accounts:
            item = QListWidgetItem(f"{account['name']} ({account['username']})")
            item.setData(Qt.UserRole, account)
            self.githubAccountList.addItem(item)
            
        # 加载GitLab账号
        gitlab_accounts = self.accountManager.get_gitlab_accounts()
        for account in gitlab_accounts:
            item = QListWidgetItem(f"{account['name']} ({account['username']})")
            item.setData(Qt.UserRole, account)
            self.gitlabAccountList.addItem(item)
            
        # 发出账号更改信号
        self.accountsChanged.emit()
        
    def showAddGithubAccountDialog(self):
        """ 显示添加GitHub账号对话框 """
        dialog = QDialog(self)
        dialog.setWindowTitle("添加GitHub账号")
        dialog.resize(380, 200)
        
        layout = QFormLayout(dialog)
        
        # 用户名输入
        usernameEdit = LineEdit()
        usernameEdit.setPlaceholderText("GitHub用户名")
        layout.addRow("用户名:", usernameEdit)
        
        # 访问令牌输入
        tokenEdit = LineEdit()
        tokenEdit.setPlaceholderText("GitHub访问令牌")
        tokenEdit.setEchoMode(QLineEdit.Password)
        layout.addRow("访问令牌:", tokenEdit)
        
        # 账号别名输入（可选）
        nameEdit = LineEdit()
        nameEdit.setPlaceholderText("可选，默认使用用户名")
        layout.addRow("账号别名:", nameEdit)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        addBtn = PrimaryPushButton("添加")
        cancelBtn = QPushButton("取消")
        
        btnLayout.addStretch(1)
        btnLayout.addWidget(addBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addRow("", btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        addBtn.clicked.connect(lambda: self.addGithubAccount(
            dialog, usernameEdit.text(), tokenEdit.text(), nameEdit.text()
        ))
        
        dialog.exec_()
        
    def addGithubAccount(self, dialog, username, token, name):
        """ 添加GitHub账号 """
        if not username or not token:
            QMessageBox.warning(dialog, "输入错误", "用户名和访问令牌不能为空")
            return
            
        # 如果未提供别名，置为None让AccountManager使用默认值
        name = name if name else None
        
        # 添加账号
        if self.accountManager.add_github_account(username, token, name):
            dialog.accept()
            InfoBar.success(
                title="添加成功",
                content=f"GitHub账号 {username} 已成功添加",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            dialog.accept()  # 关闭对话框
            # 显示更详细的错误信息
            QMessageBox.warning(
                self, 
                "添加失败", 
                "无法验证账号，可能的原因:\n\n"
                "1. 用户名或访问令牌不正确\n"
                "2. 令牌权限不足，需要至少有 'repo' 权限\n"
                "3. 网络连接问题\n"
                "4. GitHub API访问限制\n\n"
                "您可以尝试使用'通过Web登录'方式添加账号"
            )
            
    def showAddGitlabAccountDialog(self):
        """ 显示添加GitLab账号对话框 """
        dialog = QDialog(self)
        dialog.setWindowTitle("添加GitLab账号")
        dialog.resize(400, 220)
        
        layout = QFormLayout(dialog)
        
        # GitLab实例URL输入
        urlEdit = LineEdit()
        urlEdit.setPlaceholderText("如: https://gitlab.com/")
        layout.addRow("GitLab URL:", urlEdit)
        
        # 访问令牌输入
        tokenEdit = LineEdit()
        tokenEdit.setPlaceholderText("GitLab访问令牌")
        tokenEdit.setEchoMode(QLineEdit.Password)
        layout.addRow("访问令牌:", tokenEdit)
        
        # 账号别名输入（可选）
        nameEdit = LineEdit()
        nameEdit.setPlaceholderText("可选，默认从URL中提取")
        layout.addRow("账号别名:", nameEdit)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        addBtn = PrimaryPushButton("添加")
        cancelBtn = QPushButton("取消")
        
        btnLayout.addStretch(1)
        btnLayout.addWidget(addBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addRow("", btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        addBtn.clicked.connect(lambda: self.addGitlabAccount(
            dialog, urlEdit.text(), tokenEdit.text(), nameEdit.text()
        ))
        
        dialog.exec_()
        
    def addGitlabAccount(self, dialog, url, token, name):
        """ 添加GitLab账号 """
        if not url or not token:
            QMessageBox.warning(dialog, "输入错误", "GitLab URL和访问令牌不能为空")
            return
            
        # 确保URL格式正确
        if not url.startswith("http"):
            url = "https://" + url
            
        # 如果未提供别名，置为None让AccountManager使用默认值
        name = name if name else None
        
        # 添加账号
        if self.accountManager.add_gitlab_account(url, token, name):
            dialog.accept()
            InfoBar.success(
                title="添加成功",
                content=f"GitLab账号已成功添加",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            dialog.accept()  # 关闭对话框
            # 显示更详细的错误信息
            QMessageBox.warning(
                self, 
                "添加失败", 
                "无法验证账号，可能的原因:\n\n"
                "1. GitLab实例URL不正确\n"
                "2. 访问令牌不正确或已过期\n"
                "3. 令牌权限不足，需要至少有 'api' 权限\n"
                "4. 网络连接问题\n"
                "5. SSL证书验证问题\n\n"
                "您可以尝试使用'通过Web登录'方式添加账号"
            )
            
    def onGithubSelectionChanged(self):
        """ 处理GitHub账号列表选择变化 """
        self.removeGithubAccountBtn.setEnabled(len(self.githubAccountList.selectedItems()) > 0)
        
    def onGitlabSelectionChanged(self):
        """ 处理GitLab账号列表选择变化 """
        self.removeGitlabAccountBtn.setEnabled(len(self.gitlabAccountList.selectedItems()) > 0)
        
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
                
    def removeGitlabAccount(self):
        """ 移除所选GitLab账号 """
        selected_items = self.gitlabAccountList.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除GitLab账号 {account['username']} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.accountManager.remove_gitlab_account(account['url'], account['username']):
                InfoBar.success(
                    title="删除成功",
                    content=f"GitLab账号 {account['username']} 已删除",
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
        
    def getGitlabAccounts(self):
        """ 获取所有GitLab账号 """
        return self.accountManager.get_gitlab_accounts() 

    def startGithubOAuth(self):
        """ 开始GitHub OAuth登录 """
        # 检查OAuth配置
        if not self.oauthHandler.github_client_id or not self.oauthHandler.github_client_secret:
            # 显示配置对话框
            self.configureGithubOAuth()
            return
            
        # 启动OAuth流程
        success = self.oauthHandler.start_github_auth()
        if not success:
            QMessageBox.warning(self, "认证失败", "无法启动GitHub认证流程，请检查配置")
        
    def configureGithubOAuth(self):
        """ 配置GitHub OAuth """
        dialog = QDialog(self)
        dialog.setWindowTitle("配置GitHub OAuth")
        dialog.resize(400, 200)
        
        layout = QFormLayout(dialog)
        
        # 客户端ID输入
        clientIdEdit = LineEdit()
        clientIdEdit.setText(self.oauthHandler.github_client_id)
        clientIdEdit.setPlaceholderText("GitHub OAuth客户端ID")
        layout.addRow("Client ID:", clientIdEdit)
        
        # 客户端密钥输入
        clientSecretEdit = LineEdit()
        clientSecretEdit.setText(self.oauthHandler.github_client_secret)
        clientSecretEdit.setPlaceholderText("GitHub OAuth客户端密钥")
        clientSecretEdit.setEchoMode(QLineEdit.Password)
        layout.addRow("Client Secret:", clientSecretEdit)
        
        # 提示信息
        infoLabel = QLabel("请在GitHub开发者设置中创建OAuth应用，并确保回调URL设置为:")
        layout.addRow("", infoLabel)
        
        callbackLabel = QLabel(self.oauthHandler.github_redirect_uri)
        callbackLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow("回调URL:", callbackLabel)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        saveBtn = PrimaryPushButton("保存并认证")
        cancelBtn = QPushButton("取消")
        
        btnLayout.addStretch(1)
        btnLayout.addWidget(saveBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addRow("", btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        saveBtn.clicked.connect(lambda: self.saveGithubOAuthConfig(
            dialog, clientIdEdit.text(), clientSecretEdit.text()
        ))
        
        dialog.exec_()
        
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
    
    def startGitlabOAuth(self):
        """ 开始GitLab OAuth登录 """
        # 显示配置对话框
        self.configureGitlabOAuth()
    
    def configureGitlabOAuth(self):
        """ 配置GitLab OAuth """
        dialog = QDialog(self)
        dialog.setWindowTitle("配置GitLab OAuth")
        dialog.resize(450, 250)
        
        layout = QFormLayout(dialog)
        
        # GitLab实例URL输入
        urlEdit = LineEdit()
        urlEdit.setPlaceholderText("如: https://gitlab.com/")
        layout.addRow("GitLab URL:", urlEdit)
        
        # 客户端ID输入
        clientIdEdit = LineEdit()
        clientIdEdit.setText(self.oauthHandler.gitlab_client_id)
        clientIdEdit.setPlaceholderText("GitLab OAuth应用ID")
        layout.addRow("Client ID:", clientIdEdit)
        
        # 客户端密钥输入
        clientSecretEdit = LineEdit()
        clientSecretEdit.setText(self.oauthHandler.gitlab_client_secret)
        clientSecretEdit.setPlaceholderText("GitLab OAuth应用密钥")
        clientSecretEdit.setEchoMode(QLineEdit.Password)
        layout.addRow("Client Secret:", clientSecretEdit)
        
        # 提示信息
        infoLabel = QLabel("请在GitLab开发者设置中创建OAuth应用，并确保回调URL设置为:")
        layout.addRow("", infoLabel)
        
        callbackLabel = QLabel(self.oauthHandler.gitlab_redirect_uri)
        callbackLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow("回调URL:", callbackLabel)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        saveBtn = PrimaryPushButton("保存并认证")
        cancelBtn = QPushButton("取消")
        
        btnLayout.addStretch(1)
        btnLayout.addWidget(saveBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addRow("", btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        saveBtn.clicked.connect(lambda: self.saveGitlabOAuthConfig(
            dialog, urlEdit.text(), clientIdEdit.text(), clientSecretEdit.text()
        ))
        
        dialog.exec_()
    
    def saveGitlabOAuthConfig(self, dialog, url, client_id, client_secret):
        """ 保存GitLab OAuth配置并开始认证 """
        if not url or not client_id or not client_secret:
            QMessageBox.warning(dialog, "输入错误", "URL、客户端ID和密钥不能为空")
            return
            
        # 确保URL格式正确
        if not url.startswith("http"):
            url = "https://" + url
            
        # 更新配置
        self.gitlab_url = url
        self.oauthHandler.gitlab_client_id = client_id
        self.oauthHandler.gitlab_client_secret = client_secret
        
        # 创建环境变量（会话级别）
        os.environ["GITLAB_CLIENT_ID"] = client_id
        os.environ["GITLAB_CLIENT_SECRET"] = client_secret
        
        # 关闭配置对话框
        dialog.accept()
        
        # 开始认证流程
        success = self.oauthHandler.start_gitlab_auth(url)
        if not success:
            QMessageBox.warning(self, "认证失败", "无法启动GitLab认证流程，请检查配置")
    
    def handleGitlabOAuthSuccess(self, code):
        """ 处理GitLab OAuth登录成功 """
        # 使用授权码完成账号添加
        if hasattr(self, 'gitlab_url') and self.oauthHandler.gitlab_client_id and self.oauthHandler.gitlab_client_secret:
            # 添加账号
            if self.accountManager.add_gitlab_account_oauth(
                code,
                self.oauthHandler.gitlab_redirect_uri,
                self.oauthHandler.gitlab_client_id,
                self.oauthHandler.gitlab_client_secret,
                self.gitlab_url
            ):
                InfoBar.success(
                    title="添加成功",
                    content="GitLab账号已成功添加",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                QMessageBox.warning(self, "添加失败", "无法通过OAuth验证添加GitLab账号") 