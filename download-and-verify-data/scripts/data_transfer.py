#!/usr/bin/env python3
"""Download public data and produce explicit integrity evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import ipaddress
import json
import os
import re
import shutil
import socket
import sys
import time
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException, HTTPSConnection
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import (
    HTTPHandler,
    HTTPRedirectHandler,
    HTTPSHandler,
    ProxyHandler,
    Request,
    build_opener,
)


EXIT_OK = 0
EXIT_INCOMPLETE = 2
EXIT_USAGE = 64
CHUNK_SIZE = 1024 * 1024


class InputError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InputError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_public_url(value: str, allow_private_network: bool = False) -> str:
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https", "ftp"}:
        raise InputError(f"unsupported URL scheme: {parsed.scheme or '(missing)'}")
    if not parsed.hostname:
        raise InputError("URL must include a host")
    if parsed.username is not None or parsed.password is not None:
        raise InputError("credential-bearing URLs are not allowed")
    try:
        port = parsed.port
    except ValueError as exc:
        raise InputError("URL contains an invalid port") from exc
    if not allow_private_network:
        hostname = parsed.hostname.rstrip(".").lower()
        if hostname == "localhost" or hostname.endswith(".localhost"):
            raise InputError("local and private network URLs are not allowed")
        resolve_public_addresses(hostname, port)
    return value


def resolve_public_addresses(hostname: str, port: int | None) -> list[str]:
    try:
        literal = ipaddress.ip_address(hostname)
        candidates = [literal]
    except ValueError:
        try:
            candidates = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
            ]
        except socket.gaierror as exc:
            raise InputError(f"URL host could not be resolved: {hostname}") from exc
    addresses = list(dict.fromkeys(candidates))
    if not addresses or any(not address.is_global for address in addresses):
        raise InputError("local, private, reserved, and non-global network URLs are not allowed")
    return [str(address) for address in addresses]


def create_public_socket(connection) -> socket.socket:
    addresses = resolve_public_addresses(connection.host, connection.port)
    last_error: OSError | None = None
    for address in addresses:
        try:
            return socket.create_connection(
                (address, connection.port), connection.timeout, connection.source_address
            )
        except OSError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


class PublicHTTPConnection(HTTPConnection):
    def __init__(self, host, *, allow_private_network: bool, **kwargs):
        self.allow_private_network = allow_private_network
        super().__init__(host, **kwargs)

    def connect(self):
        if self.allow_private_network:
            return super().connect()
        self.sock = create_public_socket(self)
        if self._tunnel_host:
            self._tunnel()


class PublicHTTPSConnection(HTTPSConnection):
    def __init__(self, host, *, allow_private_network: bool, **kwargs):
        self.allow_private_network = allow_private_network
        super().__init__(host, **kwargs)

    def connect(self):
        if self.allow_private_network:
            return super().connect()
        self.sock = create_public_socket(self)
        server_hostname = self.host
        if self._tunnel_host:
            self._tunnel()
            server_hostname = self._tunnel_host
        self.sock = self._context.wrap_socket(self.sock, server_hostname=server_hostname)


class PublicHTTPHandler(HTTPHandler):
    def __init__(self, allow_private_network: bool):
        super().__init__()
        self.allow_private_network = allow_private_network

    def http_open(self, req):
        def factory(host, **kwargs):
            return PublicHTTPConnection(
                host, allow_private_network=self.allow_private_network, **kwargs
            )

        return self.do_open(factory, req)


class PublicHTTPSHandler(HTTPSHandler):
    def __init__(self, allow_private_network: bool):
        super().__init__()
        self.allow_private_network = allow_private_network

    def https_open(self, req):
        def factory(host, **kwargs):
            return PublicHTTPSConnection(
                host,
                allow_private_network=self.allow_private_network,
                context=self._context,
                **kwargs,
            )

        return self.do_open(factory, req)


def pin_ftp_request(request: Request) -> Request:
    parsed = urlsplit(request.full_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise InputError("URL contains an invalid port") from exc
    address = resolve_public_addresses(parsed.hostname, port or 21)[0]
    literal_host = f"[{address}]" if ":" in address else address
    netloc = f"{literal_host}:{port}" if port is not None else literal_host
    pinned_url = urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )
    headers = dict(request.header_items())
    headers.update(request.unredirected_hdrs)
    return Request(
        pinned_url,
        data=request.data,
        headers=headers,
        unverifiable=request.unverifiable,
        origin_req_host=request.origin_req_host,
        method=request.get_method(),
    )


class SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allow_private_network: bool):
        super().__init__()
        self.allow_private_network = allow_private_network

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl, self.allow_private_network)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_url(request: Request, timeout: float, allow_private_network: bool):
    if urlsplit(request.full_url).scheme.lower() == "ftp" and not allow_private_network:
        request = pin_ftp_request(request)
    opener = build_opener(
        ProxyHandler({}),
        PublicHTTPHandler(allow_private_network),
        PublicHTTPSHandler(allow_private_network),
        SafeRedirectHandler(allow_private_network),
    )
    return opener.open(request, timeout=timeout)


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


def probe_url(url: str, timeout: float, allow_private_network: bool) -> dict[str, Any]:
    request = Request(url, method="HEAD", headers={"User-Agent": "download-and-verify-data/1"})
    try:
        with open_url(request, timeout, allow_private_network) as response:
            headers = response.headers
            return {
                "final_url": response.geturl(),
                "etag": headers.get("ETag"),
                "last_modified": headers.get("Last-Modified"),
                "content_length": parse_expected_bytes(headers.get("Content-Length")),
                "accept_ranges": headers.get("Accept-Ranges"),
            }
    except (HTTPError, URLError, OSError):
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
    etag = current.get("etag")
    if etag and not str(etag).strip().startswith("W/"):
        return previous.get("etag") == current.get("etag")
    return bool(current.get("last_modified") and current.get("content_length") is not None) and all(
        previous.get(key) == current.get(key) for key in ("last_modified", "content_length")
    )


def validate_partial_response(
    response,
    offset: int,
    remote: dict[str, Any],
    response_length: int | None,
) -> int | None:
    content_range = response.headers.get("Content-Range", "")
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+|\*)", content_range.strip())
    if not match:
        raise OSError("resume response is missing a valid Content-Range")
    start, end = int(match.group(1)), int(match.group(2))
    total = None if match.group(3) == "*" else int(match.group(3))
    if total is None:
        raise OSError("resume response must declare the total Content-Range length")
    if start != offset or end < start:
        raise OSError("resume Content-Range does not match the requested offset")
    if response_length is not None and response_length != end - start + 1:
        raise OSError("resume Content-Length does not match Content-Range")
    if remote.get("content_length") is not None and total != remote.get("content_length"):
        raise OSError("resume total length changed")
    etag = remote.get("etag")
    if etag and not str(etag).strip().startswith("W/"):
        if response.headers.get("ETag") != etag:
            raise OSError("resume ETag changed")
    elif remote.get("last_modified"):
        if response.headers.get("Last-Modified") != remote.get("last_modified"):
            raise OSError("resume Last-Modified changed")
    return total


def download_attempt(
    url: str,
    part: Path,
    metadata_path: Path,
    remote: dict[str, Any],
    timeout: float,
    allow_private_network: bool,
) -> dict[str, Any]:
    previous = read_metadata(metadata_path)
    offset = part.stat().st_size if part.exists() and metadata_matches(previous, remote, url) else 0
    if part.exists() and offset == 0:
        quarantine(part)
    headers = {"User-Agent": "download-and-verify-data/1"}
    if offset:
        headers["Range"] = f"bytes={offset}-"
        if remote.get("etag") and not str(remote["etag"]).strip().startswith("W/"):
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
    with open_url(request, timeout, allow_private_network) as response:
        status = getattr(response, "status", None)
        resumed = bool(offset and status == 206)
        response_length = parse_expected_bytes(response.headers.get("Content-Length"))
        expected_total = response_length if not resumed else None
        if resumed:
            try:
                expected_total = validate_partial_response(response, offset, remote, response_length)
            except OSError:
                if part.exists():
                    quarantine(part)
                metadata_path.unlink(missing_ok=True)
                raise
        mode = "ab" if resumed else "wb"
        if offset and not resumed:
            offset = 0
        with part.open(mode) as handle:
            while chunk := response.read(CHUNK_SIZE):
                handle.write(chunk)
        final_url = response.geturl()
    return {
        "resumed": resumed,
        "resume_offset": offset if resumed else 0,
        "response_length": response_length,
        "expected_total": expected_total,
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
    allow_private_network: bool = False,
) -> dict[str, Any]:
    validate_public_url(url, allow_private_network)
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
        sha_matches = not expected_sha256 or existing["sha256"] == expected_sha256
        md5_matches = not expected_md5 or existing.get("md5") == expected_md5
        size_matches = expected_bytes is None or existing["bytes"] == expected_bytes
        checksums_supplied = bool(expected_sha256 or expected_md5)
        if checksums_supplied and size_matches and sha_matches and md5_matches:
            result.update(
                {
                    "status": "already_valid",
                    "integrity_level": "verified_sha256" if expected_sha256 else "verified_md5",
                    "integrity_note": "Existing file matches the trusted upstream checksum.",
                    "actual_bytes": existing["bytes"],
                    "actual_sha256": existing["sha256"],
                    "actual_md5": existing.get("md5"),
                }
            )
            return result
        proven_mismatch = (
            (expected_bytes is not None and not size_matches)
            or (expected_sha256 is not None and not sha_matches)
            or (expected_md5 is not None and not md5_matches)
        )
        if proven_mismatch:
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

    remote = probe_url(url, timeout, allow_private_network)
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
            transfer = download_attempt(
                url, part, metadata_path, remote, timeout, allow_private_network
            )
            expected_transfer_length = transfer.get("expected_total") or remote.get("content_length")
            if expected_transfer_length is not None and part.stat().st_size < expected_transfer_length:
                raise OSError(
                    f"short transfer: expected {expected_transfer_length} bytes, got {part.stat().st_size}"
                )
            last_error = None
            break
        except (HTTPError, HTTPException, URLError, TimeoutError, OSError) as exc:
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


def load_manifest(path: Path, allow_private_network: bool = False) -> list[dict[str, Any]]:
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
        url = validate_public_url(str(row.get("url", "")), allow_private_network)
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


def transfer_sidecar_paths(target: Path) -> set[Path]:
    return {
        target,
        Path(str(target) + ".part"),
        Path(str(target) + ".part.meta.json"),
    }


def run_download(args: argparse.Namespace) -> int:
    started_at = utc_now()
    output = Path(args.output).resolve()
    report_path = (
        Path(args.report).resolve()
        if args.report
        else default_report_path(output.parent, "download").resolve()
    )
    if report_path in transfer_sidecar_paths(output):
        raise InputError("report path must differ from the target and its transfer sidecars")
    result = download_one(
        args.url,
        output,
        expected_bytes=args.bytes,
        expected_sha256=args.sha256,
        expected_md5=args.md5,
        retries=args.retries,
        timeout=args.timeout,
        allow_private_network=args.allow_private_network,
    )
    report = make_report("download", started_at, [result])
    atomic_json_write(report_path, report)
    print(json.dumps({"report": str(report_path.resolve()), "summary": report["summary"]}))
    return EXIT_INCOMPLETE if report["summary"]["failed"] else EXIT_OK


def run_batch(args: argparse.Namespace) -> int:
    started_at = utc_now()
    manifest_path = Path(args.manifest).resolve()
    manifest = load_manifest(manifest_path, args.allow_private_network)
    output_dir = Path(args.output_dir).resolve()
    target_paths = [(output_dir / row["relative_path"]).resolve() for row in manifest]
    if any(not target.is_relative_to(output_dir) for target in target_paths):
        raise InputError("a manifest target resolves outside output-dir")
    if len(set(target_paths)) != len(target_paths):
        raise InputError("manifest contains duplicate destination paths")
    report_path = (
        Path(args.report).resolve()
        if args.report
        else default_report_path(output_dir, "batch").resolve()
    )
    reserved = {manifest_path}
    for target in target_paths:
        reserved.update(transfer_sidecar_paths(target))
    if report_path in reserved:
        raise InputError("report path conflicts with the manifest or a transfer target")
    results = []
    for row, target in zip(manifest, target_paths):
        results.append(
            download_one(
                row["url"],
                target,
                expected_bytes=row["bytes"],
                expected_sha256=row["sha256"],
                expected_md5=row["md5"],
                retries=args.retries,
                timeout=args.timeout,
                allow_private_network=args.allow_private_network,
            )
        )
        results[-1]["relative_path"] = row["relative_path"].as_posix()
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
    report_path = (
        Path(args.report).resolve()
        if args.report
        else default_report_path(root.parent, "verify").resolve()
    )
    manifest_output = Path(args.manifest_output).resolve() if args.manifest_output else None
    existing_files = {item.resolve() for item in files}
    if report_path in existing_files:
        raise InputError("report path would overwrite an inventoried file")
    if manifest_output in existing_files:
        raise InputError("manifest output would overwrite an inventoried file")
    if manifest_output is not None and manifest_output == report_path:
        raise InputError("report and manifest output paths must differ")
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
    report = make_report("verify", started_at, results)
    atomic_json_write(report_path, report)
    if manifest_output is not None:
        write_inventory(manifest_output, results)
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
    download.add_argument("--allow-private-network", action="store_true", help=argparse.SUPPRESS)
    download.set_defaults(func=run_download)

    batch = subparsers.add_parser("batch", help="Download files from a CSV or JSON manifest")
    batch.add_argument("--manifest", required=True)
    batch.add_argument("--output-dir", required=True)
    batch.add_argument("--retries", type=int, default=3)
    batch.add_argument("--timeout", type=float, default=30.0)
    batch.add_argument("--report")
    batch.add_argument("--allow-private-network", action="store_true", help=argparse.SUPPRESS)
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
    except (FileNotFoundError, PermissionError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except OSError as exc:
        print(f"operational error: {exc}", file=sys.stderr)
        return EXIT_INCOMPLETE
    except KeyboardInterrupt:
        print("interrupted; partial files were retained", file=sys.stderr)
        return EXIT_INCOMPLETE


if __name__ == "__main__":
    raise SystemExit(main())
