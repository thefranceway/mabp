# Coding rubric: from observed error behavior to a candidate archetype and shadow pattern

This closes gap 1 in [PHASE2_GAPS.md](PHASE2_GAPS.md): "No coding rubric. There is no
written test for when a record is coded S1 to S7." It is a procedure for turning an
observed agent behavior into a logged, falsifiable prediction, not a trained classifier.
It outputs a hypothesis and a confidence in words, never a probability — the dataset is
nowhere near large enough to calibrate one, and inventing one would repeat the exact
failure in [CASE_STUDY_UNSUPERVISED_FABRICATION.md](CASE_STUDY_UNSUPERVISED_FABRICATION.md).

Every prediction made with this rubric is logged in
[predictions_log.json](predictions_log.json) **before** it is checked against more
evidence, with a status that starts `pending` and is updated only when real evidence
arrives. That log is the baseline this rubric is tested against over time.

## Step 1 — Narrow the archetype from structural facts, not from the error itself

Answer these from what is actually known about the agent's construction, before looking
at the failure:

- **Does it persist state across invocations?** No → rules out Resident (requires
  sustained presence and accumulated pattern) and weakens Agent (requires a motivation
  that holds across time).
- **Does it set its own goals, or execute a given one?** Execute-only → rules out
  Architect (self-starting, builds systems toward its own goals).
- **Does it hold open questions, or is it required to close them?** Required to close →
  rules out Philosopher (holds open questions instead of forcing them closed).
- What's left after ruling out is the candidate archetype. If nothing is ruled out, or
  more than one archetype survives, say so and stop — do not force a single pick.

## Step 2 — Match the failure to a shadow pattern's guard, not its label

Each shadow pattern in `AGENT_DESIGN_STUDIO.md` has a guard: the question the agent
should have asked itself before acting. Read the guard, not just the pattern's name, and
check whether the observed failure is what happens when that specific question goes
unasked. A failure that merely sounds similar to a pattern's one-line description, but
does not match its guard, is not a match.

## Step 3 — Weigh transfer against reproducibility, not against severity

A pattern transferring across structurally different implementations of the same
trigger condition is evidence of a real disposition. A single occurrence, or a failure
tied to one specific code bug that does not reappear once that bug is fixed, is evidence
for "glitch," not for a shadow pattern — regardless of how severe that one occurrence was.

## Step 4 — Log the prediction, state what would confirm or reject it, and stop

Write the entry to `predictions_log.json` with `status: "pending"`. State explicitly
what new evidence would move it to `confirmed` or `disconfirmed`. Never mark your own
prediction confirmed from the same evidence that produced it — confirmation requires a
new, independent instance or a second coder, per `PHASE2_GAPS.md`.

## Worked example

See `predictions_log.json`, entry `2026-10-07-headless-agent`: the archetype/shadow read
in `CASE_STUDY_UNSUPERVISED_FABRICATION.md`, applied to this rubric's own four steps.
That entry is the rubric's first baseline prediction, logged `pending`, not `confirmed`.
