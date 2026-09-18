---
name: wps-cloud-localizer
description: Expose WPS Cloud / WPS 云盘 folder metadata on Windows so local programs can enumerate paths and recognize that files exist, without opening or downloading file contents by default. Also supports explicit full hydration, offline pinning, SHA-256 verification against a transfer manifest, and incomplete-sync diagnosis. Use when a user asks to make a WPS cloud directory locally visible, list cloud files from a program, download an entire WPS folder, keep it offline, verify hydration, recover missing project files, audit sync completeness, or run the bundled scripts. Do not use for deleting WPS conflict copies or silently stopping WPS processes.
---

# WPS Cloud Localizer

Operate only on the exact WPS directory the user identifies. Default to metadata-only discovery: expose names and paths without pinning or reading file contents. Pin and hydrate only when the user explicitly asks for a complete download, offline availability, content verification, or SHA-256 validation. The scripts do not upload, rename, overwrite, or delete source files.

## Select A Workflow

1. Use `scripts/localize_wps_cloud.ps1 -MetadataOnly` by default for a general WPS folder without a trusted manifest.
2. Use `scripts/sync_wps_project.ps1` when the project has a CSV transfer manifest with `relative_path`, `bytes`, and `sha256` columns.
3. Use `scripts/wps-localize.cmd` only as a convenience wrapper for the general workflow.

Read [references/operations.md](references/operations.md) before a live run or when diagnosing incomplete results.

## Preflight

1. Resolve the target to an absolute path and confirm it is the user-selected directory, not a drive root, profile root, or broad workspace root.
2. Ensure the report directory is outside the target WPS tree. The general script enforces this and defaults to `%LOCALAPPDATA%\WpsCloudLocalizer\reports\<timestamp>`.
3. Check free disk space only before a full hydration run. Metadata-only discovery does not intentionally download file contents.
4. Check whether another localizer or sync run is already operating on the same tree. Do not run concurrent passes against one target.
5. Leave `wpscloudsvr` running. Do not stop WPS, Explorer, or sync processes unless the user explicitly requests troubleshooting that requires it.
6. Preserve every `-副本<timestamp>` conflict file. Report conflicts separately; never delete or merge them automatically.

## General Folder Workflow

Default to metadata-only discovery so local programs can enumerate names and paths:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/localize_wps_cloud.ps1 `
  "C:\Users\me\WPSDrive\Folder" -MetadataOnly
```

This mode does not pin files, read their contents, calculate hashes, or claim offline readiness. Use `-SkipExplorer` only when WPS has already exposed the directory metadata.

Only after an explicit request for full download or offline availability, hydrate and verify local attributes:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/localize_wps_cloud.ps1 `
  "C:\Users\me\WPSDrive\Folder" -CalculateSha256
```

Use `-Silent` to hide the worker Explorer window or `-VisibleExplorer` for interactive diagnosis. Do not combine `-Silent` and `-VisibleExplorer`. `-MetadataOnly` cannot be combined with `-DiscoveryOnly` or `-CalculateSha256`.

## Manifest Project Workflow

Always pass both paths because the bundled script must not infer a project from the skill directory. For visibility only, avoid pinning and content reads:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/sync_wps_project.ps1 `
  -ProjectRoot "C:\Users\me\WPSDrive\Project" `
  -ManifestPath "C:\Users\me\WPSDrive\Project\manifests\TRANSFER_MANIFEST_SHA256.csv" `
  -MetadataOnly -SkipPinProject
```

For an explicitly requested full manifest verification:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/sync_wps_project.ps1 `
  -ProjectRoot "C:\Users\me\WPSDrive\Project" `
  -ManifestPath "C:\Users\me\WPSDrive\Project\manifests\TRANSFER_MANIFEST_SHA256.csv" `
  -VerifyHashes
```

In metadata-only manifest runs, always include `-SkipPinProject` unless the user explicitly asks to change pinning attributes.

## Validate The Result

1. Require an exit code of `0` for the requested mode. Treat exit code `2` as incomplete. The CMD wrapper uses exit code `64` for missing arguments.
2. Open the generated `summary.json`, CSV file report, missing-file report, and log as applicable.
3. For general metadata-only discovery, require `metadata_only=true`, `locally_discoverable=true`, `discovery_stabilized=true`, and `directory_errors=0`. Expect `fully_localized=false`; offline/recall counts are diagnostic only.
4. For a general full-hydration run, require `fully_localized=true`, `remaining_offline_or_recall=0`, `read_failures=0`, and `directory_errors=0`.
5. For the manifest workflow, require the mode-appropriate visible or validated count, `missing_or_invalid=0`, and an empty `additional_required_missing` list.
6. Report the exact target, run mode, discovered or expected file count, localized count, failures, report path, and whether hashes were calculated.
7. State the limitation that completeness covers the directory tree exposed by the installed WPS provider; the general workflow has no server-side manifest API.

## Failure Handling

- Retry boundedly when metadata is still appearing, a file remains recall-on-access, or WPS temporarily locks a file.
- Keep failure records and partial reports. Do not delete them before a successful retry.
- If a file hash or size differs from the trusted manifest, report it as `missing_or_invalid`; do not overwrite either copy.
- If the directory tree does not stabilize, stop after the configured pass limit and report the incomplete state.
- If the exact target is unclear or resolving it could affect a broad directory, stop and ask the user to identify the intended folder.

## Bundled Scripts

- `scripts/localize_wps_cloud.ps1`: expose metadata by default workflow, or explicitly pin, hydrate, and audit a general WPS folder.
- `scripts/sync_wps_project.ps1`: hydrate and validate files listed by a transfer manifest.
- `scripts/wps-localize.cmd`: Windows CMD wrapper for the general localizer.
