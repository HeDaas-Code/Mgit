#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QLineEdit, QProgressBar, QScrollArea,
                           QWidget, QGridLayout, QCheckBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QClipboard
from qfluentwidgets import (LineEdit, PrimaryPushButton, InfoBar, 
                          InfoBarPosition, IconWidget, CardWidget)

from src.utils.two_factor_auth import TwoFactorAuth
from src.utils.logger import info, warning, error, debug

class TwoFactorSetupDialog(QDialog):
    """
    两因素认证设置对话框
    用于生成密钥和二维码，引导用户设置两因素认证
    """
    
    setupCompleted = pyqtSignal(str, list)  # 参数为设置的密钥和恢复码的哈希值列表
    
    def __init__(self, username, parent=None):
        """
        初始化两因素认证设置对话框
        
        Args:
            username: 用户名，用于生成二维码
            parent: 父窗口
        """
        super().__init__(parent)
        self.username = username
        self.twoFactorAuth = TwoFactorAuth(issuer="MGit")
        
        # 生成密钥
        self.secret_key = self.twoFactorAuth.generate_secret_key()
        
        # 生成恢复码
        self.recovery_codes = self.twoFactorAuth.generate_recovery_codes(count=8, code_length=10)
        self.hashed_recovery_codes = [self.twoFactorAuth.hash_recovery_code(code) for code in self.recovery_codes]
        
        # 初始化UI
        self.initUI()
        
        # 连接信号
        self.twoFactorAuth.qrCodeGenerated.connect(self.onQRCodeGenerated)
        
        # 生成二维码
        self.generateQRCode()
        
        # 设置提示刷新定时器
        self.setupTimer()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("设置两因素认证")
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        titleLabel = QLabel("设置两因素认证")
        titleLabel.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)
        
        # 说明
        infoLabel = QLabel(
            "两因素认证将提高您账号的安全性。请按照以下步骤设置：\n\n"
            "1. 安装身份验证器应用：\n"
            "   - Microsoft Authenticator\n"
            "   - Google Authenticator\n"
            "   - Authy 等\n\n"
            "2. 使用应用扫描下方二维码\n"
            "3. 输入验证器中生成的6位数验证码以完成设置\n\n"
            "注意：验证码每30秒刷新一次，请及时输入"
        )
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 二维码区域
        self.qrCodeLabel = QLabel()
        self.qrCodeLabel.setAlignment(Qt.AlignCenter)
        self.qrCodeLabel.setFixedSize(200, 200)
        self.qrCodeLabel.setStyleSheet("background-color: white; border: 1px solid #cccccc;")
        
        qrCodeLayout = QHBoxLayout()
        qrCodeLayout.addStretch()
        qrCodeLayout.addWidget(self.qrCodeLabel)
        qrCodeLayout.addStretch()
        layout.addLayout(qrCodeLayout)
        
        # 密钥展示
        keyLayout = QHBoxLayout()
        keyLayout.addWidget(QLabel("密钥:"))
        
        self.keyLabel = QLabel(self.formatSecretKey(self.secret_key))
        self.keyLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        keyLayout.addWidget(self.keyLabel)
        
        refreshBtn = QPushButton()
        refreshBtn.setIcon(QIcon(":/qfluentwidgets/images/refresh_line.svg"))
        refreshBtn.setToolTip("生成新密钥")
        refreshBtn.clicked.connect(self.regenerateKey)
        keyLayout.addWidget(refreshBtn)
        
        layout.addLayout(keyLayout)
        
        # 验证码输入
        validationLayout = QHBoxLayout()
        validationLayout.addWidget(QLabel("验证码:"))
        
        self.verificationCodeEdit = LineEdit()
        self.verificationCodeEdit.setPlaceholderText("6位验证码")
        self.verificationCodeEdit.setMaxLength(6)
        # 按回车键验证
        self.verificationCodeEdit.returnPressed.connect(self.verifyAndSave)
        validationLayout.addWidget(self.verificationCodeEdit)
        
        layout.addLayout(validationLayout)
        
        # 计时器显示
        timerLayout = QHBoxLayout()
        timerLayout.addWidget(QLabel("有效期:"))
        
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 30)
        self.progressBar.setValue(30)
        timerLayout.addWidget(self.progressBar)
        
        self.countdownLabel = QLabel("30秒")
        timerLayout.addWidget(self.countdownLabel)
        
        layout.addLayout(timerLayout)
        
        # 提示信息
        self.statusLabel = QLabel()
        self.statusLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.statusLabel)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        self.cancelBtn = QPushButton("取消")
        self.cancelBtn.clicked.connect(self.reject)
        btnLayout.addWidget(self.cancelBtn)
        
        self.verifyBtn = PrimaryPushButton("验证并启用")
        self.verifyBtn.clicked.connect(self.verifyAndSave)
        btnLayout.addWidget(self.verifyBtn)
        
        layout.addLayout(btnLayout)
        
        # 一些重要提示
        noteLabel = QLabel(
            "重要提示：请务必保存好您的密钥和备份验证器应用，\n"
            "否则可能导致无法登录账号。"
        )
        noteLabel.setStyleSheet("color: #e74c3c;")
        noteLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(noteLabel)
        
    def formatSecretKey(self, key):
        """格式化密钥，增加可读性"""
        formatted = ""
        for i in range(0, len(key), 4):
            formatted += key[i:i+4] + " "
        return formatted.strip()
        
    def generateQRCode(self):
        """生成二维码"""
        self.twoFactorAuth.generate_qrcode(self.username, self.secret_key)
        
    def onQRCodeGenerated(self, pixmap):
        """二维码生成完成回调"""
        self.qrCodeLabel.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
    def regenerateKey(self):
        """重新生成密钥"""
        self.secret_key = self.twoFactorAuth.generate_secret_key()
        self.keyLabel.setText(self.formatSecretKey(self.secret_key))
        self.generateQRCode()
        
    def setupTimer(self):
        """设置TOTP计时器"""
        self.timer = QTimer(self)
        # 更高的更新频率，每300毫秒更新一次，提供更精确的倒计时体验
        self.timer.timeout.connect(self.updateCountdown)
        self.timer.start(300)  # 更频繁地更新倒计时，减少误差
        self.updateCountdown()
        
    def updateCountdown(self):
        """更新TOTP倒计时"""
        remaining = self.twoFactorAuth.get_remaining_seconds()
        
        # 显示当前计数器值，便于调试
        counter = self.twoFactorAuth.get_current_counter()
        
        # 显示毫秒级精度，更直观地看到倒计时
        self.progressBar.setValue(remaining)
        
        # 当验证码即将过期时，刷新显示样式并更快地更新UI
        if remaining <= 5:
            self.progressBar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            self.countdownLabel.setText(f"{remaining}秒")
            
            # 在最后5秒时，增加visual hints提醒用户
            font = self.countdownLabel.font()
            font.setBold(True)
            self.countdownLabel.setFont(font)
            self.countdownLabel.setStyleSheet("color: #e74c3c;")
        else:
            self.progressBar.setStyleSheet("")
            self.countdownLabel.setText(f"{remaining}秒")
            
            # 恢复正常字体
            font = self.countdownLabel.font()
            font.setBold(False)
            self.countdownLabel.setFont(font)
            self.countdownLabel.setStyleSheet("")
            
        # 如果即将生成新验证码（剩余时间≤2秒），提示用户可能需要等待新代码
        if remaining <= 2:
            self.statusLabel.setText("即将生成新验证码，请稍候...")
            self.statusLabel.setStyleSheet("color: #f39c12;")
        elif not self.statusLabel.text() or self.statusLabel.text() == "即将生成新验证码，请稍候...":
            self.statusLabel.setText("")
            
    def verifyAndSave(self):
        """验证并保存密钥"""
        code = self.verificationCodeEdit.text().strip()
        
        if not code or len(code) != 6:
            self.statusLabel.setText("请输入6位验证码")
            self.statusLabel.setStyleSheet("color: #e74c3c;")
            return
        
        # 获取当前剩余时间
        remaining = self.twoFactorAuth.get_remaining_seconds()
            
        # 如果剩余时间很短（小于3秒），增加验证窗口
        valid_window = 2 if remaining <= 3 else 1
            
        if self.twoFactorAuth.verify_totp(self.secret_key, code, valid_window):
            self.statusLabel.setText("验证成功！两因素认证已启用")
            self.statusLabel.setStyleSheet("color: #2ecc71;")
            
            # 禁用输入和按钮，防止重复验证
            self.verificationCodeEdit.setEnabled(False)
            self.verifyBtn.setEnabled(False)
            self.cancelBtn.setText("关闭")
            
            # 显示恢复码对话框
            self.showRecoveryCodes()
            
            # 发出设置完成信号
            self.setupCompleted.emit(self.secret_key, self.hashed_recovery_codes)
            
            # 短暂延迟后关闭对话框
            QTimer.singleShot(1500, self.accept)
        else:
            # 如果剩余时间很短，给出更友好的提示
            if remaining <= 3:
                self.statusLabel.setText("验证失败，即将生成新验证码，请重新输入新的验证码")
            else:
                self.statusLabel.setText("验证码无效，请重试")
            self.statusLabel.setStyleSheet("color: #e74c3c;")
            self.verificationCodeEdit.clear()
            self.verificationCodeEdit.setFocus()
            
    def showRecoveryCodes(self):
        """显示恢复码对话框"""
        dialog = RecoveryCodesDialog(self.recovery_codes, self)
        dialog.exec_()
        
