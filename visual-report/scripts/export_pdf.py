#!/usr/bin/env python3
"""
Export HTML visual reports to PDF with print-specific layout reflow.

Usage:
    python export_pdf.py report.html output.pdf
    python export_pdf.py report.html output.pdf --mode report
    python export_pdf.py report.html output.pdf --mode slides

This exporter uses local Chrome/Chromium headless rendering instead of relying
on manual browser print dialogs. It injects print CSS into a temporary HTML
copy so the on-screen layout can stay interactive while the PDF uses a more
stable print layout.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SLIDE_TAG_RE = re.compile(
    r"<(?:section|div)\b[^>]*class=(?:\"[^\"]*\b(?:ppt-slide|slide)\b[^\"]*\"|'[^']*\b(?:ppt-slide|slide)\b[^']*')",
    re.IGNORECASE,
)

REPORT_PRINT_CSS = """
@media print {
  @page { size: A4; margin: 12mm; }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    min-height: auto !important;
    height: auto !important;
  }
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .no-print, .slide-nav, .slide-counter {
    display: none !important;
  }
  .avoid-break, .glass, .ppt-panel, .ppt-metric-card, table, img, canvas, svg, section, article, figure {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .print-stack,
  .grid,
  .ppt-two-col,
  .ppt-metric-grid,
  [class*="grid-cols-"],
  [class*="lg:grid-cols"],
  [class*="md:grid-cols"],
  [class*="xl:grid-cols"] {
    display: block !important;
  }
  .print-stack > *,
  .grid > *,
  .ppt-two-col > *,
  .ppt-metric-grid > *,
  [class*="grid-cols-"] > * {
    width: 100% !important;
    max-width: none !important;
    margin-bottom: 10mm !important;
  }
  .flex,
  [class*="flex-row"],
  [class*="flex-col"] {
    display: block !important;
  }
  [class*="max-w-"] {
    max-width: none !important;
  }
  table {
    width: 100% !important;
    border-collapse: collapse !important;
  }
  thead {
    display: table-header-group !important;
  }
  tr, td, th {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  canvas, img, svg {
    max-width: 100% !important;
    height: auto !important;
  }
  .pdf-page-break {
    break-before: page !important;
    page-break-before: always !important;
  }
}
"""

SLIDES_PRINT_CSS = """
@media print {
  @page { size: 13.333in 7.5in; margin: 0; }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    width: 13.333in !important;
    overflow: visible !important;
  }
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  .slide, .ppt-slide {
    display: block !important;
    visibility: visible !important;
    width: 13.333in !important;
    height: 7.5in !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    break-after: page !important;
    page-break-after: always !important;
    overflow: hidden !important;
    position: relative !important;
  }
  .slide:last-of-type, .ppt-slide:last-of-type {
    break-after: auto !important;
    page-break-after: auto !important;
  }
  .slide-nav, .slide-counter, .no-print {
    display: none !important;
  }
}
"""


def detect_mode(html: str, requested_mode: str) -> str:
    if requested_mode != "auto":
        return requested_mode
    return "slides" if SLIDE_TAG_RE.search(html) else "report"


def find_chrome(explicit_path: str | None) -> str:
    candidates = [
        explicit_path,
        os.environ.get("VISUAL_REPORT_CHROME"),
        os.environ.get("CHROME_PATH"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chrome"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)

    raise FileNotFoundError(
        "Chrome/Chromium not found. Set VISUAL_REPORT_CHROME or install Google Chrome."
    )


def inject_print_style(html: str, mode: str) -> str:
    css = SLIDES_PRINT_CSS if mode == "slides" else REPORT_PRINT_CSS
    style_tag = f"\n<style id=\"visual-report-pdf-export\">\n{css}\n</style>\n"

    if "</head>" in html:
        return html.replace("</head>", style_tag + "</head>", 1)
    if "<body" in html:
        return style_tag + html
    return f"<html><head>{style_tag}</head><body>{html}</body></html>"


def write_temp_html(source_html: str, output_dir: Path, mode: str) -> Path:
    rendered = inject_print_style(source_html, mode)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        prefix="visual-report-pdf-",
        dir=output_dir,
        delete=False,
        encoding="utf-8",
    ) as handle:
        handle.write(rendered)
        return Path(handle.name)


def build_chrome_command(chrome_path: str, input_html: Path, output_pdf: Path) -> list[str]:
    return [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=12000",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf}",
        input_html.resolve().as_uri(),
    ]


def export_pdf(input_html: Path, output_pdf: Path, mode: str, chrome_path: str | None) -> None:
    source = input_html.read_text(encoding="utf-8")
    actual_mode = detect_mode(source, mode)
    chrome = find_chrome(chrome_path)
    temp_html = write_temp_html(source, output_pdf.parent, actual_mode)

    try:
        command = build_chrome_command(chrome, temp_html, output_pdf)
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Chrome PDF export failed")

        if not output_pdf.exists() or output_pdf.stat().st_size == 0:
            raise RuntimeError("Chrome reported success, but the PDF file was not created.")

        print(f"PDF saved to: {output_pdf}")
    finally:
        try:
            temp_html.unlink(missing_ok=True)
        except OSError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Export HTML visual report to PDF with print layout reflow.")
    parser.add_argument("input_html", help="Path to HTML file")
    parser.add_argument("output_pdf", help="Path to output PDF file")
    parser.add_argument(
        "--mode",
        choices=("auto", "report", "slides"),
        default="auto",
        help="PDF layout mode. auto detects slide-style HTML and defaults to report otherwise.",
    )
    parser.add_argument(
        "--chrome-path",
        default=None,
        help="Optional explicit Chrome/Chromium binary path.",
    )

    args = parser.parse_args()

    input_html = Path(args.input_html).expanduser().resolve()
    output_pdf = Path(args.output_pdf).expanduser().resolve()

    if not input_html.exists():
        print(f"Error: File not found: {input_html}")
        sys.exit(1)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    try:
        export_pdf(input_html, output_pdf, args.mode, args.chrome_path)
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
