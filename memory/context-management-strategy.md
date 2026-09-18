---
name: context-management-strategy
description: 用户的长会话上下文管理策略：任务边界处用 /fresh（handoff+clear 聚合指令），规则落盘不依赖对话记忆
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab28bebd-345e-483b-b000-8de947130a4c
  modified: 2026-09-18T03:09:46.718Z
---

用户担心长会话导致模型钝化，讨论后采纳的策略：在自然任务边界或上下文用到七八成时做交接+清空，平时不动；不要高频清理（重建成本会超过钝化损失）。

**Why:** compact/handoff 都是有损的；钝化问题靠短上下文根治，但交接文档可能漏掉隐性上下文（踩过的坑、中途的纠正）。

**How to apply:**
- 已做成聚合指令 `/fresh`（`~/.claude/skills/fresh/`）：写交接文档到项目 `.claude/HANDOFF.md`，然后自动调用 clear_session 清空本会话；清空后用户发"继续"即可接续（全局 `~/.claude/CLAUDE.md` 里有对应的接续规则）。
- 会话接近任务边界或上下文占用高时，主动提醒用户可以 `/fresh`，并生成交接文档供用户过目补充。
- 用户中途给出的偏好、规则、纠正，不要只留在对话里——随时写进长期记忆、CLAUDE.md 或对应技能规则文件（如 [[daily-report-plain-language]] 的做法），确保 clear 后不丢。
- 关键任务状态（计划、待办、已决定事项）维护在仓库文档里（如 rdc-target-agent 的 `.agent-handoff/`），把上下文当缓存而非唯一记录。
