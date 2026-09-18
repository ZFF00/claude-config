---
name: git-daily-report
description: 基于 git 提交历史生成本地化、结构化的每日工作日报（简体中文）。当用户要求「写日报」「生成今日工作汇报」「汇总今天的提交」「把 git 活动整理成日报」或需要把一天的 commit 归纳成可粘贴的汇报时使用此技能。
license: MIT
compatibility: Requires Python 3.10+ and git installed on PATH.
metadata:
  author: workbuddy
  version: "1.0"
allowed-tools: Bash(python:*) Bash(git:*)
---

# Git 每日工作日报

## 目标
把当天（或指定区间）的 git 提交，整理成一份**简洁、可粘贴、按模块分组**的中文工作日报，而不是逐条罗列 commit hash。

## 流程
1. 用脚本收集提交（非交互、结构化输出）：
   ```bash
   python scripts/collect_git.py --since "1 day ago"
   ```
   可按需加 `--until`、`--author`、`--repo <路径>`、`--format text`。
2. 读取脚本返回的 JSON：`{ "count": N, "commits": [ {hash, author, date, subject}, ... ] }`。
3. 按以下结构组织日报：
   - **今日完成**：按模块 / 项目分组归纳（合并同主题提交）。
   - **进行中**：依据未合分支、WIP 提交推断。
   - **风险与阻塞**：没有就写「无」，不要编造。
   - **明日计划**：基于分支名、TODO 注释、未完成任务给出 2-4 条。
4. 用流畅简体中文输出；专业术语可保留英文缩写，但解释用中文。

## Gotchas（易错点）
- 部分 CI 机器时区非 UTC，`--since "1 day ago"` 可能偏移；可用 `--since "2026-08-26"` 明确日期。
- 私有仓库的提交邮件 / 分支名可能含内部信息，生成前先确认脱敏。
- 若脚本返回 `"count": 0`，**如实告知用户没有提交**，绝不编造工作内容。
- Windows 上 `git` 若在 PATH 外，先确认可用；脚本已对缺失 git 给出 stderr 提示并退出码 2。

## 验证清单
- [ ] 已确认工作目录 / `--repo` 指向目标 git 仓库
- [ ] 已对敏感信息脱敏
- [ ] 日报按「模块」分组，而非按 commit 逐条罗列
- [ ] 风险与阻塞未编造；无则写「无」
