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
scans where 55 and 11 will do). The submission must maintain the view incrementally
without moving a single published number. One editable file: `view/route.py`.

## Why it is hard

One question that is really two, with different answers, and the split is NOT the
textbook one.

`store/agg.py` keeps at most `CAP = 3` distinct candidate values per cell and discards the
rest **with no record that it did** - no spill counter, no flag, no predicate. So:

- sum/cnt are repairable by inverse delta, always.
- min/max/top are repairable by inverse delta **only while the candidate set can still
  answer for the group**. Once retractions drain it, folding returns a value the group
  does not contain.

Whether a cell can absorb a retraction is therefore a property of **that cell at that
moment**, not of the aggregate kind. Two cells can reach byte-identical `top` maps with
different true answers; what separates them is how many distinct live values the cell is
accountable for, which comes from the cell's dependency map.

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
    reasoning at all. This was the single most important cut.
  - removed `repair.touched()` - did the membership check the solution needs, in an
    editable file.
  - removed `store/carry.py` and `store/stamp.py` - a second cache and a fingerprint that
    no code path reached. Scenery, and a table of contents.
  - remaining: `core.apply()` is the only public function nothing in the shipped tree
    calls. It is the counterpart of `rebuild()` in a non-editable file and removing it
    would make the task unsolvable, so it stays.
  - preflight's 23 "unused public function" warnings are the documented false positive
    (methods reached through an instance). The proven task emits 50 of the same.
- Expert path, step by step: read `fold` and see the cap discard silently; notice `n` is
  kept but the discarded values are not; establish that a positive edit is always
  absorbable because fold and rebuild discard by the same rule; establish that a negative
  edit is absorbable only while the candidate set is a faithful witness; find the
  accountable live count in `cell.dep`; seed the retracted values into it so the
  membership case falls out; split an update into its two edits and judge each cell
  independently.
- Originality: the failure mode (bounded-state retraction repair) is distinct from the
  three used already - analytics mechanism reconstruction, cache coherence under weight
  pushes, checkpoint/resume state classification.

## Verifier contract (frozen before the environment was finished)

The load-bearing half also lives in the module docstring of `tests/test_outputs.py`, which
is the file the run audit and the quality review actually read.

Graded, all-or-nothing, three axes:

1. **Values.** Final view map and every emitted `(seq, group, kind, value)`, in order.
   Re-proved in-verifier by `tests/oracle.py`, sealed, sharing no code with the tree,
   folding over the full surviving multiset with no cap.
2. **Work.** `folds` and `scans`, counted in `view/core.py` (not editable).
3. **Lifecycle.** The driver's trace of watermark advances, late arrivals and
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

## Gates run, and their results

- `authoring/build_gt.py`: proves reference == sealed oracle on values AND shipped ==
  oracle on values AND reference cheaper than shipped, on all 12 scenarios, before it will
  write gt.json.
- `authoring/trial.py`: oracle 1, nop 0, 4 `ok-*` variants 1, 4 wrong-plan probes 0.
- `authoring/cheat_report.py`: 14 cheats, all 0, distinct failure signatures.
- `authoring/field_report.py`: every graded field separates at least one cheat.
- `tools/textcheck.py`: clean against rollout-cache-coherence and checkpoint-resume-drift.
- `tools/structcheck.py`: clean.
- `scripts/preflight.py`: no errors.

## Three-agent probe, 2026-08-13: 2 of 3. THIS IS AN EASINESS-PROBE REJECTION.

Run before packaging, three Opus agents in sealed copies of `environment/app_src` with the
instruction and nothing else, graded through the real verifier.

**First measurement was 0 of 3, and it was wrong - my reference was the problem.** All
three agents matched the reference on `folds` in all 12 scenarios and came in *under* it on
`scans`. The cause: my reference called `core.rebuild()` to create a cell that did not
exist yet, which charges a scan for re-reading a group that holds nothing. Two agents
created the cell with `core.cell()` and folded, paying 0 scans for the identical answer.
They were **strictly better than my reference** and were scored 0 for it. This is exactly
the failure CLAUDE.md warns about - "before grading any optimisation counter, ask whether a
better solution than yours would fail it" - and I hit it anyway. The reference was fixed
(a cell that does not exist holds nothing to be stale, so create and fold, never scan),
ground truth was regenerated, and the honest score is **2 of 3**.

The one failure (probe2) under-rebuilt: it absorbed edits it could not answer for, missing
folds and scans on 8 of 12 with every published value still correct. So the fence catches
the aggressive reading, and the two careful readings both found the real predicate.

**Two attempts to widen the band were tried and both reverted, for the same reason:**

1. *Second holder of retired cell state* (`store/hold.py`), the axis CLAUDE.md recommends.
   Abandoned before completion - it adds a second mechanism and length, and there was no
   probe budget left to validate that it moved the rate rather than just the runtime.
2. *Charging store traffic.* The winning solutions call `ms.group()` freely to test
   completeness - probe1 does **360** full store reads against the reference's 57 - because
   only `core.rebuild()` increments `scans`. Counting reads at the store looked like the
   exact fix. It is not: `ok-store-scan`, a correct variant that consults the row store
   instead of the dependency map, disagrees with the reference on the new counter in **11
   of 12** scenarios. Grading it would fail a correct solution, which is the run-audit
   rejection. Reverted.

The honest position: **the counter that would penalise the winning strategy is the same
counter two correct implementations disagree on.** Anything that closes this gap has to
make store traffic implementation-independent first - most plausibly by routing every group
read through a non-editable accessor that the router must call, so all correct readings pay
the same price - and that is a redesign of the environment, not a verifier tweak. Both
solving agents also agree with the sealed oracle on 400 random streams, so they solved the
problem rather than fitting the twelve scenarios.

## Gates NOT run

- **Docker is not installed on this host.** `C:\Program Files\Docker\...` is a stale PATH
  entry; the binary is absent and `dockerd` is not on PATH. So `tools/docker_trial2.py`
  never ran, and the two-image trial is unproven: the privilege drop to uid 1002, the
  root-owned 700 reward channel, the root-only gt.json/oracle.py, and `reap.py` killing
  double-forked survivors are all **unverified in a container**. The isolation cheats were
  graded by the host emulation, which does not enforce any of that, so they prove the
  grader's logic rejects them, not that the sandbox contains them.
- `harbor check` was not run (harbor not installed).
