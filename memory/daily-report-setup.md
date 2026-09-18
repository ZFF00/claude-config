---
name: daily-report-setup
description: 用户的自动工作日报方案:agent-daily-report + git-daily-report 技能 + 每晚22:00定时任务
metadata: 
  node_type: memory
  type: project
  originSessionId: e8538fc5-e93f-45c0-939c-5db667db8a89
  modified: 2026-09-17T03:56:27.069Z
---

用户想要 Codex daily report 式的自动日报(不口述、Agent 自动复盘)。2026-09-17 定稿方案:

- 技能 `agent-daily-report`(@clawhub_freeslym,纯提示词模板,四段式:任务达成/效能统计/异常与局限/明日焦点)+ `git-daily-report`(@clawhub_kidok,collect_git.py 只读收集 git log)。
- 定时任务 `daily-work-report` 每晚 22:00(cron `0 22 * * *`):汇总当天 Claude Code 会话记录 + git 提交,生成日报存到 `WPS云盘/文档/待办/日报/日报-YYYY-MM-DD.md`。
- 候选比较结论:databian(绑死 OpenClaw/飞书)、team-efficiency(作者私有看板)不适配;口述型(daily-report-zh、work-report-pro、daily-report-recorder 等)不符合"自动"前提。
- 注意:技能 SKILL.md 里宣称的"每晚 22:00 自动"本身无调度能力;用户明确要求**不开定时任务**,日报手动触发。安装流程偏好见 [[skill-install-workflow]]。
- 自研技能 `claude-daily-report`(移植自 ~/.codex/skills/codex-daily-report,八段式 schema+证据规则)有两个版本:本机 Windows 版用 ccd_session_mgmt MCP 工具;HA 服务器版(2026-09-17 部署)用自研 `scripts/collect_sessions.py` 解析 ~/.claude/projects/*/​*.jsonl 转录(逐事件时间戳,比桌面 MCP 更精确),输出到 ~/reports/daily/。本地全部 63 个技能已 tar+scp 全量同步到 HA(junction→symlink 重建);HA 上已删 wps-cloud-localizer(纯 Windows 技能)。
