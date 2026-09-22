# Software / Algorithms - inferring what a lost span of a log must have contained

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `Software`,
subcategory `Algorithms`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: a coordination service keeps an append-only operation log. A crash lost a
contiguous span of entries. What survives is the log before the gap, the log after it, and
periodic digests - a small set of derived counters and a content hash of the state - taken
at stated points, some of them inside the gap.

Mechanism: reconstruct the operations the gap must have contained. Each operation has a
declared effect on the state and on the derived counters; some operations are idempotent
and a repeat of one is indistinguishable from the original in the state but not in the
counters; some are only legal from a state that satisfies a stated precondition, which
constrains where in the gap they can sit.

Graded output: for each gap, one line per inferred operation in order, plus a line naming
the gap as undetermined when more than one reconstruction satisfies every digest, and the
reason it is undetermined. The reason is part of the answer, so an implementation that
finds one valid reconstruction and stops cannot be right by luck.

## The planning attack

The first plan a frontier agent forms: replay the surviving prefix, diff the state against
the first post-gap entry, and emit the operations that close the difference, ordered by
whatever the preconditions allow - a difference-closing search with backtracking.

The rule that breaks it: the counters are not a function of the final state. An idempotent
operation applied twice leaves the state alone and moves a counter, so a reconstruction
that closes the state difference minimally is wrong whenever a digest inside the gap says
more happened than the difference shows. Minimality is not the criterion; agreement with
every digest is.

The second discovery, which forces a replan rather than a patch: a digest taken inside the
gap constrains a prefix of it, so the search is not over whole reconstructions but over
segments between digests - and the segments are not independent, because an operation's
precondition is evaluated against the state its own segment starts from, which earlier
segments decide. An implementation that enumerates candidate sequences and filters by the
final digest has to be rebuilt as a settle over segments carrying forward the states that
remain possible.

The interacting pair to build the difficulty on: idempotent collapse decides how many
operations a counter delta admits, and the precondition rule decides which of those
orderings can exist at all. Settle either one alone and the other's answer changes.

The late case: a gap whose ordinary reconstructions all agree, where the only disagreement
is in a counter a digest does not cover until the last one. A wrong plan passes every
earlier case and fails there.

## Distinctness

Stay off the crowded Algorithms list in `docs/ORIGINALITY.md`: this is not a diff or
longest-common-subsequence alignment, not a dependency resolution, not an interval merge,
not a shortest path, not a cache policy. If your build drifts into aligning two sequences
element by element, you have arrived at the diff archetype and the screen will say so.

Before anything else, read `authoring/submissions.toml`. Two Algorithms tasks are already
there. Do not reuse their substrates, and do not reuse any of their tags - in particular
`diff-alignment`, `revision-history`, `state-reconstruction`, `record-linkage`,
`union-find`. Take a substrate from the roster below that no entry uses, or bring a better
one; never the same substrate twice.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- a coordination service whose operation log lost a span to a crash (the seed);
- a settlement engine deciding which of several partially observed acknowledgement chains
  may be truncated together, where the chains share dependency edges;
- a canonical ordering built from pairwise happened-before reports that contradict each
  other under a stated bound on how far a reporter can be wrong;
- a repair planner deciding the one legal order for a set of corrective actions whose
  preconditions expire while the plan runs.

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

The Algorithms label collects the textbook set, and the screen sees those first. This one
has no name: it is a constraint reconstruction over an append-only log where the evidence
is partly derived (counters) and partly total (hashes), and where the answer includes
saying that the evidence is insufficient. The nearest public material is work on log
recovery and on checkpoint-based repair, which assumes the log is complete and the state is
the truth - the assumption this seed removes.

## What to check before writing code

- The undetermined case has to be reachable and gradeable. Generate the population around
  it deliberately; an unshaped generator will produce gaps that are all determined and the
  second half of the contract will never be exercised (`CLAUDE.md`, 2026-09-06).
- Idempotent collapse is the load-bearing rule. Write the wrong reading down - collapse by
  state, not by counter - and measure what fraction of a shaped population it moves before
  believing it separates.
