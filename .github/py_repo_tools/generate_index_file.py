#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import html
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Tuple, Dict

API_OR_WEB_URL = os.environ.get("INPUT_STORE", "").strip()
README_PATH = Path(os.environ.get("README_PATH", "README.md"))
OUTPUT_PATH = Path(os.environ.get("INDEX_OUT", "index.html"))
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
CONFIG_PATH = Path(".github/py_repo_tools/repo_config.json")  # <- new

USER_AGENT = "repo-index-generator/1.0 (+https://github.com/)"


def fail(msg: str, code: int = 1) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def to_api_url(url: str) -> str:
    """
    Accepts:
      - https://api.github.com/repos/owner/repo
      - https://github.com/owner/repo
      - owner/repo
    Returns API URL form.
    """
    if not url:
        fail("INPUT_STORE is empty; expected a GitHub repo URL or API URL.")

    # Already an API URL
    if url.startswith("https://api.github.com/repos/"):
        return url.rstrip("/")

    # Web URL -> API URL
    if url.startswith("https://github.com/"):
        tail = url[len("https://github.com/") :].strip("/")
        parts = tail.split("/")
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            return f"https://api.github.com/repos/{owner}/{repo}"

    # owner/repo
    if "/" in url and "://" not in url:
        owner, repo = url.split("/", 1)
        return f"https://api.github.com/repos/{owner}/{repo}"

    fail(f"Could not normalise INPUT_STORE to API URL: {url}")


def fetch_repo_json(api_url: str) -> Dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    req = urllib.request.Request(api_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                fail(f"GitHub API returned HTTP {resp.status} for {api_url}")
            data = resp.read()
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as e:
        fail(f"GitHub API error {e.code}: {e.reason} for {api_url}")
    except urllib.error.URLError as e:
        fail(f"Network error: {e.reason} while fetching {api_url}")
    except json.JSONDecodeError:
        fail("Failed to parse JSON from GitHub API response.")


def derive_site_urls(repo: Dict) -> Tuple[str, str, str]:
    """
    Returns (site_title, site_description, site_url)
    - Prefer repo['homepage'] if set for site_url
    - Else use https://{owner}.github.io/{repo}
    """
    name = repo.get("name") or ""
    description = repo.get("description") or ""
    owner_login = (repo.get("owner") or {}).get("login") or "user"

    # Preferred site URL: repo homepage if it looks like a URL
    homepage = (repo.get("homepage") or "").strip()
    if homepage.startswith("http://") or homepage.startswith("https://"):
        site_url = homepage
    else:
        site_url = f"https://{owner_login}.github.io/{name}"

    # Escape for HTML context
    return (
        html.escape(name),
        html.escape(description),
        html.escape(site_url),
    )


def require_readme(readme_path: Path) -> str:
    if not readme_path.exists():
        fail(f"{readme_path} does not exist.")
    try:
        return readme_path.read_text(encoding="utf-8")
    except Exception as e:
        fail(f"Failed to read {readme_path}: {e}")


def og_image_url(title: str) -> str:
    # Build a safe OG image URL using Vercel's og-image service.
    # URL-encode title and embed a neutral icon.
    encoded_title = urllib.parse.quote(title, safe="")
    img = "https://assets.vercel.com/image/upload/front/assets/design/hyper-color-logo.svg"
    encoded_img = urllib.parse.quote(img, safe="")
    return (
        f"https://og-image.vercel.app/{encoded_title}.png"
        f"?theme=light&md=0&fontSize=100px&images={encoded_img}"
    )


def build_html(title: str, description: str, site_url: str, markdown: str) -> str:
    # We keep client-side render via Markdown-Tag (as in your original),
    # but add GitHub markdown CSS to improve appearance.
    og_img = og_image_url(title)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

  <!-- Primary Meta Tags -->
  <meta name="title" content="{title}">
  <meta name="description" content="{description}">

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website">
  <meta property="og:url" content="{site_url}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{og_img}">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:url" content="{site_url}">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_img}">

  <!-- GitHub-style Markdown CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5.5.1/github-markdown.min.css">
  <style>
    body {{ margin: 0; padding: 2rem; }}
    .markdown-body {{ box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; padding: 45px; }}
    @media (max-width: 767px) {{
      .markdown-body {{ padding: 15px; }}
    }}
  </style>

  <!-- Prism (optional, for code highlight if Markdown-Tag emits <pre><code>) -->
  <script defer src="https://cdn.jsdelivr.net/npm/prismjs@1.28.0/prism.min.js"></script>
</head>
<body>
  <article class="markdown-body">
    <github-md>
{markdown}
    </github-md>
  </article>

  <!-- Client-side Markdown renderer -->
  <script defer src="https://cdn.jsdelivr.net/gh/MarketingPipeline/Markdown-Tag/markdown-tag-GitHub.js"></script>
</body>
</html>
"""


def load_local_config() -> Dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            # Non-fatal: just ignore bad local config
            return {}
    return {}


def main() -> None:
    api_url = to_api_url(API_OR_WEB_URL)
    repo = fetch_repo_json(api_url)
    title, description, site_url = derive_site_urls(repo)
    # --- new: apply local config fallbacks if API fields are empty ---
    cfg = load_local_config()
    if not description:
        description = html.escape(cfg.get("PROJECT_DESCRIPTION", ""))
    if (not site_url) and cfg.get("PROJECT_HOMEPAGE"):
        site_url = html.escape(cfg.get("PROJECT_HOMEPAGE", ""))
    # PROJECT_AUTHOR is available if you later want to render it somewhere:
    # author = html.escape(cfg.get("PROJECT_AUTHOR", ""))  # unused currently
    # ---------------------------------------------------------------

    readme = require_readme(README_PATH)
    html_out = build_html(title, description, site_url, readme)

    try:
        OUTPUT_PATH.write_text(html_out, encoding="utf-8")
        print(f"Wrote {OUTPUT_PATH} ✅")
    except Exception as e:
        fail(f"Unable to write to {OUTPUT_PATH}: {e}")


if __name__ == "__main__":
    main()
