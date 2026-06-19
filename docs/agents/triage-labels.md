# Triage Labels

## 五类状态机

| Label | 中文 | 含义 | 进入条件 | 离开 |
|---|---|---|---|---|
| `needs-triage` | 待评估 | maintainer 需评估 | 新 issue 默认 | owner 评估后移走 |
| `needs-info` | 等待补充信息 | 等 reporter 补充 | 评估时发现信息不全 | reporter 回复后移走 |
| `ready-for-agent` | AFK agent 可接 | 完全规格化，无人工介入 | 评估后完全明确 | agent 完成 |
| `ready-for-human` | 需人工实现 | 需要 owner 拍板/操作 | 评估发现需判断 | owner 处理 |
| `wontfix` | 不修复 | 拒绝 | owner 决定 | — |

## 默认值

不重映射——直接用 5 个英文 label 名。如果 owner 在 GitHub 改了 label 名（例如改成中文），**这个文件必须同步更新**，否则 `triage` skill 会创重复 label。

## 验证

```bash
gh label list --limit 50
```