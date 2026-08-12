# Task state

## Current stage

`Stage 8 - back from a failed reference review, fixed and re-gated locally`

The bundle was submitted and the pipeline's reference verification returned **oracle 0 on
all three attempts, with the verifier reported at 0 seconds**. Nop was 0, which is correct
but proves nothing on its own: a verifier that never grades anything scores every
submission 0. The post mortem and the fix are in "Reference review" below. Everything else
in this file describes the task as it now stands.

## Assistant's assigned role

Senior training-infrastructure engineer for large post-training runs: checkpointing and
resume, data feeders and packers, gradient accumulation, learning-rate and curriculum
schedules, and the exact reproduction of a preempted job across a restart.

## Source repository

- Repo URL: https://github.com/vllm-project/vllm (issue tracker used as the seed only)
- Task shape chosen: authored on top, not an ablation of upstream code. No source from the
  repository is vendored. The trainer in `environment/app_src/` is written for this task:
  a CPU-only, integer-arithmetic training loop with the organs the failure needs (a sample
  store, an epoch sampler, a length packer with a carry slot, a per-row stochastic stream,
  an accumulation loop, an optimiser with a shadow average, a schedule memo, a bounded
  checkpoint channel).
- Why not vendor: the upstream repository is public and diffable, and any accepted fix in
  it is public with it. Writing the trainer means the shipped tree matches no public
  repository, while the failure mode is the real one.
