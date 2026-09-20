---
name: fresh
description: 一条指令完成 handoff + clear：调用 handoff 技能把当前会话写成交接文档（项目内 .claude/HANDOFF.md），然后自动清空本会话上下文。清空后用户只需发送"继续"即可无缝接续任务。
argument-hint: "（可选）下个会话的工作重点"
disable-model-invocation: true
---

将当前会话交接并清空，分两步在同一轮内完成：

## 第 1 步：写交接文档

用 Skill 工具调用 `handoff` 技能，把用户参数原样传给它，按其规范写交接文档（默认路径 `<项目根>/.claude/HANDOFF.md`）。交接文档的格式与条目以 handoff 技能为唯一规范来源，不要在本技能内另立标准。

**兜底**：若 handoff 技能不存在或加载失败，按以下简版规范内联执行——写 `<项目根>/.claude/HANDOFF.md`，包含：任务目标与当前状态、按优先级的待办清单、关键文件及状态、踩过的坑、用户中途给出的偏好与纠正、建议技能；引用而非复制其他文档；脱敏。

## 第 2 步：清空会话

1. 先用 ToolSearch 加载 `mcp__ccd_session_mgmt__clear_session`（它是延迟加载工具）。
2. 给用户发最后一条简短消息：交接文档路径 + 提示"清空后直接发送：继续"。
3. 调用 `clear_session`，参数 `session_id: "self"`。清空在本轮结束后生效。

**回退**：若 `clear_session` 工具不存在（终端 CLI 环境）或调用被拒绝，则只完成第 1 步，并告诉用户手动执行 `/clear`，之后发送"继续"。

## 注意

- 第 2 步的最后一条消息务必在调用 clear_session 的同一轮发出，清空后旧消息不再显示。
- 不要跳过交接文档直接清空。
