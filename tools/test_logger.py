#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试更新后的高级Loguru日志系统
"""

import time
import random
import threading
from src.utils.logger import (
    debug, info, warning, error, critical, exception, success, trace,
    with_context, set_context, clear_context, perf_timer, 
    LogCategory, get_recent_logs, export_log, clean_logs
)

# 性能计时器测试
@perf_timer
def slow_function():
    """模拟一个耗时的函数"""
    time.sleep(0.2)
    return "完成耗时操作"

# 上下文测试函数
def test_with_context():
    """测试日志上下文功能"""
    # 设置上下文
    set_context(用户="测试用户", 模块="测试模块")
    
    # 使用已设置的上下文记录日志
    info("这条日志带有全局上下文", LogCategory.USER)
    
    # 使用上下文管理器临时添加上下文
    with with_context(操作="测试操作", 参数={"a": 1, "b": 2}):
        info("这条日志带有临时上下文", LogCategory.USER)
        
        # 嵌套上下文
        with with_context(子操作="嵌套操作"):
            info("这条日志带有嵌套上下文", LogCategory.USER)
    
    # 上下文管理器退出后，恢复原有上下文
    info("这条日志只带有全局上下文", LogCategory.USER)
    
    # 清除上下文
    clear_context()
    info("这条日志没有任何上下文", LogCategory.USER)

# 多线程测试函数
def thread_worker(thread_id):
    """线程工作函数"""
    with with_context(线程ID=thread_id):
        info(f"线程 {thread_id} 开始工作", LogCategory.SYSTEM)
        time.sleep(random.uniform(0.1, 0.5))
        info(f"线程 {thread_id} 工作完成", LogCategory.SYSTEM)

def test_multi_threading():
    """测试多线程日志记录"""
    threads = []
    for i in range(5):
        t = threading.Thread(target=thread_worker, args=(i,), name=f"Worker-{i}")
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()

def test_categories():
    """测试各种日志类别"""
    for category in LogCategory:
        info(f"这是一条 {category.value} 类别的日志", category)

def main():
    """测试各种日志功能"""
    info("=== 测试高级Loguru日志系统 ===")
    
    # 测试基本日志级别
    debug("这是一条调试信息")
    info("这是一条普通信息")
    success("这是一条成功信息")
    warning("这是一条警告信息")
    error("这是一条错误信息")
    critical("这是一条严重错误信息")
    
    # 测试异常日志
    try:
        # 故意引发异常
        result = 1 / 0
    except Exception as e:
        exception(f"捕获到异常: {str(e)}")
    
    # 测试分类日志
    info("测试数据库操作", LogCategory.DATABASE)
    info("测试用户界面", LogCategory.UI)
    info("测试Git操作", LogCategory.REPOSITORY)
    info("测试网络请求", LogCategory.NETWORK)
    error("测试安全警告", LogCategory.SECURITY)
    
    # 测试上下文功能
    info("开始测试上下文功能")
    test_with_context()
    
    # 测试性能计时器
    info("开始测试性能计时器")
    result = slow_function()
    info(f"性能计时器测试结果: {result}")
    
    # 测试多线程
    info("开始测试多线程日志")
    test_multi_threading()
    
    # 测试所有类别
    info("开始测试所有日志类别")
    test_categories()
    
    # 测试性能追踪
    trace("这是一条性能跟踪日志", function="main", elapsed_ms=15.3)
    
    # 导出日志
    log_path = export_log(include_categories=True)
    info(f"日志已导出到: {log_path}")
    
    # 测试读取日志
    recent_logs = get_recent_logs(10)
    print(f"\n最近10条日志:\n{recent_logs}")
    
    # 测试日志清理功能（仅演示，不实际清理）
    print("\n===测试日志清理功能===")
    print("注意：实际测试中将跳过确认对话框，不会真正删除文件")
    
    # 模拟清理7天前的日志（仅预览）
    test_clean_result = clean_logs(older_than_days=7, confirm=False)
    print(f"7天前的日志清理结果: 共{test_clean_result['total_files']}个文件")
    print(f"- 已清理: {test_clean_result['deleted_files']}个")
    print(f"- 已跳过: {test_clean_result['skipped_files']}个")
    print(f"- 失败: {test_clean_result['failed_files']}个")
    
    # 模拟清理特定类别（仅预览）
    test_cat_clean = clean_logs(category=LogCategory.DATABASE, confirm=False)
    print(f"\n数据库日志清理结果: 共{test_cat_clean['total_files']}个文件，已清理{test_cat_clean['deleted_files']}个")
    
    info("=== 日志测试完成 ===")
    
if __name__ == "__main__":
    main() 