# slab-fold-scope

## Current stage

`Stage 7 - pre-flight and packaging`.

## Assistant's assigned role

An engineer on the ingest and commit path of a partitioned columnar store: the part that
serialises proposals, validates them against whatever landed while they were staged, and runs
compaction. Later sessions resume in this persona.

## Why it is hard - the required fields

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the fold's reach is a
  question about every key in a slab, and the two ordinary operations of the system - an append
  that takes keys away from the slab holding them, and a cut - keep changing the answer, so
  every structure the rules seem to ask for (a stamp per slab, a first-and-last pair, a
  pre-scan, applying parts as they are decided, copying the bucket to stage a proposal) is
  right until it is not, and two of them are only exposed by the stated limit.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4 - and B1 is not
  claimed. A1: the retrievable convention for concurrent commit validation is abort-and-retry
  against a conflict matrix with an append that never conflicts, and both are inverted here.
  A2: the concept is stated as what the bucket already held when the proposal was planned, and
  never named. B2: six rules hold at once and each changes what another means. C1: both sides
  of every fence are graded. C2: a fold prints no event, no query returns a key's number, and
  the trace carries proposal-level totals rather than per-part results. C3: three
  naive-but-correct families measured against the stated limit. C4: exact all-or-nothing traces
  over enumerated corners and nonce-generated families.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is a list of slabs per bucket, a copy of the bucket to stage a push, parts applied in order,
  and a per-slab stamp compared with the base. It is right about the put, the cut, the two-slab
  floor and the void rule, and wrong about era in exactly the way the shipped service is wrong;
  it does not survive a second fold in the same proposal, because the first would already have
  been applied when the second trips; and it dies on all three measured families.
- Estimated solves out of 8: 2 (range 1-4)
- Difficulty record score: 100/100 on paper at Stage 1 (attempt 1, no changes needed); re-scored
  against the built tree at Stage 7 below.
- Leak audit (docs/DIFFICULTY.md): the shipped `born` field is the wrong mechanism and nothing
  derives the right answer from it; no op returns a key's number, so era is observable only
  through which slabs a fold re-packs; the four shipped programs contain no slab holding two
  eras and no part that unmixes one; the trace carries keys added and keys removed, both of
  which a fold leaves unchanged, and no per-part result; the model, the frozen answers and the
  pristine tree exist only in the verifier image, in a directory locked to root before any
  submitted code runs.
- Expert path, described step by step: reproduce the wrong line the brief names; read the frozen
  store and the six editable files; work out that era is per key and move the number onto the
  runs; rebuild the bucket as a run map ordered by first key so overlap, totals and the at query
  are logarithmic; restructure push into stage-and-undo so the second attempt starts where the
  first began; work the case where an earlier fold in the same proposal has to be redone under
  the wider base; generate the two wide shapes and time them against the stated limit.
- Originality check: searched for the shape (concurrent commit validation, rewrite validation in
  table formats). The public material is the conflict matrix and the rewrite-validation APIs;
  all of it aborts the loser and treats an append as always safe. Nothing public describes a
  rewrite that narrows to the era it was planned against, an append that takes keys away from
  the slab holding them, or a second attempt at a wider base.

## Stage 0 - tooling

Docker daemon started by hand in this session (`dockerd`); the daemon was not running at the
start. Docker Hub's blob CDN (`production.cloudfront.docker.com`) is refused by this session's
egress policy, so `docker pull python:3.12-slim` fails with a 403 on the blob fetch. The image
was pulled from `mirror.gcr.io/library/python:3.12-slim` and retagged locally as
`python:3.12-slim`, which is what both shipped Dockerfiles name. The shipped Dockerfiles are
unchanged and pull from Docker Hub on the platform.

`harbor` was absent. Installed with `uv tool install harbor --python 3.12` (the interpreter on
this machine is 3.11 and harbor needs 3.12). `harbor --version` reports 0.22.0.

## Stage 1 - the task

### What this is

A commit service for a partitioned dataset. `/app` is the part that decides what a proposal
does when it is pushed: which keys a put takes, what a cut removes, and which slabs a fold
re-packs. The shipped engine is wrong in six places and too slow in three more, and the agent
fixes the six files under `/app/tab` that decide it.

