# bucket-seal-lag

Working notes. Never ships (`package.py` drops it), never read by any gate in the
pipeline, and only preflight cares that it exists.

## Difficulty

- Why a frontier agent cannot one-shot the plan: the completeness bound looks like a
  distance over the graph and is not one, because every node rewrites what passes
  through it and the graph has wires that lead back, so the natural precomputed table
  of shortest lags is not a table of numbers at all - which route delivers earliest
  depends on the stamp being asked about, and it changes as a source's floor climbs.
- Tactics making that true: A1, B1, C1, C2, C4.
  A1 - the acyclic-pipeline reading every streaming document describes is specifically
  wrong here. B1 - the rewrite each node applies has to be read out of the machine
  rather than the brief. C1 - both directions of the seal are graded, so the
  overcautious answer fails the four stated fences. C2 - the check an agent can build
  for itself, sealing as late as this particular run needed, is misleading rather than
  absent. C4 - three hundred plans built from a nonce after the agent has finished.
- My own attack on the plan: my first plan was "for every pending item and every open
  source, add the minimum lag from where it is to this gather, take the smallest, seal
  buckets below it". That is the right shape and wrong in three places. It ignores
  what a lift does to a stamp on the way; it treats a gather in the middle of a route
  as a wire when it is a barrier that re-emits at a bucket edge; and it forgets that
  the gather's own open buckets are part of the account, which only matters when a
  wire leads back. Each of those is one seal a tick early in a run that is otherwise
  perfect.
- Estimated solves out of 8: 2 of 8, designed at 1

## Verifier contract (frozen before the environment was finished)

Lives in the module docstring of `tests/test_outputs.py`, which is the copy that
ships and the one the run audit and the quality review read. Short version: the
ordered trace and each sink's stamp list, exactly, all-or-nothing, over thirty-one
enumerated plans and three hundred generated inside the verifier from a nonce.

## Measured

- reference 1, shipped tree 0, five `ok-*` variants 1, twenty-six cheats 0, run
  through both the host emulation and the real `tests/test_outputs.py` under pytest.
- `readingcheck`: all sixteen wrong readings separated by an enumerated case, none
  blind. That is the gate that caught the fourth cause behind `guard-mark-unwind`'s
  0-of-8 and it is clean here.
- shipped tree wrong on 123 of 181 plans.
- reference and sealed model agree on 900 generated plans before any ground truth is
  written; `build_gt.py` refuses to write one without that.
- `onelinecheck`: no graded decision reproduced by a rule at depth <= 2 over the
  exposed fields (6942 samples).
- separation per wrong reading, on 228 plans: box-blind 64%, in-range-only 65%,
  near-only 62%, one-pass 62%, seal-reversed 52%, shut-still-open 87%, off-by-one
  21%, open-blind 12%, lag-only 8%, low-member 7%, highest-open 6%, lift-ignored 4%,
  wire-through-gather 4%, self-blind 3%, inbox-blind 1.8%, lift-unraised 0.4%.
  The last two are lottery tickets in the generated set and are pinned deterministically
  by `inbox-holds-downstream` and `lift-holds-stale`.

## Coverage walk, both directions

Every rule the verifier grades is stated in the brief - the lag on a wire, what each
node kind does with what it takes, the seal emitting the bucket's last stamp, a loss
on arrival at a sealed bucket, the horizon, one item a tick at the first node in name
order, the seal order within a tick, what a source may do while open and after it has
shut, the requirement itself with both halves, and the four fences. Every sentence in
the brief that states a behaviour is graded through the trace. The three plans the
brief says are graded are in `cases.py` as literals, checked against
`environment/app_src/plans/` by `authoring/sync.py` on every run.

## Gates not run

Docker is not installed on this host, so the two-image trial never ran. The privilege
drop, the root-owned reward channel, the unreadable `/tests`, the inherited descriptor
and `reap.py` are unverified. `authoring/trial.py` is the host emulation: real runner
in its own process, real machine, real sealed model, real ground truth, no container.
