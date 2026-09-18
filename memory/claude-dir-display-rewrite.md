---
name: claude-dir-display-rewrite
description: 本机环境坑：工具输出里 ~/.claude/ 路径会被显示为 ~/.claude-N/（N 递增），磁盘文件实际无损
metadata: 
  node_type: memory
  type: project
  originSessionId: ab28bebd-345e-483b-b000-8de947130a4c
  modified: 2026-09-18T03:11:39.165Z
---

2026-09-18 确认的本机现象：工具结果/技能加载文本中，`~/.claude/` 及其绝对路径形式会被某个显示层改写成带递增数字后缀的假路径（`.claude-2`、`.claude-7` 等）。用 python 读原始字节验证过：磁盘内容是正确的 `~/.claude/`。疑与 claude-mem 钩子有关（2026-09-17 安装）。

**Why:** 曾因照抄显示出来的假路径导致脚本执行失败、误以为文件被写坏而反复"修复"。

**How to apply:** 凡在工具输出或技能文本里看到 `~/.claude-数字/` 路径，一律按 `~/.claude/` 使用；不要试图去"修复"文件里显示的这类路径——先用 `python3 -c "open(...,'rb')"` 或 `od -c` 核对磁盘字节再下结论。
