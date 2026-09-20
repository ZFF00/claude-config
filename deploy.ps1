# claude-config Windows 部署脚本
# 把仓库内容链接到 ~/.claude/ 下对应位置。已存在的本机文件先备份为 .bak。
# 目录用 junction（无需管理员）；文件优先 symlink，失败则 hardlink（无需管理员），
# 再失败才复制。默认注册每小时自动 pull；主编辑机可加 -NoAutoPull 跳过。
param([switch]$NoAutoPull)
$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$cl   = Join-Path $env:USERPROFILE ".claude"
New-Item -ItemType Directory -Path $cl -Force | Out-Null

function Backup-IfExists($path){
  if(Test-Path -LiteralPath $path){
    $item = Get-Item -LiteralPath $path -Force
    if($item.LinkType){
      if($item.PSIsContainer){ [System.IO.Directory]::Delete($path,$false) } else { Remove-Item -LiteralPath $path -Force }
    } else {
      $bak = "$path.bak"
      if(Test-Path -LiteralPath $bak){ Remove-Item -LiteralPath $bak -Recurse -Force }
      Move-Item -LiteralPath $path -Destination $bak -Force
      Write-Host "  backup: $path -> $bak"
    }
  }
}

function Link-Dir($name){
  $link = Join-Path $cl $name; $tgt = Join-Path $repo $name
  Backup-IfExists $link
  New-Item -ItemType Junction -Path $link -Target $tgt | Out-Null
  Write-Host "[OK] $name junction"
}

function Link-File($name){
  $link = Join-Path $cl $name; $tgt = Join-Path $repo $name
  Backup-IfExists $link
  try { New-Item -ItemType SymbolicLink -Path $link -Target $tgt -ErrorAction Stop | Out-Null; Write-Host "[OK] $name symlink"; return }
  catch {}
  try { New-Item -ItemType HardLink -Path $link -Target $tgt -ErrorAction Stop | Out-Null; Write-Host "[OK] $name hardlink (no-admin)"; return }
  catch {}
  Copy-Item -LiteralPath $tgt -Destination $link -Force
  Write-Host "[COPY] $name copied (no link privilege; re-run after pull)"
}

Link-Dir  "skills"
Link-File "settings.json"
Link-File "CLAUDE.md"
Link-Dir  "scheduled-tasks"

if(-not $NoAutoPull){
  $tr = 'git -C "' + $repo + '" pull --ff-only'
  schtasks /create /tn "claude-config-sync" /tr $tr /sc hourly /f | Out-Null
  Write-Host "[OK] registered hourly auto-pull (use -NoAutoPull on the authoring machine to skip)"
} else {
  Write-Host "[SKIP] auto-pull not registered (-NoAutoPull)"
}

Write-Host ""
Write-Host "Done. Credentials (.claude.json) and per-machine overrides (settings.local.json) are NOT managed by this repo."
Write-Host "Note: a hardlink can detach after git pull rewrites the file; re-run this script after pulling new config."
