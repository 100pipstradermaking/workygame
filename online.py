"""
online.py — Online features for WORKY.
Handles:
  1. Browser localStorage persistence (for pygbag/WebAssembly builds)
  2. Online leaderboard sync via GitHub repo file
"""

import json
import time
import sys

# ── Configuration ─────────────────────────────────────────────
REPO = "100pipstradermaking/workygame"
BRANCH = "gh-pages"
LB_FILE = "leaderboard_data.json"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{LB_FILE}"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{LB_FILE}"
MAX_ONLINE_ENTRIES = 100

def _get_token():
    """Load GitHub token from _config.py (gitignored) or env var."""
    import os
    tok = os.environ.get("WORKY_GH_TOKEN", "")
    if tok:
        return tok
    try:
        from _config import GH_TOKEN
        return GH_TOKEN
    except Exception:
        return ""

# Throttle: don't push more than once per 30 seconds
_last_push_time = 0.0
PUSH_COOLDOWN = 30.0


def is_web() -> bool:
    """Check if running in a browser (pygbag WebAssembly)."""
    try:
        import platform as _p
        return hasattr(_p, "window")
    except Exception:
        return sys.platform == "emscripten"


# ── Browser localStorage wrappers ─────────────────────────────

def web_save(key: str, data: dict) -> bool:
    """Save JSON data to browser localStorage. Returns True on success."""
    if not is_web():
        return False
    try:
        import platform
        js_data = json.dumps(data)
        platform.window.localStorage.setItem(f"worky_{key}", js_data)
        return True
    except Exception:
        return False


def web_load(key: str) -> dict | None:
    """Load JSON data from browser localStorage. Returns None if not found."""
    if not is_web():
        return None
    try:
        import platform
        raw = platform.window.localStorage.getItem(f"worky_{key}")
        if raw and str(raw) != "null" and str(raw) != "undefined":
            return json.loads(str(raw))
    except Exception:
        pass
    return None


def web_delete(key: str) -> bool:
    """Remove a key from browser localStorage."""
    if not is_web():
        return False
    try:
        import platform
        platform.window.localStorage.removeItem(f"worky_{key}")
        return True
    except Exception:
        return False


# ── Online leaderboard — READ (no auth, public raw URL) ──────

def fetch_online_leaderboard() -> list[dict]:
    """Fetch online leaderboard entries. Returns empty list on failure."""
    try:
        import urllib.request
        req = urllib.request.Request(
            RAW_URL + f"?t={int(time.time())}",  # cache-bust
            headers={"Accept": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        entries = data.get("entries", [])
        entries.sort(key=lambda e: e.get("score", 0), reverse=True)
        return entries
    except Exception:
        return []


def fetch_online_votes() -> dict:
    """Fetch online votes data. Returns empty dict on failure."""
    try:
        import urllib.request
        req = urllib.request.Request(
            RAW_URL + f"?t={int(time.time())}",
            headers={"Accept": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        return data.get("votes", {})
    except Exception:
        return {}


# ── Online leaderboard — WRITE (requires token) ──────────────

def _get_file_sha() -> str | None:
    """Get current SHA of the leaderboard file (needed for updates)."""
    try:
        import urllib.request
        req = urllib.request.Request(
            API_URL + f"?ref={BRANCH}",
            headers={
                "Authorization": f"token {_get_token()}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        return data.get("sha")
    except Exception:
        return None


def push_score_online(entry: dict) -> bool:
    """Submit a score to the online leaderboard. Returns True on success."""
    global _last_push_time

    now = time.time()
    if now - _last_push_time < PUSH_COOLDOWN:
        return False

    try:
        import urllib.request
        import base64

        # 1. Fetch current data
        entries = fetch_online_leaderboard()
        votes = fetch_online_votes()

        # 2. Update or add entry
        found = False
        for i, e in enumerate(entries):
            if (e.get("name") == entry.get("name") and
                    e.get("restaurant") == entry.get("restaurant")):
                if entry.get("score", 0) > e.get("score", 0):
                    entries[i] = entry
                found = True
                break
        if not found:
            entries.append(entry)

        # 3. Sort and trim
        entries.sort(key=lambda e: e.get("score", 0), reverse=True)
        entries = entries[:MAX_ONLINE_ENTRIES]

        # 4. Get current SHA
        sha = _get_file_sha()
        if not sha:
            return False

        # 5. Push update
        new_content = json.dumps({"entries": entries, "votes": votes}, indent=2)
        content_b64 = base64.b64encode(new_content.encode()).decode()

        body = json.dumps({
            "message": f"Leaderboard update: {entry.get('name', 'anon')}",
            "content": content_b64,
            "sha": sha,
            "branch": BRANCH,
        }).encode()

        req = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                "Authorization": f"token {_get_token()}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            },
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=10)
        _last_push_time = now
        return True
    except Exception:
        return False


def push_vote_online(voter: str, target_name: str, target_restaurant: str,
                     stars: int) -> bool:
    """Cast a vote online. Returns True on success."""
    global _last_push_time

    now = time.time()
    if now - _last_push_time < PUSH_COOLDOWN:
        return False

    try:
        import urllib.request
        import base64

        entries = fetch_online_leaderboard()
        votes = fetch_online_votes()

        key = f"{target_name}::{target_restaurant}"
        if key not in votes:
            votes[key] = {"name": target_name, "restaurant": target_restaurant, "votes": []}

        vote_list = votes[key]["votes"]
        found = False
        for v in vote_list:
            if v.get("voter") == voter:
                v["stars"] = stars
                v["time"] = now
                found = True
                break
        if not found:
            vote_list.append({"voter": voter, "stars": stars, "time": now})

        sha = _get_file_sha()
        if not sha:
            return False

        new_content = json.dumps({"entries": entries, "votes": votes}, indent=2)
        content_b64 = base64.b64encode(new_content.encode()).decode()

        body = json.dumps({
            "message": f"Vote: {voter} -> {target_name}",
            "content": content_b64,
            "sha": sha,
            "branch": BRANCH,
        }).encode()

        req = urllib.request.Request(
            API_URL,
            data=body,
            headers={
                "Authorization": f"token {_get_token()}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            },
            method="PUT",
        )
        urllib.request.urlopen(req, timeout=10)
        _last_push_time = now
        return True
    except Exception:
        return False
