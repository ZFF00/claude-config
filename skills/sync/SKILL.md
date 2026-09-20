---
name: sync
description: 手动同步 claude-config 配置仓库：拉取最新、提交推送本地脏改动、修复历史分叉与硬链接脱钩，并汇报每步结果。SessionStart/SessionEnd hooks 静默失败或怀疑配置不同步时使用。
argument-hint: "（可选）pull=只拉取 / push=只推送 / status=只检查不改动"
---

手动同步 claude-config 仓库（远程 `git@github.com:ZFF00/claude-config.git`）。hooks 的自动同步是静默的，本技能相反：**每一步都要报告结果，出现异常要说明原因并给出处理**。

## 第 0 步：定位仓库

```bash
r=$(dirname "$(readlink -f "$HOME/.claude/skills")")
git -C "$r" remote get-url origin
```

remote 必须匹配 `ZFF00/claude-config`，否则停止并报告。后续所有 git 操作用 `git -C "$r"`。

## 第 1 步：体检（参数 status 只做到这步）

报告：`git -C "$r" status -sb`（脏文件、ahead/behind）+ `git -C "$r" fetch` 后本地与 `origin/main` 的差异。

## 第 2 步：推送本地脏改动（参数 pull 跳过）

若工作区有脏改动：向用户展示 `git status -s` 与简要 diff 概况，**确认内容合理后**提交推送：

```bash
git -C "$r" add -A
git -C "$r" -c user.name=ZFF00 -c user.email=1138903623@qq.com commit -m "<按改动内容写有意义的 message>"
git -C "$r" push
```

- 提交 message 按实际改动写（如 `feat(skills): ...`），不要用 `chore(auto-sync)`。
- **禁止任何 AI 归属尾注**（Co-Authored-By 等）。
- 若发现明显误改（不该入库的内容），先问用户是提交还是 `git checkout --` 还原。

## 第 3 步：拉取（参数 push 跳过）

```bash
git -C "$r" pull --rebase
```

- rebase 冲突：展示冲突文件与两边内容，让用户决定（配置仓库多为追加式改动，通常两边都保留）；解决后 `git rebase --continue` 并 push。
- 提示 non-fast-forward / 历史被改写（远端曾 force push）且本地无独有提交时：`git fetch && git reset --hard origin/main` 对齐，并向用户说明。本地有独有提交则先走第 2 步推送逻辑或问用户。

## 第 4 步：链接完整性（Windows 专属，Linux 跳过）

pull 重写文件会打断硬链接。逐一核对：

```bash
diff -q ~/.claude/settings.json "$r/settings.json"
diff -q ~/.claude/CLAUDE.md "$r/CLAUDE.md"
```

不一致的用 PowerShell 重建（注意：以仓库侧为准，先确认 `~/.claude` 侧没有未同步的新改动）：

```
Remove-Item -LiteralPath <链接路径> -Force
New-Item -ItemType HardLink -Path <链接路径> -Target <仓库文件>
```

## 第 5 步：汇总

一段话报告：拉了什么（最新几条提交标题）、推了什么、修了什么链接、当前 `status -sb` 是否干净同步。