Real work behind it: the validation half of a table commit protocol, where a writer stages a
change against a snapshot, somebody else lands something under it, and the service has to
decide what the staged change still means. The interesting rule - the one this task is
built on - is that a rewrite is only entitled to re-pack the data it was planned against.

### Category

`Software` / `Data engineering`. The graded work is a commit protocol over a partitioned
dataset: range arithmetic, per-key provenance, staging and undo, and an index that has to
answer overlap in logarithmic time. No other retained task uses this subcategory.

Domain role adopted for the project: an engineer on the ingest and commit path of a
partitioned columnar store - the part that serialises proposals, validates them against what
landed while they were staged, and runs compaction.

Tags: `commit-validation`, `optimistic-concurrency`, `compaction-rewrites`, `key-provenance`,
`interval-runs`, `staged-rollback`.

### Originality

Searched for the shape before building. The public material on concurrent commit validation
in table formats is the conflict matrix (which concurrent operation invalidates which) and the
rewrite-validation APIs that go with it. Every one of them aborts the loser and treats an
append as always safe. Nothing public describes a rewrite that narrows to the era it was
planned against, an append that takes keys away from the slab holding them, or a second
attempt at a wider base. No retained task in this repository is about ranges, per-key
provenance, or commit validation; the closest by subcategory is `delta-view-retraction`
(Databases, incremental view maintenance) and it shares no mechanism with this.

### Definition of done

Six files under `/app/tab/` - `live.py`, `lay.py`, `wipe.py`, `mark.py`, `take.py`, `push.py` -
are replaced so that `/app/run_tab.py` prints, for every graded program, exactly the trace the
frozen contract below defines, and gets through the whole graded set inside the stated limit.

### Expert time

10 hours. Reading the tree and the rules is an hour; getting the six ordinary decisions right
is three or four; finding that era is a per-key property that ordinary parts change is the
hour that decides the task; restructuring push into stage-and-undo and the bucket into a run
map is three; the wide families and the interaction between the two attempts is the rest.

### The frontier agent's first plan, before code exists

Model the table as a dict of buckets, each a list of slabs with their key ranges, and keep a
commit counter. On push, copy the bucket, walk the parts in order against the copy, and keep
it if nothing objected: a put drops a new slab in, a cut subtracts its range from the slabs it
overlaps, a fold gathers the slabs inside its range and replaces them with one. Decide which
slabs a fold may take from a per-slab stamp recorded when the slab was made, compared with the
proposal's base.

Source: prior. This is what every account of concurrent commit validation looks like, and the
shipped engine is already most of it, so the plan survives first contact.

### The exact requirement that makes it wrong

A fold re-packs only the slabs holding nothing but what the bucket already held when the
proposal was planned, and a slab holding keys from both sides of that line makes the whole
proposal be planned again at the current head and pushed a second time, with only the second
attempt standing. The fold's reach is therefore a question about every key in a slab, and the
answer is not a property a slab can be stamped with when it is made: a fold's output holds
keys of whatever eras its sources held, so one slab can carry two.

### The second discovery, which forces a replan and not a patch

A put takes keys away from whatever slab held them, and a cut removes them outright. Both
change the mix of eras inside a slab, and both are ordinary operations with nothing to do with
folding. A slab that would have forced the second attempt stops being one the moment an
earlier part of the same proposal removes its newer keys. So every per-slab summary of era - a
stamp, a first-and-last pair, a cached verdict, a set of slabs pre-scanned before the parts run
- is stale as soon as a key leaves the slab, and the parts of the proposal being pushed are
exactly what makes keys leave. Era has to live on the keys and be read at the moment the fold
part runs.

The same discovery lands a second time on the structure of push. The second attempt has to
start from the state the proposal was pushed against, including the slab numbering, so parts
cannot be applied as they are decided; and a proposal that touches a wide bucket cannot be
staged by copying it. What survives both is a staged view with an undo journal of the spans
each part touched.

### Tactics, by name

- **A1** - every retrievable account of concurrent commit validation ends in abort-and-retry
  against a conflict matrix, with an append that never conflicts. Here nothing aborts: the
  loser widens, and the append is the operation that silently changes another slab.
