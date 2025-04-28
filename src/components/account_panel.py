#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QMenu, QAction, QDialog, QMessageBox,
                           QInputDialog, QFormLayout, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QFont, QCursor
from qfluentwidgets import (CardWidget, TransparentToolButton, FluentIcon, 
                          ToolTipFilter, ToolTipPosition, LineEdit, PrimaryPushButton,
                          InfoBar, InfoBarPosition, ComboBox, RoundMenu)

from src.utils.enhanced_account_manager import EnhancedAccountManager
from src.utils.oauth_handler import OAuthHandler, OAuthBrowserDialog
from src.utils.logger import info, warning, error, debug
from src.components.two_factor_dialog import TwoFactorSetupDialog, TwoFactorVerifyDialog, TwoFactorRecoveryDialog
from src.utils.two_factor_auth import TwoFactorAuth

class AccountPanel(QWidget):
    """
    账号面板组件，显示在Git面板顶部
    提供登录状态、账号切换和账号管理功能
    """
    
    # 定义信号
    accountChanged = pyqtSignal(object)  # 账号变更信号，传递账号信息，可以是dict或None
    
    def __init__(self, parent=None, account_manager=None):
        super().__init__(parent)
        # 使用传入的账号管理器或创建新实例
        self.accountManager = account_manager if account_manager else EnhancedAccountManager()
        self.oauthHandler = OAuthHandler(self)
        self.twoFactorAuth = TwoFactorAuth(issuer="MGit")
        
        # 初始化验证对话框状态
        self._verification_dialog_active = False
        
        # 初始化UI
        self.initUI()
        
        # 连接信号
        self.accountManager.loginSuccess.connect(self.onLoginSuccess)
        self.accountManager.loginFailed.connect(self.onLoginFailed)
        self.accountManager.autoLoginStarted.connect(self.onAutoLoginStarted)
        self.accountManager.avatarLoaded.connect(self.onAvatarLoaded)
        self.accountManager.accountsChanged.connect(self.updateAccountSelector)
        self.accountManager.twoFactorRequired.connect(self.showTwoFactorVerification)
        
        # OAuth信号连接
        self.oauthHandler.githubAuthSuccess.connect(self.onGithubOAuthSuccess)
        self.oauthHandler.githubAuthFailed.connect(self.onOAuthFailed)
        self.oauthHandler.giteeAuthSuccess.connect(self.onGiteeOAuthSuccess)
        self.oauthHandler.giteeAuthFailed.connect(self.onOAuthFailed)
        
        # 尝试自动登录
        QTimer.singleShot(500, self.accountManager.auto_login)
        
    def initUI(self):
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 账号卡片
        self.accountCard = CardWidget(self)
        cardLayout = QVBoxLayout(self.accountCard)
        cardLayout.setContentsMargins(10, 10, 10, 10)
        cardLayout.setSpacing(5)
        
        # 标题栏
        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)
        
        titleLabel = QLabel("账号")
        titleLabel.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        titleLayout.addWidget(titleLabel)
        
        # 添加设置按钮
        self.settingsBtn = TransparentToolButton(FluentIcon.SETTING)
        self.settingsBtn.setToolTip("账号设置")
        self.settingsBtn.clicked.connect(self.showAccountSettings)
        titleLayout.addWidget(self.settingsBtn)
        
        # 添加账号管理按钮
        self.manageBtn = TransparentToolButton(FluentIcon.PEOPLE)
        self.manageBtn.setToolTip("账号管理")
        self.manageBtn.clicked.connect(self.showAccountManagement)
        titleLayout.addWidget(self.manageBtn)
        
        cardLayout.addLayout(titleLayout)
        
        # 当前账号信息区域
        self.accountInfoWidget = QWidget()
        accountInfoLayout = QHBoxLayout(self.accountInfoWidget)
        accountInfoLayout.setContentsMargins(0, 0, 0, 0)
        accountInfoLayout.setSpacing(10)
        
        # 头像标签
        self.avatarLabel = QLabel()
        self.avatarLabel.setFixedSize(32, 32)
        self.avatarLabel.setScaledContents(True)
        self.avatarLabel.setPixmap(FluentIcon.PEOPLE.icon().pixmap(32, 32))  # 默认头像
        accountInfoLayout.addWidget(self.avatarLabel)
        
        # 账号信息
        infoLayout = QVBoxLayout()
        infoLayout.setContentsMargins(0, 0, 0, 0)
        infoLayout.setSpacing(0)
        
        self.nameLabel = QLabel("未登录")
        self.nameLabel.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        infoLayout.addWidget(self.nameLabel)
        
        self.statusLabel = QLabel("点击登录按钮以连接账号")
        self.statusLabel.setFont(QFont("Microsoft YaHei", 8))
        infoLayout.addWidget(self.statusLabel)
        
        accountInfoLayout.addLayout(infoLayout)
        
        # 登录/切换账号按钮
        self.loginBtn = TransparentToolButton(FluentIcon.CHEVRON_DOWN_MED)
        self.loginBtn.setToolTip("登录或切换账号")
        self.loginBtn.clicked.connect(self.showLoginMenu)
        accountInfoLayout.addWidget(self.loginBtn)
        
        cardLayout.addWidget(self.accountInfoWidget)
        
        # 添加到主布局
        layout.addWidget(self.accountCard)
        
        # 更新UI状态
        self.updateUIState()
        
    def updateUIState(self):
        """根据登录状态更新UI"""
        current_account = self.accountManager.get_current_account()
        
        if current_account:
            # 已登录状态
            account_data = current_account['data']
            account_type = current_account['type']
            
            self.nameLabel.setText(account_data['name'])
            
            if account_type == 'github':
                self.statusLabel.setText(f"GitHub: {account_data['username']}")
            elif account_type == 'gitee':
                self.statusLabel.setText(f"Gitee: {account_data['username']}")
            
            # 检查是否有头像缓存
            avatar = self.accountManager.get_avatar(account_data['username'])
            if avatar:
                self.avatarLabel.setPixmap(avatar)
            elif 'avatar_url' in account_data and account_data['avatar_url']:
                # 显示默认头像，等待加载完成
                self.avatarLabel.setPixmap(FluentIcon.PEOPLE.icon().pixmap(32, 32))
            else:
                self.avatarLabel.setPixmap(FluentIcon.PEOPLE.icon().pixmap(32, 32))
        else:
            # 未登录状态
            self.nameLabel.setText("未登录")
            self.statusLabel.setText("点击登录按钮以连接账号")
            self.avatarLabel.setPixmap(FluentIcon.PEOPLE.icon().pixmap(32, 32))
            
    def showLoginMenu(self):
        """显示登录菜单"""
        menu = QMenu(self)
        
        # 添加GitHub登录选项
        githubMenu = QMenu("GitHub账号", self)
        
        github_accounts = self.accountManager.get_github_accounts()
        if github_accounts:
            for account in github_accounts:
                action = githubMenu.addAction(f"{account['name']} ({account['username']})")
                action.triggered.connect(lambda checked, username=account['username']: 
                                       self.switchToAccount('github', username))
                
            githubMenu.addSeparator()
            
        # 去掉使用Token添加账号的选项，只保留OAuth登录
        add_github_oauth = githubMenu.addAction("添加GitHub账号")
        add_github_oauth.triggered.connect(self.startGithubOAuth)
        
        # 将GitHub菜单添加到主菜单
        menu.addMenu(githubMenu)
        
        # 添加Gitee登录选项
        giteeMenu = QMenu("Gitee账号", self)
        
        gitee_accounts = self.accountManager.get_gitee_accounts()
        if gitee_accounts:
            for account in gitee_accounts:
                action = giteeMenu.addAction(f"{account['name']} ({account['username']})")
                action.triggered.connect(lambda checked, username=account['username']: 
                                      self.switchToAccount('gitee', username))
                
            giteeMenu.addSeparator()
            
        # 修改Gitee账号添加方式，使用OAuth登录
        add_gitee_oauth = giteeMenu.addAction("添加Gitee账号")
        add_gitee_oauth.triggered.connect(self.startGiteeOAuth)
        
        # 将Gitee菜单添加到主菜单
        menu.addMenu(giteeMenu)
        
        # 如果已登录，添加注销选项
        if self.accountManager.get_current_account():
            menu.addSeparator()
            logout_action = menu.addAction("注销当前账号")
            logout_action.triggered.connect(self.logout)
            
        # 显示菜单
        menu.exec_(self.loginBtn.mapToGlobal(self.loginBtn.rect().bottomLeft()))
        
    def switchToAccount(self, account_type, username):
        """切换到指定账号，先退出当前账号"""
        try:
            # 先检查是否已经登录其他账号
            current_account = self.accountManager.get_current_account()
            if current_account:
                # 先退出当前账号
                debug(f"切换账号：先退出当前账号 {current_account['type']}/{current_account['data']['username']}")
                self.accountManager.current_account = None
                # 通知UI账号已退出
                self.updateUIState()
                
            # 登录指定账号
            debug(f"切换到账号：{account_type}/{username}")
            self.accountManager.login_with_account(account_type, username)
            
        except Exception as e:
            error(f"切换账号时出错: {str(e)}")
            QMessageBox.warning(self, "切换账号失败", f"切换账号时出错: {str(e)}")
        
    def ensureCleanOAuthState(self):
        """确保OAuth状态干净，停止任何正在进行的授权流程"""
        try:
            # 先检查OAuth处理器是否有force_stop_auth方法
            if hasattr(self.oauthHandler, 'force_stop_auth'):
                debug("清理任何正在进行的OAuth流程")
                self.oauthHandler.force_stop_auth()
            
            # 确保没有当前账号
            current_account = self.accountManager.get_current_account()
            if current_account:
                debug("清理当前账号登录状态")
                # 退出当前账号
                self.accountManager.current_account = None
                self.accountManager.accounts['last_login'] = None
                self.accountManager.save_accounts()
                # 更新UI状态
                self.updateUIState()
                # 发出账号变更信号
                self.accountChanged.emit(None)
            
            return True
        except Exception as e:
            error(f"清理OAuth状态时出错: {str(e)}")
            return False
        
    def startGiteeOAuth(self):
        """启动Gitee OAuth授权流程"""
        # 确保OAuth状态干净
        if not self.ensureCleanOAuthState():
            QMessageBox.warning(self, "准备授权失败", "无法清理现有的授权状态，请尝试重启应用")
            return
        
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
        try:
            # 显示正在处理的提示
            InfoBar.info(
                title="正在授权",
                content="正在启动Gitee授权流程，请稍候...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
            self.oauthHandler.start_gitee_auth()
        except Exception as e:
            error(f"启动Gitee OAuth授权失败: {str(e)}")
            QMessageBox.warning(self, "授权失败", f"启动授权流程失败: {str(e)}")
            
    def configureGiteeOAuth(self):
        """配置Gitee OAuth"""
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
        """保存Gitee OAuth配置并继续授权流程"""
        if not client_id or not client_secret:
            QMessageBox.warning(dialog, "输入错误", "Client ID和Client Secret不能为空")
            return
            
        # 更新配置
        self.oauthHandler.gitee_client_id = client_id
        self.oauthHandler.gitee_client_secret = client_secret
        
        # 加密保存配置
        self.oauthHandler.save_oauth_config()
        
        # 关闭对话框
        dialog.accept()
        
        # 继续OAuth流程
        self.startGiteeOAuth()
        
    def onGiteeOAuthSuccess(self, code):
        """Gitee OAuth授权成功回调"""
        try:
            InfoBar.success(
                title="授权成功",
                content="Gitee授权成功，正在添加账号...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
            # 使用授权码添加Gitee账号
            self.accountManager.add_gitee_account_oauth(
                code,
                self.oauthHandler.gitee_client_id,
                self.oauthHandler.gitee_client_secret,
                self.oauthHandler.gitee_redirect_uri
            )
            
            # 确保OAuth处理器清理资源
            if hasattr(self.oauthHandler, 'force_stop_auth'):
                QTimer.singleShot(5000, self.oauthHandler.force_stop_auth)
        except Exception as e:
            error(f"处理Gitee OAuth回调失败: {str(e)}")
            QMessageBox.warning(self, "添加账号失败", f"处理授权响应失败: {str(e)}")
            
            # 确保OAuth处理器清理资源
            if hasattr(self.oauthHandler, 'force_stop_auth'):
                self.oauthHandler.force_stop_auth()
            
    def onGithubOAuthSuccess(self, code):
        """GitHub OAuth授权成功回调"""
        try:
            InfoBar.success(
                title="授权成功",
                content="GitHub授权成功，正在添加账号...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
            # 使用授权码添加GitHub账号
            self.accountManager.add_github_account_oauth(
                code,
                self.oauthHandler.github_client_id,
                self.oauthHandler.github_client_secret
            )
            
            # 确保OAuth处理器清理资源
            if hasattr(self.oauthHandler, 'force_stop_auth'):
                QTimer.singleShot(5000, self.oauthHandler.force_stop_auth)
        except Exception as e:
            error(f"处理GitHub OAuth回调失败: {str(e)}")
            QMessageBox.warning(self, "添加账号失败", f"处理授权响应失败: {str(e)}")
            
            # 确保OAuth处理器清理资源
            if hasattr(self.oauthHandler, 'force_stop_auth'):
                self.oauthHandler.force_stop_auth()
            
    def startGithubOAuth(self):
        """启动GitHub OAuth授权流程"""
        # 确保OAuth状态干净
        if not self.ensureCleanOAuthState():
            QMessageBox.warning(self, "准备授权失败", "无法清理现有的授权状态，请尝试重启应用")
            return
            
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
        try:
            # 显示正在处理的提示
            InfoBar.info(
                title="正在授权",
                content="正在启动GitHub授权流程，请稍候...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
            self.oauthHandler.start_github_auth()
        except Exception as e:
            error(f"启动GitHub OAuth授权失败: {str(e)}")
            QMessageBox.warning(self, "授权失败", f"启动授权流程失败: {str(e)}")
            
    def configureGithubOAuth(self):
        """配置GitHub OAuth"""
        dialog = QDialog(self)
        dialog.setWindowTitle("配置GitHub OAuth")
        dialog.resize(450, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 添加说明信息
        infoLabel = QLabel(
            "为了使用OAuth登录，您需要在GitHub上创建一个OAuth应用。\n"
            "按照以下步骤操作：\n\n"
            "1. 访问 https://github.com/settings/developers\n"
            "2. 点击 'New OAuth application'\n"
            "3. 填写应用信息：\n"
            "   - 应用名称: MGit (或任意名称)\n"
            "   - 应用主页: http://localhost\n"
            "   - 授权回调地址: 使用下面显示的回调地址\n"
            "   - 权限范围: 勾选 repo、user\n"
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
        openGithubBtn = QPushButton("打开GitHub OAuth应用管理")
        
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
        """打开GitHub OAuth应用管理页面"""
        import webbrowser
        webbrowser.open("https://github.com/settings/developers")
        
    def saveGithubOAuthConfig(self, dialog, client_id, client_secret):
        """保存GitHub OAuth配置并继续授权流程"""
        if not client_id or not client_secret:
            QMessageBox.warning(dialog, "输入错误", "Client ID和Client Secret不能为空")
            return
            
        # 更新配置
        self.oauthHandler.github_client_id = client_id
        self.oauthHandler.github_client_secret = client_secret
        
        # 加密保存配置
        self.oauthHandler.save_oauth_config()
        
        # 关闭对话框
        dialog.accept()
        
        # 继续OAuth流程
        self.startGithubOAuth()
        
    def onOAuthFailed(self, error_message):
        """OAuth授权失败回调"""
        try:
            error(f"OAuth授权失败: {error_message}")
            QMessageBox.warning(self, "授权失败", f"授权过程中出错: {error_message}")
            
            # 确保OAuth处理器清理资源
            if hasattr(self.oauthHandler, 'force_stop_auth'):
                self.oauthHandler.force_stop_auth()
        except Exception as e:
            error(f"处理OAuth失败回调时发生错误: {str(e)}")
        
    def logout(self):
        """注销当前账号"""
        current_account = self.accountManager.get_current_account()
        if current_account:
            self.accountManager.current_account = None
            self.accountManager.accounts['last_login'] = None
            self.accountManager.save_accounts()
            
            # 更新UI
            self.updateUIState()
            
            # 发出账号变更信号
            self.accountChanged.emit(None)
            
            InfoBar.success(
                title="已注销",
                content="已成功注销当前账号",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def showAccountSettings(self):
        """显示账号设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("账号设置")
        dialog.resize(350, 200)
        
        layout = QVBoxLayout(dialog)
        
        # 自动登录选项
        autoLoginCheck = QCheckBox("启用自动登录")
        autoLoginCheck.setChecked(self.accountManager.accounts['auto_login'])
        layout.addWidget(autoLoginCheck)
        
        # 二次验证选项
        twoFactorCheck = QCheckBox("启用两因素认证（2FA）")
        twoFactorCheck.setChecked(self.accountManager.accounts['2fa_enabled'])
        layout.addWidget(twoFactorCheck)
        
        # 2FA 管理按钮 (仅当2FA启用时显示)
        self.manageTwoFactorBtn = QPushButton("配置两因素认证")
        self.manageTwoFactorBtn.clicked.connect(self.showTwoFactorManagement)
        self.manageTwoFactorBtn.setEnabled(twoFactorCheck.isChecked())
        layout.addWidget(self.manageTwoFactorBtn)
        
        # 连接复选框变化信号
        twoFactorCheck.stateChanged.connect(lambda state: self.manageTwoFactorBtn.setEnabled(state == Qt.Checked))
        
        # 加密设置说明
        infoLabel = QLabel("账号数据采用本地加密存储，密钥保存在用户目录下的.mgit文件夹中。")
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 重置加密按钮
        resetEncryptionBtn = QPushButton("重置加密设置")
        resetEncryptionBtn.clicked.connect(self.confirmResetEncryption)
        layout.addWidget(resetEncryptionBtn)
        
        layout.addStretch(1)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        saveBtn = PrimaryPushButton("保存")
        cancelBtn = QPushButton("取消")
        
        btnLayout.addStretch(1)
        btnLayout.addWidget(saveBtn)
        btnLayout.addWidget(cancelBtn)
        
        layout.addLayout(btnLayout)
        
        # 连接信号
        cancelBtn.clicked.connect(dialog.reject)
        saveBtn.clicked.connect(lambda: self.saveAccountSettings(
            dialog, autoLoginCheck.isChecked(), twoFactorCheck.isChecked()
        ))
        
        dialog.exec_()
        
    def saveAccountSettings(self, dialog, auto_login, two_factor):
        """保存账号设置"""
        # 更新设置
        self.accountManager.set_auto_login(auto_login)
        self.accountManager.set_2fa_enabled(two_factor)
        
        # 关闭对话框
        dialog.accept()
        
        InfoBar.success(
            title="设置已保存",
            content="账号设置已成功保存",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def confirmResetEncryption(self):
        """确认重置加密设置"""
        reply = QMessageBox.warning(
            self,
            "重置加密设置",
            "重置加密设置将清除所有已保存的账号信息，并重新生成加密密钥。\n\n"
            "此操作不可撤销，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 调用重置方法
                self.accountManager._recreate_encryption_key()
                
                # 更新UI
                self.updateUIState()
                
                InfoBar.success(
                    title="重置成功",
                    content="加密设置已重置，所有账号信息已清除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            except Exception as e:
                error(f"重置加密设置失败: {str(e)}")
                QMessageBox.critical(self, "重置失败", f"重置加密设置时出错: {str(e)}")
                
    def showAccountManagement(self):
        """显示账号管理对话框"""
        try:
            # 先确保清理所有OAuth状态，避免冲突
            self.ensureCleanOAuthState()
            
            # 防止重复打开对话框
            if hasattr(self, 'accountManagementDialog') and self.accountManagementDialog:
                try:
                    if self.accountManagementDialog.isVisible():
                        # 已有对话框，激活它
                        self.accountManagementDialog.activateWindow()
                        return
                    else:
                        # 销毁已有但不可见的对话框
                        debug("清理未关闭的不可见对话框")
                        self.cleanupAccountDialog()
                except Exception as e:
                    error(f"检查对话框状态时出错: {str(e)}")
                    # 安全起见，尝试清理
                    self.cleanupAccountDialog()
            
            # 创建新对话框
            self.accountManagementDialog = QDialog(self)
            dialog = self.accountManagementDialog
            dialog.setWindowTitle("账号管理")
            dialog.resize(450, 350)
            
            layout = QVBoxLayout(dialog)
            
            # 账号列表标签
            layout.addWidget(QLabel("已保存的账号:"))
            
            # 账号选择器（ComboBox）
            self.accountSelector = ComboBox()
            layout.addWidget(self.accountSelector)
            
            # 账号详情区
            self.accountDetailsWidget = QWidget()
            detailsLayout = QFormLayout(self.accountDetailsWidget)
            
            self.detailTypeLabel = QLabel("")
            detailsLayout.addRow("类型:", self.detailTypeLabel)
            
            self.detailNameLabel = QLabel("")
            detailsLayout.addRow("名称:", self.detailNameLabel)
            
            self.detailUsernameLabel = QLabel("")
            detailsLayout.addRow("用户名:", self.detailUsernameLabel)
            
            self.detailAddedLabel = QLabel("")
            detailsLayout.addRow("添加时间:", self.detailAddedLabel)
            
            self.detailLastUsedLabel = QLabel("")
            detailsLayout.addRow("最后使用:", self.detailLastUsedLabel)
            
            layout.addWidget(self.accountDetailsWidget)
            
            # 操作按钮
            btnLayout = QHBoxLayout()
            
            self.loginSelectedBtn = PrimaryPushButton("登录选中账号")
            self.loginSelectedBtn.clicked.connect(self.safeLoginSelectedAccount)
            btnLayout.addWidget(self.loginSelectedBtn)
            
            self.renameSelectedBtn = QPushButton("重命名")
            self.renameSelectedBtn.clicked.connect(self.safeRenameSelectedAccount)
            btnLayout.addWidget(self.renameSelectedBtn)
            
            self.removeSelectedBtn = QPushButton("删除")
            self.removeSelectedBtn.clicked.connect(self.safeRemoveSelectedAccount)
            btnLayout.addWidget(self.removeSelectedBtn)
            
            layout.addLayout(btnLayout)
            
            # 底部按钮
            bottomBtnLayout = QHBoxLayout()
            closeBtn = QPushButton("关闭")
            closeBtn.clicked.connect(dialog.accept)
            
            bottomBtnLayout.addStretch(1)
            bottomBtnLayout.addWidget(closeBtn)
            
            layout.addLayout(bottomBtnLayout)
            
            # 初始化账号详情
            try:
                # 延迟初始化选择器，避免多个信号同时触发
                self.updateAccountSelector()
                
                # 连接选择变化信号
                self.accountSelector.currentIndexChanged.connect(
                    lambda index: QTimer.singleShot(10, lambda: self.updateAccountDetails(index))
                )
                
                # 初始化账号详情
                QTimer.singleShot(10, self.updateAccountDetails)
            except Exception as e:
                error(f"初始化账号选择器失败: {str(e)}")
            
            # 防止对话框被垃圾回收
            dialog.setAttribute(Qt.WA_DeleteOnClose, False)
            
            # 使用finished信号连接清理函数，确保资源会被清理
            dialog.finished.connect(self.cleanupAccountDialog)
            
            # 安全执行对话框
            dialog.exec_()
        except Exception as e:
            error(f"显示账号管理对话框失败: {str(e)}")
            # 确保在出错时也能清理资源
            self.cleanupAccountDialog()
    
    def cleanupAccountDialog(self):
        """清理账号管理对话框资源"""
        try:
            if hasattr(self, 'accountManagementDialog') and self.accountManagementDialog:
                debug("正在清理账号管理对话框资源...")
                
                # 断开所有信号连接
                if hasattr(self, 'accountSelector') and self.accountSelector:
                    try:
                        self.accountSelector.currentIndexChanged.disconnect()
                    except Exception as e:
                        debug(f"断开账号选择器信号失败: {str(e)}")
                    
                    self.accountSelector.deleteLater()
                    self.accountSelector = None
                
                # 删除对话框
                try:
                    # 确保对话框关闭
                    if self.accountManagementDialog.isVisible():
                        self.accountManagementDialog.reject()
                except:
                    pass
                
                self.accountManagementDialog.deleteLater()
                self.accountManagementDialog = None
                
                debug("账号管理对话框资源已清理")
                
                # 强制垃圾回收，帮助释放资源
                import gc
                gc.collect()
        except Exception as e:
            error(f"清理账号管理对话框资源失败: {str(e)}")

    def safeLoginSelectedAccount(self):
        """安全地登录选中的账号并关闭对话框"""
        try:
            # 获取当前选择器数据，检查是否有选中的账号
            if not hasattr(self, 'accountSelector') or not self.accountSelector:
                return False
                
            current_data = self.accountSelector.currentData()
            if not current_data:
                return False
                
            account_type = current_data['type']
            username = current_data['username']
            
            # 获取对话框引用，准备关闭
            dialog = self.accountManagementDialog if hasattr(self, 'accountManagementDialog') else None
            
            # 断开所有信号连接，防止触发不必要的更新
            if hasattr(self, 'accountSelector') and self.accountSelector:
                try:
                    self.accountSelector.blockSignals(True)
                except:
                    pass
            
            # 先关闭对话框，确保资源释放优先于账号切换
            if dialog:
                try:
                    # 立即接受对话框，但保留资源清理到后面
                    dialog.accept()
                except Exception as e:
                    error(f"关闭账号管理对话框时出错: {str(e)}")
            
            # 确保清理干净OAuth状态，为新账号登录做准备
            self.ensureCleanOAuthState()
            
            # 使用switchToAccount方法来确保先退出当前账号再登录新账号
            debug(f"安全登录账号: {account_type}/{username}")
            result = self.switchToAccount(account_type, username)
            
            # 确保清理资源
            self.cleanupAccountDialog()
            
            return result
        except Exception as e:
            error(f"安全登录选中账号时出错: {str(e)}")
            # 确保在出错时也能清理资源
            self.cleanupAccountDialog()
            return False
    
    def loginSelectedAccount(self):
        """登录选中的账号"""
        try:
            if not hasattr(self, 'accountSelector') or not self.accountSelector:
                return False
                
            current_data = self.accountSelector.currentData()
            if not current_data:
                return False
                
            account_type = current_data['type']
            username = current_data['username']
            
            # 使用switchToAccount方法来确保先退出当前账号
            return self.switchToAccount(account_type, username)
        except Exception as e:
            error(f"登录账号时发生错误: {str(e)}")
            QMessageBox.warning(self, "登录失败", f"登录账号时出错: {str(e)}")
            return False
    
    def safeRenameSelectedAccount(self):
        """安全地重命名选中账号"""
        try:
            if not hasattr(self, 'accountSelector') or not self.accountSelector:
                return
                
            current_data = self.accountSelector.currentData()
            if not current_data:
                return
                
            # 调用原始重命名方法
            self.renameSelectedAccount()
        except Exception as e:
            error(f"安全重命名账号时出错: {str(e)}")
    
    def renameSelectedAccount(self):
        """重命名选中的账号"""
        try:
            current_data = self.accountSelector.currentData()
            if not current_data:
                return
                
            account_type = current_data['type']
            username = current_data['username']
            
            # 查找账号
            account = None
            accounts_list = None
            index = -1
            if account_type == 'github':
                accounts_list = self.accountManager.accounts['github']
                for i, acc in enumerate(accounts_list):
                    if acc['username'] == username:
                        account = acc
                        index = i
                        break
            elif account_type == 'gitee':
                accounts_list = self.accountManager.accounts['gitee']
                for i, acc in enumerate(accounts_list):
                    if acc['username'] == username:
                        account = acc
                        index = i
                        break
                        
            if not account or not accounts_list or index == -1:
                return
                
            # 获取新名称
            new_name, ok = QInputDialog.getText(
                self,
                "重命名账号",
                "请输入新的账号名称:",
                text=account['name']
            )
            
            if ok and new_name:
                # 更新账号名称
                account['name'] = new_name
                accounts_list[index] = account
                
                # 保存更改
                self.accountManager.save_accounts()
                
                # 更新UI
                self.updateAccountSelector()
                self.updateUIState()
                
                InfoBar.success(
                    title="重命名成功",
                    content=f"账号已重命名为: {new_name}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except Exception as e:
            error(f"重命名账号时发生错误: {str(e)}")
            QMessageBox.warning(self, "重命名失败", f"重命名账号时出错: {str(e)}")
    
    def safeRemoveSelectedAccount(self):
        """安全地删除选中账号"""
        try:
            if not hasattr(self, 'accountSelector') or not self.accountSelector:
                return
                
            current_data = self.accountSelector.currentData()
            if not current_data:
                return
                
            # 调用原始删除方法
            self.removeSelectedAccount()
        except Exception as e:
            error(f"安全删除账号时出错: {str(e)}")
            
    def removeSelectedAccount(self):
        """删除选中的账号"""
        try:
            current_data = self.accountSelector.currentData()
            if not current_data:
                return
                
            account_type = current_data['type']
            username = current_data['username']
            
            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除账号 {username} 吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 查找账号
                success = False
                if account_type == 'github':
                    for i, acc in enumerate(self.accountManager.accounts['github']):
                        if acc['username'] == username:
                            self.accountManager.accounts['github'].pop(i)
                            success = True
                            break
                elif account_type == 'gitee':
                    for i, acc in enumerate(self.accountManager.accounts['gitee']):
                        if acc['username'] == username:
                            self.accountManager.accounts['gitee'].pop(i)
                            success = True
                            break
                            
                if success:
                    # 保存更改
                    self.accountManager.save_accounts()
                    
                    # 更新UI
                    self.updateAccountSelector()
                    self.updateUIState()
                    
                    InfoBar.success(
                        title="删除成功",
                        content=f"账号已删除: {username}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self
                    )
        except Exception as e:
            error(f"删除账号时发生错误: {str(e)}")
            QMessageBox.warning(self, "删除失败", f"删除账号时出错: {str(e)}")
        
    def onLoginSuccess(self, account):
        """登录成功回调"""
        info(f"登录成功: {account['type']}/{account['data']['username']}")
        
        # 更新UI
        self.updateUIState()
        
        # 发出账号变更信号
        self.accountChanged.emit(account)
        
        InfoBar.success(
            title="登录成功",
            content=f"已成功登录到 {account['data']['name']}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def onLoginFailed(self, error_message):
        """登录失败回调"""
        error(f"登录失败: {error_message}")
        
        # 更新UI
        self.updateUIState()
        
        InfoBar.error(
            title="登录失败",
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
    def onAutoLoginStarted(self):
        """自动登录开始回调"""
        debug("尝试自动登录中...")
        
        InfoBar.info(
            title="自动登录",
            content="正在尝试自动登录...",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def onAvatarLoaded(self, username, pixmap):
        """头像加载完成回调"""
        current_account = self.accountManager.get_current_account()
        if current_account and current_account['data']['username'] == username:
            self.avatarLabel.setPixmap(pixmap)
            
    def showTwoFactorManagement(self):
        """显示两因素认证管理对话框"""
        # 检查是否有当前账号
        current_account = self.accountManager.get_current_account()
        if not current_account:
            QMessageBox.warning(self, "未登录", "请先登录账号才能管理两因素认证")
            return
            
        # 获取当前用户名
        username = current_account['data']['username']
        
        # 检查是否已设置2FA
        if self.accountManager.has_2fa_setup(username):
            # 已设置，显示管理选项
            menu = QMenu(self)
            
            view_qr_action = menu.addAction("查看二维码")
            view_qr_action.triggered.connect(lambda: self.showTwoFactorQRCode(username))
            
            reset_action = menu.addAction("重置两因素认证")
            reset_action.triggered.connect(lambda: self.setupTwoFactorAuth(username))
            
            recover_action = menu.addAction("使用恢复码")
            recover_action.triggered.connect(lambda: self.showTwoFactorRecovery(username))
            
            remove_action = menu.addAction("移除两因素认证")
            remove_action.triggered.connect(lambda: self.removeTwoFactorAuth(username))
            
            menu.exec_(QCursor.pos())
        else:
            # 未设置，启动设置流程
            self.setupTwoFactorAuth(username)
            
    def setupTwoFactorAuth(self, username):
        """为指定用户设置两因素认证"""
        dialog = TwoFactorSetupDialog(username, self)
        dialog.setupCompleted.connect(lambda secret_key, hashed_codes: self.saveTwoFactorSecret(username, secret_key, hashed_codes))
        dialog.exec_()
        
    def saveTwoFactorSecret(self, username, secret_key, hashed_recovery_codes=None):
        """保存用户的两因素认证密钥"""
        # 保存2FA密钥
        self.accountManager.save_2fa_secret(username, secret_key)
        
        # 如果提供了恢复码，保存恢复码
        if hashed_recovery_codes:
            self.accountManager.save_2fa_recovery_codes(username, hashed_recovery_codes)
        
        # 更新界面显示
        self.updateAccountSelector()
        
        InfoBar.success(
            title="已启用",
            content="两因素认证已成功启用",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def showTwoFactorQRCode(self, username):
        """显示用户的两因素认证二维码"""
        # 获取密钥
        secret_key = self.accountManager.get_2fa_secret(username)
        if not secret_key:
            QMessageBox.warning(self, "未设置", "该账号尚未设置两因素认证")
            return
            
        # 生成二维码
        pixmap = self.twoFactorAuth.generate_qrcode(username, secret_key)
        if not pixmap:
            QMessageBox.warning(self, "生成失败", "无法生成二维码，请重新设置两因素认证")
            return
            
        # 显示二维码对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("两因素认证二维码")
        dialog.setFixedSize(300, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        titleLabel = QLabel("扫描下方二维码")
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)
        
        # 二维码
        qrLabel = QLabel()
        qrLabel.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qrLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(qrLabel)
        
        # 密钥显示
        keyLayout = QHBoxLayout()
        keyLayout.addWidget(QLabel("密钥:"))
        
        keyLabel = QLabel(self.formatSecretKey(secret_key))
        keyLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        keyLayout.addWidget(keyLabel)
        
        layout.addLayout(keyLayout)
        
        # 说明
        infoLabel = QLabel("如果您需要重新扫描或在新设备上设置，可以使用此二维码。\n请妥善保管您的认证器应用，它是您账号的重要安全凭证。")
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 确定按钮
        btnLayout = QHBoxLayout()
        okBtn = QPushButton("确定")
        okBtn.clicked.connect(dialog.accept)
        btnLayout.addStretch(1)
        btnLayout.addWidget(okBtn)
        btnLayout.addStretch(1)
        layout.addLayout(btnLayout)
        
        dialog.exec_()
        
    def formatSecretKey(self, key):
        """格式化密钥，增加可读性"""
        formatted = ""
        for i in range(0, len(key), 4):
            formatted += key[i:i+4] + " "
        return formatted.strip()
        
    def removeTwoFactorAuth(self, username):
        """移除用户的两因素认证"""
        reply = QMessageBox.warning(
            self,
            "移除两因素认证",
            "确定要移除两因素认证吗？这将降低您账号的安全性。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.accountManager.remove_2fa_secret(username)
            
            InfoBar.success(
                title="已移除",
                content="两因素认证已成功移除",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            
    def showTwoFactorVerification(self, secret_key):
        """显示两因素认证验证对话框"""
        if self._verification_dialog_active:
            warning("已有两因素认证验证对话框正在显示")
            return
            
        self._verification_dialog_active = True
        
        # 获取当前用户名，用于恢复流程
        username = None
        if hasattr(self.accountManager, '_pending_login') and self.accountManager._pending_login:
            username = self.accountManager._pending_login['data'].get('username')
        
        # 显示验证对话框
        dialog = TwoFactorVerifyDialog(secret_key, username, self)
        
        # 连接信号
        dialog.verificationSuccess.connect(self.onTwoFactorSuccess)
        dialog.verificationFailed.connect(self.onTwoFactorFailed)
        dialog.recoveryRequested.connect(self.showTwoFactorRecovery)
        
        # 显示对话框
        dialog.exec_()
        
        # 标记对话框已关闭
        self._verification_dialog_active = False
        
    def onTwoFactorSuccess(self):
        """两因素认证成功回调"""
        info("两因素验证成功，完成登录流程")
        
        try:
            # 完成登录流程
            success = self.accountManager.complete_two_factor_auth()
            
            if success:
                InfoBar.success(
                    title="验证成功",
                    content="两因素认证成功，已完成登录",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                # 检查是否有待处理的登录
                if hasattr(self.accountManager, '_pending_login') and self.accountManager._pending_login:
                    account_type = self.accountManager._pending_login['type']
                    username = self.accountManager._pending_login['data']['username']
                    warning(f"两因素验证成功，但登录 {account_type}/{username} 未完成，尝试重新完成登录")
                    
                    # 尝试再次完成登录
                    QTimer.singleShot(500, self.accountManager.complete_two_factor_auth)
                else:
                    warning("两因素验证成功，但登录流程无法完成")
                    InfoBar.warning(
                        title="登录未完成",
                        content="两因素验证成功，但登录流程未完成，请重试",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
        except Exception as e:
            error(f"两因素验证后完成登录时发生错误: {str(e)}")
            InfoBar.error(
                title="登录失败",
                content=f"两因素验证成功，但登录时出错: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        
    def onTwoFactorFailed(self):
        """两因素认证失败回调"""
        self.loginFailed.emit("两因素验证失败，请重新尝试")
        
    def showTwoFactorRecovery(self, username):
        """显示两因素认证恢复对话框"""
        # 检查是否有恢复码
        recovery_codes = self.accountManager.get_2fa_recovery_codes(username)
        if not recovery_codes:
            QMessageBox.warning(
                self, 
                "无法恢复", 
                "未找到恢复码，无法进行恢复。\n请联系管理员或重置账号。"
            )
            return
        
        # 创建恢复对话框
        dialog = TwoFactorRecoveryDialog(username, self)
        
        # 连接信号
        dialog.recoverySuccess.connect(self.onTwoFactorRecoverySuccess)
        dialog.recoveryFailed.connect(self.onTwoFactorRecoveryFailed)
        
        # 显示对话框
        dialog.exec_()
        
    def onTwoFactorRecoverySuccess(self, username, used_hash):
        """两因素认证恢复成功回调，先完成登录，再禁用2FA"""
        info(f"用户 {username} 的恢复码验证成功，尝试完成登录")
        
        # 检查是否在登录验证过程中
        is_login_flow = hasattr(self.accountManager, '_pending_login') and self.accountManager._pending_login
        
        if is_login_flow:
            # 在登录流程中使用恢复码 - 先完成登录
            try:
                # 临时设置，允许登录通过
                if username in self.accountManager.accounts['2fa_secrets']:
                    # 临时备份原始密钥
                    original_secret = self.accountManager.accounts['2fa_secrets'][username]
                    # 临时删除2FA要求，允许登录完成
                    del self.accountManager.accounts['2fa_secrets'][username]
                    
                    # 完成登录
                    success = self.accountManager.complete_two_factor_auth()
                    
                    if success:
                        # 登录成功后永久禁用2FA
                        self.accountManager.disable_2fa_after_recovery(username, used_hash)
                        InfoBar.success(
                            title="登录成功",
                            content="使用恢复码成功登录并禁用了两因素认证",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
                    else:
                        # 登录失败，恢复原始2FA密钥
                        self.accountManager.accounts['2fa_secrets'][username] = original_secret
                        InfoBar.warning(
                            title="登录未完成",
                            content="恢复码验证成功，但登录流程未完成，请重试",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
                else:
                    # 直接完成登录
                    success = self.accountManager.complete_two_factor_auth()
                    if success:
                        InfoBar.success(
                            title="登录成功",
                            content="使用恢复码成功登录",
                            orient=Qt.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
            except Exception as e:
                error(f"恢复码登录过程中出错: {str(e)}")
                InfoBar.error(
                    title="登录失败",
                    content=f"恢复码验证成功，但登录过程出错: {str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        else:
            # 非登录流程中使用恢复码 - 直接禁用2FA
            if self.accountManager.disable_2fa_after_recovery(username, used_hash):
                InfoBar.success(
                    title="已禁用2FA",
                    content="两因素认证已成功禁用",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="操作失败",
                    content="无法禁用两因素认证，请联系管理员",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
        
        # 更新界面显示
        self.updateAccountSelector()
        
    def onTwoFactorRecoveryFailed(self):
        """两因素认证恢复失败回调"""
        warning("两因素认证恢复失败")
        
        InfoBar.error(
            title="恢复失败",
            content="无法验证恢复码，请重试或联系管理员",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def updateAccountSelector(self):
        """更新账号选择器"""
        if not hasattr(self, 'accountSelector') or not self.accountSelector:
            return
            
        try:
            # 暂时阻塞信号，避免触发不必要的updateAccountDetails调用
            old_block_state = self.accountSelector.blockSignals(True)
            
            # 清空选择器
            self.accountSelector.clear()
            
            # 添加GitHub账号
            github_accounts = self.accountManager.get_github_accounts()
            for account in github_accounts:
                # 不直接使用 FluentIcon.GITHUB.icon() 而是转换为字符串
                self.accountSelector.addItem(
                    "GitHub", 
                    f"GitHub: {account['name']} ({account['username']})",
                    {'type': 'github', 'username': account['username']}
                )
                
            # 添加Gitee账号
            gitee_accounts = self.accountManager.get_gitee_accounts()
            for account in gitee_accounts:
                self.accountSelector.addItem(
                    "Gitee",
                    f"Gitee: {account['name']} ({account['username']})",
                    {'type': 'gitee', 'username': account['username']}
                )
                
            # 恢复信号状态
            self.accountSelector.blockSignals(old_block_state)
        except RuntimeError as e:
            error(f"更新账号选择器时发生运行时错误: {str(e)}")
        except Exception as e:
            error(f"更新账号选择器时发生异常: {str(e)}")
        
    def updateAccountDetails(self, index=None):
        """根据选中的账号更新详情显示"""
        if not hasattr(self, 'accountSelector') or not self.accountSelector:
            return
            
        try:
            # 检查选择器是否为空
            if self.accountSelector.count() == 0:
                self.detailTypeLabel.setText("")
                self.detailNameLabel.setText("")
                self.detailUsernameLabel.setText("")
                self.detailAddedLabel.setText("")
                self.detailLastUsedLabel.setText("")
                
                # 设置按钮状态
                if hasattr(self, 'loginSelectedBtn'):
                    self.loginSelectedBtn.setEnabled(False)
                if hasattr(self, 'renameSelectedBtn'):
                    self.renameSelectedBtn.setEnabled(False)
                if hasattr(self, 'removeSelectedBtn'):
                    self.removeSelectedBtn.setEnabled(False)
                return
                
            # 获取当前选中账号
            current_data = self.accountSelector.currentData()
            if not current_data:
                return
                
            account_type = current_data['type']
            username = current_data['username']
            
            # 查找账号详情
            account = None
            if account_type == 'github':
                accounts = self.accountManager.get_github_accounts()
                for acc in accounts:
                    if acc['username'] == username:
                        account = acc
                        break
            elif account_type == 'gitee':
                accounts = self.accountManager.get_gitee_accounts()
                for acc in accounts:
                    if acc['username'] == username:
                        account = acc
                        break
                        
            if not account:
                return
                
            # 安全地更新详情显示
            try:
                self.detailTypeLabel.setText(account_type.capitalize())
                self.detailNameLabel.setText(account['name'])
                self.detailUsernameLabel.setText(account['username'])
                
                # 添加时间
                added_at = datetime.fromisoformat(account['added_at']) if 'added_at' in account else None
                if added_at:
                    self.detailAddedLabel.setText(added_at.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    self.detailAddedLabel.setText("未知")
                    
                # 最后使用时间
                last_used = datetime.fromisoformat(account['last_used']) if 'last_used' in account else None
                if last_used:
                    self.detailLastUsedLabel.setText(last_used.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    self.detailLastUsedLabel.setText("未知")
            except Exception as e:
                error(f"更新账号详情标签时出错: {str(e)}")
                
            # 启用按钮
            try:
                if hasattr(self, 'loginSelectedBtn'):
                    self.loginSelectedBtn.setEnabled(True)
                if hasattr(self, 'renameSelectedBtn'):
                    self.renameSelectedBtn.setEnabled(True)
                if hasattr(self, 'removeSelectedBtn'):
                    self.removeSelectedBtn.setEnabled(True)
            except Exception as e:
                error(f"启用账号管理按钮时出错: {str(e)}")
        except Exception as e:
            error(f"更新账号详情时发生错误: {str(e)}")

from datetime import datetime
from PyQt5.QtCore import QUrl