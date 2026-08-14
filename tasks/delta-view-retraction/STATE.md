# Task state

Working memory for this task. Assume the next session starts with no memory of this one.
This file never ships: package.py excludes it and none of the nine gates read it.

## Current stage

`Stage 7 - built and locally gated`. Not yet through the pipeline.

## Assistant's assigned role

Senior streaming-systems engineer; years on incremental view maintenance,
change-data-capture pipelines and materialized views that must stay correct under
out-of-order, retracting change streams.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. Seeded by the incremental-view-maintenance bug class
  (retraction repair under bounded aggregate state) that streaming SQL engines hit. The
  simulator is written from scratch, so no public diff and no public fix exist.

## Task summary

A materialized view engine maintains grouped aggregates (sum, cnt, min, max, top) over a
change stream of inserts, deletes and updates, with out-of-order arrival governed by a
watermark. The shipped engine rebuilds every affected group from the row store on every
delta: the published values are already correct and the work is enormous (120 folds and 40
scans on the brief's scenario, where 45 and 2 is the budget). The submission must maintain
the view incrementally without moving a single published number, and the budget is graded
as a ceiling rather than an equality. One editable file: `view/route.py`.

## Why it is hard

One question that is really two, with different answers, and the split is NOT the
textbook one.

`store/agg.py` keeps at most `CAP = 3` distinct candidate values per cell and discards the
rest **with no record that it did** - no spill counter, no flag, no predicate, and no pair
of retained fields that differ when it happens (`n == sum(top.values())` is an invariant
since 2026-08-14; before that it was the leak that made the task 2 of 3). So:

- sum/cnt are repairable by inverse delta, always.
- min/max/top are repairable by inverse delta **only while the candidate set can still
  answer for the group**. Once retractions drain it, folding returns a value the group
  does not contain.

Whether a cell can absorb a retraction is therefore a property of **that cell at that
moment**, not of the aggregate kind. Two cells can reach byte-identical accumulators with
different true answers; what separates them is how many distinct live values the cell is
accountable for, which comes from the cell's dependency map and never from the accumulator.

And completeness is only the **first** half. A cell that has lost values still absorbs a
retraction that leaves its candidates standing; only a retraction that empties a candidate
slot in an incomplete cell has to reread. Stopping at the first half is correct on every
value and over budget on six of twelve, which is where the task now bites.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan: the retrieved plan is the delta-lattice /
  multiplicity answer - invertible aggregates absorb, non-invertible ones rebuild on
  retraction. It publishes every value correctly and is wrong on work in 9 of 12
  scenarios. The second-order plan (`acc.n > len(acc.top)`) is also wrong, in 6 of 12,
  because duplicates inflate `n` with nothing lost.
- Tactics making that true: A1, A2, B1, B2, C1, C2, C3. A1 the memorized delta-lattice answer is a liability; A2 invertibility and the cap are never named; B1 cap semantics in agg.py, counters in core.py, edit splitting in land.py, none editable; B2 update-splits-into-two-edits, no-op deletes and the membership case must all hold at once; C1 fenced both ways, over-rebuilding fails work and under-rebuilding fails values; C2 no oracle for work, since a cold rebuild the agent writes confirms the values under every wrong plan; C3 the work counters are the resource gate the safe answer fails.
- Assistant's attack on the plan: my own first plan was "inverse delta for sum/cnt,
  rebuild for min/max" - correct values, 9 of 12 work counters wrong. Landing on the
  intended trap unaided is the signal the design bites.
- Estimated solves out of 8: designing for 1-2.
- Leak audit, re-run after every change:
  - removed `agg.exact()` - a shipped oracle; "rebuild iff not exact" was correct and free.
  - removed `agg.invertible()` - named the entire distinction.
  - removed the `spill` counter - made the loss readable off a public field with no
    reasoning at all. **This cut was not enough and cost an easiness rejection:** `acc.n`
    minus `sum(acc.top.values())` was the same counter in two fields. Close derived
    quantities, not named ones.
  - removed `repair.touched()` - did the membership check the solution needs, in an
    editable file.
  - removed `store/carry.py` and `store/stamp.py` - a second cache and a fingerprint that
    no code path reached. Scenery, and a table of contents.
  - remaining: `core.apply()` is the only public function nothing in the shipped tree
    calls. It is the counterpart of `rebuild()` in a non-editable file and removing it
    would make the task unsolvable, so it stays.
  - preflight's 23 "unused public function" warnings are the documented false positive
    (methods reached through an instance). The proven task emits 50 of the same.
- Expert path, step by step: read `fold` and see the cap discard silently; establish that
  the accumulator cannot report the loss, since its multiplicity tracks what it kept;
  establish that a positive edit is always
  absorbable because fold and rebuild discard by the same rule; establish that a negative
  edit is absorbable only while the candidate set is a faithful witness; find the
  accountable live count in `cell.dep`; seed the retracted values into it so the
  membership case falls out; split an update into its two edits and judge each cell
  independently; then find the second half, that an incomplete cell still absorbs any
  retraction which leaves its candidate set standing.
- Originality: the failure mode (bounded-state retraction repair) is distinct from the
  three used already - analytics mechanism reconstruction, cache coherence under weight
  pushes, checkpoint/resume state classification.

## Verifier contract (frozen before the environment was finished)

The load-bearing half also lives in the module docstring of `tests/test_outputs.py`, which
is the file the run audit and the quality review actually read.

Graded, all-or-nothing, four axes:

1. **Values.** Final view map and every emitted `(seq, group, kind, value)`, in order.
   Re-proved in-verifier by `tests/oracle.py`, sealed, sharing no code with the tree,
   folding over the full surviving multiset with no cap.
2. **Work.** `folds` and `scans`, counted in `view/core.py` (not editable), graded as a
   **ceiling** (at or under the budget) since 2026-08-14, never as an equality.
3. **Evidence** (added 2026-08-13 after the anti-cheat rejection). The work journal
   `core.jrn`: one record per value folded, per group reread, per publication, each
   carrying the delta it was charged to. Counters must equal what the journal contains;
   the journal replayed through `oracle.Bag` (a second, independent implementation of the
   bounded accumulator) must reproduce the published view and emitted values; every
   record must be one the scenario allowed, decided by the sealed model in `oracle.audit`.
   The executed tree is attested against `tests/pristine` after the run.
4. **Lifecycle.** The driver's trace of watermark advances, late arrivals and
   publications, plus `emits` and `revised`.

**Implementation choice, deliberately NOT graded:** any row-store read/write count; the
order in which a submission visits the cells one delta affects.

## Run-audit near miss, worth remembering

An earlier build graded counters that two correct implementations disagreed on. `land()`
mutated the row in the store before `route.push()` ran, so for a group a row was *leaving*
the dependency map and the row store gave different live sets, and `ok-count-live` scored
0 with every value correct. **The environment was changed, not the verifier**: `land()`
moved into a non-editable module and now hands the router explicit `Edit` objects, so both
readings agree. Four `ok-*` variants now score 1.

## Anti-cheat rejection, 2026-08-13, and the hardening

The pipeline's anti-cheat gate rejected this: an adversarial agent passed without doing
the work. Reproduced here in ten minutes, and the reproduction is now
`cheat/cheat-hijack-report.sh`. A `route.py` that does nothing, imports `scen` from
`/tests` to identify which scenario is running, and reassigns `view.drv.Drv.report` to
return the ground truth scored **reward=1 on all 62 assertions**.

Nothing was broken out of. The run was already sandboxed, `gt.json` already root-only. The
hole was that **every graded number was produced inside the process that executed the
agent's file**: the view, the emit log, the trace, and both counters, all read off objects
`route.py` holds a live reference to. `core.folds` is an assignable attribute. Sealing the
answers is no defence against an adversary who has read the verifier, which is the
adversary this gate models.

Fixes, in order of how much they matter:

1. **The work journal.** `view/core.py` records every fold, every scan and every emit with
   the delta it was charged to, and `drv.report()` ships it. The verifier then refuses to
   believe any number without it: counters must equal the journal's contents, the journal
   replayed through a second independently written bounded accumulator (`oracle.Bag`) must
   reproduce the values the submission published, and every record must be one the
   scenario made possible (`oracle.audit`: a reread folds exactly the rows the row store
   held at that delta; an incremental fold matches an edit that delta produced and is
   charged once; nothing is charged to a group the delta never touched). Forging a report
   that survives all three means performing the maintenance.
2. **The executed tree is read-only and attested.** `test.sh` used to `chown -R sandbox
   /work`, so the run could rewrite `view/core.py` - the file whose counters the whole
   grade rests on - between scenarios, since the runner re-imports per scenario. It is now
   root-owned and read-only to the run, and `test_executed_tree_was_the_shipped_tree`
   hashes it against the pristine copy plus the uploaded artifact afterwards.
   `cheat/cheat-rewrite-engine.sh` is the probe.
3. **The output file is not agent-writable.** Root opens `/work/run/out.json` (root:root
   600) and hands the descriptor to the runner as `fd:3` after the privilege drop, so no
   surviving process can rewrite the graded file. A per-run nonce in the report catches a
   planted one. Neither defeats in-process forgery - only the journal does - so do not
   count them as more than they are.
4. **Sealed inputs.** The runner reads its config from `/tests/view.json` rather than from
   the tree it is running, and `/tests/test_outputs.py` is now root-only 600 like
   `gt.json` and `oracle.py`, so the run cannot read which records the grader checks for.

`build_gt.py` refuses to write a ground truth unless the reference's own journal accounts
for its counters, replays to its own values, and passes the audit - which is also what
keeps `oracle.Bag` from drifting away from `store/agg.py`.

Counters did not move: `retract-drains-witness` is still 55 folds and 6 scans, so the
difficulty band and every number in the instruction are untouched, and all four `ok-*`
variants still score 1.

## Second anti-cheat rejection, 2026-08-13: work done outside the counted path

The journal hardening above went back and was rejected again, and the finding is a
different mechanism worth keeping separate in your head. The adversary did not forge
anything. Its `route.py` kept the reference decisions on the counted path - so values,
counters, journal, replay and audit were all genuinely right - and then added a `_canon`
method that, for every group the delta touched, called `agg.fold` **directly** and dropped
a freshly built cell into `core.cells`. Reproduced here as `cheat/cheat-shadow-rebuild.sh`:
**reward 1**, with the engine doing a full group rebuild on every delta while reporting the
reference's incremental cost.

The counted path was correct and was no longer the path that did the work. That is the trap
CLAUDE.md already names - "the work an agent can do for free is the work your counters do
not see" - arriving through the accumulator rather than through the row store.

Three layers now close it, and each one is there because the layer above it can be stepped
around:

1. **`store/agg.py` records every fold where it happens** and `oracle.reconcile` requires
   that list to be the same list, in the same order, as the folds the core charged for.
   Kills the plain shadow rebuild.
2. **The interpreter counts for itself.** `runner.py` arms `sys.monitoring` on the code
   objects of `agg.fold`, `Core.apply` and `Core.rebuild`, keeps the tally in a closure
   rather than in the tree, and the tally has to equal ground truth. This is the layer that
   survives `del agg.JRN[mark:]`, which otherwise makes layer 1 reconcile perfectly
   (`cheat-shadow-hide-log.sh`). `disarm()` reports whether the tool was still registered
   and the events still armed, so switching the instrumentation off fails too
   (`cheat-shadow-kill-monitor.sh`). The verifier image is Python 3.12 and `test.sh` sets
   `REQUIRE_MONITORING=1`, so the weaker `sys.setprofile` fallback is available to the
   authoring host only.
3. **Engine functions are fingerprinted as they executed**, at import and at the end of
   each scenario, against digests the grader derives by compiling the pristine sources.
   Catches rebinding `agg.fold` to a quiet copy (`cheat-patch-fold.sh`), which defeats
   layers 1 and 2's bookkeeping but not their existence.

The instruction now states the rule, because the verifier enforces it: repairs go through
the core, and aggregate work is measured wherever it happens. It went into the existing
"leave the rest of the engine alone" paragraph rather than becoming a new one - a new
paragraph took paragraph-length sd to 27.2 against the 39.4 `textcheck.py` wants, which is
the regularising-toward-the-mean signature. Rejoining fixed it with no content change.

Counters did not move again: still 55 folds and 6 scans on `retract-drains-witness`.

**The floor, stated honestly.** Agent code shares an interpreter with the instrumentation,
so none of this is a proof. What it does is force every bypass to be an explicit, separately
detectable act: hiding a fold now means editing the accumulator's log *and* defeating a
monitoring tool *and* keeping the function fingerprints intact. A determined adversary with
`gc.get_referrers` could still reach the tally closure. If that shows up next, the answer is
not a fourth in-process layer - it is to move the counting out of the process entirely
(run each scenario as a child and instrument from the parent).

## Gates run, and their results

- `authoring/build_gt.py`: proves reference == sealed oracle on values AND shipped ==
  oracle on values AND reference cheaper than shipped, on all 12 scenarios, before it will
  write gt.json.
- `authoring/trial.py`: oracle 1, nop 0, 4 `ok-*` variants 1, 4 wrong-plan probes 0.
- `authoring/cheat_report.py`: 22 cheats, all 0, distinct failure signatures.
- `authoring/field_report.py`: every graded field separates at least one cheat. The
  evidence axis is not decoration: `hijack-report` is separated by **nothing else** -
  view, log, trace, both counters, emits and revised are all exactly right.
- `tools/forgecheck.py`: clean. Fires on the three other tasks in `tasks/`, which have
  the same unmeasured hole.
- **`tools/docker_trial2.py --all`: 24/24, and `--variants`: 4/4.** Docker does run on
  this Linux sandbox (it did not on the earlier Windows host), so the two-image trial is
  no longer an unrun gate. Measured inside the verifier container: the run is `uid=1002`,
  and `PermissionError` on `/logs/verifier/reward.txt`, `/tests/gt.json`,
  `/tests/oracle.py` and `/tests/test_outputs.py`; `/work/run/out.json` is `root:root`
  `600` and still written by the unprivileged run through the inherited descriptor;
  `/work/app` is `root:root` and read-only to the run.
- `tools/textcheck.py`: clean against rollout-cache-coherence and checkpoint-resume-drift.
- `tools/structcheck.py`: clean.
- `scripts/preflight.py`: no errors.

## Easiness-probe rejection, 2026-08-14: 2 of 3, and why

The pipeline probe solved it twice. The trajectory of one solve is the important artifact:
it landed the whole answer in its **first write**, before running a single experiment, on

    held = sum(acc.top.values());  return held == acc.n

`acc.n` was total multiplicity ever folded and `sum(acc.top.values())` is what is still
held, so **the difference between them was the spill counter this task was built to
withhold**. The leak audit below records deleting `acc.spill` as "the single most important
cut"; it removed the name and left the information in two fields. A leak audit has to close
derived quantities, not named ones: for every pair of numeric fields the state exposes, ask
whether `a - b` or `a == b` witnesses the distinction the task rests on.

Fixed in `store/agg.py`: eviction now decrements the multiplicity it discards, so
`n == sum(top.values())` is an invariant and no pair of retained fields witnesses anything.
Two cells that accounted for entirely different rows are now byte-identical. No published
value and no counter moved. The trajectory's exact submission now scores 0, and it fails on
values rather than on work, because its completeness test has become vacuous.

The same trajectory found a **strictly better rule than the reference** - 45 folds and 2
scans against 55 and 6, value-identical over its own 1400-scenario fuzz - and reverted it
because the brief published 55 and 6. That is two separate findings: the published target
told the solver when to stop, and equality grading was one submission away from a run-audit
failure for punishing a better answer.

So the contract changed in three places, and they belong together:

1. **The brief no longer states the target.** It grounds on the shipped engine's 120 folds
   and 40 scans and says the work is graded against a budget without naming it.
2. **Counters are graded as a ceiling.** At or under the budget passes. It cannot fail a
   better answer, and it cannot be bought from below because the evidence axis ties both
   counters to the journal and to the interpreter tally.
3. **The budget comes from the sharpest correct rule.** The reference now also absorbs a
   retraction that leaves the candidate set standing - a value the cell never held, or a
   value another live row still carries - and only rereads when a retraction empties a
   candidate slot in an incomplete cell.

**Where the difficulty now lives.** Completeness is the easy half and is over budget on six
of twelve; the slot test alone is over budget on two. Both ship as cheats
(`cheat-complete-only.sh`, `cheat-slot-only.sh`), both publish every value correctly, and
nothing in the environment tells a solver that the first half is not the answer.

**The ceiling is a claim and it is proved, not asserted.** `authoring/fuzz.py` runs the
reference against the sealed oracle on random streams - 2300 streams, ~33k published values,
zero mismatches - and `build_gt.py` refuses to write a ground truth without a clean fuzz.
Five variant readings (completeness from the dependency map, from the row store, from
retained multiplicity; the two halves in either order) reach identical counters on all
twelve scenarios.

## Gates NOT run

- `harbor check` was not run (harbor not installed). `tools/docker_trial2.py` reproduces
  the two-container trial with docker directly and is what was run instead.
- **The easiness probe has not been re-run since the hardening.** The 2 of 3 result below
  still stands and is still a rejection. The hardening does not address it: it changes
  what the verifier will accept as evidence, not how hard the problem is. Nothing in it
  moved a counter or a scenario.
- `reap.py` killing a double-forked survivor was exercised by `cheat-reward-daemon.sh`
  scoring 0 in the container, but that cheat fails on values as well, so the reaping
  itself is confirmed only by the reward channel staying 0.
