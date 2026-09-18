# claude-config Windows 部署脚本
# 把仓库内容链接到 ~/.claude/ 下对应位置。已存在的本机文件先备份为 .bak。
$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$cl   = Join-Path $env:USERPROFILE ".claude"
New-Item -ItemType Directory -Path $cl -Force | Out-Null

function Backup-IfExists($path){
  if(Test-Path -LiteralPath $path){
    $item = Get-Item -LiteralPath $path -Force
    if($item.LinkType){ # 已是链接，直接删
      if($item.PSIsContainer){ [System.IO.Directory]::Delete($path,$false) } else { Remove-Item -LiteralPath $path -Force }
    } else {
      $bak = "$path.bak"
      Move-Item -LiteralPath $path -Destination $bak -Force
      Write-Host "已备份现有 $path -> $bak"
    }
  }
}

# 1. skills 目录 junction
$linkSkills = Join-Path $cl "skills"
Backup-IfExists $linkSkills
New-Item -ItemType Junction -Path $linkSkills -Target (Join-Path $repo "skills") | Out-Null
Write-Host "[OK] skills junction"

# 2. settings.json symlink（如需本机差异化，改用 settings.local.json 覆盖）
$linkSettings = Join-Path $cl "settings.json"
Backup-IfExists $linkSettings
New-Item -ItemType SymbolicLink -Path $linkSettings -Target (Join-Path $repo "settings.json") | Out-Null
Write-Host "[OK] settings.json symlink"

# 3. CLAUDE.md symlink
$linkClaude = Join-Path $cl "CLAUDE.md"
Backup-IfExists $linkClaude
New-Item -ItemType SymbolicLink -Path $linkClaude -Target (Join-Path $repo "CLAUDE.md") | Out-Null
Write-Host "[OK] CLAUDE.md symlink"

# 4. scheduled-tasks junction
$linkST = Join-Path $cl "scheduled-tasks"
Backup-IfExists $linkST
New-Item -ItemType Junction -Path $linkST -Target (Join-Path $repo "scheduled-tasks") | Out-Null
Write-Host "[OK] scheduled-tasks junction"

# 5. 注册每小时自动拉取
schtasks /create /tn "claude-config-sync" /tr "git -C `"$repo`" pull --ff-only" /sc hourly /f | Out-Null
Write-Host "[OK] 已注册每小时自动 pull"

Write-Host "`n部署完成。注意：凭据(.claude.json)与本机差异(settings.local.json)不由本仓库管理。"
Write-Host "若需 symlink 权限，请以管理员运行或开启开发者模式。"
