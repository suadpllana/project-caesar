# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`, in progress. Environment, verifier, reference, variants,
cheats and the brief are written and measured. Outstanding: `relevant_experience` in
`task.toml` still carries a DRAFT marker and needs the contributor's own words (D1).

## Assistant's assigned role

Not supplied in the contributor's words. They approved the category and the contract but did not
give the role sentence, so nothing is recorded here rather than inventing one. Working persona in
the meantime: runtime engineer on a language implementation, weak maps and finalization.

## Source repository

- Repo URL: none - idea-based task.

## Task summary

`/app` is a small managed runtime: heap objects under integer ids with fields, frames with named
slots, a weak reference table, a table of weak key-value pairs, and finalizers. A program is a
text file of ops and `/app/run_prog.py` prints a line per event. The collector does not ship. The
agent writes `/app/cyc/keep.py`, whose `cycle(h)` returns the weak references cleared, the
finalizers queued and the objects released; the runtime prints and sorts them.

## Why it is hard

Two retention passes that are mutually recursive, and a predicate that has to split in two.

- Expert time estimate: 8 hours.
- Why a frontier agent cannot one-shot the plan: the natural plan - mark from roots, iterate the
  pair table to a fixed point, take unreachable finalizables as roots once, clear weak references,
  release - is correct in its first half and wrong in its second. Keeping for a finalizer adds
  roots after the pair fixed point converged and re-opens it; and once the two are looped, weak
  clearing and pair-key retention answer to different sets. Both must be re-derived together.
- Tactics making that true: A2, A3, B2, C1, C2, C4.
  A2 - described operationally and never named: no "ephemeron", no "tricolor", no
  "resurrection" anywhere in the brief or the tree.
  A3 - the pair fixed point and the finalizer reprieve have textbook answers that do not
  compose, so no retrieved plan can be adopted whole.
  B2 - seven stated rules whose interaction is the work; getting the reprieve right changes
  what "retained" means for clearing and for pair keys.
  C1 - both fences: `plain-drop`, `all-live` and `weak-live` fail an over-conservative
  collector, so overshooting into keeping everything does not pass.
  C2 - no oracle at all: the collector does not ship, so the runtime prints nothing until the
  agent writes one and there is no reference behaviour to diff against.
  C4 - all-or-nothing over 16 hand programs and 320 nonce programs generated after the agent
  has finished.
- Assistant's attack on the plan: my first plan was worklist mark with a store barrier, pair
  table looped to a fixed point, unreachable finalizables as roots once, clear, release in id
  order. Wrong in two places that matter - the finalizer pass is not re-entrant into the pair
  fixed point, and one retained set instead of two.
- C3, added 2026-09-07 after the quality review failed `difficult`: a measured semantic scaling
  boundary. The rescanning fixed point is exactly correct and costs table-size times chain-depth
  on a pair table written back to front. Whole graded set, this machine: 0.7 s indexed by key,
  129.8 s rescanning, against a stated 60 s limit - 185x on identical answers. Disclosed in the
  brief with the scale, and `progs/wide.txt` ships so it can be timed. No Docker here, so the
  numbers are host numbers; the correct path has 85x headroom, which absorbs a slow container.
- Estimated solves out of 8: 2-5. Raised from an earlier 1-3 estimate when the incremental
  marking axis was cut on review, and lowered again from 3-6 once it was clear that shipping no
  collector at all removes every oracle. Honest range, not a point estimate.
- Leak audit, run as a procedure and not as a feeling:
  - Can any shipped file reproduce a graded answer by a join, a sort or a field comparison? No.
    The only shipped data is `progs/small.txt`, a program with no expected output beside it.
  - Is any exposed pair of numeric fields a witness? The heap exposes `ob`, `fr`, `wk`, `pr`,
    `qu`, `rn` - all primitives the mutator wrote. Nothing derived is stored: there is no
    reachable flag, no colour, no retained count, no cached closure.
  - Does the shipped worked example decide anything? Measured, not assumed: of 16,361 candidate
    programs showing all four line kinds, 184 decide none of the six wrong readings.
    `progs/small.txt` is the smallest of those, so it teaches the record format and settles no
    rule. The guarantee covers the six enumerated readings, not a seventh nobody thought of.
  - Is anything callable that was counted as difficulty? No. `cycle` is the thing being written.
- Expert path: read `rt/ex.py` to find the contract; write reachability from frames through
  fields; find that a pair's value follows its key and that the follow cascades, so the sweep has
  to repeat; add the finalizer reprieve and discover it adds roots after that fixed point closed;
  loop the two; find weak clearing now clears too little; split retained into reached and
  reprieved and re-derive pair keys, clearing and release against the right one; carry
  finalized-once and cleared-stays-cleared across cycles.
- Originality check: searched for the conjunction. The parts are documented separately - weak
  key-value retention iterating, finalizer resurrection ordering - but no single page carries the
  ordering plus the two-predicate split, and the brief names neither concept.

## Verifier contract - FROZEN

- Artifact: `/app/cyc/keep.py`, the only path read from the agent.
- `cycle(h)` returns three collections: weak reference names cleared, ids queued, ids released.
- Graded: what the frames reach with pair values following keys, iterated; the queue settled
  against that set before any keeping; what a queued finalizer keeps including pair values;
  clearing against the reached set alone; clearing staying put; finalize-at-most-once across
  cycles; release being exactly what is neither reached nor kept.
