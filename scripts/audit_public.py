#!/usr/bin/env python3
"""Fail if the public package contains private paths, internal snapshots, or missing files."""

from __future__ import annotations

import sys
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "SKILL.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "requirements.txt",
    "agents/openai.yaml",
    "references/concept-routing.md",
    "references/ratio-native-recomposition.md",
    "references/wide-5x1-recomposition.md",
    "references/quality-review.md",
    "references/creator-profile.example.md",
    "scripts/render-ratio-pack.py",
    "scripts/build-wechat-cover-stitch.py",
    "examples/LICENSE.md",
)
FORBIDDEN_PATTERNS = (
    ("macOS absolute user path", re.compile(r"/" + r"Users/[^/\s]+/")),
    ("legacy private archive name", re.compile("feige" + r"-cover-agent-skill-archive")),
    ("internal project snapshot", re.compile(r"project/" + "_codex")),
    ("private portrait catalog", re.compile("\u4e2a\u4eba" + "\u5b9e\u62cd")),
    ("private quality archive", re.compile("\u4f18\u8d28" + "\u5b58\u6863")),
    ("private-only repository instruction", re.compile("\u672c\u4ed3\u5e93\u5fc5\u987b\u4fdd\u6301 " + "Private")),
)
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
    ".txt",
    ".toml",
}


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            failures.append(f"MISSING: {relative}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE", ".gitignore"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(content):
                failures.append(f"FORBIDDEN {label}: {path.relative_to(ROOT)}")

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8") if (ROOT / "SKILL.md").is_file() else ""
    if not skill.startswith("---\nname: creator-cover\n"):
        failures.append("SKILL.md frontmatter must declare name: creator-cover")
    if "2000×400" not in skill or "5:1" not in skill:
        failures.append("SKILL.md must retain the exact 5:1 contract")
    if "硬文字清单" not in skill:
        failures.append("SKILL.md must retain the hard-text review gate")

    metadata = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8") if (ROOT / "agents/openai.yaml").is_file() else ""
    if "$creator-cover" not in metadata:
        failures.append("agents/openai.yaml default_prompt must mention $creator-cover")

    if failures:
        print("Public-package audit failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("OK: public package contains required files and no known private-path markers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
