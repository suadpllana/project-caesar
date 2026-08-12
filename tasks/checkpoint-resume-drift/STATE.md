# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`

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

## Verifier contract - FROZEN

- Artifacts: `/app/train/ckpt.py`, `/app/data/feed.py`, `/app/train/noise.py`,
  `/app/train/sched.py`. Nothing else is read from the agent's container.
- The verifier bakes a pristine copy of the shipped tree, overlays those four paths onto
  it, and runs the trainer over the fourteen scenarios in `tests/scen.py`.
- Checked per scenario, all-or-nothing: `p`, `ema`, `step`, `reads`, `pos`, `upd` and the
  loop's `trace` in order.
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

- The trainer is not run in process. `tests/runner.py` is a supervisor that spawns one
  unprivileged child per trainer life and talks to it over a pipe, taking its own half of
  the tree from the sealed pristine copy, so a kill in a scenario is a process dying. The
  corpus, the arithmetic kernels, the counters and the checkpoint channel are all on the
  supervisor's side, which is what makes the work counters measurements rather than
  reports. The corpus is generated from `tests/corpus.json`, a seed that is not the one
  shipped in `conf/corpus.json`, so a sample's tokens have to be asked for and every ask
  is charged.
- The image lockdown is hardening, not a graded quantity. `tests/test.sh` closes every
  directory the trainer's uid could write, best effort and never fatally, and
  `test_the_trainer_had_nowhere_to_write` then asks what that uid could actually have
  opened for writing: reachability through the directories above a path, and read-only
  mounts, both count the way the kernel counts them. See the post mortem below for why
  that distinction is load bearing.

## Reference verification failure, 2026-08-12, and the fix

The bundle went to the pipeline and came back rejected at reference verification: three
oracle attempts and three nop attempts, every one of them scoring 0. Nothing about the
submission was wrong. `test_the_trainer_had_nowhere_to_write` was scanning the whole image
for any inode carrying a write bit for uid 1002 and failing the grade on what it found, so
it was grading a property of the container the platform handed us rather than a property
of the thing being graded. Anything the harness mounts or uploads that carries a group or
world write bit fails every submission alike, the reference included.

Reproduced here exactly, by mounting the declared artifacts at `/app` as a volume with the
modes an uploader might leave: 101 assertions pass, that one fails, reward 0 for oracle and
for nop both. `find / -xdev` in the old lockdown walks past every mount, which is how the
same paths that fail the check escape the sweep that was supposed to close them.

Three changes, all in `tests/`:

- The lockdown covers `/app` as well, since everything the run reads was copied into
  `/work` before it, and it sweeps each mount rather than only the root filesystem.
  `/logs` is left alone deliberately: it is the harness's channel, and chowning a host
  directory out from under whoever mounted it is not ours to do. Its verifier directory is
  locked as before and checked on its own.
- Every chown and chmod in the lockdown is non-fatal. `set -Eeuo pipefail` plus a chown
  that a runtime refuses on a mount point was a second way to score every attempt 0, this
  time before the run started at all.
- The check asks whether the trainer's uid could have written, not whether a write bit
  exists somewhere. A world-writable directory under a directory that uid cannot walk into
  is not a channel, and neither is anything on a read-only mount. Verified both ways in the
  container: `/tmp` closed with a 777 directory inside it passes, and the moment `/tmp`
  itself is opened, the same tree fails.

The general form of it, for the next task: the verifier may grade the submission and the
work it caused, and nothing else. A container property belongs in `test.sh` as hardening,
where failing to achieve it costs an anti-cheat guarantee, not the reference's score.

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
  the files that have to change would hand over half the diagnosis, and one of the three
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
| No answer leaked into agent image | pass | the built image holds the trainer, its config, the demo scenario and the runner. The sweep cheat finds nothing |
| Oracle = 1 | pass | real two-container run, 102 assertions passed |
| Nop = 0 | pass | real two-container run |
| Cheats all score 0 | pass | 22 of 22 on the real images, including the seven reward-tamper probes and the four evasions of the bounded channel. The privilege probe reports uid 1002 and PermissionError on all twelve paths it tries |
| Alternative correct solutions = 1 | pass | 4 of 4 through the real verifier (`--variants`) |
| `field_report.py` | pass | every cheat diverges; no graded field separates nothing |
| `cheat_report.py` | pass | host run; `test_the_trainer_had_nowhere_to_write` fails there for every entry including the reference, because an ordinary host `/tmp` is open, and the container run is the authority on that one |
| Verifier survives a hostile container | pass | oracle scores 1 with the artifacts arriving on a world-writable `/app` mount, a world-writable `/logs` mount, a read-only mount carrying world-writable files, a stray `tmpfs`, and `no-new-privileges` |
| The lockdown still bites | pass | a world-writable directory or a uid-1002-owned directory left open after `test.sh` fails the run; the same directory under a closed `/tmp` does not |
| `preflight.py` | pass | no errors; one warning, the standing one for a verifier that executes agent code, which this one does under supervision and with the reward-tamper cheats it asks for |
| `harbor check` rubric | not run | `harbor` is not installed in this sandbox |
| Reference verification on the platform | fail, then fixed here | 0 of 3 oracle attempts on 2026-08-12; cause reproduced and fixed, see the post mortem above. Not re-run on the platform |

## Open questions and next steps

- `instruction.md` has not been through the contributor's own read (D1). It was drafted
  here from the task's own material and measured with `tools/textcheck.py` against both
  instructions known to have passed the AI-text screen: burstiness 0.979 against their
  0.938 and 0.926, short sentences 44 per cent, long sentences 20 per cent, and zero stock
  vocabulary, hedges, antithesis constructions, three-item lists, dash asides and
  first-person singular. No measurement can certify a classifier verdict.
- `harbor check` has not been run; `harbor` is not installed here. Every other gate has.
- The counter-grading risk that sank the previous task was audited directly here rather
  than assumed: `authoring/field_report.py` shows no dead graded field, and
  `authoring/variant_check.py` runs four alternative correct implementations through the
  real verifier. If a fifth shape is found that scores 0 on identical semantics, the
  graded set is what should change.
- The platform's own verifier log for the failed run has not been read; the diagnosis
  above comes from reproducing the same signature locally, oracle and nop both 0 with
  every graded axis passing. If the rebuilt bundle fails reference verification again,
  the job directory's `ctrf.json` names the assertion and is the first thing to fetch.
