# claude-skills

Claude Code 的 skill 目录（真实位置）。`~/.claude/skills` 是指向这里的目录联接（junction）。

- 来源：同级的 `skills/`（Codex skill 目录）中筛选出的 Claude 兼容 skill 的副本
- 原则：这里的文件是**副本**，可以自由修改；`skills/` 里的原件不动
- 路径差异：副本里 `~/.codex/skills` / `$CODEX_HOME/skills` 已替换为 `~/.claude/skills`

导入脚本：`import-codex-skills-to-claude.ps1`（复制 + 建立 junction）
