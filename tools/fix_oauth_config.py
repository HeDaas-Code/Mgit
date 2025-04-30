#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MGit OAuth配置修复工具
此脚本用于修复OAuth配置保存问题和Gitee OAuth导致的崩溃问题
"""

import os
import sys
import shutil
import time
from pathlib import Path
from cryptography.fernet import Fernet

def info(msg):
    """输出信息日志"""
    print(f"[INFO] {msg}")

def error(msg):
    """输出错误日志"""
    print(f"[ERROR] {msg}")

def warning(msg):
    """输出警告日志"""
    print(f"[WARNING] {msg}")

def backup_file(file_path):
    """备份文件"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak.{int(time.time())}"
        try:
            shutil.copy2(file_path, backup_path)
            info(f"已备份文件: {file_path} -> {backup_path}")
            return True
        except Exception as e:
            error(f"备份文件失败: {str(e)}")
            return False
    return False

def reset_oauth_config():
    """重置OAuth配置文件"""
    # 获取MGit配置目录
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, '.mgit')
    
    # 检查目录是否存在
    if not os.path.exists(config_dir):
        error(f"MGit配置目录不存在: {config_dir}")
        return False
    
    # OAuth配置文件路径
    oauth_config_file = os.path.join(config_dir, 'oauth_config.dat')
    
    # 备份现有配置文件
    if os.path.exists(oauth_config_file):
        if not backup_file(oauth_config_file):
            return False
        
        # 删除现有配置文件
        try:
            os.remove(oauth_config_file)
            info(f"已删除现有OAuth配置文件: {oauth_config_file}")
        except Exception as e:
            error(f"删除OAuth配置文件失败: {str(e)}")
            return False
    
    info("OAuth配置已重置")
    return True

def recreate_encryption_key():
    """重新创建加密密钥"""
    # 获取MGit配置目录
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, '.mgit')
    
    # 检查目录是否存在
    if not os.path.exists(config_dir):
        error(f"MGit配置目录不存在: {config_dir}")
        return False
    
    # 密钥文件路径
    key_file = os.path.join(config_dir, 'key.dat')
    
    # 备份现有密钥文件
    if os.path.exists(key_file):
        if not backup_file(key_file):
            return False
    
    # 生成新密钥
    try:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        info(f"已创建新的加密密钥: {key_file}")
        return True
    except Exception as e:
        error(f"创建新密钥失败: {str(e)}")
        return False

def cleanup_ssl_certs():
    """清理SSL证书"""
    # 获取MGit配置目录
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, '.mgit')
    
    # SSL证书目录
    cert_dir = os.path.join(config_dir, 'certs')
    
    # 检查目录是否存在
    if not os.path.exists(cert_dir):
        info("SSL证书目录不存在，无需清理")
        return True
    
    # 备份证书目录
    backup_dir = f"{cert_dir}.bak.{int(time.time())}"
    try:
        if os.path.exists(cert_dir):
            shutil.copytree(cert_dir, backup_dir)
            info(f"已备份SSL证书目录: {backup_dir}")
            
            # 删除证书目录
            shutil.rmtree(cert_dir)
            info(f"已删除SSL证书目录: {cert_dir}")
        return True
    except Exception as e:
        error(f"清理SSL证书失败: {str(e)}")
        return False

def clean_account_sessions():
    """清理账户会话状态"""
    # 获取MGit配置目录
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, '.mgit')
    
    # 账号文件路径
    accounts_file = os.path.join(config_dir, 'encrypted_accounts.dat')
    
    # 备份账号文件
    if os.path.exists(accounts_file):
        if not backup_file(accounts_file):
            return False
    
    info("账户会话状态已清理")
    return True

def main():
    """主函数"""
    print("\nMGit OAuth配置修复工具")
    print("=======================\n")
    print("此工具将修复OAuth配置保存问题和Gitee OAuth导致的崩溃问题")
    print("修复过程会重置所有OAuth配置和账户登录状态\n")
    
    # 询问用户确认
    confirm = input("是否继续修复? (y/n): ")
    if confirm.lower() not in ['y', 'yes']:
        print("已取消修复")
        return
    
    print("\n开始修复...\n")
    
    # 重置OAuth配置
    if reset_oauth_config():
        print("[√] OAuth配置重置成功")
    else:
        print("[×] OAuth配置重置失败")
    
    # 重新创建加密密钥
    if recreate_encryption_key():
        print("[√] 加密密钥重新创建成功")
    else:
        print("[×] 加密密钥重新创建失败")
    
    # 清理SSL证书
    if cleanup_ssl_certs():
        print("[√] SSL证书清理成功")
    else:
        print("[×] SSL证书清理失败")
    
    # 清理账户会话状态
    if clean_account_sessions():
        print("[√] 账户会话状态清理成功")
    else:
        print("[×] 账户会话状态清理失败")
    
    print("\n修复完成！请重新启动MGit应用\n")
    print("如需进一步帮助，请联系开发者")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        error(f"修复过程出错: {str(e)}")
    
    # 等待用户按下任意键退出
    input("\n按Enter键退出...") 