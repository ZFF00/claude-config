# Import selected Codex skills into Claude Code via a junction.
#
# Layout after running:
#   <AI>\claude-skills\            real folder (this script lives here) - Claude agent can read/write it
#   %USERPROFILE%\.claude\skills   junction -> <AI>\claude-skills        - Claude Code reads skills through it
#
# - Source folder (<AI>\skills, the Codex skills) is NOT modified.
# - Every path fix below is applied to the COPY only.
# - Existing skill folders in the destination are skipped unless -Overwrite.
# - Script is ASCII-only on purpose (Windows PowerShell 5.1 mis-reads non-ASCII
#   literals in BOM-less .ps1 files); paths are derived from the script location.
#
# Usage (run from anywhere):
#   powershell -ExecutionPolicy Bypass -File "<path>\claude-skills\import-codex-skills-to-claude.ps1"
#   ... -Overwrite      overwrite skill folders that already exist in claude-skills
#   ... -SkipJunction   only copy, do not touch %USERPROFILE%\.claude\skills

param(
    [switch]$Overwrite,
    [switch]$SkipJunction
)

$ErrorActionPreference = "Stop"

# ---------- resolve paths from script location ----------
$Dest   = Split-Path -Parent $MyInvocation.MyCommand.Path          # ...\AI\claude-skills
$AiRoot = Split-Path -Parent $Dest                                  # ...\AI
$Source = Join-Path $AiRoot "skills"                                # ...\AI\skills  (Codex)
$Link   = Join-Path $env:USERPROFILE ".claude\skills"

if (-not (Test-Path (Join-Path $Source "scanpy\SKILL.md"))) {
    Write-Host "Codex skills folder not found next to this script: $Source" -ForegroundColor Red
    exit 1
}

Write-Host "Codex source : $Source"
Write-Host "Claude dest  : $Dest"
Write-Host "Junction     : $Link  ->  $Dest"
Write-Host ""

# ---------- skill list ----------
# key = folder under source, value = folder under dest
$skills = [ordered]@{
    # --- ready to use as-is (27) ---
    "define-goal"                         = "define-goal"
    "create-readme"                       = "create-readme"
    "folder-structure-blueprint-generator"= "folder-structure-blueprint-generator"
    "python-project-structure"            = "python-project-structure"
    "python-configuration"                = "python-configuration"
    "python-testing-patterns"             = "python-testing-patterns"
    "uv-package-manager"                  = "uv-package-manager"
    "anndata"                             = "anndata"
    "scanpy"                              = "scanpy"
    "scvi-tools"                          = "scvi-tools"
    "bulk-rnaseq"                         = "bulk-rnaseq"
    "cellxgene-census"                    = "cellxgene-census"
    "nextflow"                            = "nextflow"
    "scientific-visualization"            = "scientific-visualization"
    "scientific-writing"                  = "scientific-writing"
    "literature-review"                   = "literature-review"
    "citation-management"                 = "citation-management"
    "paper-lookup"                        = "paper-lookup"
    "scipilot-figure-skill"               = "scipilot-figure-skill"
    "research"                            = "research"
    "research-report"                     = "research-report"
    "research-project-bootstrap"          = "research-project-bootstrap"
    "data-analysis-skills"                = "data-analysis-skills"
    "download-and-verify-data"            = "download-and-verify-data"
    "wps-cloud-localizer"                 = "wps-cloud-localizer"
    "agent-handoff"                       = "agent-handoff"
    ".system\review-agent"                = "review-agent"
    # --- need path fixes in the copy (5) ---
    "visual-report"                       = "visual-report"
    "jupyter-notebook"                    = "jupyter-notebook"
    "research-deep"                       = "research-deep"
    "skill-navigator"                     = "skill-navigator"
    "screenshot"                          = "screenshot"
}

# ---------- copy ----------
$copied = @(); $skipped = @(); $missing = @()
foreach ($entry in $skills.GetEnumerator()) {
    $src = Join-Path $Source $entry.Key
    $dst = Join-Path $Dest   $entry.Value
    if (-not (Test-Path -LiteralPath $src)) { $missing += $entry.Key; continue }
    if ((Test-Path -LiteralPath $dst) -and -not $Overwrite) { $skipped += $entry.Value; continue }
    if (Test-Path -LiteralPath $dst) { Remove-Item -Recurse -Force -LiteralPath $dst }
    Copy-Item -Recurse -Force -LiteralPath $src -Destination $dst
    $copied += $entry.Value
}

