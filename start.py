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
import re
import hashlib
from pathlib import Path
import json
import socket
import uuid
import datetime

# 检测是否在PyInstaller环境中运行
is_pyinstaller = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

# 调试模式，True为显示控制台，False为隐藏控制台
DEBUG = False  # 可根据需要修改

# 国内镜像源
PIP_MIRROR = "-i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com"

# 辅助文件路径
DEV_INFO_FILE = os.path.join(os.path.expanduser("~"), ".mgit", "dev_info.json")

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

def get_requirements_hash():
    """获取requirements.txt的哈希值，用于检测文件是否变化"""
    try:
        requirements_path = Path("requirements.txt")
        if not requirements_path.exists():
            return None
            
        # 读取文件内容
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 计算MD5哈希值
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    except Exception as e:
        print_warning(f"计算requirements.txt哈希值失败: {str(e)}")
        return None

def get_installed_packages(python_path):
    """获取已安装的包列表"""
    try:
        result = subprocess.check_output(
            [python_path, "-m", "pip", "freeze"], 
            universal_newlines=True
        )
        
        # 解析pip freeze的输出
        packages = {}
        for line in result.strip().split('\n'):
            if line and not line.startswith('#'):
                # 处理不同格式的包名和版本
                if '==' in line:
                    name, version = line.split('==', 1)
                    packages[name.lower()] = version
                elif '>=' in line:
                    name = line.split('>=', 1)[0]
                    packages[name.lower()] = None
                elif '@' in line:  # git安装格式
                    name = line.split('@', 1)[0]
                    if ' ' in name:
                        name = name.split(' ')[0]
                    packages[name.lower()] = None
                else:
                    packages[line.lower()] = None
                    
        return packages
    except Exception as e:
        print_warning(f"获取已安装包列表失败: {str(e)}")
        return {}

def parse_requirements():
    """解析requirements.txt文件"""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        return []
        
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            
        packages = []
        for line in content:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
                
            # 提取包名
            match = re.match(r'([a-zA-Z0-9_\-\.]+).*', line)
            if match:
                packages.append(match.group(1))
                
        return packages
    except Exception as e:
        print_warning(f"解析requirements.txt失败: {str(e)}")
        return []

def check_and_update_packages():
    """检查并更新新增的依赖包"""
    venv_hash_file = Path("venv-dev/.requirements_hash")
    current_hash = get_requirements_hash()
    
    # 如果requirements.txt不存在
    if current_hash is None:
        print_warning("requirements.txt文件不存在，跳过依赖检查")
        return True
        
    # 获取上次安装时的哈希值
    last_hash = None
    if venv_hash_file.exists():
        try:
            with open(venv_hash_file, 'r') as f:
                last_hash = f.read().strip()
        except:
            pass
            
    # 如果哈希值相同，说明requirements.txt没有变化
    if current_hash == last_hash:
        print_info("依赖库无变化，无需更新")
        return True
        
    # 获取Python和pip路径
    if platform.system() == "Windows":
        python_path = os.path.join("venv-dev", "Scripts", "python")
        pip_path = os.path.join("venv-dev", "Scripts", "pip")
    else:
        python_path = os.path.join("venv-dev", "bin", "python")
        pip_path = os.path.join("venv-dev", "bin", "pip")
        
    try:
        # 获取已安装的包
        installed_packages = get_installed_packages(python_path)
        
        # 获取requirements.txt中的包
        required_packages = parse_requirements()
        
        # 找出新增的包
        new_packages = []
        for package in required_packages:
            if package.lower() not in installed_packages:
                new_packages.append(package)
                
        # 如果有新增的包，安装它们
        if new_packages:
            print_info(f"检测到{len(new_packages)}个新增依赖库，正在安装...")
            for package in new_packages:
                print_info(f"正在安装: {package}")
                cmd = f"{pip_path} install {package} {PIP_MIRROR}"
                subprocess.run(cmd, shell=True, check=True)
                
            print_info("新增依赖库安装完成")
        else:
            # 如果没有新增包但哈希值不同，可能是版本要求变了，重新安装所有依赖
            print_info("依赖库有更新，正在重新安装...")
            cmd = f"{pip_path} install -r requirements.txt {PIP_MIRROR}"
            subprocess.run(cmd, shell=True, check=True)
            print_info("依赖库更新完成")
            
        # 保存新的哈希值
        with open(venv_hash_file, 'w') as f:
            f.write(current_hash)
            
        return True
    except Exception as e:
        print_error(f"更新依赖库失败: {str(e)}")
        return False