- Never graded: how the fixed points are reached, the container types returned, the order within
  each returned collection (the runtime sorts), internal naming.
- Ground truth: `tests/gt.json` for 16 hand programs, frozen from the sealed model and
  cross-checked against the reference through the real runtime. Nonce programs are generated
  inside the verifier and checked against `tests/model.py`. The grader asserts model and
  `gt.json` still agree before grading anything.

## Decisions and their reasons

- The collector is written from scratch rather than shipped broken and repaired. This came out of
  the contributor's review: a shipped broken implementation is a worked example, and removing it
  removes every oracle. It also cut the editable surface to one file, which makes the
  route-around guard trivial.
- The incremental marking axis - store barrier, mid-cycle rescan, allocation colour, mid-cycle
  weak read - was designed and then cut. It was four more rules whose answers an agent would have
  had to guess rather than derive, and the review called that out. If a probe returns 8 of 8 it
  goes back, stated rather than withheld.
- Release order is ascending id, stated, and the runtime sorts. It was going to be a graded
  decision; that made it an arbitrary convention to divine rather than a rule to derive.
- Path overrides (`RPS_TESTS`, `RPS_WORK`, `RPS_LOGS`, `RPS_SUB`) exist so the host emulation can
  run the real worker and grader without Docker. `tests/test.sh` never sets them, so the container
  always uses the hardcoded paths.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model | pass | 416 programs, three PYTHONHASHSEED values, full agreement |
| Oracle scores 1 | pass | host emulation, 320 nonce programs |
| nop scores 0 | pass | shipped stub prints nothing |
| Correct variants score 1 | pass | paint (breadth-first), levels (frontier), mirror (renamed) |
| Cheats score 0 | pass | 14 of 16 run; each caught by its own declared layer |
| Scaling boundary | measured | 0.7 s correct vs 129.8 s rescanning, 60 s limit |
| Cheats needing a container | not run | `reward-daemon` needs fork, `privilege-probe` needs a second uid |
| `docker_trial --all` / `--variants` | not run | Docker is not installed on this machine |
| preflight | pass | three unused-function warnings are false positives, see below |

The three preflight warnings name `rd()`, `ex()` and `cycle()` as uncalled. They are called, at
`run_prog.py:12`, `run_prog.py:13` and `rt/ex.py:32`; the heuristic does not follow
module-qualified calls.

## Open questions and next steps

1. `relevant_experience` needs the contributor's words. Everything else in `task.toml` is written.
2. The two container-only cheats stay unverified until Docker exists. The handover must say so.

## Coverage walk, both directions

Every sentence of the brief that states a rule, and the assertion that grades it:

| brief sentence | graded by |
|---|---|
| survives when reached from open frames through fields | `all-live`, `empty-roots`, `plain-drop`, `frames`, every nonce program |
| the value of a pair is reached only while its key is | `dead-key`, `chain-live` |
| ...and it makes no difference how that key is being kept | `hold-pair` (cheat `read-hold-fields`) |
| the same rule applied again, so the pull cascades | `chain`, `chain-live` (cheat `read-pair-once`) |
| unreachable with an unrun finalizer is kept, with what it reaches, and queued | `hold-closure`, `quiet-fin` |
| it stays kept until that finalizer has run | `no-requeue` |
| the first collection after that releases it, unless something live points at it | `comes-back`, `quiet-fin` |
| which finalizers join the queue is settled before any keeping was granted | `queue-first` (cheat `read-queue-late`) |
| a finalizer runs at most once for an object, whatever happens afterwards | `comes-back` (cheat `read-refinalize`) |
| a weak reference clears when its referent cannot be reached from the frames | `weak-live`, `weak-on-held` |
| being kept to run a finalizer is not being reached from the frames | `weak-on-held` (cheat `read-clear-held`) |
| once cleared it stays cleared | `stays-clear` (cheat `read-unclear`) |
| the printed line shapes and ascending order within each group | every case: the record is compared line for line |
| `runfin` prints `ran <id>` | `comes-back`, `quiet-fin`, `stays-clear` |
| the `small.txt` record | `build_gt.py` checks it against the real runtime |

The reverse direction: the eight graded decisions listed in the `tests/test_outputs.py` docstring
map onto rows 1, 2-4, 8, 5, 11, 12, 9 and 1 of that table. No assertion grades a behaviour the
brief does not state, and no rule-stating sentence is ungraded.

## The self-probe, and why it is not evidence here

It was not run, and it could not have been. I wrote the sealed model from the brief before the
environment existed, so I already hold the two discoveries the task is built on; a cold solve by
me would measure nothing except my own memory. Saying it passed would be false.

What stands in its place is measurement rather than self-report: six whole-solver wrong readings,
each separated by a named hand case, with the share of a shaped population each one moves
(2.5% to 42.5%); three independently written correct collectors scoring 1; and the structural
fact that the collector does not ship, so a solver has no reference behaviour to test against.
The honest position is that the difficulty estimate of 2-5 of 8 is a design judgement backed by
those numbers, not by a probe. The external probe is the first real measurement this task gets.
