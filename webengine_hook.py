# WebEngine初始化钩子
import os
import sys

print("WebEngine钩子脚本开始执行...")

# 设置WebEngine环境变量（这必须在任何PyQt导入前设置）
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --disable-dev-shm-usage"
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = ""
os.environ["QTWEBENGINE_DISK_CACHE_MAX_SIZE"] = "10485760"  # 限制磁盘缓存大小为10MB

# 阻止WebEngine创建太多线程
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
# 禁用持久存储
os.environ["QTWEBENGINE_DISABLE_EMBEDDED_PERSISTENCE"] = "1"

# WebEngine相关的全局变量
if getattr(sys, 'frozen', False):
    # 设置用户数据目录到临时文件夹
    print("运行在PyInstaller环境中，配置临时目录...")
    import tempfile
    cache_dir = os.path.join(tempfile.gettempdir(), "MGit", "webcache")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["QTWEBENGINE_DISK_CACHE_DIR"] = cache_dir

# 确保在QApplication创建前设置属性
try:
    print("导入Qt模块并设置WebEngine属性...")
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication
    
    # 设置WebEngine相关属性（必须在QApplication实例化前设置）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    
    # 强制预先导入WebEngine相关模块
    import PyQt5.QtWebEngineWidgets
    print("WebEngine模块导入成功")
    
    print("WebEngine预初始化成功")
except Exception as e:
    print(f"WebEngine预初始化失败: {e}")
