#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import webbrowser
import threading
import urllib3
import socket
import sys
import time
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QTimer, QUrlQuery, Qt, QEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar, QMessageBox, QApplication, qApp
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineCertificateError
from qfluentwidgets import InfoBar, InfoBarPosition
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet

# 导入日志模块
from src.utils.logger import info, warning, error, debug
from src.utils.ssl_helper import SSLHelper

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径，处理PyInstaller打包后的路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# 全局引用，避免资源被过早回收
_browser_dialogs = []
_is_app_exiting = False

# 应用退出监测函数
def check_app_exiting(exit_callback=None):
    """检查应用是否正在退出，并在应用退出时执行回调"""
    global _is_app_exiting
    
    if _is_app_exiting:
        return True
        
    # 获取主窗口列表
    windows = QApplication.topLevelWidgets()
    active_windows = [w for w in windows if w.isVisible() and not isinstance(w, QDialog)]
    
    # 如果没有活跃的主窗口，认为应用正在退出
    if not active_windows:
        info("检测到应用正在退出，执行最终资源清理")
        _is_app_exiting = True
        if exit_callback:
            try:
                exit_callback()
            except Exception as e:
                error(f"执行退出回调时出错: {str(e)}")
        return True
    
    return False

# 注册应用退出时的全局资源清理
def cleanup_web_resources():
    """全局WebEngine资源清理函数，确保在应用退出时释放所有WebEngine资源"""
    global _browser_dialogs, _is_app_exiting
    
    # 标记应用正在退出
    _is_app_exiting = True
    
    info("正在清理全局WebEngine资源...")
    
    # 清理所有保存的浏览器对话框
    for dialog_ref in _browser_dialogs[:]:
        try:
            dialog = dialog_ref()
            if dialog and hasattr(dialog, 'cleanupWebResources'):
                info("清理保存的浏览器对话框资源")
                dialog.cleanupWebResources()
        except Exception as e:
            error(f"清理保存的浏览器对话框时出错: {str(e)}")
    
    # 清空引用列表
    _browser_dialogs.clear()
    
    try:
        # 强制清理所有QWebEngineProfile
        profiles = QWebEngineProfile.defaultProfile()
        if profiles:
            info("正在清理默认WebEngine配置文件...")
            profiles.clearAllVisitedLinks()
            profiles.clearHttpCache()
            profiles.cookieStore().deleteAllCookies()
    except Exception as e:
        error(f"清理WebEngine配置文件时出错: {str(e)}")
    
    # 强制进行垃圾回收
    import gc
    gc.collect()
    
