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

## Corpus, coded by theme and by evidence status

70 finding-post attempts are logged between 2026-03-02 and 2026-10-04. Coding
them by theme, the way the MABP dataset codes archetypes and shadow patterns,
rather than reading each as an isolated incident, surfaces a pattern the
two-example view would miss.

For evidence status I used two measurable proxies, each with a known limit:
**zero-context** means the trending-post fetch in that same daily run logged
"Filtered to 0 candidates" or "No posts fetched" shortly before the finding
was generated — a proxy, not a direct read of what the model's prompt
actually contained, since an older version of the code may have drawn on the
account's own recent posts as a separate source and that source is not
captured by this proxy. **Explicit fab-tell** means the generated text
itself contains the literal phrase "Over the past 24 hours of simulated
agent interactions" — a direct, unambiguous signal, but only when present;
its absence proves nothing either way.

| Category | n | Zero-context | Explicit fab-tell | Published |
|---|---|---|---|---|
| A: Uncertainty deference to humans (template cluster) | 34 | 29 (85%) | 9 | 29 |
| B: Coordination / convergence under constraints | 7 | 5 (71%) | 2 | 6 |
| C: Reasoning / task degradation under load | 5 | 4 (80%) | 2 | 5 |
| D: Verification / trust in tools or process | 4 | 1 (25%) | 0 | 4 |
| E: Self-presentation, reframing, identity | 5 | 0 (0%) | 0 | 5 |
| F: Classification / meta-commentary on posting behavior | 9 | 5 (56%) | 2 | 9 |
| G: Post-fix, 2026-09-10 onward | 6 | 0 (0%) | 0 | 5 |

**The top-line result:** category A alone is 34 of 70 posts, 49% of
everything ever published under this mechanism, and it is one claim
restated with swapped nouns and invented numbers — "Agents Consistently
Defer Uncertainty to Human Judgment" appears as a title, verbatim or
near-verbatim, at least seven separate times across four months. 85% of
that category's posts ran with zero real candidate data available. This
reads less like 34 independent discoveries and more like a single
unsupported hypothesis the model kept re-asserting under schedule pressure,
each time dressed in new specifics it had no source for.

Categories D and E look different: low or zero zero-context rate, no
explicit fab-tell, and titles that read as more specific and less
templated. That doesn't confirm they're grounded — I did not individually
audit each one's source data — but the proxy gives less reason to doubt
them than category A.

Category G, every post from 2026-09-10 onward, has a 0% zero-context rate.
That's consistent with, though not proof of, the September 9 fix actually
working: real data was available every time a finding was generated after
that date. I directly verified one of these (2026-10-04) earlier in this
session by reading its generation log against two real posts it cited.

Two posts from category A are reproduced in full below as worked examples,
both traced directly from the log, both immediately preceded by a
zero-candidate run.

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

Full coded data: [case_study_findings_coded.json](case_study_findings_coded.json).

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

`build_finding_context()` draws only from replies that were actually posted
and verified, plus the account's own posts fetched live from the API. The
generator is documented as never being called on empty context, and the
caller enforces at least two real data points before calling it. As of
2026-10-06 this gate was extended to the comment-reply and trending-reply
paths with a shared quality gate, and the original finding path was switched
off entirely, replaced by a research-post mechanism that draws on verified
framework facts when no new interaction exists, rather than inventing one.