def create_venv():
    """创建虚拟环境并安装依赖包"""
    venv_path = Path("venv-dev")
    venv_exists = venv_path.exists()
    
    # 检查虚拟环境是否已存在
    if venv_exists:
        print_info("检测到已存在的虚拟环境 venv-dev")
        return check_and_update_packages()
    
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
        subprocess.run(f"{python_path} -m pip install --upgrade pip {PIP_MIRROR}", shell=True, check=True)
        
        # 检查requirements.txt是否存在
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            print_info("正在安装依赖包...")
            subprocess.run(f"{pip_path} install -r requirements.txt {PIP_MIRROR}", shell=True, check=True)
            print_info("依赖包安装完成")
            
            # 保存requirements.txt的哈希值
            current_hash = get_requirements_hash()
            if current_hash:
                venv_hash_file = Path("venv-dev/.requirements_hash")
                with open(venv_hash_file, 'w') as f:
                    f.write(current_hash)
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

def create_dev_info_file():
    """创建开发信息辅助文件，记录版本号、目录信息等"""
    print_info("正在创建开发信息文件...")
    
    # 确保目录存在
    os.makedirs(os.path.dirname(DEV_INFO_FILE), exist_ok=True)
    
    # 收集信息
    info = {
        "version": {
            "major": 1,
            "minor": 2,
            "patch": 1,
            "build": int(time.time()),
            "string": "1.2.1-dev"
        },
        "app": {
            "name": "MGit",
            "launch_time": datetime.datetime.now().isoformat(),
            "build_type": "development"
        },
        "paths": {
            "app_dir": os.path.abspath(os.getcwd()),
            "user_home": os.path.expanduser("~"),
            "app_data": os.path.join(os.path.expanduser("~"), ".mgit"),
            "plugins_dir": os.path.abspath("plugins"),
            "user_plugins_dir": os.path.join(os.path.expanduser("~"), ".mgit", "plugins")
        },
        "system": {
            "os": platform.system(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "machine_id": str(uuid.getnode())
        }
    }
    
    # 创建用户插件目录
    os.makedirs(info["paths"]["user_plugins_dir"], exist_ok=True)
    
    # 写入文件
    try:
        with open(DEV_INFO_FILE, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        print_info(f"开发信息文件已创建: {DEV_INFO_FILE}")
        return True
    except Exception as e:
        print_error(f"创建开发信息文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    # 显示欢迎信息
    print("\n" + "=" * 40)
    print("   MGit应用启动脚本")
    print("=" * 40 + "\n")
    
    # 创建开发信息文件
    create_dev_info_file()
    
    # 检查Python版本
    python_installed = check_python()
    
    if not python_installed:
        # 尝试下载并安装Python
        if not download_python():
            print_error("无法安装或找到合适的Python版本，应用将无法运行")
            input("按Enter键退出...")
            sys.exit(1)
    
    # 检查虚拟环境，如果不存在则创建
    venv_python = create_venv()
    if not venv_python:
        print_error("虚拟环境创建失败，应用将无法运行")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 检查并更新包
    check_and_update_packages()
    
    # 运行应用
    run_application()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n操作已取消，程序退出")
        sys.exit(0)
    except Exception as e:
        print_error(f"启动过程中发生错误: {str(e)}")
        input("按Enter键退出...")
        sys.exit(1) 