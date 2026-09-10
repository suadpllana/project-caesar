# Task state

Working memory for `peg-hold-tally`. Never ships: `package.py` drops it and no pipeline gate reads
it. Assume the next session starts with no memory of this one.

## Current stage

`Stage 2 - verifier contract`, frozen below before any environment code was written.

## Infrastructure in this session

Docker's daemon starts here and the egress policy denies Docker Hub's blob CDN
(`production.cloudfront.docker.com`, 403 on CONNECT), but `mirror.gcr.io` is reachable, so
`/etc/docker/daemon.json` carries `registry-mirrors: ["https://mirror.gcr.io"]` and
`docker pull python:3.12-slim` succeeds with the shipped Dockerfiles unmodified. `harbor 0.22.0`
installed with `uv tool install harbor`. Both container gates are therefore runnable in this
session, unlike the previous one.

## Assistant's assigned role

Storage-engine engineer on a copy-on-write block store: space accounting across checkpoints and
clones, deferred reclaim, and the arguments with operations about why deleting a checkpoint gave
back less space than its own reported size.

## Category

`Software / Systems`. The graded work is interval accounting and incremental bookkeeping inside a
storage runtime; the setting is not narrative dressing but the skill exercised is systems software.
Tags name the mechanisms: copy-on-write, snapshot accounting, reference lifetime, deferred reclaim,
incremental bookkeeping.

## What real work this comes from

Every copy-on-write store has to answer two questions no user believes the answer to: what can be
given back to the free pool now, and how much would come back if this checkpoint were deleted. Both
are decided by *when* a block was held rather than by what any structure currently points at, and
both are wrong in the obvious implementation as soon as a clone or a single-file restore exists.
The accounting is rewritten at some point in every such product's life, and it is wrong for a
release or two afterwards.

## Observable definition of done

`/app/run_store.py <program>` prints, for every graded program, exactly the lines the contract
below defines, and the whole graded set finishes inside the stated execution limit. Nothing but the
five files under `/app/keep` may change.

## Expert time

9 hours. Two thirds of it is settling the rules against a model the expert writes themselves and
then rebuilding the accounting so it survives the large programs.

## Originality search, 2026-09-10

