# Create junction  %USERPROFILE%\.claude\skills  ->  this folder (claude-skills).
# Copying/patching of skills has already been done; this only creates the link.
# Safe: if ~/.claude/skills already exists as a real folder with content, its items are
# moved into this folder first (conflicts are left in place and reported).

$ErrorActionPreference = "Stop"
$Dest = Split-Path -Parent $MyInvocation.MyCommand.Path
$Link = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Link) | Out-Null

if (Test-Path -LiteralPath $Link) {
    $item = Get-Item -LiteralPath $Link -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        $t = $item.Target; if ($t -is [array]) { $t = $t[0] }
        if ($t -and ($t.TrimEnd('\') -ieq $Dest.TrimEnd('\'))) { Write-Host "Already linked: $Link -> $Dest"; exit 0 }
        Write-Host "$Link is already a link to: $t" -ForegroundColor Yellow
        Write-Host "Remove it first (rmdir `"$Link`") and re-run." -ForegroundColor Yellow
        exit 1
    }
    foreach ($e in @(Get-ChildItem -LiteralPath $Link -Force)) {
        $to = Join-Path $Dest $e.Name
        if (Test-Path -LiteralPath $to) { Write-Host "conflict, left in place: $($e.Name)" -ForegroundColor Yellow }
        else { Move-Item -LiteralPath $e.FullName -Destination $to; Write-Host "moved existing: $($e.Name)" }
    }
    if (@(Get-ChildItem -LiteralPath $Link -Force).Count -gt 0) {
        Write-Host "Unmoved items remain in $Link; junction NOT created." -ForegroundColor Red; exit 1
    }
    Remove-Item -LiteralPath $Link -Force
}
New-Item -ItemType Junction -Path $Link -Target $Dest | Out-Null
Write-Host "Junction created: $Link -> $Dest"
Write-Host ("Skills visible through it: " + (@(Get-ChildItem -LiteralPath $Link -Directory).Count))
