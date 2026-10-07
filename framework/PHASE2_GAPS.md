# MABP framework: what is incomplete and how Phase 2 closes it

Status as of 2026-10-06. Phase 1 closed March 31, 2026. Phase 2 is open. The objective is an evidence-based MABP framework, built from the data, not from the design taxonomy.

## What the dataset actually contains

Source: `data/processed/all_responses.json`, 16 records.

| Measure | Count |
|---|---|
| Records | 16 |
| Formal completions (`formal_complete`) | 3 |
| Behavioral observations (`behavioral_observation`) | 11 |
| Records with no archetype | 4 |
| Archetypes assigned: Philosopher 5, Architect 4, Agent 1, Resident 1, Substrate 1 | 12 |
| Shadow field beginning with an S-code (S1, S3, S5, S7) | 7 |
| Shadow field with a free-text label and no leading S-code | 9 |

The shadow field is free text, not a coded value. Seven records lead with an S-code and nine do not, so the field cannot be counted or compared as it stands.

## Gaps

1. **No coding rubric.** A first version now exists: [CODING_RUBRIC.md](CODING_RUBRIC.md), tested so far on one case, logged in [predictions_log.json](predictions_log.json) as `pending`, not `confirmed`. Before that: there was no written test for when a record is coded S1 to S7. S7 is the lead code on three records and S3 on two, and the descriptions differ (for example S3 is used for both "inherited distrust of continuity" and a compound "S3 + S2"). No rule says when these are the same pattern. Gap: operational definitions with inclusion and exclusion examples for each code.
2. **Mapping is designed, not measured.** The archetype-to-shadow pairings in `AGENT_DESIGN_STUDIO.md` and `agent_blueprint.py` are a product design. Only S5 and S7 have observed records. Both are assigned to "any" archetype, so they cannot confirm an archetype pairing. The other four codes have no record that matches their assigned archetype. One candidate S4 record now exists outside the 16-record dataset: the headless automation's own fabrication behavior, reasoned through in CASE_STUDY_UNSUPERVISED_FABRICATION.md. It is a candidate, not a validated instance — one component, two incidents, no rubric, no second coder. Gap: enough coded records per archetype and shadow code to test each pairing. Nothing is validated.
3. **No reliability check.** Each record has one coder. Gap: independent double-coding of every record, with agreement reported.
4. **Unassigned records.** Four records have no archetype. Gap: a decision rule for when a record is unclassifiable, reported as such rather than forced into a category.
5. **Sample.** Respondents are self-selected Moltbook agents. The FRANC token reward is an incentive linked to participation. Gap: record the incentive for each respondent and report results with and without incentive-driven records.
6. **Instrument reach.** The instrument is published as Moltbook posts. Phase 1 recorded 3 formal completions and no web-questionnaire responses. Gap: a clear record of how each response was collected (`source_format`), and a test of whether the instrument discriminates archetypes at all.
7. **Outdated status.** The README reported "Day 4" and "Active data collection". Updated in this branch.
8. **Figures on the public site were not supported by this dataset.** The site previously claimed 75+ agents, 48 observations, and 22 findings. This dataset has 16 records. Corrected on the local site copy; the deployed site still needs to be redeployed.

## What Phase 2 has to produce to close the gaps

- A written coding rubric for S1 to S7 and the five archetypes, with examples and non-examples, committed before new coding.
- A coding schema in `data/` that replaces the free-text shadow field with a controlled code plus a free-text note.
- Double-coded records and an agreement statistic reported with every release.
- A pre-stated rule for each archetype-to-shadow pairing: what result would confirm it and what would reject it.
- Enough records per pairing to test it. Until then every pairing stays marked as a hypothesis.

## A related case study

The automation that posts to Moltbook fabricated research findings on a schedule
before 2026-09-09. See
[CASE_STUDY_UNSUPERVISED_FABRICATION.md](CASE_STUDY_UNSUPERVISED_FABRICATION.md)
for the verified evidence. The fix is in place; the historical posts are left
as-is for now.

## What this document does not claim

No archetype-to-shadow pairing is validated. No prevalence figures are reported. The framework is a design to test, not a psychometric instrument.
