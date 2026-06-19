# Domain Docs — Single-Context Layout

## 布局

```
Mgit/
├── CONTEXT.md           ← 项目级领域术语表
└── docs/
    ├── adr/             ← 架构决策记录
    └── agents/          ← Agent skills 配置
```

## 消费者规则

| Skill | 读什么 |
|---|---|
| `improve-codebase-architecture` | `CONTEXT.md`（领域语言）+ `docs/adr/*`（历史决策） |
| `diagnose` | `CONTEXT.md` + `docs/adr/*` + 代码路径 |
| `tdd` | `CONTEXT.md`（测试术语）+ `docs/adr/*`（架构约束） |
| `grill-with-docs` | `CONTEXT.md`（懒创建内容，沉淀领域知识） |
| `to-issues` / `to-prd` | `docs/agents/issue-tracker.md` |
| `triage` | `docs/agents/triage-labels.md` |

## 写 CONTEXT.md 的原则

1. **优先填自创词**（项目内"非业界通用"术语）
2. **每条断言挂 `file:LINE` 锚点**——不可溯源就不写
3. **9 章结构**（来自 `setup-matt-pocock` post-install-completion 模板）：
   - 项目是什么 / 不是什么
   - 领域语言
   - 命名空间（变量 / 类 / 模块）
   - 关键不变量
   - 状态机
   - 进程模型
   - 错误处理约定
   - 测试约定
   - `prefer/avoid` 表（防漂移）

## 写 ADR 的原则

1. **文件名**：`NNNN-<短横线连接的标题>.md`（`0001-xxx.md`）
2. **每个 ADR 含**：状态 / 上下文 / 决策 / 后果 / 备选
3. **不可回改**——如需改，写新 ADR 引用旧 ADR