# ---------- path fixes (COPIES ONLY) ----------
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function Patch-File {
    param([string]$Path, [hashtable]$Replacements)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $text = [System.IO.File]::ReadAllText($Path, $utf8NoBom)
    $orig = $text
    foreach ($k in $Replacements.Keys) { $text = $text.Replace($k, $Replacements[$k]) }
    if ($text -ne $orig) {
        [System.IO.File]::WriteAllText($Path, $text, $utf8NoBom)
        Write-Host "  patched: $Path"
    }
}

Write-Host "Applying path fixes to copies..."
$codexToClaude = @{ "~/.codex/skills" = "~/.claude/skills"; '$CODEX_HOME/skills' = '$HOME/.claude/skills' }

foreach ($name in @("visual-report", "jupyter-notebook", "research-deep", "skill-navigator")) {
    if ($copied -contains $name) {
        Patch-File (Join-Path $Dest "$name\SKILL.md") $codexToClaude
    }
}
if ($copied -contains "skill-navigator") {
    # scan_skills.py: Path.home()/".codex"/skills -> Path.home()/".claude"/skills (and project-level likewise)
    Patch-File (Join-Path $Dest "skill-navigator\scripts\scan_skills.py") @{ '".codex"' = '".claude"' }
}
# screenshot: no path fix needed; "Codex" there is only an example app name.

# ---------- junction ----------
if (-not $SkipJunction) {
    Write-Host ""
    Write-Host "Setting up junction..."
    $claudeDir = Split-Path -Parent $Link
    New-Item -ItemType Directory -Force -Path $claudeDir | Out-Null

    if (Test-Path -LiteralPath $Link) {
        $item = Get-Item -LiteralPath $Link -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $target = $item.Target
            if ($target -is [array]) { $target = $target[0] }
            if ($target -and ($target.TrimEnd('\') -ieq $Dest.TrimEnd('\'))) {
                Write-Host "  junction already points to $Dest - nothing to do"
            } else {
                Write-Host "  $Link is already a link to: $target" -ForegroundColor Yellow
                Write-Host "  Not changing it. Remove it manually (rmdir `"$Link`") and re-run if you want it repointed." -ForegroundColor Yellow
            }
        } else {
            # real directory: move its contents into Dest, then replace with junction
            $existing = @(Get-ChildItem -LiteralPath $Link -Force)
            if ($existing.Count -gt 0) {
                Write-Host "  $Link already has $($existing.Count) item(s); moving them into $Dest"
                foreach ($e in $existing) {
                    $to = Join-Path $Dest $e.Name
                    if (Test-Path -LiteralPath $to) {
                        Write-Host "    conflict, left in place: $($e.Name)" -ForegroundColor Yellow
                    } else {
                        Move-Item -LiteralPath $e.FullName -Destination $to
                        Write-Host "    moved: $($e.Name)"
                    }
                }
            }
            $left = @(Get-ChildItem -LiteralPath $Link -Force)
            if ($left.Count -eq 0) {
                Remove-Item -LiteralPath $Link -Force
                New-Item -ItemType Junction -Path $Link -Target $Dest | Out-Null
                Write-Host "  junction created: $Link -> $Dest"
            } else {
                Write-Host "  $Link still has unmoved items; junction NOT created. Resolve conflicts and re-run." -ForegroundColor Red
            }
        }
    } else {
        New-Item -ItemType Junction -Path $Link -Target $Dest | Out-Null
        Write-Host "  junction created: $Link -> $Dest"
    }
}

# ---------- report ----------
Write-Host ""
Write-Host ("Copied  ({0}): {1}" -f $copied.Count,  ($copied  -join ", "))
if ($skipped.Count) { Write-Host ("Skipped ({0}, already exist; use -Overwrite): {1}" -f $skipped.Count, ($skipped -join ", ")) -ForegroundColor Yellow }
if ($missing.Count) { Write-Host ("Missing in source ({0}): {1}" -f $missing.Count, ($missing -join ", ")) -ForegroundColor Yellow }
Write-Host ""
Write-Host "Done. Restart Claude Code (or start a new session) to pick up the skills."