- Seed issue, for reviewers: `vllm-project/vllm#40533` ("[RFC]: Hybrid checkpoint ABI for
  non-KV prefix resume"). Its load-bearing distinction is between *payload equality*, the
  stored bytes coming back unchanged, and *logical value equality*, the restored state
  meaning the same thing once it is realised again in a live context. That distinction is
  what this task is built on, moved from a serving cache to a training loop: some of the
  trainer's state is authoritative and has to come back verbatim, and some of it is a
  realisation of settings that have since changed, and putting that second kind back is
  what breaks the run.
- Proper-noun sweep: the shipped tree carries no project, product, company or person name,
  no upstream identifiers, no distinctive error strings, no URLs. Identifiers are in the
  register of ordinary internal code (`pfx`-style abbreviations: `pstore` has no analogue
  here, but `feed`, `pack`, `samp`, `drv`, `ckstore`, `hd`, `ws`, `ntok`, `at_`).
- Upstream-diff check: there is nothing to diff. An agent that finds the seed issue learns
  the payload-versus-realisation distinction in the abstract, which the instruction already
  states as a requirement ("everything the amended settings reach has to follow the
  amendment; everything already fixed before the save has to come through untouched"). It
  learns nothing about which of this trainer's nine state holders falls on which side, and
  that is the whole task.

## Task summary

The agent gets a working trainer that checkpoints and resumes. A run that comes back from
a checkpoint is not the run that went down: it restarts the data stream, reseeds the
per-row stochastic stream, drops the accumulation window that was open, and loses the item
the packer was holding. The agent must make everything after a load identical to the path
the trainer would have been on had it never been interrupted, across an amended
configuration applied while the trainer was down, a curriculum bump that straddles a held
item, an epoch boundary, two save-and-load cycles, and a bounded checkpoint channel that
refuses a payload big enough to hold everything. Four files may be edited; everything else
is restored from a pristine copy before grading.

## Why it is hard

One question that is really two, and the same test does not answer both.

- State the history produced cannot be recovered from anything else, so it has to be
  carried: parameters, optimiser moments, the shadow average, the sampler cursor, the item
  the packer drew and could not place, the position of the per-row stream, and everything
  an open accumulation window has taken in.
- State that is a view of the configuration has to be dropped and derived again, because
  the configuration in force after a load is the amended one. The schedule memo is that.
- And the holder the obvious test gets wrong: the open window's length came from the
  schedule, which makes it look derived, but it was latched when the window opened, before
  the amendment existed. While the window is open that number is history.

Both directions are graded. `cheat-keep-schedule-memo` carries the view and fails three
scenarios of fourteen; `cheat-relatch-window` derives the latched value and fails exactly
one.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan: the first plan is "save the sampler state,
  the RNG state and the scheduler state dict, restore them all". That plan produces correct
  output on eleven of the fourteen scenarios, because the scheduler half of it is harmless
  until something is amended, and the held item's curriculum bound is invisible until a
  curriculum step straddles it. Forming the correct plan means classifying nine state
  holders by reading where each value is latched, in files the agent cannot edit, and then
  noticing that "can it be recomputed" is not the test.
- Tactics making that true: A1, A2, A3 poison the default plan; B1, B2 withhold it; C1,
  C2, C3, C4 make the wrong plan fail late. Each one, concretely:
  - Prong A1: the retrieved fix for "my resumed run does not reproduce" is exactly the
    plan that fails here, and its third element (restore the scheduler's state dictionary)
    is the specific defect. The transplant is `cheat-keep-schedule-memo` and scores 0.
  - Prong A2: the concept is never named. The instruction says a value pinned before the
    save must not be derived again, and a value derived after the load must not have been
    pinned, without saying which holders those are.
  - Prong A3: no single remembered recipe satisfies both directions at once, because the
    same holder class (schedule-derived) splits across them.
  - Prong B1: the load-bearing facts are spread and none of them is in an editable file.
    Where the curriculum bound is latched is in `data/pack.py`; how many draws a microbatch
    takes is in `data/pack.py` and `train/model.py` together; when the window length is
    fixed is in `train/loop.py`; what the channel accepts is in `core/ckstore.py`.
  - Prong B2: the amendment rule, the latched bound, the stream position, the mid-window
    state, the epoch boundary and the payload cap all have to hold at once.
  - Prong C1: fenced both ways. `amend-window` fails an over-derivation; `amend-lr`,
    `amend-bound` and `amend-ema` fail an over-restoration; `straight` and `empty-carry`
    fail anything that breaks ordinary behaviour or cannot encode an empty carry slot.
  - Prong C2: the obvious oracle is denied for the accounting. The agent can compare a
    resumed run against its own uninterrupted run and catch parameter drift, which is fair
    and is the expert path; it has nothing to compare read counts against.
  - Prong C3: two resource gates. The channel refuses an oversized payload outright, which
    kills "serialise the trainer". The read counter kills reconstructing position by
    replaying the stream, which is otherwise a correct plan.
  - Prong C4: exact integer equality on every field, all-or-nothing, over fourteen
    scenarios.
- Assistant's attack on the plan: my first plan was to give every holder a snapshot and put
  them all back, trimming whatever the channel refused. That plan gets `straight`,
  `empty-carry`, `boundary`, `midwindow`, `carry-bump`, `rollback`, `epoch`, `twice`,
  `wide` right and fails `amend-lr`, `amend-bound`, `amend-ema` on the schedule memo. My
  second plan, after seeing that, was "views are always recomputed", which fixes those
  three and breaks `amend-window`. Both are in `cheat/` and both score 0. The third plan,
  reconstructing the stream position from the step counter, is right whenever the packer
  produced three rows and wrong whenever it produced four, which is the kind of wrongness
  that survives casual testing.
- Estimated solves out of 8: 1 to 2.
- Expert path, step by step:
  1. Run `/app/run_train.py` on the shipped demo and see the trace announce step 0 after a
     load taken at step 2.
  2. Read `train/ckpt.py` and find the holder list; read `build.py` and find the eight
     parts a load rebuilds.
  3. Write the two empty snapshots, `data/feed.py` and `train/noise.py`, and add `loop` to
     the holder list. Most scenarios pass at this point.
  4. Read `data/pack.py` and notice the bound travels with the held item rather than being
     re-read at placement, which puts the bound in the carry slot's snapshot.
  5. Read `train/model.py` and `data/pack.py` together and see that one draw is taken per
     packed row and the row count is not a function of the step, which settles the stream
     position.
  6. Build an amended-resume scenario and compare it against the same op list with the
     down time deleted. That is what exposes the schedule memo.
  7. Read `train/loop.py` and see the window length latched at `k == 0`, which is what
     stops the fix in step 6 from being "never restore anything schedule-shaped".
  8. Read `core/ckstore.py` for the cap and confirm the carried set fits.
- Originality check: searched for public write-ups of training resumes that do not
  reproduce. What exists is the standard advice to save the sampler state and the RNG
  state and the scheduler state dictionary, plus a long tail of dataloader-state issues.
  Nothing anywhere makes the latched-versus-derived distinction this task is built on, and
  no public code has this trainer's shape.

## Reference review - the failure and the fix

Symptom: oracle 0, 0, 0, verifier 0s. Locally, on the same bundle, the oracle scored 1 in
about four seconds on the real two-container run, so nothing was wrong with the solution
or the ground truth. What the bundle had was a verifier that made demands of the machine
it ran on, and the pipeline's machine is not this sandbox.

Three of those demands, in the order they bite. Every one of them is reproducible here by
running the shipped verifier image under a container configuration the platform might
plausibly use.

1. **The preamble aborted on a refused chown.** `set -Eeuo pipefail`, then a run of
   unguarded `chown`/`chmod` calls over `/tests`, `/pristine`, `/work` and nine writable
   directories. Under a read-only root filesystem the first of them fails and the script
   is gone in 17 milliseconds, having written nothing but the default 0. That is exactly
   "verifier 0s" and it scores oracle and nop alike.
2. **A whole-filesystem sweep.** Two `find / -xdev` passes, then two more per mount, each
   chowning and chmodding whatever they found. Slow on a large image, and it reaches into
   volumes that belong to the platform rather than to the task.
3. **A graded assertion about the image rather than the submission.**
   `test_the_trainer_had_nowhere_to_write` walked the filesystem after the run and failed
   if *any* path was writable by uid 1002. One writable mount the platform provides and
   the reference fails, having done everything right.

What changed:

- The preamble is best effort throughout. Every `chown` and `chmod` ends in `|| true`;
  every step that genuinely has to succeed ends in `|| die`, which writes 0 and stops
  before any agent code runs. `set -e` stays on.
- The two conditions that must hold - a reward channel the run cannot reach, and answer
  material it cannot read - are **checked** rather than assumed, against the permissions
  the kernel would actually apply to uid 1002 rather than against a mode bit pattern.
- The filesystem sweep is gone. `tests/premark.py` surveys the image before the run,
  `test_outputs.py` surveys it again afterwards, and what fails a submission is a path the
  trainer's uid owns that was not there before: a file the trainer created. A path the
  verifier could not close is recorded, printed and not graded. Both surveys are bounded
  in time and node count, and if either comes back incomplete the check skips rather than
  guesses.
- The privilege drop no longer shells out to `setpriv`. `tests/runner.py` owns the policy
  in `drop_privileges()` and the interpreter applies it between fork and exec, and
  `probe()` proves it before the first scenario by starting one child under those
  credentials and asking what uid it came up as. A platform that cannot do that now fails
  one assertion that says so, instead of fourteen scenarios reporting that the trainer
  went away.
- `instruction.md` gained the sentence the new disk rule needs: do not write files, we
  look over the image either side of the run, anything left behind fails the submission
  whether or not the resume leaned on it.

Proof the fix is not a local accident: the oracle now scores 1 under a read-only root
filesystem, a world-writable mount the verifier is not allowed to close, dropped `CHOWN`
and `FOWNER` capabilities, a tmpfs `/tmp`, a bind-mounted `/logs`, no network, and a
64-process limit. The shipped bundle scored 0 on the first of those. And the disk rule
still bites: pointed at a writable mount the verifier cannot close,
`cheat-side-channel-file` writes its file, reproduces the state, passes the other 102
assertions and is failed by the disk check alone.

What is still unknown, stated plainly: the platform never said *why* it scored 0, so this
is a fix for every platform dependency the verifier had, not a fix for an observed cause.
The read-only-root reproduction matches the reported signature exactly, including the
duration; the writable-mount one matches the score but not the duration. If the next
reference review still fails, `/logs/verifier/premark.json` and the `env` block in
`/work/out.json` now carry enough to say which.

## Verifier contract - FROZEN

- Artifacts: `/app/train/ckpt.py`, `/app/data/feed.py`, `/app/train/noise.py`,
  `/app/train/sched.py`. Nothing else is read from the agent's container.
- The verifier bakes a pristine copy of the shipped tree, overlays those four paths onto
  it, and runs the trainer over the fourteen scenarios in `tests/scen.py`.
- Checked per scenario, all-or-nothing: `p`, `ema`, `step`, `reads`, `pos`, `upd` and the
  loop's `trace` in order, plus the lifecycle - one trainer process to begin with, one more
  per load, no process id reused.
- Checked once for the run as a whole: the privilege drop happened, the reward channel was
  closed to the run's uid, and the trainer left nothing on disk that was not there before
  it started.
- Not graded, deliberately: the checkpoint payload's length, slot order or framing;
  `draws`, because putting a held item back by winding the cursor back one and drawing it
  again is bookkeeping rather than work; `loads` and `saves`, which the driver counts and
  no implementation can move.
- Every graded field is re-derived at verification time by `tests/oracle.py`, a sealed
  from-scratch trainer sharing no code with the tree, and the ground truth's `p`, `ema` and
  `step` are additionally re-proved against the same op list with the down time compacted
  out, which never checkpoints at all.
- Tolerances: none. Everything is integer arithmetic and exact.
- Ground truth: `tests/gt.json`, generated by `authoring/build_gt.py`, root-only in the
  verifier image. `tests/oracle.py` is root-only too, so the run cannot import it.

## Decisions and their reasons

- `draws` was in the graded set during design and was taken out. It is separated only by
  `cheat-rewind-cursor`, which reproduces the same sample stream and differs only in how
  many times it asked the sampler. That is the shape the run audit rejected on the previous
  task, so it is out; `cheat-rewind-cursor` still scores 0, on the parameters, because a
  fresh draw cannot carry the bound the item was drawn under.
- The counters that bind are incremented in `data/store.py`, `train/model.py` and
  `train/opt.py`, all outside the editable set, so they measure real work for any
  implementation.
- `train/sched.py` is in the artifact set and the reference does not change it. Naming only
  the files that have to change would hand over half the diagnosis, and one of the four
  alternative correct solutions does solve it by editing that file instead.
- The trace is written by `train/loop.py` and `train/drv.py`, both non-editable, and is
  compared in order. Nothing in it is generated by agent code.
- The scenario set is readable by the run's uid and that is fine: knowing which op
  sequences execute does not produce the parameter vectors they end on.
  `cheat-peek-scenarios.sh` documents that.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Both images build | pass | `tools/docker_trial2.py`; base image had to come from a mirror and the sandbox's proxy CA had to be injected for pip, neither of which the shipped Dockerfiles carry |
| No answer leaked into agent image | pass | the built image holds 20 files: the trainer, its config, the demo scenario, the runner. The sweep cheat finds nothing |
| Oracle = 1 | pass | real two-container run, 103 assertions passed |
| Nop = 0 | pass | real two-container run |
| Cheats all score 0 | pass | 22 of 22 on the real images, including the eight reward-tamper probes and the four evasions of the bounded channel. The privilege probe reports uid 1002 and PermissionError on all twelve paths it tries |
| Alternative correct solutions = 1 | pass | 4 of 4 through the real verifier (`--variants`) |
| Oracle under a hostile container config | pass | 1 under a read-only root filesystem, a world-writable extra mount, dropped CHOWN and FOWNER, a tmpfs /tmp, a bind-mounted /logs, no network, and `--pids-limit 64` |
| `field_report.py` | pass | every cheat diverges; no graded field separates nothing |
| `preflight.py` | pass | clean |
| `harbor check` rubric | not run | `harbor` is not installed in this sandbox |

## Open questions and next steps

- `instruction.md` has not been through the contributor's own read (D1). It was drafted
  here from the task's own material and measured with `tools/textcheck.py` against both
  instructions known to have passed the AI-text screen: burstiness 0.946 against their
  0.938 and 0.926, short sentences 44 per cent, long sentences 18 per cent, and zero stock
  vocabulary, hedges, antithesis constructions, three-item lists, dash asides and
  first-person singular. No measurement can certify a classifier verdict.
- `harbor check` has not been run; `harbor` is not installed here. Every other gate has.
- The counter-grading risk that sank the previous task was audited directly here rather
  than assumed: `authoring/field_report.py` shows no dead graded field, and
  `authoring/variant_check.py` runs four alternative correct implementations through the
  real verifier. If a fifth shape is found that scores 0 on identical semantics, the
  graded set is what should change.
- The same discipline now applies to the verifier's own environment. A graded assertion
  about the machine is the environmental cousin of a graded implementation choice: it
  fails a correct submission for something the solver never touched. There is one left,
  the privilege drop, and it is kept because a verifier that cannot run agent code
  unprivileged must not report a score at all.
