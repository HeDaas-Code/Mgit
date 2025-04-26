#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import signal
import platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from qfluentwidgets import FluentTranslator

# 导入日志工具
from src.utils.logger import info, warning, error, critical, exception, debug

# 导入主窗口
from src.views.main_window import MainWindow

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def signal_handler(sig, frame):
    """处理信号中断，如Ctrl+C"""
    if sig == signal.SIGINT:
        critical("键盘中断接收，应用正在关闭...")
    elif sig == signal.SIGTERM:
        critical("终止信号接收，应用正在关闭...")
    elif sig == signal.SIGSEGV:
        critical("检测到段错误，尝试保存工作...")
        # 尝试保存工作
        if 'w' in globals() and hasattr(w, 'editor') and hasattr(w.editor, 'document') and w.editor.document().isModified():
            try:
                # 尝试自动保存到临时文件
                import tempfile
                temp_dir = tempfile.gettempdir()
                recovery_file = os.path.join(temp_dir, "mgit_recovery.md")
                with open(recovery_file, 'w', encoding='utf-8') as f:
                    f.write(w.editor.toPlainText())
                info(f"已保存恢复文件至: {recovery_file}")
            except Exception as e:
                error(f"保存恢复文件失败: {str(e)}")
    else:
        warning(f"接收到信号 {sig}，应用正在关闭...")
        
    QApplication.quit()
    sys.exit(0)

def setup_signal_handling():
    """设置信号处理，捕获常见的中断信号"""
    # SIGINT: 键盘中断（Ctrl+C）
    signal.signal(signal.SIGINT, signal_handler)
    
    # SIGTERM: 终止信号
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 在Windows系统上，有些信号可能不可用
    try:
        # SIGHUP: 终端挂起或控制进程终止
        signal.signal(signal.SIGHUP, signal_handler)
        
        # SIGSEGV: 段错误（可能导致崩溃，但我们尝试优雅处理）
        signal.signal(signal.SIGSEGV, signal_handler)
        
        # SIGABRT: 程序中止
        signal.signal(signal.SIGABRT, signal_handler)
        
        # SIGFPE: 浮点异常
        signal.signal(signal.SIGFPE, signal_handler)
    except (AttributeError, ValueError) as e:
        warning(f"部分信号处理器无法设置: {e}")

def main():
    """ 应用程序入口 """
    info("========== MGit 应用程序启动 ==========")
    
    # 设置全局异常处理器
    from src.utils.logger import setup_exception_logging
    setup_exception_logging()
    info("全局异常处理器已设置")
    
    # 记录系统信息
    system_info = f"系统: {platform.system()} {platform.release()} ({platform.version()})"
    python_info = f"Python: {platform.python_version()}"
    info(f"运行环境: {system_info}, {python_info}")
    
    # 确保日志目录存在
    from src.utils.logger import get_log_dir
    log_dir = get_log_dir()
    info(f"日志目录: {log_dir}")
    
    # 预加载QFluentWidgets资源，确保SVG图标可用
    try:
        from qfluentwidgets import getIconColor, Theme, FluentIconBase, isDarkTheme
        from qfluentwidgets import FluentIcon
        # 预先访问一些图标，确保资源文件被加载
        icons = [FluentIcon.SETTING, FluentIcon.FOLDER, FluentIcon.SAVE, FluentIcon.DELETE]
        for icon in icons:
            icon.path()  # 预加载图标
        info("QFluentWidgets资源预加载完成")
    except Exception as e:
        warning(f"QFluentWidgets资源预加载失败: {str(e)}")
    
    # 设置应用信息
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)  # 优化WebEngine性能
    
    # 引用保持，防止GC
    global app, w, translator
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("MGit")
    app.setOrganizationName("MGitTeam")
    info("Qt应用程序实例已创建")
    
    # 设置翻译器
    translator = FluentTranslator()
    app.installTranslator(translator)
    
    # 设置关闭时清理缓存
    from PyQt5.QtWebEngineWidgets import QWebEngineProfile
    profile = QWebEngineProfile.defaultProfile()
    profile.clearHttpCache()
    
    # 延迟导入，避免循环依赖
    from qfluentwidgets import InfoBar, InfoBarManager
    # 替换InfoBar管理器的单例模式
    def safe_close():
        try:
            # 安全移除所有InfoBar，避免退出时崩溃
            for manager in [InfoBarManager.top(), InfoBarManager.bottom(), 
                           InfoBarManager.left(), InfoBarManager.right()]:
                manager.closeAllInfoBars()
        except:
            pass
    
    # 注册退出回调
    app.aboutToQuit.connect(safe_close)
    
    # 启动主窗口
    info("正在初始化主窗口...")
    w = MainWindow()
    w.show()
    info("主窗口显示成功")
    
    # 设置信号处理
    setup_signal_handling()
    info("信号处理器设置完成")
    
    info("应用程序进入事件循环...")
    # 运行应用
    exit_code = app.exec_()
    
    # 明确断开信号连接
    app.aboutToQuit.disconnect()
    
    # 清理全局变量，避免延迟释放
    info("正在清理资源...")
    if 'w' in globals():
        w.deleteLater()
    
    # 强制处理待处理的事件
    app.processEvents()
    
    # 标记应用已准备好退出
    app = None
    w = None
    translator = None
    
    info(f"应用程序结束退出，退出代码: {exit_code}")
    sys.exit(exit_code)
    
if __name__ == '__main__':
    main() 