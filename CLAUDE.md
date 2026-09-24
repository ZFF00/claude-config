# 全局环境与工作约定（跨机器同步）

> 本文件由 claude-config 仓库同步到各机器的 `~/.claude/CLAUDE.md`，每次会话自动加载。
> 原始项目级记忆备份在本仓库 `memory/` 下。

## 通用（所有机器适用）

- **一律用中文回复**：正文、进度汇报、总结、提问选项、Explanatory 风格的 ★ Insight 块都用中文；代码、命令、路径、提交信息照原样。**上下文压缩/续接会话后尤其注意**——2026-09-24 HA 上 rdc-target-agent 会话压缩后连续几条回复切成了英文，被用户纠正。
- **无 Claude.ai 账号**：仅用第三方中转 (micuapi.ai) 的 API key，通过 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` 配置。不要建议 claude.ai 登录流程。
- **中转站指纹校验**：micuapi 只放行标准 Claude Code 客户端；裸 curl / 非标客户端会被 400/503 拒绝。
- **写 JSON 必须无 BOM**：用 PowerShell/记事本编辑 `settings.json` 等会加 UTF-8 BOM，导致解析失败（"Unexpected token"）。写法：`[IO.File]::WriteAllText(path, text, (New-Object System.Text.UTF8Encoding($false)))`。
- **路径消毒幻觉**（重要）：本 harness 会把家目录路径改写成占位符显示（本地 `C:/Users/PC-0312*`、远程 `/home/...` 都可能显示成同一形态），有时还会反向翻译命令里的路径。**症状**：`Test-Path "$env:X\y"`(字符串拼接) 与 `-LiteralPath` 结果不一致、递归遍历卡在云盘占位文件。**对策**：文件操作用 `-LiteralPath` + 变量；判断真实路径存疑时用 `od -c` / `fsutil reparsepoint query` 看原始字节；git 操作用 `git -C <dir>` 而非 `Set-Location`。

## Claude Desktop 侧边栏会话自归类

- **分组命名规则**：本机目录 → `💻 <项目目录名>（Local）`；服务器目录 → `🌐 <项目目录名>（<host>）`（host 用服务器简称，如 `HA`；括号为全角）。目录名取**当前工作目录的 basename**（worktree 会话用主仓库目录名）——侧边栏的自动分组显示名在会话内不可见，不要引用。例：`💻 待办（Local）`、`🌐 RDC_evaluation（HA）`。组名是纯文本不支持颜色，用 emoji 做视觉标记。
- 会话开始后的第一次回复中，若本会话运行在 Claude Desktop（存在 `ccd_sidebar` 系列 MCP 工具），用 `move_sessions(["self"], <group_id>)` 把本会话归入符合上述命名的分组：先 `list_groups` 找同名组，没有才 `create_group`。**静默执行**：不在回复正文里叙述或汇报归类过程与结果（不写"确认主机身份""已归入 XX 组"之类），hostname 探测和归组调用直接做即可；可交给子 agent 后台完成以免干扰正题。
- **判断 host 用运行时身份，不用路径特征**（路径消毒会把远程/本地路径互相伪装，文件存在性探测也不可靠——2026-09-21 曾因"并行会话迁移仓库删旧址 + 路径消毒"叠加，一度误判为 shell 中途换机器，靠 hostname/IP + fsutil hardlink 才厘清）。**未实测 hostname/IP 前禁止建组贴标签**（2026-09-21 有 HA 会话凭猜测自标 Local，靠人发现才纠正；另注意本机也有 MSYS bash，"bash=远程"不成立）。标准动作：执行 `hostname` + `hostname -I`（Windows 用 `ipconfig`），按清单映射标签：`192.168.1.42`→`HA`、`192.168.1.41`→`HA_old`；PowerShell + Windows 盘符环境 → `Local`（用户有两台本地 Windows 机，均标 `Local`：办公 PC hostname `DESKTOP-JBCGL8E`；便携机 hostname `NB-0514`／IP `192.168.8.211`）。清单外的机器直接用真实 hostname 当标签，不要猜。（HA 实测 hostname `test-RWS7250-I41-HS621GE-EGS-MGX4`。）
- 移动 "self" 不需要用户确认；不要顺手移动其他会话（会弹确认打扰用户）。

## claude-config 仓库同步约定

- **自动同步由 hooks 承担**（settings.json 内，随仓库分发到所有机器）：SessionStart 后台 `git pull --ff-only`（静默失败不阻塞）；SessionEnd 检测脏改动则 `add + commit + push`（push 被拒时先 `pull --rebase` 重试）。原 Windows 每小时计划任务 `claude-config-sync` 已停用。
- **hook 命令必须 bash 与 PowerShell 5.1 双方都能解析**——Windows 上 Claude Code 用 PowerShell 执行 hook 命令，纯 bash 写法（`$(...)`、`&&`、`[ -n ]`、`if...fi`）每次都 ParserError，2026-09-23 前 Windows 侧同步从未生效。现行机制（2026-09-23，commit 40cb3c8）：hook 只写一行"多态"命令（仅用裸 token / `"$HOME/..."` / 单引号字面量三种两边语义一致的元素），`git -C "$HOME/.claude/skills"` 穿过 junction/symlink 自动发现仓库顶层，内联 `!alias` 由 **Git 自带的 sh** 执行 `tools/config-sync.sh`（POSIX sh、行尾必须 LF）。改同步逻辑只改该脚本；别把任何 shell 语法写回 settings.json 的 command 字符串。仓库/脚本缺失时静默退出（HA 等未部署机器无噪音）。
- **Claude 主动修改配置仓库文件（CLAUDE.md / settings.json / skills / memory 等）后，应立即用有意义的 message commit + push**，不要依赖 SessionEnd 兜底的 `chore(auto-sync)` 提交。
- 编辑工具（临时文件+重命名写入）和 `git pull` 都会**打断 settings.json / CLAUDE.md 的硬链接**：改完/拉完后核对 `~/.claude/` 与仓库两侧是否一致，不一致就重建硬链接或重跑 deploy 脚本。
- **git 提交不加任何 AI 归属尾注**：不写 `Co-Authored-By: Claude ...`、"Generated with Claude Code" 等（GitHub 会把 Co-Authored-By 渲染成仓库贡献者）。提交作者统一用 ZFF00 <1138903623@qq.com>（settings.json 已设 `attribution` 为空作机制兜底）。

## 技能管理（skill）

- 技能库由 **claude-config 仓库** 统一管理：仓库 `skills/` ← junction/symlink → `~/.claude/skills`。
- **社区技能一律实体化到 `skills/` 顶层**（下载后把技能目录移到顶层，不保留 `@user_xxx`/`@clawhub_xxx` 二级目录，来源写在提交信息里）。**仓库内禁止提交 symlink/junction**——Linux 建的 symlink 到 Windows 会退化成文本文件（2026-09 git-daily-report 踩坑）；链接属于机器，不属于仓库。
- 删 junction（如本机遗留）：Windows 用 `[System.IO.Directory]::Delete($link,$false)` 或 `cmd /c rmdir`（**不要**用 `Remove-Item -Recurse`，会穿透删目标文件）。
- **安装技能的流程偏好**：模糊需求（"想要 XX 技能"）→ 先调研/下载到临时目录审阅 → 给比较和推荐 → **等用户拍板再正式装**；不要直接装推荐项。明确点名单个技能可直接装，但先检查内容（注入/恶意命令/数据外流）。

## 日报

- 每日工作日报走技能 `agent-daily-report` + `git-daily-report`；**默认手动触发**（用户明确要求不开自动定时任务，尽管技能 SKILL.md 里写"每晚22:00"——那只是模板话术，本身无调度能力）。
- 日报输出到 `WPS云盘/文档/待办/日报/日报-YYYY-MM-DD.md`。

## Windows PC 专属

- Claude Desktop 走 3P gateway 模式，配置在 `%LOCALAPPDATA%\Claude-3p\`（`deploymentMode: 3p`），与 `%APPDATA%\Claude\` 无关。桌面问题先看 `Claude-3p\logs\main.log`。
- **代理坑**：桌面 app 会把系统代理 `127.0.0.1:33210` 注入 CLI 的 HTTP(S)_PROXY（即使 `ProxyEnable=0`）。本地代理客户端关闭时，桌面对话报 `ConnectionRefused`；独立 `claude` CLI 不受影响。已设 WinINET `ProxyOverride=www.micuapi.ai;*.micuapi.ai` 让网关直连。Clash 类客户端可能覆盖此项，横幅复发就在代理客户端里重加 bypass。
- **侧边栏分组自动排序**：登录时经 HKCU Run 键 `claude-sidebar-sort` 跑 `tools/sort-sidebar-groups.ps1`（🌐 服务器组在前、💻 Local 组在后，块内保序）。原理与限制：分组顺序存在 `Claude-3p\claude_desktop_config.json` 的 `epitaxyPrefs["dframe-group-scopes"]`，App **仅启动时读取**，运行中外部改写无效且会被内存态覆盖——所以只能登录时（App 启动前）排；当天新增的组先追加末尾，下次启动归位。
- 配置仓库物理位置：`%USERPROFILE%\.claude-config`（本仓库 clone，2026-09-21 自 `%LOCALAPPDATA%\claude-skills` 迁入）。**不要放 `%LOCALAPPDATA%`**——Claude Desktop 是 MSIX 应用，其进程写 `AppData\Local` 会被透明重定向进包容器 `Packages\Claude_xxxx\LocalCache`，卸载/重置会连仓库一起清空；也不要放 WPS 云盘（无合并机制、占位文件复制不全）。完整部署与迁移步骤见仓库 `docs/windows-setup.md`。

## HA 服务器专属

- ssh 别名 `HA` → 192.168.1.42（用户 zhangfengfeng）；另有 `HA_old`(.41)、`HA_claw`。Ubuntu 24.04，sudo 需密码。
- 部署脚本 `~/install-sub2api-codex-claude.sh`，可预设 env 全非交互安装 Codex+Claude Code。
- node 无系统安装，nvm 是部分安装（有 `~/.nvm/versions/node/v24.14.1` 但无 nvm.sh）→ 把该 bin 目录加进 PATH。
- **SSH from Windows 坑**：PowerShell here-string 通过 `ssh HA "bash -s"` 会带 CRLF + BOM，尾部 `\r` 会粘到每行最后一个 token（假错误如 `/dev/null: Permission denied`）。优先用单行 `ssh HA '...'`，或 scp 一个无 BOM 文件过去执行。
- 数据盘 `/opt/disk` 49T；组学库 `~/disk/Data`（git 仓库，只跟踪代码/清单）。
