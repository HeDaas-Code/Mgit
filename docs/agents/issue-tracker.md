# Issue Tracker — GitHub

## 工具

- **`gh` CLI** —— 所有 issue CRUD 用 `gh issue {create,list,view,edit,close,reopen}`
- **认证** —— 已配 `HeDaas-Code` 账户的 token（keyring 存储），含 `repo` scope

## 工作流

1. 新 issue 创建：`gh issue create --title "..." --body-file /tmp/issue-N.md`
2. 列表拉取：`gh issue list --limit 100 --json number,title,labels,state`
3. 单条查看：`gh issue view <N>`
4. 评论：`gh issue comment <N> --body-file <file>`
5. 关 issue：`gh issue close <N>` / `gh issue reopen <N>`

## 模板

`/tmp/issue-N.md` 五段式：
- `## Problem` —— 现象 + 复现步骤 + 期望/实际 + 证据锚点
- `## Task` —— 需做什么
- `## Acceptance` —— checkbox
- `## Dependencies` —— 阻塞 / 关联 issue
- `## Anchors` —— 引用文件 `file:LINE` 或 commit SHA

## 不做的事

- ❌ 替 owner 关 issue 或 merge PR（HITL 边界）
- ❌ 改 PR review 评论（owner 决定）