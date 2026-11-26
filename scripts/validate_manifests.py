#!/usr/bin/env python3
"""Validates plugin manifests, SKILL.md frontmatter, and open-source hygiene."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = [
    ROOT / "plugin.json",
    ROOT / ".antigravity-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".codex-plugin" / "plugin.json",
]
REQUIRED_KEYS = {"name", "displayName", "version", "description", "author", "repository", "keywords"}


def main() -> int:
    errors = []
    versions = set()
    for mpath in MANIFESTS:
        if not mpath.exists():
            errors.append(f"Missing manifest: {mpath}")
            continue
        raw = mpath.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"UTF-8 BOM detected (must be BOM-free): {mpath}")
        data = json.loads(raw.decode("utf-8"))
        missing = REQUIRED_KEYS - set(data.keys())
        if missing:
            errors.append(f"{mpath.name} missing keys: {sorted(missing)}")
        versions.add(data.get("version"))

    if len(versions) != 1:
        errors.append(f"Version drift across manifests: {versions}")

    skill_md = ROOT / "skills" / "codebase-ast-rag-indexer" / "SKILL.md"
    if not skill_md.exists():
        errors.append("Missing skills/codebase-ast-rag-indexer/SKILL.md")
    else:
        txt = skill_md.read_text(encoding="utf-8")
        fm = re.match(r"^---\s*\n(.*?)\n---", txt, re.DOTALL)
        if not fm:
            errors.append("SKILL.md missing YAML frontmatter")
        else:
            body = fm.group(1)
            if "name:" not in body or "description:" not in body:
                errors.append("SKILL.md frontmatter must declare name and description")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"OK: Validated {len(MANIFESTS)} manifests (v{next(iter(versions))}) and SKILL.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
