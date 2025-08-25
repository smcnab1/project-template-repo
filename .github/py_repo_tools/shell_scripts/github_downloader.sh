#!/usr/bin/env bash
set -euo pipefail

# Download a folder or file from a GitHub repo (public or private).
# Supports:
#   owner/repo[:path]
#   owner/repo@ref[:path]
#   https://github.com/owner/repo/tree/ref/path
#
# Public repos -> svn export
# Private repos -> GitHub API + GITHUB_TOKEN (zipball)

usage() {
  echo "Usage:"
  echo "  $0 owner/repo[:path]"
  echo "  $0 owner/repo@ref[:path]"
  echo "  $0 https://github.com/owner/repo/tree/ref/path"
  exit 1
}

if [[ $# -lt 1 ]]; then usage; fi
INPUT="$1"

# Parse input
strip_domain() {
  local url="$1"
  echo "${url#https://github.com/}"
}

owner="" repo="" ref="" path=""

parse_input() {
  local in="$1"
  if [[ "$in" == http*://github.com/* ]]; then
    in="$(strip_domain "$in")"
  fi

  if [[ "$in" == */tree/* ]]; then
    owner="${in%%/*}"
    local rest="${in#*/}"
    repo="${rest%%/*}"
    local after_repo="${rest#*/}"
    local after_tree="${after_repo#tree/}"
    ref="${after_tree%%/*}"
    path="${after_tree#*/}"
    [[ "$path" == "$ref" ]] && path=""
    return
  fi

  local head="${in%%[:@]*}"
  local tail="${in#"$head"}"
  owner="${head%%/*}"
  repo="${head#*/}"

  if [[ "$tail" == @*:* ]]; then
    local after_at="${tail#@}"
    ref="${after_at%%:*}"
    path="${after_at#*:}"
  elif [[ "$tail" == :* ]]; then
    ref=""
    path="${tail#:}"
  elif [[ "$tail" == @* ]]; then
    ref="${tail#@}"
    path=""
  else
    ref=""
    path=""
  fi
}
parse_input "$INPUT"

if [[ -z "$owner" || -z "$repo" ]]; then
  echo "❌ Could not parse owner/repo from input: '$INPUT'" >&2
  usage
fi

GHDOMAIN="https://github.com"
svn_base="${GHDOMAIN}/${owner}/${repo}"

# Detect if private
is_private() {
  local api="https://api.github.com/repos/${owner}/${repo}"
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    curl -s -H "Authorization: token $GITHUB_TOKEN" "$api" | grep -q '"private": true'
  else
    curl -s "$api" | grep -q '"private": true'
  fi
}

if is_private; then
  echo "🔒 Private repo detected. Using GitHub API + zipball..."
  REF="${ref:-main}"
  tmpdir=$(mktemp -d)
  zipfile="$tmpdir/repo.zip"

  auth=()
  [[ -n "${GITHUB_TOKEN:-}" ]] && auth=(-H "Authorization: token $GITHUB_TOKEN")

  curl -sL "${auth[@]}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${owner}/${repo}/zipball/${REF}" \
    -o "$zipfile"

  unzip -q "$zipfile" -d "$tmpdir"
  extracted=$(find "$tmpdir" -maxdepth 1 -type d -name "${owner}-${repo}-*")
  if [[ -n "$path" ]]; then
    echo "Exporting $owner/$repo@$REF:$path"
    cp -r "$extracted/$path" .
  else
    echo "Exporting $owner/$repo@$REF (full repo)"
    cp -r "$extracted"/* .
  fi
  rm -rf "$tmpdir"

else
  echo "🌍 Public repo detected. Using svn export..."
  svn_url=""
  if [[ -z "$ref" ]]; then
    svn_url="${svn_base}/trunk"
    [[ -n "$path" ]] && svn_url="${svn_url}/${path}"
  else
    if svn ls "${svn_base}/branches/${ref}" >/dev/null 2>&1; then
      svn_url="${svn_base}/branches/${ref}"
    elif svn ls "${svn_base}/tags/${ref}" >/dev/null 2>&1; then
      svn_url="${svn_base}/tags/${ref}"
    else
      svn_url="${svn_base}/trunk"
    fi
    [[ -n "$path" ]] && svn_url="${svn_url}/${path}"
  fi

  echo "Exporting $svn_url"
  svn --force export "$svn_url" .
fi
