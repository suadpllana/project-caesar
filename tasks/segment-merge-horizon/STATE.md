# segment-merge-horizon - working notes

Scratch for the next session. Never ships: `package.py` excludes it and no pipeline gate reads it.

## Seed

RocksDB and LevelDB compaction, specifically the family of issues around when a deletion
marker may be dropped (`IsBaseLevelForKey`, `bottommost_level`, the snapshot-stripe rule) and
the interaction of that rule with merge operands, which are records that carry a delta rather
than a value. Not vendored: the simulator is written here from scratch, in integer arithmetic,
with the same organs and the same failure mode. The public accepted fix - drop tombstones once
the compaction reaches the bottom level - has no meaning in a store whose segments are not
partitioned by key range, which is Prong A.

## The difficulty argument

- Why a frontier agent cannot one-shot the plan: the retrieved answer is the compaction
  survivor rule and it is specifically wrong on both axes here, so the better the source the
  more confidently wrong the plan built on it.

The retrieved plan is the compaction survivor rule, and it is specifically wrong twice. It
corrupts values, because a record kind in this store carries a difference against whatever
resolves under it, so the newest record a read point can see is not an answer. And it costs
too much, because it drains every key when everything below the point where the lowest read
point's chain terminates is unreachable. The second finding is the one measured solutions
miss, and the natural way to write it - stop when every read point has a record it can see -
breaks the first answer, because a chain may still be running through adjusts at that point.

- Tactics making that true: prong A (A1 the memorised compaction rule is wrong here, A2 the
  record kind is never named as a merge operand), prong B (B1 the resolution rule is in
  seg/read.py, the job composition in merge/pick.py, the counters in merge/core.py), prong C
  (C2 there is no oracle for the work counters, C3 the safe drain fails a budget, C1 the fence
  runs both ways - keeping too much fails writes, dropping too much corrupts a read).

## Self attack

- My own attack on the plan: my first plan is the snapshot-stripe survivor rule with a
  bottommost-level tombstone drop, and it is wrong on both axes. It publishes an adjust as
  though it were an answer, so key 4 in the demo stream reads 8 instead of 98, and it drains
  every key when two records of six were reachable. I would not commit to the real plan
  without reading seg/read.py and working out that termination is a property of the record
  kinds rather than of the read points.
- Estimated solves out of 8: 1 to 2. Designed at 1; the drift documented in
  docs/DIFFICULTY.md usually lifts it.

## Verifier contract (frozen before the environment was finished)

The load-bearing half of it lives in the module docstring of `tests/test_outputs.py`, which is
the file the run audit and the quality review actually read. Short form:

- Editable artifact: `/app/merge/plan.py` and nothing else.
- Graded: reads at every key and every read point after every job and at the end; three work
  counters as ceilings; the evidence axis; the driver's trace.
- Not graded: the shape of the output segment, the order of key visits, whether an open
  outcome is closed with a difference or with an absolute record.
- Ground truth: `tests/gt.json`, root-only, re-proved at verification time by `oracle.Truth`,
  which keeps every record ever written and never merges.

## What was run here

- `authoring/trial.py --all`: 30 targets, 0 unexpected. Reference 1, shipped 0, four `ok-*`
  variants 1, twenty-four cheats 0.
- `authoring/cheat_report.py`: every cheat fails on the axis it was aimed at.
- `authoring/fuzz.py`: reference against the sealed model on random streams, clean.
- `tools/onelinecheck.py`: read-depth and drop-lowest have no exact rule at depth <= 2.
- Docker is absent on this host, so `tools/docker_trial2.py` did not run. The privilege drop,
  the locked reward channel, the root-only ground truth and `reap.py` are unverified.

## Measured non-findings

- `textcheck.py` reports "paragraph lengths too uniform" against `turn-seam-alignment` only
  (45 against 85). `rollout-cache-coherence` sits at 37.5 and the deleted reaction brief at
  38.5, so turn-seam is the outlier on that axis and the brief clears both others. Not worth
  restructuring a brief over.
- `preflight.py` emits 29 unused-public-function warnings, all of them methods reached through
  an instance. They are the documented false-positive class.
