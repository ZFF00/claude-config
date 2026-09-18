# Memory index

- [Claude Desktop 3P setup](claude-desktop-3p-setup.md) — no claude.ai account; desktop runs via micuapi.ai gateway from %LOCALAPPDATA%\Claude-3p; two installs; BOM breaks JSON; desktop injects stale system proxy 127.0.0.1:33210 into CLI (ConnectionRefused when proxy client is off); relay rejects non-Claude-Code clients
- [Skill install workflow](skill-install-workflow.md) — 模糊需求先比较再装,用户拍板;社区技能需 junction 提级;删 junction 用 cmd rmdir
- [Daily report setup](daily-report-setup.md) — agent-daily-report + git-daily-report + 每晚22:00定时任务,日报存 WPS云盘/文档/待办/日报/
- [HA server remote](ha-server-remote.md) — ssh alias HA (192.168.1.42, zhangfengfeng); non-interactive install via ~/install-sub2api-codex-claude.sh env presets; node via partial nvm v24.14.1 (no nvm.sh); key from host-creds-*.json; pitfalls: PowerShell here-string CRLF+BOM over ssh, harness path-sanitizer illusions (verify with od -c)
- [Context management strategy](context-management-strategy.md) — 长会话在任务边界用 /fresh(handoff+clear) 交接清空；规则/偏好随时落盘到记忆/CLAUDE.md/技能，别只留对话；关键状态维护在仓库文档里
- [Daily report plain language](daily-report-plain-language.md) — 日报面向经理/非技术读者，禁 git/技术术语(主分支/合并/commit/回归测试/版本号/接口名)，翻译成结果语言
- [Claude dir display rewrite](claude-dir-display-rewrite.md) — harness 把 ~/.claude/ 显示成 ~/.claude-N/(N递增，磁盘无损，疑与 claude-mem 钩子有关)；看到带数字后缀路径一律按 ~/.claude/ 用，用 od -c 核字节
