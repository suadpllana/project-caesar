# Task state

Working memory for `shard-redraw-resume`. Assume the next session starts with no memory of this
one - anything not written here is lost. This file never ships in the zip.

## Current stage

`Stage 7 - rebuilt after a quality-review `difficult` failure` (2026-09-14, second pass)

## Assistant's assigned role

Training-infrastructure engineer on a data-parallel stack: the part that decides which samples
each rank consumes, what a checkpoint has to hold for a run to come back where it left off, and
what changes when a preempted job returns on a different number of ranks. Comfortable with
gradient accumulation, dynamic loss scaling, deterministic epoch shuffles that are evaluated one
position at a time instead of materialised, and the difference between a run that resumes and a
run that merely restarts.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, authored from scratch
- Task shape chosen: not applicable (no repository), so no ablation decision is required
- Contributor's relationship to it: not applicable
- License: not applicable; every line of the agent-facing tree was written for this task
- Pinned commit vendored: none
- Load-bearing couplings: authored, not mined - listed under "Why it is hard" below
- Identifier degradation: the tree uses a terse legacy register (`rig/`, `draw`, `cut`, `scal`,
  `turn`, `keep`, `lead`, `st`, `sc`, `gt`, `nf`) by choice, recorded in
  `difficulty_explanation`. No name misdescribes what it holds, and the domain words the
  category rests on (rank, micro, accum, epoch, scale, ckpt, shuffle) are left intact
- Proper-noun sweep: nothing to sweep - no project, product or person is named anywhere in the
  agent-facing tree, and the only proper nouns in the bundle are in this file
- Upstream-diff check: not applicable; there is no upstream to diff against

## Task summary

`/app` replays a training run described by a text program: a dataset size and a seed, a rank
count, a micro-batch size and an accumulation depth, a checkpoint cadence, a loss-scale growth
interval and an epoch count, plus a list of sample ids that come back non-finite and a sequence
of legs (`run n`, `kill`, `back r`). It prints which samples each rank fed on every attempted
step, whether the step was applied or skipped, the scale after it, every checkpoint, every
preemption, every return and every epoch boundary. Six files under `/app/rig/` decide all of
that and all six ship wrong. The agent repairs them so that every graded program's trace matches
the frozen contract, inside the stated execution limit.

## Why it is hard

The rules are all in the brief. What is not in the brief is which of the structures those rules
seem to ask for survive all of them at once, and that is the work. The memorized shape for this
code - permute the epoch, shard it per rank, run a cursor down each rank's shard, checkpoint the
cursor - is wrong three separate ways, and the third has no line in the tree to fix.

- Expert time estimate: 12 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the first plan
  is the DistributedSampler shape and it is defeated in stages. A skipped step takes its window
  without advancing the applied count, so the cadence and the epoch's progress run on two clocks.
  Then a return on a different rank count redraws the order, so a saved position addresses a
  different sequence of samples. Then the rule that has no local repair: an epoch hands each
  sample out once, so after a redraw a window is the next samples the epoch has not fed rather
  than the next positions. The shipped engine keeps a scalar cursor and no ledger at all, so
  there is nothing to correct - the structure cannot express the question. Two derivations follow
  and neither is stated anywhere: the shuffle is a cycle-walking Feistel and is therefore
  invertible, so a sample's position under any order is one evaluation away and an inverse ships
  nowhere; and two walks under one order collapse to a single head, because a walk leaves nothing
  unfed behind it, which is what makes a four-hundred-leg run affordable and what makes `rows`
  minus samples fed the right test for whether the epoch is out.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B1, B2, C1, C2, C3, C4. A1 is the prior
  as liability - the retrieved shape slices the epoch per rank, resumes a cursor and promises the
  order is independent of the world size, and all three are wrong here. A2: nothing is called
  resharding, elastic resume or a stateful sampler. B1: the ledger, the width, the scale machine,
  the step, the checkpoint and the leg driver each hold one part of what a return has to
  reproduce, and no single file says where one lands. B2: twelve rules hold at once. C1: both
  sides are fenced, so a run that never returns must be untouched by the ledger. C2: the natural
  oracle is a torch pipeline built beside it, which agrees on the plain runs and disagrees on
  exactly the graded cases. C3: two correct-but-infeasible families, both measured. C4:
  enumerated corners plus a nonce population, graded all or nothing.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was to keep the run state as (epoch, position, applied) and patch the six files where they
  disagree with the brief. It is wrong at the first skipped step, wrong again at the first return
  on a new rank count, and structurally wrong the moment a sample would be handed out twice -
  which is where the state stops being a position and becomes a ledger of what the epoch has
  fed. Every one of those findings arrives after the plain programs already pass.
