---
name: daily-work-report
description: 每晚22:00复盘当天Claude Code会话与git提交,按agent-daily-report模板自动生成工作日报
---

生成今天的工作日报,数据来自两个来源,均为真实记录:

【来源1:Claude Code 会话记录】
用 mcp__ccd_session_mgmt__list_sessions 和 mcp__ccd_session_mgmt__search_session_transcripts 检索今天(本地日期)所有会话,提取:完成的任务、修改/产出的文件(带路径)、安装配置的工具、遇到的问题与解决方式。

【来源2:git 提交记录】
运行 git-daily-report 技能的收集脚本:
python "C:\Users\PC-0312\.claude\skills\git-daily-report\scripts\collect_git.py" --repo "C:/Users/PC-0312/WPSDrive/411903953/WPS云盘/文档/待办" --since "1 day ago"
读取返回 JSON。若该目录不是 git 仓库、脚本报错或 count 为 0,此节写"今日无代码提交",不视为错误。按 git-daily-report 技能的要求:按模块归纳提交而非逐条罗列 hash,注意脱敏。

【生成日报】
按 agent-daily-report 技能(~/.claude/skills/agent-daily-report/SKILL.md)的模板输出四部分:✅ 任务达成、📊 效能统计、⚠️ 异常与局限、📅 明日焦点。要求:
- 只汇报真实发生的操作,严禁编造;当日无有效记录则明确写"无关键产出"
- 任务达成中列出具体产出物的文件路径
- 把琐碎原子操作提炼为业务成果
- 中文撰写,语气专业克制

【保存】
将日报存为 "C:/Users/PC-0312/WPSDrive/411903953/WPS云盘/文档/待办/日报/日报-YYYY-MM-DD.md"(目录不存在则创建),并在回复中输出日报全文。