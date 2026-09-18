# WPS Cloud Localization Operations

## Workflow Comparison

| Workflow | Source of expected files | Primary verification | Reports |
|---|---|---|---|
| General metadata-only | Directory tree exposed by WPS | Stable local enumeration of names and paths | `summary.json`, `files.csv`, `directory_errors.csv`, `localize.log` |
| General full hydration | Directory tree exposed by WPS | Offline and recall-on-access attributes; optional SHA-256 | `summary.json`, `files.csv`, `directory_errors.csv`, `localize.log` |
| Manifest project | Trusted transfer manifest | File visibility, byte count, optional manifest SHA-256 | `summary_*.json`, `missing_*.csv`, `sync_*.log` |

## General Metadata-Only Mode

Run `localize_wps_cloud.ps1 -MetadataOnly` for the default visibility goal. It:

- Uses a minimized or hidden Explorer worker to expose lazy WPS directory metadata, unless `-SkipExplorer` is set.
- Enumerates directory names and file paths until the exposed tree stabilizes.
- Does not apply `Pinned`/`Unpinned` attributes.
- Does not open or read file contents and does not calculate content hashes.
- Reports `metadata_only=true`, `locally_discoverable`, and `fully_localized=false`.

`locally_discoverable=true` means ordinary local programs can enumerate the paths currently exposed by WPS. It does not mean file contents are downloaded, readable without network access, or fully available offline.

## General Full-Hydration Mode

- Applies Windows `Pinned` and removes `Unpinned` attributes with `attrib.exe +P -U`.
- Uses a minimized or hidden Explorer worker by default to expose lazy WPS directory metadata.
- Reads each file sequentially to trigger local hydration.
- Writes reports outside the target tree by default.
- Does not rename, edit, upload, or delete files.

Running the general script without `-MetadataOnly` preserves the full-localization behavior. `-DiscoveryOnly` still pins the target tree and enumerates it, but does not perform the full content-read passes; use `-MetadataOnly` when pinning must not change.

## What The Manifest Script Changes

- Optionally applies `Pinned` attributes to the project tree.
- Enumerates parent directories from manifest paths and reads expected files.
- Writes diagnostic reports under `<ProjectRoot>\tmp\wps_sync`.
- With `-VerifyHashes`, compares each hydrated file to the manifest SHA-256.
- Does not repair a mismatch or replace a missing file.

The manifest CSV must contain:

| Column | Meaning |
|---|---|
| `relative_path` | Path relative to `ProjectRoot` |
| `bytes` | Expected file length |
| `sha256` | Expected SHA-256, used with `-VerifyHashes` |

## Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Requested run completed, or discovery/metadata-only mode completed |
| `2` | Full localization or manifest validation remains incomplete |
| `64` | The CMD wrapper was called without a target path |

Metadata-only exit code `0` means discovery stabilized without directory errors. It proves only local discoverability of the tree exposed by WPS, not content hydration. Discovery-only exit code `0` likewise does not prove every file is hydrated.

## WPS Process And Conflict Files

`wpscloudsvr` running is normally expected. The scripts rely on the installed WPS cloud provider to expose and hydrate content, so process presence is not itself a blocker.

WPS may create names such as `name-副本20260809123000.ext` after synchronization conflicts. Localization must preserve these files. Compare hashes and timestamps separately before any later cleanup, and require explicit user authorization for deletion.

## Bounded Retry Guidance

- General folder: tune `MaxDiscoveryPasses`, `MetadataRefreshDelaySeconds`, and `MaxDownloadPasses`.
- Manifest project: tune `MaxPasses`, `RetryDelaySeconds`, and `ChunkTimeoutSeconds`.
- Default to metadata-only. Run full hydration only when the user explicitly requests complete download, offline availability, or content/hash verification.
- Do not increase timeouts indefinitely. Preserve the failed report and identify the exact blocked path.

## Result Handoff

Report:

1. Absolute target path.
2. General or manifest workflow.
3. Discovery stabilization state.
4. Total directories/files or manifest rows.
5. Remaining offline, read failures, missing files, invalid hashes, and directory errors.
6. Whether SHA-256 verification ran.
7. Report directory and summary path.
8. Any WPS conflict copies observed, without deleting them.
