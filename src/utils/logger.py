#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
高级日志模块 - 基于Loguru实现
提供丰富的日志记录功能和上下文管理
"""

import os
import sys
import time
import json
import platform
import socket
import inspect
import threading
import traceback
import tempfile
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union

from loguru import logger

# 日志级别枚举
class LogLevel(str, Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

# 日志类别枚举
class LogCategory(str, Enum):
    SYSTEM = "系统"
    UI = "界面"
    DATABASE = "数据库"
    NETWORK = "网络"
    REPOSITORY = "仓库"  # 替换原有的Git分类
    PROJECT = "项目"     # 新增项目分类
    IO = "IO"
    PLUGIN = "插件"
    SECURITY = "安全"
    PERFORMANCE = "性能"
    USER = "用户操作"
    CONFIG = "配置"      # 新增配置分类
    UPDATE = "更新"      # 新增更新分类
    API = "API"
    ERROR = "错误"

# 系统信息获取
def get_system_info() -> Dict[str, str]:
    """获取系统信息
    Returns:
        Dict[str, str]: 系统信息字典
    """
    info = {
        "系统": platform.system(),
        "版本": platform.version(),
        "发布": platform.release(),
        "架构": platform.machine(),
        "处理器": platform.processor(),
        "Python版本": platform.python_version(),
        "主机名": socket.gethostname(),
        "用户": os.getenv("USERNAME") or os.getenv("USER") or "未知",
        "时区": time.strftime("%Z", time.localtime()),
        "当前目录": os.getcwd(),
        "PID": os.getpid(),
    }
    
    # 获取已安装软件包
    try:
        import pkg_resources
        packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])
        info["已安装包"] = packages
    except:
        info["已安装包"] = []
        
    return info

# 确保资源路径正确
def resource_path(relative_path):
    """ 获取资源的绝对路径，处理PyInstaller打包后的路径 """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def get_log_dir():
    """获取日志目录，确保其存在"""
    try:
        # 首先尝试使用用户主目录
        home_dir = str(Path.home())
        log_dir = os.path.join(home_dir, '.mgit', 'logs')
    except Exception:
        # 如果无法获取主目录，使用临时目录
        log_dir = os.path.join(tempfile.gettempdir(), 'mgit', 'logs')
    
    # 确保目录存在
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except Exception:
            # 如果创建失败，回退到临时目录
            log_dir = os.path.join(tempfile.gettempdir(), 'mgit', 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
    
    return log_dir

# 上下文记录器
class LogContext:
    """日志上下文管理器，用于分组记录操作"""
    
    _local = threading.local()
    
    @classmethod
    def get_current_context(cls) -> Dict[str, Any]:
        """获取当前线程的日志上下文
        Returns:
            Dict[str, Any]: 当前上下文信息
        """
        if not hasattr(cls._local, 'context'):
            cls._local.context = {}
        return cls._local.context
    
    @classmethod
    def set_context(cls, key: str, value: Any):
        """设置上下文变量
        Args:
            key: 上下文键名
            value: 上下文值
        """
        context = cls.get_current_context()
        context[key] = value
    
    @classmethod
    def remove_context(cls, key: str):
        """移除上下文变量
        Args:
            key: 上下文键名
        """
        context = cls.get_current_context()
        if key in context:
            del context[key]
            
    @classmethod
    def clear_context(cls):
        """清空上下文"""
        if hasattr(cls._local, 'context'):
            cls._local.context = {}
        
    def __init__(self, **kwargs):
        self.prev_context = {}
        self.kwargs = kwargs
    
    def __enter__(self):
        context = self.get_current_context()
        self.prev_context = context.copy()
        context.update(self.kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._local.context = self.prev_context

# 日志格式化工具
class LogFormatter:
    """日志格式化器，提供多种格式化方法"""
    
    @staticmethod
    def format_dict(d: Dict[str, Any]) -> str:
        """将字典格式化为日志友好字符串
        Args:
            d: 要格式化的字典
        Returns:
            str: 格式化后的字符串
        """
        try:
            return json.dumps(d, ensure_ascii=False, indent=2)
        except:
            return str(d)
    
    @staticmethod
    def format_exception(e: Exception) -> str:
        """格式化异常信息
        Args:
            e: 异常对象
        Returns:
            str: 格式化后的异常信息
        """
        tb = traceback.format_exception(type(e), e, e.__traceback__)
        return ''.join(tb)
    
    @staticmethod
    def format_context(context: Dict[str, Any]) -> str:
        """格式化上下文信息
        Args:
            context: 上下文字典
        Returns:
            str: 格式化后的上下文信息
        """
        if not context:
            return ""
            
        parts = []
        for k, v in context.items():
            if isinstance(v, dict):
                parts.append(f"{k}={{{','.join(f'{sk}:{sv}' for sk, sv in v.items())}}}")
            else:
                parts.append(f"{k}={v}")
        
        return "[" + ", ".join(parts) + "]"

class Logger:
    """应用日志记录器，提供统一的日志记录接口，基于Loguru实现"""
    
    # 单例模式
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, app_name="MGit", log_level="INFO"):
        # 避免重复初始化
        if self._initialized:
            return
            
        self._initialized = True
        self.app_name = app_name
        self.start_time = datetime.now()
        
        # 使用获取日志目录的函数
        self.log_dir = get_log_dir()
        
        # 设置日志文件路径
        self.log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}.log")
        
        # 模块分类日志文件 
        self.category_log_dir = os.path.join(self.log_dir, "categories")
        os.makedirs(self.category_log_dir, exist_ok=True)
        
        # 性能日志路径
        self.perf_log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}_perf.log")
        
        # 错误日志路径（单独存储错误和关键日志）
        self.error_log_file = os.path.join(self.log_dir, f"{self.app_name.lower()}_error.log")
        
        # 初始化系统信息
        self.system_info = get_system_info()
        
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器 - 彩色输出
        logger.add(
            sys.stdout, 
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <blue>{extra[category]}</blue> - <level>{message}</level>",
            level=log_level,
            filter=self._log_filter
        )
        
        # 添加主文件处理器 - 记录所有日志
        logger.add(
            self.log_file,
            rotation="10 MB",
            retention="30 days",
            compression="zip", 
            encoding="utf-8",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {thread.name}({thread.id}) | {extra[category]} | {extra[context]} - {message}",
            filter=self._log_filter
        )
        
        # 添加错误日志处理器 - 仅记录ERROR及以上级别
        logger.add(
            self.error_log_file,
            rotation="5 MB",
            retention="60 days",  # 错误日志保留更长时间
            compression="zip",
            encoding="utf-8",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {thread.name}({thread.id}) | {extra[category]} | {extra[context]} - {message}",
            filter=self._log_filter
        )
        
        # 添加性能日志处理器
        logger.add(
            self.perf_log_file,
            rotation="5 MB",
            retention="14 days",
            compression="zip",
            encoding="utf-8",
            level="TRACE",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            filter=lambda record: record["extra"].get("category") == "性能"
        )
        
        # 为每个类别创建专用日志文件
        for category in LogCategory:
            category_file = os.path.join(self.category_log_dir, f"{category.value.lower()}.log")
            logger.add(
                category_file,
                rotation="5 MB",
                retention="14 days",
                compression="zip",
                encoding="utf-8",
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
                filter=lambda record, cat=category.value: record["extra"].get("category") == cat
            )
        
        # 初始化上下文记录器
        self.context = LogContext()
        
        # 记录启动日志
        with logger.contextualize(category="系统", context=""):
            logger.info(f"====== {self.app_name} 日志系统启动 ======")
            logger.info(f"日志文件路径: {self.log_file}")
            
            # 记录系统信息
            logger.info(f"系统信息: {platform.system()} {platform.release()} ({platform.version()})")
            logger.info(f"Python版本: {platform.python_version()}")
            logger.info(f"操作系统: {platform.platform()}")
            logger.info(f"主机名: {socket.gethostname()}")
    
    def _log_filter(self, record):
        """自定义日志过滤器
        Args:
            record: 日志记录对象
        Returns:
            bool: 是否记录该日志
        """
        # 确保额外字段存在
        if "category" not in record["extra"]:
            record["extra"]["category"] = "系统"
        if "context" not in record["extra"]:
            # 获取当前上下文
            context = LogContext.get_current_context()
            record["extra"]["context"] = LogFormatter.format_context(context)
        
        return True
    
    def log(self, level: Union[str, LogLevel], message: str, category: Union[str, LogCategory] = None, **kwargs):
        """通用日志记录方法
        Args:
            level: 日志级别
            message: 日志消息
            category: 日志类别
            **kwargs: 额外参数，会添加到上下文
        """
        if not category:
            # 尝试从调用栈获取合适的类别
            stack = inspect.stack()
            if len(stack) > 1:
                module = stack[1].frame.f_globals.get("__name__", "")
                if "ui" in module or "view" in module:
                    category = LogCategory.UI
                elif "git" in module:
                    category = LogCategory.REPOSITORY
                elif "db" in module or "database" in module:
                    category = LogCategory.DATABASE
                elif "net" in module or "http" in module:
                    category = LogCategory.NETWORK
                elif "plugin" in module:
                    category = LogCategory.PLUGIN
                elif "io" in module or "file" in module:
                    category = LogCategory.IO
                else:
                    category = LogCategory.SYSTEM
        
        # 获取调用者信息
        frame = inspect.currentframe().f_back
        file_name = frame.f_code.co_filename
        func_name = frame.f_code.co_name
        line_no = frame.f_lineno
        
        # 创建上下文
        context = {}
        if kwargs:
            context.update(kwargs)
            
        # 合并当前线程上下文
        thread_context = LogContext.get_current_context()
        if thread_context:
            context.update(thread_context)
            
        # 格式化上下文
        context_str = LogFormatter.format_context(context)
        
        # 使用Loguru的contextualize功能
        with logger.contextualize(category=category, context=context_str):
            logger_method = getattr(logger, level.lower() if isinstance(level, str) else level.value.lower())
            logger_method(message)
            
    def debug(self, message: str, category: Union[str, LogCategory] = None, **kwargs):
        """记录调试级别日志"""
        self.log(LogLevel.DEBUG, message, category, **kwargs)
    
    def info(self, message: str, category: Union[str, LogCategory] = None, **kwargs):
        """记录信息级别日志"""
        self.log(LogLevel.INFO, message, category, **kwargs)
    
    def success(self, message: str, category: Union[str, LogCategory] = None, **kwargs):
        """记录成功级别日志"""
        self.log(LogLevel.SUCCESS, message, category, **kwargs)
    
    def warning(self, message: str, category: Union[str, LogCategory] = None, **kwargs):
        """记录警告级别日志"""
        self.log(LogLevel.WARNING, message, category, **kwargs)
    
    def error(self, message: str, category: Union[str, LogCategory] = None, **kwargs):
        """记录错误级别日志"""
        self.log(LogLevel.ERROR, message, category, **kwargs)
    
    def critical(self, message: str, category: Union[str, LogCategory] = None, **kwargs):
        """记录严重级别日志"""
        self.log(LogLevel.CRITICAL, message, category, **kwargs)
    
    def exception(self, message: str, exc_info=True, category: Union[str, LogCategory] = None, **kwargs):
        """记录异常日志，包含堆栈信息
        Args:
            message: 异常消息
            exc_info: 是否包含异常信息
            category: 日志类别
            **kwargs: 额外上下文
        """
        with logger.contextualize(category=category or LogCategory.SYSTEM, context=LogFormatter.format_context(kwargs)):
            logger.exception(message)
    
    def trace(self, message: str, category: Union[str, LogCategory] = LogCategory.PERFORMANCE, **kwargs):
        """记录跟踪级别日志，主要用于性能分析
        Args:
            message: 日志消息
            category: 日志类别，默认为"性能"
            **kwargs: 额外上下文
        """
        self.log(LogLevel.TRACE, message, category, **kwargs)
    
    # 性能计时装饰器
    def perf_timer(self, func=None, name=None, threshold_ms=10):
        """性能计时装饰器，记录函数执行时间
        Args:
            func: 被装饰的函数
            name: 计时器名称，默认为函数名
            threshold_ms: 阈值（毫秒），超过此值才记录，默认10ms
        """
        def decorator(fn):
            fn_name = name or fn.__name__
            
            @wraps(fn)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = fn(*args, **kwargs)
                elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 仅当执行时间超过阈值时记录
                if elapsed_time > threshold_ms:
                    self.trace(
                        f"函数 {fn_name} 执行耗时: {elapsed_time:.2f}ms", 
                        function=fn_name,
                        elapsed_ms=elapsed_time
                    )
                return result
            return wrapper
        
        if func:
            return decorator(func)
        return decorator
        
    def get_log_file_path(self):
        """获取当前日志文件路径"""
        return self.log_file
        
    def get_log_dir(self):
        """获取日志目录路径"""
        return self.log_dir
    
    def get_category_log_file(self, category: Union[str, LogCategory]):
        """获取指定类别的日志文件路径
        Args:
            category: 日志类别
        Returns:
            str: 日志文件路径
        """
        if isinstance(category, LogCategory):
            category = category.value
        
        return os.path.join(self.category_log_dir, f"{category.lower()}.log")
        
    def export_log(self, target_path=None, include_categories=False):
        """导出日志文件到指定路径
        Args:
            target_path: 目标路径，如果为None则返回当前日志文件路径
            include_categories: 是否包含类别日志
        Returns:
            Union[str, List[str]]: 导出的日志文件路径(列表)
        """
        import zipfile
        
        if target_path is None:
            # 创建导出目录（如果需要）
            export_dir = os.path.join(os.path.expanduser("~"), "Documents")
            if not os.path.exists(export_dir):
                export_dir = os.path.expanduser("~")
                
            # 生成唯一文件名，包含时间戳
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            if include_categories:
                # 创建zip文件包含所有日志
                target_path = os.path.join(export_dir, f"{self.app_name.lower()}_logs_{timestamp}.zip")
                
                try:
                    with zipfile.ZipFile(target_path, 'w') as zipf:
                        # 添加主日志文件
                        if os.path.exists(self.log_file):
                            zipf.write(self.log_file, os.path.basename(self.log_file))
                        
                        # 添加错误日志
                        if os.path.exists(self.error_log_file):
                            zipf.write(self.error_log_file, os.path.basename(self.error_log_file))
                            
                        # 添加性能日志
                        if os.path.exists(self.perf_log_file):
                            zipf.write(self.perf_log_file, os.path.basename(self.perf_log_file))
                        
                        # 添加分类日志
                        for category in LogCategory:
                            cat_file = self.get_category_log_file(category)
                            if os.path.exists(cat_file):
                                zipf.write(cat_file, f"categories/{os.path.basename(cat_file)}")
                    
                    logger.info(f"日志导出成功(包含类别): {target_path}")
                    return target_path
                except Exception as e:
                    logger.error(f"日志导出失败: {str(e)}")
                    return None
            else:
                # 只导出主日志文件
                target_path = os.path.join(export_dir, f"{self.app_name.lower()}_log_{timestamp}.log")
        
        try:
            import shutil
            # 复制当前日志文件到目标路径
            shutil.copy2(self.log_file, target_path)
            logger.info(f"日志导出成功: {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"日志导出失败: {str(e)}")
            return None
            
    def get_all_log_files(self):
        """获取所有日志文件路径列表
        Returns:
            list: 日志文件路径列表
        """
        log_files = []
        try:
            # 获取主日志文件
            if os.path.exists(self.log_file):
                log_files.append(self.log_file)
            
            # 获取错误日志
            if os.path.exists(self.error_log_file):
                log_files.append(self.error_log_file)
                
            # 获取性能日志
            if os.path.exists(self.perf_log_file):
                log_files.append(self.perf_log_file)
            
            # 获取类别日志
            for category in LogCategory:
                cat_file = self.get_category_log_file(category)
                if os.path.exists(cat_file):
                    log_files.append(cat_file)
            
            # 获取所有轮转日志文件
            import glob
            for zip_file in glob.glob(os.path.join(self.log_dir, "*.zip")):
                log_files.append(zip_file)
                
            # 获取可能的旧格式备份文件（向后兼容）
            for i in range(1, 6):  # 默认最多5个备份
                backup_file = f"{self.log_file}.{i}"
                if os.path.exists(backup_file):
                    log_files.append(backup_file)
        except Exception as e:
            logger.error(f"获取日志文件列表失败: {str(e)}")
            
        return log_files
            
    def get_recent_logs(self, lines=100, category=None):
        """获取最近的日志内容
        Args:
            lines: 要读取的行数
            category: 日志类别，如果指定则读取对应类别的日志
        Returns:
            str: 日志内容
        """
        try:
            # 确定要读取的日志文件
            log_file = self.log_file
            if category:
                if isinstance(category, str) and category.upper() == "ERROR":
                    log_file = self.error_log_file
                elif isinstance(category, str) and category.upper() == "PERFORMANCE":
                    log_file = self.perf_log_file
                else:
                    log_file = self.get_category_log_file(category)
            
            if not os.path.exists(log_file):
                return f"日志文件不存在: {log_file}"
                
            # 使用 tail 方式读取最后N行
            with open(log_file, 'r', encoding='utf-8') as f:
                # 读取所有行并保留最后 lines 行
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"读取日志失败: {str(e)}"
    
    def clean_logs(self, older_than_days=None, category=None, confirm=True):
        """手动清理日志文件
        Args:
            older_than_days: 清理指定天数之前的日志，None表示清理所有
            category: 要清理的日志类别，None表示清理所有类别
            confirm: 是否需要确认，默认True
        Returns:
            dict: 清理结果统计
            
        使用示例:
            # 清理所有日志（会弹出确认对话框）
            clean_logs()
            
            # 清理30天前的所有日志
            clean_logs(older_than_days=30)
            
            # 清理特定类别的所有日志
            clean_logs(category=LogCategory.DATABASE)
            
            # 清理7天前的错误日志
            clean_logs(older_than_days=7, category=LogCategory.ERROR)
            
            # 不显示确认对话框，直接清理
            clean_logs(confirm=False)
        """
        if confirm:
            if older_than_days:
                confirm_msg = f"将清理{older_than_days}天前的"
                if category:
                    category_name = category.value if isinstance(category, LogCategory) else category
                    confirm_msg += f"{category_name}类别的"
                confirm_msg += "日志文件，确认继续？"
            else:
                confirm_msg = "将清理所有日志文件，此操作不可恢复，确认继续？"
                
            try:
                # 在日志中记录清理操作
                with logger.contextualize(category="系统", context=""):
                    logger.warning(f"尝试清理日志: older_than_days={older_than_days}, category={category}")
                    
                # 显示确认对话框
                try:
                    # 尝试使用GUI对话框确认
                    from PyQt5.QtWidgets import QMessageBox, QApplication
                    app = QApplication.instance()
                    if app is None:
                        # 如果没有QApplication实例，跳过GUI确认
                        pass
                    else:
                        result = QMessageBox.question(
                            None, 
                            "确认清理日志", 
                            confirm_msg,
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if result != QMessageBox.Yes:
                            logger.info("用户取消了日志清理操作")
                            return {
                                "total_files": 0,
                                "deleted_files": 0,
                                "failed_files": 0,
                                "skipped_files": 0,
                                "cancelled": True,
                                "details": ["用户取消了操作"]
                            }
                except ImportError:
                    # 如果PyQt5不可用，跳过GUI确认
                    pass
                except Exception as e:
                    # 其他错误，跳过GUI确认
                    logger.warning(f"显示确认对话框失败: {str(e)}")
            except:
                pass
        
        # 获取要清理的文件列表
        files_to_clean = []
        
        # 计算截止日期
        cutoff_date = None
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # 主日志文件
        if not category or category in (LogCategory.SYSTEM, "系统"):
            if os.path.exists(self.log_file):
                files_to_clean.append(self.log_file)
        
        # 错误日志
        if not category or category in (LogCategory.ERROR, "ERROR", "错误"):
            if os.path.exists(self.error_log_file):
                files_to_clean.append(self.error_log_file)
        
        # 性能日志
        if not category or category in (LogCategory.PERFORMANCE, "PERFORMANCE", "性能"):
            if os.path.exists(self.perf_log_file):
                files_to_clean.append(self.perf_log_file)
        
        # 类别日志
        if not category:
            # 清理所有类别
            for cat in LogCategory:
                cat_file = self.get_category_log_file(cat)
                if os.path.exists(cat_file):
                    files_to_clean.append(cat_file)
        elif category:
            # 清理特定类别
            if isinstance(category, LogCategory) or isinstance(category, str):
                cat_file = self.get_category_log_file(category)
                if os.path.exists(cat_file):
                    files_to_clean.append(cat_file)
        
        # 压缩日志文件
        import glob
        if not category:
            # 所有压缩文件
            zip_pattern = os.path.join(self.log_dir, "*.zip")
            zip_files = glob.glob(zip_pattern)
            if cutoff_date:
                # 按日期筛选
                for zip_file in zip_files:
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(zip_file))
                        if file_time < cutoff_date:
                            files_to_clean.append(zip_file)
                    except:
                        pass
            else:
                # 全部清理
                files_to_clean.extend(zip_files)
            
            # 类别子目录中的压缩文件
            cat_zip_pattern = os.path.join(self.category_log_dir, "*.zip")
            cat_zip_files = glob.glob(cat_zip_pattern)
            if cutoff_date:
                for zip_file in cat_zip_files:
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(zip_file))
                        if file_time < cutoff_date:
                            files_to_clean.append(zip_file)
                    except:
                        pass
            else:
                files_to_clean.extend(cat_zip_files)
        
        # 统计
        result = {
            "total_files": len(files_to_clean),
            "deleted_files": 0,
            "failed_files": 0,
            "skipped_files": 0,
            "details": []
        }
        
        # 执行清理
        for file_path in files_to_clean:
            try:
                if cutoff_date:
                    # 按日期清理
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        result["deleted_files"] += 1
                        result["details"].append(f"已删除: {file_path}")
                    else:
                        result["skipped_files"] += 1
                else:
                    # 清理后重新创建空文件（对于非压缩文件）
                    if file_path.endswith(".zip"):
                        os.remove(file_path)
                    else:
                        # 对于常规日志文件，清空内容但保留文件
                        open(file_path, 'w').close()
                    result["deleted_files"] += 1
                    result["details"].append(f"已清理: {file_path}")
            except Exception as e:
                result["failed_files"] += 1
                result["details"].append(f"清理失败 {file_path}: {str(e)}")
        
        # 记录清理结果
        try:
            with logger.contextualize(category="系统", context=""):
                logger.info(f"日志清理完成: 共{result['total_files']}个文件, "
                         f"已删除/清空{result['deleted_files']}个, "
                         f"跳过{result['skipped_files']}个, "
                         f"失败{result['failed_files']}个")
        except:
            pass
            
        return result
    
    def set_context(self, **kwargs):
        """设置当前线程的日志上下文
        Args:
            **kwargs: 上下文键值对
        """
        for key, value in kwargs.items():
            LogContext.set_context(key, value)
    
    def clear_context(self):
        """清除当前线程的日志上下文"""
        LogContext.clear_context()
    
    def with_context(self, **kwargs):
        """创建一个带有指定上下文的上下文管理器
        Args:
            **kwargs: 上下文键值对
        Returns:
            LogContext: 上下文管理器
        """
        return LogContext(**kwargs)

# 创建全局日志记录器实例
log = Logger()

# 方便导入的别名
debug = log.debug
info = log.info
success = log.success
warning = log.warning
error = log.error
critical = log.critical
exception = log.exception
trace = log.trace
with_context = log.with_context
set_context = log.set_context
clear_context = log.clear_context
perf_timer = log.perf_timer

# 导出相关函数
get_log_file_path = log.get_log_file_path
get_log_dir = log.get_log_dir
get_log_directory = log.get_log_dir  # 添加别名，兼容get_log_directory调用
export_log = log.export_log
get_all_log_files = log.get_all_log_files
get_recent_logs = log.get_recent_logs
clean_logs = log.clean_logs

# 设置全局异常处理器
def setup_exception_logging():
    """设置全局异常处理器，捕获未处理的异常并记录到日志"""
    # 使用Loguru的异常捕获装饰器
    @logger.catch
    def _global_exception_handler(exc_type, exc_value, exc_traceback):
        # 保留标准错误处理
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # 设置全局异常处理器
    sys.excepthook = _global_exception_handler
    
def show_error_message(parent, title, message, e=None):
    """显示错误消息对话框并记录到日志
    
    Args:
        parent: 父窗口
        title: 错误标题
        message: 错误消息
        e: 异常对象（可选）
    """
    from PyQt5.QtWidgets import QMessageBox
    
    # 构建完整错误消息
    full_message = message
    if e:
        full_message = f"{message}: {str(e)}"
    
    # 记录到日志
    error(f"UI错误 - {title}: {full_message}", LogCategory.UI, dialog=title)
    
    # 显示对话框
    QMessageBox.critical(parent, title, full_message)
    
    return full_message

def get_category_size(category):
    """获取指定分类的日志大小
    Args:
        category: 日志类别名称或LogCategory枚举
    Returns:
        int: 日志大小（字节）
    """
    if isinstance(category, LogCategory):
        category = category.value
    
    try:
        # 获取类别日志文件路径
        log_file = log.get_category_log_file(category)
        
        # 如果文件存在，返回文件大小
        if os.path.exists(log_file):
            return os.path.getsize(log_file)
        return 0
    except Exception as e:
        logger.error(f"获取分类 {category} 大小时出错: {str(e)}")
        return 0 