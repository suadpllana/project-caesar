# Software / Data engineering - the minimal recompute after a retroactive correction

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `Software`,
subcategory `Data engineering`. Follow `NEW-TASK-PROMPT.md` as the build contract in full:
read `docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: a batch pipeline described as steps, each declaring the partitions it reads and
the partition it writes. The grains differ: some steps are hourly, some daily, some read a
trailing window of several days. Outputs can be pinned - published downstream and not
rewritable. Inputs expire under a retention rule, and when a fine-grained input has
expired a stated substitution allows a coarser materialization to stand in for it.

Mechanism: one source partition is corrected retroactively. Produce the plan that brings
every output back into agreement with the corrected source, in an order that can actually
run, and no larger than it has to be. A pinned output is not rewritten, but everything
downstream of it is still wrong and must be recomputed from the pinned output as it
stands. A step whose expired input has no legal substitute cannot be recomputed at all;
its downstreams take the stated alternative path instead.

Graded output: the ordered plan, one line per step and partition, naming the mode each
runs in - full, from a substitute, from a pinned input, or the alternative path - and a
line for every output that cannot be brought into agreement, with the reason.

## The planning attack

The first plan a frontier agent forms: take the transitive closure of everything
downstream of the corrected partition, topologically sort it, and emit it. This is the
plan every orchestration write-up describes, and it is correct for a pipeline whose steps
all share one grain and whose inputs never expire.

The rule that breaks it: recoverability is decided during the walk, not before it. Whether
a step can run at all depends on whether its expired inputs have a legal substitute, which
depends on whether the substitute was itself produced after the correction - which the
walk only knows once it has reached the step that produces it. The closure is not a set
that can be computed first and ordered afterwards.

The second discovery, which forces a replan rather than a patch: a trailing-window step
turns one corrected day into several corrected downstream partitions, and the window
itself is clipped by retention, so the fan-out of a single correction is not constant and
not knowable from the graph alone. An implementation that expands the closure partition by
partition and then orders it has to be rebuilt as a settle that carries, for each
partition, whether it is recoverable and from what - because that answer changes what the
closure contains.

The interacting pair to build the difficulty on: the substitution rule decides whether a
step is recoverable, and the pinning rule decides which version of its input it recomputes
from. A step can be recoverable from a substitute and still produce a different answer
depending on whether its upstream is pinned, and the minimality requirement means the
wrong choice is not merely slower, it is a different plan.

The late case: a diamond where one arm is pinned and the other is not, feeding a
trailing-window step whose window reaches back past a retention boundary. Both arms
ordinarily agree; there they do not.

## Distinctness

Stay off the crowded Data engineering list in `docs/ORIGINALITY.md`: no watermarks or
late-arriving events, no exactly-once or idempotent-key dedup, no small-file compaction, no
schema evolution, no CDC ordering from a binlog, no shuffle skew. This seed has no
streaming in it at all, which is what keeps it out of the neighbourhood most submissions
under this label occupy.

Before anything else, read `authoring/submissions.toml`. `slab-fold-scope` is already there
under this label and `delta-view-retraction` next door under Databases. Do not reuse their
substrates or any of their tags - `commit-validation`, `optimistic-concurrency`,
`compaction-rewrites`, `key-provenance`, `staged-rollback`, `incremental-view-maintenance`,
`watermark-ordering`. `late-dimension-updates` is in the ledger with its bundle missing;
treat slowly-changing dimensions as occupied ground.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- a batch pipeline planning the recompute after a retroactive correction (the seed);
- deciding which partitions of a backfill may run at once when a step appends rather than
  replaces and a lease bounds how many writers a partition admits;
- settling which of several manifests a reader sees when producers commit at different
  grains and one producer's commit is partially visible;
- reconciling a pipeline's declared outputs against what is actually on disk after an
  interrupted run, deciding per partition whether to resume, discard or adopt.

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

Pipelines are written about endlessly, and the writing is about scheduling, retries and
streaming semantics. Retroactive correction under mismatched grains is the part every team
does by hand and nobody publishes, because the answer depends on local rules - what is
pinned, what expired, what may stand in for what. That is the shape `docs/DIFFICULTY.md`
calls public rules applied to a concrete messy case.

## What to check before writing code

- Minimality must be observable. If a plan that recomputes more still grades as correct,
  the whole difficulty leaks away; state the rule precisely and grade the plan exactly.
- Measure the fan-out before committing to the trailing window: a window that never
  reaches a retention boundary in the generated population makes the late case
  unreachable, and an unreachable case measures nothing.
