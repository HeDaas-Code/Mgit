@echo off
echo ========================================
echo MGit - 打包脚本
echo ========================================
echo.

:: 切换到项目根目录
cd ..
echo 当前工作目录: %CD%

:: 检查虚拟环境
if not exist venv\Scripts\python.exe (
    echo 错误: 未找到虚拟环境
    echo 请先创建并激活虚拟环境
    exit /b 1
)

:: 检查图标文件
if not exist app.ico (
    echo 错误: 未找到应用图标 app.ico
    exit /b 1
)

:: 检查spec文件
if not exist MGit.spec (
    echo 错误: 未找到MGit.spec文件
    exit /b 1
)

:: 检查是否已安装PyInstaller
if not exist venv\Scripts\pyinstaller.exe (
    echo 正在安装PyInstaller...
    venv\Scripts\pip.exe install pyinstaller
)

:: 清理旧的构建产物
if exist build (
    echo 正在清理旧的build目录...
    rmdir /s /q build
)
if exist dist (
    echo 正在清理旧的dist目录...
    rmdir /s /q dist
)

:: 执行打包
echo.
echo 正在打包应用...
venv\Scripts\pyinstaller.exe --clean MGit.spec

:: 检查结果
if not exist dist\MGit.exe (
    echo.
    echo 打包失败!
    exit /b 1
)

echo.
echo ========================================
echo 打包成功! 生成文件: dist\MGit.exe
echo ========================================

exit /b 0 