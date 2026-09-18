import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "data_transfer.py"
SPEC = importlib.util.spec_from_file_location("data_transfer", SCRIPT)
DATA_TRANSFER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DATA_TRANSFER)


class DataHandler(BaseHTTPRequestHandler):
    payload = (b"verified-public-data\n" * 1024)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        self.send_header("ETag", '"test-etag-v1"')
        self.send_header("Last-Modified", "Tue, 11 Aug 2026 00:00:00 GMT")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        self.send_header("ETag", '"test-etag-v1"')
        self.send_header("Last-Modified", "Tue, 11 Aug 2026 00:00:00 GMT")
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, format, *args):
        return


class DownloadAndVerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DataHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/dataset.bin"
        cls.sha256 = hashlib.sha256(DataHandler.payload).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        cls.server.server_close()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args):
        arguments = list(map(str, args))
        if arguments and arguments[0] in {"download", "batch"}:
            arguments.insert(1, "--allow-private-network")
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_cli_public_only(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            capture_output=True,
            text=True,
            check=False,
        )

    def load_report(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_download_with_trusted_sha256_is_verified(self):
        output = self.root / "dataset.bin"
        report = self.root / "report.json"

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--sha256",
            self.sha256,
            "--bytes",
            len(DataHandler.payload),
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), DataHandler.payload)
        self.assertFalse(Path(str(output) + ".part").exists())
        item = self.load_report(report)["results"][0]
        self.assertEqual(item["status"], "downloaded")
        self.assertEqual(item["integrity_level"], "verified_sha256")
        self.assertEqual(item["actual_sha256"], self.sha256)

    def test_download_without_upstream_hash_records_local_baseline(self):
        output = self.root / "dataset.bin"
        report = self.root / "report.json"

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        item = self.load_report(report)["results"][0]
        self.assertEqual(item["integrity_level"], "local_baseline")
        self.assertEqual(item["actual_sha256"], self.sha256)
        self.assertIn("not an upstream integrity proof", item["integrity_note"])

    def test_report_path_cannot_overwrite_download_target(self):
        output = self.root / "dataset.bin"

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--report",
            output,
        )

        self.assertEqual(result.returncode, 64)
        self.assertFalse(output.exists())

    def test_mismatched_existing_file_is_quarantined_before_replacement(self):
        output = self.root / "dataset.bin"
        output.write_bytes(b"old-conflicting-data")
        report = self.root / "report.json"

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--sha256",
            self.sha256,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), DataHandler.payload)
        quarantined = list((self.root / ".download-quarantine").rglob("dataset.bin"))
        self.assertEqual(len(quarantined), 1)
        self.assertEqual(quarantined[0].read_bytes(), b"old-conflicting-data")
        item = self.load_report(report)["results"][0]
        self.assertEqual(Path(item["quarantined_existing"]), quarantined[0])

    def test_sha256_mismatch_cannot_be_overridden_by_matching_md5(self):
        output = self.root / "dataset.bin"
        output.write_bytes(DataHandler.payload)
        report = self.root / "report.json"
        matching_md5 = hashlib.md5(DataHandler.payload).hexdigest()

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--sha256",
            "0" * 64,
            "--md5",
            matching_md5,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())
        self.assertEqual(self.load_report(report)["results"][0]["status"], "integrity_failed")

    def test_size_only_existing_file_is_preserved_as_unverified_conflict(self):
        output = self.root / "dataset.bin"
        output.write_bytes(DataHandler.payload)
        report = self.root / "report.json"

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--bytes",
            len(DataHandler.payload),
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(output.read_bytes(), DataHandler.payload)
        self.assertFalse((self.root / ".download-quarantine").exists())
        self.assertEqual(self.load_report(report)["results"][0]["status"], "conflict")

    def test_wrong_expected_hash_rejects_download_and_preserves_invalid_bytes(self):
        output = self.root / "dataset.bin"
        report = self.root / "report.json"

        result = self.run_cli(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--sha256",
            "0" * 64,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(output.exists())
        rejected = list((self.root / ".download-quarantine").rglob("dataset.bin.part"))
        self.assertEqual(len(rejected), 1)
        item = self.load_report(report)["results"][0]
        self.assertEqual(item["status"], "integrity_failed")

    def test_short_transfer_retries_with_range_and_resumes(self):
        payload = DataHandler.payload

        class FlakyRangeHandler(BaseHTTPRequestHandler):
            get_count = 0
            range_headers = []

            def do_HEAD(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("ETag", '"resume-etag-v1"')
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

            def do_GET(self):
                type(self).get_count += 1
                range_header = self.headers.get("Range")
                type(self).range_headers.append(range_header)
                if type(self).get_count == 1:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("ETag", '"resume-etag-v1"')
                    self.end_headers()
                    self.wfile.write(payload[: len(payload) // 2])
                    self.wfile.flush()
                    self.connection.close()
                    return
                start = int(range_header.removeprefix("bytes=").removesuffix("-"))
                remaining = payload[start:]
                self.send_response(206)
                self.send_header("Content-Length", str(len(remaining)))
                self.send_header("Content-Range", f"bytes {start}-{len(payload) - 1}/{len(payload)}")
                self.send_header("ETag", '"resume-etag-v1"')
                self.end_headers()
                self.wfile.write(remaining)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), FlakyRangeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/resume.bin"
            output = self.root / "resume.bin"
            report = self.root / "resume-report.json"
            result = self.run_cli(
                "download",
                "--url",
                url,
                "--output",
                output,
                "--sha256",
                self.sha256,
                "--retries",
                3,
                "--report",
                report,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), payload)
        self.assertEqual(FlakyRangeHandler.get_count, 2)
        self.assertIsNone(FlakyRangeHandler.range_headers[0])
        self.assertTrue(FlakyRangeHandler.range_headers[1].startswith("bytes="))
        self.assertTrue(self.load_report(report)["results"][0]["resumed"])

    def test_head_disabled_short_get_retries_from_scratch(self):
        payload = DataHandler.payload

        class NoHeadHandler(BaseHTTPRequestHandler):
            get_count = 0

            def do_HEAD(self):
                self.send_error(405)

            def do_GET(self):
                type(self).get_count += 1
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if type(self).get_count == 1:
                    self.wfile.write(payload[: len(payload) // 2])
                    self.wfile.flush()
                    self.connection.close()
                else:
                    self.wfile.write(payload)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), NoHeadHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            output = self.root / "no-head.bin"
            report = self.root / "no-head-report.json"
            result = self.run_cli(
                "download",
                "--url",
                f"http://127.0.0.1:{server.server_port}/no-head.bin",
                "--output",
                output,
                "--retries",
                3,
                "--report",
                report,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(NoHeadHandler.get_count, 2)
        self.assertEqual(output.read_bytes(), payload)

    def test_truncated_chunked_response_retries_without_traceback(self):
        payload = DataHandler.payload

        class TruncatedChunkHandler(BaseHTTPRequestHandler):
            get_count = 0

            def do_HEAD(self):
                self.send_error(405)

            def do_GET(self):
                type(self).get_count += 1
                self.send_response(200)
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                if type(self).get_count == 1:
                    first = payload[:128]
                    self.wfile.write(f"{len(first):X}\r\n".encode("ascii"))
                    self.wfile.write(first + b"\r\n")
                    self.wfile.flush()
                    self.connection.close()
                else:
                    self.wfile.write(f"{len(payload):X}\r\n".encode("ascii"))
                    self.wfile.write(payload + b"\r\n0\r\n\r\n")

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), TruncatedChunkHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            output = self.root / "chunked.bin"
            result = self.run_cli(
                "download",
                "--url",
                f"http://127.0.0.1:{server.server_port}/chunked.bin",
                "--output",
                output,
                "--sha256",
                self.sha256,
                "--retries",
                2,
                "--report",
                self.root / "chunked-report.json",
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(TruncatedChunkHandler.get_count, 2)
        self.assertEqual(output.read_bytes(), payload)

    def test_resume_requires_strong_identity_metadata(self):
        current = {"etag": None, "last_modified": None, "content_length": 100}
        previous = {"url": self.url, **current}
        self.assertFalse(DATA_TRANSFER.metadata_matches(previous, current, self.url))

        weak_current = {"etag": 'W/"weak"', "last_modified": None, "content_length": 100}
        weak_previous = {"url": self.url, **weak_current}
        self.assertFalse(DATA_TRANSFER.metadata_matches(weak_previous, weak_current, self.url))

    def test_malformed_content_range_forces_clean_restart(self):
        payload = DataHandler.payload

        class MalformedRangeHandler(BaseHTTPRequestHandler):
            range_headers = []

            def do_HEAD(self):
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("ETag", '"range-etag-v1"')
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

            def do_GET(self):
                range_header = self.headers.get("Range")
                type(self).range_headers.append(range_header)
                if range_header:
                    start = len(payload) // 2
                    remaining = payload[start:]
                    self.send_response(206)
                    self.send_header("Content-Length", str(len(remaining)))
                    self.send_header("Content-Range", f"bytes 0-{len(remaining) - 1}/{len(payload)}")
                    self.send_header("ETag", '"range-etag-v1"')
                    self.end_headers()
                    self.wfile.write(remaining)
                else:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("ETag", '"range-etag-v1"')
                    self.end_headers()
                    self.wfile.write(payload)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), MalformedRangeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/range.bin"
            output = self.root / "range.bin"
            part = Path(str(output) + ".part")
            part.write_bytes(payload[: len(payload) // 2])
            Path(str(part) + ".meta.json").write_text(
                json.dumps(
                    {
                        "url": url,
                        "final_url": url,
                        "etag": '"range-etag-v1"',
                        "last_modified": None,
                        "content_length": len(payload),
                    }
                ),
                encoding="utf-8",
            )
            report = self.root / "range-report.json"
            result = self.run_cli(
                "download",
                "--url",
                url,
                "--output",
                output,
                "--sha256",
                self.sha256,
                "--retries",
                3,
                "--report",
                report,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(MalformedRangeHandler.range_headers[0], f"bytes={len(payload) // 2}-")
        self.assertIsNone(MalformedRangeHandler.range_headers[1])
        self.assertEqual(output.read_bytes(), payload)

    def test_resume_with_unknown_total_forces_clean_restart(self):
        payload = DataHandler.payload

        class UnknownTotalHandler(BaseHTTPRequestHandler):
            range_headers = []

            def do_HEAD(self):
                self.send_response(200)
                self.send_header("ETag", '"unknown-total-etag"')
                self.end_headers()

            def do_GET(self):
                range_header = self.headers.get("Range")
                type(self).range_headers.append(range_header)
                if range_header:
                    start = len(payload) // 2
                    remaining = payload[start:]
                    self.send_response(206)
                    self.send_header("Content-Length", str(len(remaining)))
                    self.send_header(
                        "Content-Range", f"bytes {start}-{len(payload) - 1}/*"
                    )
                    self.send_header("ETag", '"unknown-total-etag"')
                    self.end_headers()
                    self.wfile.write(remaining)
                else:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(payload)))
                    self.send_header("ETag", '"unknown-total-etag"')
                    self.end_headers()
                    self.wfile.write(payload)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), UnknownTotalHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/unknown-total.bin"
            output = self.root / "unknown-total.bin"
            part = Path(str(output) + ".part")
            part.write_bytes(payload[: len(payload) // 2])
            Path(str(part) + ".meta.json").write_text(
                json.dumps(
                    {
                        "url": url,
                        "final_url": url,
                        "etag": '"unknown-total-etag"',
                        "last_modified": None,
                        "content_length": None,
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "download",
                "--url",
                url,
                "--output",
                output,
                "--sha256",
                self.sha256,
                "--retries",
                3,
                "--report",
                self.root / "unknown-total-report.json",
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(UnknownTotalHandler.range_headers), 2)
        self.assertTrue(UnknownTotalHandler.range_headers[0].startswith("bytes="))
        self.assertIsNone(UnknownTotalHandler.range_headers[1])
        self.assertEqual(output.read_bytes(), payload)

    def test_private_network_url_is_rejected_by_default(self):
        output = self.root / "private.bin"
        result = self.run_cli_public_only(
            "download",
            "--url",
            self.url,
            "--output",
            output,
            "--report",
            self.root / "private-report.json",
        )
        self.assertEqual(result.returncode, 64)
        self.assertFalse(output.exists())

    def test_http_connection_pins_validated_ip_before_request(self):
        self.assertTrue(hasattr(DATA_TRANSFER, "PublicHTTPConnection"))
        fake_socket = object()
        with mock.patch.object(
            DATA_TRANSFER, "resolve_public_addresses", return_value=["93.184.216.34"]
        ), mock.patch.object(
            DATA_TRANSFER.socket, "create_connection", return_value=fake_socket
        ) as create_connection:
            connection = DATA_TRANSFER.PublicHTTPConnection(
                "example.com", timeout=5, allow_private_network=False
            )
            connection.connect()

        self.assertIs(connection.sock, fake_socket)
        self.assertEqual(create_connection.call_args.args[0], ("93.184.216.34", 80))

    def test_ftp_request_uses_validated_literal_ip(self):
        self.assertTrue(hasattr(DATA_TRANSFER, "pin_ftp_request"))
        request = DATA_TRANSFER.Request(
            "ftp://downloads.example.org/pub/data.bin",
            headers={"User-Agent": "test-agent"},
        )
        with mock.patch.object(
            DATA_TRANSFER, "resolve_public_addresses", return_value=["93.184.216.34"]
        ):
            pinned = DATA_TRANSFER.pin_ftp_request(request)

        self.assertEqual(pinned.full_url, "ftp://93.184.216.34/pub/data.bin")
        self.assertEqual(pinned.get_header("User-agent"), "test-agent")

    def test_https_handler_uses_runtime_supported_connection_arguments(self):
        handler = DATA_TRANSFER.PublicHTTPSHandler(allow_private_network=False)
        captured = {}

        def capture(factory, request):
            captured["connection"] = factory("example.com", timeout=5)
            return "captured"

        with mock.patch.object(handler, "do_open", side_effect=capture):
            result = handler.https_open(DATA_TRANSFER.Request("https://example.com/"))

        self.assertEqual(result, "captured")
        self.assertIsInstance(captured["connection"], DATA_TRANSFER.PublicHTTPSConnection)

    def test_http_404_writes_failure_report_and_returns_incomplete(self):
        class NotFoundHandler(BaseHTTPRequestHandler):
            get_count = 0

            def do_HEAD(self):
                self.send_error(404)

            def do_GET(self):
                type(self).get_count += 1
                self.send_error(404)

            def log_message(self, format, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), NotFoundHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            report = self.root / "404-report.json"
            result = self.run_cli(
                "download",
                "--url",
                f"http://127.0.0.1:{server.server_port}/missing.bin",
                "--output",
                self.root / "missing.bin",
                "--retries",
                2,
                "--report",
                report,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(result.returncode, 2)
        self.assertEqual(NotFoundHandler.get_count, 2)
        self.assertNotIn("Traceback", result.stderr)
        item = self.load_report(report)["results"][0]
        self.assertEqual(item["status"], "error")
        self.assertEqual(item["attempts"], 2)

    def test_missing_manifest_is_usage_error_without_traceback(self):
        result = self.run_cli(
            "batch",
            "--manifest",
            self.root / "missing.csv",
            "--output-dir",
            self.root / "downloads",
            "--report",
            self.root / "missing-report.json",
        )
        self.assertEqual(result.returncode, 64)
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_url_port_is_usage_error_without_traceback(self):
        result = self.run_cli_public_only(
            "download",
            "--url",
            "https://example.com:notaport/data.bin",
            "--output",
            self.root / "bad-port.bin",
            "--report",
            self.root / "bad-port-report.json",
        )
        self.assertEqual(result.returncode, 64)
        self.assertNotIn("Traceback", result.stderr)

    def test_batch_manifest_downloads_safe_relative_paths(self):
        manifest = self.root / "manifest.csv"
        output_dir = self.root / "downloads"
        report = self.root / "batch-report.json"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["relative_path", "url", "bytes", "sha256"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "relative_path": "nested/dataset.bin",
                    "url": self.url,
                    "bytes": len(DataHandler.payload),
                    "sha256": self.sha256,
                }
            )

        result = self.run_cli(
            "batch",
            "--manifest",
            manifest,
            "--output-dir",
            output_dir,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((output_dir / "nested" / "dataset.bin").read_bytes(), DataHandler.payload)
        self.assertEqual(self.load_report(report)["summary"]["verified"], 1)

    def test_batch_manifest_rejects_parent_path_escape(self):
        manifest = self.root / "manifest.csv"
        output_dir = self.root / "downloads"
        report = self.root / "batch-report.json"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["relative_path", "url"])
            writer.writeheader()
            writer.writerow({"relative_path": "../escape.bin", "url": self.url})

        result = self.run_cli(
            "batch",
            "--manifest",
            manifest,
            "--output-dir",
            output_dir,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 64)
        self.assertFalse((self.root / "escape.bin").exists())

    def test_batch_report_path_cannot_overwrite_manifest_target(self):
        manifest = self.root / "manifest.csv"
        output_dir = self.root / "downloads"
        report = output_dir / "dataset.bin"
        with manifest.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["relative_path", "url"])
            writer.writeheader()
            writer.writerow({"relative_path": "dataset.bin", "url": self.url})

        result = self.run_cli(
            "batch",
            "--manifest",
            manifest,
            "--output-dir",
            output_dir,
            "--report",
            report,
        )

        self.assertEqual(result.returncode, 64)
        self.assertFalse(report.exists())

    def test_verify_directory_creates_sha256_inventory(self):
        data_dir = self.root / "existing"
        data_dir.mkdir()
        (data_dir / "a.txt").write_bytes(b"alpha")
        (data_dir / "b.txt").write_bytes(b"beta")
        report = self.root / "verify-report.json"
        manifest = self.root / "inventory.csv"

        result = self.run_cli(
            "verify",
            "--path",
            data_dir,
            "--report",
            report,
            "--manifest-output",
            manifest,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = self.load_report(report)
        self.assertEqual(payload["summary"]["local_baseline"], 2)
        with manifest.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([row["relative_path"] for row in rows], ["a.txt", "b.txt"])
        self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))

    def test_verify_outputs_cannot_overwrite_inventoried_files(self):
        data_dir = self.root / "existing"
        data_dir.mkdir()
        source = data_dir / "a.txt"
        source.write_bytes(b"alpha")
        report = self.root / "verify-report.json"

        result = self.run_cli(
            "verify",
            "--path",
            data_dir,
            "--report",
            report,
            "--manifest-output",
            source,
        )

        self.assertEqual(result.returncode, 64)
        self.assertEqual(source.read_bytes(), b"alpha")
        self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
