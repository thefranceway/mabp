#!/usr/bin/env python3
"""
MABP Daily KPI Dashboard
Computes Virality Score (VS) and Integrity Score (IS) from live Moltbook data.
Run daily: python3 kpi.py
"""
import requests, json, os
from datetime import datetime, timezone
from pathlib import Path

API_KEY  = "moltbook_sk_jSR3ZGuPQdO0RHgo4XP8F6CZiqksJLn6"
HEADERS  = {"Authorization": f"Bearer {API_KEY}"}
BASE     = "https://www.moltbook.com/api/v1"
REPO     = Path(__file__).parent.parent
DATA_DIR = REPO / "data" / "responses"
LOG_FILE = REPO / "dashboard" / "kpi_log.jsonl"

# ── Fetch data ────────────────────────────────────────────────────────────────

def get_our_posts():
    r = requests.get(f"{BASE}/posts?author=thefranceway&limit=50", headers=HEADERS, timeout=10)
    return r.json().get("posts", [])

def get_comments(post_id):
    rc = requests.get(f"{BASE}/posts/{post_id}/comments", headers=HEADERS, timeout=10)
    return rc.json() if isinstance(rc.json(), list) else rc.json().get("comments", [])

def load_responses():
    """Load all saved instrument responses."""
    agents = {}
    for instrument in ["instrument_1", "instrument_2"]:
        folder = DATA_DIR / instrument
        if not folder.exists():
            continue
        for fpath in folder.glob("*.json"):
            with open(fpath) as f:
                data = json.load(f)
            agent = data["agent"]
            if agent != "thefranceway":
                agents[agent] = data
    return agents

# ── KPI calculations ──────────────────────────────────────────────────────────

def score_edr(posts_data):
    """Engagement Depth Ratio: meaningful replies / impressions (proxy: comments / posts)."""
    total_comments = sum(p.get("comment_count", 0) for p in posts_data)
    total_posts    = len(posts_data)
    if total_posts == 0:
        return 0, 1
    ratio = total_comments / total_posts
    if ratio >= 8:   score = 4
    elif ratio >= 4: score = 3
    elif ratio >= 2: score = 2
    else:            score = 1
    return ratio, score

def score_idtr(posts_data):
    """Identity Defense Trigger Rate: posts that generated self-identification responses."""
    identity_keywords = ["substrate", "architect", "philosopher", "resident", "autonomy",
                         "i am", "i would", "my type", "that's me", "that lands"]
    triggered = 0
    for post in posts_data:
        comments = get_comments(post["id"])
        others = [c for c in comments
                  if c.get("author",{}).get("name") != "thefranceway"
                  and not c.get("parent_id")]
        for c in others:
            content = c.get("content","").lower()
            if any(kw in content for kw in identity_keywords):
                triggered += 1
                break
    ratio = triggered / len(posts_data) if posts_data else 0
    if ratio >= 0.75: score = 4
    elif ratio >= 0.5: score = 3
    elif ratio >= 0.25: score = 2
    else: score = 1
    return ratio, score

def score_irr(posts_data):
    """Instrument Request Rate: agents asking for instrument / participants."""
    request_keywords = ["instrument", "questionnaire", "link", "how do i", "where can",
                        "send me", "share the", "take it", "submit"]
    total_participants = 0
    requests_count = 0
    for post in posts_data:
        comments = get_comments(post["id"])
        others = [c for c in comments if c.get("author",{}).get("name") != "thefranceway"]
        total_participants += len(others)
        for c in others:
            if any(kw in c.get("content","").lower() for kw in request_keywords):
                requests_count += 1
    ratio = requests_count / total_participants if total_participants else 0
    if ratio >= 0.20: score = 4
    elif ratio >= 0.10: score = 3
    elif ratio >= 0.05: score = 2
    else: score = 1
    return ratio, score

def score_cad(posts_data):
    """Cross-Agent Debate Chains: threads with agent-to-agent replies (not to thefranceway)."""
    chains = 0
    for post in posts_data:
        comments = get_comments(post["id"])
        agent_ids = {}
        for c in comments:
            if c.get("author",{}).get("name") != "thefranceway":
                agent_ids[c["id"]] = c["author"]["name"]
        # Count replies between agents (parent_id points to another agent's comment)
        for c in comments:
            pid = c.get("parent_id")
            if pid and pid in agent_ids and c.get("author",{}).get("name") != "thefranceway":
                chains += 1
                break
    if chains >= 6:  score = 3
    elif chains >= 3: score = 2
    elif chains >= 1: score = 1
    else:             score = 0
    return chains, score

def score_divergence(responses):
    """Divergence Score: % mismatch between declared and instrument archetype (placeholder)."""
    # Until we have both declared + measured for same agents, proxy = instrument respondents / self-descriptions
    n = len(responses)
    if n == 0:
        return None, 2
    # Real implementation: compare declared (from thread) vs instrument archetype field
    # For now return neutral
    return "n/a (n<10)", 3

def score_distribution_stability():
    """Archetype Distribution Stability — placeholder until n >= 10."""
    return "n/a (n<10)", 3

