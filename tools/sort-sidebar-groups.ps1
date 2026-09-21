# 排序 Claude Desktop 侧边栏自定义分组：🌐(服务器) 组在前，💻(Local) 组在后，块内保持原有相对顺序。
# 注意：App 只在启动时读取此文件，运行期间外部修改无效且会被内存态覆盖——本脚本应在登录时(App 启动前)执行。
$f = Join-Path $env:LOCALAPPDATA 'Claude-3p\claude_desktop_config.json'
if (-not (Test-Path -LiteralPath $f)) { exit 0 }
try {
  $cfg = [IO.File]::ReadAllText($f) | ConvertFrom-Json
  $scopes = $cfg.preferences.epitaxyPrefs.'dframe-group-scopes'
  if ($null -eq $scopes) { exit 0 }
  $changed = $false
  foreach ($prop in $scopes.PSObject.Properties) {
    $g = @($prop.Value.groups)
    if ($g.Count -lt 2) { continue }
    $remote = @($g | Where-Object { $_.name -like '🌐*' })
    $local  = @($g | Where-Object { $_.name -notlike '🌐*' })
    $sorted = @($remote + $local)
    if ((($g | ForEach-Object { $_.id }) -join ',') -ne (($sorted | ForEach-Object { $_.id }) -join ',')) {
      $prop.Value.groups = $sorted
      $changed = $true
    }
  }
  if ($changed) {
    $out = $cfg | ConvertTo-Json -Depth 100 -Compress
    [IO.File]::WriteAllText($f, $out, (New-Object System.Text.UTF8Encoding($false)))
  }
} catch { exit 0 }
