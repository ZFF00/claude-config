---
name: skill-install-workflow
description: "用户安装技能的偏好流程,以及 skillhub 社区技能在 Claude Code 下的落盘/junction 适配方法"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e8538fc5-e93f-45c0-939c-5db667db8a89
  modified: 2026-09-17T03:24:05.340Z
---

用户对安装类请求的偏好:当需求存在多个候选(如"想要 XX 技能")时,先调研候选、下载到临时目录审阅、给出比较和推荐,**等用户拍板再正式安装**;不要直接装推荐项。明确点名单个技能时可直接装,但装前审查内容(注入/恶意命令/数据外流)。

**Why:** 2026-09-17 我直接安装了 agent-daily-report 并建了定时任务,用户随后说"先不安装,先找一下有哪些,再比较一下哪个好",要求回滚后先比较。

**How to apply:** 模糊需求 → skillhub search → `skillhub install <name> --dir $env:TEMP\skill-review` 临时审阅 → 比较表+推荐 → 用户确认 → 正式安装。

技术要点(见 [[claude-desktop-3p-setup]]):
- skillhub CLI 已装(WindowsApps 下 skillhub.cmd),无 uninstall 子命令,卸载=删目录。
- 社区技能(@user_xxx/@clawhub_xxx)会装进 `~/.claude/skills/@命名空间/技能名/` 二级目录,Claude Code 扫不到;需建 junction 提级:`New-Item -ItemType Junction -Path ~/.claude/skills/技能名 -Target 二级路径`。删 junction 必须用 `cmd /c rmdir`(PS5.1 的 Remove-Item -Recurse 会穿透删目标文件)。
- `~/.claude/skills` 实际落盘在 `~/.claude-skills`(路径映射)。
