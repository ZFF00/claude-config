# Data Download Integrity Policy

## Scope

The core supports public anonymous HTTP, HTTPS, and FTP file URLs. Authentication, browser sessions, cookies, signed-in portals, API tokens, cloud credentials, torrents, peer-to-peer sources, and proprietary sync providers are outside the first version.

## Integrity Levels

| Level | Evidence | Permitted claim |
|---|---|---|
| `verified_sha256` | Local SHA-256 matches a trusted publisher or manifest SHA-256 | Cryptographically verified against the stated source |
| `verified_md5` | Local MD5 matches a trusted publisher or manifest MD5 | Legacy checksum matched; collision resistance is weak |
| `local_baseline` | No trusted checksum; local SHA-256 recorded after transfer and available size checks | Locally inventoried, not upstream-verified |
| `unverified` | Transfer incomplete, source changed, or existing file cannot be identified | No integrity claim |
| `failed` | Expected bytes or trusted checksum differs | Integrity failure |

An ETag is transport metadata, not automatically a cryptographic hash. Never interpret multipart S3 ETags as MD5.

## Preflight

1. Resolve the destination to an absolute path under the user-selected directory or current workspace.
2. Estimate expected bytes and confirm adequate free space for the final file plus `.part` and possible quarantined conflicts.
3. Record the requested URL, final redirected URL, dataset version, expected bytes, checksum value, checksum source, and access time when available.
4. Reject embedded usernames/passwords and unsupported schemes before creating output files.
5. Validate every manifest relative path before downloading any row.
6. Reject duplicate targets and any collision among data, `.part`, metadata, report, manifest input, or inventory output paths before network access.
7. Resolve hosts to globally routable addresses by default, revalidate redirects, disable environment proxies, and connect to the validated literal address while retaining the original HTTPS hostname for certificate checks. Reject loopback, link-local, private, reserved, and local hostnames.

## Transfer And Resume

- Write content to `<target>.part` and resume only with matching metadata in `<target>.part.meta.json`.
- A strong ETag match is sufficient for resume identity. Without it, require matching URL, Last-Modified, and Content-Length when those values are available.
- If a server ignores Range, restart the `.part` file instead of appending duplicate bytes.
- Default to three attempts with bounded exponential delays. The CLI accepts 1-20 attempts and never retries forever.
- Preserve a partial file after network exhaustion so a later invocation can resume it.

## Existing And Rejected Files

- If an existing final file matches trusted bytes and checksum, report `already_valid` and do not download it again.
- If trusted evidence proves an existing final file differs, move it beneath a sibling `.download-quarantine/<UTC timestamp>/` directory before downloading a replacement.
- If no trusted expectation exists, preserve the existing file and report a conflict instead of replacing it.
- Move a fully downloaded but mismatched `.part` file to quarantine. Never delete it or give it the final name automatically.

## Reports And Exit Codes

Every run writes an atomic JSON report with source, final URL, destination, attempts, resume state, expected and actual bytes, hashes, integrity level, quarantine paths, errors, and aggregate counts.

| Exit | Meaning |
|---:|---|
| `0` | Requested operation completed; all items have verified or explicitly recorded local-baseline evidence |
| `2` | Network, conflict, or integrity failure left the operation incomplete |
| `64` | URL, manifest, checksum, path, or CLI input was invalid |
