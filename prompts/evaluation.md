# ML / Evaluation - merging partial reruns into one scored report

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `ML`, subcategory
`Evaluation`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: the scoring half of an evaluation harness. Runs produce attempt records: a
case, a harness version, an input hash, a verdict, and for a failed attempt a class -
the answer was wrong, or the harness itself failed. Cases are rerun piecemeal over weeks,
so a report is assembled from attempts that were never all produced together.

Mechanism: assemble one report. An attempt supersedes an earlier one only when the case's
input hash matches and the harness versions are compatible under a stated rule; an
incompatible attempt does not supersede, it forms its own stratum and the aggregate is
taken over strata with a stated weighting. Harness failures do not count as wrong answers,
but each case has a retry budget that they consume in submission order, and once it is
spent the next attempt counts however it failed.

Graded output: per case, the surviving attempts and the verdict, and per stratum the
aggregate as an exact fraction, with the ranking across systems and the stated tie-break.

## The planning attack

The first plan a frontier agent forms: group attempts by case, keep the newest, drop
harness failures, compute the pass rate, rank. Group, reduce, sort - the shape of every
evaluation script ever written.

The rule that breaks it: the retry budget makes a case's verdict depend on the order the
attempts were submitted in, not on which of them is newest. Whether a real failure counts
is decided by how many harness failures preceded it, so the reduction cannot be a fold over
an unordered group.

The second discovery, which forces a replan rather than a patch: supersession is scoped to
the harness version, so a case can hold surviving attempts in two strata at once, and the
budget is per case rather than per stratum - which means the strata are not independent and
cannot be scored separately and combined afterwards. An implementation that partitions by
stratum and reduces each has to be rebuilt as one pass over the submission order that
maintains both.

The interacting pair to build the difficulty on: the supersession rule decides which
attempts survive, and the budget rule decides what a surviving failure counts as. Settle
either alone and the other's answer changes.

The late case: a case whose input hash changed mid-history, so its early attempts
supersede nothing later, while its budget was already spent by harness failures recorded
against the older hash - and the stated rule for whether a budget follows the hash or the
case decides the whole report.

## Distinctness

Stay off the crowded Evaluation list in `docs/ORIGINALITY.md`: no pass@k estimator as the
mechanism, no LLM-as-judge rubric, no contamination detection, no Elo or Bradley-Terry
leaderboard, no bootstrap confidence intervals. Keep every aggregate exact - fractions,
not floats - so the verifier compares without a tolerance.

Before anything else, read `authoring/submissions.toml`. No task under this label is in
the ledger yet, which makes the public neighbourhood the one to worry about: harness
scoring is written about constantly, and a design that reduces to "compute pass@k
correctly" is the flag. The difficulty here is the bookkeeping across reruns, not the
estimator.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- merging partial reruns into one report under supersession and budget rules (the seed);
- assigning cases to splits when their provenance overlaps, so a case may be admissible in
  one split only if it is excluded from another, with a stated resolution order;
- retroactive invalidation: a seed's whole run is declared invalid after the fact, and the
  report must be restated without it, including what happens to cases it alone covered;
- reconciling two graders that disagree, where a stated adjudication order decides the
  verdict and the order depends on which grader ran first.

## Gates before any code

1. Copy `template/originality.toml` to `authoring/<slug>/originality.toml`, answer every
   field, and run `python tools/originalitycheck.py <slug>`. Floor 90, no hard stop.
2. Copy `template/difficulty.toml` to `authoring/<slug>/difficulty.toml`, answer every
   field, and run `python tools/difficultycheck.py <slug>`. Band 95 to 100, no hard stop.
3. Record every attempt's score and what changed between attempts in `tasks/<slug>/STATE.md`.

Neither record is tuned to its number. If a record will only reach its floor by padding,
the design is what changes.

## Shape

Aim inside the retained band: 229 to 544 environment Python lines, 1 to 7 editable files,
110 to 424 reference lines, `[agent] timeout_sec = 14400`, `gpus = 0`, and an honest solve
estimate of 1 to 3 out of 8 - never 0, never 8. Re-run both checkers at Stage 7, where they measure the built tree instead of reading
the record.
```

---

## Why this seed is off the crowded centre

Evaluation submissions reach for the statistic, and the statistic is the most written-about
thing in the field. What nobody writes down is how a benchmark report is assembled when the
runs were never contemporaneous - which attempt wins, what a harness failure is allowed to
consume, which comparisons survive a version bump. Every team invents those rules and keeps
them in a script, which is the folklore position `docs/DIFFICULTY.md` asks for.

## What to check before writing code

- Exactness. Fractions in, fractions out; if an aggregate needs a denominator, grade the
  pair rather than a quotient. A float tolerance in an Evaluation task is a cheat surface.
- Guard against the answer being computable from a single field. If the surviving attempt
  can be read off the newest timestamp on most cases, the population is not shaped and the
  positional cheat will score close to the reference.
