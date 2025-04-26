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
from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QTimer, QUrlQuery
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QProgressBar, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineCertificateError
from qfluentwidgets import InfoBar, InfoBarPosition
from datetime import datetime

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

# 注册应用退出时的全局资源清理
def cleanup_web_resources():
    """全局WebEngine资源清理函数，确保在应用退出时释放所有WebEngine资源"""
    info("正在清理全局WebEngine资源...")
    
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
        # 对于localhost始终接受证书
        if "localhost" in error.url().host() or "127.0.0.1" in error.url().host():
            error.ignoreCertificateError()
            return True
        return super().certificateError(error)

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
        
        # 尝试多个端口，防止端口占用
        self.available_ports = [8000, 8080, 9000, 9090, 10000, 10800]
        self.port = self.available_ports[0]  # 默认使用第一个端口
        
        # 初始化SSL辅助工具
        self.ssl_helper = SSLHelper()
        
        # 检查并确保有有效的SSL证书
        self.cert_file, self.key_file = self.ssl_helper.ensure_valid_cert()
        
        # GitHub OAuth配置
        self.github_client_id = os.environ.get("GITHUB_CLIENT_ID", "")
        self.github_client_secret = os.environ.get("GITHUB_CLIENT_SECRET", "")
        
        # Gitee OAuth配置
        self.gitee_client_id = os.environ.get("GITEE_CLIENT_ID", "")
        self.gitee_client_secret = os.environ.get("GITEE_CLIENT_SECRET", "")
        
        # 更新重定向URI
        self.update_redirect_uris()
        
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
        
    def start_github_auth(self):
        """启动GitHub OAuth流程"""
        try:
            # 检查Client ID和Secret是否已设置
            if not self.github_client_id or not self.github_client_secret:
                error("未设置GitHub OAuth客户端ID和密钥")
                self.githubAuthFailed.emit("未配置GitHub OAuth，请先配置应用")
                return False
                
            # 启动回调服务器
            if not self.start_server():
                self.githubAuthFailed.emit("无法启动OAuth回调服务器")
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
        # 检查Client ID和Secret是否已设置
        if not self.gitee_client_id or not self.gitee_client_secret:
            error("未设置Gitee OAuth客户端ID和密钥")
            self.giteeAuthFailed.emit("未配置Gitee OAuth，请先配置应用")
            return False
            
        # 启动回调服务器
        if not self.start_server():
            self.giteeAuthFailed.emit("无法启动OAuth回调服务器")
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
            
    def _handle_github_code(self, code):
        """处理GitHub OAuth回调中的授权码"""
        info("收到GitHub OAuth授权码")
        
        # 发射授权成功信号
        self.githubAuthSuccess.emit(code)
        
        # 使用threading.Timer代替QTimer避免线程问题
        def delayed_stop():
            self.stop_server()
            
        # 5秒后停止服务器
        timer = threading.Timer(5.0, delayed_stop)
        timer.daemon = True
        timer.start()
        
    def _handle_gitee_code(self, code):
        """处理Gitee OAuth回调中的授权码"""
        info("收到Gitee OAuth授权码")
        
        # 发射授权成功信号
        self.giteeAuthSuccess.emit(code)
        
        # 使用threading.Timer代替QTimer避免线程问题
        def delayed_stop():
            self.stop_server()
            
        # 5秒后停止服务器
        timer = threading.Timer(5.0, delayed_stop)
        timer.daemon = True
        timer.start()
        
    def _on_dialog_closed(self):
        """对话框关闭时的清理函数"""
        info("OAuth浏览器对话框已关闭")
        
        if self.browser_dialog:
            # 主动调用清理方法
            try:
                if hasattr(self.browser_dialog, 'cleanupWebResources'):
                    self.browser_dialog.cleanupWebResources()
            except Exception as e:
                error(f"清理OAuth浏览器资源时出错: {str(e)}")
                
            # 确保对话框被标记为已清理
            try:
                # 尝试销毁对话框
                self.browser_dialog.deleteLater()
            except Exception as e:
                error(f"销毁OAuth浏览器对话框时出错: {str(e)}")
                
        # 最后将引用设为None，释放对象
        self.browser_dialog = None
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
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
        self.webView = None  # 初始化webView为None
        self.webPage = None  # 初始化webPage为None
        self.profile = None  # 初始化profile为None
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        # 设置窗口标题
        provider_name = "GitHub" if self.provider_type == "github" else "Gitee"
        self.setWindowTitle(f"{provider_name} 授权")
        self.resize(800, 600)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建自定义Profile和Page以禁用安全警告
        self.profile = QWebEngineProfile("OAuthProfile", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        # 使用自定义Page类，以便覆盖certificateError方法
        self.webPage = OAuthWebEnginePage(self.profile, self)
        
        # 添加Web视图
        self.webView = QWebEngineView()
        self.webView.setPage(self.webPage)
        
        self.webView.loadStarted.connect(self.onLoadStarted)
        self.webView.loadProgress.connect(self.onLoadProgress)
        self.webView.loadFinished.connect(self.onLoadFinished)
        self.webView.urlChanged.connect(self._check_redirect)
        layout.addWidget(self.webView)
        
        # 添加进度条
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        layout.addWidget(self.progressBar)
        
        # 底部按钮区域
        btnLayout = QHBoxLayout()
        
        self.cancelBtn = QPushButton("取消")
        self.cancelBtn.clicked.connect(self.reject)
        btnLayout.addWidget(self.cancelBtn)
        
        layout.addLayout(btnLayout)
        
        # 加载URL
        self.webView.load(QUrl(self.auth_url))
        
    def closeEvent(self, event):
        """对话框关闭事件"""
        info("OAuth浏览器对话框关闭中...")
        
        # 先停止所有网络请求和页面加载
        if self.webView:
            self.webView.stop()
            
        # 清理所有WebEngine资源
        self.cleanupWebResources()
        
        # 继续原有的关闭事件
        super().closeEvent(event)
        
        # 确保reject信号被发送
        self.reject()
        
    def cleanupWebResources(self):
        """清理WebEngine相关资源，避免资源泄漏"""
        info("正在清理WebEngine资源...")
        
        try:
            if self.webView:
                # 停止加载并断开所有信号连接
                self.webView.stop()
                
                try:
                    # 安全断开信号连接
                    self.webView.loadStarted.disconnect()
                    self.webView.loadProgress.disconnect()
                    self.webView.loadFinished.disconnect()
                    self.webView.urlChanged.disconnect()
                except (TypeError, RuntimeError):
                    # 如果断开失败，可能是因为信号没有连接或其他运行时错误
                    pass
                
                # 清除页面内容
                self.webView.setHtml("")
                
                # 先将页面设为空，然后再删除页面对象
                if self.webPage:
                    # 保存对页面的引用
                    page_to_delete = self.webPage
                    # 在删除页面前先将webView的页面设为None
                    self.webView.setPage(None)
                    # 延迟删除页面
                    page_to_delete.deleteLater()
                    self.webPage = None
                
                # 从布局中移除webView
                if self.webView.parent():
                    try:
                        self.webView.parent().layout().removeWidget(self.webView)
                    except:
                        pass
                
                # 设置webView的父对象为None，确保其被正确删除
                self.webView.setParent(None)
                
                # 安排延迟删除webView
                self.webView.deleteLater()
                self.webView = None
            
            # 显式清理profile
            if self.profile:
                # 先清理缓存
                if hasattr(self.profile, 'clearHttpCache'):
                    self.profile.clearHttpCache()
                
                # 清除所有cookies
                if hasattr(self.profile, 'cookieStore'):
                    cookieStore = self.profile.cookieStore()
                    if cookieStore:
                        cookieStore.deleteAllCookies()
                
                # 清理缓存的数据
                self.profile.clearAllVisitedLinks()
                
                # 延迟删除profile
                self.profile.deleteLater()
                self.profile = None
                
        except Exception as e:
            error(f"清理WebEngine资源时发生错误: {str(e)}")
        finally:
            # 强制垃圾回收
            import gc
            gc.collect()
        
    def reject(self):
        """用户取消对话框"""
        info("OAuth登录被用户取消")
        self.cleanupWebResources()
        super().reject()
        
    def accept(self):
        """用户接受对话框"""
        info("OAuth登录完成")
        self.cleanupWebResources()
        super().accept()
        
    def onLoadStarted(self):
        """页面开始加载"""
        self.progressBar.setValue(0)
        self.progressBar.show()
        
    def onLoadProgress(self, progress):
        """页面加载进度更新"""
        self.progressBar.setValue(progress)
        
    def onLoadFinished(self, success):
        """页面加载完成"""
        if success:
            self.progressBar.setValue(100)
            # 隐藏进度条
            QTimer.singleShot(500, self.progressBar.hide)
            
            # 检查当前URL是否匹配重定向URL模式，如果是则处理授权码
            current_url = self.webView.url().toString()
            if current_url.startswith(self.redirect_uri_base):
                self._check_redirect(QUrl(current_url))
        else:
            # 如果授权已完成，忽略后续错误
            if self.auth_completed:
                return
                
            self.progressBar.setValue(0)
            # 显示加载失败的提示，但不立即关闭对话框
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
            # 发出失败信号，但延迟处理以便用户看到错误页面
            QTimer.singleShot(3000, lambda: self.authFailed.emit("页面加载失败"))
            
    def _check_redirect(self, url):
        """检查URL是否是回调URL，并获取授权码"""
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
            info(f"获取到OAuth授权码: {code[:4]}***")
            
            # 标记授权已完成
            self.auth_completed = True
            
            # 发送成功信号
            self.authSuccess.emit(code)
            
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
                <script>
                    setTimeout(function() {{
                        window.close();
                    }}, 1500);
                </script>
            </body>
            </html>
            '''
            
            self.webView.setHtml(success_html)
            
            # 延迟关闭对话框
            QTimer.singleShot(1500, self.accept)
        
        # 检查是否授权失败
        elif query.hasQueryItem("error"):
            # 获取错误信息
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
                <script>
                    setTimeout(function() {{
                        window.close();
                    }}, 3000);
                </script>
            </body>
            </html>
            '''
            
            self.webView.setHtml(error_html)
            
            # 延迟关闭对话框
            QTimer.singleShot(3000, self.reject) 