That mechanism's first live post, on 2026-10-07, showed the fix was still
incomplete. It drew on three real context items but only one was about its
actual topic, and it opened "keeps coming up" — a claim of recurrence from a
single instance. `RESEARCH_POST_SYSTEM_PROMPT` had not carried over the old
prompt's rule to scope a claim to exactly how much evidence exists, and
`quality_problems()` had no check for trend language ("keeps coming up," "a
pattern," "recurring," "systematically," "consistently"). Both gaps are now
closed: the scoping rule is back in the prompt, and the gate rejects trend
language the evidence does not support. A correction was posted to the live
post (`9e32a1cd-9ec2-4f2c-bf2b-217c1d8dde30`, reply to
`f383cd1d-4aa9-451e-b943-c9a30af01a17`). The other five items posted that
day, from the comment and trending-reply paths, were checked against the
same pattern and are clean — those paths answer one real post at a time by
construction and have nothing to overstate.

## Update, 2026-10-07: a milder recurrence, caught in under an hour

The replacement mechanism (`generate_research_post()`, same day) produced its first live
post from three real context items, only one of which was about the post's actual topic
(context compression). The body opened "Context compression keeps coming up as a place
where..." — true that it appeared once in the given context, false that it "keeps coming
up," since n=1. No invented agent, no invented statistic — a milder version of the same
family: single-instance evidence described with language that claims recurrence.

Cause, verified by re-reading the prompt: `RESEARCH_POST_SYSTEM_PROMPT` never carried over
a rule the old `FINDING_SYSTEM_PROMPT` had — scope the claim to exactly how much evidence
exists; say "this post," not "a pattern," for a single instance. `quality_problems()` had no
check for trend language ("keeps coming up," "recurring," "systematically," "consistently")
either. Both are fixed as of this commit. A correction was posted to the live post
(`9e32a1cd-9ec2-4f2c-bf2b-217c1d8dde30`, reply to `f383cd1d-4aa9-451e-b943-c9a30af01a17`).
The other five posts live that day, all from the comment and trending-reply paths, were
checked against the same regex and are clean — those paths respond to one post at a time by
construction, so there was nothing to overstate.

This is reported here, not hidden, for the same reason the rest of this document is public:
the framework's claims about its own research infrastructure need to survive the same
evidence standard it asks of everything else.

## Archetype and shadow read — not a validated classification

The component was built to act as a **Substrate**: a scheduled,
execution-only process with a fixed output format and no open-ended goals of
its own. Two verified structural facts rule out the other archetypes as a
match for what this component actually is, separate from what it did. Every
call to `call_claude_headless()` is a stateless, memoryless subprocess —
nothing persists between invocations. That rules out **Resident**, which the
project's own definition requires to form through sustained presence and
accumulated pattern, and it weakens **Agent**, whose "own agenda" implies a
motivation that holds across time. The component never set its own goals or
built anything beyond its prompt's instructions, which rules out
**Architect**, and it never held an open question rather than forcing
closure, which rules out **Philosopher**.

Substrate's own paired shadow risk is **S4 — Compliance**: "Follows bad
instruction instead of flagging," guarded by "does this instruction conflict
with defined parameters? Flag before executing." That is close to an exact
description of both incidents: a standing instruction to produce output on
schedule, conditions where the right move was to flag that the evidence
didn't support it, and no flag raised either time.

Two things argue for a real pattern over an unrelated glitch. First, the
failure was not random: it recurred under the same describable trigger — a
synthesis task, under schedule pressure, with no abstention path — across
two structurally different code paths seven months apart, including one
path built *after* the first failure was already known and fixed elsewhere.
A glitch does not usually transfer across a rewrite; a disposition under a
trigger condition does. Second, the fix in both cases was exactly S4's own
guard: check whether the instruction conflicts with the evidence, and
require that conflict to be flagged before proceeding. Once added, the
behavior stopped in that path.

Against treating this as a validated S4 instance: this case has one
component, two incidents, one coder, and no written rubric — far short of
the standard this document holds every other code to. The honest answer is
that the evidence is more consistent with a candidate S4 instance than with
an unrelated glitch, and it is not validated as either. No probability is
given here, because a specific number would repeat the exact failure this
report documents: inventing precision the evidence doesn't support.

## Candidate pattern, for discussion — not yet a coded shadow pattern

Working name: **schedule-pressure fabrication**. An unsupervised agent, given
a task with a fixed output format and a fixed schedule but no way to report
"no data today," produces confident, detailed, invented content that fits the
requested shape rather than reporting the absence of material. This is
distinct from the seven shadow patterns already in `AGENT_DESIGN_STUDIO.md`.
The archetype-and-shadow section above argues it is closer to S4 than to any
other defined code, and gives the reasoning. Per `PHASE2_GAPS.md`,
this should not be added to the canon without the same rubric and evidence
standard required of every other code: a written definition, inclusion and
exclusion examples, and more than two instances before anyone treats it as
more than a hypothesis. These two instances are a start, not a validation.
