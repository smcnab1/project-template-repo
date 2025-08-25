#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import subprocess
import requests
from pathlib import Path
import sys

CONFIG_PATH = Path(".github/py_repo_tools/repo_config.json")
TARGET_FILE = Path("README.md")


def fail(msg: str, code: int = 1) -> None:
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)


def get_github_username() -> str | None:
    """Fetch GitHub username from API if token is available."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "replace-repo-links/1.0",
    }

    try:
        resp = requests.get("https://api.github.com/user", headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json().get("login")
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch GitHub username ({e})")
        return None


def get_repo_name() -> str:
    """Extract repository name from git remote URL, fallback to template."""
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        print("⚠️ Warning: Could not detect remote.origin.url, using default name")
        return "project-template-repo"

    repo_name = url.split("/")[-1].removesuffix(".git")
    return repo_name or "project-template-repo"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        fail(f"Missing config file: {CONFIG_PATH}")
    try:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        fail(f"Failed to parse {CONFIG_PATH}: {e}")


def update_file(
    target: Path, placeholder: str, replacement: str, date_token: str = "DATE"
) -> None:
    if not target.exists():
        fail(f"Target file not found: {target}")

    contents = target.read_text(encoding="utf-8")
    changed = False

    if placeholder in contents:
        contents = contents.replace(placeholder, replacement)
        changed = True
    else:
        print(f"⚠️ Placeholder '{placeholder}' not found in {target}")

    current_date = datetime.datetime.now().strftime("%d %b %y")
    if date_token in contents:
        contents = contents.replace(date_token, current_date)
        changed = True

    if changed:
        target.write_text(contents, encoding="utf-8")
        print(f"✅ Updated {target} with repo links and date")
    else:
        print(f"ℹ️ No changes applied to {target}")


def main() -> None:
    config = load_config()
    placeholder = config.get("PLACEHOLDER_REPO")
    if not placeholder:
        fail(f"No 'PLACEHOLDER_REPO' key in {CONFIG_PATH}")

    repo_name = get_repo_name()
    username = get_github_username() or "smcnab1"
    replacement = f"{username}/{repo_name}"

    update_file(TARGET_FILE, placeholder, replacement)


if __name__ == "__main__":
    main()
