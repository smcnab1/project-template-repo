#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

CONFIG_PATH = Path(".github/py_repo_tools/repo_config.json")
TARGET_FILE = Path(".github/SECURITY.md")
PLACEHOLDER = "example@hello.com"


def fail(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def load_config(path: Path) -> dict:
    if not path.exists():
        fail(f"Config file not found: {path}")
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        fail(f"Failed to read/parse config {path}: {e}")


def replace_email(target: Path, old: str, new: str) -> None:
    if not target.exists():
        fail(f"Target file not found: {target}")

    contents = target.read_text(encoding="utf-8")
    if old not in contents:
        print(f"⚠️ Placeholder '{old}' not found in {target} — no changes made.")
        return

    updated = contents.replace(old, new)
    target.write_text(updated, encoding="utf-8")
    print(f"✅ Replaced '{old}' with '{new}' in {target}")


def main():
    config = load_config(CONFIG_PATH)
    email = config.get("CONTACT_EMAIL")
    if not email:
        fail(f"No 'CONTACT_EMAIL' key found in {CONFIG_PATH}")

    replace_email(TARGET_FILE, PLACEHOLDER, email)


if __name__ == "__main__":
    main()
