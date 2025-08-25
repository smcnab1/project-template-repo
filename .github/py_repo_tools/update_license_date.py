#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime

# Defaults (can be overridden)
CONFIG_PATH = Path(".github/py_repo_tools/repo_config.json")
LICENSE_PATH = Path(os.environ.get("LICENSE_PATH", "LICENSE.md"))
CURRENT_YEAR = str(datetime.now().year)


def fail(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            fail(f"Failed to parse {CONFIG_PATH}: {e}")
    return {}


def main() -> None:
    if not LICENSE_PATH.exists():
        fail(f"License file not found: {LICENSE_PATH}")

    cfg = load_config()
    # Optional start year: env wins, else config key, else None
    start_year = os.environ.get("LICENSE_START_YEAR") or cfg.get("LICENSE_START_YEAR")

    original = LICENSE_PATH.read_text(encoding="utf-8")
    updated = original
    changed = False

    # 1) Replace explicit ranges like "2019 - YEAR" -> "2019 - 2025"
    #    We only touch ranges that explicitly end with the YEAR token
    range_pattern = re.compile(
        r"(?P<start>\b\d{4}\b)\s*-\s*(?:YEAR|\{YEAR\}|\{\{YEAR\}\})"
    )

    def range_repl(m: re.Match) -> str:
        nonlocal changed
        changed = True
        return f"{m.group('start')}-{CURRENT_YEAR}"

    updated, n1 = range_pattern.subn(range_repl, updated)

    # 2) Replace stand-alone YEAR placeholders (YEAR, {YEAR}, {{YEAR}})
    #    If a start_year is provided, write "start-CURRENT"; else just CURRENT
    placeholder_pattern = re.compile(r"\bYEAR\b|\{YEAR\}|\{\{YEAR\}\}")
    if placeholder_pattern.search(updated):
        repl = f"{start_year}-{CURRENT_YEAR}" if start_year else CURRENT_YEAR
        updated, n2 = placeholder_pattern.subn(repl, updated)
        changed = changed or n2 > 0

    if not changed:
        print(f"ℹ️ No YEAR placeholders found or already up to date in {LICENSE_PATH}")
        return

    LICENSE_PATH.write_text(updated, encoding="utf-8")
    if start_year:
        print(f"✅ Updated {LICENSE_PATH} → set year(s) to {start_year}-{CURRENT_YEAR}")
    else:
        print(f"✅ Updated {LICENSE_PATH} → set year to {CURRENT_YEAR}")


if __name__ == "__main__":
    main()
