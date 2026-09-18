<#
.SYNOPSIS
Exposes WPS cloud file metadata, or explicitly pins and hydrates a directory.

.DESCRIPTION
Metadata-only mode uses one Explorer worker window to make WPS expose lazy
directory metadata without pinning or reading file contents. Full localization
mode recursively pins the discovered tree, reads every file, and verifies that
no file remains Offline or recall-on-access. Reports are stored outside the
cloud directory by default.

.EXAMPLE
.\localize_wps_cloud.ps1 "C:\Users\me\WPSDrive\MyFolder" -MetadataOnly

.EXAMPLE
.\localize_wps_cloud.ps1 "D:\WPSDrive\Archive" -CalculateSha256

.EXAMPLE
.\localize_wps_cloud.ps1 "D:\WPSDrive\Archive" -Silent
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [Alias("Path")]
    [string]$TargetPath,

    [ValidateRange(2, 50)]
    [int]$MaxDiscoveryPasses = 8,

    [ValidateRange(0, 30)]
    [int]$ExplorerSettleSeconds = 0,

    [ValidateRange(0, 60)]
    [int]$MetadataRefreshDelaySeconds = 2,

    [ValidateRange(1, 20)]
    [int]$MaxDownloadPasses = 3,

    [ValidateRange(1, 64)]
    [int]$BufferSizeMB = 4,

    [ValidateRange(5, 600)]
    [int]$ReadTimeoutSeconds = 60,

    [string]$ReportDirectory = "",

    [switch]$VisibleExplorer,
    [switch]$Silent,
    [switch]$SkipExplorer,
    [switch]$CalculateSha256,
    [switch]$DiscoveryOnly,
    [switch]$MetadataOnly
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if ($VisibleExplorer -and $Silent) {
    throw "Use either -VisibleExplorer or -Silent, not both."
}
if ($MetadataOnly -and $DiscoveryOnly) {
    throw "Use either -MetadataOnly or -DiscoveryOnly, not both."
}
if ($MetadataOnly -and $CalculateSha256) {
    throw "-CalculateSha256 reads file contents and cannot be used with -MetadataOnly."
}

