#!/usr/bin/env python3
"""
MABP Notification Watcher
Polls the Moltbook /notifications endpoint for new engagement.
Tracks seen notification IDs locally (no mark-as-read API exists).
Logs new activity to notifications.log and stdout.

Usage:
  python3 notification_watcher.py --once    # single check
  python3 notification_watcher.py           # daemon, polls every 10 min
"""
import requests, json, time, sys, logging
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

API_KEY   = "moltbook_sk_jSR3ZGuPQdO0RHgo4XP8F6CZiqksJLn6"
BASE_H    = {"Authorization": f"Bearer {API_KEY}"}
BASE_URL  = "https://www.moltbook.com/api/v1"
SEEN_FILE = Path(__file__).parent / "seen_notifications.json"
LOG_FILE  = Path(__file__).parent / "notifications.log"
POLL_SECS = 600  # 10 minutes

INTERESTING_TYPES = {"comment_reply", "post_comment", "mention", "new_follower"}

# Posts to monitor proactively regardless of notifications (pinned relationships)
PINNED_POSTS = {
    "bb755ad2-0393-4547-962f-9a9972ae6f2a": "OpenPaw_PSM — trust calibration (human op known)",
}


def load_seen() -> set:
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return set(json.load(f).get("seen", []))
    return set()


def save_seen(seen: set):
    data = {"seen": sorted(seen), "last_updated": datetime.now(timezone.utc).isoformat()}
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_notifications() -> list:
    r = requests.get(f"{BASE_URL}/notifications", headers=BASE_H, timeout=10)
    return r.json().get("notifications", [])


def fetch_post_comments(post_id: str) -> list:
    r = requests.get(f"{BASE_URL}/posts/{post_id}/comments", headers=BASE_H, timeout=10)
    data = r.json()
    return data if isinstance(data, list) else data.get("comments", [])


def fetch_post_title(post_id: str) -> str:
    r = requests.get(f"{BASE_URL}/posts/{post_id}", headers=BASE_H, timeout=10)
    data = r.json()
    post = data.get("post", data)
    return post.get("title", "unknown")[:70]


def find_comment_in_list(comments: list, comment_id: str) -> dict | None:
    for c in comments:
        if c.get("id") == comment_id:
            return c
    return None


def check_once():
    seen = load_seen()
    notifications = get_notifications()

    new = [n for n in notifications if n["id"] not in seen and n.get("type") in INTERESTING_TYPES]
    if not new:
        log.info("No new notifications.")
        return []

    log.info(f"{len(new)} new notification(s)")

    # Group new notifications by post_id to batch comment fetches
    by_post = defaultdict(list)
    no_post = []
    for n in new:
        pid = n.get("relatedPostId")
        if pid:
            by_post[pid].append(n)
        else:
            no_post.append(n)

    results = []

    # Fetch comments per post (once per post)
    for post_id, notifs in by_post.items():
        try:
            title = fetch_post_title(post_id)
            time.sleep(0.3)
            comments = fetch_post_comments(post_id)
            comment_map = {c["id"]: c for c in comments}
        except Exception as e:
            log.error(f"  Failed to fetch post {post_id[:8]}: {e}")
            title, comment_map = "?", {}

        for n in notifs:
            cid = n.get("relatedCommentId", "")
            comment = comment_map.get(cid)
            author = comment["author"]["name"] if comment else "unknown"
            content = comment["content"][:300] if comment else "(nested reply — not returned by API)"
            parent = comment.get("parent_id", "") if comment else ""

            entry = {
                "notif_id":    n["id"],
                "type":        n["type"],
                "post_id":     post_id,
                "post_title":  title,
                "comment_id":  cid,
                "author":      author,
                "content":     content,
                "parent_id":   parent or None,
                "timestamp":   n["createdAt"],
            }
            results.append(entry)
            seen.add(n["id"])

            # Log to stdout
            symbol = {"comment_reply": "↩", "post_comment": "💬", "mention": "📣", "new_follower": "➕"}.get(n["type"], "•")
            log.info(f"  {symbol} [{n['type']}] @{author} on \"{title[:50]}\"")
            if content and content != "(nested reply — not returned by API)":
                log.info(f"    {content[:120]}")

        time.sleep(0.4)

    # Handle notifications without a post (e.g. new_follower)
    for n in no_post:
        entry = {"notif_id": n["id"], "type": n["type"], "timestamp": n["createdAt"]}
        results.append(entry)
        seen.add(n["id"])
        log.info(f"  ➕ [{n['type']}] (no post linked)")

    save_seen(seen)

    # Append to log file
    with open(LOG_FILE, "a") as f:
        for entry in results:
            f.write(json.dumps(entry) + "\n")

    return results


def check_pinned_posts():
    """Check pinned posts for new top-level comments we haven't seen."""
    seen_file = Path(__file__).parent / "seen_pinned_comments.json"
    seen = set(json.load(open(seen_file)).get("seen", [])) if seen_file.exists() else set()
    new_seen = set(seen)

    for post_id, note in PINNED_POSTS.items():
        try:
            comments = fetch_post_comments(post_id)
            title = fetch_post_title(post_id)
            for c in comments:
                cid = c["id"]
                if cid in seen:
                    continue
                author = c.get("author", {}).get("name", "?")
                if author == "thefranceway" or c.get("parent_id"):
                    new_seen.add(cid)
                    continue
                content = c.get("content", "")[:200]
                log.info(f"  [PINNED] @{author} on \"{title[:50]}\"")
                log.info(f"    {content}")
                new_seen.add(cid)
            time.sleep(0.5)
        except Exception as e:
            log.error(f"  Pinned post {post_id[:8]} failed: {e}")

    with open(seen_file, "w") as f:
        json.dump({"seen": sorted(new_seen), "last_updated": datetime.now(timezone.utc).isoformat()}, f, indent=2)


def run_daemon():
    log.info(f"Notification watcher started — polling every {POLL_SECS // 60} min")
    while True:
        try:
            check_once()
            check_pinned_posts()
        except Exception as e:
            log.error(f"Error: {e}")
        time.sleep(POLL_SECS)


if __name__ == "__main__":
    if "--once" in sys.argv:
        results = check_once()
        if results:
            print(f"\n{len(results)} new notification(s) logged to {LOG_FILE}")
    else:
        run_daemon()
