# Memory index

- [Claude Desktop 3P setup](claude-desktop-3p-setup.md) — no claude.ai account; desktop runs via micuapi.ai gateway from %LOCALAPPDATA%\Claude-3p; two installs; BOM breaks JSON; desktop injects stale system proxy 127.0.0.1:33210 into CLI (ConnectionRefused when proxy client is off); relay rejects non-Claude-Code clients
- [Skill install workflow](skill-install-workflow.md) — 模糊需求先比较再装,用户拍板;社区技能需 junction 提级;删 junction 用 cmd rmdir
- [Daily report setup](daily-report-setup.md) — agent-daily-report + git-daily-report + 每晚22:00定时任务,日报存 WPS云盘/文档/待办/日报/
- [HA server remote](ha-server-remote.md) — ssh alias HA (192.168.1.42, zhangfengfeng); non-interactive install via ~/install-sub2api-codex-claude.sh env presets; node via partial nvm v24.14.1 (no nvm.sh); key from host-creds-*.json; pitfalls: PowerShell here-string CRLF+BOM over ssh, harness path-sanitizer illusions (verify with od -c)