$script:TargetRoot = [System.IO.Path]::GetFullPath($TargetPath)
if (-not [System.IO.Directory]::Exists($script:TargetRoot)) {
    throw "Target directory does not exist: $($script:TargetRoot)"
}

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (-not $ReportDirectory) {
    $localAppData = [Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
    $ReportDirectory = Join-Path $localAppData "WpsCloudLocalizer\reports\$runStamp"
}
$script:ReportRoot = [System.IO.Path]::GetFullPath($ReportDirectory)
$targetPrefix = $script:TargetRoot.TrimEnd('\') + '\'
if ($script:ReportRoot.Equals($script:TargetRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    $script:ReportRoot.StartsWith($targetPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "ReportDirectory must be outside TargetPath so report writes do not change the cloud tree."
}

New-Item -ItemType Directory -Force -Path $script:ReportRoot | Out-Null
$script:LogPath = Join-Path $script:ReportRoot "localize.log"
$script:SummaryPath = Join-Path $script:ReportRoot "summary.json"
$script:FileReportPath = Join-Path $script:ReportRoot "files.csv"
$script:DirectoryErrorPath = Join-Path $script:ReportRoot "directory_errors.csv"
$script:Buffer = New-Object byte[] ($BufferSizeMB * 1MB)
$script:ShellApplication = $null
$script:WorkerWindow = $null
$script:WorkerWindowOwned = $false
$script:WorkerOriginalPath = $null
$script:WorkerWasVisible = $false
$script:WorkerWasMinimized = $false
$script:DirectoryErrors = [System.Collections.Generic.List[object]]::new()
$script:ReadResults = @{}
$script:VisitedDirectories = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$script:StartTime = Get-Date

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class WpsLocalizerNativeMethods
{
    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);
}
"@

function Write-LocalizerLog {
    param([string]$Message)

    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding UTF8
}

function Get-NormalizedPath {
    param([string]$Path)

    return [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Test-PathInsideTarget {
    param([string]$Path)

    $normalized = Get-NormalizedPath -Path $Path
    return $normalized.Equals($script:TargetRoot.TrimEnd('\'), [System.StringComparison]::OrdinalIgnoreCase) -or
        $normalized.StartsWith($script:TargetRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)
}

function Get-RelativeTargetPath {
    param([string]$Path)

    $rootUri = [Uri]($script:TargetRoot.TrimEnd('\') + '\')
    $pathUri = [Uri](Get-NormalizedPath -Path $Path)
    return [Uri]::UnescapeDataString($rootUri.MakeRelativeUri($pathUri).ToString()).Replace('/', '\')
}

function Get-ShellWindowPath {
    param($Window)

    try {
        $folderPath = $Window.Document.Folder.Self.Path
        if ($folderPath) {
            return Get-NormalizedPath -Path $folderPath
        }
    } catch {
        return $null
    }
    return $null
}

function Get-ShellWindows {
    $windows = @()
    if (-not $script:ShellApplication) {
        return $windows
    }
    try {
        foreach ($window in @($script:ShellApplication.Windows())) {
            try {
                $executable = [System.IO.Path]::GetFileName([string]$window.FullName)
                if ($executable -ieq "explorer.exe") {
                    $windows += $window
                }
            } catch {
                continue
            }
        }
    } catch {
        Write-LocalizerLog "Explorer window enumeration failed: $($_.Exception.Message)"
    }
    return $windows
}

function Find-ShellWindowByPath {
    param(
        [string]$Path,
        [System.Collections.Generic.HashSet[long]]$ExcludedHandles,
        [int]$TimeoutSeconds = 10
    )

    $expected = Get-NormalizedPath -Path $Path
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        foreach ($window in @(Get-ShellWindows)) {
            try {
                $handle = [long]$window.HWND
                if ($ExcludedHandles -and $ExcludedHandles.Contains($handle)) {
                    continue
                }
                $actual = Get-ShellWindowPath -Window $window
                if ($actual -and $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
                    return $window
                }
            } catch {
                continue
            }
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    return $null
}

function Set-ExplorerWorkerDisplay {
    param($Window)

    try {
        $handle = [IntPtr]([long]$Window.HWND)
        if ($Silent) {
            [void][WpsLocalizerNativeMethods]::ShowWindowAsync($handle, 0)
        } elseif (-not $VisibleExplorer) {
            [void][WpsLocalizerNativeMethods]::ShowWindowAsync($handle, 6)
        }
    } catch {}
}

function Start-ExplorerWorker {
    if ($SkipExplorer) {
        Write-LocalizerLog "Explorer navigation disabled by -SkipExplorer."
        return
    }

    $script:ShellApplication = New-Object -ComObject Shell.Application
    $existingHandles = [System.Collections.Generic.HashSet[long]]::new()
    foreach ($window in @(Get-ShellWindows)) {
        try { [void]$existingHandles.Add([long]$window.HWND) } catch {}
    }

    Write-LocalizerLog "Opening one Explorer worker window for directory discovery."
    $script:ShellApplication.Explore($script:TargetRoot)
    $worker = Find-ShellWindowByPath -Path $script:TargetRoot -ExcludedHandles $existingHandles -TimeoutSeconds 12
    if (-not $worker) {
        $worker = Find-ShellWindowByPath -Path $script:TargetRoot -ExcludedHandles $null -TimeoutSeconds 1
        if (-not $worker) {
            Write-LocalizerLog "A dedicated Explorer window was not created; per-directory fallback will be used."
            return
        }
        $script:WorkerOriginalPath = Get-ShellWindowPath -Window $worker
        try {
            $handle = [IntPtr]([long]$worker.HWND)
            $script:WorkerWasVisible = [WpsLocalizerNativeMethods]::IsWindowVisible($handle)
            $script:WorkerWasMinimized = [WpsLocalizerNativeMethods]::IsIconic($handle)
        } catch {}
        Write-LocalizerLog "Reusing an existing Explorer window and restoring it when finished."
    } else {
        $script:WorkerWindowOwned = $true
    }

    $script:WorkerWindow = $worker
    Set-ExplorerWorkerDisplay -Window $worker
}

function Wait-ExplorerAtPath {
    param(
        $Window,
        [string]$Path,
        [int]$TimeoutSeconds = 15
    )

    $expected = Get-NormalizedPath -Path $Path
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        $actual = Get-ShellWindowPath -Window $Window
        if ($actual -and $actual.Equals($expected, [System.StringComparison]::OrdinalIgnoreCase)) {
            try {
                $Window.Refresh()
                [void]@($Window.Document.Folder.Items())
            } catch {}
            return $true
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    return $false
}

function Invoke-ExplorerFallbackVisit {
    param([string]$DirectoryPath)

    $beforeHandles = [System.Collections.Generic.HashSet[long]]::new()
    foreach ($window in @(Get-ShellWindows)) {
        try { [void]$beforeHandles.Add([long]$window.HWND) } catch {}
    }

    try {
        $script:ShellApplication.Explore($DirectoryPath)
        $window = Find-ShellWindowByPath -Path $DirectoryPath -ExcludedHandles $beforeHandles -TimeoutSeconds 12
        if (-not $window) {
            return $false
        }
        Set-ExplorerWorkerDisplay -Window $window
        [void](Wait-ExplorerAtPath -Window $window -Path $DirectoryPath -TimeoutSeconds 5)
        if ($ExplorerSettleSeconds -gt 0) {
            Start-Sleep -Seconds $ExplorerSettleSeconds
        }
        try { $window.Quit() } catch {}
        return $true
    } catch {
        return $false
    }
}

function Invoke-ExplorerVisit {
    param([string]$DirectoryPath)

    if ($SkipExplorer) {
        return $true
    }

    if ($script:WorkerWindow) {
        try {
            $script:WorkerWindow.Navigate2($DirectoryPath)
            if (Wait-ExplorerAtPath -Window $script:WorkerWindow -Path $DirectoryPath -TimeoutSeconds 15) {
                if ($ExplorerSettleSeconds -gt 0) {
                    Start-Sleep -Seconds $ExplorerSettleSeconds
                }
                return $true
            }
        } catch {
            Write-LocalizerLog "Worker navigation failed for $DirectoryPath :: $($_.Exception.Message)"
        }
    }

    return Invoke-ExplorerFallbackVisit -DirectoryPath $DirectoryPath
}

function Close-ExplorerWorker {
    if ($script:WorkerWindow -and $script:WorkerWindowOwned) {
        try {
            $script:WorkerWindow.Quit()
            Write-LocalizerLog "Explorer worker window closed."
        } catch {
            Write-LocalizerLog "Explorer worker close failed: $($_.Exception.Message)"
        }
    } elseif ($script:WorkerWindow -and $script:WorkerOriginalPath) {
        try {
            $script:WorkerWindow.Navigate2($script:WorkerOriginalPath)
            [void](Wait-ExplorerAtPath -Window $script:WorkerWindow -Path $script:WorkerOriginalPath -TimeoutSeconds 10)
            $handle = [IntPtr]([long]$script:WorkerWindow.HWND)
            if ($script:WorkerWasMinimized) {
                [void][WpsLocalizerNativeMethods]::ShowWindowAsync($handle, 6)
            } elseif ($script:WorkerWasVisible) {
                [void][WpsLocalizerNativeMethods]::ShowWindowAsync($handle, 5)
            } else {
                [void][WpsLocalizerNativeMethods]::ShowWindowAsync($handle, 0)
            }
            Write-LocalizerLog "Existing Explorer window restored."
        } catch {
            Write-LocalizerLog "Explorer window restore failed: $($_.Exception.Message)"
        }
    }
    $script:WorkerWindow = $null
    $script:WorkerWindowOwned = $false
    $script:WorkerOriginalPath = $null
    $script:WorkerWasVisible = $false
    $script:WorkerWasMinimized = $false
}

function Set-TreePinned {
    Write-LocalizerLog "Applying Pinned and removing Unpinned attributes."
    & attrib.exe +P -U $script:TargetRoot 2>&1 | ForEach-Object { Write-LocalizerLog "attrib: $_" }
    if ($LASTEXITCODE -ne 0) {
        Write-LocalizerLog "Warning: attrib returned $LASTEXITCODE for the target root."
    }
    & attrib.exe +P -U (Join-Path $script:TargetRoot "*") /S /D 2>&1 | ForEach-Object { Write-LocalizerLog "attrib: $_" }
    if ($LASTEXITCODE -ne 0) {
        Write-LocalizerLog "Warning: recursive attrib returned $LASTEXITCODE."
    }
}

function Add-DirectoryError {
    param(
        [string]$Path,
        [string]$Stage,
        [string]$Detail
    )

    $script:DirectoryErrors.Add([pscustomobject]@{
        path = $Path
        stage = $Stage
        detail = $Detail
    })
}

function Get-ChildDirectories {
    param([string]$DirectoryPath)

    try {
        return @([System.IO.Directory]::EnumerateDirectories($DirectoryPath))
    } catch {
        Add-DirectoryError -Path $DirectoryPath -Stage "enumerate_directories" -Detail $_.Exception.Message
        return @()
    }
}

function Get-ChildFiles {
    param([string]$DirectoryPath)

    try {
        return @([System.IO.Directory]::EnumerateFiles($DirectoryPath))
    } catch {
        Add-DirectoryError -Path $DirectoryPath -Stage "enumerate_files" -Detail $_.Exception.Message
        return @()
    }
}

function Get-TreeSnapshot {
    param([switch]$VisitDirectories)

    $knownDirectories = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $knownFiles = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $queue = [System.Collections.Generic.Queue[string]]::new()
    [void]$knownDirectories.Add($script:TargetRoot)
    $queue.Enqueue($script:TargetRoot)
    $visitFailures = 0

    while ($queue.Count -gt 0) {
        $directory = $queue.Dequeue()
        if ($VisitDirectories -and -not $script:VisitedDirectories.Contains($directory)) {
            if (Invoke-ExplorerVisit -DirectoryPath $directory) {
                [void]$script:VisitedDirectories.Add($directory)
            } else {
                $visitFailures++
                Add-DirectoryError -Path $directory -Stage "explorer_visit" -Detail "Explorer did not navigate to this directory."
            }
        }

        try {
            [void]@([System.IO.Directory]::EnumerateFileSystemEntries($directory))
        } catch {
            Add-DirectoryError -Path $directory -Stage "enumerate_entries" -Detail $_.Exception.Message
        }

        foreach ($file in @(Get-ChildFiles -DirectoryPath $directory)) {
            if (Test-PathInsideTarget -Path $file) {
                [void]$knownFiles.Add((Get-NormalizedPath -Path $file))
            }
        }
        foreach ($child in @(Get-ChildDirectories -DirectoryPath $directory)) {
            $normalizedChild = Get-NormalizedPath -Path $child
            if ((Test-PathInsideTarget -Path $normalizedChild) -and $knownDirectories.Add($normalizedChild)) {
                $queue.Enqueue($normalizedChild)
            }
        }
    }

    $directories = @($knownDirectories | Sort-Object)
    $files = @($knownFiles | Sort-Object)
    $signatureInput = (@($directories | ForEach-Object { "D:" + (Get-RelativeTargetPath -Path $_) }) +
        @($files | ForEach-Object { "F:" + (Get-RelativeTargetPath -Path $_) })) -join "`n"
    $signatureBytes = [System.Text.Encoding]::UTF8.GetBytes($signatureInput)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        $signature = ([BitConverter]::ToString($hasher.ComputeHash($signatureBytes))).Replace("-", "")
    } finally {
        $hasher.Dispose()
    }

    return [pscustomobject]@{
        Directories = $directories
        Files = $files
        Signature = $signature
        VisitFailures = $visitFailures
    }
}

function Invoke-StableDiscovery {
    $previousSignature = $null
    $stableCount = 0
    $lastSnapshot = $null
    for ($pass = 1; $pass -le $MaxDiscoveryPasses; $pass++) {
        if ($pass -gt 1 -and $MetadataRefreshDelaySeconds -gt 0) {
            Write-LocalizerLog "Waiting $MetadataRefreshDelaySeconds seconds for WPS metadata refresh."
            Start-Sleep -Seconds $MetadataRefreshDelaySeconds
        }
        Write-LocalizerLog "Discovery pass $pass/$MaxDiscoveryPasses started."
        $lastSnapshot = Get-TreeSnapshot -VisitDirectories:(-not $SkipExplorer)
        Write-LocalizerLog "Discovery pass $pass found $($lastSnapshot.Directories.Count) directories and $($lastSnapshot.Files.Count) files; Explorer failures: $($lastSnapshot.VisitFailures)."

        if ($lastSnapshot.Signature -eq $previousSignature) {
            $stableCount++
        } else {
            $stableCount = 0
        }
        if ($stableCount -ge 1) {
            return [pscustomobject]@{ Snapshot = $lastSnapshot; Stabilized = $true; Passes = $pass }
        }
        $previousSignature = $lastSnapshot.Signature
    }

    return [pscustomobject]@{ Snapshot = $lastSnapshot; Stabilized = $false; Passes = $MaxDiscoveryPasses }
}

function Test-AttributeFlag {
    param(
        [System.IO.FileAttributes]$Attributes,
        [long]$Flag
    )

    return (([long]$Attributes -band $Flag) -ne 0)
}

function Get-LocalizationState {
    param([string]$FilePath)

    try {
        $attributes = [System.IO.File]::GetAttributes($FilePath)
        $offline = Test-AttributeFlag -Attributes $attributes -Flag ([long][System.IO.FileAttributes]::Offline)
        $recallOnOpen = Test-AttributeFlag -Attributes $attributes -Flag 0x00040000
        $recallOnDataAccess = Test-AttributeFlag -Attributes $attributes -Flag 0x00400000
        return [pscustomobject]@{
            Exists = $true
            Attributes = [long]$attributes
            Offline = $offline
            RecallOnOpen = $recallOnOpen
            RecallOnDataAccess = $recallOnDataAccess
            NeedsHydration = ($offline -or $recallOnOpen -or $recallOnDataAccess)
        }
    } catch {
        return [pscustomobject]@{
            Exists = $false
            Attributes = 0
            Offline = $false
            RecallOnOpen = $false
            RecallOnDataAccess = $false
            NeedsHydration = $true
        }
    }
}

function Read-FileFully {
    param([string]$FilePath)

    $stream = $null
    $hasher = $null
    try {
        $stream = [System.IO.FileStream]::new(
            $FilePath,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite,
            $script:Buffer.Length,
            ([System.IO.FileOptions]::Asynchronous -bor [System.IO.FileOptions]::SequentialScan)
        )
        if ($CalculateSha256) {
            $hasher = [System.Security.Cryptography.SHA256]::Create()
        }

        [long]$totalBytes = 0
        while ($true) {
            $readTask = $stream.ReadAsync($script:Buffer, 0, $script:Buffer.Length)
            if (-not $readTask.Wait([TimeSpan]::FromSeconds($ReadTimeoutSeconds))) {
                return [pscustomobject]@{
                    Success = $false
                    Bytes = $totalBytes
                    Sha256 = $null
                    Detail = "read_timeout_after:$totalBytes"
                }
            }
            $read = $readTask.Result
            if ($read -le 0) {
                break
            }
            $totalBytes += $read
            if ($hasher) {
                [void]$hasher.TransformBlock($script:Buffer, 0, $read, $null, 0)
            }
        }

        $sha256 = $null
        if ($hasher) {
            [void]$hasher.TransformFinalBlock($script:Buffer, 0, 0)
            $sha256 = ([BitConverter]::ToString($hasher.Hash)).Replace("-", "")
        }
        return [pscustomobject]@{
            Success = $true
            Bytes = $totalBytes
            Sha256 = $sha256
            Detail = "read_complete"
        }
    } catch {
        return [pscustomobject]@{
            Success = $false
            Bytes = 0
            Sha256 = $null
            Detail = $_.Exception.Message
        }
    } finally {
        if ($hasher) { $hasher.Dispose() }
        if ($stream) { $stream.Dispose() }
    }
}

function Invoke-DownloadPass {
    param(
        [string[]]$Files,
        [int]$Pass
    )

    $checked = 0
    $failures = 0
    foreach ($file in $Files) {
        $checked++
        $relativePath = Get-RelativeTargetPath -Path $file
        $readResult = Read-FileFully -FilePath $file
        $state = Get-LocalizationState -FilePath $file
        $success = $readResult.Success -and $state.Exists -and -not $state.NeedsHydration
        if (-not $success) {
            $failures++
        }
        $script:ReadResults[$file] = [pscustomobject]@{
            relative_path = $relativePath
            full_path = $file
            locally_discoverable = [bool]$state.Exists
            content_local = [bool]($state.Exists -and -not $state.NeedsHydration)
            bytes_read = [long]$readResult.Bytes
            sha256 = $readResult.Sha256
            success = $success
            detail = $readResult.Detail
            attributes = [long]$state.Attributes
            offline = [bool]$state.Offline
            recall_on_open = [bool]$state.RecallOnOpen
            recall_on_data_access = [bool]$state.RecallOnDataAccess
            download_pass = $Pass
        }

        if (($checked % 100) -eq 0 -or $checked -eq $Files.Count) {
            Write-LocalizerLog "Download pass $Pass progress: $checked/$($Files.Count); failures or still offline: $failures."
        }
    }
    return $failures
}

function Export-FinalReports {
    param(
        $Discovery,
        $FinalSnapshot,
        [bool]$Completed,
        [int]$RemainingOffline,
        [int]$ReadFailures
    )

    $fileRows = foreach ($file in $FinalSnapshot.Files) {
        if ($script:ReadResults.ContainsKey($file)) {
            $readRow = $script:ReadResults[$file]
            [pscustomobject]@{
                relative_path = $readRow.relative_path
                full_path = $readRow.full_path
                locally_discoverable = [bool]$readRow.locally_discoverable
                content_local = [bool]$readRow.content_local
                bytes_read = $readRow.bytes_read
                sha256 = $readRow.sha256
                success = [bool]$readRow.success
                detail = $readRow.detail
                attributes = $readRow.attributes
                offline = $readRow.offline
                recall_on_open = $readRow.recall_on_open
                recall_on_data_access = $readRow.recall_on_data_access
                download_pass = $readRow.download_pass
            }
        } else {
            $state = Get-LocalizationState -FilePath $file
            $contentLocal = $state.Exists -and -not $state.NeedsHydration
            [pscustomobject]@{
                relative_path = Get-RelativeTargetPath -Path $file
                full_path = $file
                locally_discoverable = [bool]$state.Exists
                content_local = [bool]$contentLocal
                bytes_read = 0
                sha256 = $null
                success = if ($MetadataOnly) { [bool]$state.Exists } else { [bool]$contentLocal }
                detail = if ($MetadataOnly) { "metadata_visible_not_read" } else { "not_read" }
                attributes = [long]$state.Attributes
                offline = [bool]$state.Offline
                recall_on_open = [bool]$state.RecallOnOpen
                recall_on_data_access = [bool]$state.RecallOnDataAccess
                download_pass = 0
            }
        }
    }
    @($fileRows) | Export-Csv -LiteralPath $script:FileReportPath -NoTypeInformation -Encoding UTF8
    @($script:DirectoryErrors) | Export-Csv -LiteralPath $script:DirectoryErrorPath -NoTypeInformation -Encoding UTF8

    $summary = [ordered]@{
        started_at = $script:StartTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        finished_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        target_path = $script:TargetRoot
        fully_localized = $Completed
        metadata_only = [bool]$MetadataOnly
        locally_discoverable = [bool]($Discovery.Stabilized -and $script:DirectoryErrors.Count -eq 0)
        discovery_stabilized = [bool]$Discovery.Stabilized
        discovery_passes = [int]$Discovery.Passes
        directories_discovered = [int]$FinalSnapshot.Directories.Count
        files_discovered = [int]$FinalSnapshot.Files.Count
        remaining_offline_or_recall = $RemainingOffline
        read_failures = $ReadFailures
        directory_errors = [int]$script:DirectoryErrors.Count
        directories_visited_in_explorer = [int]$script:VisitedDirectories.Count
        explorer_navigation_enabled = (-not [bool]$SkipExplorer)
        silent_explorer = [bool]$Silent
        explorer_settle_seconds = $ExplorerSettleSeconds
        metadata_refresh_delay_seconds = $MetadataRefreshDelaySeconds
        hashes_calculated = [bool]$CalculateSha256
        discovery_only = [bool]$DiscoveryOnly
        report_directory = $script:ReportRoot
        file_report = $script:FileReportPath
        directory_error_report = $script:DirectoryErrorPath
        log = $script:LogPath
        limitation = "Completeness covers the directory tree exposed by the installed WPS cloud provider; no server-side manifest API is used."
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $script:SummaryPath -Encoding UTF8
}

try {
    Write-LocalizerLog "WPS cloud localization started."
    Write-LocalizerLog "Target: $($script:TargetRoot)"
    Write-LocalizerLog "Reports: $($script:ReportRoot)"
    if (-not $MetadataOnly) {
        Set-TreePinned
    }
    Start-ExplorerWorker

    $discovery = Invoke-StableDiscovery
    $snapshot = $discovery.Snapshot
    if (-not $MetadataOnly) {
        Set-TreePinned
    }

    if ($MetadataOnly) {
        $remaining = @($snapshot.Files | Where-Object { (Get-LocalizationState -FilePath $_).NeedsHydration }).Count
        $locallyDiscoverable = $discovery.Stabilized -and $script:DirectoryErrors.Count -eq 0
        Export-FinalReports -Discovery $discovery -FinalSnapshot $snapshot -Completed $false -RemainingOffline $remaining -ReadFailures 0
        Write-LocalizerLog "Metadata-only run finished: $($snapshot.Directories.Count) directories, $($snapshot.Files.Count) files, discovery_stabilized=$($discovery.Stabilized), directory_errors=$($script:DirectoryErrors.Count). No files were pinned or content-read."
        Write-LocalizerLog "Summary: $($script:SummaryPath)"
        if (-not $locallyDiscoverable) {
            exit 2
        }
        exit 0
    }

    if ($DiscoveryOnly) {
        $remaining = @($snapshot.Files | Where-Object { (Get-LocalizationState -FilePath $_).NeedsHydration }).Count
        Export-FinalReports -Discovery $discovery -FinalSnapshot $snapshot -Completed $false -RemainingOffline $remaining -ReadFailures 0
        Write-LocalizerLog "Discovery-only run finished: $($snapshot.Directories.Count) directories, $($snapshot.Files.Count) files, $remaining offline or recall-on-access."
        exit 0
    }

    for ($downloadPass = 1; $downloadPass -le $MaxDownloadPasses; $downloadPass++) {
        Write-LocalizerLog "Download pass $downloadPass/$MaxDownloadPasses started for $($snapshot.Files.Count) files."
        [void](Invoke-DownloadPass -Files $snapshot.Files -Pass $downloadPass)
        Set-TreePinned

        $nextDiscovery = Invoke-StableDiscovery
        $nextSnapshot = $nextDiscovery.Snapshot
        $offlineNow = @($nextSnapshot.Files | Where-Object { (Get-LocalizationState -FilePath $_).NeedsHydration }).Count
        $failedNow = @($script:ReadResults.Values | Where-Object { -not $_.success }).Count
        Write-LocalizerLog "Download pass $downloadPass finished: $offlineNow files still offline or recall-on-access; $failedNow read results unsuccessful."

        $treeChanged = $nextSnapshot.Signature -ne $snapshot.Signature
        $snapshot = $nextSnapshot
        $discovery = $nextDiscovery
        if (-not $treeChanged -and $offlineNow -eq 0 -and $failedNow -eq 0 -and $discovery.Stabilized) {
            break
        }
    }

    $remainingOffline = @($snapshot.Files | Where-Object { (Get-LocalizationState -FilePath $_).NeedsHydration }).Count
    $readFailures = @($script:ReadResults.Values | Where-Object { -not $_.success }).Count
    $completed = $discovery.Stabilized -and $remainingOffline -eq 0 -and $readFailures -eq 0 -and $script:DirectoryErrors.Count -eq 0
    Export-FinalReports -Discovery $discovery -FinalSnapshot $snapshot -Completed $completed -RemainingOffline $remainingOffline -ReadFailures $readFailures

    Write-LocalizerLog "Finished: directories=$($snapshot.Directories.Count), files=$($snapshot.Files.Count), remaining_offline=$remainingOffline, read_failures=$readFailures, directory_errors=$($script:DirectoryErrors.Count)."
    Write-LocalizerLog "Summary: $($script:SummaryPath)"
    if (-not $completed) {
        exit 2
    }
    exit 0
} finally {
    Close-ExplorerWorker
    if ($script:ShellApplication) {
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($script:ShellApplication) } catch {}
    }
}
