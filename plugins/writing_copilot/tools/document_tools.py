#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Document and Git tools for the Writing Copilot agent
"""

import os
from typing import List
from langchain.tools import Tool
from src.utils.logger import info, warning, error


def _validate_path(file_path: str) -> tuple:
    """
    验证文件路径安全性，防止路径遍历攻击
    
    Args:
        file_path: 要验证的文件路径
    
    Returns:
        (is_valid, error_message_or_resolved_path)
    """
    try:
        # 获取当前工作目录作为基准目录
        base_dir = os.path.abspath(os.getcwd())
        
        # 解析为绝对路径
        abs_path = os.path.abspath(file_path)
        
        # 检查路径是否在允许的目录内
        if not abs_path.startswith(base_dir + os.sep) and abs_path != base_dir:
            return False, f"安全错误: 不允许访问工作目录之外的文件 - {file_path}"
        
        return True, abs_path
    except Exception as e:
        return False, f"路径验证失败: {str(e)}"


def create_document_tools(app) -> List[Tool]:
    """创建文档操作工具"""
    
    def read_current_document() -> str:
        """读取当前文档内容"""
        try:
            if hasattr(app, 'editor') and app.editor:
                content = app.editor.toPlainText()
                return f"当前文档内容:\n{content}"
            return "错误: 未打开任何文档"
        except Exception as e:
            return f"读取文档失败: {str(e)}"
    
    def read_document(file_path: str) -> str:
        """读取指定文档内容"""
        try:
            # 验证路径安全性
            is_valid, result = _validate_path(file_path)
            if not is_valid:
                return result
            
            validated_path = result
            
            if not os.path.exists(validated_path):
                return f"错误: 文件不存在 - {file_path}"
            
            with open(validated_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"文档内容 ({file_path}):\n{content}"
        except Exception as e:
            return f"读取文档失败: {str(e)}"
    
    def write_document(file_path: str, content: str) -> str:
        """写入文档内容"""
        try:
            # 验证路径安全性
            is_valid, result = _validate_path(file_path)
            if not is_valid:
                return result
            
            validated_path = result
            
            # 创建目录（如果不存在）
            dir_name = os.path.dirname(validated_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            with open(validated_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            info(f"文档已写入: {file_path}")
            return f"成功: 文档已保存到 {file_path}"
        except Exception as e:
            error(f"写入文档失败: {str(e)}")
            return f"写入文档失败: {str(e)}"
    
    def edit_current_document(content: str) -> str:
        """编辑当前文档"""
        try:
            if hasattr(app, 'editor') and app.editor:
                app.editor.setPlainText(content)
                info("当前文档已更新")
                return "成功: 当前文档已更新"
            return "错误: 未打开任何文档"
        except Exception as e:
            error(f"编辑文档失败: {str(e)}")
            return f"编辑文档失败: {str(e)}"
    
    def append_to_document(content: str) -> str:
        """在当前文档末尾追加内容"""
        try:
            if hasattr(app, 'editor') and app.editor:
                current_content = app.editor.toPlainText()
                new_content = current_content + "\n" + content
                app.editor.setPlainText(new_content)
                info("内容已追加到文档")
                return "成功: 内容已追加"
            return "错误: 未打开任何文档"
        except Exception as e:
            error(f"追加内容失败: {str(e)}")
            return f"追加内容失败: {str(e)}"
    
    def insert_at_cursor(content: str) -> str:
        """在光标位置插入内容"""
        try:
            if hasattr(app, 'editor') and app.editor:
                cursor = app.editor.textCursor()
                cursor.insertText(content)
                info("内容已插入")
                return "成功: 内容已插入到光标位置"
            return "错误: 未打开任何文档"
        except Exception as e:
            error(f"插入内容失败: {str(e)}")
            return f"插入内容失败: {str(e)}"
    
    def list_documents(directory: str = ".") -> str:
        """列出目录中的文档"""
        try:
            # 验证路径安全性
            is_valid, result = _validate_path(directory)
            if not is_valid:
                return result
            
            validated_dir = result
            
            if not os.path.exists(validated_dir):
                return f"错误: 目录不存在 - {directory}"
            
            # 深度和文件数量限制，防止资源耗尽
            MAX_DEPTH = 5
            MAX_FILES = 1000
            
            files = []
            start_depth = validated_dir.rstrip(os.sep).count(os.sep)
            
            for root, dirs, filenames in os.walk(validated_dir):
                current_depth = root.rstrip(os.sep).count(os.sep) - start_depth
                if current_depth >= MAX_DEPTH:
                    # 不再向更深层目录递归
                    dirs[:] = []
                
                for filename in filenames:
                    if filename.endswith(('.md', '.txt', '.markdown')):
                        files.append(os.path.join(root, filename))
                        if len(files) >= MAX_FILES:
                            warning(f"list_documents: 已达到文件数量上限 {MAX_FILES}，结果已被截断。")
                            break
                if len(files) >= MAX_FILES:
                    break
            
            if not files:
                return f"目录 {directory} 中没有找到文档"
            
            result = "找到的文档:\n" + "\n".join(files)
            if len(files) >= MAX_FILES:
                result += f"\n警告: 已达到文件数量上限 {MAX_FILES}，结果可能不完整。"
            return result
        except Exception as e:
            return f"列出文档失败: {str(e)}"
    
    # 创建工具列表
    tools = [
        Tool(
            name="read_current_document",
            func=lambda x: read_current_document(),
            description="读取当前打开的文档内容。不需要参数。"
        ),
        Tool(
            name="read_document",
            func=read_document,
            description="读取指定路径的文档内容。输入: 文件路径"
        ),
        Tool(
            name="write_document",
            func=lambda x: write_document(*x.split('|', 1)) if '|' in x else "错误: 需要格式 'file_path|content'。注意：如果内容包含'|'字符，仅第一个'|'将作为分隔符。",
            description="将内容写入指定文件。输入格式: 'file_path|content'（第一个'|'作为分隔符）"
        ),
        Tool(
            name="edit_current_document",
            func=edit_current_document,
            description="用新内容替换当前文档的所有内容。输入: 新的文档内容"
        ),
        Tool(
            name="append_to_document",
            func=append_to_document,
            description="在当前文档末尾追加内容。输入: 要追加的内容"
        ),
        Tool(
            name="insert_at_cursor",
            func=insert_at_cursor,
            description="在光标当前位置插入内容。输入: 要插入的内容"
        ),
        Tool(
            name="list_documents",
            func=list_documents,
            description="列出指定目录中的所有文档（.md, .txt, .markdown）。输入: 目录路径（可选，默认为当前目录）"
        ),
    ]
    
    return tools


def create_git_tools(app) -> List[Tool]:
    """创建Git操作工具"""
    
    def get_git_manager():
        """获取Git管理器"""
        if hasattr(app, 'gitManager') and app.gitManager:
            return app.gitManager
        return None
    
    def create_branch(branch_name: str) -> str:
        """创建新分支"""
        try:
            git_manager = get_git_manager()
            if not git_manager:
                return "错误: Git管理器不可用"
            
            git_manager.create_branch(branch_name)
            info(f"分支已创建: {branch_name}")
            return f"成功: 已创建分支 {branch_name}"
        except Exception as e:
            error(f"创建分支失败: {str(e)}")
            return f"创建分支失败: {str(e)}"
    
    def switch_branch(branch_name: str) -> str:
        """切换分支"""
        try:
            git_manager = get_git_manager()
            if not git_manager:
                return "错误: Git管理器不可用"
            
            git_manager.checkout_branch(branch_name)
            info(f"已切换到分支: {branch_name}")
            return f"成功: 已切换到分支 {branch_name}"
        except Exception as e:
            error(f"切换分支失败: {str(e)}")
            return f"切换分支失败: {str(e)}"
    
    def commit_changes(message: str) -> str:
        """提交更改"""
        try:
            git_manager = get_git_manager()
            if not git_manager:
                return "错误: Git管理器不可用"
            
            # 添加所有更改
            git_manager.stage_all()
            
            # 提交
            git_manager.commit(message)
            info(f"已提交更改: {message}")
            return f"成功: 已提交更改 - {message}"
        except Exception as e:
            error(f"提交失败: {str(e)}")
            return f"提交失败: {str(e)}"
    
    def get_git_status() -> str:
        """获取Git状态"""
        try:
            git_manager = get_git_manager()
            if not git_manager:
                return "错误: Git管理器不可用"
            
            status = git_manager.get_status()
            return f"Git状态:\n{status}"
        except Exception as e:
            return f"获取状态失败: {str(e)}"
    
    def list_branches() -> str:
        """列出所有分支"""
        try:
            git_manager = get_git_manager()
            if not git_manager:
                return "错误: Git管理器不可用"
            
            branches = git_manager.list_branches()
            current = git_manager.current_branch()
            
            result = f"当前分支: {current}\n\n所有分支:\n"
            result += "\n".join(f"{'* ' if b == current else '  '}{b}" for b in branches)
            
            return result
        except Exception as e:
            return f"列出分支失败: {str(e)}"
    
    def get_commit_history(limit: int = 10) -> str:
        """获取提交历史"""
        try:
            git_manager = get_git_manager()
            if not git_manager:
                return "错误: Git管理器不可用"
            
            history = git_manager.get_commit_history(limit)
            return f"最近{limit}次提交:\n{history}"
        except Exception as e:
            return f"获取提交历史失败: {str(e)}"
    
    # 创建工具列表
    tools = [
        Tool(
            name="create_branch",
            func=create_branch,
            description="创建新的Git分支。输入: 分支名称"
        ),
        Tool(
            name="switch_branch",
            func=switch_branch,
            description="切换到指定的Git分支。输入: 分支名称"
        ),
        Tool(
            name="commit_changes",
            func=commit_changes,
            description="提交当前所有更改。输入: 提交消息"
        ),
        Tool(
            name="get_git_status",
            func=lambda x: get_git_status(),
            description="获取当前Git仓库状态。不需要参数。"
        ),
        Tool(
            name="list_branches",
            func=lambda x: list_branches(),
            description="列出所有Git分支。不需要参数。"
        ),
        Tool(
            name="get_commit_history",
            func=lambda x: get_commit_history(_safe_int(x, 10)),
            description="获取提交历史。输入: 要显示的提交数量（可选，默认10）"
        ),
    ]
    
    def _safe_int(value: str, default: int = 10) -> int:
        """安全地将字符串转换为整数"""
        try:
            if value and value.strip().isdigit():
                return int(value.strip())
            return default
        except (ValueError, AttributeError):
            return default
    
    return tools
