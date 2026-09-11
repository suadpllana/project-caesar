# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 1 - Idea intake` (complete; difficulty record scored 100/100, in band)

## Assistant's assigned role

You are a training-infrastructure engineer on a large-model team: the person who owns the
sharded optimizer, the gradient buffers and the checkpoint path, and who gets paged when a
resumed run does not reproduce the run it resumed from. Comfortable with flat parameter
buffers cut into per-rank slices, with optimizer state that is sharded by position rather
than by parameter, with the residual that a bounded update leaves behind, and with the fact
that a checkpoint written under one topology is a sequence of numbers and nothing else.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/TODO (never in environment/);
  names referenced by instruction/verifier left untouched: not applicable - the tree is authored,
  its identifiers are chosen in the legacy register from the start and no upstream name exists
- Proper-noun sweep done? Every provenance-carrying name replaced with a neutral equivalent,
  replacements recorded in the conversion table, built image grepped for the originals: not
  applicable - nothing in the tree comes from a named project
- Upstream-diff check: what an agent learns by diffing against upstream, and why the task
  survives it: not applicable - there is no upstream to diff against

## Task summary

`/app` is the part of a training run that decides what an optimizer step actually changes. A
program is a text file of ops: parameters are declared with a slot count, gradients arrive for
every slot of a parameter, a world size cuts the live parameters into per-rank shards, and each
step lets every rank spend a fixed budget applying the pending gradients of the slots it owns,
in flat order, stopping at the first slot it cannot afford and leaving the rest pending.
Freezes, thaws and world-size changes take effect only at the next step, and a parameter that
enters the map goes in at the end. Checkpoints record the value and moment of every slot in the
map, in flat order, and nothing else.

The shipped engine treats the parameter as the unit - one value, one moment, one pending number
per parameter, shards snapped to parameter edges, a map in declaration order, a restore at the
flat positions the map holds now - and is therefore wrong in six places. Six files under
`/app/opt` are editable; the rest of the tree is frozen and the verifier uses its own pristine
copy of it.

## Why it is hard

The unit of everything here is the slot, and every retrievable account of sharded optimizer
state makes the parameter the unit: placed whole, owned whole, updated whole. A rank stops
inside a parameter, so state has to be per slot; a shard is a count of slots, so ownership
boundaries fall inside parameters; and the flat order is the order parameters last entered the
map, so a checkpoint is a historical artifact and not a function of the parameter set.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the plan its prior and
  its best search result both produce - per-parameter value, moment and pending, a
  parameter-aligned shard cut, an all-or-nothing update, a restore positioned against the live
  map - is coherent, matches every public account of flat sharded optimizer state, and is wrong
  on all four counts here; the correct structure only becomes visible after working out that a
  budget stop leaves a cut inside a parameter, that the cut outlives the boundary that made it,
  and that the flat order a checkpoint was written in is not the flat order standing now.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4.
  A1 the parameter-as-unit prior is a liability at every one of the four decisions it touches.
  A2 the residual rule is stated as behaviour and the concept is never named.
  B2 twelve rules hold at once and each changes what another means.
  C1 both sides of every fence are graded, so overshooting fails as surely as undershooting.
  C2 no query reports a boundary, a stop or a pending gradient, and the only local comparison is
  an engine wrong in six places.
  C3 a measured scale family where the naive walk stays exactly correct and misses the limit.
  C4 exact traces, all-or-nothing, enumerated corners plus nonce-generated families.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was to hold one value, one moment and one pending number per parameter, since a gradient op
  gives every slot of a parameter the same number; to keep trainable parameters in declaration
  order and add their lengths for flat offsets; to cut the flat length into equal contiguous
  shards and walk each shard parameter by parameter applying whole parameters until the budget
  ran out; and to restore a checkpoint at the flat positions the map holds now. That plan is
  wrong four times over and each wrongness is invisible until a specific case: the stop rule
  makes application cover a prefix, not a parameter; the shard cut is a count of slots, so a
  parameter can be owned by two ranks and take two stops in one step; the map is laid at the
  step from re-entry order, so a thaw moves a parameter to the end and every offset after it;
  and the checkpoint's flat order is the one that stood at the save. It is also too slow by two
  orders of magnitude at the stated scale.
