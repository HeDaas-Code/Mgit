# CONTEXT.md — Mgit 项目领域术语

> 维护项目级"领域语言"——agent 在写代码、issue、ADR 前**必读**。
> 写规则：每条断言挂 `file:LINE` 锚点，找不到出处的不写。

## 项目是什么 / 不是什么

- **是**：Python + PyQt5 桌面 Markdown 笔记 app，集成 Git 版本控制 + AI Copilot
- **不是**：云优先 SaaS / 纯 CLI / 移动端 / 网页版

## 领域语言

### 自创词

| 术语 | 定义 | 出处 |
|---|---|---|
| **MGit** | 项目名（Markdown + Git 组合） | [[raw-docs/root/README]] |
| **Copilot** | AI 写作助手（5 种模式） | [[raw-docs/root/README]] |
| **Mode Selector** | Copilot 5 种模式的 UI 选择器 | [[raw-docs/root/CHANGELOG]] |
| **Activity Bar** | VSCode 风格的左侧导航栏 | [[raw-docs/root/README]] |
| **Side Bar** | VSCode 风格的功能面板 | [[raw-docs/root/README]] |
| **PluginBase 插件** | 用 `pluginbase` 库实现的插件架构 | [[raw-docs/docs/plugin_development]] |

### Copilot 5 种模式

| 模式 | 用途 | 出处 |
|---|---|---|
| 行内补全 | 上下文续写 | [[raw-docs/root/README]] |
| 编辑模式 | 按指令优化文本 | [[raw-docs/root/README]] |
| 创作模式 | 提示词 → 完整文档 | [[raw-docs/root/README]] |
| 对话模式 | 与 AI 自然对话 | [[raw-docs/root/README]] |
| 代理模式 | 自动执行文档任务 + 审计工作流 | [[raw-docs/root/README]] |

## 命名空间

| 类型 | 命名约定 | 出处 |
|---|---|---|
| 包名 | `src.components`, `src.copilot`, `src.plugins`, `src.theme`, `src.utils`, `src.views` | `ls src/` |
| Python 类 | PascalCase | 业界惯例 |
| 函数/变量 | snake_case | 业界惯例 |
| Git 分支 | `feature/<desc>`, `fix/<desc>`, `chore/<desc>` | [[AGENTS]] |

## 关键不变量

- Python 版本 ≥ 3.10（启动脚本自动检测）
- PyQt5 + PyQt-Fluent-Widgets + GitPython + PyQtWebEngine + PluginBase（核心依赖）
- **资源管理**：自动清理 Web 资源（避免长时间运行内存泄漏）—— [[raw-docs/root/README]]
- **OAuth**：GitHub + Gitee 双平台支持 —— [[raw-docs/docs/oauth_authentication]]

## 状态机

### Copilot 模式切换

```
[无模式] → [行内补全] → [编辑] → [创作] → [对话] → [代理]
                                  ↓
                              [模式切换 UI]
```

具体状态机定义：见 `src/copilot/` 包源码（待详读）。

## 进程模型

- **单进程 PyQt5 桌面应用**——`start.py` 启动 → 主窗口
- **`start.py` 职责**：
  - Python 环境检测
  - 自动创建 `venv-dev`
  - 自动安装依赖
  - Windows 下控制台可见性切换（`DEBUG` flag）
  - 跨平台（Windows / Linux / macOS）

## 错误处理约定

- `log_system_updates.md` 详细记了日志清理/优化历史 —— [[raw-docs/docs/log_system_updates]]
- 日志管理是显式子系统（非 print）

## 测试约定

> ⚠️ **当前状态未知**——仓库内未发现 `tests/` 目录（commit 84 但无测试套件）。
> 见 [[工作Wiki/90-meta/wiki-meta]] "测试缺口" 章节。

## prefer / avoid 表（防漂移）

| prefer | avoid | why |
|---|---|---|
| 中文注释 + 英文标识符 | 全英文注释 | owner 偏好中文沟通 |
| PluginBase 插件架构 | 改用 entry_points | 项目已用 PluginBase |
| PyQt5 + PyQt-Fluent-Widgets | PyQt6 | 项目已锁定 PyQt5 |
| `requirements.txt` | Poetry / uv | 启动脚本期望 pip 风格 |
| `start.py` 单脚本启动 | pyproject.toml script entry | 跨平台环境管理 + Windows 自动安装 |
| 显式日志子系统 | print | 日志分析/清理需要结构化 |

## 待补充

- [ ] Copilot 5 模式的真实代码路径（`src/copilot/` 详读后填）
- [ ] 插件加载时序（plugin_discovery 流程）
- [ ] OAuth 双平台差异点
- [ ] UI 重构前/后对比（`vscode_ui_design.md` 是设计意图，但缺实施 diff）
- [ ] 已知 bug / 技术债（CHANGELOG 拉一份出来）

## 关联笔记

- [[AGENTS]] — Agent 配置
- [[工作Wiki/README]] — 工作 Wiki 入口
- [[工作Wiki/00-index/README]] — 项目速览