#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit - 启动脚本
用于初始化开发环境并启动应用
"""

import os
import sys
import subprocess
import platform
import urllib.request
import tempfile
import time
import shutil
from pathlib import Path

# 检测是否在PyInstaller环境中运行
is_pyinstaller = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# 调试模式，True为显示控制台，False为隐藏控制台
DEBUG = False  # 可根据需要修改

def print_info(message):
    """打印信息消息"""
    print(f"[信息] {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"[警告] {message}")

def print_error(message):
    """打印错误消息"""
    print(f"[错误] {message}")

def get_system_python():
    """获取系统Python路径"""
    system = platform.system()
    python_cmd = "python" if system == "Windows" else "python3"
    
    try:
        # 检查系统Python是否可用
        subprocess.check_output([python_cmd, "--version"], stderr=subprocess.STDOUT)
        return python_cmd
    except (subprocess.SubprocessError, FileNotFoundError):
        # 尝试其他可能的命令
        alternatives = ["python3", "python"] if system == "Windows" else ["python", "python3.10", "python3.11"]
        
        for cmd in alternatives:
            try:
                subprocess.check_output([cmd, "--version"], stderr=subprocess.STDOUT)
                return cmd
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None

def check_python():
    """检查Python是否已安装，并且版本是否大于3.10"""
    # 如果是在PyInstaller环境中，使用系统Python而不是打包环境的Python
    python_cmd = get_system_python() if is_pyinstaller else "python"
    
    if not python_cmd:
        print_warning("未检测到系统Python，需要安装Python 3.10或更高版本")
        return False
    
    try:
        # 尝试获取Python版本
        version_info = subprocess.check_output(
            [python_cmd, "--version"], 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        print_info(f"检测到Python: {version_info.strip()}")
        
        # 使用sys.version_info获取更详细的版本信息
        result = subprocess.check_output(
            [python_cmd, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"], 
            universal_newlines=True
        )
        
        version = result.strip()
        major, minor = map(int, version.split('.'))
        
        if major >= 3 and minor >= 10:
            print_info(f"Python版本满足要求: {version}")
            return True
        else:
            print_warning(f"Python版本过低: {version}，需要3.10或更高版本")
            return False
    except (subprocess.SubprocessError, FileNotFoundError):
        print_warning("未检测到Python，需要安装Python 3.10或更高版本")
        return False

def download_python():
    """下载并安装Python"""
    system = platform.system()
    
    if system == "Windows":
        print_info("正在准备下载Python安装程序...")
        
        # 检测系统架构
        is_64bit = platform.machine().endswith('64')
        
        # 构建下载URL
        if is_64bit:
            download_url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
        else:
            download_url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe"
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exe')
        temp_file.close()
        installer_path = temp_file.name
        
        print_info(f"正在下载Python 3.10.11 安装程序...")
        try:
            # 下载安装程序
            urllib.request.urlretrieve(download_url, installer_path)
            print_info("下载完成，正在安装Python...")
            
            # 构建安装命令 - 使用/quiet选项静默安装，并添加Python到PATH
            install_args = [
                installer_path,
                "/quiet", 
                "InstallAllUsers=1",
                "PrependPath=1", 
                "Include_test=0",
                "Include_pip=1"
            ]
            
            # 运行安装程序
            result = subprocess.run(install_args, check=True)
            
            if result.returncode == 0:
                print_info("Python安装成功!")
            else:
                print_error(f"Python安装失败，返回代码: {result.returncode}")
                return False
                
            # 清理安装文件
            try:
                os.unlink(installer_path)
            except:
                pass
                
            # 刷新环境变量
            print_info("正在刷新环境变量...")
            os.environ["PATH"] = subprocess.check_output(
                'powershell -command "[System.Environment]::GetEnvironmentVariable(\'PATH\',\'Machine\') + \';\' + [System.Environment]::GetEnvironmentVariable(\'PATH\',\'User\')"',
                shell=True
            ).decode('utf-8').strip()
            
            # 验证安装
            print_info("等待Python安装生效...")
            time.sleep(5)  # 等待安装完成和环境变量生效
            
            return check_python()
            
        except Exception as e:
            print_error(f"Python安装过程中发生错误: {str(e)}")
            print_info("请手动安装Python 3.10或更高版本: https://www.python.org/downloads/")
            input("安装完成后，请按Enter键继续...")
            return check_python()
    else:
        print_info("非Windows系统，请手动安装Python 3.10或更高版本")
        print_info("Linux用户可使用包管理器安装，例如: sudo apt install python3.10")
        print_info("macOS用户可使用Homebrew安装: brew install python@3.10")
        input("安装完成后，请按Enter键继续...")
        return check_python()

def create_venv():
    """创建虚拟环境并安装依赖包"""
    venv_path = Path("venv-dev")
    
    # 检查虚拟环境是否已存在
    if venv_path.exists():
        print_info("检测到已存在的虚拟环境 venv-dev")
        return True
    
    print_info("正在创建虚拟环境 venv-dev...")
    
    try:
        # 获取系统Python解释器路径（而不是打包后的内置Python）
        python_executable = get_system_python() if is_pyinstaller else sys.executable
        
        if not python_executable:
            print_error("无法找到可用的Python解释器来创建虚拟环境")
            return False
            
        print_info(f"使用 {python_executable} 创建虚拟环境")
        
        # 创建虚拟环境
        subprocess.run([python_executable, "-m", "venv", "venv-dev"], check=True)
        
        # 获取pip路径
        if platform.system() == "Windows":
            pip_path = os.path.join("venv-dev", "Scripts", "pip")
            python_path = os.path.join("venv-dev", "Scripts", "python")
        else:
            pip_path = os.path.join("venv-dev", "bin", "pip")
            python_path = os.path.join("venv-dev", "bin", "python")
        
        # 更新pip
        print_info("正在更新pip...")
        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # 检查requirements.txt是否存在
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            print_info("正在安装依赖包...")
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
            print_info("依赖包安装完成")
        else:
            print_warning("未找到requirements.txt文件，跳过依赖安装")
        
        return True
    except subprocess.SubprocessError as e:
        print_error(f"创建虚拟环境失败: {str(e)}")
        return False
    except Exception as e:
        print_error(f"设置虚拟环境时发生错误: {str(e)}")
        return False

def run_application():
    """使用虚拟环境运行应用"""
    print_info("准备启动应用...")
    
    # 检查run.py是否存在
    run_script = Path("run.py")
    if not run_script.exists():
        print_error("未找到入口文件 run.py")
        input("按Enter键退出...")
        return False
    
    # 获取Python解释器路径
    if platform.system() == "Windows":
        python_path = os.path.join("venv-dev", "Scripts", "python")
    else:
        python_path = os.path.join("venv-dev", "bin", "python")
    
    # 构建命令
    cmd = [python_path, "run.py"]
    
    try:
        # 根据DEBUG模式决定显示方式
        if DEBUG:
            print_info("以调试模式启动应用...")
            subprocess.run(cmd)
        else:
            print_info("以无控制台模式启动应用...")
            # 在Windows上使用startupinfo隐藏控制台
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                subprocess.Popen(cmd, startupinfo=startupinfo)
            else:
                # 在Unix系统上使用nohup或类似命令
                cmd.insert(0, "nohup")
                cmd.append("&")
                subprocess.Popen(" ".join(cmd), shell=True)
        return True
    except Exception as e:
        print_error(f"启动应用失败: {str(e)}")
        input("按Enter键退出...")
        return False

def main():
    """主函数"""
    print_info("=" * 50)
    print_info("MGit 部署启动脚本")
    print_info("=" * 50)
    
    if is_pyinstaller:
        print_info("正在打包环境中运行，将使用系统Python创建虚拟环境")
    
    # 检查Python
    python_ok = check_python()
    if not python_ok:
        python_ok = download_python()
        if not python_ok:
            print_error("无法设置Python环境，请手动安装Python 3.10或更高版本")
            input("按Enter键退出...")
            sys.exit(1)
    
    # 创建虚拟环境
    venv_ok = create_venv()
    if not venv_ok:
        print_error("无法设置虚拟环境，请检查错误信息")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 运行应用
    run_application()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n程序被用户中断")
    except Exception as e:
        print_error(f"程序执行过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...") 