- Estimated solves out of 8: 2 (designing for the hard edge of the 1-7 band)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2): attempt 1 on 2026-09-11 scored 100/100, in band (95-100), no hard stop; one warning,
  `gate.measured` not yet true, closed the same day by the measurement below
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet set
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-11 100/100 first
  and only attempt
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing".
  - a query reporting a stop, a boundary, a remaining budget or a pending gradient: no such op
    exists; pending state is observable only through the values and moments a later step leaves
  - the per-parameter value, moment and pending fields the shipped engine keeps: they are the
    shipped mechanism and are wrong, a prefix application cannot be expressed in them, and
    nothing in the tree derives per-slot state from them
  - the example programs under `/app/progs`: they exercise the op language and the one wrong
    line the brief names; none contains a thaw that lands a starved parameter in the last rank,
    a save that straddles a re-lay, or a parameter longer than a shard
  - a stored offset, slot total, shard boundary or pending weight: none is stored anywhere; a
    parameter record carries its length and its state, the map carries order, and every offset,
    boundary and total is derived where it is asked for
  - the sealed model, the frozen answers and the pristine tree: verifier image only, in a
    directory locked to root before any submitted code runs
- Expert path, described step by step:
  1. run the shipped engine on `/app/progs/tiny.txt` and reproduce the wrong line the brief names
  2. read the frozen driver, op table and registry to learn that nothing above `opt/` knows what
     a slot is, so every decision named in the brief is inside the six editable files
  3. work out from the stop rule that an application covers a prefix of a rank's slice, so value,
     moment and pending live per slot and a parameter becomes a list of runs
  4. rebuild the walk so a step costs its stops rather than its shard, by keeping the parameters
     that still carry pending work in map order and entering each rank's slice at its own first
     owned slot
  5. work out that the map is laid at the step and ordered by re-entry, so ownership is a fact
     about the run's history; rebuild the offsets only when the map moves
  6. record the map with every checkpoint and restore each saved slot into the parameter and
     offset that flat position held then, splicing the saved run sequence across boundaries that
     no longer align with the live map
  7. generate wide programs at the stated scale and time the naive walk and the rebuilt one
     against the stated limit
- Originality check: searched 2026-09-11 for public write-ups of sharded optimizer state under a
  changing world size and of flat-buffer checkpoint resharding. The closest public material is
  the universal-checkpointing tutorial of a public sharded-training library and the long-running
  issue that automatic repartitioning under a new world size is unsupported. Both assume the
  checkpoint names its parameters and that the flat order is declaration order, and both apply a
  parameter's update whole; neither describes a per-rank spend budget, a residual left inside a
  parameter, or a flat order set by re-entry. No public write-up of this rule set exists, and no
  retained task in this repository uses this mechanism: the eleven here are reachability under
  disequality, incremental aggregate maintenance, cancellation during unwind, ownership
  coalitions, thread anchoring, deferred focus, publication order, collector reachability,
  commit-time rewrite entitlement, stream emission boundaries and container lifetimes.

## Verifier contract - FROZEN after Stage 2 (2026-09-11)

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: exactly the six files it may edit -
  `/app/opt/cell.py`, `/app/opt/lay.py`, `/app/opt/cut.py`, `/app/opt/walk.py`,
  `/app/opt/tick.py`, `/app/opt/keep.py`. The verifier reads nothing else from the agent's
  container, so the driver, the op table, the registry and the trace writer cannot be
  reshaped: they are the verifier's own pristine copy.
- What is checked: the six files are laid over `tests/pristine/`, every graded program is run
  through the frozen driver, and the printed trace is compared line for line. All or nothing.
  349 programs: 28 enumerated hand programs, one per graded decision plus the must-still-work
  side of each fence, and 321 generated inside the verifier from a seed drawn after the
  agent's container is gone, across nine families.
- Tolerances: none. Exact string equality of whole traces.
- Ground truth, and where it lives: `tests/seal/model.py`, an independent second
  implementation, and `tests/seal/gt.json`, the frozen answers to the enumerated programs.
  `tests/seal/` is `chmod 700` root-owned before any submitted code runs. The grader asserts
  the model still reproduces `gt.json` exactly before it judges anything.

