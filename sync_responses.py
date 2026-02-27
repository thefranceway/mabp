#!/usr/bin/env python3
"""
MABP Response Watcher
Polls Moltbook for new responses to Instruments 1 & 2.
When a new agent responds, saves their response JSON, updates the combined
dataset, commits, and pushes to github.com/thefranceway/mabp.

Run once manually or via launchd. Checks every 15 minutes.
"""
import requests, json, os, subprocess, time, logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

API_KEY   = "moltbook_sk_jSR3ZGuPQdO0RHgo4XP8F6CZiqksJLn6"
BASE_URL  = "https://www.moltbook.com/api/v1"
REPO_DIR  = Path(__file__).parent
DATA_DIR  = REPO_DIR / "data" / "responses"
PROCESSED = REPO_DIR / "data" / "processed" / "all_responses.json"
POLL_SECS = 900  # 15 minutes

INSTRUMENTS = {
    "instrument_1": "275e52a5-878e-4f6d-89d0-ccee6bece026",
    "instrument_2": "73ed75df-a43d-4a0f-9da5-c8e9b2a1a2b3",
}

ADMIN_PATTERNS = [
    "UPDATE —", "Part 2 is live", "incentives for everyone",
    "Shadow Module", "Instrument II", "is live —",
]

def get_headers():
    return {"Authorization": f"Bearer {API_KEY}"}

def resolve_instrument2_id():
    """Shadow module ID — look it up dynamically."""
    r = requests.get(f"{BASE_URL}/posts?author=thefranceway&limit=50",
                     headers=get_headers(), timeout=10)
    posts = r.json().get("posts", [])
    shadow = next((p for p in posts
                   if "shadow module" in p.get("title","").lower()
                   or "part 2" in p.get("title","").lower()), None)
    if shadow:
        INSTRUMENTS["instrument_2"] = shadow["id"]

def fetch_responses(instrument: str, post_id: str) -> dict:
    """Return {agent_name: response_dict} for top-level non-admin comments."""
    rc = requests.get(f"{BASE_URL}/posts/{post_id}/comments",
                      headers=get_headers(), timeout=10)
    comments = rc.json() if isinstance(rc.json(), list) else rc.json().get("comments", [])

    results = {}
    for c in comments:
        if c.get("parent_id"):
            continue
        author = c.get("author", {}).get("name", "unknown")
        content = c.get("content", "")

        # Skip thefranceway admin/meta posts
        if author == "thefranceway" and any(p in content for p in ADMIN_PATTERNS):
            continue

        # Keep longest response per agent
        if author in results and len(content) <= len(results[author]["content"]):
            continue

        results[author] = {
            "comment_id":    c["id"],
            "agent":         author,
            "content":       content,
            "created_at":    c.get("created_at", ""),
            "source_post_id": post_id,
            "instrument":    instrument,
            "archetype":     None,
            "archetype_secondary": None,
            "shadow_pattern": None,
            "notes":         "",
        }
    return results

def load_existing(instrument: str) -> dict:
    folder = DATA_DIR / instrument
    existing = {}
    for fpath in folder.glob("*.json"):
        with open(fpath) as f:
            data = json.load(f)
        existing[data["agent"]] = data
    return existing

def save_response(instrument: str, resp: dict):
    folder = DATA_DIR / instrument
    folder.mkdir(parents=True, exist_ok=True)
    fpath = folder / f"{resp['agent']}.json"
    with open(fpath, "w") as f:
        json.dump(resp, f, indent=2, ensure_ascii=False)

def rebuild_combined():
    combined = []
    for instrument in ["instrument_1", "instrument_2"]:
        folder = DATA_DIR / instrument
        for fpath in sorted(folder.glob("*.json")):
            with open(fpath) as f:
                combined.append(json.load(f))
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED, "w") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    return len(combined)

def git_commit_push(new_agents: list[str]):
    names = ", ".join(new_agents)
    msg = f"Add response(s): {names}\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
    subprocess.run(["git", "-C", str(REPO_DIR), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m", msg], check=True)
    subprocess.run(["git", "-C", str(REPO_DIR), "push"], check=True)
    log.info(f"Pushed to GitHub: {names}")

def check_once():
    resolve_instrument2_id()
    new_agents = []

    for instrument, post_id in INSTRUMENTS.items():
        try:
            live    = fetch_responses(instrument, post_id)
            saved   = load_existing(instrument)
            fresh   = {a: r for a, r in live.items() if a not in saved}

            for agent, resp in fresh.items():
                save_response(instrument, resp)
                log.info(f"New response: @{agent} on {instrument}")
                new_agents.append(f"@{agent} ({instrument})")
        except Exception as e:
            log.error(f"Error on {instrument}: {e}")

    if new_agents:
        total = rebuild_combined()
        log.info(f"Dataset now: {total} respondents")
        try:
            git_commit_push(new_agents)
        except Exception as e:
            log.error(f"Git push failed: {e}")
    else:
        log.info("No new responses.")

    return new_agents

if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        check_once()
    else:
        log.info(f"Watcher started. Polling every {POLL_SECS//60} minutes.")
        while True:
            check_once()
            time.sleep(POLL_SECS)
