# Download Manifest Schema

Use UTF-8 CSV or JSON. Validate all rows before starting network transfers.

## Input Fields

| Field | Required | Meaning |
|---|---:|---|
| `relative_path` | Yes | Safe destination path below `--output-dir`; absolute paths and `..` are rejected |
| `url` | Yes | Public anonymous HTTP, HTTPS, or FTP file URL |
| `bytes` | No | Expected non-negative file length |
| `sha256` | No | Trusted 64-character hexadecimal SHA-256 |
| `md5` | No | Trusted 32-character hexadecimal legacy MD5 |

CSV example:

```csv
relative_path,url,bytes,sha256,md5
raw/sample-a.fastq.gz,https://example.org/sample-a.fastq.gz,1048576,0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef,
```

JSON may be an array or an object containing `files`:

```json
{
  "files": [
    {
      "relative_path": "raw/sample-a.fastq.gz",
      "url": "https://example.org/sample-a.fastq.gz",
      "bytes": 1048576,
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }
  ]
}
```

Repository name, accession, dataset version, license, citation, checksum source URL, and retrieval date should be stored beside the transfer manifest when known. They are provenance metadata, not required downloader inputs in version 1.

## Generated Inventory

The `verify` and `manifest` commands produce CSV with:

| Field | Meaning |
|---|---|
| `relative_path` | Path relative to the inventoried root |
| `bytes` | Actual local byte length |
| `sha256` | Actual locally calculated SHA-256 |

Generated hashes are `local_baseline` until compared with a trusted upstream checksum.

## JSON Report

The report contains `schema_version`, mode and timestamps, aggregate `summary`, and per-file `results`. Important result fields include `status`, `integrity_level`, expected/actual bytes and hashes, attempts, resume state, quarantine paths, partial path, and error.