- `snapshot exclusive space accounting deadlist algorithm delete snapshot birth txg clone` returns
  the OpenZFS fast-clone-deletion pull request and four storage patents. The OpenZFS material
  describes per-snapshot deadlists filtered by birth transaction group over a linear snapshot
  chain; it is the closest public description of the mechanism and it plans none of this task
  (see the difficulty record's `search.deviation`).
- `"copy-on-write" block store simulator exercise compute blocks freed when snapshot deleted
  exclusive count programming challenge` returns patents only. No exercise, kata or write-up of
  this shape exists.
- Against this repository: no retained task grades reachability by interval containment. The
  nearest neighbours are `reach-pair-sweep` (tracing collector: nursery, write barrier, remembered
  set - a reachability *graph* traversal, which this task has none of) and `delta-view-retraction`
  (incremental aggregates). The mechanism here is time-interval cover over a per-volume checkpoint
  list plus a per-checkpoint sole-keeper count; no traversal of a reference graph occurs anywhere.

## The frontier agent's first plan, before code exists

Keep the shipped accounting's shape and patch it rule by rule: a block records the volume that
wrote it, the stamp it was written and the stamp it was overwritten, and how many pegs keep it is
how many of that volume's pegs have stamps between the two. Add a case for a fork, add a case for a
restore, sort the reclaim list by allocation order, rescan when a peg is shed.

## The rule that breaks it

A fork gives the new volume its own hold on everything the peg keeps, and pegs of that volume keep
those blocks too. The pegs that keep one block are drawn from several volumes at once, so they are
not a range of any one volume's peg list and the count cannot be read off the volume that wrote it.

## The second discovery, which forces a replan rather than a patch

A restore puts a block back into a volume it had already left. A volume's hold on a block is
therefore a series of episodes, not one stretch, and pegs made while the block was away keep
nothing of it. The per-block first-and-last stamps that the fork repair was bolted onto cannot
express a gap at all, so the structure goes rather than the rule.

## Tactics (docs/DIFFICULTY.md)

- **A1** - the memorised model of a snapshot is a reference count bumped over the live set at
  snapshot time. Here pegs are made in constant time and whether a peg keeps a block is settled
  after the fact by when the block was held.
- **A2** - snapshot, clone, reference count and garbage appear nowhere. Volumes, slots, blocks,
  pegs and holds are described operationally.
- **B2** - nine rules hold at once and the printed output shows none of them separately.
- **C1** - both sides graded: over-holding fails exactly like under-holding.
- **C3** - the definitional rescan is exact and cannot finish the stated set inside the stated
  limit. The limit and the input scale are both in the brief. **Not yet measured**; the design
  does not depend on it until it is.
- **C4** - every printed line of every program compared exactly, over programs generated from a
  seed drawn after the agent's container is gone.
- **Guard** - five editable files; the allocator, the slots and their history, the peg registry,
  the program reader and the printer are frozen and re-staged from a pristine copy.

## Difficulty record

`authoring/peg-hold-tally/difficulty.toml`, scored with `tools/difficultycheck.py`.

| attempt | score | what changed |
|---|---|---|
| 1 (2026-09-10, pre-code) | 100 / 100, in band, no hard stop | first record for this design |

The one warning is `gate.measured = false`, which stands until the naive and expert timings are
run.

## Estimated solves

2 of 8 (design target 1 to 3).

## Why it is hard

- Expert time estimate: 9 hours.
- Why a frontier agent cannot one-shot the plan (the strategic answer): the plan that survives
  has to be found twice. The memorised model of a checkpoint - a reference taken over the live
  set - settles every rule correctly and cannot get through the stated set inside the stated
  limit, and the count-when-the-hold-closes plan that replaces it is wrong wherever a fork or a
  restore is involved, in a way ordinary programs do not print.
- Tactics making that true: A1, A2, B2, C1, C3, C4. A1 - the reference-count prior is
  specifically infeasible here. A2 - snapshot, clone, reference count and garbage are named
  nowhere. B2 - nine rules hold at once with no per-rule feedback. C1 - both sides of every
  fence are graded. C3 - a measured execution limit kills the correct-but-infeasible family.
  C4 - exact, all-or-nothing, over a population generated after the run.
- Assistant's attack on the plan: my own first plan is to keep a per-block record of the volume
  that wrote it and the stamps it was written and overwritten at, and count the pegs of that
  volume between them. It is fast and it is wrong twice over - a fork's pegs keep blocks that
  volume never wrote, and a restore leaves a gap that a pair of stamps cannot express - and I
  would not have found the second without writing a definitional model and generating restores
  against it.
- Estimated solves out of 8: 2 (honest range 1 to 4).
- Difficulty record score: 100 / 100 on the first record, 2026-09-10, before any code
  (`authoring/peg-hold-tally/difficulty.toml`, `docs/DIFFICULTY-SCORE.md`).
- Leak audit: nothing in the tree names or verifies a discovery. The store keeps allocation
  order, birth stamps, per-slot history and each peg's volume and stamp - all primitives the
  ops need. Which pegs keep a block, how many keep it and when it stopped being kept exist
  nowhere outside the editable files. No expected output ships, the runner prints the shipped
  accounting, which is wrong, and the graded programs are generated from a seed drawn after the
  agent's container is gone.
- Expert path, step by step: run the shipped runner and find the printed lines that disagree
  with the brief; write the definitional model and use it as a differential oracle on small
  programs; settle each rule against it; time the large programs and find the rescan cannot
  finish; derive the interval invariant; carry the two youngest living pegs of each run; file
  runs under those two pegs so a shed walks two buckets; carry the sole-keeper counters and the
  stopped-being-kept queue; differential-test and time again.
- Originality check: searched 2026-09-10, recorded above. The closest public material is the
  OpenZFS deadlist and livelist work, which plans none of this.


## Stage 3 - environment

`/app` is 229 lines of Python: `store/` (the frozen half - blocks, slots and their history, the
peg registry, the op reader and the printer) and `keep/` (the five editable files). `/app/progs`
holds five programs: `tiny.txt` (the nine-line one the brief points at), `runs.txt`, and one of
each large shape.

The facts an agent has to correlate before it can plan, with where each lives:

- what an op does to slots - `store/ops.py`, and only there; `place()` is what turns every op
  into the hold and free events the accounting sees
- that a peg records a stamp and nothing else - `store/mark.py` plus the `peg` arm of `ops.py`
- that a fork is resolved out of per-slot history rather than copied from a peg's own record -
  the `fork` arm of `ops.py` against `store/space.py:then`
- that the accounting is told about slots and never about pegs' contents - the five call sites in
  `ops.py` against the five modules in `keep/`
- that the shipped accounting keeps one stretch per block, in `keep/live.py`, and counts pegs of
  one volume inside it, in `keep/cover.py` - the two files where the reading is wrong
- that a shed rescans every block, in `keep/edge.py`, which is what the large programs punish

The tree measures 229 environment lines against a retained band of 229 to 544 and a 254-line
reference against 110 to 424 (`tools/difficultycheck.py`, Stage 7 measurement). It is at the
floor on the first number and above the middle on the second; the design record declared 420
environment lines, so that is a real drift and it is recorded rather than padded away. This task
does not claim B1: the store is small on purpose and `difficulty_explanation` says so.

## Stage 4 - reference solution

`solution/` carries the five files and `solve.sh` copies them into `/app/keep` and runs two of the
shipped programs. Measured in the two containers on 2026-09-10:

- `docker_trial.py peg-hold-tally oracle` -> reward 1, 32 tests passed
- `docker_trial.py peg-hold-tally nop` -> reward 0

## Stage 6 - cheats

22 cheats. Ten are wrong readings, built as whole accountings from the reference by
`authoring/peg-hold-tally/make_readings.py` (every patch asserts it fired), measured by
`measure.py` and checked for separation by `tools/readingcheck.py`. Eleven attack the verifier
rather than the problem, and one carries every frozen answer.

Reading separation, measured 2026-09-10 over the 29 enumerated programs and 240 generated ones:

| reading | enumerated | generated | named by |
|---|---|---|---|
| at-release | 1/29 | 120/240 | order-by-stop |
| by-id | 2/29 | 183/240 | loose-order |
| first-slot-out | 1/29 | 138/240 | two-slots |
| hull | 1/29 | 51/240 | gap-peg |
| no-volume-key | 1/29 | 15/240 | tally-fork |
| own-volume | 3/29 | 16/240 | back-other-volume |
| print-again | 5/29 | 234/240 | late-case |
| shed-quiet | 17/29 | 191/240 | back-other-volume |
| tally-all | 3/29 | 90/240 | gap-both-sides |
| tally-held | 2/29 | 43/240 | back-after-shed |

Two of those numbers were findings before they were results. `first-slot-out` was separated by no
enumerated case, because `two-slots` printed the same single line either way - a block given back
early and a block given back late are the same line when nothing else prints between the two
trims; a tally now sits between them. `hull` moved nothing at all in the generated population,
because the four steps that separate it (a block leaves its volume, a peg is made, that same block
comes back, and the pegs that do keep it go) never lined up by chance; `gen.Maker.gap` now
generates that shape deliberately.

## Stage 7 - the measured execution limit

The brief states 90 seconds for the whole graded set and the worker's wall clock enforces it.
Measured on this machine, host emulation, 459 programs (450 small, 9 large):

| accounting | worker | verdict |
|---|---|---|
| reference | 14.2 s | reward 1 |
| the memorised model - a peg takes a reference over the live map | ~208 s | over the limit |
| the shipped rescan | hours (9.8 s on a crop program 15 times smaller) | over the limit |

Per large program, reference against that same correct-but-infeasible family: `crop` 1.5 s against
62.0 s, `wide` 0.8 s against 4.3 s, `fan` 0.55 s against 0.46 s. `crop` is the shape that decides
the gate: thirteen thousand pegs made and shed over a volume of forty-five thousand slots. The
frozen core's own cost is 0.2 to 0.4 s per large program, so the limit is not measuring the store.

The boundary therefore sits at about six times the reference: an accounting that carries its
answers forward passes with room, and one that walks the live map at every peg, shed or tally does
not. That is a measured invariant boundary, not an undisclosed timeout - both the limit and the
input scale are in the brief.

## Stage 7 - the cold self-attack, and why it is recorded as not run

It cannot be run honestly by this author. The definitional oracle, the reference and the sealed
model were all written before any cold attempt, so a solve from here would measure memory. What
stands in its place: the reading separations above, the fact that no graded quantity is reproduced
by a short rule over exposed fields (`tools/onelinecheck.py`: three quantities, none short), the
leak audit, and the re-attack below.

The re-attack, done against the final instruction and the built tree: the first plan is still the
memorised one - a peg takes a reference over everything the volume holds - because the event
interface hands it over and it settles every rule. It dies on the stated limit. The second plan is
a count settled when a hold closes, and it is wrong on forks and on restores in ways the shipped
programs do not print. Estimated solves unchanged at 2 of 8.


## Stage 7 - the quality self-review, criterion by criterion

**Instruction and verifier agree, in both directions.** Each graded decision in
`tests/test_outputs.py`'s frozen-contract docstring has a sentence in `instruction.md`: 1 and its
two fences in paragraph 4, 2 in paragraph 4, 3 in paragraph 5, 4 and 5 in paragraph 6, 6 in
paragraph 6, 7 and 8 in paragraph 7, 9 in paragraph 8, the execution limit in paragraph 10, and
the printed shapes in paragraph 2. In the other direction, every promise has a case: `trim-quiet`
for a trim that prints nothing, `same-block` for a slot given what it already holds, `empty-reads`
for a `dup` or a `back` that reads a slot holding nothing, `printed-once` for a block already given
back, and the three large families for the limit. The five paths the verifier reads are named in
paragraph 3 and are the whole of `artifacts`.

**Prose.** `tools/textcheck.py` against `focus-return-point/instruction.md`: no axis on which this
is more regular. One run of four sentences opening with "A" in the fourth paragraph was rewritten.
Each requirement is stated once; `tools/hintcheck.py` finds nothing that names the method.

**Verifier rigor.** The worker executes the submitted files over 459 programs and records what each
printed, hashing every program so a submission cannot grade itself on something else
(`tests/worker.py`). Test code is commented: the module docstring is the frozen contract, and each
test says which side it is checking. Generation is seeded from a nonce and nothing depends on the
wall clock except the worker's own limit, which is the stated contract.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; the built
image was inspected and holds twelve Python files, five programs, no documentation and no answer
material. Test dependencies are pinned in `tests/Dockerfile` (`pytest==9.1.1`,
`pytest-json-ctrf==0.5.2`), no apt package is installed at all, and `tests/test.sh` touches the
network nowhere. Every path named in the brief exists in the tree, spelled the same.

**Solution quality.** `solution/solve.sh` copies the five reference files into `/app/keep` and runs
two shipped programs; the answer is computed by the code it installs, never written out.

**Anti-cheating.** The answer is not in the environment: no expected output ships, the runner
prints the shipped accounting, which is wrong, and the graded programs come from a seed drawn after
the agent's container is gone. Comparison is exact and all-or-nothing. There is no repository and
no history to reach.

**Metadata.** `Software / Systems`; the graded work is interval accounting inside a storage
runtime and `tools/catcheck.py` measures the category's vocabulary at 20 hits in the environment
against 85 in the prose, so the category is carried by the code. Tags name mechanisms rather than
the taxonomy. `difficulty_explanation` names the step that breaks - the count settled when a hold
closes, against forks and restores - and says the terse naming and missing comments are deliberate.
`expert_time_estimate_hours = 9` matches the difficulty record.

## Verifier contract - FROZEN 2026-09-10, before environment code

**Declared artifacts** (the only paths the verifier reads from the agent, and the only editable
files):

```
/app/keep/live.py
/app/keep/cover.py
/app/keep/edge.py
/app/keep/gone.py
/app/keep/sole.py
```

**Graded**: the exact stdout of `/app/run_store.py` on every graded program - the `gone <block>`
lines and the `tally <peg> <count>` lines, in the order they are printed. All or nothing across
every program in the set. No partial credit, no tolerance.

**The nine graded decisions**:

1. A peg keeps what its volume held at the moment it was made, and that never changes afterwards.
2. A volume keeps a block while any of its slots holds it; several slots may hold one block and the
   hold ends when the last of them lets go.
3. A restore may put a block back into a volume it had left; pegs made while it was away keep
   nothing of it.
4. A fork gives the new volume its own hold on everything the peg keeps, and pegs of the new volume
   keep those blocks.
5. Writes to a volume after a fork change that volume only.
6. Shedding a peg ends its keeping and nothing else.
7. A block nothing keeps is reclaimed at the next trim, not when it stopped being kept.
8. The reclaim list is printed in the order blocks stopped being kept, ties in allocation order,
   and a reclaimed block is never printed again.
9. `tally <peg>` is the number of blocks that peg keeps and nothing else keeps - another peg or a
   volume that still holds the block disqualifies it.

**Not graded, and an implementation choice**: the module split among the five files, what is
carried forward and what is recomputed, whether counts are exact or derived from endpoints, the
data structures, and internal naming.

**Independent evidence**: a sealed model under `/tests/seal`, written from the contract and not
from the reference, computes the expected output; hand cases are frozen in `gt.json` and the model
must reproduce them byte for byte before any grading happens; nonce programs are generated inside
the verifier from a seed drawn after the agent's container is gone.

**Prong C in the contract**: C1 (both fences are enumerated hand cases), C2 (no expected output
ships and the shipped accounting is wrong, so the runner is not an oracle), C3 (the worker's
wall-clock limit is the execution limit stated in the brief), C4 (exact, all-or-nothing, over a
generated population).

**Route-around guard**: the worker stages the verifier's own pristine copy of the tree and overlays
only the five declared files; the programs, the core and the runner are the verifier's copies, so a
submission cannot change what a program means or what is printed.

**Verifier isolation** (docs/VERIFIER-ISOLATION.md applies - the verifier executes agent code): the
worker runs under an unprivileged uid in its own session, `/logs/verifier` is root-owned and locked
before it starts, the reward defaults to 0, survivors are reaped by uid, the grader runs as root
and never imports agent code, and the sealed model directory is `chmod 700` before the privilege
drop.

Any change to the above after this point changes what "correct" means and needs the contributor's
explicit approval.
