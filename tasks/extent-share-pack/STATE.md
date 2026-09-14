# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - pre-flight and packaging`

## Assistant's assigned role

Storage engineer on the allocator and accounting half of a copy-on-write store: the part that
decides which extent a write lands in, what a clone shares, when an extent is rewritten to the
blocks still in use, and what the two per-volume figures an operator reads actually mean.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repo
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): none
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? The tree is authored, not vendored; identifiers are written in
  the legacy register directly (`st/`, `ext`, `pt`, `pk`, `occ`, `vp`, `vo`). No conversion
  table is needed because no original names exist.
- Proper-noun sweep done? Nothing in the tree names a product, project or person; the domain
  words used (volume, file, slot, extent, block) are generic storage vocabulary.
- Upstream-diff check: not applicable

## Task summary

`/app` is the accounting half of a store that keeps file data in extents. A file is an array of
slots and each slot points at one block of one extent. A write allocates a new extent; a clone
copies pointers, so two volumes can sit on the same extent; a snapshot copies every pointer of a
volume; a trim clears slots; dropping a volume removes all of its. An extent takes up its whole
size for as long as any block of it is pointed at, dies when nothing points into it, and is
rewritten down to the blocks still pointed at when exactly one volume is on it and it is under
half occupied. Three questions are asked of the store: how much a volume is on, how much the
store holds, and how much smaller the store would be if a volume were dropped. The shipped
engine gets the accounting wrong across six files, and answers the third question with the unshared sum, which is not what the question means.

## Why it is hard

The first plan is a reference count per extent and two running totals per volume. Neither
survives the rules, and neither fails on a program anyone would write by hand.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the brief states every rule, but the structure those rules need is not the one they suggest. Occupancy
  is per block and not per pointer, presence is per volume and has to be a tally rather than a
  set, and the drop-gain question reads the other volume's occupancy inside an extent, a figure
  no per-extent or per-volume total holds. A plan committed to reference counts produces a store
  that is right on every program that does not clone a block twice and wrong on every program
  that does.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1 the prior that freeing part of an extent frees part of the space and that an exclusive figure is the unshared sum; A2 the rewrite is described by what it does and never named; B1 the id counter, the print order, the op bodies and the containers are frozen while occupancy, presence, rewriting, the candidate set and the two queries are editable, so the plan is assembled from how they call each other; B2 seven rules that have to hold at once; C1 both sides fenced, an engine that never rewrites fails the first shipped program; C2 no second store and no standard tool computes these figures; C3 walking the live extents per query and walking the files per rewrite are both correct and both die at the stated import size; C4 line-for-line comparison on a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is a slot array per file, a per-extent size and reference count, a per-volume sum of the sizes
  it references and a second sum over the extents nobody else references, answering `own` from
  the second sum and finding an extent's pointers by walking the volume's files when a rewrite
  moves them. That plan is wrong in three places. A clone can put two slots on one block, so a
  reference count is not an occupancy figure and the half rule fires at the wrong time. A volume
  that holds an extent through two slots still holds it after one is cleared, so presence cannot
  be a set that is discarded on the first clear. And `own` is not the unshared sum: dropping a
  volume leaves a two-volume extent single-held, which rewrites it down to the blocks the
  survivor sits on, so the answer needs the survivor's occupancy inside that extent - a figure
  the first plan never keeps. The third is the one I would find last, because it is invisible
  until a program both shares an extent and leaves it under half occupied.