class TwoFactorVerifyDialog(QDialog):
    """
    两因素认证验证对话框
    用于验证用户输入的两因素认证代码
    """
    
    verificationSuccess = pyqtSignal()
    verificationFailed = pyqtSignal()
    recoveryRequested = pyqtSignal(str)  # 发出恢复请求信号，参数为用户名
    
    def __init__(self, secret_key, username=None, parent=None):
        """
        初始化两因素认证验证对话框
        
        Args:
            secret_key: Base32编码的密钥
            username: 用户名，用于恢复流程
            parent: 父窗口
        """
        super().__init__(parent)
        self.secret_key = secret_key
        self.username = username
        self.twoFactorAuth = TwoFactorAuth()
        self.attempt_count = 0
        self.max_attempts = 3
        
        # 初始化UI
        self.initUI()
        
        # 设置提示刷新定时器
        self.setupTimer()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("两因素认证")
        self.resize(350, 230)  # 增加高度以容纳恢复按钮
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题，不使用图标
        titleLabel = QLabel("两因素认证")
        titleLabel.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)
        
        # 说明
        infoLabel = QLabel("请输入验证器应用中生成的6位验证码")
        infoLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(infoLabel)
        
        # 验证码输入
        self.codeEdit = LineEdit()
        self.codeEdit.setPlaceholderText("6位验证码")
        self.codeEdit.setMaxLength(6)
        self.codeEdit.returnPressed.connect(self.verifyCode)
        layout.addWidget(self.codeEdit)
        
        # 计时器显示
        timerLayout = QHBoxLayout()
        timerLayout.addWidget(QLabel("有效期:"))
        
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 30)
        self.progressBar.setValue(30)
        timerLayout.addWidget(self.progressBar)
        
        self.countdownLabel = QLabel("30秒")
        timerLayout.addWidget(self.countdownLabel)
        
        layout.addLayout(timerLayout)
        
        # 提示信息
        self.statusLabel = QLabel()
        self.statusLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.statusLabel)
        
        # 恢复按钮
        if self.username:  # 只有当提供了用户名时才显示恢复选项
            recoveryLayout = QHBoxLayout()
            self.recoveryBtn = QPushButton("使用恢复码")
            self.recoveryBtn.clicked.connect(self.requestRecovery)
            recoveryLayout.addStretch()
            recoveryLayout.addWidget(self.recoveryBtn)
            recoveryLayout.addStretch()
            layout.addLayout(recoveryLayout)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        self.cancelBtn = QPushButton("取消")
        self.cancelBtn.clicked.connect(self.reject)
        btnLayout.addWidget(self.cancelBtn)
        
        self.verifyBtn = PrimaryPushButton("验证")
        self.verifyBtn.clicked.connect(self.verifyCode)
        btnLayout.addWidget(self.verifyBtn)
        
        layout.addLayout(btnLayout)
        
    def setupTimer(self):
        """设置TOTP计时器"""
        self.timer = QTimer(self)
        # 更高的更新频率，每300毫秒更新一次，提供更精确的倒计时体验
        self.timer.timeout.connect(self.updateCountdown)
        self.timer.start(300)  # 更频繁地更新倒计时，减少误差
        self.updateCountdown()
        
    def updateCountdown(self):
        """更新TOTP倒计时"""
        remaining = self.twoFactorAuth.get_remaining_seconds()
        
        # 显示当前计数器值，便于调试
        counter = self.twoFactorAuth.get_current_counter()
        
        # 显示毫秒级精度，更直观地看到倒计时
        self.progressBar.setValue(remaining)
        
        # 当验证码即将过期时，刷新显示样式并更快地更新UI
        if remaining <= 5:
            self.progressBar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
            self.countdownLabel.setText(f"{remaining}秒")
            
            # 在最后5秒时，增加visual hints提醒用户
            font = self.countdownLabel.font()
            font.setBold(True)
            self.countdownLabel.setFont(font)
            self.countdownLabel.setStyleSheet("color: #e74c3c;")
        else:
            self.progressBar.setStyleSheet("")
            self.countdownLabel.setText(f"{remaining}秒")
            
            # 恢复正常字体
            font = self.countdownLabel.font()
            font.setBold(False)
            self.countdownLabel.setFont(font)
            self.countdownLabel.setStyleSheet("")
            
        # 如果即将生成新验证码（剩余时间≤2秒），提示用户可能需要等待新代码
        if remaining <= 2:
            self.statusLabel.setText("即将生成新验证码，请稍候...")
            self.statusLabel.setStyleSheet("color: #f39c12;")
        elif not self.statusLabel.text() or self.statusLabel.text() == "即将生成新验证码，请稍候...":
            self.statusLabel.setText("")
            
    def verifyCode(self):
        """验证输入的代码"""
        code = self.codeEdit.text().strip()
        
        if not code or len(code) != 6:
            self.statusLabel.setText("请输入6位验证码")
            self.statusLabel.setStyleSheet("color: #e74c3c;")
            return
            
        self.attempt_count += 1
        
        # 获取当前剩余时间
        remaining = self.twoFactorAuth.get_remaining_seconds()
        
        # 如果剩余时间很短（小于3秒），增加验证窗口，减少时间误差带来的影响
        # 即：如果在周期边界附近，增加验证窗口以提高成功率
        valid_window = 2 if remaining <= 3 else 1
        
        if self.twoFactorAuth.verify_totp(self.secret_key, code, valid_window):
            self.statusLabel.setText("验证成功")
            self.statusLabel.setStyleSheet("color: #2ecc71;")
            
            # 发出验证成功信号
            self.verificationSuccess.emit()
            
            # 禁用输入和按钮，防止重复验证
            self.codeEdit.setEnabled(False)
            self.verifyBtn.setEnabled(False)
            self.cancelBtn.setText("关闭")
            
            # 短暂延迟后关闭对话框
            QTimer.singleShot(1000, self.accept)
        else:
            # 验证失败
            remaining_attempts = self.max_attempts - self.attempt_count
            
            # 如果剩余时间很短，给出更友好的提示
            if remaining <= 3:
                self.statusLabel.setText(f"验证失败，即将生成新验证码，请重新输入新的验证码")
                self.statusLabel.setStyleSheet("color: #e74c3c;")
                # 不计入尝试次数
                self.attempt_count -= 1
            elif remaining_attempts > 0:
                self.statusLabel.setText(f"验证码无效，还有{remaining_attempts}次尝试机会")
                self.statusLabel.setStyleSheet("color: #e74c3c;")
            else:
                self.statusLabel.setText("验证失败次数过多")
                self.statusLabel.setStyleSheet("color: #e74c3c;")
                
                # 发出验证失败信号
                self.verificationFailed.emit()
                
                # 禁用验证按钮
                self.verifyBtn.setEnabled(False)
                
                # 短暂延迟后关闭对话框
                QTimer.singleShot(2000, self.reject)
                
            self.codeEdit.clear()
            self.codeEdit.setFocus() 

    def requestRecovery(self):
        """请求使用恢复码"""
        if self.username:
            self.recoveryRequested.emit(self.username)
            self.accept()  # 关闭当前对话框

