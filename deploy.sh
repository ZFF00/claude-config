#!/usr/bin/env bash
# claude-config Linux/HA 部署脚本
# 把仓库内容软链到 ~/.claude/ 下对应位置。已存在的本机文件先备份为 .bak。
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CL="$HOME/.claude"
mkdir -p "$CL"

backup_if_exists() {
  local p="$1"
  if [ -L "$p" ]; then rm -f "$p"
  elif [ -e "$p" ]; then mv "$p" "$p.bak"; echo "已备份 $p -> $p.bak"; fi
}

# 1. skills
backup_if_exists "$CL/skills"
ln -sfn "$REPO/skills" "$CL/skills"
echo "[OK] skills symlink"

# 2. settings.json（本机差异用 settings.local.json 覆盖）
backup_if_exists "$CL/settings.json"
ln -sf "$REPO/settings.json" "$CL/settings.json"
echo "[OK] settings.json symlink"

# 3. CLAUDE.md
backup_if_exists "$CL/CLAUDE.md"
ln -sf "$REPO/CLAUDE.md" "$CL/CLAUDE.md"
echo "[OK] CLAUDE.md symlink"

# 4. scheduled-tasks
backup_if_exists "$CL/scheduled-tasks"
ln -sfn "$REPO/scheduled-tasks" "$CL/scheduled-tasks"
echo "[OK] scheduled-tasks symlink"

# 5. 每小时自动拉取
# 注意：set -euo pipefail 下，空 crontab 时 `crontab -l` 退出 1、`grep -v` 无匹配也退出 1，
# 会让整条管线在 pipefail 下失败并中断脚本（软链已建好但 crontab 未注册）。`|| true` 兜底两种情况。
( crontab -l 2>/dev/null | grep -v 'claude-config pull' || true ; echo "0 * * * * git -C \"$REPO\" pull --ff-only -q" ) | crontab -
echo "[OK] 已注册每小时自动 pull (crontab)"

echo ""
echo "部署完成。凭据与本机差异(settings.local.json)不由本仓库管理。"
