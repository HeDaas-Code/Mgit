#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit - 打包脚本
使用此脚本打包应用为可执行文件
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """运行命令并打印输出"""
    print(f"执行命令: {command}")
    process = subprocess.Popen(
        command, 
        shell=True, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd=cwd
    )
    
    for line in process.stdout:
        print(line, end='')
    
    process.wait()
    return process.returncode

def build_app():
    """打包应用为可执行文件"""
    print("=" * 50)
    print("MGit - 开始打包应用")
    print("=" * 50)
    
    # 检测系统
    system = platform.system()
    print(f"系统类型: {system}")
    
    # 获取脚本所在目录及项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)  # 项目根目录在脚本目录的上一级
    os.chdir(root_dir)  # 切换到项目根目录
    print(f"脚本目录: {script_dir}")
    print(f"项目根目录: {root_dir}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查虚拟环境
    venv_dir = os.path.join(root_dir, "venv")
    if not os.path.exists(venv_dir):
        print(f"错误: 未找到虚拟环境: {venv_dir}")
        sys.exit(1)
    
    # 检查图标文件
    icon_file = os.path.join(root_dir, "app.ico")
    if not os.path.exists(icon_file):
        print(f"错误: 未找到图标文件: {icon_file}")
        sys.exit(1)
    
    # 确定虚拟环境中的命令路径
    if system == "Windows":
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        pyinstaller_exe = os.path.join(venv_dir, "Scripts", "pyinstaller.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        pip_exe = os.path.join(venv_dir, "bin", "pip")
        pyinstaller_exe = os.path.join(venv_dir, "bin", "pyinstaller")
    
    # 检查各命令是否存在
    if not os.path.exists(python_exe):
        print(f"错误: 虚拟环境中未找到Python: {python_exe}")
        sys.exit(1)
    
    if not os.path.exists(pip_exe):
        print(f"错误: 虚拟环境中未找到pip: {pip_exe}")
        sys.exit(1)
    
    # 检查是否已安装PyInstaller，如果没有则安装
    if not os.path.exists(pyinstaller_exe):
        print("未找到PyInstaller，正在安装...")
        result = run_command(f'"{pip_exe}" install pyinstaller')
        if result != 0:
            print("安装PyInstaller失败")
            sys.exit(1)
    
    # 确保spec文件存在
    spec_file = os.path.join(root_dir, "MGit.spec")
    if not os.path.exists(spec_file):
        print(f"错误: 未找到spec文件: {spec_file}")
        sys.exit(1)
    
    # 清理旧的构建产物
    dist_dir = os.path.join(root_dir, "dist")
    build_dir = os.path.join(root_dir, "build")
    
    if os.path.exists(dist_dir):
        print(f"正在清理旧的dist目录: {dist_dir}")
        shutil.rmtree(dist_dir)
    
    if os.path.exists(build_dir):
        print(f"正在清理旧的build目录: {build_dir}")
        shutil.rmtree(build_dir)
    
    # 将工作目录设置为项目根目录，确保PyInstaller能正确找到所有资源
    os.chdir(root_dir)
    
    # 使用PyInstaller打包应用
    print("开始打包...")
    command = f'"{pyinstaller_exe}" --clean "{spec_file}"'
    result = run_command(command, cwd=root_dir)
    
    if result != 0:
        print("打包失败")
        sys.exit(1)
    
    # 检查构建产物
    exe_file = os.path.join(dist_dir, "MGit.exe") if system == "Windows" else os.path.join(dist_dir, "MGit")
    if not os.path.exists(exe_file):
        print(f"错误: 未找到打包后的文件: {exe_file}")
        sys.exit(1)
    
    print("=" * 50)
    print(f"打包成功! 生成文件: {exe_file}")
    print("=" * 50)

if __name__ == "__main__":
    build_app() 