# Claude Code / Desktop 统一配置说明（Windows）

> 目的：让本机的 skills、settings.json、CLAUDE.md、scheduled-tasks 全部由 GitHub 仓库
> `git@github.com:ZFF00/claude-config.git` 统一管理，多台机器 + HA 服务器共享一套配置，
> 改一处全网同步。

---

## 一、前提

- 已装 **Git for Windows**（含 Git Bash，hooks 依赖它）。
- 已配好能访问仓库的 **SSH 密钥**（走 SSH，不用 PAT）。测试：`ssh -T git@github.com` 能认出你。
- 装了 Claude Desktop（它是 **MSIX 打包应用**，这是下面所有坑的根源）。

## 二、核心原理（务必先懂）

配置仓库 clone 到本地某目录，再由 `deploy.ps1` 把仓库里的对应项**链接**进 `~/.claude/`（不是拷贝）：

| `~/.claude/` 项           | 链接方式                                   |
| ------------------------- | ------------------------------------------ |
| skills/、scheduled-tasks/ | Junction（目录软链，无需管理员）           |
| settings.json、CLAUDE.md  | 优先 symlink，无管理员时降级 Hardlink      |

**⚠️ 仓库必须放在 `%USERPROFILE%\.claude-config`，绝对不要放 `%LOCALAPPDATA%`。**

原因：Claude Desktop 是 MSIX 应用，它启动的进程（包括 Claude Code 会话）写 `AppData\Local`
会被 Windows **透明重定向**进包容器 `...\AppData\Local\Packages\Claude_xxxx\LocalCache\Local\`。
后果：
- 仓库只有从 Desktop 里才看得见，包外独立 CLI 找不到；
- 卸载 / Reset Claude Desktop 会把容器连同仓库一起清空。

`%USERPROFILE%` 根目录**不受**此重定向影响，所以仓库放那儿。

---

## 三、A —— 全新机器首次配置

```powershell
# 1. clone 到 profile 根（不是 LOCALAPPDATA！）
git clone git@github.com:ZFF00/claude-config.git "$env:USERPROFILE\.claude-config"

# 2. 从仓库里运行部署脚本重建链接
#    主编辑机加 -NoAutoPull（跳过已废弃的每小时计划任务，同步靠 hooks）
& "$env:USERPROFILE\.claude-config\deploy.ps1" -NoAutoPull
```

`deploy.ps1` 会自动：备份 `~/.claude` 里的同名原文件为 `.bak` → 建立四条链接 → 打印每步 `[OK]`。

## 四、B —— 已经装在 %LOCALAPPDATA% 的机器，迁出来

```powershell
$src  = "$env:LOCALAPPDATA\claude-skills"      # 旧位置（在 MSIX 容器里）
$dest = "$env:USERPROFILE\.claude-config"      # 新位置

# 0. 先确保旧仓库干净、已推送（有脏改动先在旧位置 commit+push）
git -C $src status -s

# 1. 复制到新位置（保留 .git，用复制不用移动，留退路）
robocopy $src $dest /E /R:1 /W:1

# 2. 验证新位置 git 完好
git -C $dest rev-parse --short HEAD
git -C $dest remote get-url origin

# 3. 从新位置重建链接（自动指向新址）
& "$dest\deploy.ps1" -NoAutoPull

# 4. 确认远端可达后，删掉容器里的旧副本
git -C $dest fetch --dry-run
Remove-Item -LiteralPath $src -Recurse -Force
```

## 五、验证（两种情况都做）

```powershell
$cl = "$env:USERPROFILE\.claude"
# junction 目标应指向 .claude-config
Get-Item "$cl\skills","$cl\scheduled-tasks" | Select-Object Name,Target
# hardlink 物理成员——绝不能再出现 LocalCache\Packages
fsutil hardlink list "$cl\settings.json"
fsutil hardlink list "$cl\CLAUDE.md"
```

成员里只应看到 `\Users\<你>\.claude\...` 和 `\Users\<你>\.claude-config\...` 两处，
**没有** `Packages\Claude_xxxx\LocalCache` 就对了。

---

## 六、日常同步怎么工作（不用手动）

同步由 `settings.json` 里的 hooks 承担，自动、无需配路径：
- **SessionStart**：后台 `git pull --ff-only`（静默，失败不阻塞）。
- **SessionEnd**：有脏改动就自动 `add + commit + push`（push 被拒先 `pull --rebase` 再推）。
- hooks 靠 `readlink -f ~/.claude/skills` 反查仓库位置，所以仓库放哪都能自动找到，`settings.json` 不用改。

手动同步 / 排查：调用技能 `sync-config`。
原来的每小时计划任务 `claude-config-sync` 已废弃，看到残留就删。

## 七、坑清单（重要）

1. **仓库位置**：放 `%USERPROFILE%\.claude-config`，别放 `%LOCALAPPDATA%`（见第二节 MSIX 重定向）。
2. **改 .ps1 文件**：必须存成 **UTF-8 带 BOM + CRLF**（和 JSON 相反！）。无 BOM 时 PS 5.1 按 GBK
   解码，会吞掉中文注释后的换行、把 `param()` 块吃掉且**静默失效**。存盘选 "UTF-8 with BOM" + 行尾 CRLF。
3. **改 JSON 文件**（settings.json 等）：必须 **无 BOM**，否则 `Unexpected token` 解析失败。
4. **git pull 后 hardlink 可能脱链**：若远端改动了 settings.json 或 CLAUDE.md，pull/rebase 会新建
   文件断开硬链 → **重跑 `deploy.ps1 -NoAutoPull`** 重建，再对比两侧 hash 确认一致。
5. **不进仓库的东西**：settings.local.json（本机差异，如 model/插件）、`~/.claude.json` 和
   `.credentials.json`（凭据，会串号）、cache/sessions/history。这些每台机器自己管。
6. **git 提交**：作者统一 `ZFF00 <1138903623@qq.com>`，**不加任何 AI 归属尾注**
   （不写 `Co-Authored-By` / `Generated with...`）。