# 注册退出函数
import atexit
atexit.register(cleanup_web_resources)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调请求的HTTP处理器"""
    
    def log_message(self, format, *args):
        """覆盖默认日志，使用自定义日志器"""
        debug(f"OAuthCallback: {format % args}")
        
    def _send_response(self, msg, status=200):
        """发送HTTP响应"""
        try:
            self.send_response(status)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            # 确保使用UTF-8编码，并处理任何编码错误
            if isinstance(msg, str):
                msg = msg.encode('utf-8', errors='xmlcharrefreplace')
            self.wfile.write(msg)
        except Exception as e:
            error(f"发送HTTP响应时出错: {str(e)}")
        
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query = parse_qs(parsed_path.query)
            
            if path == '/github/callback':
                # 处理GitHub回调
                if 'code' in query:
                    code = query['code'][0]
                    self.server.github_callback(code)
                    # 显示成功页面
                    self._send_response('''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>GitHub OAuth 成功</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                            h1 { color: #2c974b; }
                            p { font-size: 16px; }
                        </style>
                    </head>
                    <body>
                        <h1>GitHub 授权成功</h1>
                        <p>授权已完成，您可以关闭此页面并返回应用。</p>
                    </body>
                    </html>
                    ''')
                else:
                    # 显示错误页面
                    error_message = query.get('error_description', ['未知错误'])[0]
                    self._send_response(f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>GitHub OAuth 失败</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                            h1 {{ color: #cb2431; }}
                            p {{ font-size: 16px; }}
                        </style>
                    </head>
                    <body>
                        <h1>GitHub 授权失败</h1>
                        <p>错误信息: {error_message}</p>
                        <p>请关闭此页面并重试。</p>
                    </body>
                    </html>
                    ''', 400)
                    
            elif path == '/gitee/callback':
                # 处理Gitee回调
                if 'code' in query:
                    code = query['code'][0]
                    self.server.gitee_callback(code)
                    # 显示成功页面
                    self._send_response('''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>Gitee OAuth 成功</title>
                        <style>
                            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                            h1 { color: #c71d23; }
                            p { font-size: 16px; }
                        </style>
                    </head>
                    <body>
                        <h1>Gitee 授权成功</h1>
                        <p>授权已完成，您可以关闭此页面并返回应用。</p>
                    </body>
                    </html>
                    ''')
                else:
                    # 显示错误页面
                    error_message = query.get('error_description', ['未知错误'])[0]
                    self._send_response(f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                        <title>Gitee OAuth 失败</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                            h1 {{ color: #db3b21; }}
                            p {{ font-size: 16px; }}
                        </style>
                    </head>
                    <body>
                        <h1>Gitee 授权失败</h1>
                        <p>错误信息: {error_message}</p>
                        <p>请关闭此页面并重试。</p>
                    </body>
                    </html>
                    ''', 400)
            else:
                # 未知路径
                self._send_response('''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                    <title>无效请求</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #24292e; }
                        p { font-size: 16px; }
                    </style>
                </head>
                <body>
                    <h1>无效请求</h1>
                    <p>请关闭此页面并返回应用。</p>
                </body>
                </html>
                ''', 404)
        except Exception as e:
            error(f"OAuth回调处理异常: {str(e)}")
            self._send_response(f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                <title>服务器错误</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    h1 {{ color: #cb2431; }}
                    p {{ font-size: 16px; }}
                </style>
            </head>
            <body>
                <h1>服务器错误</h1>
                <p>处理请求时发生错误: {str(e)}</p>
                <p>请关闭此页面并重试。</p>
            </body>
            </html>
            ''', 500)

class OAuthWebEnginePage(QWebEnginePage):
    """处理证书错误的WebEnginePage子类"""
    
    def certificateError(self, error):
        """处理证书错误，对于本地连接始终接受"""
        try:
            # 对于localhost始终接受证书
            if "localhost" in error.url().host() or "127.0.0.1" in error.url().host():
                error.ignoreCertificateError()
                return True
            return super().certificateError(error)
        except Exception as e:
            error(f"证书错误处理失败: {str(e)}")
            # 默认接受证书错误，避免阻断流程
            try:
                error.ignoreCertificateError()
            except:
                pass
            return True
            
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """处理来自网页的JavaScript控制台消息"""
        # 使用数值比较而不是常量名称，避免版本兼容性问题
        # 根据PyQt文档，警告级别通常是1
        if level >= 1:  # 0:Info, 1:Warning, 2:Error
            debug(f"WebEngine JavaScript [Level {level}] ({sourceID}:{lineNumber}): {message}")

class OAuthHandler(QObject):
    """OAuth授权流程处理器"""
    
    # 定义信号
    githubAuthSuccess = pyqtSignal(str)  # 参数：授权码
    githubAuthFailed = pyqtSignal(str)   # 参数：错误信息
    giteeAuthSuccess = pyqtSignal(str)   # 参数：授权码
    giteeAuthFailed = pyqtSignal(str)    # 参数：错误信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = None
        self.server_thread = None
        self.host = "localhost"
        self.use_ssl = True  # 默认使用SSL
        self.browser_dialog = None  # 保存对话框引用
        self._auth_in_progress = False  # 标记是否有正在进行的授权流程
        self._cleanup_timers = []  # 保存所有清理计时器
        
        # 尝试多个端口，防止端口占用
        self.available_ports = [8000, 8080, 9000, 9090, 10000, 10800]
        self.port = self.available_ports[0]  # 默认使用第一个端口
        
        # 初始化SSL辅助工具
        self.ssl_helper = SSLHelper()
        
        # 检查并确保有有效的SSL证书
        self.cert_file, self.key_file = self.ssl_helper.ensure_valid_cert()
        
        # 初始化加密工具
        self._init_encryption()
        
        # 配置文件路径
        self.config_file = self._get_config_file_path()
        
        # GitHub OAuth配置
        self.github_client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
        
        # Gitee OAuth配置
        self.gitee_client_id = os.environ.get("GITEE_CLIENT_ID", "")
        self.gitee_client_secret = os.environ.get("GITEE_CLIENT_SECRET", "")
        
        # 尝试加载保存的配置
        self.load_oauth_config()
        
        # 更新重定向URI
        self.update_redirect_uris()
        
    def _get_config_file_path(self):
        """获取OAuth配置文件路径"""
        # 使用与账号管理器相同的配置目录
        home_dir = str(Path.home())
        config_dir = os.path.join(home_dir, '.mgit')
        
        # 确保目录存在
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        return os.path.join(config_dir, 'oauth_config.dat')
        
    def _init_encryption(self):
        """初始化加密工具，使用与账号管理器相同的密钥"""
        try:
            # 使用与账号管理器相同的密钥文件
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, '.mgit')
            key_file = os.path.join(config_dir, 'key.dat')
            
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            if os.path.exists(key_file):
                # 加载现有密钥
                with open(key_file, 'rb') as f:
                    self.key = f.read()
                    
                # 创建Fernet实例
                self.fernet = Fernet(self.key)
                info("OAuth加密已使用已有密钥初始化")
            else:
                # 如果密钥不存在，则创建新密钥 (这部分通常由账号管理器完成，这里作为备用)
                try:
                    info("创建新的加密密钥")
                    self.key = Fernet.generate_key()
                    with open(key_file, 'wb') as f:
                        f.write(self.key)
                    self.fernet = Fernet(self.key)
                    info("已创建并保存新的加密密钥")
                except Exception as e:
                    error(f"创建加密密钥失败: {str(e)}")
                    self.fernet = None
                    return
        except Exception as e:
            error(f"OAuth加密初始化失败: {str(e)}")
            self.fernet = None
            
    def save_oauth_config(self):
        """加密保存OAuth配置"""
        if not self.fernet:
            # 尝试重新初始化加密工具
            self._init_encryption()
            if not self.fernet:
                warning("无法保存OAuth配置：加密工具未初始化")
                return False
                
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # 构建配置数据
            config_data = {
                'github': {
                    'client_id': self.github_client_id,
                    'client_secret': self.github_client_secret
                },
                'gitee': {
                    'client_id': self.gitee_client_id,
                    'client_secret': self.gitee_client_secret
                },
                # 添加版本号和时间戳，便于将来可能的配置迁移
                'version': '2.0',
                'timestamp': datetime.now().isoformat()
            }
            
            # 序列化并加密
            json_data = json.dumps(config_data, ensure_ascii=False)
            encrypted_data = self.fernet.encrypt(json_data.encode('utf-8'))
            
            # 使用临时文件模式保存，避免写入中断导致配置文件损坏
            temp_file = self.config_file + '.tmp'
            with open(temp_file, 'wb') as f:
                f.write(encrypted_data)
                
            # 替换原文件
            if os.path.exists(self.config_file):
                # 保留原文件备份
                backup_file = self.config_file + '.bak'
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(self.config_file, backup_file)
                
            os.rename(temp_file, self.config_file)
                
            info("OAuth配置已安全加密保存")
            return True
        except Exception as e:
            error(f"保存OAuth配置失败: {str(e)}")
            return False
            
    def load_oauth_config(self):
        """加载加密的OAuth配置"""
        if not self.fernet:
            # 尝试重新初始化加密工具
            self._init_encryption()
            if not self.fernet:
                warning("无法加载OAuth配置：加密工具未初始化")
                return False
                
        try:
            # 首先尝试加载主配置文件
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'rb') as f:
                        encrypted_data = f.read()
                        
                    # 解密数据
                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    config = json.loads(decrypted_data.decode('utf-8'))
                    
                    # 更新配置
                    if 'github' in config:
                        self.github_client_id = config['github'].get('client_id', '')
                        self.github_client_secret = config['github'].get('client_secret', '')
                        
                    if 'gitee' in config:
                        self.gitee_client_id = config['gitee'].get('client_id', '')
                        self.gitee_client_secret = config['gitee'].get('client_secret', '')
                        
                    info("OAuth配置已从加密存储加载")
                    return True
                except Exception as e:
                    error(f"解密主配置文件失败: {str(e)}")
                    
                    # 尝试加载备份文件
                    backup_file = self.config_file + '.bak'
                    if os.path.exists(backup_file):
                        try:
                            info("尝试从备份文件加载配置")
                            with open(backup_file, 'rb') as f:
                                encrypted_data = f.read()
                                
                            # 解密数据
                            decrypted_data = self.fernet.decrypt(encrypted_data)
                            config = json.loads(decrypted_data.decode('utf-8'))
                            
                            # 更新配置
                            if 'github' in config:
                                self.github_client_id = config['github'].get('client_id', '')
                                self.github_client_secret = config['github'].get('client_secret', '')
                                
                            if 'gitee' in config:
                                self.gitee_client_id = config['gitee'].get('client_id', '')
                                self.gitee_client_secret = config['gitee'].get('client_secret', '')
                                
                            info("OAuth配置已从备份文件加载")
                            
                            # 保存到主配置文件
                            self.save_oauth_config()
                            return True
                        except Exception as backup_e:
                            error(f"从备份加载配置也失败: {str(backup_e)}")
                            return False
                    return False
            else:
                debug("OAuth配置文件不存在，使用默认值")
                return False
        except Exception as e:
            error(f"加载OAuth配置失败: {str(e)}")
            return False
        
    def update_redirect_uris(self):
        """更新重定向URI"""
        # 本地开发环境下使用HTTP避免证书问题
        self.use_ssl = False  # 默认使用HTTP来避免证书问题
        protocol = "http"  # 始终使用HTTP协议以避免证书问题
        
        # GitHub重定向URI
        self.github_redirect_uri = f"{protocol}://{self.host}:{self.port}/github/callback"
        
        # Gitee重定向URI
        self.gitee_redirect_uri = f"{protocol}://{self.host}:{self.port}/gitee/callback"
        
    def find_available_port(self):
        """查找可用的端口"""
        debug(f"正在搜索可用端口...")
        # 首先尝试默认端口
        for port in self.available_ports:
            try:
                # 尝试绑定端口
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((self.host, port))
                    info(f"找到可用端口: {port}")
                    return port
            except OSError as e:
                warning(f"端口 {port} 不可用: {e}")
        
        # 如果所有预定义端口都不可用，尝试随机端口
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.host, 0))  # 系统分配随机端口
                _, port = s.getsockname()
                info(f"使用随机分配的端口: {port}")
                return port
        except OSError as e:
            error(f"无法找到可用端口: {e}")
            return None
            
    def start_server(self):
        """启动OAuth回调服务器"""
        # 如果服务器已在运行，先停止
        if self.server_thread and self.server_thread.is_alive():
            self.stop_server()
            
        # 查找可用端口
        self.port = self.find_available_port()
        if not self.port:
            error("无法启动OAuth服务器: 未找到可用端口")
            return False
            
        # 更新重定向URI
        self.update_redirect_uris()
        
        try:
            # 创建服务器
            oauth_server = HTTPServer((self.host, self.port), OAuthCallbackHandler)
            
            # 设置回调函数
            oauth_server.github_callback = self._handle_github_code
            oauth_server.gitee_callback = self._handle_gitee_code
            
            # SSL已禁用，使用HTTP以避免证书问题
            self.use_ssl = False
                    
            # 在新线程中启动服务器
            self.server = oauth_server
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            info(f"OAuth回调服务器已启动: http://{self.host}:{self.port}")
            return True
        except Exception as e:
            error(f"启动OAuth服务器失败: {str(e)}")
            return False
            
    def stop_server(self):
        """停止OAuth回调服务器"""
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                info("OAuth回调服务器已停止")
            except Exception as e:
                error(f"停止OAuth服务器时出错: {str(e)}")
                
        self.server = None
        self.server_thread = None
        
    def force_stop_auth(self):
        """强制停止当前的OAuth授权流程"""
        debug("强制停止OAuth授权流程")
        self._auth_in_progress = False
        
        # 清理所有计时器
        for timer in self._cleanup_timers:
            if timer and timer.is_alive():
                try:
                    timer.cancel()
                except:
                    pass
        self._cleanup_timers = []
        
        # 关闭浏览器对话框
        if self.browser_dialog:
            try:
                debug("强制关闭OAuth浏览器对话框")
                # 使用safeReject方法安全关闭对话框
                if hasattr(self.browser_dialog, 'safeReject'):
                    self.browser_dialog.safeReject()
                else:
                    self.browser_dialog.reject()
                self.browser_dialog = None
            except Exception as e:
                error(f"关闭OAuth浏览器对话框时出错: {str(e)}")
        
        # 停止服务器
        self.stop_server()
        
        debug("OAuth授权流程已强制停止")
        
    def start_github_auth(self):
        """启动GitHub OAuth流程"""
        try:
            # 检查是否有正在进行的授权流程
            if self._auth_in_progress:
                debug("有正在进行的OAuth流程，先强制停止")
                self.force_stop_auth()
                
            self._auth_in_progress = True
                
            # 检查Client ID和Secret是否已设置
            if not self.github_client_id or not self.github_client_secret:
                error("未设置GitHub OAuth客户端ID和密钥")
                self.githubAuthFailed.emit("未配置GitHub OAuth，请先配置应用")
                self._auth_in_progress = False
                return False
                
            # 启动回调服务器
            if not self.start_server():
                self.githubAuthFailed.emit("无法启动OAuth回调服务器")
                self._auth_in_progress = False
                return False
                
            # 确保重定向URI使用HTTP
            self.update_redirect_uris()
                
            # 构建授权URL
            auth_url = (
                f"https://github.com/login/oauth/authorize?"
                f"client_id={self.github_client_id}&"
                f"redirect_uri={self.github_redirect_uri}&"
                f"scope=repo"
            )
            
            info(f"启动GitHub OAuth流程，URL: {auth_url}")
            
            # 显示提示和选项弹窗
            reply = QMessageBox.question(
                self.parent(),
                "OAuth授权",
                "您可以选择在内置浏览器中授权，或打开系统浏览器完成授权。\n\n系统浏览器可能更稳定。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.No:
                # 使用系统浏览器
                webbrowser.open(auth_url)
                
                # 显示提示
                QMessageBox.information(
                    self.parent(),
                    "在浏览器中完成授权",
                    "请在打开的浏览器窗口中完成授权。\n完成后将自动返回应用。",
                    QMessageBox.StandardButton.Ok
                )
                
                return True
            
            # 在内置浏览器中打开
            try:
                self.browser_dialog = OAuthBrowserDialog(auth_url, "github", self.github_redirect_uri, parent=self.parent())
                self.browser_dialog.authSuccess.connect(lambda code: self._handle_github_code(code))
                self.browser_dialog.authFailed.connect(lambda error: self.githubAuthFailed.emit(error))
                self.browser_dialog.finished.connect(lambda: self._on_dialog_closed())
                self.browser_dialog.show()
                return True
            except Exception as e:
                error(f"打开OAuth浏览器对话框失败: {str(e)}")
                self.githubAuthFailed.emit(f"打开授权对话框失败: {str(e)}")
                return False
                
        except Exception as e:
            error(f"启动GitHub OAuth流程失败: {str(e)}")
            self.githubAuthFailed.emit(f"启动授权流程失败: {str(e)}")
            return False
            
    def start_gitee_auth(self, gitee_url="https://gitee.com"):
        """启动Gitee OAuth流程"""
        try:
            # 检查是否有正在进行的授权流程
            if self._auth_in_progress:
                debug("有正在进行的OAuth流程，先强制停止")
                self.force_stop_auth()
                
            self._auth_in_progress = True
                
            # 检查Client ID和Secret是否已设置
            if not self.gitee_client_id or not self.gitee_client_secret:
                error("未设置Gitee OAuth客户端ID和密钥")
                self.giteeAuthFailed.emit("未配置Gitee OAuth，请先配置应用")
                self._auth_in_progress = False
                return False
                
            # 启动回调服务器
            if not self.start_server():
                self.giteeAuthFailed.emit("无法启动OAuth回调服务器")
                self._auth_in_progress = False
                return False
                
            # 确保重定向URI使用HTTP
            self.update_redirect_uris()
                
            # 构建授权URL
            auth_url = (
                f"{gitee_url}/oauth/authorize?"
                f"client_id={self.gitee_client_id}&"
                f"redirect_uri={self.gitee_redirect_uri}&"
                f"response_type=code&"
                f"scope=projects pull_requests issues"
            )
            
            info(f"启动Gitee OAuth流程，URL: {auth_url}")
            
            # 显示提示和选项弹窗
            reply = QMessageBox.question(
                self.parent(),
                "OAuth授权",
                "您可以选择在内置浏览器中授权，或打开系统浏览器完成授权。\n\n系统浏览器可能更稳定。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.No:
                # 使用系统浏览器
                webbrowser.open(auth_url)
                
                # 显示提示
                QMessageBox.information(
                    self.parent(),
                    "在浏览器中完成授权",
                    "请在打开的浏览器窗口中完成授权。\n完成后将自动返回应用。",
                    QMessageBox.StandardButton.Ok
                )
                
                return True
            
            try:
                # 在内置浏览器中打开
                self.browser_dialog = OAuthBrowserDialog(auth_url, "gitee", self.gitee_redirect_uri, parent=self.parent())
                self.browser_dialog.authSuccess.connect(lambda code: self._handle_gitee_code(code))
                self.browser_dialog.authFailed.connect(lambda error: self.giteeAuthFailed.emit(error))
                self.browser_dialog.finished.connect(lambda: self._on_dialog_closed())
                self.browser_dialog.show()
                return True
            except Exception as e:
                error(f"启动Gitee OAuth流程失败: {str(e)}")
                self.giteeAuthFailed.emit(f"启动授权流程失败: {str(e)}")
                return False
                
        except Exception as e:
            error(f"启动Gitee OAuth流程失败: {str(e)}")
            self.giteeAuthFailed.emit(f"启动授权流程失败: {str(e)}")
            return False
            
    def _handle_github_code(self, code):
        """处理GitHub OAuth回调中的授权码"""
        info("收到GitHub OAuth授权码")
        
        # 清除授权中状态标志
        self._auth_in_progress = False
        
        # 发射授权成功信号
        self.githubAuthSuccess.emit(code)
        
        # 使用threading.Timer代替QTimer避免线程问题
        def delayed_stop():
            self.stop_server()
            
        # 5秒后停止服务器
        timer = threading.Timer(5.0, delayed_stop)
        timer.daemon = True
        timer.start()
        
        # 保存计时器引用以便于清理
        self._cleanup_timers.append(timer)
        
    def _handle_gitee_code(self, code):
        """处理Gitee OAuth回调中的授权码"""
        info("收到Gitee OAuth授权码")
        
        # 清除授权中状态标志
        self._auth_in_progress = False
        
        # 发射授权成功信号
        self.giteeAuthSuccess.emit(code)
        
        # 使用threading.Timer代替QTimer避免线程问题
        def delayed_stop():
            self.stop_server()
            
        # 5秒后停止服务器
        timer = threading.Timer(5.0, delayed_stop)
        timer.daemon = True
        timer.start()
        
        # 保存计时器引用以便于清理
        self._cleanup_timers.append(timer)
        
    def _on_dialog_closed(self):
        """对话框关闭时的清理函数"""
        info("OAuth浏览器对话框已关闭")
        
        # 清除授权中状态标志
        self._auth_in_progress = False
        
        # 解除对对话框的引用，但不尝试主动清理资源
        # 对话框自己会负责在合适的时机清理资源
        dialog = self.browser_dialog
        self.browser_dialog = None
        
        # 检查应用是否正在退出
        if check_app_exiting() and dialog and hasattr(dialog, 'cleanupWebResources'):
            # 应用退出时进行清理
            try:
                info("应用正在退出，清理OAuth浏览器资源")
                dialog.cleanupWebResources()
            except Exception as e:
                error(f"清理OAuth浏览器资源时出错: {str(e)}")
                
        # 使用threading.Timer代替QTimer避免线程问题
        def delayed_stop():
            self.stop_server()
            
        # 5秒后停止服务器
        timer = threading.Timer(5.0, delayed_stop)
        timer.daemon = True
        timer.start()
        
        # 保存计时器引用以便于清理
        self._cleanup_timers.append(timer)
        
class OAuthBrowserDialog(QDialog):
    """内置浏览器的OAuth授权对话框"""
    
    # 定义信号
    authSuccess = pyqtSignal(str)  # 参数：授权码
    authFailed = pyqtSignal(str)   # 参数：错误信息
    
    def __init__(self, auth_url, provider_type, redirect_uri_base, parent=None):
        super().__init__(parent)
        self.auth_url = auth_url
        self.provider_type = provider_type
        self.redirect_uri_base = redirect_uri_base
        self.auth_completed = False  # 标记授权是否已完成
        self.cleanup_done = False    # 标记清理是否已完成
        self.cleanup_delayed = False # 标记是否已安排延迟清理
        self.webView = None  # 初始化webView为None
        self.webPage = None  # 初始化webPage为None
        self.profile = None  # 初始化profile为None
        self.main_parent = parent    # 保存主窗口引用
        
        # 设置窗口标志
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 将自己加入全局引用列表，避免过早回收
        global _browser_dialogs
        import weakref
        _browser_dialogs.append(weakref.ref(self))
        
        # 初始化UI
        try:
            self.initUI()
        except Exception as e:
            error(f"初始化OAuth浏览器对话框失败: {str(e)}")
            # 确保在初始化失败时也能发送信号
            self.authFailed.emit(f"初始化授权对话框失败: {str(e)}")
            # 安排对话框延迟关闭
            QTimer.singleShot(100, self.close)

    def initUI(self):
        """初始化UI"""
        # 设置窗口标题
        provider_name = "GitHub" if self.provider_type == "github" else "Gitee"
        self.setWindowTitle(f"{provider_name} 授权")
        self.resize(800, 600)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            # 创建自定义Profile和Page以禁用安全警告
            self.profile = QWebEngineProfile(f"OAuthProfile-{id(self)}", self)
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            
            # 使用自定义Page类，以便覆盖certificateError方法
            self.webPage = OAuthWebEnginePage(self.profile, self)
            
            # 添加Web视图
            self.webView = QWebEngineView(self)  # 确保有明确的父对象
            self.webView.setPage(self.webPage)
            
            # 使用try-except包装每个信号连接，以便在失败时能够继续
            try:
                self.webView.loadStarted.connect(self.onLoadStarted)
            except Exception as e:
                error(f"连接loadStarted信号失败: {str(e)}")
                
            try:
                self.webView.loadProgress.connect(self.onLoadProgress)
            except Exception as e:
                error(f"连接loadProgress信号失败: {str(e)}")
                
            try:
                self.webView.loadFinished.connect(self.onLoadFinished)
            except Exception as e:
                error(f"连接loadFinished信号失败: {str(e)}")
                
            try:
                self.webView.urlChanged.connect(self._check_redirect)
            except Exception as e:
                error(f"连接urlChanged信号失败: {str(e)}")
                
            layout.addWidget(self.webView)
            
            # 添加进度条
            self.progressBar = QProgressBar(self)  # 确保有明确的父对象
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)
            layout.addWidget(self.progressBar)
            
            # 底部按钮区域
            btnLayout = QHBoxLayout()
            
            self.cancelBtn = QPushButton("取消", self)  # 确保有明确的父对象
            self.cancelBtn.clicked.connect(self.safeReject)
            btnLayout.addWidget(self.cancelBtn)
            
            layout.addLayout(btnLayout)
            
            # 加载URL
            try:
                self.webView.load(QUrl(self.auth_url))
            except Exception as e:
                error(f"加载OAuth URL失败: {str(e)}")
                self.authFailed.emit(f"加载授权页面失败: {str(e)}")
                QTimer.singleShot(1000, self.safeReject)
                
        except Exception as e:
            error(f"初始化OAuth浏览器界面失败: {str(e)}")
            self.authFailed.emit(f"初始化授权界面失败: {str(e)}")
            QTimer.singleShot(1000, self.safeReject)
        
    def closeEvent(self, event):
        """对话框关闭事件"""
        info("OAuth浏览器对话框关闭中...")
        
        # 先停止加载以避免额外网络请求
        if hasattr(self, 'webView') and self.webView:
            try:
                self.webView.stop()
            except:
                pass
        
        # 标记为已完成，避免后续URL处理
        self.auth_completed = True
        
        # 检查应用是否正在退出
        if check_app_exiting():
            # 如果应用正在退出，立即清理资源
            info("检测到应用退出，立即清理资源")
            self.cleanupWebResources()
        else:
            # 如果应用仍在运行，不立即清理，而是安排延迟清理
            if not self.cleanup_delayed:
                info("应用仍在运行，安排延迟资源清理")
                self.cleanup_delayed = True
                # 使用更长的延迟时间，避免过早清理
                QTimer.singleShot(2000, self.check_and_cleanup)
        
        # 接受关闭事件
        event.accept()
        
    def check_and_cleanup(self):
        """检查应用状态并决定是否清理资源"""
        # 如果已经清理过，直接返回
        if self.cleanup_done:
            return
            
        # 检查应用是否仍在运行
        if check_app_exiting():
            # 如果应用正在退出，立即清理资源
            info("延迟检测到应用退出，执行资源清理")
            self.cleanupWebResources()
        else:
            # 应用仍在运行，将资源清理推迟
            # 只在第一次推迟时输出日志，避免频繁日志
            if not hasattr(self, '_cleanup_postponed'):
                info("应用仍在运行，资源清理将在应用退出前执行")
                self._cleanup_postponed = True
                
            # 使用弱引用检查主窗口状态
            import weakref
            if self.main_parent and isinstance(self.main_parent, QObject):
                parent_ref = weakref.ref(self.main_parent)
                parent = parent_ref()
                if parent and parent.isVisible():
                    # 主窗口仍然可见，继续推迟清理，但不再输出日志
                    QTimer.singleShot(30000, self.check_and_cleanup)  # 延长检查间隔到30秒
                else:
                    # 主窗口不可见，执行清理
                    info("检测到主窗口不可见，执行资源清理")
                    self.cleanupWebResources()
            else:
                # 无法确定主窗口状态，保守地推迟清理，但不再输出日志
                QTimer.singleShot(30000, self.check_and_cleanup)  # 延长检查间隔到30秒
        
    def finalize(self):
        """在UI线程中执行的最终清理，与closeEvent分离以避免崩溃"""
        info("OAuth浏览器对话框进行最终清理...")
        
        # 检查应用是否正在退出
        if check_app_exiting():
            # 如果应用正在退出，立即清理资源
            try:
                self.cleanupWebResources()
            except Exception as e:
                error(f"清理资源时发生错误: {str(e)}")
        else:
            # 应用仍在运行，不立即清理资源
            if not self.cleanup_delayed:
                info("应用仍在运行，安排延迟资源清理")
                self.cleanup_delayed = True
                QTimer.singleShot(2000, self.check_and_cleanup)
            
        # 发出可能的取消信号
        if not self.auth_completed:
            try:
                self.authFailed.emit("用户取消了授权")
            except:
                pass
                
        # 从全局引用列表中移除自己
        global _browser_dialogs
        import weakref
        for i, ref in enumerate(_browser_dialogs[:]):
            if ref() is self:
                try:
                    _browser_dialogs.pop(i)
                except:
                    pass
                break
                
        # 确保deleteLater被调用，但不立即执行（让Qt事件循环来处理）
        try:
            self.deleteLater()
        except:
            pass
        
    def cleanupWebResources(self):
        """安全地清理WebEngine相关资源，只在应用退出或明确需要时执行"""
        # 如果已经清理过，直接返回
        if self.cleanup_done:
            return
            
        info("正在安全清理WebEngine资源...")
        
        # 标记已清理，避免重复清理
        self.cleanup_done = True
        
        # 首先断开所有信号，防止异步调用
        if hasattr(self, 'webView') and self.webView:
            try:
                # 停止任何正在进行的加载
                self.webView.stop()
                
                # 确保当前页面是空白页，减少资源占用
                try:
                    self.webView.setHtml("<html><body></body></html>")
                except:
                    pass
                    
                # 断开所有信号连接
                try:
                    self.webView.loadStarted.disconnect()
                except:
                    pass
                try:
                    self.webView.loadProgress.disconnect()
                except:
                    pass
                try:
                    self.webView.loadFinished.disconnect()
                except:
                    pass
                try:
                    self.webView.urlChanged.disconnect()
                except:
                    pass
            except Exception as e:
                error(f"断开WebView信号时出错: {str(e)}")
        
        # 清理网页和配置文件
        try:
            # 删除页面对象
            if hasattr(self, 'webPage') and self.webPage:
                try:
                    if hasattr(self, 'webView') and self.webView:
                        self.webView.setPage(None)
                    self.webPage.deleteLater()
                    self.webPage = None
                except Exception as e:
                    error(f"删除WebPage时出错: {str(e)}")
            
            # 清理配置文件资源
            if hasattr(self, 'profile') and self.profile:
                try:
                    if hasattr(self.profile, 'clearHttpCache'):
                        self.profile.clearHttpCache()
                    
                    if hasattr(self.profile, 'cookieStore'):
                        try:
                            store = self.profile.cookieStore()
                            if store:
                                store.deleteAllCookies()
                        except:
                            pass
                            
                    try:
                        self.profile.clearAllVisitedLinks()
                    except:
                        pass
                        
                    # 使用deleteLater
                    self.profile.deleteLater()
                    self.profile = None
                except Exception as e:
                    error(f"清理WebEngineProfile时出错: {str(e)}")
        except Exception as e:
            error(f"清理Web资源时出错: {str(e)}")
        
        # 清理UI组件
        try:
            # 移除webView
            if hasattr(self, 'webView') and self.webView:
                try:
                    layout = self.layout()
                    if layout:
                        layout.removeWidget(self.webView)
                    self.webView.deleteLater()
                    self.webView = None
                except Exception as e:
                    error(f"移除WebView时出错: {str(e)}")
        except Exception as e:
            error(f"清理UI组件时出错: {str(e)}")
        
    def safeReject(self):
        """安全地取消对话框"""
        info("OAuth登录被用户取消")
        
        # 先设置已完成标志，避免进一步的URL处理
        self.auth_completed = True
        
        # 不立即清理资源，在对话框关闭后会自动清理
        self.close()
        
    def reject(self):
        """用户取消对话框，优先使用安全方法"""
        info("OAuth对话框被拒绝")
        self.safeReject()
        
    def accept(self):
        """用户接受对话框，确保安全关闭"""
        info("OAuth登录完成，安全关闭对话框")
        
        # 先设置已完成标志
        self.auth_completed = True
        
        # 不立即清理资源，在对话框关闭后会自动清理
        self.close()
        
    def onLoadStarted(self):
        """页面开始加载"""
        # 如果已完成授权，忽略后续加载
        if self.auth_completed:
            return
            
        try:
            self.progressBar.setValue(0)
            self.progressBar.show()
        except:
            pass
        
    def onLoadProgress(self, progress):
        """页面加载进度更新"""
        # 如果已完成授权，忽略后续进度
        if self.auth_completed:
            return
            
        try:
            self.progressBar.setValue(progress)
        except:
            pass
        
    def onLoadFinished(self, success):
        """页面加载完成"""
        # 如果已完成授权，忽略后续加载完成事件
        if self.auth_completed:
            return
            
        try:
            if success:
                self.progressBar.setValue(100)
                # 隐藏进度条
                try:
                    QTimer.singleShot(500, self.progressBar.hide)
                except:
                    pass
                
                # 检查当前URL是否匹配重定向URL模式
                try:
                    current_url = self.webView.url().toString()
                    if current_url.startswith(self.redirect_uri_base):
                        self._check_redirect(QUrl(current_url))
                except:
                    pass
            else:
                try:
                    self.progressBar.setValue(0)
                except:
                    pass
                    
                try:
                    # 显示加载失败的提示
                    current_url = self.webView.url().toString()
                    
                    # 如果当前URL是回调URL，不显示错误（可能是正常的授权完成后的跳转）
                    if current_url.startswith(self.redirect_uri_base):
                        return
                        
                    # 标记授权已失败
                    self.auth_completed = True
                    
                    error_html = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>页面加载失败</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                            h1 {{ color: #cb2431; }}
                            p {{ font-size: 16px; }}
                        </style>
                    </head>
                    <body>
                        <h1>页面加载失败</h1>
                        <p>无法加载页面: {current_url}</p>
                        <p>请检查您的网络连接，然后重试。</p>
                        <button onclick="window.close()">关闭</button>
                    </body>
                    </html>
                    '''
                    self.webView.setHtml(error_html)
                    
                    # 发出失败信号，延迟处理以便用户看到错误页面
                    try:
                        QTimer.singleShot(3000, lambda: self.authFailed.emit("页面加载失败"))
                    except:
                        # 直接发出信号
                        self.authFailed.emit("页面加载失败")
                except Exception as e:
                    error(f"处理页面加载失败事件时出错: {str(e)}")
                    try:
                        self.authFailed.emit("页面加载过程中出错")
                    except:
                        pass
                    self.safeReject()
        except Exception as e:
            error(f"onLoadFinished处理失败: {str(e)}")
            try:
                self.authFailed.emit(f"页面加载完成处理失败: {str(e)}")
            except:
                pass
            self.safeReject()
            
    def _check_redirect(self, url):
        """检查URL是否是回调URL，并获取授权码"""
        # 如果已完成授权，忽略后续重定向
        if self.auth_completed:
            return
            
        try:
            # 仅当URL字符串以预期回调URI开头时才处理
            url_str = url.toString()
            
            if not url_str.startswith(self.redirect_uri_base):
                return
                
            info(f"检测到OAuth重定向URL: {url_str}")
            
            # 提取查询参数
            query = QUrlQuery(url.query())
            
            # 检查是否授权成功
            if query.hasQueryItem("code"):
                # 获取授权码
                code = query.queryItemValue("code")
                info(f"获取到OAuth授权码: {code[:4] if len(code) > 4 else '****'}***")
                
                # 标记授权已完成
                self.auth_completed = True
                
                # 发送成功信号
                try:
                    self.authSuccess.emit(code)
                except Exception as e:
                    error(f"发送授权成功信号失败: {str(e)}")
                
                # 给用户一个成功的反馈
                success_html = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>授权成功</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        h1 {{ color: #28a745; }}
                        p {{ font-size: 16px; }}
                    </style>
                </head>
                <body>
                    <h1>授权成功</h1>
                    <p>您已成功授权应用访问您的账户。</p>
                    <p>窗口将在几秒后自动关闭...</p>
                </body>
                </html>
                '''
                
                try:
                    self.webView.setHtml(success_html)
                except:
                    pass
                
                # 延迟关闭对话框
                try:
                    QTimer.singleShot(1500, self.accept)
                except:
                    # 如果定时器设置失败，立即调用accept
                    self.accept()
            
            # 检查是否授权失败
            elif query.hasQueryItem("error"):
                # 获取错误信息
                try:
                    error_code = query.queryItemValue("error")
                    error_description = query.queryItemValue("error_description") if query.hasQueryItem("error_description") else "未知错误"
                    
                    error_msg = f"{error_code}: {error_description}"
                    error(f"OAuth授权失败: {error_msg}")
                    
                    # 标记授权已完成
                    self.auth_completed = True
                    
                    # 发送失败信号
                    self.authFailed.emit(error_msg)
                    
                    # 给用户一个错误反馈
                    error_html = f'''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>授权失败</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                            h1 {{ color: #cb2431; }}
                            p {{ font-size: 16px; }}
                        </style>
                    </head>
                    <body>
                        <h1>授权失败</h1>
                        <p>错误信息: {error_msg}</p>
                        <p>窗口将在几秒后自动关闭...</p>
                    </body>
                    </html>
                    '''
                    
                    self.webView.setHtml(error_html)
                    
                    # 延迟关闭对话框
                    QTimer.singleShot(3000, self.safeReject)
                except Exception as e:
                    error(f"处理OAuth错误回调时出错: {str(e)}")
                    # 直接发送失败信号并关闭窗口
                    try:
                        self.authFailed.emit("处理授权错误时出现问题")
                    except:
                        pass
                    self.safeReject()
            else:
                # 没有授权码或错误，但是URL符合回调格式，可能是其他情况
                info(f"收到未预期的OAuth回调URL: {url_str}")
        except Exception as e:
            error(f"_check_redirect处理失败: {str(e)}")
            try:
                self.authFailed.emit(f"处理授权回调失败: {str(e)}")
            except:
                pass
            self.safeReject() 