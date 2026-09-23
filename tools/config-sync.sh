#!/bin/sh
# claude-config 自动同步，由 settings.json 的 SessionStart/SessionEnd hook 经
# git 内联 alias 调起。git 的 "!" alias 固定用 Git 自带的 sh 执行（Git for
# Windows 也捆绑 sh），天然跨平台——绕开 Windows 上 hook 命令落到 PowerShell 5.1
# 解析 bash 语法报 ParserError 的问题（2026-09-23 修复前 Windows 侧同步从未生效）。
#
# 用法: sh tools/config-sync.sh pull|push   （git 执行 !alias 时 cwd 已在仓库顶层）
# 约束: 必须保持 POSIX sh 语法；行尾必须 LF（.gitattributes 已全局 eol=lf）。

# 防呆：只在 claude-config 仓库里动手（skills 链接指错地方时静默退出）
git remote get-url origin 2>/dev/null | grep -q 'ZFF00/claude-config' || exit 0

case "$1" in
pull)
    git pull --ff-only --quiet
    ;;
push)
    [ -n "$(git status --porcelain 2>/dev/null)" ] || exit 0
    git add -A
    git -c user.name=ZFF00 -c user.email=1138903623@qq.com commit -q -m "chore(auto-sync): $(uname -n)"
    git push -q || { git pull --rebase -q && git push -q; }
    ;;
esac
