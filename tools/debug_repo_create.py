#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit - 仓库创建问题调试
此脚本用于独立调试和排查仓库创建路径相关问题
"""

import os
import sys
import traceback
import git

def debug_path(path):
    """打印路径信息用于调试"""
    print(f"路径: {path}")
    print(f"  绝对路径: {os.path.abspath(path)}")
    print(f"  规范路径: {os.path.normpath(path)}")
    print(f"  存在: {os.path.exists(path)}")
    if os.path.exists(path):
        print(f"  是目录: {os.path.isdir(path)}")
        if os.path.isdir(path):
            print(f"  目录内容: {os.listdir(path)}")
    print()

def init_repository(path, name=None):
    """尝试初始化仓库"""
    try:
        print("=" * 50)
        print(f"尝试在以下位置初始化仓库:")
        
        if name:
            # 如果提供了名称，就将其加入路径
            full_path = os.path.join(path, name)
            print(f"基础路径: {path}")
            print(f"仓库名称: {name}")
            print(f"完整路径: {full_path}")
        else:
            # 否则直接使用提供的路径
            full_path = path
            print(f"完整路径: {full_path}")
        
        # 确保路径是绝对路径
        full_path = os.path.abspath(full_path)
        print(f"绝对路径: {full_path}")
        
        # 检查路径是否存在
        if not os.path.exists(full_path):
            print(f"路径不存在，尝试创建目录...")
            os.makedirs(full_path)
            print(f"目录创建成功")
        
        # 检查是否已经是Git仓库
        git_dir = os.path.join(full_path, '.git')
        if os.path.exists(git_dir):
            print(f"该目录已经是Git仓库")
            return git.Repo(full_path)
        
        # 初始化仓库
        print(f"开始初始化Git仓库...")
        repo = git.Repo.init(full_path, initial_branch="main")
        print(f"仓库初始化成功")
        
        # 创建README文件
        readme_path = os.path.join(full_path, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {os.path.basename(full_path)}\n\n初始化的Git仓库")
        print(f"README.md创建成功")
        
        # 添加并提交
        repo.git.add('README.md')
        repo.git.commit('-m', '初始化仓库，添加README')
        print(f"初始提交完成")
        
        return repo
    except Exception as e:
        print(f"初始化仓库失败: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("MGit仓库创建调试工具")
    print("=" * 50)
    
    # 检查运行环境
    if hasattr(sys, '_MEIPASS'):
        print(f"当前在PyInstaller环境中运行")
        print(f"临时目录: {sys._MEIPASS}")
    else:
        print(f"当前在普通Python环境中运行")
    
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本位置: {os.path.abspath(__file__)}")
    print()
    
    # 获取用户输入
    path = input("请输入要创建仓库的路径: ")
    if not path:
        path = os.getcwd()
        print(f"使用当前目录: {path}")
    
    name = input("请输入仓库名称(留空则直接使用输入的路径): ")
    
    # 调试路径
    print("\n路径信息:")
    debug_path(path)
    
    if name:
        full_path = os.path.join(path, name)
        debug_path(full_path)
    
    # 尝试初始化仓库
    repo = init_repository(path, name)
    
    if repo:
        print("\n仓库初始化成功!")
        print(f"仓库路径: {repo.working_dir}")
    else:
        print("\n仓库初始化失败!")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main() 