#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit - Markdown笔记与Git版本控制
启动脚本
"""

import sys
import os
import subprocess
import platform
import time
from pathlib import Path

# 设置WebEngine缓存路径，避免打包后的权限问题
if getattr(sys, 'frozen', False):
    # 修复PyQt WebEngine在打包环境中的缓存路径
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"
    
    # 设置缓存目录到用户临时目录
    import tempfile
    cache_dir = os.path.join(tempfile.gettempdir(), "MGit", "webcache")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["QTWEBENGINE_DISK_CACHE_DIR"] = cache_dir
    
    # 禁用磁盘缓存，减少退出时的资源清理问题
    os.environ["QTWEBENGINE_DISABLE_DISK_CACHE"] = "1"

# 预先导入PyQt5模块（如果可用）
# 这样可以确保在无控制台模式下能够正常获取用户输入
try:
    from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
    from PyQt5.QtCore import Qt
    
    # 全局QApplication实例
    def ensure_app():
        """确保存在QApplication实例"""
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        return app
    
    # 创建全局应用实例
    qt_available = True
except ImportError:
    qt_available = False
    def ensure_app():
        return None

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径，处理PyInstaller打包后的路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# PyInstaller打包时关闭启动画面
try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# 处理工作目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的应用
    application_path = os.path.dirname(sys.executable)
    # 将打包应用所在目录设为工作目录，避免资源访问出错
    os.chdir(application_path)
    # 设置基本目录为MEIPASS
    base_dir = sys._MEIPASS
    
    # 如果PyQt可用，确保应用实例存在
    if qt_available:
        app = ensure_app()
else:
    # 如果是普通Python环境，设置基本目录为脚本所在目录
    base_dir = os.path.dirname(os.path.abspath(__file__))

# 确保当前目录在Python路径中
sys.path.insert(0, base_dir)

# 在打包环境中打印调试信息
if getattr(sys, 'frozen', False):
    print(f"运行在PyInstaller环境中")
    print(f"应用路径: {application_path}")
    print(f"MEIPASS路径: {sys._MEIPASS}")
    print(f"当前工作目录: {os.getcwd()}")

# 导入日志模块
from src.utils.logger import info, warning, error, debug, critical

def check_git():
    """检查Git是否已安装并可用"""
    try:
        # 在打包环境中，可能需要完整的路径
        if getattr(sys, 'frozen', False):
            # 查找可能的Git可执行文件路径
            git_bin = "git"
            if platform.system() == "Windows":
                potential_paths = [
                    "C:\\Program Files\\Git\\cmd\\git.exe",
                    "C:\\Program Files (x86)\\Git\\cmd\\git.exe",
                    os.path.join(os.environ.get('ProgramFiles', ''), 'Git', 'cmd', 'git.exe'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Git', 'cmd', 'git.exe'),
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Git', 'cmd', 'git.exe')
                ]
                
                # 检查路径是否存在
                for path in potential_paths:
                    if os.path.exists(path):
                        git_bin = path
                        break
                
            # 尝试使用完整路径执行Git命令
            try:
                version = subprocess.check_output([git_bin, "--version"], 
                                            stderr=subprocess.DEVNULL, 
                                            universal_newlines=True)
                info(f"Git检查通过 (使用路径: {git_bin}): {version.strip()}")
                return True
            except (subprocess.SubprocessError, FileNotFoundError):
                # 尝试使用普通方式（依赖PATH环境变量）
                pass
        
        # 普通检查方式
        version = subprocess.check_output(["git", "--version"], 
                                        stderr=subprocess.DEVNULL, 
                                        universal_newlines=True)
        info(f"Git检查通过: {version.strip()}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        warning("未检测到Git，应用需要Git才能正常运行")
        return False

def install_git():
    """引导用户安装Git"""
    system = platform.system()
    
    # 如果PyQt不可用，回退到命令行模式
    if not qt_available:
        info("无法使用GUI模式，将使用命令行模式")
        return False
    
    # 确保Qt应用实例
    ensure_app()
    
    if system == "Windows":
        info("Windows系统检测到，将尝试自动安装Git...")
        try:
            # 检查是否可以自动安装
            auto_install = QMessageBox.question(
                None, 
                "自动安装Git", 
                "是否允许自动下载并安装Git？",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes
            
            if auto_install:
                # 下载Git安装程序
                import urllib.request
                import tempfile
                
                info("正在下载Git安装程序...")
                
                # 检测系统架构，选择合适的安装包
                if platform.machine().endswith('64'):
                    download_url = "https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.1/Git-2.41.0-64-bit.exe"
                else:
                    download_url = "https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.1/Git-2.41.0-32-bit.exe"
                
                # 创建临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
                temp_file.close()
                installer_path = temp_file.name
                
                # 下载进度弹窗
                progress_message = QMessageBox()
                progress_message.setWindowTitle("下载Git安装程序")
                progress_message.setText("正在下载Git安装程序，请稍候...")
                progress_message.setStandardButtons(QMessageBox.NoButton)
                progress_message.show()
                QApplication.processEvents()
                
                # 下载安装程序
                try:
                    urllib.request.urlretrieve(download_url, installer_path)
                    progress_message.close()
                except Exception as e:
                    progress_message.close()
                    QMessageBox.critical(None, "下载失败", f"下载Git安装程序失败: {str(e)}")
                    return False
                
                info("下载完成，正在安装Git...")
                QMessageBox.information(None, "安装Git", "即将启动Git安装程序，请按照安装向导完成安装。")
                
                # 运行安装程序
                subprocess.run([installer_path])
                
                info("请等待Git安装完成...")
                
                # 等待安装并检测安装结果
                for _ in range(30):  # 等待最多30秒
                    time.sleep(1)
                    if check_git():
                        info("Git安装成功!")
                        try:
                            os.remove(installer_path)  # 删除安装程序
                        except:
                            pass
                        QMessageBox.information(None, "安装成功", "Git已成功安装！")
                        return True
                
                warning("自动安装可能未完成，请确认Git安装状态")
                try:
                    os.remove(installer_path)  # 尝试删除安装程序
                except:
                    pass
                
                # 询问用户安装是否完成
                install_complete = QMessageBox.question(
                    None,
                    "确认安装",
                    "Git安装向导是否已完成？\n如果已完成，请点击'是'继续",
                    QMessageBox.Yes | QMessageBox.No
                ) == QMessageBox.Yes
                
                if install_complete and check_git():
                    return True
                
            # 如果用户选择手动安装或自动安装失败
            manual_msg = "请按照以下步骤手动安装Git:\n\n"
            manual_msg += "1. 访问 https://git-scm.com/download/win 下载Git安装程序\n"
            manual_msg += "2. 运行安装程序并按照向导完成安装\n"
            manual_msg += "3. 安装完成后重启此应用"
            
            QMessageBox.information(None, "手动安装Git", manual_msg)
            
            # 询问用户是否已完成安装
            install_done = QMessageBox.question(
                None,
                "确认安装",
                "是否已完成Git安装？",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes
            
            if install_done:
                return check_git()
            return False
            
        except Exception as e:
            error(f"自动安装Git失败: {str(e)}")
            manual_msg = "自动安装失败，请手动安装Git:\n\n"
            manual_msg += "1. 访问 https://git-scm.com/download/win 下载Git安装程序\n"
            manual_msg += "2. 运行安装程序并按照向导完成安装\n"
            manual_msg += "3. 安装完成后重启此应用"
            
            QMessageBox.warning(None, "安装失败", manual_msg)
            
            # 询问用户是否已完成安装
            install_done = QMessageBox.question(
                None,
                "确认安装",
                "是否已完成Git安装？",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes
            
            return install_done and check_git()
            
    elif system == "Darwin":  # macOS
        manual_msg = "请按照以下步骤安装Git:\n\n"
        manual_msg += "1. 打开终端，输入 'xcode-select --install' 并按Enter\n"
        manual_msg += "2. 按照弹出的提示安装开发者工具（包含Git）\n"
        manual_msg += "3. 安装完成后重启此应用"
        
        QMessageBox.information(None, "安装Git", manual_msg)
        
    elif system == "Linux":
        distro = ""
        try:
            # 尝试获取Linux发行版
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except:
            pass
        
        manual_msg = "请按照以下步骤安装Git:\n\n"
        
        if distro in ["ubuntu", "debian", "mint"]:
            manual_msg += "请在终端中执行:\nsudo apt update && sudo apt install git"
        elif distro in ["fedora", "rhel", "centos"]:
            manual_msg += "请在终端中执行:\nsudo dnf install git"
        elif distro in ["arch", "manjaro"]:
            manual_msg += "请在终端中执行:\nsudo pacman -S git"
        else:
            manual_msg += "请使用您的软件包管理器安装Git"
            
        manual_msg += "\n\n安装完成后重启此应用"
        
        QMessageBox.information(None, "安装Git", manual_msg)
        
    else:
        manual_msg = "请访问 https://git-scm.com/downloads 下载适合您系统的Git安装程序\n\n"
        manual_msg += "安装完成后重启此应用"
        
        QMessageBox.information(None, "安装Git", manual_msg)
    
    # 询问用户是否已完成安装
    install_done = QMessageBox.question(
        None,
        "确认安装",
        "是否已完成Git安装？",
        QMessageBox.Yes | QMessageBox.No
    ) == QMessageBox.Yes
    
    return install_done and check_git()

def check_git_config():
    """检查Git的基础配置，确保user.name和user.email已设置"""
    if not check_git():
        return False
        
    try:
        # 检查user.name
        name_output = subprocess.check_output(
            ["git", "config", "--get", "user.name"], 
            stderr=subprocess.DEVNULL, 
            universal_newlines=True
        ).strip()
        
        # 检查user.email
        email_output = subprocess.check_output(
            ["git", "config", "--get", "user.email"], 
            stderr=subprocess.DEVNULL, 
            universal_newlines=True
        ).strip()
        
        if name_output and email_output:
            info(f"Git配置检查通过: user.name={name_output}, user.email={email_output}")
            return True
        else:
            warning("Git配置不完整，需要设置用户名和邮箱")
            return False
    except subprocess.SubprocessError:
        warning("Git配置未设置，需要配置用户名和邮箱")
        return False

def setup_git_config():
    """设置Git的基础配置"""
    info("Git需要设置用户名和邮箱才能正常使用")
    info("这些信息仅用于记录提交者，不会被用于其他用途")
    
    # 如果PyQt不可用，回退到命令行模式
    if not qt_available:
        try:
            # 获取用户名
            name = input("请输入您的名字 (如: 张三): ")
            if not name:
                warning("用户名不能为空")
                return False
            
            # 获取邮箱
            email = input("请输入您的邮箱 (如: email@example.com): ")
            if not email or '@' not in email:
                warning("邮箱格式不正确")
                return False
            
            # 设置Git配置
            subprocess.check_call(["git", "config", "--global", "user.name", name])
            subprocess.check_call(["git", "config", "--global", "user.email", email])
            
            info("Git配置成功设置!")
            return True
        except subprocess.SubprocessError as e:
            error(f"Git配置设置失败: {str(e)}")
            return False
    
    try:
        # 确保Qt应用实例
        ensure_app()
        
        # 获取用户名
        name, ok = QInputDialog.getText(None, "Git配置", "请输入您的名字 (如: 张三):")
        if not ok or not name:
            warning("用户名不能为空")
            return False
        
        # 获取邮箱
        email, ok = QInputDialog.getText(None, "Git配置", "请输入您的邮箱 (如: email@example.com):")
        if not ok or not email or '@' not in email:
            warning("邮箱格式不正确")
            return False
        
        # 设置Git配置
        subprocess.check_call(["git", "config", "--global", "user.name", name])
        subprocess.check_call(["git", "config", "--global", "user.email", email])
        
        info("Git配置成功设置!")
        
        # 显示成功消息
        QMessageBox.information(None, "Git配置", "Git配置已成功设置！")
        
        return True
    except subprocess.SubprocessError as e:
        error(f"Git配置设置失败: {str(e)}")
        
        # 显示错误消息
        try:
            QMessageBox.critical(None, "Git配置失败", f"无法设置Git配置: {str(e)}")
        except:
            pass
            
        return False
    except Exception as e:
        error(f"设置Git配置时发生错误: {str(e)}")
        return False

def check_environment():
    """检查并设置运行环境"""
    info("正在检查Git环境...")
    
    # 先确保QFluentWidgets的InfoBar正常关闭
    if qt_available:
        try:
            # 预先加载QFluentWidgets并定制InfoBar行为
            import qfluentwidgets
            from PyQt5.QtCore import QTimer
            
            # 修改qfluentwidgets的InfoBarManager，避免退出时崩溃
            @staticmethod
            def safe_exit_filter(obj, e):
                """安全的事件过滤器，防止对象被删除后访问"""
                try:
                    return obj.parent().eventFilter(obj, e)
                except:
                    return False
                    
            # 尝试猴子补丁，替换eventFilter方法
            try:
                from qfluentwidgets.components.widgets.info_bar import InfoBarManager
                InfoBarManager._old_eventFilter = InfoBarManager.eventFilter
                InfoBarManager.eventFilter = safe_exit_filter
            except:
                warning("无法替换InfoBarManager的eventFilter方法")
                
        except ImportError:
            warning("无法加载qfluentwidgets库")
    
    # 在打包环境中可能需要更新PATH
    if getattr(sys, 'frozen', False):
        # 获取系统PATH
        path_env = os.environ.get('PATH', '')
        
        # 在Windows环境下，可能需要添加Git路径
        if platform.system() == "Windows":
            # 可能的Git安装路径
            git_paths = [
                "C:\\Program Files\\Git\\cmd",
                "C:\\Program Files (x86)\\Git\\cmd",
                os.path.join(os.environ.get('ProgramFiles', ''), 'Git', 'cmd'),
                os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'Git', 'cmd'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Git', 'cmd')
            ]
            
            # 添加Git路径到环境变量
            for git_path in git_paths:
                if os.path.exists(git_path) and git_path not in path_env:
                    os.environ['PATH'] = git_path + os.pathsep + path_env
                    info(f"已添加Git路径到环境变量: {git_path}")
                    break
    
    # 检查Git
    git_available = check_git()
    if not git_available:
        if not install_git():
            error("请安装Git后再运行此应用")
            sys.exit(1)
    
    # 检查Git配置
    git_config_valid = check_git_config()
    if not git_config_valid:
        if not setup_git_config():
            warning("请完成Git配置后再运行此应用")
            warning("您可以通过以下命令手动配置:")
            warning("git config --global user.name \"您的名字\"")
            warning("git config --global user.email \"您的邮箱\"")
            sys.exit(1)
    
    info("Git环境检查完成")
    info("-" * 50)

if __name__ == "__main__":
    try:
        # 检查环境
        check_environment()
        
        # 启动应用
        info("正在启动MGit应用...")
        from src.main import main
        
        # 捕获之前可能的警告，避免干扰用户体验
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
        
        # 定义清理函数
        def cleanup_resources():
            """在Python解释器退出前执行清理工作"""
            try:
                # 强制清理PyQt资源，避免退出时崩溃
                import gc
                from PyQt5.QtWidgets import QApplication
                
                # 处理任何待处理的事件
                app = QApplication.instance()
                if app:
                    app.processEvents()
                
                # 强制垃圾回收
                gc.collect()
                
                # 确保日志正确关闭
                import logging
                logging.shutdown()
            except:
                pass
        
        # 注册退出时的清理函数
        import atexit
        atexit.register(cleanup_resources)
        
        # 运行主程序
        main()
    except ImportError as e:
        error(f"导入模块失败: {str(e)}")
        print(f"错误: 导入模块失败: {str(e)}")
        print("这可能是由于PyInstaller打包时未包含所有必要文件")
        print("请将此错误反馈给开发者")
        if not getattr(sys, 'frozen', False):
            raise
        if qt_available:
            # 使用GUI显示错误
            ensure_app()
            QMessageBox.critical(None, "启动错误", f"导入模块失败: {str(e)}\n\n这可能是由于PyInstaller打包时未包含所有必要文件\n请将此错误反馈给开发者")
        else:
            # 回退到控制台模式
            input("按Enter键退出...")
        sys.exit(1)
    except Exception as e:
        error(f"应用启动失败: {str(e)}")
        print(f"错误: 应用启动失败: {str(e)}")
        if not getattr(sys, 'frozen', False):
            raise
        if qt_available:
            # 使用GUI显示错误
            ensure_app()
            QMessageBox.critical(None, "启动错误", f"应用启动失败: {str(e)}")
        else:
            # 回退到控制台模式
            input("按Enter键退出...")
        sys.exit(1) 