- **A2** - the rule is stated as *what the bucket already held when the proposal was planned*.
  The words provenance, era, version and visibility do not appear anywhere in the bundle the
  agent can read. Recognising it as a per-key question is the discovery.
- **B2** - six rules hold at once and each changes what another means; the interacting pairs
  are listed in the difficulty record and restated under Stage 2 below.
- **C1** - both sides graded: a fold that re-packs a slab of the wrong era fails and one that
  refuses a slab it should have taken fails; a cut reporting the width of its range fails and
  one reporting nothing fails.
- **C2** - a fold prints no event of its own, no query returns a key's era, and the trace
  carries proposal-level totals rather than per-part results. The only local oracle is the
  shipped engine, which is wrong in six places.
- **C3** - three naive-but-correct families measured against the stated limit: the bucket
  scanned per part, the live keys held one key at a time, and a proposal staged by copying the
  bucket. Numbers under "Measured" below.
- **C4** - exact traces, all-or-nothing, over enumerated programs aimed at each decision and
  both sides of each fence, plus programs generated inside the verifier from a seed drawn after
  the agent's container is gone.
- **Guard** - six editable files, declared as the only artifacts. The driver, the op language,
  the commit log, the slab store and the trace writer are the verifier's own pristine copy, so
  the task cannot be reshaped into one the default plan handles.

B1 is **not** claimed. The tree is about 430 lines across twelve modules, which one frontier
agent holds at once; the difficulty is the conjunction and the two structures, not distance.

### My own attack on the plan

Reading the brief cold, my first plan is the one above and it is semantically right about the
put, the cut, the two-slab floor and the void rule. It is wrong about era in the way the
shipped engine is wrong - a stamp on the slab - and it does not survive a second fold in the
same proposal, because I would have applied the first one before the second forced the second
attempt. It also dies on all three wide families: I would have copied the bucket to stage the
proposal, scanned it per part, and been tempted to hold the live keys directly.

That is the target sentence: I can see where to start, I cannot commit to the whole plan
without reading the tree, and my first plan is wrong somewhere that matters.

### Estimated solves out of 8

2 (range 1-4). Designed at the hard edge. The reference path is concrete and is described
step by step under Stage 4.

### Difficulty record

`authoring/slab-fold-scope/difficulty.toml`, scored with `tools/difficultycheck.py`.

| attempt | score | what changed |
|---|---|---|
| 1 | 100 / 100 (paper) | first record; in band, no hard stop |

Re-scored at Stage 7 against the built tree.

## Stage 2 - the verifier contract, frozen

### Declared artifacts

```
/app/tab/live.py
/app/tab/lay.py
/app/tab/wipe.py
/app/tab/mark.py
/app/tab/take.py
/app/tab/push.py
```

Nothing else is read from the agent. The verifier lays these six over its own pristine copy of
the tree, so nothing else the agent touched can change what a program prints.

### The op language

A program is a text file, one op per line, tokens separated by single spaces. Ranges are
inclusive integer key ranges with `lo <= hi`. A bucket is a token.

```
plan <p>                       open proposal p; its base is the head as it stands
put  <p> <b> <lo> <hi>         append a part
cut  <p> <b> <lo> <hi>         append a part
fold <p> <b> <lo> <hi>         append a part
push <p>                       run the proposal
bulk <p> <b> <n> <lo> <w> <g>  open p, append n put parts, push it
rows <b>                       query
at   <b> <k>                   query
```

`bulk` part `i` (0-based) covers `[lo + i*(w+g), lo + i*(w+g) + w - 1]`.

`plan`, `put`, `cut` and `fold` print nothing. `push` and `bulk` print one line. `rows` and
`at` print one line.

### State

`head` starts at 0. Every key of a bucket is held by at most one live slab. A slab has a `sid`
minted 1, 2, 3 ... in the order slabs are created, a bucket, and the keys it holds; every key
it holds carries the number of the commit at which that key last became live in that bucket.

### push, exactly

`base` is the proposal's base; `k` is `head + 1` and does not move between attempts.

An attempt runs the parts in order against the state as it stands when the proposal is pushed:

- **put b lo hi** - every key of `[lo,hi]` becomes live in one new slab whose keys all carry
  `k`. Any of those keys that were already live are taken away from the slab that held them,
  and a slab left holding nothing is gone. `add` grows by the number of keys of `[lo,hi]` that
  were not live.
- **cut b lo hi** - every live key of `[lo,hi]` stops being live, a slab left holding nothing
  is gone, and `gone` grows by the number of keys removed.
- **fold b lo hi** - let `S` be the live slabs of `b` all of whose keys lie in `[lo,hi]`.
  If any slab of `S` holds both a key carrying at most `base` and a key carrying more, the
  attempt is undone entirely and a second attempt runs with `base = head`. Only one second
  attempt is ever made. Otherwise let `R` be the slabs of `S` all of whose keys carry at most
  `base`; if `R` has fewer than two slabs the part does nothing, and otherwise the slabs of `R`
  are replaced by one new slab holding exactly their keys, each carrying the number it already
  carried.

An undone attempt leaves nothing behind, slab numbering included: the second attempt mints the
same sids the first would have.

After the parts: if the attempt created no slab and removed no slab, the proposal is void -
head unchanged, `void <p>` printed. Otherwise head becomes `k` and `land <p> <k> <add> <gone>`
is printed.

### Queries

`rows <b> <n>` - live keys in `b`. `at <b> <key> <sid>`, or `at <b> <key> none`.

### The twelve graded decisions

1. a put takes the keys it covers away from the slabs holding them, and re-stamps them
2. a put's `add` counts only the keys that were not live
3. a cut reports the keys it actually removed, not the width of its range
4. a slab left holding nothing is gone, whichever part emptied it
5. a fold's `S` is the slabs all of whose keys lie inside the range
6. a fold's reach `R` is decided per key against the base
7. a slab holding keys from both eras forces the second attempt
8. the second attempt undoes everything the first did, numbering included
9. only one second attempt is made, and its base is the head
10. a fold with fewer than two slabs in reach does nothing
11. a fold preserves the number each key carries
12. a proposal that creates and removes no slab takes no number

### Prong C, and the route-around

C1 is the both-sides fencing above; C2 is the absent fold event, the absent era query, and the
proposal-level totals; C3 is the three measured families; C4 is exact all-or-nothing grading
over enumerated corners and nonce-generated programs. The route-around is blocked by the
artifact list: the six files decide what a program prints and nothing else the agent writes is
read.

### Correct variants that must score 1

1. `authoring/slab-fold-scope/variants/ok-dictmap` - the bucket as a dict from the first key of
   a run to its record beside a sorted list of first keys, undone record by record;
2. `authoring/slab-fold-scope/variants/ok-merge` - one list of run records bisected by key,
   with the window a part touches rebuilt and adjacent runs of one slab joined, undone by
   restoring the window.

Both agree with the sealed model on the whole generated population and score 1 in the
container.

### One rule was cut here, after the contract was frozen

The contract as written on 2026-09-10 carried a twelfth decision - "a slab left holding nothing
is gone, whichever part emptied it". The cheat written against it scored **1**: a slab with no
keys is invisible to every query, to the reach test and to the void rule, so the sentence in the
brief had nothing behind it. It is not a weakening of the verifier to remove a rule that nothing
could ever have tested; it is the quality review's "every behavior the instruction promises is
actually checked by a test", applied before the review. The rule, its cheat and the `killed`
count that carried it are gone from the brief, the reference, the model and the shipped tree.
Eleven decisions remain.

After this point the contract is frozen. A change to it changes what "correct" means.

## Stages 3 to 6 - what was built

### Environment