- Estimated solves out of 8: 2 (designed at the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py): 100/100 on the first design, 2026-09-14,
  before any code. Re-scored 100/100 against the rebuilt tree the same day: 276 environment
  lines, 6 editable files, 268 reference lines, 30 cheats, 2 variants.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not
  anchored; this task has not been accepted.
- Score history: 2026-09-14 design 100/100; first build failed the quality review on `difficult`,
  `instruction concision` and `solvable`; rebuilt the same day and re-scored 100/100.
- Leak audit (docs/DIFFICULTY.md): no inverse for the shuffle ships anywhere, so the fast
  membership test has to be derived. Nothing in the tree stores a count of samples fed, a ledger,
  or a step count for an epoch - the shipped engine keeps one scalar. The four shipped programs
  run through the shipped wrong driver, so no correct trace exists in the agent's tree. The
  ledger has no entry point of its own; the redraw goes through the same window call as every
  other step. `tools/deadfieldcheck.py` and `tools/onelinecheck.py` were run against the built
  tree; results under Validation status.
- Expert path, described step by step: run the shipped driver on `small.txt` and line the trace
  up against the brief one line kind at a time; establish that the window is cut from the order
  and dealt after, which the per-rank slicing cannot express; split the applied count from the
  epoch's progress; find that a return redraws the order and that a sample must not come round
  twice, so the state is what the epoch has fed and not where it got to; derive the inverse of
  the shuffle so that question costs one evaluation; derive that two walks under one order
  collapse, so the ledger is one head per rank count and the epoch ends on `rows` minus fed; time
  `wide.txt` and `deep.txt` against the stated limit and remove anything that costs the size of
  the set or the length of the epoch so far.
- Originality check: searched 2026-09-14. The pieces are public and the combination is not.
  PyTorch's `DistributedSampler` gives the shard-per-rank shape; Hugging Face `accelerate` and
  `diffusers` issues 963, 499 and 3467 are the public record of schedulers stepping on skipped or
  accumulated steps and of resume landing on the wrong step under accumulation; MosaicML's
  StreamingDataset documents elastic resumption and states the opposite of this spec, that sample
  order is the same regardless of the number of GPUs, and resumes by skipping a count rather than
  by tracking what was handed out; format-preserving encryption by Feistel plus cycle walking is
  the public technique behind an order evaluated at a position. No page found plans this task, and
  the closest one actively misleads, which is the A1 bet.

## Verifier contract - FROZEN, amended once

Frozen 2026-09-14 before `tests/` was written. Amended the same day, after the quality review
failed the bundle on `difficult`, by adding one rule: an epoch hands each sample out once. That
is a change to what "correct" means and is recorded as such. It is additive everywhere it can be:
of the 22 answers frozen under the original contract, 20 came out byte-identical and only the two
cases with a mid-epoch return moved, which `build_gt.py` reported and which is the evidence the
rule changes nothing about a run that never resizes.

- Artifacts the agent produces: `/app/rig/draw.py`, `/app/rig/cut.py`, `/app/rig/scal.py`,
  `/app/rig/turn.py`, `/app/rig/keep.py`, `/app/rig/lead.py`. Nothing else is read.
- What is checked: the verifier lays those six over its own pristine copy of the tree, replays
  every graded program, and compares the whole trace line for line. 26 enumerated programs
  against `tests/seal/gt.json`; 321 generated inside the verifier from a seed drawn after the
  agent's container is gone, across nine families. 347 in total. Every one must match.
- Tolerances: none. Exact string equality on every line, including order.
- Ground truth: `tests/seal/model.py` and `tests/seal/gt.json`, in a directory `chmod 700` before
  the privilege drop, so the uid that runs agent code cannot read either.

The twelve graded decisions, as they now stand:

 1  a step takes `rank * micro * accum` samples the epoch has not handed out
 2  chunk `j * rank + r` of that window, `micro` wide, is rank r's micro-batch j
 3  the order for an epoch is drawn from the seed, the epoch and the rank count in force
 4  no epoch hands the same sample out twice
 5  a walk resumes where the last walk under that order stopped
 6  the epoch ends when what it has not handed out will not fill another window
 7  the epoch edge is tested before a step is attempted, and rolling spends no run budget
 8  a step whose window holds a non-finite sample is skipped, and still takes that window
 9  a skipped step does not advance the applied count
