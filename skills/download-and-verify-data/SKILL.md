---
name: download-and-verify-data
description: Use when a user asks to download public data files or datasets, resume an interrupted transfer, download from a CSV or JSON manifest, verify existing downloads, compare checksums, or create a SHA-256 inventory. Do not use for sources requiring login, cookies, API tokens, or other credentials.
---

# Download And Verify Data

Download public anonymous data with explicit, machine-readable integrity evidence. Never call a locally calculated hash an upstream verification.

## Workflow

1. Resolve the exact public source URL, expected files, destination, dataset version, expected bytes, and publisher checksums. Prefer a repository API, official CLI, or exported manifest over scraping a web page.
2. Use the user-selected destination. If none is given, create `downloads/<task-name>/` inside the current workspace. Never default to a profile root, desktop, or system Downloads folder.
3. Read [references/integrity-policy.md](references/integrity-policy.md) before downloading. Read [references/manifest-schema.md](references/manifest-schema.md) for batch input or interoperable output.
4. Use an available Python 3 interpreter to run `scripts/data_transfer.py`. In Codex Desktop, load workspace dependencies when Python is not on `PATH`. Do not install Python or download tools automatically.
5. Require exit code `0` and inspect the JSON report before reporting success. Exit code `2` means incomplete or failed integrity; `64` means invalid input.

## Commands

Single file with trusted evidence:

```powershell
python scripts/data_transfer.py download --url "https://example.org/data.bin" --output "downloads/study/data.bin" --bytes 123456 --sha256 "<64-hex>" --report "downloads/study/download-report.json"
```

Batch download:

```powershell
python scripts/data_transfer.py batch --manifest "manifest.csv" --output-dir "downloads/study" --report "downloads/study/batch-report.json"
```

Inventory existing files:

```powershell
python scripts/data_transfer.py verify --path "downloads/study" --manifest-output "downloads/study-sha256.csv" --report "downloads/study-verify.json"
```

For a public data repository, first resolve direct file URLs and official checksums with its stable API or CLI, write a manifest, then use `batch`. Do not claim that this script can interpret every repository page.

## Safety Rules

- Accept only anonymous `https`, `http`, or `ftp` URLs. Reject credential-bearing URLs.
- Download to `.part`; finalize on the same volume only after validation.
- Resume only when URL plus a strong ETag, or URL plus Last-Modified and Content-Length, still match.
- Use bounded retries. Never convert a retry limit into an infinite loop.
- Preserve existing unverified files. Quarantine an existing file only when trusted size or checksum proves it conflicts.
- Quarantine rejected downloaded bytes; never promote them to the requested final path.
- Always calculate SHA-256. Treat MD5 as legacy accidental-corruption evidence, not strong authentication.
- Require every supplied checksum to match; a matching MD5 must never override a SHA-256 mismatch.

## Result Handoff

Report the absolute destination, source, file count, bytes, integrity level, checksum source, resumed transfers, quarantined paths, failures, and JSON report path. Say `local_baseline` explicitly when no publisher checksum was available.

## Common Mistakes

| Mistake | Required correction |
|---|---|
| Calling a local hash verified | Label it `local_baseline` |
| Overwriting a same-name file | Validate, preserve, or quarantine with evidence |
| Trusting HTTP success alone | Check bytes and calculate SHA-256 |
| Parsing arbitrary HTML by default | Prefer an official API, CLI, or manifest |
| Hiding partial failures | Return exit code `2` and retain the report |
