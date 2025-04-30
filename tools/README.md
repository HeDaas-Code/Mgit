# 开发工具集

此文件夹包含与MGit项目相关的辅助开发和测试工具。这些工具不是应用程序运行所必需的，但在开发、调试和构建过程中提供帮助。

## 文件说明

### 构建相关
- **build.py** - Python打包脚本，用于将应用打包为可执行文件
- **build.bat** - Windows批处理脚本，简化Windows系统上的打包过程
- **pre_find_module_path.py** - PyInstaller钩子，确保QtWebEngine资源在正确位置
- **webengine_hook.py** - WebEngine初始化钩子，在打包时被复制到正确位置

### 调试工具
- **debug_repo_create.py** - 用于调试和排查Git仓库创建路径相关问题
- **test_logger.py** - 测试和演示高级日志系统功能

### UI相关工具
- **list_progressring_api.py** - 列出ProgressRing组件的API接口
- **show_icons.py** - 显示所有可用的FluentIcon图标

## 使用方法

### 运行工具
这些工具通常直接运行：

```
python tools/工具名称.py
```

或在Windows系统上：

```
tools\工具名称.py
```

### 构建应用
现在构建脚本已移动到tools目录，请按照以下方式运行构建脚本：

#### 使用Python打包（推荐）:
```
python tools/build.py
```

#### 使用批处理文件打包（仅Windows）:
```
tools\build.bat
```

构建脚本已经更新，能够自动处理文件路径，确保从项目根目录正确引用所有需要的资源和文件。

## 构建过程说明

1. 构建脚本会自动检测脚本所在目录并导航到项目根目录
2. 检查虚拟环境、图标文件和spec文件是否存在
3. 清理旧的构建产物
4. 执行PyInstaller打包过程
5. 验证构建成功并输出结果路径

## 注意事项

- 这些工具主要用于开发过程，不应包含在最终的发布版本中
- 部分工具可能依赖特定的环境设置或额外的依赖项
- 使用构建工具前，请确保已正确设置虚拟环境
- 构建过程中的钩子文件会被自动复制到正确位置，无需手动操作 