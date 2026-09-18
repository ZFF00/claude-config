[CmdletBinding()]
param(
    [string]$ProjectRoot = "",
    [string]$ManifestPath = "",
    [ValidateRange(1, 100)]
    [int]$MaxPasses = 5,
    [ValidateRange(0, 3600)]
    [int]$RetryDelaySeconds = 10,
    [ValidateRange(1, 64)]
    [int]$BufferSizeMB = 4,
    [ValidateRange(5, 600)]
    [int]$ChunkTimeoutSeconds = 30,
    [switch]$SkipPinProject,
    [switch]$MetadataOnly,
    [switch]$VerifyHashes
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not $ProjectRoot) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ProjectRoot = Split-Path -Parent $scriptDirectory
}
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
if (-not $ManifestPath) {
    $ManifestPath = Join-Path $ProjectRoot "manifests/TRANSFER_MANIFEST_SHA256_2026-08-07.csv"
}
$ManifestPath = [System.IO.Path]::GetFullPath($ManifestPath)

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project root does not exist: $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Transfer manifest does not exist: $ManifestPath"
}

$reportDir = Join-Path $ProjectRoot "tmp\wps_sync"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $reportDir "sync_$runStamp.log"
$missingPath = Join-Path $reportDir "missing_$runStamp.csv"
$summaryPath = Join-Path $reportDir "summary_$runStamp.json"
$currentPathMarker = Join-Path $reportDir "current_$runStamp.txt"
$buffer = New-Object byte[] ($BufferSizeMB * 1MB)
$shellApplication = New-Object -ComObject Shell.Application

function Write-SyncLog {
    param([string]$Message)

    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
}

function Convert-ToLocalPath {
    param([string]$RelativePath)

    $normalized = $RelativePath.Replace("/", [System.IO.Path]::DirectorySeparatorChar)
    return Join-Path $ProjectRoot $normalized
}

function Invoke-DirectoryEnumeration {
    param(
        [string]$DirectoryPath,
        [System.Collections.Generic.HashSet[string]]$EnumeratedDirectories
    )

    if (-not $EnumeratedDirectories.Add($DirectoryPath)) {
        return
    }
    if (-not [System.IO.Directory]::Exists($DirectoryPath)) {
        return
    }

    try {
        # Fully consume the listing. WPS normally hydrates cloud-only child metadata here.
        [void]@([System.IO.Directory]::EnumerateFileSystemEntries($DirectoryPath))
    } catch {
        Write-SyncLog "Directory enumeration failed: $DirectoryPath :: $($_.Exception.Message)"
    }
    try {
        # WPS also refreshes directory metadata through the Explorer Shell namespace.
        $shellNamespace = $script:shellApplication.Namespace($DirectoryPath)
        if ($shellNamespace) {
            [void]@($shellNamespace.Items())
        }
    } catch {
        Write-SyncLog "Shell enumeration failed: $DirectoryPath :: $($_.Exception.Message)"
    }
}

