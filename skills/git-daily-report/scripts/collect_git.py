#!/usr/bin/env python3
"""Collect git commits in a date range and emit structured JSON.

Designed for non-interactive Agent execution:
- No prompts; everything via CLI args.
- Structured output (JSON) to stdout; diagnostics to stderr.
- Helpful error messages; exit code 2 on git failure, 3 on usage error.
"""
import argparse
import json
import re
import subprocess
import sys

DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def expand_day(value: str | None, end: bool) -> str | None:
    """Expand a bare YYYY-MM-DD to a full-day boundary.

    git interprets a bare date as midnight, so --since D --until D is an
    empty window. Expand --since to 00:00:00 and --until to 23:59:59 of
    that day; anything else (e.g. '1 day ago') passes through unchanged.
    """
    if value and DATE_ONLY.match(value):
        return f"{value} 23:59:59" if end else f"{value} 00:00:00"
    return value


def run_git(args: list[str], repo: str) -> str:
    cmd = ["git", "-C", repo, *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return proc.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print(f"git error: {exc.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print("git executable not found; install git and ensure it is on PATH.", file=sys.stderr)
        sys.exit(2)


def collect(repo: str, since: str, until: str | None, author: str | None, all_refs: bool) -> list[dict]:
    # Field separator \x1f, record separator \x1e — safe for git log parsing.
    fmt = "%x1f".join(["%H", "%an", "%ad", "%s"]) + "%x1e"
    args = ["log", f"--since={since}", f"--pretty=format:{fmt}", "--date=short"]
    if all_refs:
        # Daily-report commits often land on worktree/agent branches that are
        # not merged into HEAD yet; without --all they are invisible.
        args.append("--all")
    if until:
        args.append(f"--until={until}")
    if author:
        args.append(f"--author={author}")

    raw = run_git(args, repo)
    commits: list[dict] = []
    for block in raw.split("\x1e"):
        block = block.strip("\n")
        if not block:
            continue
        parts = block.split("\x1f")
        if len(parts) < 4:
            continue
        h, an, ad, s = parts[0], parts[1], parts[2], parts[3]
        commits.append(
            {
                "hash": h[:8],
                "author": an,
                "date": ad,
                "subject": s,
            }
        )
    return commits


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect git commits as structured JSON for daily reports."
    )
    parser.add_argument("--repo", default=".", help="Path to git repo (default: cwd)")
    parser.add_argument("--since", default="1 day ago", help="git --since value, e.g. '1 day ago' or '2026-08-26'")
    parser.add_argument("--until", default=None, help="git --until value (optional)")
    parser.add_argument("--author", default=None, help="Filter by author (optional)")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format (default json)")
    parser.add_argument(
        "--no-all",
        dest="all_refs",
        action="store_false",
        help="Only search HEAD's branch instead of all refs (default: --all, covering worktree/unmerged branches)",
    )
    args = parser.parse_args()

    since = expand_day(args.since, end=False)
    until = expand_day(args.until, end=True)
    commits = collect(args.repo, since, until, args.author, args.all_refs)

    if args.format == "json":
        print(json.dumps({"count": len(commits), "commits": commits}, ensure_ascii=False, indent=2))
    else:
        if not commits:
            print("(no commits in range)")
        for c in commits:
            print(f"- [{c['date']}] {c['subject']} ({c['hash']})")


if __name__ == "__main__":
    main()