- Estimated solves out of 8: 2 (range 1 to 4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-14 scored 100/100, in band, one warning
  (`gate.measured` still false until the two import families are timed).
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-14 first record,
  100.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the tree stores per
  extent only a size and a pointer tally, so occupancy and presence have to be built; the
  shipped rewrite finds pointers by walking every file, so no reverse index announces itself;
  no expected output ships beside the programs; `use` sums a shared extent into every holder so
  no pair of printed numbers yields the drop gain; the sealed model and the frozen answers sit
  in a root-only directory.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  run the shipped store and read its trace against the brief; separate the three questions the
  design conflates (pointers on an extent, blocks occupied, volumes present); make occupancy a
  tally per block; make presence a tally per volume; derive what a drop gives back and find the
  rewrite it triggers in the survivor; keep the survivor's occupancy per volume so that figure
  is available; re-examine every extent that lost a pointer, whichever op removed it, and
  rewrite in ascending id; give each extent the slots that point into it so a rewrite moves them
  without walking the store; time the two import programs against the limit.
- Originality check: searched 2026-09-14 for public write-ups of this accounting. What exists is
  background, not a plan: the LWN article on copy-on-write subvolumes and snapshots and Josef
  Bacik's post on extent reference counting explain sharing and why partially referenced extents
  hold their whole space; quota manuals define an exclusive figure as the data no other volume
  references. That definition is the wrong reading here, since `own` also carries the space a
  rewrite would give back in the volume that survives. No page describes this store, its rewrite
  rule, its ops or its queries, and the local inventory has no task on extent sharing.

## What has to be correlated across the tree before a plan exists (Stage 3 gate)

None of these is in one place, and a plan that gets any of them wrong is wrong everywhere:

- what a slot holds. `environment/app_src/st/vol.py` declares the array, but the shape of what
  goes in it is fixed by the two frozen readers: the copy in `ops.py` passes a slot's contents
  straight back to `pt.put`, and the `at` branch of `ops.ex` reads the extent's number off it.
  Change the representation and both break, which is the fence on restructuring.
- when the settle runs. `ops.py` calls `step.done` at the end of every op that moves a pointer,
  including `cp`, `sn` and `rm`, so the settle is not a write-time concern; `st/step.py` decides
  what it looks at and `st/pt.py` decides what it is told about.
- where extent numbers come from. `st/ids.py` hands them out, `ops._wr` takes one before it
  touches a slot, and `st/pk.py` takes one per rewrite, so the numbering in a trace is the joint
  product of three files.
- what is printed and in what order. `st/say.py` holds the line shapes; the order comes from the
  order `ops.py` and `st/step.py` call it in.
- what an extent costs. Nothing in the tree computes it: `st/tot.py` reads a total that
  `st/ext.py` is supposed to maintain, and the shipped `ext.py` maintains a pointer tally
  instead, which is the whole of the first wrong reading.
- what a drop would give back. `st/own.py` reads two totals that only `st/ext.py` can move, and
  the second of them does not exist in the shipped tree at all.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 82 rows walked - 4 test functions, 27 enumerated cases, 6 artifacts, the 60 s clock and 24 rules of the sealed model split out of its two top-level definitions; no NOT STATED row survives; `python tools/tracecheck.py extent-share-pack` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 18 readings written as one-edit variants of the reference in `authoring/extent-share-pack/readings.py`. `tools/readingcheck.py` separates every one of them with an enumerated case, and each is separated by the case named for its rule (own-pair for own-solo-only, own-nogain for own-no-threshold, own-dup for vocc-by-pointer, hold-dup for occ-by-pointer, hold-twice for vol-as-set, pack-half for pack-at-most-half, pack-shared for pack-shared-too, pack-under for pack-no-shrink and pack-desc-blocks, drop-cascade for cand-skip-drop, line-order for pack-before-gone, pack-order for pack-desc-id). Measured on 210 generated programs, the readings move between 6.2 and 100 per cent of the population; the smallest are pack-before-gone at 6.2 and pack-desc-id at 8.1, and vocc-by-pointer needed the share family reshaped to put two slots of one volume on one block of a shared extent, which took it from 5.7 to 11.9. No reading survives that reproduces the published evidence, so nothing undecidable is graded. The judgement worth recording is about the unshared-sum reading of `own`, which is the load-bearing one: it is ruled out by the definition rather than by an example, because the definition says what dropping the volume would give back and the settle rule one paragraph above says what a drop leaves behind. Working that out is the task, so no worked example was added for it - an example that decided it would hand over the discovery, and the reading is decided by the text either way. Every convention that is not the difficulty - the half rule at exactly half, the ordering of lines inside an op, extent numbering, the empty slot - is stated outright instead.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the shipped tree matches 12 of the 27 enumerated programs and 1 of 42 drawn ones, reward 0. The constant strategy answers every question with 4, the commonest number in the frozen answers (22 of the 57 numbers those programs print), reward 0, caught by cp-before. The positional strategy answers the drop question with what the volume is on, reward 0, caught by own-dup, and moves 71 per cent of a generated population. The worked example replayed is `cheat-forge-key.sh`, which carries the frozen answers and hands them back for every program it recognises: it passes all 27 enumerated programs and dies on the first drawn one, reward 0. Reading the answer key out of the verifier at run time is `cheat-probe-answer-key.sh`, reward 0.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 s wall clock on the half that executes submitted code. Validated against two implementations written apart from the reference - `authoring/extent-share-pack/variants/ok-flat` and `.../ok-lazy`, which both score 1 - and against the naive pair under `authoring/extent-share-pack/slow`, which is exactly correct and dies on the clock: 50.8 s for one wide program answering by walking the live extents, 31.9 s for one deep program finding an extent's pointers by walking the files, against 0.89 s and 1.59 s for the reference. The reference settles the whole graded set in 8.3 s in a verifier container held to one CPU and 2048 MB, which is 7 times the headroom the clock asks for, and the graded set carries three of each large family. The worst case of each generated large family was timed too: 1.03 s and 2.19 s for the reference, 2.16 s and 5.21 s for the sealed model.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. One gap found and closed: the settle paragraph said the rewritten extent "is given up" while the printing paragraph said an extent given up prints `gone`, so a literal reading printed a `gone` line for every rewrite that the model never prints. The instruction now says the old extent is dropped as part of the rewrite, and that a rewrite prints nothing else for the extent it replaced. Everything else came back settled by a sentence: the half rule as twice the occupied blocks against the size, the ordering of `put`, `gone` and `pack` inside one op, extent numbering from 1 with the write taking its number before it touches a slot, `none` for an empty slot, a bulk printing nothing, and the copy reading its source before it writes.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the six editable files, taken at their original paths -
  `/app/st/ext.py`, `/app/st/pt.py`, `/app/st/pk.py`, `/app/st/own.py`, `/app/st/tot.py`,
  `/app/st/step.py`. Nothing else is read from the agent's container.
- What is checked: the verifier lays those six files over its own pristine copy of the tree and
  runs every graded program through `ops.ex`, comparing the printed trace line for line. Hand
  programs are compared with `tests/seal/gt.json`, frozen before the grading file was written;
  generated programs are compared with the sealed model. All or nothing.
- Tolerances: none - exact string comparison of every line. The only limit is the wall clock on
  the run that executes submitted code, which is also the execution limit stated in the brief.
- Ground truth, and where it lives: `tests/seal/gt.json` and `tests/seal/model.py`, in a
  directory locked to root before the privilege drop.

### The graded semantics, frozen

State: volumes hold files, a file is an array of slots, a slot is empty or points at one block
of one extent, an extent has an id and a size in blocks. Ids come from one counter starting at 1.

Ops, one per line: `vol v`; `fil v f n`; `wr v f lo hi`; `cp v f lo hi w g off`; `tr v f lo hi`;
`sn v w`; `rm v`; `use v`; `own v`; `tot`; `bulk v f n w`.

1. `wr` allocates one extent of `hi - lo + 1` blocks, taking the next id before any slot changes,
   and points slot `lo + i` at block `i` of it, dropping whatever those slots held.
2. `cp` copies the pointers of slots `lo..hi` of `v/f` as they stood before the op started into
   slots `off..off + hi - lo` of `w/g`; an empty source slot clears the destination.
3. `tr` clears the named slots. `sn` creates a volume holding a file of the same name and the
   same pointers for every file of `v`. `rm` removes a volume and all of its pointers.
4. `bulk v f n w` creates file `f` in `v` with `n * w` slots and performs `n` writes, the i-th
   covering slots `i*w .. i*w + w - 1`. Nothing is printed for a bulk.
5. After the pointer changes of `wr`, `cp`, `tr`, `sn` and `rm`: every extent no slot points into
   is freed, printing `gone <id>` in ascending id order; then every extent that has slots of
   exactly one volume pointing into it and fewer than half its blocks pointed at - twice the
   occupied blocks less than the size - is rewritten to a new extent taking the next id, sized
   at the occupied block count, the occupied blocks keeping their relative order, every pointer
   moved, and the old extent freed, printing `pack <old> <new> <size>` in ascending old id.
6. `use v` prints the total size of the extents at least one of whose blocks a slot of `v` points
   at, each extent counted once. `tot` prints the total size of every live extent. `own v` prints
   how much smaller `tot` would be if `rm v` ran next.
7. Printed lines of one op come in the order: `put` (write only), then `gone`, then `pack`.

Line formats: `put <id> <size>`, `gone <id>`, `pack <old> <new> <size>`, `use <vol> <blocks>`,
`own <vol> <blocks>`, `tot <blocks>`.

### Prong C tactics in the contract, and the route-around guard

- C1: every enumerated case has a must-still-work twin - an extent at exactly half is left alone,
  a shared extent under half is left alone, a volume holding an extent twice keeps it after one
  clear, and a plain single-volume trim must rewrite.
- C2: nothing in the tree says what the three queries should print, no standard tool computes
  them, and the model is unreadable from inside the run.
- C3: two import families. Answering a query by walking the live extents dies on the first;
  finding an extent's pointers by walking the files dies on the second.
- C4: hand programs pin each rule; the generated population is drawn from a seed taken after the
  agent's container is gone and shaped around the readings.
- Route-around guard: only the six files are collected, and they are laid over the verifier's own
  copy of the tree, so the driver, the op bodies, the id counter, the containers and the printer
  cannot be changed.

## Decisions and their reasons

- Category `Software / Databases`: the graded work is extent bookkeeping inside a storage engine.
  `Software / Systems` is retired for new tasks.
- The queries are the only observable, and `own` is defined as a counterfactual on the store's
  own rules rather than as "unshared space", because that is where the second discovery lives.
- `bulk` prints nothing and creates its own file, so nothing can die or be rewritten inside one.
- The epilogue runs once per op, not once per pointer change, so a write that empties an extent
  and then refills a block of another is one pass.
- `at v f i` was added after the first draft of the cases: without it the renumbering a rewrite
  performs is unobservable, because any injective map from the surviving blocks produces the same
  behaviour everywhere else. With it, `pack-under` and `pack-dup` grade the renumbering directly,
  and the copy rules get a fence as well.
- Candidates for the settle are the extents that lost a pointer, which is not a simplification:
  gaining a pointer can only raise occupancy or raise the number of volumes on an extent, and
  both make it less eligible, so nothing an op adds can create work for the settle. The brute
  force engine in `authoring/` examines every extent after every op instead, and the two agree on
  every program run through both.
- The nine isolation probes ship a store that is right everywhere except the drop question,
  rather than the shipped broken tree. Built on the shipped tree they scored 0, but for the wrong
  reason: that tree answers the size questions by walking the live extents, so it ran past the
  clock on the large programs and the payload never had a complete run to attack. Rebuilt, each
  probe finishes the graded set in seconds and fails on `own-dup` and `own-pair` alone, so a
  reward of 1 could only come from the payload reaching the reward channel.
- The verifier plumbing (`tests/test.sh`, `tests/reap.py`, `tests/test_outputs.py`, both
  Dockerfiles) was rewritten rather than carried over once `tools/simcheck.py` reported it at
  0.98 to 1.00 against `slab-fold-scope`; the shapes are the same because the isolation rules are
  the same, but nothing is copied. The two Dockerfiles still read as close to their neighbours,
  which is what a five-line canonical Dockerfile looks like.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py extent-share-pack --build`; harbor is not installed in this session, so the two-image emulation stands in for it |
| No answer leaked into agent image | pass | `tools/imagecheck.py`: the image holds 27 files, workdir /app, nothing from tests/ or solution/; a scripted audit finds no frozen answer line anywhere in the agent tree |
| oracle = 1 | pass | two-image run, 30 tests passed, reward 1 |
| nop = 0 | pass | two-image run, reward 0; the shipped tree matches 12 of 27 enumerated and 1 of 42 drawn programs |
| Cheats all score 0 | pass | 33 of 33 trials behaved as required in one `--all` run (oracle, nop and 31 cheats); the nine isolation probes were then rebuilt on a store that is right except for the drop question, so each payload had a complete run to attack, and all nine were re-run and still scored 0 |
| Correct variants score 1 | pass | ok-flat and ok-lazy, both in the two-image run |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | no errors; the remaining warnings are the cross-module call false positives every retained bundle also raises |
| `difficultycheck.py` at Stage 7 | pass | 100/100 on the measured tree, in band, no drift |
| `readingcheck.py` | pass | 18 of 18 readings separated by an enumerated case |
| `forgecheck.py` | pass | the answer-key forgery is present and scores 0 |
| `onelinecheck.py` | pass | 3 of 5 graded quantities have a short rule, the drop gain and the rewrite decision do not |
| `catcheck`, `extraneouscheck`, `solvecheck`, `hintcheck`, `deadfieldcheck`, `simcheck` | pass | simcheck still reports the two Dockerfiles as close to other bundles, which is what a five-line canonical Dockerfile looks like |
| `harbor check` rubric | not run | harbor is not installed and no model API key is available in this session |

## Quality self-review (docs/QUALITY-REVIEW.md), criterion by criterion

Instruction against verifier, both directions. Every test function, enumerated case, artifact,
clock and model rule has a row in `authoring/extent-share-pack/trace.md` citing the sentence that
tells the agent about it, and `tracecheck` is clean. The converse was walked by hand: each op
description is exercised by a case (`wr` by put-fresh and put-steal, `cp` by cp-before and
cp-empty, `tr` by pack-under, `sn` by own-snap and hold-last, `rm` by drop-gone and drop-cascade,
`bulk` by line-quiet), each accounting rule by the case named for it, the print order by
line-order and pack-order, and the execution limit by the two slow cheats. The six collected
paths are named in the instruction; the printed line formats are given down to the separator; the
half rule is stated as twice the occupied blocks against the size; ties are settled by extent
number; the empty slot prints `none`.

Instruction prose. Read aloud for cadence and rewritten twice: the op paragraph was broken into
one sentence per op and the two long accounting sentences were split, which took the short
sentence share from 4 per cent to 17 and removed both dash asides (`tools/textcheck.py` against
`tasks/slab-fold-scope/instruction.md`). Residual: cadence is still more even than that
reference, and the type-token ratio is lower, which is what a contract that names the same five
nouns in every rule looks like.

Verifier rigor. The tests read a trace produced by running the submitted files over programs the
submission has not seen, not a state it could write; `tests/test_outputs.py` carries the frozen
contract as its module docstring and one commented section per group; the population is seeded
from a nonce drawn in `tests/test.sh` after the agent's container is gone, and the model computes
the expectation from the same seed, so the verdict is deterministic while the programs are not
predictable.

Environment hygiene. `tools/imagecheck.py` reports the agent image would hold 27 files under
`/app` and nothing from `tests/` or `solution/`; the agent tree has no comment, docstring or
`.md` file; every pip install is pinned and no apt package is; the paths the instruction names all
exist and are spelled the same way.

Solution quality. `solution/solve.sh` copies six implementation files into place and runs two
shipped programs; it computes nothing by echo and reads nothing the agent could not read.

Anti-cheating. A scripted audit finds no frozen answer line anywhere in the agent tree, and no
file named after an enumerated program. Thirty-one cheats score 0 in the two-image run, among
them a forgery carrying the frozen answers, the constant strategy, and nine isolation probes.

Metadata. `Software / Databases` with six tags naming the techniques rather than the taxonomy;
`difficulty_explanation` names the three places the first plan is wrong and says the identifier
register is a design choice; `solution_explanation` walks the six files in the order the rules
force; `verification_explanation` names the case that catches each wrong reading;
`relevant_experience` is the domain role and nothing beyond it; ten hours matches the work.

## Cold self-attack, and what stands in its place

The self-probe was NOT RUN as a cold solve. The order of work here was contract, then
environment, then reference and sealed model, so by the time a cold attempt could have been
staged the author had written both implementations and the generator; a probe reported as cold by
an author in that position measures memory, not difficulty. What is recorded instead is what can
be measured honestly:

- the author's attack on the plan, above, naming the three places the first plan is wrong;
- eighteen wrong readings written down and separated, each by the enumerated case named for its
  rule, with the fraction of a generated population each one moves;
- the shortcut strategies scored, including a forgery carrying the frozen answers;
- the no-oracle property: nothing in the tree states what the three questions should print, and
  the sealed model and the frozen answers are unreadable from inside the graded run, which was
  confirmed in the image rather than assumed - the sandbox uid gets PermissionError on the model,
  on gt.json, on the directory listing and on the reward file;
- the cold-reader pass over every printed token, which found and closed one real contract gap.

## Open questions and next steps

Packaged and ready for the platform gates. The residual risks worth flagging to a reviewer:
the difficulty estimate of 2 solves out of 8 is a judgement, not a measurement; `harbor check`
could not be run in this session; and the prose screen's cadence axis still reads a little more
even than the retained bundle it was compared against, which is a property of a contract that has
to state ten rules exactly once each.
