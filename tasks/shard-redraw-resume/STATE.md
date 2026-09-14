# Task state

Working memory for `shard-redraw-resume`. Assume the next session starts with no memory of this
one - anything not written here is lost. This file never ships in the zip.

## Current stage

`Stage 7 - pre-flight and packaging` (2026-09-14; packaged, container gates outstanding)

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
cursor - is wrong three separate ways here, and the third way cannot be patched into it.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the first plan
  is the DistributedSampler shape, and it is defeated in stages. A skipped step consumes its
  window without advancing the applied count, so the checkpoint cadence and the data position
  move at different rates and neither is a function of the other. Then a return on a different
  rank count redraws the order for the epoch the run was in, which makes the saved position index
  a different sequence of ids and makes every per-rank shard, per-rank cursor and per-epoch step
  count computed before the resize a quantity of a geometry no longer in force. That is a replan,
  not a patch: the stable coordinate is the position in the epoch order, everything else is
  derived from it at the moment it is needed, and the same reformulation is what the sixty
  million row program forces for a second reason.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B1, B2, C1, C2, C3, C4. A1 is the prior as liability - the retrieved
  shape shards the epoch per rank and promises the order is independent of the world size, while
  here the window is cut first and the order is drawn for the rank count in force. A2: nothing
  is called resharding, elastic resume or a stateful sampler. B1: the window arithmetic, the id
  lookup, the scale machine, the step, the checkpoint and the leg driver each hold one part of
  what a resume has to reproduce, and no single file says where a return lands. B2: eleven rules
  hold at once. C1: both sides are fenced, so a run that never resizes must not redraw and a
  resized run must repeat samples inside one epoch. C2: the natural oracle is a torch pipeline
  built beside it, which agrees on the plain runs and disagrees on exactly the graded cases.
  C3: two correct-but-infeasible families, both measured. C4: enumerated corners plus a nonce
  population, graded all or nothing.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was to keep the run state as (epoch, applied step, rank) and derive the position from the
  applied count, patching the six files where they disagree with the brief. It is wrong at the
  first skipped step, because the position is not the applied count times a window; and it is
  structurally wrong at the first `back` on a new rank count, because the position is then not a
  count of windows of any width and the shard lists are drawn from an order that no longer
  applies. Both findings arrive after the plain programs already pass.
- Estimated solves out of 8: 2 (designed at the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py): attempt 1 on 2026-09-14 scored 100/100 with
  no hard stop, one warning (`gate.measured` was false before the timings were run). Recorded at
  `authoring/shard-redraw-resume/difficulty.toml`. No earlier attempt: the first design reached
  the band.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not
  anchored; this task has not been submitted.
- Score history: 2026-09-14, 100/100 on the design record before any code; re-measured against
  the built tree at Stage 7 (see Validation status).
- Leak audit (docs/DIFFICULTY.md): the shuffle module takes a rank count argument, which is
  visible and used on the live path, and says nothing about what a return does with it. No count
  of an epoch's steps, and no window count, is stored anywhere - only the position, the applied
  count and the scale state, all of them primitives the ops set or the rules advance. The four
  shipped programs are run through the shipped wrong driver, so no correct trace of any program
  exists in the agent's tree. The resize goes through the same window arithmetic as every other
  step and has no entry point of its own. `tools/deadfieldcheck.py` and `tools/onelinecheck.py`
  were run against the built tree; results under Validation status.
- Expert path, described step by step: run the shipped driver on `small.txt` and line the trace
  up against the brief one line kind at a time; establish that a window is cut out of the epoch
  order first and dealt to ranks after, which the shipped per-rank slicing cannot express;
  rewrite the sampler as arithmetic on the position, evaluating the shuffle one position at a
  time; split the applied count from the position so the checkpoint carries both and the skip
  path consumes its window without moving the applied count; settle what a return restores and
  what it must recompute, given that the rank count is not checkpoint state and the order depends
  on it; handle the epoch edge in its own right, including a resize that ends an epoch with no
  step in it; time `wide.txt` and `deep.txt` against the stated limit and remove anything that
  costs the size of the dataset or the length of the run.
- Originality check: searched 2026-09-14. The pieces are public and the combination is not.
  PyTorch's `DistributedSampler` gives the shard-per-rank shape; Hugging Face `accelerate` and
  `diffusers` issues 963, 499 and 3467 are the public record of schedulers stepping on skipped
  or accumulated steps and of resume landing on the wrong step under accumulation; MosaicML's
  StreamingDataset documents elastic resumption and states the opposite of this spec, that sample
  order is the same regardless of the number of GPUs; format-preserving encryption by Feistel
  plus cycle walking is the public technique behind an order evaluated one position at a time.
  No page found plans this task, and the closest one actively misleads, which is the A1 bet.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-14, before `tests/` or the environment were written. Only a change to what
"correct" means needs contributor approval.

