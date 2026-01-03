#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent Mode - Autonomous task execution with audit system
"""

from typing import List, Dict, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
import json
import os
from .siliconflow_client import SiliconFlowClient
from src.utils.logger import info, warning, error
from src.utils.git_manager import GitManager


class AgentTask:
    """Represents an agent task"""
    
    def __init__(self, task_id: str, description: str, task_type: str):
        self.task_id = task_id
        self.description = description
        self.task_type = task_type  # read, edit, create, branch, commit
        self.status = 'pending'  # pending, in_progress, completed, failed, auditing, approved, rejected
        self.created_at = datetime.now()
        self.completed_at = None
        self.result = None
        self.error = None
        self.changes = []  # List of changes made
        self.audit_comments = []
        
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'description': self.description,
            'task_type': self.task_type,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'changes': self.changes,
            'audit_comments': self.audit_comments
        }


class AgentMode(QObject):
    """
    Agent mode for autonomous task execution
    Includes audit system similar to GitHub branch/PR workflow
    """
    
    task_started = pyqtSignal(str)  # task_id
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error
    task_needs_audit = pyqtSignal(str)  # task_id
    status_changed = pyqtSignal(str)
    
    def __init__(self, client: SiliconFlowClient, git_manager: Optional[GitManager] = None):
        super().__init__()
        self.client = client
        self.git_manager = git_manager
        self.tasks: Dict[str, AgentTask] = {}
        self.task_counter = 0
        
    def create_task(self, description: str, task_type: str) -> str:
        """
        Create a new agent task
        
        Args:
            description: Task description
            task_type: Type of task
            
        Returns:
            Task ID
        """
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task = AgentTask(task_id, description, task_type)
        self.tasks[task_id] = task
        info(f"Created agent task: {task_id}")
        return task_id
        
    def execute_task(self, task_id: str, context: Dict = None):
        """
        Execute an agent task
        
        Args:
            task_id: Task ID
            context: Additional context for task execution
        """
        if task_id not in self.tasks:
            error(f"Task not found: {task_id}")
            return
            
        task = self.tasks[task_id]
        task.status = 'in_progress'
        self.task_started.emit(task_id)
        self.status_changed.emit(f"Executing task: {task.description}")
        
        # Create execution thread
        thread = TaskExecutionThread(
            self.client,
            task,
            context or {},
            self.git_manager
        )
        thread.task_completed.connect(self._on_task_completed)
        thread.task_failed.connect(self._on_task_failed)
        thread.start()
        
    def read_document(self, file_path: str, callback: Optional[Callable] = None) -> str:
        """
        Read document content
        
        Args:
            file_path: Path to document
            callback: Optional callback
            
        Returns:
            Task ID
        """
        task_id = self.create_task(f"Read document: {file_path}", "read")
        context = {'file_path': file_path}
        self.execute_task(task_id, context)
        
        if callback:
            self.task_completed.connect(
                lambda tid, result: callback(result) if tid == task_id else None
            )
            
        return task_id
        
    def edit_document(
        self,
        file_path: str,
        instruction: str,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Edit document based on instruction
        
        Args:
            file_path: Path to document
            instruction: Edit instruction
            callback: Optional callback
            
        Returns:
            Task ID
        """
        task_id = self.create_task(f"Edit document: {file_path}", "edit")
        context = {
            'file_path': file_path,
            'instruction': instruction
        }
        self.execute_task(task_id, context)
        
        if callback:
            self.task_completed.connect(
                lambda tid, result: callback(result) if tid == task_id else None
            )
            
        return task_id
        
    def create_document(
        self,
        file_path: str,
        prompt: str,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Create new document
        
        Args:
            file_path: Path for new document
            prompt: Creation prompt
            callback: Optional callback
            
        Returns:
            Task ID
        """
        task_id = self.create_task(f"Create document: {file_path}", "create")
        context = {
            'file_path': file_path,
            'prompt': prompt
        }
        self.execute_task(task_id, context)
        
        if callback:
            self.task_completed.connect(
                lambda tid, result: callback(result) if tid == task_id else None
            )
            
        return task_id
        
    def create_branch(self, branch_name: str, callback: Optional[Callable] = None) -> str:
        """
        Create new Git branch
        
        Args:
            branch_name: Name for new branch
            callback: Optional callback
            
        Returns:
            Task ID
        """
        if not self.git_manager:
            error("Git manager not available")
            return None
            
        task_id = self.create_task(f"Create branch: {branch_name}", "branch")
        context = {'branch_name': branch_name}
        self.execute_task(task_id, context)
        
        if callback:
            self.task_completed.connect(
                lambda tid, result: callback(result) if tid == task_id else None
            )
            
        return task_id
        
    def commit_changes(
        self,
        message: str,
        files: List[str] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Commit changes to Git
        
        Args:
            message: Commit message
            files: List of files to commit (None = all)
            callback: Optional callback
            
        Returns:
            Task ID
        """
        if not self.git_manager:
            error("Git manager not available")
            return None
            
        task_id = self.create_task(f"Commit changes: {message}", "commit")
        context = {
            'commit_message': message,
            'files': files
        }
        self.execute_task(task_id, context)
        
        if callback:
            self.task_completed.connect(
                lambda tid, result: callback(result) if tid == task_id else None
            )
            
        return task_id
        
    def audit_task(self, task_id: str, approved: bool, comment: str = ""):
        """
        Audit a completed task
        
        Args:
            task_id: Task ID
            approved: Whether task is approved
            comment: Audit comment
        """
        if task_id not in self.tasks:
            error(f"Task not found: {task_id}")
            return
            
        task = self.tasks[task_id]
        
        audit_record = {
            'timestamp': datetime.now().isoformat(),
            'approved': approved,
            'comment': comment
        }
        task.audit_comments.append(audit_record)
        
        if approved:
            task.status = 'approved'
            info(f"Task {task_id} approved")
            # Apply changes if needed
            self._apply_task_changes(task)
        else:
            task.status = 'rejected'
            warning(f"Task {task_id} rejected: {comment}")
            
        self.status_changed.emit(f"Task {'approved' if approved else 'rejected'}")
        
    def _apply_task_changes(self, task: AgentTask):
        """Apply approved task changes"""
        if task.task_type in ['edit', 'create']:
            # Changes already in result, application should handle
            pass
        elif task.task_type == 'commit':
            # Commit was already made during execution
            pass
            
        info(f"Applied changes for task {task.task_id}")
        
    def _on_task_completed(self, task_id: str, result: object):
        """Handle task completion"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = 'completed'
            task.completed_at = datetime.now()
            task.result = result
            
            # Tasks that modify content need audit
            if task.task_type in ['edit', 'create', 'commit']:
                task.status = 'auditing'
                self.task_needs_audit.emit(task_id)
                info(f"Task {task_id} needs audit")
            else:
                task.status = 'approved'
                
            self.task_completed.emit(task_id, result)
            self.status_changed.emit("Task completed")
            
    def _on_task_failed(self, task_id: str, error_msg: str):
        """Handle task failure"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = 'failed'
            task.completed_at = datetime.now()
            task.error = error_msg
            
            self.task_failed.emit(task_id, error_msg)
            self.status_changed.emit(f"Task failed: {error_msg}")
            
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
        
    def get_pending_audits(self) -> List[AgentTask]:
        """Get tasks pending audit"""
        return [task for task in self.tasks.values() if task.status == 'auditing']
        
    def export_task_history(self, file_path: str):
        """Export task history to file"""
        history = [task.to_dict() for task in self.tasks.values()]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        info(f"Task history exported to {file_path}")


class TaskExecutionThread(QThread):
    """Thread for executing agent tasks"""
    
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)  # task_id, error_msg
    
    def __init__(
        self,
        client: SiliconFlowClient,
        task: AgentTask,
        context: Dict,
        git_manager: Optional[GitManager]
    ):
        super().__init__()
        self.client = client
        self.task = task
        self.context = context
        self.git_manager = git_manager
        
    def run(self):
        try:
            task_type = self.task.task_type
            
            if task_type == 'read':
                result = self._execute_read()
            elif task_type == 'edit':
                result = self._execute_edit()
            elif task_type == 'create':
                result = self._execute_create()
            elif task_type == 'branch':
                result = self._execute_branch()
            elif task_type == 'commit':
                result = self._execute_commit()
            else:
                raise ValueError(f"Unknown task type: {task_type}")
                
            self.task_completed.emit(self.task.task_id, result)
            
        except Exception as e:
            self.task_failed.emit(self.task.task_id, str(e))
            
    def _execute_read(self) -> str:
        """Execute read task"""
        file_path = self.context.get('file_path')
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.task.changes.append({
            'action': 'read',
            'file': file_path,
            'size': len(content)
        })
        
        return content
        
    def _execute_edit(self) -> Dict:
        """Execute edit task"""
        file_path = self.context.get('file_path')
        instruction = self.context.get('instruction')
        
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        # Generate edit using AI
        prompt = f"""你是一个专业的文档编辑助手。请根据指令编辑以下文档。

原文档内容：
{original_content}

编辑指令：
{instruction}

请返回编辑后的完整文档内容（只返回文档内容，不要包含任何解释）："""

        messages = [{'role': 'user', 'content': prompt}]
        response = self.client.chat_completion(messages, temperature=0.5, max_tokens=4096)
        
        if 'choices' not in response or len(response['choices']) == 0:
            raise RuntimeError("Failed to generate edit")
            
        edited_content = response['choices'][0]['message']['content'].strip()
        
        self.task.changes.append({
            'action': 'edit',
            'file': file_path,
            'original_size': len(original_content),
            'new_size': len(edited_content)
        })
        
        return {
            'file_path': file_path,
            'original_content': original_content,
            'edited_content': edited_content
        }
        
    def _execute_create(self) -> Dict:
        """Execute create task"""
        file_path = self.context.get('file_path')
        prompt = self.context.get('prompt')
        
        if not file_path:
            raise ValueError("File path not provided")
            
        # Generate content using AI
        system_prompt = """你是一个专业的文档写作助手。请根据用户需求创作高质量的Markdown文档。
文档应该结构清晰、内容充实、格式规范。"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': prompt}
        ]
        response = self.client.chat_completion(messages, temperature=0.8, max_tokens=4096)
        
        if 'choices' not in response or len(response['choices']) == 0:
            raise RuntimeError("Failed to generate content")
            
        content = response['choices'][0]['message']['content'].strip()
        
        self.task.changes.append({
            'action': 'create',
            'file': file_path,
            'size': len(content)
        })
        
        return {
            'file_path': file_path,
            'content': content
        }
        
    def _execute_branch(self) -> str:
        """Execute branch creation task"""
        if not self.git_manager:
            raise RuntimeError("Git manager not available")
            
        branch_name = self.context.get('branch_name')
        if not branch_name:
            raise ValueError("Branch name not provided")
            
        # Create branch using git manager
        self.git_manager.create_branch(branch_name)
        
        self.task.changes.append({
            'action': 'branch',
            'branch_name': branch_name
        })
        
        return branch_name
        
    def _execute_commit(self) -> Dict:
        """Execute commit task"""
        if not self.git_manager:
            raise RuntimeError("Git manager not available")
            
        commit_message = self.context.get('commit_message')
        files = self.context.get('files')
        
        if not commit_message:
            raise ValueError("Commit message not provided")
            
        # Add and commit files
        if files:
            for file in files:
                self.git_manager.repo.index.add([file])
        else:
            self.git_manager.repo.git.add(A=True)
            
        commit = self.git_manager.repo.index.commit(commit_message)
        
        self.task.changes.append({
            'action': 'commit',
            'message': commit_message,
            'sha': commit.hexsha,
            'files': files or 'all'
        })
        
        return {
            'commit_sha': commit.hexsha,
            'message': commit_message
        }