The twelve graded decisions:

 1. the map holds the live parameters, and is laid again only at a step, and only when a
    parameter was declared, frozen or thawed or the world size was set since it was last laid
 2. a parameter already in the map keeps its place; ones newly live go on the end, in the
    order they became live
 3. a parameter leaving the map loses its moments, and keeps its values and what is pending
 4. the shard is ceil(total/ws) slots; the last is short, and one past the world size or past
    the end of the map is empty
 5. a rank walks the slots it holds in increasing flat position with a running total from zero
 6. a slot with nothing pending costs nothing and is passed over untouched
 7. any other slot costs the size of its pending gradient and is applied while the total stays
    within the budget
 8. the first slot a rank cannot afford stops it, and that slot and everything behind it in
    its shard keep what is pending
 9. applying a slot adds the pending to the moment, takes the moment off the value, and
    clears what was pending
10. a gradient reaches every slot of its parameter whether or not the parameter is in the map
11. a checkpoint is the value and moment of every slot of the map in flat order; a restore
    puts each pair back into the slot that flat position held at the save
12. a restore leaves what is pending, the live set, the world size and the budget alone

Prong C, as built: C1 both sides of every fence are enumerated (`spend-all` against
`spend-block`, `spend-zero` against `spend-prefix`, `map-round-trip` against `map-chill`);
C2 a step prints nothing and no query reports a boundary, a stop or a pending gradient, so the
only local comparison is an engine wrong in six places; C3 the two scale families, measured;
C4 exact whole-trace comparison over enumerated corners plus nonce-generated families, with
`test_every_family_is_represented` keeping the population honest. The route-around guard is the
artifact list: six files, everything else pristine.

## Decisions and their reasons

- Category `ML` / subcategory `Training`. The graded decisions are training decisions - what a
  shard of optimizer state owns, what an update leaves pending, what a freeze does to a moment,
  what a checkpoint of a flat buffer means when the topology under it has moved - and the tree
  carries the machinery to match. It is the one row of the guideline table no retained task in
  this checkout occupies.
- Values, moments and gradients are integers throughout. Exact all-or-nothing comparison of
  traces is the grading contract, and a float optimizer would make two correct implementations
  disagree on rounding; the graded quantities here are structural.
- The trace is printed only by the three query ops. A step prints nothing, so a wrong walk is
  invisible until a value or moment run is printed later.

## Measurements

All on this host, one core, Python 3.12 in the emulated tree, against the 120 second wall the
verifier puts on the worker.

- Resource gate, on the shipped programs. `wide` is 12000 parameters over 24.0M slots taking
  20000 steps on 8 ranks; `deep` is 6000 longer parameters over the same number of slots taking
  12000 steps on 12 ranks. The reference settles `wide` in 1.9 s and `deep` in 1.4 s, and the
  whole graded set of 349 programs in 10.0 s. Three readings that are each exactly correct miss
  the limit: each rank walking its shard parameter by parameter takes 386.8 s on `wide` and
  56.4 s on `deep`; the map laid again at every step takes 135.1 s on `wide`; per-slot state
  takes 163.1 s on `wide` and peaks at 4318 MB against the 2048 the task is given. All three
  print exactly the reference's traces on everything they finish - diffed byte for byte.
- Residual risk, recorded honestly: the shard-walk family misses by 3x on a single program and
  by roughly 10x on the graded set, so it is safe on any plausible hardware. The map-laid-every-
  step family misses by 1.13x on a single program and by about 3.4x on the set; on a much faster
  machine it could come inside the limit. It is an exactly correct implementation, so it passing
  would weaken the gate rather than break the verifier.
- Contract cross-check: three implementations written apart - the reference run through the
  frozen driver, the sealed model, and a per-slot model that keeps one cell per slot and walks
  every slot of every shard - agree line for line on 1603 generated programs plus the 28
  enumerated ones.
- Wrong readings: 14, built as asserted patches of the reference. Every one is separated by an
  enumerated case (`tools/readingcheck.py` shrinks each to the smallest program that separates
  it) and each moves between 7.5 and 100 per cent of a 280-program generated population.