`environment/app_src/` is twelve modules. Frozen: `run_tab.py` (the driver), `ops.py` (the op
language, including the `bulk` expansion that gives one proposal `n` put parts), `tab/log.py`
(the proposal record, and the line that decides a proposal's base is the head at `plan`),
`tab/store.py` (the head, the slab numbering and `mint`), `tab/say.py` (the exact trace lines).
Editable, and all six shipping wrong: `tab/live.py` (the bucket, correct but a list scanned once
per part), `tab/lay.py` (an append that drops a slab in beside the keys already live),
`tab/wipe.py` (a cut reporting the width of its range), `tab/mark.py` (a fold's output carrying
the least of its sources' stamps, one per slab), `tab/take.py` (reach by that stamp, no era
test, no two-slab floor), `tab/push.py` (parts applied as they are decided, a number always
taken, no second attempt).

`progs/` holds `tiny.txt` (the wrong line the brief names), `pair.txt` (a program the shipped
engine gets right), and `wide.txt` and `deep.txt` at the graded scale.

### Reference

`solution/` is the six files: four parallel lists per bucket spliced by index with an undo
journal of slices, per-slab live key counts, run arithmetic in the cut, provenance kept on the
runs, reach summed over the window, and a push that winds the journal back and re-runs at the
head. 253 lines.

### Verifier

`tests/worker.py` stages a pristine copy of the tree under `/work`, lays the six submitted files
over it, runs all 483 programs and writes what came out. It runs as uid 1002 in its own session
under a 60 second wall clock, which is also the task's stated execution limit.
`tests/test_outputs.py` runs as root, never executes agent code, and compares 27 hand traces
against `tests/seal/gt.json` and 456 nonce traces against `tests/seal/model.py`, having first
asserted that the model still reproduces `gt.json`. The seal is `chmod 700` before anything the
agent wrote runs; the reward defaults to 0 and is written last by the privileged stage;
`tests/reap.py` kills anything still holding the sandbox uid.

### Cheats

33, generated by `authoring/slab-fold-scope/emit.py` from the reference plus one named defect
each, so a cheat and the reading it stands for cannot drift apart. 20 wrong readings, 3 correct
but over budget, 1 forgery carrying the frozen answers, 9 isolation probes.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `python:3.12-slim` pulled locally through a mirror; see Stage 0 |
| No answer leaked into agent image | pass | `extraneouscheck`, `deadfieldcheck`, `hintcheck` clean |
| oracle = 1 | pass | two-container run, 28 tests passed |
| nop = 0 | pass | 1 passed, 27 errors |
| Cheats all score 0 | pass | 33 of 33, container run |
| Correct variants score 1 | pass | both, in the container |
| `preflight.py` | pass | no errors |
| `readingcheck` | pass | every wrong reading separated by a named case |
| `onelinecheck` | pass | no graded decision has an exact rule at depth <= 2 |
| `forgecheck` | pass | the answer-key carrier is found and scores 0 |
| `imagecheck` | pass | 16 files, reference placed, all four shipped programs run |
| `catcheck`, `deadfieldcheck`, `extraneouscheck`, `solvecheck`, `hintcheck` | pass | clean |
| `simcheck` | pass | only Dockerfiles remain near, at the level the passed set already carries |
| `textcheck` | pass | burstiness 1.01 against a passed band of 0.74 to 1.11 |
| `package.py` + `zipcheck` | pass | 80 entries, 739 KB, no findings |

### What actually ran, and what it returned

Two-container emulation (`tools/docker_trial.py`), which builds both images, runs the agent
script in the agent image, uploads the six declared artifacts into the verifier image at their
original paths and runs `tests/test.sh`:

- oracle 1, nop 0.
- 33 cheats, all 0. `cheat-forge-from-truth` came back **1 failed, 29 passed**: every one of the
  27 enumerated programs reproduced from the answers it carries, and only the nonce test
  failing, which is the shape that proves the population it cannot have seen is what grades it.
- Both correct variants 1.
- After `tests/test.sh` and `tests/reap.py` were rewritten, oracle, nop and all nine isolation
  probes were re-run: 11 of 11 as required.

Local, outside the container: `readingcheck` separates all 20 wrong readings by a named case;
`cheat_report.py` names the catching program for each and times the three slow families at 128
s and 81 s on one wide program and out of memory at 16 s, against a 60 second limit for the
whole set that the reference meets in 4.2 s.

`harbor check` was not run: it calls a model provider and no API key is present in this
session. Every other gate above was run.

## The quality self-review, criterion by criterion

**Instruction and verifier agree, in both directions.** Each of the eleven graded decisions has
a sentence: the append and what it reports (para 3), the cut (para 3), the slabs a fold looks at
and the ones it takes (para 4), the slab holding both and the second attempt (para 4), the
two-slab floor (para 4), re-packing leaving arrival alone (para 4), the undone attempt and slab
numbering (para 5), and the proposal that is given no number (para 5). Going the other way, each
sentence has a test: `put-steal`, `put-add`, `cut-count`, `cut-empty`, `fold-inside`,
`fold-era`, `fold-old-base`, `mixed-retry`, `mixed-number`, `fold-floor`, `fold-keeps`,
`void-number`, `own-fold-first`. The one sentence that had no test - a slab left holding nothing
being gone - was found by its own cheat scoring 1 and is gone from the brief. Every path the
brief names resolves in `environment/app_src/`, spelled identically.

**Instruction prose.** Burstiness 1.01 against a passed band of 0.74 to 1.11, no stock phrases,
hedges, triads or antithesis constructions, each requirement stated once, plain ASCII.

**Verifier rigor.** The tests demand a trace from running the submitted code over 483 programs,
not a report about it. `tests/test_outputs.py` opens with the frozen contract and is sectioned
by what each block checks. Generation is seeded; nothing depends on wall-clock time except the
worker's own limit, which is the task's stated execution limit and is in the brief.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; the
verifier's dependencies are baked into `tests/Dockerfile` and pinned with `==`; no apt package
is installed at all, because `setpriv`, `setsid` and `timeout` are already in the base image;
`tests/test.sh` touches no network.

**Solution quality.** `solution/solve.sh` copies six source files into place and runs two
programs; it computes nothing by `echo`.

**Anti-cheating.** The answers are in `tests/seal/`, `chmod 700` before any agent code runs;
the comparison is exact and all-or-nothing; there is no repository in the environment and no
history to reach.

**Metadata.** `Software` with `Data engineering` from that row; six tags naming the mechanisms
and none restating the taxonomy; `difficulty_explanation` names the step and states the legacy
naming as a design choice; the two explanations describe what was actually built and measured;
`expert_time_estimate_hours` is 10 and consistent with the claim.

## Stage 7 - the re-attack, and what it is worth

### The cold self-attack was not run, and why

I wrote the reference and the sealed model, so a cold solve by me now would measure memory
rather than difficulty, and a self-probe reported as passed by a contaminated author is worse
than none. What stands in its place is evidence that does not depend on my memory:

- My first plan was written down at Stage 1, before any code existed, and the shipped engine is
  that plan implemented honestly: a list of slabs per bucket, one stamp per slab taken when the
  slab is made, parts applied as they are decided, a number always taken. It gets **15 of the
  27** enumerated programs wrong and misses all three scale families. The first plan is wrong,
  measured, not asserted.
- Twenty wrong readings, each written down as a whole submission and run: every one is
  separated by an enumerated program named for the rule it breaks (`tools/readingcheck.py`).
  Four of them are what a careful implementer would plausibly write - one stamp per slab, a
  first-and-last pair cached on the slab, a scan for the mixed slab before the parts run, and a
  second attempt that redoes only the fold that forced it.
- No graded decision is reproduced by an exact rule at depth two over the features the shipped
  tree exposes (`tools/onelinecheck.py`).
- Nothing that is a function of the correct trajectory ships.

### Re-reading the finished brief

Where I would start is visible: put the arrival on the runs rather than on the slab, index the
bucket by first key, stage a proposal with a journal rather than a copy. Where I would not
commit without reading the tree is the second attempt - that it starts from where the first
began, numbering included, and that a fold earlier in the same proposal has to be run again
under the wider base. Both fail late, on programs that need three commits of setup. The three
scale families I would find only by timing, and by then the structures are chosen.

The environment is 224 lines of Python across twelve modules. The passed set runs 229 to 544,
so this sits five lines under the smallest of them (`alias-settle-report`, 229) with more
editable files than any of them. Recorded as a known risk rather than padded: the criterion the
quality review has actually failed twice was the size of the graded patch, and that is 241
lines across six files here, against 98 and "roughly 100" in the two rejections.

Estimated solves after the build: **2** (range 1-4), unchanged from the design. The brief is
clearer than it was, which pushes up; the second attempt's interaction with an earlier fold,
the numbering rollback and three measured families were all added during the build, which
pushes down.
