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
    
    # 检测是否使用国内镜像
    use_china_mirror = is_in_china()
    mirror_opt = ""
    if use_china_mirror:
        mirrors = get_pip_mirrors()
        if mirrors:
            mirror_url = mirrors[0]["url"]
            mirror_host = mirror_url.split("/")[2]
            mirror_opt = f" -i {mirror_url} --trusted-host {mirror_host}"
            print_info(f"使用{mirrors[0]['name']}镜像源安装依赖")
            
    # 设置环境变量，禁用用户安装模式
    os.environ['PIP_USER'] = '0'
        
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
                # 使用--no-user选项避免在虚拟环境中出现用户安装问题
                cmd = f"{pip_path} install {package} --no-user {mirror_opt}"
                try:
                    subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                    print_info(f"成功安装: {package}")
                except subprocess.CalledProcessError as e:
                    print_error(f"安装失败: {package}")
                    print_error(f"错误信息: {e.stderr}")
                    
                    # 尝试其他安装方式
                    print_info(f"尝试使用隔离模式安装: {package}")
                    try:
                        cmd = f"{pip_path} install {package} --no-user --isolated {mirror_opt}"
                        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                        print_info(f"成功安装: {package}")
                    except subprocess.CalledProcessError as e2:
                        print_error(f"隔离模式安装也失败: {package}")
                        print_error(f"错误信息: {e2.stderr}")
                
            print_info("新增依赖库安装完成")
        else:
            # 如果没有新增包但哈希值不同，可能是版本要求变了，重新安装所有依赖
            print_info("依赖库有更新，正在重新安装...")
            cmd = f"{pip_path} install -r requirements.txt --no-user {mirror_opt}"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    print_error(f"安装依赖失败: {result.stderr}")
                    # 尝试使用隔离模式
                    print_info("尝试使用隔离模式安装依赖...")
                    cmd = f"{pip_path} install -r requirements.txt --no-user --isolated {mirror_opt}"
                    subprocess.run(cmd, shell=True, check=True)
            except Exception as e:
                print_error(f"安装依赖时出错: {str(e)}")
                return False
                
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
        
        # 设置环境变量，禁用用户安装模式
        os.environ['PIP_USER'] = '0'
        
        # 检测是否使用国内镜像
        use_china_mirror = is_in_china()
        mirror_opt = PIP_MIRROR
        if use_china_mirror:
            mirrors = get_pip_mirrors()
            if mirrors:
                mirror_url = mirrors[0]["url"]
                mirror_host = mirror_url.split("/")[2]
                mirror_opt = f"-i {mirror_url} --trusted-host {mirror_host}"
                print_info(f"使用{mirrors[0]['name']}镜像源安装依赖")
        
        # 更新pip
        print_info("正在更新pip...")
        try:
            subprocess.run(f"{python_path} -m pip install --upgrade pip --no-user {mirror_opt}", 
                          shell=True, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print_warning(f"pip升级失败，但将继续安装: {e.stderr}")
        
        # 检查requirements.txt是否存在
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            print_info("正在安装依赖包...")
            try:
                cmd = f"{pip_path} install -r requirements.txt --no-user {mirror_opt}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print_error(f"使用标准模式安装依赖失败: {result.stderr}")
                    print_info("尝试使用隔离模式安装...")
                    
                    cmd = f"{pip_path} install -r requirements.txt --no-user --isolated {mirror_opt}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print_error(f"隔离模式安装也失败: {result.stderr}")
                        print_warning("部分依赖可能未安装成功，但将继续执行")
                
                print_info("依赖包安装完成")
            except Exception as e:
                print_error(f"安装依赖时出错: {str(e)}")
                print_warning("部分依赖可能未安装成功，但将继续执行")
            
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

def add_dependencies_to_requirements(dependencies):
    """将依赖项添加到requirements.txt文件中"""
    try:
        # 获取requirements.txt文件路径
        req_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
        
        # 读取现有的requirements文件内容
        existing_lines = []
        existing_deps = []
        plugin_section_index = -1
        
        if os.path.exists(req_file_path):
            with open(req_file_path, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
                # 去除每行末尾的换行符
                existing_lines = [line.rstrip() for line in existing_lines]
                
                # 分析已有内容
                for i, line in enumerate(existing_lines):
                    if line.strip() and not line.strip().startswith('#'):
                        existing_deps.append(line.strip())
                    if line.strip() == "# 插件依赖":
                        plugin_section_index = i
        
        # 准备新的依赖列表
        new_deps = []
        for dep in dependencies:
            # 检查依赖是否已存在
            dep_name = dep.split('>')[0].split('=')[0].split('<')[0].strip()
            if not any(d.startswith(dep_name) for d in existing_deps):
                new_deps.append(dep)
        
        if not new_deps:
            print_info("没有新的依赖需要添加到requirements.txt")
            return True
        
        # 如果没有找到插件依赖部分，添加到文件末尾
        if plugin_section_index == -1:
            # 确保文件末尾有空行
            if existing_lines and existing_lines[-1].strip():
                existing_lines.append("")
            existing_lines.append("# 插件依赖")
            for dep in new_deps:
                existing_lines.append(dep)
        else:
            # 在插件依赖部分后添加新的依赖
            insert_position = plugin_section_index + 1
            # 跳过该部分已有的依赖
            while insert_position < len(existing_lines) and existing_lines[insert_position].strip() and not existing_lines[insert_position].strip().startswith('#'):
                insert_position += 1
            
            # 插入新依赖
            for dep in reversed(new_deps):
                existing_lines.insert(insert_position, dep)
        
        # 写入文件
        with open(req_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(existing_lines))
            # 确保文件末尾有换行符
            f.write('\n')
        
        print_info(f"已将以下依赖添加到requirements.txt: {', '.join(new_deps)}")
        return True
    except Exception as e:
        print_error(f"向requirements.txt添加依赖时出错: {str(e)}")
        import traceback
        print_error(traceback.format_exc())
        # 即使出现错误，也尝试简单追加依赖到文件末尾
        try:
            with open(req_file_path, 'a+', encoding='utf-8') as f:
                f.write("\n\n# 插件依赖 (自动添加 - 可能有错误)\n")
                for dep in dependencies:
                    f.write(f"{dep}\n")
            print_warning(f"尝试使用备用方法添加依赖到requirements.txt")
        except:
            pass
        return False

def is_in_china():
    """检测是否在中国网络环境"""
    try:
        import socket
        import urllib.request
        import time
        
        # 设置超时
        socket.setdefaulttimeout(5)
        
        # 测试国内外网站响应时间
        domains = {
            "china": ["baidu.com", "aliyun.com", "qq.com"],
            "global": ["google.com", "github.com", "pypi.org"]
        }
        
        china_response_times = []
        global_response_times = []
        
        for domain in domains["china"]:
            try:
                start_time = time.time()
                urllib.request.urlopen(f"http://{domain}", timeout=3)
                response_time = time.time() - start_time
                china_response_times.append(response_time)
            except:
                pass
                
        for domain in domains["global"]:
            try:
                start_time = time.time()
                urllib.request.urlopen(f"http://{domain}", timeout=3)
                response_time = time.time() - start_time
                global_response_times.append(response_time)
            except:
                pass
        
        # 如果国内站点响应快，国外站点响应慢或无响应，判断为国内网络
        if (china_response_times and 
            (not global_response_times or 
             min(china_response_times) < min(global_response_times) * 0.5)):
            print_info("检测到国内网络环境，将使用阿里云镜像源")
            return True
        return False
    except:
        print_warning("网络环境检测失败，默认不使用国内镜像")
        return False

def get_pip_mirrors():
    """获取推荐的pip镜像源列表"""
    mirrors = [
        {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple/"},
        {"name": "腾讯云", "url": "https://mirrors.cloud.tencent.com/pypi/simple/"},
        {"name": "华为云", "url": "https://repo.huaweicloud.com/repository/pypi/simple/"},
        {"name": "清华大学", "url": "https://pypi.tuna.tsinghua.edu.cn/simple/"},
        {"name": "中国科技大学", "url": "https://pypi.mirrors.ustc.edu.cn/simple/"}
    ]
    return mirrors

def scan_plugin_dependencies():
    """扫描plugins目录，查找所有插件依赖"""
    try:
        import importlib.util
        
        plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
        if not os.path.exists(plugins_dir):
            print_info("插件目录不存在，跳过依赖扫描")
            return []
        
        all_dependencies = []
        
        # 遍历插件目录下的文件
        for file in os.listdir(plugins_dir):
            if file.endswith('.py'):
                plugin_name = file[:-3]  # 移除.py扩展名
                try:
                    # 反射加载插件模块
                    spec = importlib.util.spec_from_file_location(
                        f"plugins.{plugin_name}", 
                        os.path.join(plugins_dir, file)
                    )
                    
                    if spec is None:
                        continue
                    
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'Plugin'):
                        # 检查插件是否定义了package_dependencies
                        plugin_class = module.Plugin
                        try:
                            # 插件类应该至少有一个初始化方法，判断参数个数
                            import inspect
                            sig = inspect.signature(plugin_class.__init__)
                            params = list(sig.parameters.values())
                            
                            # 如果只需要self参数
                            if len(params) == 1:
                                plugin_instance = plugin_class()
                            else:
                                # 创建一个临时空对象，让插件有正确的self参数
                                class TempApp:
                                    pass
                                plugin_instance = plugin_class(TempApp())
                            
                            if hasattr(plugin_instance, 'package_dependencies') and plugin_instance.package_dependencies:
                                plugin_name = getattr(plugin_instance, 'name', plugin_name)
                                print_info(f"检测到插件 '{plugin_name}' 的依赖项")
                                all_dependencies.extend(plugin_instance.package_dependencies)
                        except Exception as e:
                            print_warning(f"检查插件 {plugin_name} 依赖时出错: {str(e)}")
                except Exception as e:
                    print_warning(f"加载插件 {plugin_name} 失败: {str(e)}")
        
        return all_dependencies
    except Exception as e:
        print_error(f"扫描插件依赖时出错: {str(e)}")
        return []

def check_and_add_plugin_dependencies_to_requirements():
    """检查插件依赖是否在requirements.txt中，如果不存在则添加"""
    # 获取所有插件依赖
    plugin_dependencies = scan_plugin_dependencies()
    if not plugin_dependencies:
        print_info("没有检测到插件依赖项")
        return True
    
    print_info(f"检测到 {len(plugin_dependencies)} 个插件依赖项")
    
    # 处理依赖格式，提取纯依赖名称列表
    formatted_dependencies = []
    for dep in plugin_dependencies:
        if isinstance(dep, dict):
            package_name = dep.get('name', '')
            package_version = dep.get('version', '')
            package_optional = dep.get('optional', False)
            
            # 只处理必需依赖
            if not package_optional:
                package_full = f"{package_name}{package_version}" if package_version else package_name
                formatted_dependencies.append(package_full)
        else:
            # 旧格式：直接是字符串
            formatted_dependencies.append(dep)
    
    if not formatted_dependencies:
        print_info("没有必需的插件依赖需要添加")
        return True
    
    # 检查requirements.txt文件
    req_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if not os.path.exists(req_file_path):
        print_warning("requirements.txt文件不存在，将创建新文件")
        try:
            with open(req_file_path, 'w', encoding='utf-8') as f:
                f.write("# 插件依赖\n")
                for dep in formatted_dependencies:
                    f.write(f"{dep}\n")
            print_info(f"已创建requirements.txt并添加插件依赖")
            return True
        except Exception as e:
            print_error(f"创建requirements.txt文件失败: {str(e)}")
            return False
    
    # 读取requirements.txt，检查依赖是否已存在
    try:
        existing_deps = []
        with open(req_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_deps.append(line)
        
        # 找出需要添加的依赖
        new_deps = []
        for dep in formatted_dependencies:
            dep_name = dep.split('>')[0].split('=')[0].split('<')[0].strip()
            if not any(d.split('>')[0].split('=')[0].split('<')[0].strip() == dep_name for d in existing_deps):
                new_deps.append(dep)
        
        if not new_deps:
            print_info("所有插件依赖已在requirements.txt中")
            return True
        
        # 添加新依赖到requirements.txt
        with open(req_file_path, 'a+', encoding='utf-8') as f:
            f.seek(0, os.SEEK_END)
            # 确保文件不是以换行符结尾
            if f.tell() > 0:
                f.seek(f.tell() - 1)
                last_char = f.read(1)
                if last_char != '\n':
                    f.write('\n')
            
            # 检查是否有插件依赖部分
            f.seek(0)
            content = f.read()
            if "# 插件依赖" not in content:
                f.write("\n# 插件依赖\n")
            
            # 添加新依赖
            for dep in new_deps:
                f.write(f"{dep}\n")
        
        print_info(f"已将以下插件依赖添加到requirements.txt: {', '.join(new_deps)}")
        return True
    except Exception as e:
        print_error(f"检查和添加插件依赖到requirements.txt失败: {str(e)}")
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
    
    # 首先检查并添加插件依赖到requirements.txt
    print_info("检查插件依赖...")
    check_and_add_plugin_dependencies_to_requirements()
    
    # 检查虚拟环境，如果不存在则创建
    venv_python = create_venv()
    if not venv_python:
        print_error("虚拟环境创建失败，应用将无法运行")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 检查并更新包 - 这会处理所有在requirements.txt中的依赖，包括刚添加的插件依赖
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