- `tools/onelinecheck.py`: none of the three graded quantities - how many slots a rank applies
  on one visit, where a parameter sits after the map is laid, which parameter a restored flat
  position belongs to - has an exact rule at depth two over the fields the tree exposes.
- Additivity: `build_gt.py` re-derives the 28 frozen answers from the sealed model on every run
  and reports any that moved. None has moved since they were frozen.

## Stage 7 re-attack, read cold against the finished brief

Honest, and by an author who already knows the answer, which is why it stands beside the
measured separations rather than in place of them. A self-solve by the author who wrote the
model first would measure memory, so it is recorded as not run.

Reading the final instruction as the probe agent will: the per-slot nature of the state is
stated, not hidden - "the first slot it cannot afford stops it there, and that slot and
everything behind it in the same shard keep what is pending" tells a careful reader that two
slots of one parameter diverge. So the first plan is not naive about that. Where it goes wrong
is everything downstream of it:

- the run structure has to survive a map that moves, because a cut left by a stop sits at a
  flat position the next re-lay shifts, and nothing in the brief says that;
- a freeze and a thaw that both fall between two steps cancel, so the parameter never leaves
  and never loses its moments - a consequence of two stated rules that neither states, and the
  natural implementation drops the moments at the `frz` op;
- `own` asked between a change and the next step is answered against the map that has not
  moved yet;
- a checkpoint written before the map moved means the layout that stood then, so the live
  layout the fast walk is built around cannot answer a restore;
- a slot whose gradients cancelled to zero costs nothing and must be left exactly as it is,
  which separates "a gradient arrived" from "a gradient is pending";
- and the 120 second limit rules out both walking the shard and holding a slot per cell.

None of those is individually beyond a frontier agent. The gate is that all twelve have to be
right at once with no feedback of any kind: a step prints nothing, no query reports a boundary
or a stop, nothing in the tree is a correct example to compare against, and the grading is
all-or-nothing over 349 programs. Every one of the fourteen measured wrong readings moves
between 7.5 and 100 per cent of a generated population, so any single one of them fails tens
of programs rather than one.

Honest estimate after the build: 2 of 8, possibly 3. The instruction did not come to telegraph
the method, the load-bearing facts are still spread across the six files plus the frozen
driver, and the environment did not flatten during debugging - it grew, from 118 shipped lines
to a 337-line reference.

## Shape, measured at Stage 7

`python tools/difficultycheck.py shard-spend-carry` scores 100/100 with the tree built, and
warns that the environment came out at 231 Python lines against 380 declared at Stage 1. The
built number sits inside the retained band all the same - the retained bundles measure 224
(`slab-fold-scope`), 250 (`token-seam-emit`), 279, 300, 314 and 418 - and the number the
`difficult` rubric actually reads, the size of the graded patch, went the other way: 118
shipped lines across the six editable files against a 337-line reference. The drift is in the
Stage 1 estimate, not in the tree.

## Infrastructure

Docker's daemon runs in this session but no image can be pulled: the registry blob CDN
(`production.cloudfront.docker.com`) is refused by the egress policy with a 403 on CONNECT,
and the proxy README says not to route around a policy denial. `harbor` is not installed
either. So `tools/docker_trial.py` cannot build either image here, and the container gates
were run as host emulation instead: `authoring/shard-spend-carry/host_trial.py` lays the tree
at `/app`, the verifier at `/tests`, makes `/work` and `/logs/verifier`, creates the sandbox
uid and runs `tests/test.sh` verbatim. That exercises the privilege drop, the locked reward
channel, the sealed directory, the wall clock, the session and the reaper. What it does not
reproduce is the container boundary and the image build; `tools/imagecheck.py` covers the
second of those by assembling what the image would hold and running the shipped programs
inside it.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | |
| No answer leaked into agent image | not run | |
| `harbor run -a oracle` = 1 | not run | harbor is not installed here; tools/docker_trial.py stands in |
| `harbor run -a nop` = 0 | not run | |
| Cheats all score 0 | not run | |
| `preflight.py` | not run | |
| `harbor check` rubric | not run | needs an API key |

## Open questions and next steps

Stage 2: freeze the verifier contract, then build the tree.
