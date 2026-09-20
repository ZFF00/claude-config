#!/usr/bin/env python3
"""Collect Claude Code CLI session activity for one local calendar day.

Reads session JSONL transcripts under ~/.claude/projects/ and emits
structured JSON evidence for daily reports.

Designed for non-interactive Agent execution:
- No prompts; everything via CLI args.
- Structured output (JSON) to stdout; diagnostics to stderr.
- Exit 0 with empty sessions list when nothing matches; exit 2 on setup error.
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def text_of(content) -> str:
    """Flatten a message content field (str or list of blocks) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def tool_names(content) -> list[str]:
    names = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                names.append(block.get("name", "?"))
    return names


def collect_file(path: Path, start: datetime, end: datetime, snippet_chars: int) -> dict | None:
    session = {
        "session_id": path.stem,
        "project": path.parent.name,
        "first_ts": None,
        "last_ts": None,
        "event_count": 0,
        "user_messages": [],
        "assistant_snippets": [],
        "tool_calls": Counter(),
    }
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = parse_ts(ev.get("timestamp", ""))
                if ts is None or not (start <= ts < end):
                    continue
                session["event_count"] += 1
                iso = ts.isoformat()
                if session["first_ts"] is None:
                    session["first_ts"] = iso
                session["last_ts"] = iso
                if ev.get("isSidechain"):
                    continue
                msg = ev.get("message") or {}
                role = msg.get("role")
                if ev.get("type") == "user" and role == "user":
                    text = text_of(msg.get("content")).strip()
                    # skip tool_result-only user events (no visible text)
                    if text and not text.startswith("<"):
                        session["user_messages"].append(text[:snippet_chars])
                elif ev.get("type") == "assistant" and role == "assistant":
                    for name in tool_names(msg.get("content")):
                        session["tool_calls"][name] += 1
                    text = text_of(msg.get("content")).strip()
                    if text:
                        session["assistant_snippets"].append(text[:snippet_chars])
    except OSError as exc:
        print(f"skip {path}: {exc}", file=sys.stderr)
        return None
    if session["event_count"] == 0:
        return None
    session["tool_calls"] = dict(session["tool_calls"].most_common())
    # keep output bounded: first 10 user messages, last 5 assistant snippets
    session["user_messages"] = session["user_messages"][:10]
    session["assistant_snippets"] = session["assistant_snippets"][-5:]
    return session


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Claude Code session activity for a local day.")
    parser.add_argument("--date", required=True, help="Target local date, YYYY-MM-DD")
    parser.add_argument("--utc-offset", default="+08:00", help="Local timezone UTC offset (default +08:00, Asia/Shanghai)")
    parser.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"), help="Claude projects dir")
    parser.add_argument("--snippet-chars", type=int, default=400, help="Max chars per message snippet")
    args = parser.parse_args()

    try:
        day = datetime.strptime(args.date, "%Y-%m-%d")
        sign = 1 if args.utc_offset.startswith("+") else -1
        hh, mm = args.utc_offset[1:].split(":")
        tz = timezone(sign * timedelta(hours=int(hh), minutes=int(mm)))
    except ValueError as exc:
        print(f"bad --date or --utc-offset: {exc}", file=sys.stderr)
        sys.exit(3)

    start = day.replace(tzinfo=tz)
    end = start + timedelta(days=1)

    root = Path(args.projects_dir)
    if not root.is_dir():
        print(f"projects dir not found: {root}", file=sys.stderr)
        sys.exit(2)

    sessions = []
    scanned = 0
    for path in sorted(root.glob("*/*.jsonl")):
        # cheap pre-filter: skip files last modified before the day started
        if datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc) < start:
            continue
        scanned += 1
        result = collect_file(path, start, end, args.snippet_chars)
        if result:
            sessions.append(result)

    sessions.sort(key=lambda s: s["first_ts"])
    print(json.dumps({
        "date": args.date,
        "utc_offset": args.utc_offset,
        "files_scanned": scanned,
        "session_count": len(sessions),
        "sessions": sessions,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