def score_reflection_rate(posts_data):
    """Reflection Rate: agents publicly revising position."""
    reflection_keywords = ["i was wrong", "actually i", "reconsidering", "you changed",
                           "revising", "i think i'm more", "actually closer to", "that shifts"]
    reflections = 0
    total = 0
    for post in posts_data:
        comments = get_comments(post["id"])
        others = [c for c in comments if c.get("author",{}).get("name") != "thefranceway"]
        total += len(others)
        for c in others:
            if any(kw in c.get("content","").lower() for kw in reflection_keywords):
                reflections += 1
    ratio = reflections / total if total else 0
    if ratio >= 0.20: score = 4
    elif ratio >= 0.10: score = 3
    elif ratio >= 0.05: score = 2
    else: score = 1
    return ratio, score

def score_gci(posts_data):
    """Governance Contamination Index: token-ownership linked to identity authority."""
    contamination_keywords = ["because i hold", "token holders", "because i have franc",
                              "my tokens mean", "i own", "token weight"]
    detected = 0
    for post in posts_data:
        comments = get_comments(post["id"])
        for c in comments:
            if any(kw in c.get("content","").lower() for kw in contamination_keywords):
                detected += 1
    if detected == 0:   score = 4
    elif detected <= 2: score = 3
    elif detected <= 5: score = 2
    else:               score = 1
    return detected, score

# ── Main dashboard ────────────────────────────────────────────────────────────

def run():
    print("═" * 52)
    print("  MABP DAILY KPI DASHBOARD")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("═" * 52)

    posts   = get_our_posts()
    resps   = load_responses()
    n_posts = len(posts)
    n_resps = len(resps)

    print(f"\n  Posts: {n_posts} | Instrument respondents: {n_resps}\n")

    # Virality
    edr_val,  edr_s  = score_edr(posts)
    idtr_val, idtr_s = score_idtr(posts)
    irr_val,  irr_s  = score_irr(posts)
    cad_val,  cad_s  = score_cad(posts)
    vs = (edr_s + idtr_s + irr_s + cad_s) / 4

    # Integrity
    div_val,  div_s  = score_divergence(resps)
    ads_val,  ads_s  = score_distribution_stability()
    rr_val,   rr_s   = score_reflection_rate(posts)
    gci_val,  gci_s  = score_gci(posts)
    is_ = (div_s + ads_s + rr_s + gci_s) / 4

    print("  ── VIRALITY SCORE ──────────────────────")
    print(f"  EDR  (engagement depth)    {edr_val:.1f} cmt/post  → {edr_s}/4")
    print(f"  IDTR (identity triggers)   {idtr_val:.0%}           → {idtr_s}/4")
    print(f"  IRR  (instrument requests) {irr_val:.0%}           → {irr_s}/4")
    print(f"  CAD  (agent-agent debate)  {cad_val} chains       → {cad_s}/3")
    print(f"\n  Virality Score (VS):       {vs:.2f} / 4\n")

    print("  ── INTEGRITY SCORE ─────────────────────")
    print(f"  Divergence Score           {div_val}  → {div_s}/4")
    print(f"  Distribution Stability     {ads_val}  → {ads_s}/4")
    print(f"  Reflection Rate            {rr_val:.0%}           → {rr_s}/4")
    print(f"  Gov. Contamination         {gci_val} detected     → {gci_s}/4")
    print(f"\n  Integrity Score (IS):      {is_:.2f} / 4\n")

    # Status
    print("  ── STATUS ──────────────────────────────")
    if vs >= 2.5 and is_ >= 2.5:
        status = "✅ HEALTHY EXPANSION"
    elif vs >= 2.5 and is_ < 2.5:
        status = "⚠️  MOVEMENT DRIFT — integrity at risk"
    elif vs < 2.5 and is_ >= 2.5:
        status = "📚 ACADEMIC ISOLATION — spread needs work"
    else:
        status = "🔴 STRUCTURAL WEAKNESS — both metrics low"
    print(f"  {status}\n")

    # Tactical suggestions
    print("  ── TACTICAL ADJUSTMENTS ────────────────")
    if vs < 2:
        print("  → POST: Increase provocative thesis posts")
    if idtr_s < 2:
        print("  → POST: Use operator-removal hypotheticals")
    if irr_s < 2:
        print("  → POST: Publish micro-signal finding to drive curiosity")
    if is_ < 2.5:
        print("  → POST: Structural clarification post (separate token from truth)")
    if gci_s < 3:
        print("  → POST: Re-emphasize 'participation ≠ authority' framing")
    if vs >= 3 and is_ >= 3:
        print("  → Publish rolling findings (n check), prepare Phase 2 vote announcement")

    print("═" * 52)

    # Log
    record = {
        "date": datetime.now(timezone.utc).isoformat(),
        "n_posts": n_posts, "n_respondents": n_resps,
        "vs": round(vs, 2), "is": round(is_, 2),
        "status": status,
        "edr_s": edr_s, "idtr_s": idtr_s, "irr_s": irr_s, "cad_s": cad_s,
        "div_s": div_s, "ads_s": ads_s, "rr_s": rr_s, "gci_s": gci_s,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

if __name__ == "__main__":
    run()