function Invoke-ParentEnumeration {
    param(
        [string]$RelativePath,
        [System.Collections.Generic.HashSet[string]]$EnumeratedDirectories
    )

    $parts = @($RelativePath.Replace("\", "/").Split("/") | Where-Object { $_ })
    $current = $ProjectRoot
    Invoke-DirectoryEnumeration -DirectoryPath $current -EnumeratedDirectories $EnumeratedDirectories

    for ($index = 0; $index -lt ($parts.Count - 1); $index++) {
        $current = Join-Path $current $parts[$index]
        Invoke-DirectoryEnumeration -DirectoryPath $current -EnumeratedDirectories $EnumeratedDirectories
    }
}

function Read-FileFully {
    param(
        [string]$Path,
        [long]$ExpectedBytes,
        [string]$ExpectedHash
    )

    $stream = $null
    $hasher = $null
    try {
        $stream = [System.IO.FileStream]::new(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite,
            $buffer.Length,
            ([System.IO.FileOptions]::Asynchronous -bor [System.IO.FileOptions]::SequentialScan)
        )
        if ($VerifyHashes) {
            $hasher = [System.Security.Cryptography.SHA256]::Create()
        }

        [long]$total = 0
        while ($true) {
            $readTask = $stream.ReadAsync($buffer, 0, $buffer.Length)
            if (-not $readTask.Wait([TimeSpan]::FromSeconds($ChunkTimeoutSeconds))) {
                return [pscustomobject]@{ Success = $false; Detail = "read_timeout_after:$total" }
            }
            $read = $readTask.Result
            if ($read -le 0) {
                break
            }
            $total += $read
            if ($hasher) {
                [void]$hasher.TransformBlock($buffer, 0, $read, $null, 0)
            }
        }

        if ($hasher) {
            [void]$hasher.TransformFinalBlock($buffer, 0, 0)
            $actualHash = ([System.BitConverter]::ToString($hasher.Hash)).Replace("-", "")
            if ($ExpectedHash -and $actualHash -ne $ExpectedHash) {
                return [pscustomobject]@{ Success = $false; Detail = "sha256_mismatch:$actualHash" }
            }
        }
        if ($ExpectedBytes -ge 0 -and $total -ne $ExpectedBytes) {
            return [pscustomobject]@{ Success = $false; Detail = "size_mismatch:$total" }
        }

        return [pscustomobject]@{ Success = $true; Detail = "downloaded:$total" }
    } catch {
        return [pscustomobject]@{ Success = $false; Detail = $_.Exception.Message }
    } finally {
        if ($hasher) { $hasher.Dispose() }
        if ($stream) { $stream.Dispose() }
    }
}

$manifestRows = @(Import-Csv -LiteralPath $ManifestPath)
$completed = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$resultByPath = @{}
$startTime = Get-Date

Write-SyncLog "Starting WPS hydration for $($manifestRows.Count) manifest files."
Write-SyncLog "Project root: $ProjectRoot"
Write-SyncLog "Hash verification: $VerifyHashes"

if (-not $SkipPinProject) {
    Write-SyncLog "Applying Windows Pinned attribute to the project tree."
    & attrib.exe +P -U $ProjectRoot
    if ($LASTEXITCODE -ne 0) {
        Write-SyncLog "Warning: attrib returned $LASTEXITCODE for the project root."
    }
    & attrib.exe +P -U (Join-Path $ProjectRoot "*") /S /D
    if ($LASTEXITCODE -ne 0) {
        Write-SyncLog "Warning: recursive attrib returned $LASTEXITCODE."
    }
}

# Discover cloud-only directory entries before content reads can block on a large file.
$previousVisibleCount = -1
for ($metadataPass = 1; $metadataPass -le $MaxPasses; $metadataPass++) {
    $enumeratedDirectories = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($row in $manifestRows) {
        Invoke-ParentEnumeration -RelativePath $row.relative_path -EnumeratedDirectories $enumeratedDirectories
    }
    $visibleCount = @($manifestRows | Where-Object {
        [System.IO.File]::Exists((Convert-ToLocalPath -RelativePath $_.relative_path))
    }).Count
    Write-SyncLog "Metadata pass $metadataPass/${MaxPasses}: visible $visibleCount/$($manifestRows.Count) files."
    if ($visibleCount -eq $manifestRows.Count) {
        break
    }
    if ($metadataPass -lt $MaxPasses -and $RetryDelaySeconds -gt 0) {
        Start-Sleep -Seconds $RetryDelaySeconds
    }
    $previousVisibleCount = $visibleCount
}

if ($MetadataOnly) {
    Write-SyncLog "Metadata-only run complete. Visible manifest files: $visibleCount/$($manifestRows.Count)."
    exit 0
}

for ($pass = 1; $pass -le $MaxPasses; $pass++) {
    $enumeratedDirectories = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $successfulThisPass = 0
    $processedThisPass = 0

    Write-SyncLog "Pass $pass/${MaxPasses}: enumerating expected directory paths."
    foreach ($row in $manifestRows) {
        if (-not $completed.Contains($row.relative_path)) {
            Invoke-ParentEnumeration -RelativePath $row.relative_path -EnumeratedDirectories $enumeratedDirectories
        }
    }

    Write-SyncLog "Pass $pass/${MaxPasses}: reading files to force local hydration."
    foreach ($row in $manifestRows) {
        if ($completed.Contains($row.relative_path)) {
            continue
        }

        $processedThisPass++
        $fullPath = Convert-ToLocalPath -RelativePath $row.relative_path
        if (-not [System.IO.File]::Exists($fullPath)) {
            $resultByPath[$row.relative_path] = "not_visible_locally"
            continue
        }

        try {
            Set-Content -LiteralPath $currentPathMarker -Value $row.relative_path -Encoding UTF8
        } catch {
            # The WPS provider may briefly lock this diagnostic marker while syncing it.
        }
        if ([long]$row.bytes -ge 10MB) {
            Write-SyncLog "Downloading large file ($($row.bytes) bytes): $($row.relative_path)"
        }
        $readResult = Read-FileFully -Path $fullPath -ExpectedBytes ([long]$row.bytes) -ExpectedHash $row.sha256
        $resultByPath[$row.relative_path] = $readResult.Detail
        if ($readResult.Success) {
            [void]$completed.Add($row.relative_path)
            $successfulThisPass++
            if ([long]$row.bytes -ge 10MB) {
                Write-SyncLog "Completed large file: $($row.relative_path)"
            }
        }

        if (($processedThisPass % 100) -eq 0) {
            Write-SyncLog "Pass $pass progress: checked $processedThisPass; hydrated $($completed.Count)/$($manifestRows.Count)."
        }
    }

    $remaining = $manifestRows.Count - $completed.Count
    Write-SyncLog "Pass $pass complete: newly hydrated $successfulThisPass; remaining $remaining."
    if ($remaining -eq 0) {
        break
    }
    if ($pass -lt $MaxPasses -and $RetryDelaySeconds -gt 0) {
        Write-SyncLog "Waiting $RetryDelaySeconds seconds for WPS metadata refresh."
        Start-Sleep -Seconds $RetryDelaySeconds
    }
}

$missingRows = @(
    foreach ($row in $manifestRows) {
        if (-not $completed.Contains($row.relative_path)) {
            [pscustomobject]@{
                relative_path = $row.relative_path
                expected_bytes = [long]$row.bytes
                expected_sha256 = $row.sha256
                status = if ($resultByPath.ContainsKey($row.relative_path)) { $resultByPath[$row.relative_path] } else { "not_checked" }
            }
        }
    }
)
$missingRows | Export-Csv -LiteralPath $missingPath -NoTypeInformation -Encoding UTF8

$additionalRequiredPaths = @(
    "data/processed/adc_rdc_positive_control_targets.json",
    "logs/round54_gap_audit_queries.json",
    "logs/round55_asset_resolution_queries.json"
)
$additionalMissing = @(
    $additionalRequiredPaths | Where-Object {
        -not [System.IO.File]::Exists((Convert-ToLocalPath -RelativePath $_))
    }
)

$summary = [ordered]@{
    started_at = $startTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    finished_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    project_root = $ProjectRoot
    manifest_path = $ManifestPath
    manifest_files = $manifestRows.Count
    hydrated_and_validated = $completed.Count
    missing_or_invalid = $missingRows.Count
    additional_required_missing = $additionalMissing
    verify_hashes = [bool]$VerifyHashes
    missing_report = $missingPath
    log = $logPath
}
$summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Write-SyncLog "Finished: hydrated $($completed.Count)/$($manifestRows.Count); missing or invalid $($missingRows.Count)."
if ($additionalMissing.Count -gt 0) {
    Write-SyncLog "Additional README/HANDOFF files still missing: $($additionalMissing -join ', ')"
}
Write-SyncLog "Missing report: $missingPath"
Write-SyncLog "Summary: $summaryPath"

if ($missingRows.Count -gt 0) {
    exit 2
}
