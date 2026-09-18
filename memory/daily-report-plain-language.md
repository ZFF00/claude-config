---
name: daily-report-plain-language
description: 日报要面向非技术读者，禁用开发术语（主分支、合并、commit、回归测试等）
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab28bebd-345e-483b-b000-8de947130a4c
  modified: 2026-09-17T09:46:11.456Z
---

用户要求日报不要过于专业，点名例子是"主分支"这类 git 术语。

**Why:** 日报的读者是经理/同事，不是工程师；git 与底层技术词汇对他们没有意义。

**How to apply:** 生成日报时把开发术语翻译成结果语言：合并回主分支→改动已全部提交生效；在分支待合并→改动已提交、待并入正式版本；回归测试→自动化测试；不出现版本号、分支名、接口名（NVML/procfs 等）。此规则已写入 `~/.claude/skills/claude-daily-report/references/report-requirements.md` 的 Omit Or Translate 列表。
