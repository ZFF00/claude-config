#!/usr/bin/env python3
"""Discover Codex skills and summarize their metadata without loading bodies."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---(?:\s*\r?\n|\s*\Z)", re.DOTALL)


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.search(text)
    if not match:
        return {}

    data: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in match.group(1).splitlines():
        if raw_line.startswith((" ", "\t")) and current_key:
            continuation = raw_line.strip()
            if continuation:
                data[current_key] = f"{data[current_key]} {continuation}".strip()
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", raw_line)
        if not key_match:
            current_key = None
            continue
        current_key = key_match.group(1)
        data[current_key] = unquote(key_match.group(2))
    return data


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".claude"


def default_roots(include_plugins: bool) -> list[tuple[str, Path]]:
    home = codex_home()
    roots: list[tuple[str, Path]] = [("personal", home / "skills")]

    for directory in (Path.cwd(), *Path.cwd().parents):
        roots.append(("project", directory / ".claude" / "skills"))
        roots.append(("project", directory / ".agents" / "skills"))

    if include_plugins:
        roots.append(("plugin", home / "plugins" / "cache"))

    extra = os.environ.get("CODEX_SKILL_ROOTS", "")
    for item in extra.split(os.pathsep):
        if item.strip():
            roots.append(("custom", Path(item).expanduser()))
    return roots


def find_skill_files(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    try:
        return sorted(root.rglob("SKILL.md"), key=lambda path: str(path).lower())
    except OSError:
        return []


def inspect_skill(skill_file: Path, source: str, discovered_root: Path) -> dict[str, object]:
    issues: list[str] = []
    try:
        text = skill_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return {
            "name": skill_file.parent.name,
            "description": "",
            "source": source,
            "path": str(skill_file.parent),
            "resolved_path": str(skill_file.parent.resolve(strict=False)),
            "discovered_root": str(discovered_root),
            "resources": [],
            "issues": [f"Unable to read SKILL.md: {exc}"],
        }

    metadata = parse_frontmatter(text)
    name = metadata.get("name", "").strip()
    description = metadata.get("description", "").strip()
    if not name:
        issues.append("Missing frontmatter name")
        name = skill_file.parent.name
    if not description:
        issues.append("Missing frontmatter description")
    if name != skill_file.parent.name:
        issues.append("Folder name does not match frontmatter name")

    resources = [
        item
        for item in ("agents", "scripts", "references", "assets")
        if (skill_file.parent / item).exists()
    ]
    if "agents" not in resources:
        issues.append("Recommended agents/openai.yaml is missing")
    elif not (skill_file.parent / "agents" / "openai.yaml").is_file():
        issues.append("agents/openai.yaml is missing")

    return {
        "name": name,
        "description": description,
        "source": "system" if ".system" in skill_file.parts else source,
        "path": str(skill_file.parent),
        "resolved_path": str(skill_file.parent.resolve(strict=False)),
        "discovered_root": str(discovered_root),
        "resources": resources,
        "issues": issues,
    }


def discover(roots: list[tuple[str, Path]]) -> list[dict[str, object]]:
    skills: list[dict[str, object]] = []
    seen: set[str] = set()
    for source, root in roots:
        for skill_file in find_skill_files(root):
            identity = os.path.normcase(str(skill_file.resolve(strict=False)))
            if identity in seen:
                continue
            seen.add(identity)
            skills.append(inspect_skill(skill_file, source, root))
    return sorted(skills, key=lambda item: (str(item["name"]).lower(), str(item["path"]).lower()))


def print_table(skills: list[dict[str, object]]) -> None:
    if not skills:
        print("No skills found.")
        return
    print(f"{'NAME':<30} {'SOURCE':<10} {'STATUS':<8} DESCRIPTION")
    print("-" * 110)
    for skill in skills:
        name = str(skill["name"])[:29]
        description = str(skill["description"]).replace("\n", " ")
        status = "ok" if not skill["issues"] else "check"
        print(f"{name:<30} {str(skill['source']):<10} {status:<8} {description}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("table", "json"), default="table")
    parser.add_argument("--name", help="Return only an exact skill name")
    parser.add_argument("--root", action="append", default=[], help="Additional root to scan")
    parser.add_argument("--skip-plugins", action="store_true", help="Skip the plugin cache")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    roots = default_roots(include_plugins=not args.skip_plugins)
    roots.extend(("custom", Path(item).expanduser()) for item in args.root)
    skills = discover(roots)
    if args.name:
        skills = [skill for skill in skills if skill["name"] == args.name]

    if args.format == "json":
        json.dump(skills, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print_table(skills)
    return 0 if skills or not args.name else 1


if __name__ == "__main__":
    raise SystemExit(main())