10  a skip halves the scale, no lower than zero, and ends the run of successes; `grow` applied
    steps in a row doubles it and starts a fresh run
11  a checkpoint after every `ckpt` applied steps holds the epoch's ledger as that step left it,
    by copy; a return with none behind it goes to the start of the run
12  a return takes effect where it is given, not at the next epoch boundary

Prong C tactics in the contract: C1 both sides of every fence are enumerated (`deal-one`,
`drop-none`, `scale-grow`, `back-hold`, `plain-two` are the must-still-work side); C2 the obvious
oracle is a torch pipeline, which differs on the chunking, the drop granularity, the redraw and
the ledger; C3 two correct-but-infeasible families are killed by the execution limit; C4 the
nonce population is generated after the agent is gone and one wrong line anywhere scores 0. The
route-around guard: only the six files are taken, so the parser, the shuffle, the trace format
and the driver entry point are the verifier's own.

## Decisions and their reasons

- **The shuffle is frozen, and its inverse is not shipped.** `shuf.at` is a cycle-walking Feistel
  over the least even power of two at or above `rows`, so a position costs O(1) expected. The
  inverse is derivable from it by the same construction run backwards and is what makes "has this
  epoch fed x" affordable. Not shipping it is deliberate: the quality review's third complaint on
  the first build was that the primitive the performance path needs was already provided.
- **An epoch hands each sample out once.** This is the rule the rebuild turns on. It is one
  sentence in the brief and its consequences are stated nowhere: that the state is a ledger and
  not a cursor, that the ledger is one head per rank count, that the epoch ends on `rows` minus
  fed, and that a checkpoint has to copy the ledger rather than hold it.
- **The order depends on the rank count**, stated plainly in the brief. It is the opposite of what
  the best retrievable page promises, which is the A1 bet this task makes.
- **The example directory is `progs/`, not `runs/`.** `runs` is in `preflight.EXCLUDE_DIRS`
  because that is also what harbor calls its output, so the first build shipped a zip with no
  programs in it and the quality review failed two criteria on the dead end that created.
  `preflight.py` now errors when the brief names a path that does not survive packaging.
- **The worker replays programs in-process** rather than by subprocess, because 347 subprocess
  starts would dominate the execution limit and make the limit measure interpreter startup.
- **`PER_FAMILY = 45` and `EXEC_LIMIT = 120` in `tests/test.sh`** are the single source of the
  population size and the limit; every count and every number quoted in the brief and the
  metadata is derived from `gen.programs` at that value, not remembered.
- **The worked example was searched for, not chosen.** `make_progs.py --pick` prints, for every
  line where the shipped driver and the reference differ on `small.txt`, how many of the wrong
  readings that line decides. Line 1 decides two, both of them readings of the chunking rule the
  brief states in full anyway.
- **`fed-from-top` was written as a wrong reading and is not one.** `readingcheck` reported it
  equivalent: a walk that restarts at the top and skips what is already fed lands on exactly the
  window a walk resuming from the head lands on. That is the `slow-scan` family, which is correct
  and separated by the limit, so the reading was deleted rather than kept as a cheat that scores
  0 for the wrong reason.

## What the quality review said, and what was done about it

Failed 2026-09-14 on three blocking criteria. All three are addressed; the first was a packaging
defect and the other two share a root cause with it.

- **`instruction concision` and `solvable`, both FAIL**: the brief sent the agent to
  `/app/runs/...` and `solution/solve.sh` ran programs from `runs/`, and none of it shipped. The
  cause was a name collision: `runs` is in `preflight.EXCLUDE_DIRS` because that is also what
  harbor calls its output directory, so `package.py` dropped all four programs from the zip by
  name. Every local gate read the working tree, where they exist, so the oracle, the nop,
  `imagecheck` and 26 cheats were all green on a bundle that was a dead end on first contact.
  The directory is now `progs/`, and `preflight.py` gained a check that resolves every `/app`
  path the brief names against the packaged file list rather than against the disk. It was
  confirmed to fire on the exact defect and to be clean on all twelve bundles here.