- Artifacts the agent produces: `/app/rig/draw.py`, `/app/rig/cut.py`, `/app/rig/scal.py`,
  `/app/rig/turn.py`, `/app/rig/keep.py`, `/app/rig/lead.py`. Nothing else is read.
- What is checked: the verifier lays those six over its own pristine copy of the tree, replays
  every graded program, and compares the whole trace line for line. 22 enumerated programs
  against `tests/seal/gt.json`, frozen before `test_outputs.py` was written; 276 programs
  generated inside the verifier from a seed drawn after the agent's container is gone, across
  eight families. Every program must match. All or nothing.
- Tolerances: none. Exact string equality on every line, including order.
- Ground truth, and where it lives: `tests/seal/model.py` (an independently written whole-run
  model) and `tests/seal/gt.json`, in a directory `chmod 700` before the privilege drop, so the
  uid that runs agent code cannot read either.

The eleven graded decisions, as frozen:

 1  a step takes `rank * micro * accum` consecutive positions of the epoch order
 2  chunk `j * rank + r` of that window, `micro` wide, is what rank r feeds at accumulation j
 3  the order for an epoch is drawn from the seed, the epoch and the rank count in force
 4  the tail of an epoch short of a whole window is dropped and never read
 5  the epoch edge is tested before a step is attempted, and rolling spends no run budget
 6  a step whose window holds a non-finite id is skipped, and still consumes that window
 7  a skipped step does not advance the applied count
 8  a skip halves the scale, no lower than zero, and ends the run of successes
 9  `grow` applied steps in a row doubles the scale and starts a fresh run of successes
10  a checkpoint after every `ckpt` applied steps holds the epoch, the position, the applied
    count and the scale state; a return with none behind it goes to the start of the run
11  a return takes effect where it is given, not at the next epoch boundary

Prong C tactics in the contract: C1 both sides of every fence are enumerated (`back-hold`,
`drop-none`, `scale-grow`, `deal-one`, `plain-two` are the must-still-work side); C2 the obvious
oracle is a torch pipeline, which differs on the chunking, the drop granularity and the redraw;
C3 two correct-but-infeasible families are killed by the execution limit on the worker; C4 the
nonce population is generated after the agent is gone, and one wrong line anywhere scores 0. The
route-around guard: only the six files are taken, so the parser, the shuffle, the trace format
and the driver entry point are the verifier's own and cannot be reshaped.

## Decisions and their reasons

- **The shuffle is frozen and not editable.** It is a cycle-walking Feistel over the least even
  power of two at or above `rows`, so a position costs O(1) expected. That is what makes an epoch
  of sixty million rows answerable without building it, and it is why `slow-order-list` is a
  correct implementation rather than a broken one.
- **The order depends on the rank count.** Stated plainly in the brief. It is what turns a
  resize from a change of arithmetic into a change of data, and it is the opposite of what the
  best retrievable page promises, which is the A1 bet this task makes.
- **The worker replays programs in-process** rather than by subprocess, because 298 subprocess
  starts would dominate the execution limit and make the limit measure interpreter startup.
- **`per = 45` in `tests/test.sh`** is the single source of the population size; every count
  quoted in the brief and in the metadata is derived from `gen.programs` at that value, not
  remembered.
- **The worked example was searched for, not chosen.** Of the lines where the shipped driver and
  the reference differ on `small.txt`, line 1 is decided by only two of the fourteen wrong
  readings, and both of those are readings of the chunking rule that the brief states in full
  anyway. `make_progs.py --pick` prints the whole table.
- **`kill-none` was edited after `readingcheck` reported `kill-fresh-scale` blind.** The original
  case never moved the scale before the preemption, so the reading was invisible. `grow` went
  from 9 to 2. `build_gt.py` now keeps `frozen_progs.json` beside it so an edited program is
  reported as an edited case and not as a contract change.

## Validation status

