# Daily Report Schema

Use this section order. Follow the user's language and keep bullets concise.

```markdown
# Claude 日报 - YYYY-MM-DD

> 时区：Asia/Shanghai
> 生成时间：YYYY-MM-DD HH:mm
> 覆盖范围：索引 N 个会话，读取 M 个候选会话；必要时注明范围限制。

## 今日概览

用 2-4 句话概括当天最重要的成果、进展和风险。

## 已完成

- 具体成果；必要时注明来源会话。

## 进行中

- 当前状态和剩余工作。

## 阻塞与失败

- 阻塞原因、已尝试措施和当前影响。

## 关键决策

- 决策内容及简短依据；没有明确证据时不要补写。

## 产物与文件

- `绝对或会话中明确记录的路径`：用途或状态。

## 验证结果

- 检查或测试：通过、失败或未运行，并附必要的简短证据。

## 下一步建议

- 基于未完成事项或阻塞给出可执行建议，并标明这是建议而非已决定事项。
```

## Evidence Rules

- Prefer explicit completion messages, file-change records, saved artifact paths, git commits, and observed verification results.
- Attribute ambiguous items to the source session by title; add a shortened session ID only when titles collide.
- Report failures and unverified work plainly. Never convert "planned", "expected", or "should pass" into completion.
- Use `无已识别项` for a required section with no supported entries. Use `信息不足` when evidence is unavailable.
- Keep quoted text exceptional and brief. Paraphrase by default.
- List only paths explicitly present in readable session evidence or git output. Do not guess locations from titles.
- Suggested next actions may be inferred, but label them as recommendations and keep them separate from decisions.

## Coverage Accounting

Track these counts while working:

- indexed sessions returned by `list_sessions` (plus the current session from context)
- candidate sessions selected for detail reading
- candidate sessions successfully read
- sessions with activity inside the target interval
- unreadable or truncated sessions

If the index reaches the requested `limit`, say that older sessions may not be covered. Archived sessions are excluded unless explicitly included. When message-level timestamps are unavailable, note that in-day attribution for that session is approximate.
