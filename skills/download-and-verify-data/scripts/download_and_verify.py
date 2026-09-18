#!/usr/bin/env python3
"""Download public data and produce explicit integrity evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen


EXIT_OK = 0
EXIT_INCOMPLETE = 2
EXIT_USAGE = 64
CHUNK_SIZE = 1024 * 1024


class InputError(ValueError):
    pass


class IntegrityError(RuntimeError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InputError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_public_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https", "ftp"}:
        raise InputError(f"unsupported URL scheme: {parsed.scheme or '(missing)'}")
    if not parsed.hostname:
        raise InputError("URL must include a host")
    if parsed.username is not None or parsed.password is not None:
        raise InputError("credential-bearing URLs are not allowed")
    return value


def validate_sha256(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise InputError("sha256 must contain exactly 64 hexadecimal characters")
    return normalized


def validate_md5(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if len(normalized) != 32 or any(char not in "0123456789abcdef" for char in normalized):
        raise InputError("md5 must contain exactly 32 hexadecimal characters")
    return normalized


def parse_expected_bytes(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"bytes must be an integer, got {value!r}") from exc
    if parsed < 0:
        raise InputError("bytes must be non-negative")
    return parsed


def safe_relative_path(value: str) -> Path:
    normalized = value.replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if not normalized or candidate.is_absolute() or ".." in candidate.parts:
        raise InputError(f"unsafe relative_path: {value!r}")
    if any(":" in part or part in {"", "."} for part in candidate.parts):
        raise InputError(f"unsafe relative_path: {value!r}")
    return Path(*candidate.parts)


def hash_file(path: Path, include_md5: bool = False) -> dict[str, Any]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5() if include_md5 else None
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            size += len(chunk)
            sha256.update(chunk)
            if md5 is not None:
                md5.update(chunk)
    result: dict[str, Any] = {"bytes": size, "sha256": sha256.hexdigest()}
    if md5 is not None:
        result["md5"] = md5.hexdigest()
    return result


def quarantine(path: Path) -> Path:
    quarantine_root = path.parent / ".download-quarantine" / timestamp_slug()
    quarantine_root.mkdir(parents=True, exist_ok=True)
    destination = quarantine_root / path.name
    counter = 1
    while destination.exists():
        destination = quarantine_root / f"{path.name}.{counter}"
        counter += 1
    shutil.move(str(path), str(destination))
    return destination


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def summarize(results: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(results),
        "verified": 0,
        "local_baseline": 0,
        "failed": 0,
        "skipped": 0,
    }
    for item in results:
        level = item.get("integrity_level")
        status = item.get("status")
        if isinstance(level, str) and level.startswith("verified_"):
            summary["verified"] += 1
        elif level == "local_baseline":
            summary["local_baseline"] += 1
        if status in {"error", "integrity_failed", "conflict"}:
            summary["failed"] += 1
        if status == "already_valid":
            summary["skipped"] += 1
    return summary


def make_report(mode: str, started_at: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mode": mode,
        "started_at": started_at,
        "finished_at": utc_now(),
        "summary": summarize(results),
        "results": results,
    }


def read_metadata(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def probe_url(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, method="HEAD", headers={"User-Agent": "download-and-verify-data/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            headers = response.headers
            return {
                "final_url": response.geturl(),
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
                "content_length": parse_expected_bytes(headers.get("Content-Length")),
                "accept_ranges": headers.get("Accept-Ranges"),
            }
    except HTTPError as exc:
        if exc.code not in {400, 403, 405, 501}:
            raise
    except (URLError, OSError):
        pass
    return {
        "final_url": url,
        "etag": None,
        "last_modified": None,
        "content_length": None,
        "accept_ranges": None,
    }


def metadata_matches(previous: dict[str, Any] | None, current: dict[str, Any], url: str) -> bool:
    if not previous or previous.get("url") != url:
        return False
    if current.get("etag"):
        return previous.get("etag") == current.get("etag")
    return all(
        previous.get(key) == current.get(key)
        for key in ("last_modified", "content_length")
    ) and bool(current.get("last_modified") or current.get("content_length") is not None)


def download_attempt(
    url: str,
    part: Path,
    metadata_path: Path,
    remote: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    previous = read_metadata(metadata_path)
    offset = part.stat().st_size if part.exists() and metadata_matches(previous, remote, url) else 0
    if part.exists() and offset == 0:
        quarantine(part)
    headers = {"User-Agent": "download-and-verify-data/1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
        if remote.get("etag"):
            headers["If-Range"] = remote["etag"]
        elif remote.get("last_modified"):
            headers["If-Range"] = remote["last_modified"]
    atomic_json_write(
        metadata_path,
        {
            "url": url,
            "final_url": remote.get("final_url"),
            "etag": remote.get("etag"),
            "last_modified": remote.get("last_modified"),
            "content_length": remote.get("content_length"),
        },
    )
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", None)
        resumed = bool(offset and status == 206)
        mode = "ab" if resumed else "wb"
        if offset and not resumed:
            offset = 0
        with part.open(mode) as handle:
            while chunk := response.read(CHUNK_SIZE):
                handle.write(chunk)
        response_length = parse_expected_bytes(response.headers.get("Content-Length"))
        final_url = response.geturl()
    return {
        "resumed": resumed,
        "resume_offset": offset if resumed else 0,
        "response_length": response_length,
        "final_url": final_url,
    }


def download_one(
    url: str,
    output: Path,
    expected_bytes: int | None = None,
    expected_sha256: str | None = None,
    expected_md5: str | None = None,
    retries: int = 3,
    timeout: float = 30.0,
) -> dict[str, Any]:
    validate_public_url(url)
    expected_sha256 = validate_sha256(expected_sha256)
    expected_md5 = validate_md5(expected_md5)
    expected_bytes = parse_expected_bytes(expected_bytes)
    if retries < 1 or retries > 20:
        raise InputError("retries must be between 1 and 20")
    if timeout <= 0:
        raise InputError("timeout must be positive")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "url": url,
        "final_url": None,
        "path": str(output),
        "status": None,
        "integrity_level": None,
        "integrity_note": None,
        "expected_bytes": expected_bytes,
        "expected_sha256": expected_sha256,
        "expected_md5": expected_md5,
        "actual_bytes": None,
        "actual_sha256": None,
        "actual_md5": None,
        "etag": None,
        "last_modified": None,
        "attempts": 0,
        "resumed": False,
        "quarantined_existing": None,
        "quarantined_download": None,
        "partial_path": None,
        "error": None,
    }

    if output.exists():
        existing = hash_file(output, include_md5=bool(expected_md5))
        sha_matches = expected_sha256 and existing["sha256"] == expected_sha256
        md5_matches = expected_md5 and existing.get("md5") == expected_md5
        size_matches = expected_bytes is None or existing["bytes"] == expected_bytes
        if size_matches and (sha_matches or md5_matches):
            result.update(
                {
                    "status": "already_valid",
                    "integrity_level": "verified_sha256" if sha_matches else "verified_md5",
                    "integrity_note": "Existing file matches the trusted upstream checksum.",
                    "actual_bytes": existing["bytes"],
                    "actual_sha256": existing["sha256"],
                    "actual_md5": existing.get("md5"),
                }
            )
            return result
        if expected_sha256 or expected_md5 or expected_bytes is not None:
            result["quarantined_existing"] = str(quarantine(output))
        else:
            result.update(
                {
                    "status": "conflict",
                    "integrity_level": "unverified",
                    "integrity_note": "Existing file was preserved because no trusted expectation can identify it.",
                    "actual_bytes": existing["bytes"],
                    "actual_sha256": existing["sha256"],
                    "error": "target exists without a trusted checksum or expected size",
                }
            )
            return result

    remote = probe_url(url, timeout)
    result["final_url"] = remote.get("final_url")
    result["etag"] = remote.get("etag")
    result["last_modified"] = remote.get("last_modified")
    part = Path(str(output) + ".part")
    metadata_path = Path(str(part) + ".meta.json")
    last_error: Exception | None = None
    transfer: dict[str, Any] = {}
    for attempt in range(1, retries + 1):
        result["attempts"] = attempt
        try:
            transfer = download_attempt(url, part, metadata_path, remote, timeout)
            last_error = None
            break
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 8))
    if last_error is not None:
        result.update(
            {
                "status": "error",
                "integrity_level": "unverified",
                "integrity_note": "Download did not complete; partial data was retained for a bounded retry.",
                "partial_path": str(part) if part.exists() else None,
                "error": str(last_error),
            }
        )
        return result

    actual = hash_file(part, include_md5=bool(expected_md5))
    result["actual_bytes"] = actual["bytes"]
    result["actual_sha256"] = actual["sha256"]
    result["actual_md5"] = actual.get("md5")
    result["final_url"] = transfer.get("final_url") or result["final_url"]
    result["resumed"] = bool(transfer.get("resumed"))
    remote_size = remote.get("content_length")
    required_size = expected_bytes if expected_bytes is not None else remote_size
    mismatch = None
    if required_size is not None and actual["bytes"] != required_size:
        mismatch = f"size mismatch: expected {required_size}, got {actual['bytes']}"
    elif expected_sha256 and actual["sha256"] != expected_sha256:
        mismatch = "sha256 mismatch"
    elif expected_md5 and actual.get("md5") != expected_md5:
        mismatch = "md5 mismatch"
    if mismatch:
        result.update(
            {
                "status": "integrity_failed",
                "integrity_level": "failed",
                "integrity_note": "Downloaded bytes did not match the trusted expectation.",
                "error": mismatch,
                "quarantined_download": str(quarantine(part)),
            }
        )
        metadata_path.unlink(missing_ok=True)
        return result

    os.replace(part, output)
    metadata_path.unlink(missing_ok=True)
    if expected_sha256:
        level = "verified_sha256"
        note = "Downloaded file matches the trusted upstream SHA-256."
    elif expected_md5:
        level = "verified_md5"
        note = "Downloaded file matches the upstream MD5; MD5 is a legacy integrity check."
    else:
        level = "local_baseline"
        note = "Local SHA-256 was recorded, but it is not an upstream integrity proof."
    result.update({"status": "downloaded", "integrity_level": level, "integrity_note": note})
    return result


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("files") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise InputError("JSON manifest must be a list or contain a files list")
    else:
        raise InputError("manifest must be CSV or JSON")
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise InputError(f"manifest row {index} must be an object")
        relative = safe_relative_path(str(row.get("relative_path", "")))
        url = validate_public_url(str(row.get("url", "")))
        normalized.append(
            {
                "relative_path": relative,
                "url": url,
                "bytes": parse_expected_bytes(row.get("bytes")),
                "sha256": validate_sha256(row.get("sha256")),
                "md5": validate_md5(row.get("md5")),
            }
        )
    return normalized


def write_inventory(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "relative_path": row["relative_path"],
                    "bytes": row["actual_bytes"],
                    "sha256": row["actual_sha256"],
                }
            )
    os.replace(temporary, path)


def default_report_path(base: Path, mode: str) -> Path:
    return base / f"{mode}-report-{timestamp_slug()}.json"


def run_download(args: argparse.Namespace) -> int:
    started_at = utc_now()
    output = Path(args.output)
    result = download_one(
        args.url,
        output,
        expected_bytes=args.bytes,
        expected_sha256=args.sha256,
        expected_md5=args.md5,
        retries=args.retries,
        timeout=args.timeout,
    )
    report_path = Path(args.report) if args.report else default_report_path(output.parent, "download")
    report = make_report("download", started_at, [result])
    atomic_json_write(report_path, report)
    print(json.dumps({"report": str(report_path.resolve()), "summary": report["summary"]}))
    return EXIT_INCOMPLETE if report["summary"]["failed"] else EXIT_OK


def run_batch(args: argparse.Namespace) -> int:
    started_at = utc_now()
    manifest = load_manifest(Path(args.manifest))
    output_dir = Path(args.output_dir).resolve()
    results = []
    for row in manifest:
        results.append(
            download_one(
                row["url"],
                output_dir / row["relative_path"],
                expected_bytes=row["bytes"],
                expected_sha256=row["sha256"],
                expected_md5=row["md5"],
                retries=args.retries,
                timeout=args.timeout,
            )
        )
        results[-1]["relative_path"] = row["relative_path"].as_posix()
    report_path = Path(args.report) if args.report else default_report_path(output_dir, "batch")
    report = make_report("batch", started_at, results)
    atomic_json_write(report_path, report)
    print(json.dumps({"report": str(report_path.resolve()), "summary": report["summary"]}))
    return EXIT_INCOMPLETE if report["summary"]["failed"] else EXIT_OK


def inventory_path(path: Path) -> tuple[Path, list[Path]]:
    resolved = path.resolve()
    if not resolved.exists():
        raise InputError(f"path does not exist: {resolved}")
    if resolved.is_file():
        return resolved.parent, [resolved]
    files = sorted(
        item
        for item in resolved.rglob("*")
        if item.is_file()
        and ".download-quarantine" not in item.parts
        and not item.name.endswith((".part", ".part.meta.json"))
    )
    return resolved, files


def run_verify(args: argparse.Namespace) -> int:
    started_at = utc_now()
    root, files = inventory_path(Path(args.path))
    results = []
    for file_path in files:
        actual = hash_file(file_path)
        results.append(
            {
                "relative_path": file_path.relative_to(root).as_posix(),
                "path": str(file_path),
                "status": "inventoried",
                "integrity_level": "local_baseline",
                "integrity_note": "Local SHA-256 was recorded, but it is not an upstream integrity proof.",
                "actual_bytes": actual["bytes"],
                "actual_sha256": actual["sha256"],
                "error": None,
            }
        )
    report_path = Path(args.report) if args.report else default_report_path(root.parent, "verify")
    report = make_report("verify", started_at, results)
    atomic_json_write(report_path, report)
    if args.manifest_output:
        write_inventory(Path(args.manifest_output), results)
    print(json.dumps({"report": str(report_path.resolve()), "summary": report["summary"]}))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser("download", help="Download one public URL")
    download.add_argument("--url", required=True)
    download.add_argument("--output", required=True)
    download.add_argument("--bytes", type=int)
    download.add_argument("--sha256")
    download.add_argument("--md5")
    download.add_argument("--retries", type=int, default=3)
    download.add_argument("--timeout", type=float, default=30.0)
    download.add_argument("--report")
    download.set_defaults(func=run_download)

    batch = subparsers.add_parser("batch", help="Download files from a CSV or JSON manifest")
    batch.add_argument("--manifest", required=True)
    batch.add_argument("--output-dir", required=True)
    batch.add_argument("--retries", type=int, default=3)
    batch.add_argument("--timeout", type=float, default=30.0)
    batch.add_argument("--report")
    batch.set_defaults(func=run_batch)

    verify = subparsers.add_parser("verify", help="Inventory existing files with SHA-256")
    verify.add_argument("--path", required=True)
    verify.add_argument("--report")
    verify.add_argument("--manifest-output")
    verify.set_defaults(func=run_verify)

    manifest = subparsers.add_parser("manifest", help="Create a SHA-256 inventory for existing files")
    manifest.add_argument("--path", required=True)
    manifest.add_argument("--report")
    manifest.add_argument("--manifest-output", required=True)
    manifest.set_defaults(func=run_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.func(args))
    except InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (json.JSONDecodeError, csv.Error) as exc:
        print(f"manifest error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        print("interrupted; partial files were retained", file=sys.stderr)
        return EXIT_INCOMPLETE


if __name__ == "__main__":
    raise SystemExit(main())