Docker could not be used in this session: the daemon starts, but the egress policy returns 403
on every container-registry blob host tried (Docker Hub, GHCR, public ECR), so no base image can
be pulled and no container ran. Everything below is either a static check or a host run of the
verifier's own `worker.py` and `test_outputs.py` with the real `cases.py`, `gen.py` and sealed
model, under the same 60 second execution limit `tests/test.sh` gives the worker. Host emulation
is not container evidence, and the difference matters most for the nine isolation probes.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no registry access; `tools/imagecheck.py` interprets the Dockerfile against the build context, assembles the 17 files the image would hold, drops the reference in and runs all four shipped programs - clean |
| No answer leaked into agent image | pass | no correct trace, no ground truth, no model and no conversion table in `environment/`; `tools/deadfieldcheck.py` clean; `tools/hintcheck.py` clean |
| `harbor run -a oracle` = 1 | not run (harbor absent) | the reference scores **1** through the real worker and grader on the host, worker 1.7 to 2.0 s for all 298 programs |
| `harbor run -a nop` = 0 | not run (harbor absent) | the shipped tree scores **0**: killed at the 60 s limit on the large programs, and wrong on 17 of the 22 hand cases when run without a limit |
| Cheats all score 0 | 26 of 26 scored 0 on the host | 14 wrong readings, 2 correct-but-expensive, 1 forgery, 9 isolation probes. The probes' rewards are 0 here because each carries a wrong reading as well, which is what makes the reward a verdict on the tamper - but the host has no privilege drop and no root-owned seal, so this does **not** prove the isolation |
| Which layer catches each cheat | pass | `cheat_report.py`: every one of the 14 readings is caught by the enumerated case named for it, both slow families are exact on the small set, and the forgery reproduces 22 of 22 enumerated and fails 18 of 36 generated |
| Readings separated | pass | `tools/readingcheck.py`: all 14 separated by an enumerated case. `kill-fresh-scale` was BLIND until `kill-none` was given a growth interval that moves the scale before the preemption |
| Answer shape | pass | `tools/onelinecheck.py`: `roll-or-step` is `left < wide` and `save-after` is the cadence, both stated in the brief; `resume-seen` and `step-applied` have no exact rule at depth 2 over the fields the tree exposes, `saved_done * wide` included |
| Correct variants | pass | two independently written engines score **1**: one holding the whole engine in `lead.py` over a plain list, one caching the current window and keeping the checkpoint as a namedtuple |
| Resource gate | measured | reference 1.7-2.0 s for the whole graded set; the epoch order built into a list costs 382-389 s on one sixty-million-row program; the run state rebuilt by replaying costs 42-52 s on each four-hundred-leg program, 137 s for the three, against the 60 s limit |
| `preflight.py` | pass | no errors; 21 warnings, 20 of them the known unused-public-function false positive that every retained bundle carries, plus the reward-binary warning slab-fold-scope also carries |
| `catcheck`, `structcheck`, `textcheck`, `hintcheck`, `solvecheck`, `extraneouscheck`, `forgecheck`, `simcheck` | pass | simcheck's conceptual axis is clean; its two remaining NEAR findings are the Dockerfiles, which the retained bundles score 1.000 against each other on |
| `difficultycheck` at Stage 7 | 100/100 | measured tree: 275 environment lines, 6 editable files, 232 reference lines, 26 cheats, 2 variants. No drift from the design |
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

- *Every behaviour the tests check is in the instruction.* The eleven graded decisions are
  listed in the frozen contract above and each has a sentence in `instruction.md`: the window
  width and the chunking in paragraph 3, the tail drop and the edge test and the roll budget in
  the same paragraph, the skip and the consume and the applied count and the scale in paragraph
  4, the cadence and the return and the rank count in paragraph 5, the trace format in
  paragraph 6, the limit and the two large programs in paragraph 7.
- *Every behaviour the instruction promises is tested.* `tools/readingcheck.py` names the
  enumerated case that separates each of the fourteen wrong readings, and `cheat_report.py`
  names the first program that catches each shipped cheat.
- *Every file the tests read is named absolutely.* The six `/app/rig/*.py` in paragraph 2; a
  script checked every backticked `/app` path in the brief against the tree and all thirteen
  exist, and every op the brief names is one the parser accepts, with none left over.
- *Exact schema.* Eight line kinds, each with its fields, in paragraph 6, ending "Nothing else
  is printed".
- *Prose.* `tools/textcheck.py` against `note-carry-forward`: burstiness 0.871, 24 per cent
  short sentences, 0 stock words, 0 hedges, 1.4 contractions per thousand. The one finding left
  is paragraph-length uniformity, which every retained passing brief also carries.
- *Verifier demands evidence.* The worker replays 298 programs through the submitted files and
  the grader compares whole traces; nothing is read from an exit code or from state the agent
  could write.
- *Test code is structured and commented.* `tests/test_outputs.py` opens with the frozen
  contract and separates the self-consistency check, the enumerated cases and the nonce
  population.
- *Deterministic.* No wall-clock or network dependence in any assertion. The nonce changes the
  programs, never the verdict: the sealed model is the oracle for whatever is generated, and the
  oracle scored 1 on every run of it here.
- *Environment hygiene.* `environment/Dockerfile` copies only `app_src/`; pytest and ctrf are
  pinned and baked into `tests/Dockerfile`; `tests/test.sh` touches no network.
- *Solution quality.* `solution/solve.sh` copies six real implementation files and runs the
  driver; `tools/solvecheck.py` clean.
- *Anti-cheating.* No correct trace, ground truth or model in the agent tree; comparison is
  exact; nothing is cloned.
- *Metadata.* `category = "ML"` with `subcategory = "Training"` from that row; six tags naming
  techniques and none restating the taxonomy; `difficulty_explanation` names the concrete step
  and states the terse-register naming as a design choice; `expert_time_estimate_hours = 10`
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
