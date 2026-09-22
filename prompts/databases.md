# Software / Databases - deferred constraints across savepoints

Paste the block below as the first message of a fresh task-authoring session. It supplies
the seed and the distinctness constraints; `NEW-TASK-PROMPT.md` supplies everything else.

---

```text
Build one Frontier Bench task in this repository, filed under category `Software`,
subcategory `Databases`. Follow `NEW-TASK-PROMPT.md` as the build contract in full: read
`docs/INSTRUCTION-CONTRACT.md` first, then `AGENTS.md`, then `docs/ORIGINALITY.md`,
`docs/DIFFICULTY.md`, `docs/QUALITY-REVIEW.md` and `docs/RULES.md`. Begin immediately, own
every part of the bundle, and ask me only when two materially different meanings of the
task remain after investigation. Never spawn subagents.

This message gives you the seed. It is a starting point with a planning attack already in
it, not a specification: deepen it where the measurements say it is thin, and replace it if
either record below will not reach its floor.

## The seed

Substrate: the statement executor of a single-session store. Transactions run statements,
open and release savepoints, and roll back to them. Constraints are declared over the
tables: some checked at the end of every statement, some deferred to commit, and a
statement can move a constraint between those two modes while the transaction is open.
Referential actions fire inside the statement that triggered them.

Mechanism: decide, for every statement, what the engine reports - the statement succeeded,
it raised on a named constraint and the transaction is in an aborted state, or a deferred
violation was recorded, cleared or restored. The interesting part is what a rollback to a
savepoint does: it restores the data, and it restores the set of outstanding deferred
violations as that set stood at the savepoint, which is not the set the restored data
implies. A violation cleared after the savepoint comes back outstanding; a violation
introduced after it goes away even when the rows that caused it survive through another
path.

Graded output: one line per statement, in order, naming the outcome and - when a raise
happens - which constraint raised and which row it names.

## The planning attack

The first plan a frontier agent forms: keep the rows, keep a set of pending violations,
check constraints at the end of each statement, and on rollback restore a snapshot of the
rows and recompute the pending set from them. Every course on transactions describes
exactly this.

The rule that breaks it: the pending set is savepoint state, not derived state.
Recomputing it from the restored rows is wrong in both directions, and the brief states it
plainly, so the agent will read it, agree with it, and still write the recomputing version
because it is the one the prior supplies.

The second discovery, which forces a replan rather than a patch: moving a deferred
constraint to immediate mid-transaction checks the outstanding set at that moment, in
constraint declaration order rather than in the order the violations were recorded - so
the raise names a different row than the most recent violation, and the outstanding set
has to carry enough provenance to answer that question. An implementation that stores
pending violations as a set of constraint names has to be rebuilt to store what each one
names and when it was recorded, and rollback has to restore that structure rather than
rebuild it.

The interacting pair to build the difficulty on: the savepoint restore rule decides which
violations are outstanding, and the declaration-order check rule decides which of them
raises first. Settle either alone and the other's answer changes.

The late case: a transaction where a referential action inside a statement introduces a
violation of a constraint that is deferred, while the statement's own constraint is
immediate, and a later rollback to a savepoint taken mid-statement is illegal and must be
reported as such rather than performed.

## Distinctness

Stay off the crowded Databases list in `docs/ORIGINALITY.md`: no MVCC, no snapshot
isolation or write skew, no B-tree or LSM, no write-ahead log or crash recovery, no query
planner, no lock manager or deadlock detection, no buffer pool. This task has one session
and no concurrency at all - that is deliberate, and it is what keeps it away from the
neighbourhood every other Databases submission occupies.

Before anything else, read `authoring/submissions.toml`. `delta-view-retraction` is
already there under this label. Do not reuse its substrate or any of its tags -
`incremental-view-maintenance`, `retraction-handling`, `watermark-ordering`,
`change-data-capture`, `bounded-aggregate-state`. `heap-file-replacement` and
`late-dimension-updates` are in the ledger too with their bundles missing; treat storage
layout and slowly-changing dimensions as occupied ground.

Write `mechanism.sentence` in the originality record before you write anything else, and
hold it to the twin test: if that sentence could be the abstract of a tutorial, or could
describe a task someone else plausibly submitted this month, change the design.

Substrate roster, one to a task:
- deferred constraints, savepoints and a mid-transaction mode flip (the seed);
- trigger firing: row-level against statement-level, before against after, with a stated
  recursion depth and a rule for what a trigger's own writes fire;
- unique and exclusion constraints settled under updates that swap values between rows
  within one statement;
- a statement re-checking the rows it already matched when they changed underneath it,
  with a stated rule for which version the statement then acts on.

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

Every Databases submission that reaches for difficulty reaches for concurrency, and the
screen sees a hundred snapshot-isolation tasks. Deferred constraint checking is in the SQL
standard and in two implementations' documentation, and neither settles the savepoint
interaction this seed grades - the documentation says what a rollback restores about data
and is silent about the outstanding set. That silence is the task.

## What to check before writing code

- The savepoint rule must be stated in the instruction, completely, including what happens
  to a violation cleared after the savepoint. It is the contract, not the difficulty; the
  difficulty is what it costs to implement alongside the declaration-order rule
  (`docs/INSTRUCTION-CONTRACT.md`).
- Check that no single editable file can carry all of it. If the whole task collapses into
  one function's bookkeeping, split the engine so the rules meet across modules.
