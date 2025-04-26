#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import base64
import time
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timedelta
import requests
import urllib3
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PyQt5.QtCore import QObject, pyqtSignal, QByteArray
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QUrl

# 导入日志工具
from src.utils.logger import info, warning, error, critical, debug

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EnhancedAccountManager(QObject):
    """
    增强的账号管理器，支持：
    1. 账号本地加密存储
    2. 自动登录
    3. 多账号切换
    4. 头像加载和缓存
    5. 支持GitHub OAuth和Gitee Token认证
    6. 两因素认证(2FA)支持
    7. 2FA恢复码支持
    """
    
    # 定义信号
    accountsChanged = pyqtSignal()  # 账号列表变化信号
    loginSuccess = pyqtSignal(dict)  # 登录成功信号，传递账号信息
    loginFailed = pyqtSignal(str)    # 登录失败信号，传递错误信息
    autoLoginStarted = pyqtSignal()  # 自动登录开始信号
    avatarLoaded = pyqtSignal(str, QPixmap)  # 头像加载完成信号，参数：用户名，头像
    twoFactorRequired = pyqtSignal(str)  # 需要两因素验证信号，参数：密钥
    
    def __init__(self, config_dir=None):
        """
        初始化账号管理器
        
        Args:
            config_dir: 配置目录，默认为用户目录下的.mgit
        """
        super().__init__()
        
        self.current_account = None
        self.avatar_cache = {}  # 用户名 -> QPixmap
        
        # 设置配置目录
        if config_dir is None:
            home_dir = str(Path.home())
            self.config_dir = os.path.join(home_dir, '.mgit')
        else:
            self.config_dir = config_dir
            
        # 确保目录存在
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # 账号和密钥文件路径
        self.accounts_file = os.path.join(self.config_dir, 'encrypted_accounts.dat')
        self.key_file = os.path.join(self.config_dir, 'key.dat')
        
        # 默认账号配置
        self.accounts = {
            'github': [],
            'gitee': [],  # 新增对Gitee的支持
            'last_login': None,  # 记录最后登录的账号
            'auto_login': True,  # 自动登录开关
            '2fa_enabled': False,  # 二次验证开关
            '2fa_secrets': {},  # 二次验证密钥 username -> secret_key
            '2fa_recovery_codes': {}  # 二次验证恢复码 username -> [hashed_code1, hashed_code2, ...]
        }
        
        # 初始化加密工具
        self._init_encryption()
        
        # 网络访问管理器（用于加载头像）
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._handle_avatar_response)
        
        # 初始加载账号数据
        self.load_accounts()
        
    def _init_encryption(self):
        """初始化加密工具，生成或加载密钥"""
        try:
            if os.path.exists(self.key_file):
                # 加载现有密钥
                with open(self.key_file, 'rb') as f:
                    self.key = f.read()
            else:
                # 生成新密钥
                self.key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(self.key)
                    
            # 创建Fernet实例
            self.fernet = Fernet(self.key)
        except Exception as e:
            error(f"初始化加密工具失败: {str(e)}")
            # 如果出错，创建新的密钥
            self._recreate_encryption_key()
            
    def _recreate_encryption_key(self):
        """重新创建加密密钥"""
        try:
            info("重新创建加密密钥")
            # 备份原文件（如果存在）
            if os.path.exists(self.key_file):
                backup_file = f"{self.key_file}.bak.{int(time.time())}"
                os.rename(self.key_file, backup_file)
                info(f"原密钥已备份为: {backup_file}")
                
            if os.path.exists(self.accounts_file):
                backup_file = f"{self.accounts_file}.bak.{int(time.time())}"
                os.rename(self.accounts_file, backup_file)
                info(f"原账号文件已备份为: {backup_file}")
                
            # 生成新密钥
            self.key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.key)
                
            # 创建Fernet实例
            self.fernet = Fernet(self.key)
            
            # 重置账号数据
            self.accounts = {
                'github': [],
                'gitee': [],
                'last_login': None,
                'auto_login': True,
                '2fa_enabled': False,
                '2fa_secrets': {},
                '2fa_recovery_codes': {}
            }
            
            # 保存重置后的账号数据
            self.save_accounts()
            info("加密密钥和账号数据重置成功")
        except Exception as e:
            critical(f"重新创建加密密钥失败: {str(e)}")
            # 如果仍然失败，使用内存中的默认值继续运行
            self.key = Fernet.generate_key()
            self.fernet = Fernet(self.key)
            
    def load_accounts(self):
        """从加密文件加载账号信息"""
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'rb') as f:
                    encrypted_data = f.read()
                    
                try:
                    # 尝试解密数据
                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    loaded_accounts = json.loads(decrypted_data.decode('utf-8'))
                    
                    # 更新配置，但保留默认值
                    self.accounts.update(loaded_accounts)
                    info("账号数据加载成功")
                    
                    # 触发自动登录检查
                    if self.accounts['auto_login'] and self.accounts['last_login']:
                        self.autoLoginStarted.emit()
                except InvalidToken as e:
                    warning(f"账号文件解密失败，可能密钥不匹配: {str(e)}")
                    self._recreate_encryption_key()
        except Exception as e:
            error(f"加载账号数据失败: {str(e)}")
            
    def save_accounts(self):
        """加密保存账号信息"""
        try:
            # 序列化账号数据
            json_data = json.dumps(self.accounts, ensure_ascii=False)
            
            # 加密数据
            encrypted_data = self.fernet.encrypt(json_data.encode('utf-8'))
            
            # 保存加密数据
            with open(self.accounts_file, 'wb') as f:
                f.write(encrypted_data)
                
            # 发出信号通知账号列表已更新
            self.accountsChanged.emit()
            debug("账号数据保存成功")
        except Exception as e:
            error(f"保存账号数据失败: {str(e)}")
            
    def get_github_accounts(self):
        """获取GitHub账号列表"""
        return self.accounts['github']
        
    def get_gitee_accounts(self):
        """获取Gitee账号列表"""
        return self.accounts['gitee']
        
    def add_github_account_oauth(self, code, client_id, client_secret, name=None):
        """
        通过OAuth方式添加GitHub账号
        
        Args:
            code: 从GitHub OAuth回调中获取的授权码
            client_id: GitHub OAuth应用的Client ID
            client_secret: GitHub OAuth应用的Client Secret
            name: 账号别名，默认为用户名
        
        Returns:
            bool: 是否添加成功
        """
        try:
            # 使用授权码获取访问令牌
            response = requests.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code
                },
                headers={'Accept': 'application/json'},
                verify=False  # 禁用SSL证书验证
            )
            
            if response.status_code != 200:
                error(f"获取GitHub访问令牌失败: {response.status_code} - {response.text}")
                return False
            
            # 解析响应获取访问令牌
            data = response.json()
            if 'access_token' not in data:
                error(f"GitHub OAuth响应中未找到访问令牌: {data}")
                return False
            
            token = data['access_token']
            
            # 获取用户信息
            user_response = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {token}'},
                verify=False  # 禁用SSL证书验证
            )
            
            if user_response.status_code != 200:
                error(f"获取GitHub用户信息失败: {user_response.status_code} - {user_response.text}")
                return False
            
            user_data = user_response.json()
            username = user_data.get('login')
            avatar_url = user_data.get('avatar_url')
            
            if not username:
                error("GitHub用户信息中未找到用户名")
                return False
            
            # 如果未提供别名，使用用户名
            if name is None:
                name = username
            
            # 获取当前时间作为添加时间
            now = datetime.now().isoformat()
            
            # 检查是否已存在该账号，如果存在则更新
            account_exists = False
            for account in self.accounts['github']:
                if account['username'] == username:
                    account_exists = True
                    account.update({
                        'token': token,
                        'name': name,
                        'avatar_url': avatar_url,
                        'last_used': now
                    })
                    break
            
            # 如果不存在则添加新账号
            if not account_exists:
                new_account = {
                    'username': username,
                    'token': token,
                    'name': name,
                    'avatar_url': avatar_url,
                    'added_at': now,
                    'last_used': now
                }
                self.accounts['github'].append(new_account)
            
            # 保存账号信息
            self.save_accounts()
            
            # 加载头像
            if avatar_url:
                self._load_avatar(username, avatar_url)
            
            # 设置为当前账号并触发登录成功信号
            self.current_account = {
                'type': 'github',
                'data': self.accounts['github'][-1] if not account_exists else next(acc for acc in self.accounts['github'] if acc['username'] == username)
            }
            
            # 更新最后登录的账号记录
            self.accounts['last_login'] = {
                'type': 'github',
                'username': username
            }
            
            # 保存账号更新
            self.save_accounts()
            
            # 发出登录成功信号
            self.loginSuccess.emit(self.current_account)
            
            return True
        except Exception as e:
            error(f"通过OAuth添加GitHub账号时出错: {str(e)}")
            return False
            
    def add_gitee_account(self, username, token, name=None):
        """
        添加Gitee账号
        
        Args:
            username: Gitee用户名，如为None则从API获取
            token: Gitee访问令牌
            name: 账号别名，默认为用户名
        
        Returns:
            bool: 是否添加成功
        """
        try:
            # 验证令牌和获取用户信息
            headers = {'Authorization': f'token {token}'}
            response = requests.get('https://gitee.com/api/v5/user', headers=headers, verify=False)
            
            if response.status_code != 200:
                error(f"Gitee令牌验证失败: {response.status_code} - {response.text}")
                return False
                
            user_data = response.json()
            if not username:
                username = user_data.get('login')
            elif username != user_data.get('login'):
                warning(f"提供的用户名 {username} 与API返回的 {user_data.get('login')} 不匹配")
                username = user_data.get('login')
                
            avatar_url = user_data.get('avatar_url')
            
            # 如果未提供别名，使用用户名
            if name is None:
                name = username
                
            # 获取当前时间作为添加时间
            now = datetime.now().isoformat()
            
            # 检查是否已存在该账号，如果存在则更新
            account_exists = False
            for account in self.accounts['gitee']:
                if account['username'] == username:
                    account_exists = True
                    account.update({
                        'token': token,
                        'name': name,
                        'avatar_url': avatar_url,
                        'last_used': now
                    })
                    break
            
            # 如果不存在则添加新账号
            if not account_exists:
                new_account = {
                    'username': username,
                    'token': token,
                    'name': name,
                    'avatar_url': avatar_url,
                    'added_at': now,
                    'last_used': now
                }
                self.accounts['gitee'].append(new_account)
            
            # 保存账号信息
            self.save_accounts()
            
            # 加载头像
            if avatar_url:
                self._load_avatar(username, avatar_url)
            
            # 设置为当前账号并触发登录成功信号
            self.current_account = {
                'type': 'gitee',
                'data': self.accounts['gitee'][-1] if not account_exists else next(acc for acc in self.accounts['gitee'] if acc['username'] == username)
            }
            
            # 更新最后登录的账号记录
            self.accounts['last_login'] = {
                'type': 'gitee',
                'username': username
            }
            
            # 保存账号更新
            self.save_accounts()
            
            # 发出登录成功信号
            self.loginSuccess.emit(self.current_account)
            
            return True
        except Exception as e:
            error(f"添加Gitee账号失败: {str(e)}")
            return False
            
    def login_with_account(self, account_type, username):
        """
        使用指定账号登录
        
        Args:
            account_type: 账号类型 ('github' 或 'gitee')
            username: 用户名
            
        Returns:
            bool: 是否登录成功
        """
        try:
            if account_type not in ['github', 'gitee']:
                error(f"不支持的账号类型: {account_type}")
                self.loginFailed.emit(f"登录失败: 不支持的账号类型 {account_type}")
                return False
                
            # 查找账号
            accounts = self.accounts[account_type]
            for account in accounts:
                if account['username'] == username:
                    # 检查是否需要两因素认证
                    if self.accounts['2fa_enabled'] and username in self.accounts['2fa_secrets']:
                        # 记录待处理的登录信息
                        self._pending_login = {'type': account_type, 'data': account}
                        info(f"账号 {username} 需要双因素验证，已保存待处理登录信息")
                        
                        # 获取2FA密钥并触发验证流程
                        secret_key = self.accounts['2fa_secrets'][username]
                        self.twoFactorRequired.emit(secret_key)
                        
                        # 返回True表示处理继续，但实际登录会在验证完成后进行
                        return True
                        
                    # 如果不需要2FA，直接完成登录
                    info(f"不需要双因素验证，直接登录: {account_type}/{username}")
                    
                    # 更新最后使用时间
                    account['last_used'] = datetime.now().isoformat()
                    
                    # 设置为当前账号
                    self.current_account = {'type': account_type, 'data': account}
                    self.accounts['last_login'] = {'type': account_type, 'username': username}
                    
                    # 保存更改
                    self.save_accounts()
                    
                    # 加载头像
                    self._load_avatar(username, account.get('avatar_url', ''))
                    
                    # 发出登录成功信号
                    self.loginSuccess.emit(self.current_account)
                    
                    return True
                    
            error(f"找不到账号: {account_type}/{username}")
            self.loginFailed.emit(f"登录失败: 找不到账号 {username}")
            return False
        except Exception as e:
            error(f"登录账号失败: {str(e)}")
            self.loginFailed.emit(f"登录失败: {str(e)}")
            return False
            
    def complete_two_factor_auth(self):
        """
        完成两因素认证，继续登录流程
        在两因素认证成功后调用
        
        Returns:
            bool: 是否成功完成登录
        """
        if not hasattr(self, '_pending_login') or not self._pending_login:
            info("没有待处理的登录信息，无法完成双因素验证")
            return False
        
        try:
            # 获取待处理的登录信息
            account_type = self._pending_login['type']
            account = self._pending_login['data']
            username = account['username']
            
            # 记录登录状态
            info(f"完成双因素验证，继续登录流程: {account_type}/{username}")
            
            # 更新最后使用时间
            account['last_used'] = datetime.now().isoformat()
            
            # 设置为当前账号
            self.current_account = self._pending_login
            self.accounts['last_login'] = {'type': account_type, 'username': username}
            
            # 保存更改
            self.save_accounts()
            
            # 加载头像
            self._load_avatar(username, account.get('avatar_url', ''))
            
            # 发出登录成功信号
            self.loginSuccess.emit(self.current_account)
            
            # 清除待处理登录
            pending_login_backup = self._pending_login
            self._pending_login = None
            
            return True
        except Exception as e:
            error(f"完成双因素验证失败: {str(e)}")
            
            # 保留待处理登录信息，以便后续重试
            if hasattr(self, '_pending_login') and self._pending_login:
                # 记录重试次数
                if not hasattr(self, '_2fa_retry_count'):
                    self._2fa_retry_count = 0
                self._2fa_retry_count += 1
                
                # 最多重试3次
                if self._2fa_retry_count >= 3:
                    self._pending_login = None
                    self._2fa_retry_count = 0
                    error("两因素验证重试次数过多，已清除待处理登录")
                    
            return False
            
    def auto_login(self):
        """
        尝试自动登录
        如果有上次登录的账号，自动登录该账号
        """
        # 发出自动登录开始信号
        self.autoLoginStarted.emit()
        
        # 检查是否启用自动登录
        if not self.accounts['auto_login']:
            info("自动登录已禁用")
            return False
        
        # 检查是否有上次登录的账号
        if not self.accounts['last_login']:
            info("没有上次登录记录，无法自动登录")
            return False
        
        # 获取上次登录的账号信息
        account_type = self.accounts['last_login']['type']
        username = self.accounts['last_login']['username']
        
        info(f"开始自动登录: {account_type}/{username}")
        
        # 检查是否需要双因素认证
        needs_2fa = False
        if self.accounts['2fa_enabled'] and username in self.accounts['2fa_secrets']:
            info(f"账号 {username} 需要双因素认证")
            needs_2fa = True
        
        # 使用账号登录
        if self.login_with_account(account_type, username):
            if needs_2fa:
                info(f"自动登录触发了双因素认证流程")
            else:
                info(f"自动登录成功: {account_type}/{username}")
            return True
        else:
            error(f"自动登录失败: {account_type}/{username}")
            return False
            
    def remove_account(self, account_type, username):
        """
        移除指定账号
        
        Args:
            account_type: 账号类型 ('github' 或 'gitee')
            username: 用户名
            
        Returns:
            bool: 是否移除成功
        """
        try:
            if account_type not in ['github', 'gitee']:
                error(f"不支持的账号类型: {account_type}")
                return False
                
            # 查找并移除账号
            accounts = self.accounts[account_type]
            removed = False
            
            for i, account in enumerate(accounts):
                if account['username'] == username:
                    self.accounts[account_type].pop(i)
                    removed = True
                    break
                    
            if not removed:
                error(f"找不到要移除的账号: {account_type}/{username}")
                return False
                
            # 如果移除的是当前账号，重置当前账号
            if (self.current_account and 
                self.current_account['type'] == account_type and 
                self.current_account['data']['username'] == username):
                self.current_account = None
                
            # 如果移除的是最后登录的账号，重置最后登录记录
            if (self.accounts['last_login'] and 
                self.accounts['last_login']['type'] == account_type and 
                self.accounts['last_login']['username'] == username):
                self.accounts['last_login'] = None
                
            # 如果有相关的2FA密钥，也一并删除
            if username in self.accounts['2fa_secrets']:
                del self.accounts['2fa_secrets'][username]
                
            # 保存更改
            self.save_accounts()
            
            return True
        except Exception as e:
            error(f"移除账号失败: {str(e)}")
            return False
            
    def set_auto_login(self, enabled):
        """设置是否启用自动登录"""
        self.accounts['auto_login'] = bool(enabled)
        self.save_accounts()
        
    def set_2fa_enabled(self, enabled):
        """设置是否启用二次验证"""
        self.accounts['2fa_enabled'] = bool(enabled)
        self.save_accounts()
        
    def is_2fa_enabled(self):
        """返回是否启用二次验证"""
        return self.accounts['2fa_enabled']
        
    def save_2fa_secret(self, username, secret_key):
        """
        保存用户的2FA密钥
        
        Args:
            username: 用户名
            secret_key: 2FA密钥
        """
        self.accounts['2fa_secrets'][username] = secret_key
        self.save_accounts()
        
    def remove_2fa_secret(self, username):
        """
        移除用户的2FA密钥
        
        Args:
            username: 用户名
        """
        if username in self.accounts['2fa_secrets']:
            del self.accounts['2fa_secrets'][username]
            self.save_accounts()
            
    def get_2fa_secret(self, username):
        """
        获取用户的2FA密钥
        
        Args:
            username: 用户名
            
        Returns:
            str: 2FA密钥，如果未设置则返回None
        """
        return self.accounts['2fa_secrets'].get(username)
        
    def has_2fa_setup(self, username):
        """
        检查用户是否已设置2FA
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否已设置2FA
        """
        return username in self.accounts['2fa_secrets']
        
    def get_current_account(self):
        """获取当前登录的账号"""
        return self.current_account
        
    def get_avatar(self, username):
        """
        获取指定用户的头像
        
        Args:
            username: 用户名
            
        Returns:
            QPixmap: 用户头像，如果未加载则返回None
        """
        return self.avatar_cache.get(username)
        
    def _load_avatar(self, username, avatar_url):
        """
        加载用户头像
        
        Args:
            username: 用户名
            avatar_url: 头像URL
        """
        if not avatar_url:
            debug(f"用户 {username} 没有头像URL")
            return
            
        debug(f"加载用户 {username} 的头像: {avatar_url}")
        
        # 创建网络请求
        request = QNetworkRequest(QUrl(avatar_url))
        request.setAttribute(QNetworkRequest.User, username)  # 存储用户名，用于回调识别
        
        # 发送请求
        self.network_manager.get(request)
        
    def _handle_avatar_response(self, reply):
        """处理头像加载响应"""
        username = reply.request().attribute(QNetworkRequest.User)
        
        if reply.error():
            error(f"加载用户 {username} 的头像失败: {reply.errorString()}")
            return
            
        # 读取图像数据
        image_data = reply.readAll()
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            # 缓存头像
            self.avatar_cache[username] = pixmap
            
            # 发出信号
            self.avatarLoaded.emit(username, pixmap)
            debug(f"用户 {username} 的头像加载成功")
        else:
            error(f"用户 {username} 的头像数据无效")
            
    def save_2fa_recovery_codes(self, username, hashed_codes):
        """
        保存用户的2FA恢复码哈希值
        
        Args:
            username: 用户名
            hashed_codes: 恢复码的哈希值列表
        """
        if '2fa_recovery_codes' not in self.accounts:
            self.accounts['2fa_recovery_codes'] = {}
            
        self.accounts['2fa_recovery_codes'][username] = hashed_codes
        self.save_accounts()
        info(f"已为用户 {username} 保存2FA恢复码")
        
    def get_2fa_recovery_codes(self, username):
        """
        获取用户的2FA恢复码哈希值
        
        Args:
            username: 用户名
            
        Returns:
            list: 恢复码哈希值列表，如果未设置则返回空列表
        """
        if '2fa_recovery_codes' not in self.accounts:
            return []
            
        return self.accounts['2fa_recovery_codes'].get(username, [])
        
    def remove_recovery_code(self, username, used_hash):
        """
        移除已使用的恢复码
        
        Args:
            username: 用户名
            used_hash: 已使用的恢复码哈希值
            
        Returns:
            bool: 是否成功移除
        """
        if ('2fa_recovery_codes' not in self.accounts or 
            username not in self.accounts['2fa_recovery_codes']):
            return False
            
        recovery_codes = self.accounts['2fa_recovery_codes'][username]
        if used_hash in recovery_codes:
            recovery_codes.remove(used_hash)
            self.accounts['2fa_recovery_codes'][username] = recovery_codes
            self.save_accounts()
            info(f"已移除用户 {username} 的已使用恢复码")
            return True
            
        return False
        
    def verify_recovery_code(self, username, recovery_code):
        """
        验证恢复码是否有效
        
        Args:
            username: 用户名
            recovery_code: 用户输入的恢复码
        
        Returns:
            tuple: (是否验证成功, 已使用的恢复码哈希)
        """
        # 导入TwoFactorAuth类避免循环引用
        from src.utils.two_factor_auth import TwoFactorAuth
        tfa = TwoFactorAuth()
        
        # 获取存储的恢复码哈希值
        hashed_codes = self.get_2fa_recovery_codes(username)
        if not hashed_codes:
            error(f"用户 {username} 没有设置恢复码")
            return False, None
            
        # 验证恢复码
        is_valid, used_hash = tfa.verify_recovery_code(recovery_code, hashed_codes)
        
        return is_valid, used_hash

    def disable_2fa_after_recovery(self, username, used_hash):
        """
        在恢复码验证成功后禁用2FA
        
        Args:
            username: 用户名
            used_hash: 已使用的恢复码哈希
            
        Returns:
            bool: 是否成功禁用2FA
        """
        try:
            # 移除已使用的恢复码
            self.remove_recovery_code(username, used_hash)
            
            # 禁用2FA
            if username in self.accounts['2fa_secrets']:
                del self.accounts['2fa_secrets'][username]
                
            # 清除所有恢复码
            if username in self.accounts['2fa_recovery_codes']:
                del self.accounts['2fa_recovery_codes'][username]
                
            self.save_accounts()
            info(f"已通过恢复码成功禁用用户 {username} 的2FA")
            return True
        except Exception as e:
            error(f"禁用2FA时出错: {str(e)}")
            return False

    def verify_and_disable_2fa(self, username, recovery_code):
        """
        验证恢复码并禁用2FA (已弃用，请使用verify_recovery_code和disable_2fa_after_recovery)
        保留此方法以兼容旧代码
        
        Args:
            username: 用户名
            recovery_code: 用户输入的恢复码
            
        Returns:
            bool: 是否成功禁用2FA
        """
        is_valid, used_hash = self.verify_recovery_code(username, recovery_code)
        
        if not is_valid:
            return False
            
        return self.disable_2fa_after_recovery(username, used_hash) 