- **`difficult`, FAIL**: "Every semantic rule is spelled out in the instruction ... six files
  totalling ~150 lines, each shipped with one bug that directly contradicts the prose, and the
  index-computable shuffle needed for the performance path is already provided in `shuf.py`."
  Every word of that was accurate about the first build. The repair is one rule whose
  consequences are stated nowhere: an epoch hands each sample out once. It removes the
  one-bug-per-sentence shape, because the shipped engine keeps a scalar cursor and has no ledger
  at all - there is no line that contradicts the rule, only a structure that cannot express it.
  It makes two derivations load-bearing that no sentence gives away: the shuffle's inverse, which
  ships nowhere, and the collapse of two walks under one order into a single head, which is what
  makes a four-hundred-leg run affordable and what makes `rows` minus fed the right epoch-end
  test. And it replaces the gate that rested on the provided primitive with two that do not:
  re-walking the epoch from the top is exactly correct and costs 218 to 222 seconds on each
  four-hundred-leg program. Measured on `tools/onelinecheck.py`, the epoch-end decision went from
  an exact one-term rule (`left < wide`) to no rule at depth two, and three of four graded
  quantities now have none.

## Validation status

Docker could not be used in this session: the daemon starts, but the egress policy returns 403 on
every container-registry blob host tried (Docker Hub, GHCR, public ECR), so no base image can be
pulled and no container ran. Everything below is either a static check or a host run of the
verifier's own `worker.py` and `test_outputs.py` with the real `cases.py`, `gen.py` and sealed
model, under the same 120 second execution limit `tests/test.sh` gives the worker. Host emulation
is not container evidence, and the difference matters most for the nine isolation probes.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no registry access; `tools/imagecheck.py` interprets the Dockerfile against the build context, assembles the files the image would hold, drops the reference in and runs all four shipped programs - clean |
| Brief's paths ship | pass | the new `preflight.py` check resolves every `/app` path in the brief against the packaged file list |
| No answer leaked into agent image | pass | no correct trace, no ground truth, no model and no inverse in `environment/`; `deadfieldcheck` and `hintcheck` clean |
| `harbor run -a oracle` = 1 | not run (harbor absent) | the reference scores **1** through the real worker and grader on the host, worker 11.2 s for all 347 programs |
| `harbor run -a nop` = 0 | not run (harbor absent) | the shipped tree scores **0** |
| Cheats all score 0 | 30 of 30 scored 0 on the host | 18 wrong readings, 2 correct-but-expensive, 1 forgery, 9 isolation probes. The probes each carry a wrong reading as well, which is what makes the reward a verdict on the tamper - but the host has no privilege drop and no root-owned seal, so this does **not** prove the isolation |
| Which layer catches each cheat | pass | `cheat_report.py`: all 18 readings caught by the enumerated case named for each, both slow families exact on the small set, the forgery reproduces 26 of 26 enumerated and fails 20 of 35 generated |
| Readings separated | pass | `tools/readingcheck.py`: every reading separated by an enumerated case. `fed-from-top` came back equivalent and was deleted - it is the `slow-scan` family, not a wrong reading |
| Answer shape | pass | `tools/onelinecheck.py`: only `save-after` is short (the cadence, stated in the brief); `roll-or-step`, `window-first` and `step-applied` have no exact rule at depth 2 over the fields the shipped tree exposes |
| Correct variants | pass | two independently written engines score **1**: one holding the whole engine in `lead.py` with the ledger as a list of pairs, one over a dict with the shuffle memoised both ways |
| Resource gate | measured | reference 11.2 s for the whole graded set; the epoch order built into a list costs 393-398 s on one sixty-million-row program; the epoch re-walked from the top costs 18-36 s on each of those and 218-222 s on each four-hundred-leg program, against the 120 s limit |
| Additivity of the contract change | proved | adding the no-repeat rule left 20 of the 22 previously frozen answers byte-identical; only the two mid-epoch-return cases moved, which is what the rule is for |
| `preflight.py` | pass | no errors; 22 warnings, 20 of them the known unused-public-function false positive every retained bundle carries |
| `catcheck`, `structcheck`, `textcheck`, `hintcheck`, `solvecheck`, `extraneouscheck`, `forgecheck`, `simcheck` | pass | simcheck's conceptual axis is clean |
| `difficultycheck` | 100/100 | measured tree: 276 environment lines, 6 editable files, 268 reference lines, 30 cheats, 2 variants |
| `harbor check` rubric | not run | no API key and no harbor in this environment |

## Stage 7 re-attack, and the self-probe