class RecoveryCodesDialog(QDialog):
    """
    显示恢复码对话框
    用于在设置2FA时显示恢复码，并提供打印和复制功能
    """
    
    def __init__(self, recovery_codes, parent=None):
        """
        初始化恢复码对话框
        
        Args:
            recovery_codes: 恢复码列表
            parent: 父窗口
        """
        super().__init__(parent)
        self.recovery_codes = recovery_codes
        self.clipboard = QApplication.clipboard()
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("备份恢复码")
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        titleLabel = QLabel("备份恢复码")
        titleLabel.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)
        
        # 说明
        infoLabel = QLabel(
            "这些是您的账号恢复码。请将它们保存在安全的地方。\n\n"
            "如果您无法访问您的验证器应用，可以使用这些一次性恢复码登录。\n\n"
            "每个恢复码仅能使用一次。"
        )
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 恢复码卡片
        codesCard = CardWidget()
        codesLayout = QVBoxLayout(codesCard)
        
        # 恢复码
        for i, code in enumerate(self.recovery_codes):
            codeLayout = QHBoxLayout()
            
            # 恢复码标签
            codeLabel = QLabel(f"{i+1}. {code}")
            codeLabel.setFont(QFont("Consolas", 10))
            codeLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
            codeLayout.addWidget(codeLabel)
            
            # 复制按钮
            copyBtn = QPushButton("复制")
            copyBtn.setFixedWidth(50)
            copyBtn.clicked.connect(lambda checked, c=code: self.copyCode(c))
            codeLayout.addWidget(copyBtn)
            
            codesLayout.addLayout(codeLayout)
            
        layout.addWidget(codesCard)
        
        # 警告信息
        warningLabel = QLabel(
            "警告：如果您丢失了验证器应用和恢复码，您将无法访问您的账号！\n"
            "请立即保存这些恢复码。"
        )
        warningLabel.setStyleSheet("color: #e74c3c;")
        warningLabel.setWordWrap(True)
        layout.addWidget(warningLabel)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        # 复制全部按钮
        copyAllBtn = QPushButton("复制全部")
        copyAllBtn.clicked.connect(self.copyAllCodes)
        btnLayout.addWidget(copyAllBtn)
        
        # 打印按钮
        printBtn = QPushButton("打印")
        printBtn.clicked.connect(self.printCodes)
        btnLayout.addWidget(printBtn)
        
        # 确认按钮
        self.confirmBtn = PrimaryPushButton("我已保存恢复码")
        self.confirmBtn.clicked.connect(self.accept)
        btnLayout.addWidget(self.confirmBtn)
        
        layout.addLayout(btnLayout)
        
    def copyCode(self, code):
        """复制单个恢复码到剪贴板"""
        self.clipboard.setText(code)
        InfoBar.success(
            title="已复制",
            content=f"恢复码已复制到剪贴板",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def copyAllCodes(self):
        """复制所有恢复码到剪贴板"""
        all_codes = "\n".join([f"{i+1}. {code}" for i, code in enumerate(self.recovery_codes)])
        self.clipboard.setText(all_codes)
        InfoBar.success(
            title="已复制全部",
            content="所有恢复码已复制到剪贴板",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        
    def printCodes(self):
        """打印恢复码"""
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            
            printer = QPrinter()
            dlg = QPrintDialog(printer, self)
            
            if dlg.exec_() == QDialog.Accepted:
                # 创建打印文档
                document = QTextDocument()
                html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial; }}
                        h1 {{ text-align: center; }}
                        .code {{ font-family: Consolas, monospace; padding: 5px; margin: 5px; border: 1px solid #ccc; }}
                        .warning {{ color: red; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <h1>两因素认证恢复码</h1>
                    <p>如果您无法访问验证器应用，可以使用这些一次性恢复码登录。<br>
                    每个恢复码仅能使用一次。</p>
                    <div class="codes">
                """
                
                for i, code in enumerate(self.recovery_codes):
                    html += f'<div class="code">{i+1}. {code}</div>\n'
                    
                html += """
                    </div>
                    <p class="warning">警告：如果您丢失了验证器应用和恢复码，您将无法访问您的账号！</p>
                </body>
                </html>
                """
                
                document.setHtml(html)
                document.print_(printer)
                
                InfoBar.success(
                    title="打印成功",
                    content="恢复码已发送到打印机",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        except ImportError:
            InfoBar.warning(
                title="无法打印",
                content="打印功能不可用",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

class TwoFactorRecoveryDialog(QDialog):
    """
    两因素认证恢复对话框
    用于当用户无法使用验证器应用时，通过恢复码禁用2FA
    """
    
    recoverySuccess = pyqtSignal(str, str)  # 参数: 用户名, 已使用的恢复码哈希
    recoveryFailed = pyqtSignal()
    
    def __init__(self, username, parent=None):
        """
        初始化两因素认证恢复对话框
        
        Args:
            username: 需要恢复的用户名
            parent: 父窗口
        """
        super().__init__(parent)
        self.username = username
        self.attempt_count = 0
        self.max_attempts = 3
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("恢复两因素认证")
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        titleLabel = QLabel("使用恢复码")
        titleLabel.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(titleLabel)
        
        # 说明
        infoLabel = QLabel(
            f"请输入您在设置两因素认证时保存的恢复码之一。\n\n"
            f"使用恢复码将会禁用您账号 ({self.username}) 的两因素认证。\n"
            f"每个恢复码只能使用一次。"
        )
        infoLabel.setWordWrap(True)
        layout.addWidget(infoLabel)
        
        # 恢复码输入
        self.recoveryCodeEdit = LineEdit()
        self.recoveryCodeEdit.setPlaceholderText("输入恢复码，格式如：XXXX-XXXX-XXXX")
        layout.addWidget(self.recoveryCodeEdit)
        
        # 提示信息
        self.statusLabel = QLabel()
        self.statusLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.statusLabel)
        
        # 按钮区域
        btnLayout = QHBoxLayout()
        
        self.cancelBtn = QPushButton("取消")
        self.cancelBtn.clicked.connect(self.reject)
        btnLayout.addWidget(self.cancelBtn)
        
        self.verifyBtn = PrimaryPushButton("验证并禁用2FA")
        self.verifyBtn.clicked.connect(self.verifyAndDisable)
        btnLayout.addWidget(self.verifyBtn)
        
        layout.addLayout(btnLayout)
        
    def verifyAndDisable(self):
        """验证恢复码并禁用2FA"""
        recovery_code = self.recoveryCodeEdit.text().strip()
        
        if not recovery_code:
            self.statusLabel.setText("请输入恢复码")
            self.statusLabel.setStyleSheet("color: #e74c3c;")
            return
            
        self.attempt_count += 1
        
        # 从账户管理器获取验证方法
        from src.utils.enhanced_account_manager import EnhancedAccountManager
        account_manager = EnhancedAccountManager()
        
        # 验证恢复码，但不立即禁用2FA
        is_valid, used_hash = account_manager.verify_recovery_code(self.username, recovery_code)
        
        if is_valid and used_hash:
            self.statusLabel.setText("验证成功！准备完成登录并禁用两因素认证")
            self.statusLabel.setStyleSheet("color: #2ecc71;")
            
            # 发出恢复成功信号，携带用户名和恢复码哈希
            self.recoverySuccess.emit(self.username, used_hash)
            
            # 禁用输入和按钮
            self.recoveryCodeEdit.setEnabled(False)
            self.verifyBtn.setEnabled(False)
            self.cancelBtn.setText("关闭")
            
            # 短暂延迟后关闭对话框
            QTimer.singleShot(2000, self.accept)
        else:
            # 验证失败
            remaining_attempts = self.max_attempts - self.attempt_count
            
            if remaining_attempts > 0:
                self.statusLabel.setText(f"恢复码无效，还有{remaining_attempts}次尝试机会")
                self.statusLabel.setStyleSheet("color: #e74c3c;")
                self.recoveryCodeEdit.clear()
                self.recoveryCodeEdit.setFocus()
            else:
                self.statusLabel.setText("验证失败次数过多")
                self.statusLabel.setStyleSheet("color: #e74c3c;")
                
                # 发出恢复失败信号
                self.recoveryFailed.emit()
                
                # 禁用验证按钮
                self.verifyBtn.setEnabled(False)
                
                # 短暂延迟后关闭对话框
                QTimer.singleShot(2000, self.reject) 