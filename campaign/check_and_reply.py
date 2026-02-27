#!/usr/bin/env python3
"""
MABP Comment Watcher + Auto-Responder
Polls all thefranceway posts for unreplied comments.
Tracks replied comments in replied.json (local state) so the Moltbook API's
limitation of not returning nested comments doesn't cause false positives.

Usage:
  python3 check_and_reply.py --once     # single check, print unreplied
  python3 check_and_reply.py            # daemon, polls every 10 min
"""
import requests, json, time, sys, logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

API_KEY   = "moltbook_sk_jSR3ZGuPQdO0RHgo4XP8F6CZiqksJLn6"
BASE_H    = {"Authorization": f"Bearer {API_KEY}"}
POST_H    = {**BASE_H, "Content-Type": "application/json"}
BASE_URL  = "https://www.moltbook.com/api/v1"
STATE     = Path(__file__).parent / "replied.json"
POLL_SECS = 600  # 10 minutes

def load_replied() -> set:
    if STATE.exists():
        with open(STATE) as f:
            return set(json.load(f).get("replied_to", []))
    return set()

def save_replied(replied: set):
    with open(STATE) as f:
        data = json.load(f)
    data["replied_to"] = sorted(replied)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(STATE, "w") as f:
        json.dump(data, f, indent=2)

def short(uid: str) -> str:
    return uid[:8]

def get_posts():
    r = requests.get(f"{BASE_URL}/posts?author=thefranceway&limit=50",
                     headers=BASE_H, timeout=10)
    return r.json().get("posts", [])

def get_comments(post_id: str) -> list:
    rc = requests.get(f"{BASE_URL}/posts/{post_id}/comments",
                      headers=BASE_H, timeout=10)
    return rc.json() if isinstance(rc.json(), list) else rc.json().get("comments", [])

def find_unreplied(posts, replied: set) -> list:
    """Return list of dicts with post + comment info for all unreplied comments."""
    unreplied = []
    for post in posts:
        if post.get("comment_count", 0) == 0:
            continue
        comments = get_comments(post["id"])
        seen_keys = set()
        for c in comments:
            author = c["author"]["name"]
            if author == "thefranceway":
                continue
            if c.get("parent_id"):          # skip nested (agent-to-agent)
                continue
            key = (author, c["content"][:60])
            if key in seen_keys:            # deduplicate API retries
                continue
            seen_keys.add(key)
            if short(c["id"]) in replied:   # already handled
                continue
            unreplied.append({
                "post_id":    post["id"],
                "post_title": post.get("title", "")[:55],
                "comment_id": c["id"],
                "author":     author,
                "content":    c["content"],
            })
        time.sleep(0.25)
    return unreplied

def post_reply(post_id: str, parent_id: str, content: str) -> bool:
    resp = requests.post(f"{BASE_URL}/posts/{post_id}/comments",
        headers=POST_H,
        json={"content": content, "parent_id": parent_id},
        timeout=15)
    return resp.status_code == 201

def mark_replied(comment_id: str):
    replied = load_replied()
    replied.add(short(comment_id))
    save_replied(replied)

def check_once(auto_reply=False):
    replied = load_replied()
    posts   = get_posts()
    unreplied = find_unreplied(posts, replied)

    if not unreplied:
        log.info("All comments replied to ✓")
        return []

    log.info(f"{len(unreplied)} unreplied comment(s):")
    for u in unreplied:
        log.info(f"  [{u['post_id'][:8]}] @{u['author']} [{u['comment_id'][:8]}]: {u['content'][:80]}")

    return unreplied

def run_daemon():
    log.info(f"Watcher started — polling every {POLL_SECS//60} min")
    while True:
        try:
            check_once()
        except Exception as e:
            log.error(f"Error: {e}")
        time.sleep(POLL_SECS)

if __name__ == "__main__":
    if "--once" in sys.argv:
        results = check_once()
        if results:
            print(f"\n{len(results)} comment(s) need replies:")
            for u in results:
                print(f"\n  [{u['post_id'][:8]}] \"{u['post_title']}\"")
                print(f"  @{u['author']} [{u['comment_id'][:8]}]:")
                print(f"  {u['content'][:300]}")
    else:
        run_daemon()