Read cold, the brief states every rule, so the rule set is not the barrier and was never meant
to be. What the brief does not state is which structure survives all of them, and the shipped
tree embodies the structure that does not: per-rank slices of a materialised epoch, a cursor
each, and a checkpoint keyed on the applied count. Each of those is right until one rule kills
it, and the rule that kills the last one is the return on a different rank count, which arrives
after the plain programs already pass. The two measured boundaries then forbid the two natural
correct-but-expensive repairs.

The honest residual risk is in the too-easy direction, not the too-hard one: an agent that
rewrites the six files from the brief instead of patching them can reach the right structure
without the detour, because nothing is hidden. The bet is that the memorized shape is strongly
attractive, that eleven interacting rules make one unplanned-for rule likely, and that the
scale families punish both natural structures. Estimate unchanged at 2 of 8.

**The cold self-attack described in the build order was not run, and is recorded as not run.**
This session wrote the reference, the sealed model and the enumerated cases, so a cold solve by
the same author would measure memory rather than difficulty, and a self-probe reported as passed
by a contaminated author is worse than no self-probe. Standing in its place are the measurements
that do not depend on the author's memory: all 14 wrong readings separated by a named case, two
of four graded quantities with no short rule over the exposed fields, no correct trace anywhere
in the agent's tree, and the two scale boundaries measured rather than asserted.

## Quality self-review, criterion by criterion (docs/QUALITY-REVIEW.md)

Answered with the file that satisfies each, not with "looks fine".

- *Every behaviour the tests check is in the instruction.* The twelve graded decisions are listed
  in the frozen contract above and each has a sentence in `instruction.md`: the window and the
  no-repeat rule and the chunking and the epoch edge in paragraph 3, the skip and the scale in
  paragraph 4, the cadence and the return in paragraph 5, the trace format in paragraph 6, the
  limit and the two large programs in paragraph 7.
- *Every behaviour the instruction promises is tested.* `tools/readingcheck.py` names the
  enumerated case that separates each of the eighteen wrong readings, and `cheat_report.py` names
  the first program that catches each shipped cheat.
- *Every file the tests read is named absolutely.* The six `/app/rig/*.py` in paragraph 2; the
  new `preflight.py` check resolves every backticked `/app` path in the brief against the
  packaged file list, which is the check the first build did not have.
- *Exact schema.* Eight line kinds, each with its fields, in paragraph 6, ending "Nothing else is
  printed".
- *Prose.* `tools/textcheck.py` against `note-carry-forward`: the only finding left is
  paragraph-length uniformity, which every retained passing brief also carries.
- *Verifier demands evidence.* The worker replays 347 programs through the submitted files and
  the grader compares whole traces; nothing is read from an exit code or from state the agent
  could write.
- *Test code is structured and commented.* `tests/test_outputs.py` opens with the frozen contract
  and separates the self-consistency check, the enumerated cases and the nonce population.
- *Deterministic.* No wall-clock or network dependence in any assertion. The nonce changes the
  programs, never the verdict: the sealed model is the oracle for whatever is generated.
- *Environment hygiene.* `environment/Dockerfile` copies only `app_src/`; pytest and ctrf are
  pinned and baked into `tests/Dockerfile`; `tests/test.sh` touches no network.
- *Solution quality.* `solution/solve.sh` copies six real implementation files and runs the
  driver on two shipped programs; `tools/solvecheck.py` clean, and the script was run end to end
  against a copy of the tree.
- *Anti-cheating.* No correct trace, ground truth, model or shuffle inverse in the agent tree;
  comparison is exact; nothing is cloned.
- *Metadata.* `category = "ML"` with `subcategory = "Training"` from that row; six tags naming
  techniques and none restating the taxonomy; `difficulty_explanation` names the concrete step
  and states the terse-register naming as a design choice; `expert_time_estimate_hours = 12`
  matches the claim.

## Open questions and next steps

- The nine isolation probes are unproven. They are written, they ship, and the verifier follows
  `docs/VERIFIER-ISOLATION.md` line by line, but the only proof that the isolation holds is a
  container run and this session could not make one. Run `python tools/docker_trial.py
  shard-redraw-resume --all` on a machine with registry access before submitting.
- The easiness probe has not been run. Nothing local substitutes for it.
- `tests/test.sh` sets `EXEC_LIMIT=60` and `PER_FAMILY=45`, and every count in the brief and in
  the metadata is derived from `gen.programs` at that value. Re-derive them after any change to
  either number or to the generator.
