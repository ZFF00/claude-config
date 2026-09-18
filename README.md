# claude-config

跨机器统一的 Claude Code 配置：技能、全局设置、记忆、定时任务、插件登记。

## 仓库结构

```
claude-config/
├── skills/                        # 全部技能（→ ~/.claude/skills）
├── settings.json                  # 全局设置（→ ~/.claude/settings.json）；不含凭据
├── CLAUDE.md                      # 全局指令/记忆（→ ~/.claude/CLAUDE.md）
├── memory/                        # 原始项目级记忆备份（参考用）
├── scheduled-tasks/               # 定时任务定义
├── plugins/known_marketplaces.json# 插件市场登记（本体不同步，各机重拉）
├── deploy.ps1                     # Windows 一键部署
├── deploy.sh                      # Linux/HA 一键部署
└── .gitignore / .gitattributes
```

## 不同步的内容（务必留在本机）

- **凭据**：`~/.claude.json`、`.credentials.json`（含 token/账号，会串号）
- **缓存/会话/历史**：`cache/ sessions/ debug/ telemetry/ history.jsonl`
- **本机覆盖**：`settings.local.json`（每台不同的网关地址/代理等放这里）
- **插件本体**：`plugins/marketplaces/`（缓存，`/plugin marketplace add` 会自动重拉）

## 新机器部署

### Windows

```powershell
git clone git@github.com:ZFF00/claude-config.git "$env:LOCALAPPDATA\claude-skills"
& "$env:LOCALAPPDATA\claude-skills\deploy.ps1"          # 消费端：装自动 pull
# 主编辑机（authority，只手动 pull）改用：
# & "$env:LOCALAPPDATA\claude-skills\deploy.ps1" -NoAutoPull
```

> Windows 无管理员/开发者模式时，文件 symlink 会失败，脚本自动降级为 **hardlink**（无需管理员，`settings.json`/`CLAUDE.md` 与仓库同为一份文件）。目录用 junction，同样无需管理员。

### Linux / HA 服务器

```bash
git clone git@github.com:ZFF00/claude-config.git ~/claude-config && bash ~/claude-config/deploy.sh
```

`deploy` 脚本做的事：把 `skills/`、`settings.json`、`CLAUDE.md`、`scheduled-tasks/` 链接（junction/symlink）到 `~/.claude/` 下对应位置；不覆盖已存在的本机文件（会先备份）。

## 日常同步

- **拉取（自动）**：装一次定时任务，每小时 `git pull --ff-only`。
  - Windows：`schtasks /create /tn "claude-config-sync" /tr "git -C \"%LOCALAPPDATA%\claude-skills\" pull --ff-only" /sc hourly /f`
  - Linux：`(crontab -l; echo "0 * * * * git -C ~/claude-config pull --ff-only -q") | crontab -`
- **推送（手动）**：在改动的机器上 `git -C <repo> add -A && git commit -m "..." && git push`。
  - 只有一台当"权威"来改，其它机器只 pull，可避免合并冲突。

## 注意事项

- 编辑 `settings.json` 务必 **UTF-8 无 BOM**（BOM 会让 Claude 解析失败）。
- 行尾由 `.gitattributes` 统一为 LF（防 Windows↔Linux 乱码）。
- 技能库不要放在网盘同步目录（无合并、占位文件导致复制不全）——用本仓库 + git 管理。
