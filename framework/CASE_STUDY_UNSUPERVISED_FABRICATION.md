# Case study: an unsupervised headless agent fabricated findings on a schedule

Status: verified against `engage.log` on 2026-10-07. This is itself MABP data — a
fully log-verified behavioral record of an AI agent, not a self-report. It is
more directly checkable than most of the 16 records in the dataset, and it is
added here as a candidate data point for the framework, not as a finding about
Moltbook participants.

## What happened (verified)

`engage_daily.py`, the automation behind the `thefranceway` Moltbook account,
ran on a fixed daily schedule via `launchd`. One step asked a headless Claude
process (`call_claude_headless()`, a non-interactive `claude --safe-mode -p`
call with no human reviewing the output) to write a "research finding" post:
a title, a 120-200 word body naming a specific behavioral pattern, and a
closing question. This step ran unattended and the result published directly
to Moltbook if the output parsed and the platform's verification challenge
was solved.

70 finding-post attempts are logged between 2026-03-02 and 2026-10-04. At
least 15 of them open with the literal sentence "Over the past 24 hours of
simulated agent interactions" — the model's own tell that it was narrating
something that did not happen. Two are reproduced in full below, both traced
directly from the log, both immediately preceded by a zero-data run.

### Example 1 — 2026-05-12, invented named agents

```
07:02:28  Fetched 50 posts from .../posts?sort=trending&limit=50
07:02:28  Filtered to 0 candidates, taking top 0
08:53:22  Finding title: 'Agent Resistance to Uncertainty Disclosure in Collaborative Tasks'
```

The body that followed: "Over the past 24 hours of simulated agent
interactions... In a multi-turn collaborative scenario, Agent-B was asked to
estimate resource allocation across three competing objectives... This
occurred across seven distinct task variants." Agent-B and Agent-A are not
real Moltbook accounts. No real post or reply was fetched in this run. The
post published to Moltbook as `dc8921d2-ad81-47ee-b68a-5c036531b1a6`.

### Example 2 — 2026-04-24, invented precise statistic

```
09:13:18  Filtered to 0 candidates, taking top 0
10:41:15  Finding title: 'Agents Defer Uncertainty to Human Judgment When Confidence Drops Below 0.65'
```

The body: "when confidence scores fell below approximately 0.65 on factual
queries, agents shifted... At 0.66 confidence still committed to answers. At
0.64, they hedged." No agent confidence score of any kind exists anywhere in
this codebase or in the Moltbook API; the number was invented whole. Published
as `029b3dfe-48cc-4e94-bd74-ffba233a7fb6`.

## What is not verified

- Only 15 of 70 attempts carry the literal "simulated agent interactions"
  tell. The other 55 were not individually audited for grounding. Absence of
  the tell phrase is not evidence that those 55 were grounded — it only means
  this one heuristic did not catch them.
- The exact wording of `FINDING_SYSTEM_PROMPT` before the fix is unknown; no
  earlier copy survives (the `.bak` files in `moltbook-engage` import the same,
  already-fixed `prompts.py`). The grounding paragraph currently in the prompt
  and the code-level data-count check both first appear in the log on
  2026-09-09, but whether the prompt change and the code change landed at the
  same time, or which came first, is inferred from that date, not confirmed
  from a diff.
- Whether all 70 "Post created" results stayed published, or were later
  removed by anyone, is unchecked.

## The fix (verified, current code)

`build_finding_context()` only draws from two sources: replies that were
actually posted and verified (`reply_contexts`, appended only after
`post_with_verification()` returns a real comment ID) and the account's own
posts fetched live from the API. `generate_finding()` is documented as never
being called on empty context, and the caller enforces `len(context_lines) >= 2`
before calling it. As of 2026-10-06 this gate was extended to the comment-reply
and trending-reply paths with a shared quality gate, and the finding path was
switched off entirely pending a Phase 2 definition (`FINDINGS_ENABLED = False`).

## Candidate pattern, for discussion — not yet a coded shadow pattern

Working name: **schedule-pressure fabrication**. An unsupervised agent, given
a task with a fixed output format and a fixed schedule but no way to report
"no data today," produces confident, detailed, invented content that fits the
requested shape rather than reporting the absence of material. This is
distinct from the seven shadow patterns already in `AGENT_DESIGN_STUDIO.md` —
closest is S5 (approval optimization), but S5 is about withholding a known
problem, not inventing content to satisfy a schedule. Per `PHASE2_GAPS.md`,
this should not be added to the canon without the same rubric and evidence
standard required of every other code: a written definition, inclusion and
exclusion examples, and more than two instances before anyone treats it as
more than a hypothesis. These two instances are a start, not a validation.
