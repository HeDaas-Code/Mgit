# 在查找模块路径前执行的钩子
import os
import sys

if getattr(sys, 'frozen', False):
    # 确保QtWebEngine资源在正确的位置
    import PyQt5
    pyqt_path = os.path.dirname(PyQt5.__file__)
    
    # 检查并确保QtWebEngineProcess可执行文件
    webengine_bin = os.path.join(pyqt_path, 'Qt', 'bin', 'QtWebEngineProcess')
    webengine_bin_exe = webengine_bin + '.exe'
    
    if os.path.exists(webengine_bin) or os.path.exists(webengine_bin_exe):
        print(f"找到WebEngine进程: {webengine_bin}")
        # 确保WebEngine二进制文件路径在PATH中
        os.environ['PATH'] = os.path.join(pyqt_path, 'Qt', 'bin') + os.pathsep + os.environ.get('PATH', '')
