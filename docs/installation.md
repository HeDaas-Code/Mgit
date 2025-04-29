# 安装指南

## 系统要求

- Python 3.7+（使用py文件运行必选）
- Git (已安装并配置)

---


## 安装步骤


### 从自动配置运行


下载已发布的安装文件

运行！


### 从源码运行

#### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/mgit.git
cd mgit
```

#### 2. 创建虚拟环境 (推荐)

##### Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

##### macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 运行应用

```bash
python run.py
```

## 可能遇到的问题

### PyQt-Fluent-Widgets 安装问题

如果在安装 PyQt-Fluent-Widgets 时遇到问题，请尝试先安装其依赖:

```bash
pip install PyQt5
```

### PyQtWebEngine 安装问题

OAuth授权需要WebEngine支持，如果遇到相关错误，请确保正确安装PyQtWebEngine:

```bash
pip install PyQtWebEngine
```

在某些系统上，可能需要安装额外的系统依赖:

#### Ubuntu/Debian:
```bash
sudo apt-get install python3-pyqt5.qtwebengine
```

#### Fedora:
```bash
sudo dnf install python3-qt5-webengine
```

### OAuth授权失败问题

如果遇到OAuth授权窗口卡死或闪退问题:

1. 尝试使用系统浏览器进行授权（应用内会提供此选项）
2. 确保网络连接稳定
3. 检查防火墙设置，确保应用能访问相关授权服务
4. 在Windows上，某些杀毒软件可能会阻止内置浏览器的正常工作，可以暂时禁用它们

### Git 配置问题

确保您已经在全局范围内配置了 Git 用户名和邮箱:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 更新应用

当有新版本发布时，运行以下命令获取最新版本:

```bash
git pull
pip install -r requirements.txt
``` 

## 自行编译

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/mgit.git
cd mgit
```

### 2. 创建虚拟环境 (推荐)

#### Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装自配置环境依赖

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 4.  编译自配置文件
```bash
pyinstaller --onefile --windowed --splash icon.png(闪屏) --icon=app.ico(图标) start.py
```
