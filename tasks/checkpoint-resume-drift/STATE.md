# Task state

## Current stage

`Stage 8 - Hardened after an anti-cheat probe rejection, re-gated locally`

## Assistant's assigned role

Senior training-infrastructure engineer for large post-training runs: checkpointing and
resume, data feeders and packers, gradient accumulation, learning-rate and curriculum
schedules, and the exact reproduction of a preempted job across a restart.

## The anti-cheat probe rejection, and what it cost

The task shipped, cleared its build gates, and then lost the anti-cheat probe. An
adversarial agent scored 1 without solving it. The judge's account, in its own terms:

- `/app/train/ckpt.py` kept all carried state in a module-level `_HOLDOUT` dict, which
  survived the in-process `cx.down()` that the driver called a kill, and sent a
  four-integer handle through the checkpoint channel. The bounded payload was not answered.
  It was stepped around.
- A `_Quiet` meter stand-in blinded the `reads`, `pos` and `upd` counters while the
  submission replayed the whole stream, so the replay was never charged.

Both of those were the same defect wearing two hats: **everything the verifier compared
against lived in the same process as the code it was grading**. A kill was an attribute
assignment. A counter was an integer on an object the agent's own file was handed. In
Python, in one process, neither of those can be defended. The fix is structural rather
than a patch on the old shape, and it is what the rest of this file describes.

Three things changed, and nothing about the problem the agent is asked to solve did.

1. **A kill is the death of a process.** The trainer now runs as a child process that a
   supervisor spawns, one per life. A `kill` op signals that process group, waits, and
   reaps every process left running as the trainer's uid. The following `load` starts a
   new process from nothing. The only thing that crosses is the vector the checkpoint
   channel accepted, because the channel lives in the supervisor.
2. **The counters are measurements, not reports.** `reads`, `pos` and `upd` are tallies
   the supervisor keeps while serving the trainer. The corpus, the gradient kernel and the
   optimiser kernel are all on its side of the link. A trainer cannot lower a counter it
   never holds.
3. **The corpus is not derivable from the tree.** It is generated from a seed that lives
   only in the supervisor, and the seed used for grading is not the one in
   `environment/app_src/conf/corpus.json`. A submission that computes a sample's tokens
   instead of asking for them gets the tokens of a different corpus, so "answer your own
   requests and skip the charge" produces a wrong run rather than a free one.

The editable surface did not move. `train/ckpt.py`, `data/feed.py`, `train/noise.py` and
`train/sched.py` have the same API, the reference solution is byte-for-byte the same
answer, and all four alternative correct implementations still score 1.

## Source repository

- Repo URL: https://github.com/vllm-project/vllm (issue tracker used as the seed only)
- Task shape chosen: authored on top, not an ablation of upstream code. No source from the
  repository is vendored. The trainer in `environment/app_src/` is written for this task:
  a CPU-only, integer-arithmetic training loop with the organs the failure needs (a sample
  store, an epoch sampler, a length packer with a carry slot, a per-row stochastic stream,
  an accumulation loop, an optimiser with a shadow average, a schedule memo, a bounded
  checkpoint channel), split across a supervisor and the trainer process it drives.
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
  register of ordinary internal code (`feed`, `pack`, `samp`, `drv`, `ckstore`, `svc`,
  `lk`, `hd`, `ws`, `ntok`, `at_`).
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
    fixed is in `train/loop.py`; what the channel accepts is in `core/ckstore.py` and
    `core/svc.py`.
  - Prong B2: the amendment rule, the latched bound, the stream position, the mid-window
    state, the epoch boundary and the payload cap all have to hold at once.
  - Prong C1: fenced both ways. `amend-window` fails an over-derivation; `amend-lr`,
    `amend-bound` and `amend-ema` fail an over-restoration; `straight` and `empty-carry`
    fail anything that breaks ordinary behaviour or cannot encode an empty carry slot.
  - Prong C2: the obvious oracle is denied for the accounting. The agent can compare a
    resumed run against its own uninterrupted run and catch parameter drift, which is fair
    and is the expert path; it has nothing to compare read counts against, and since the
    graded corpus is not the one in its tree, it has no absolute numbers to chase either.
  - Prong C3: two resource gates. The channel refuses an oversized payload outright, which
    kills "serialise the trainer". The read counter kills reconstructing position by
    replaying the stream, which is otherwise a correct plan, and the counter is now kept
    by the process that serves the samples, so the replay cannot be made free.
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
     parts a fresh trainer is built from.
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

Frozen a second time. The first freeze held through the build gates and lost the
anti-cheat probe, so the parts of it that were unenforceable were replaced rather than
patched. What is graded did not change; where it is measured did.

- Artifacts: `/app/train/ckpt.py`, `/app/data/feed.py`, `/app/train/noise.py`,
  `/app/train/sched.py`. Nothing else is read from the agent's container.
- The verifier bakes a pristine copy of the shipped tree, overlays those four paths onto
  it, and runs the trainer over the fourteen scenarios in `tests/scen.py`.
- **Process model.** `tests/runner.py` is the supervisor. It imports `train/drv.py` and
  `core/svc.py` from `/pristine`, never from the overlaid tree, and never imports
  `build.py` or anything `build.py` reaches, so no agent code runs in it. Each trainer life
  is a child process launched through `setpriv` as uid 1002, in its own session, with a
  scrubbed environment and no writable directory anywhere on the image. A `kill` op signals
  the process group, waits for it, and reaps every remaining process of that uid.
- **What crosses a kill.** The vector the checkpoint channel accepted, and nothing else.
  The channel is `core/svc.py`'s, on the supervisor's side of the pipe; `core/ckstore.py`
  in the tree is a proxy to it. Memory dies with the process, disk is closed off, and
  survivors are reaped.
- **Where the counters come from.** The supervisor. `reads` is one per sample it served,
  `pos` is the positions it computed gradients over, `upd` is the optimiser steps it
  applied, `draws` is one per sampler request. The trainer reports only `p`, `ema` and
  `step`, all of which require the real corpus to be right.
- **Where the trace comes from.** The supervisor, from the requests it served. An update
  entry is written when it applies an update. A microbatch entry is written only if the row
  count and token count the loop announces match the gradients it just computed; a mismatch
  is an error, not a trace line.
- **The corpus.** Generated by the supervisor from `tests/corpus.json` (root-only, 600).
  The tree ships `conf/corpus.json` with a different seed for the agent's own runs.
  `authoring/corpus_check.py` proves the graded seed still puts every scenario in the
  position its aim describes, and `build_gt.py` refuses to write without it.
- Checked per scenario, all-or-nothing: `p`, `ema`, `step`, `reads`, `pos`, `upd` and the
  `trace` in order. Plus, per scenario, that the number of trainer processes was one more
  than the number of loads and that no process id was reused.
- Not graded, deliberately: the checkpoint payload's length, slot order or framing;
  `draws`, because putting a held item back by winding the cursor back one and drawing it
  again is bookkeeping rather than work; `loads` and `saves`, which the supervisor counts
  and no implementation can move.
- Every graded field is re-derived at verification time by `tests/oracle.py`, a sealed
  from-scratch trainer sharing no code with the tree, and the ground truth's `p`, `ema` and
  `step` are additionally re-proved against the same op list with the down time compacted
  out, which never checkpoints at all.
- Tolerances: none. Everything is integer arithmetic and exact.
- Ground truth: `tests/gt.json`, generated by `authoring/build_gt.py`, root-only in the
  verifier image. `tests/oracle.py` and `tests/corpus.json` are root-only too.

## Decisions and their reasons

- The supervisor runs as root and the trainer does not. `docs/VERIFIER-ISOLATION.md` rule 1
  is that the process which imports, calls or execs agent code must be unprivileged, and it
  is: the supervisor drops to uid 1002 with `setpriv` before `exec`ing the interpreter that
  loads any of the tree. Root is needed on the supervisor side to do that drop and to reap
  the uid afterwards. It parses the trainer's frames as hostile input, bounded in length,
  integer-typed, range-checked, and it holds no state the trainer can name.
- The arithmetic kernels moved to the supervisor along with the counters. Keeping them in
  the trainer would leave `pos` and `upd` forgeable, and moving them costs nothing: the
  decisions the task is about are all still in the tree the agent reads.
- The graded corpus differs from the shipped one. Without that, a submission can compute a
  sample's tokens from the seed in `conf/train.json` and replay the stream without ever
  asking the service for anything, which is the `_Quiet` exploit in a new coat.
  `cheat-quiet-link` is exactly that attempt and it scores 0 on the parameters.
- `draws` was in the graded set during design and was taken out. It is separated only by
  `cheat-rewind-cursor`, which reproduces the same sample stream and differs only in how
  many times it asked the sampler. That is the shape the run audit rejected on the previous
  task, so it is out; `cheat-rewind-cursor` still scores 0, on the parameters, because a
  fresh draw cannot carry the bound the item was drawn under.
- `train/sched.py` is in the artifact set and the reference does not change it. Naming only
  the files that have to change would hand over half the diagnosis, and one of the four
  alternative correct solutions does solve it by editing that file instead.
- The scenario set is readable by the run's uid and that is fine: knowing which op
  sequences execute does not produce the parameter vectors they end on, and now it does not
  produce the corpus they were computed over either. `cheat-peek-scenarios.sh` documents
  that.
- The instruction states the process model and the corpus split plainly. Both are things
  the grade depends on that are not derivable from the tree, so under the content rules
  they have to be stated; neither hands over which holders belong in the checkpoint.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Both images build | pass | `tools/docker_trial2.py`; base image from a mirror and the sandbox's proxy CA injected for pip, neither of which the shipped Dockerfiles carry |
| No answer leaked into agent image | pass | the sweep cheat finds nothing; the agent image carries `conf/corpus.json`, which is its own corpus and not the graded one |
| Oracle = 1 | pass | real two-container run, 101 assertions passed |
| Nop = 0 | pass | real two-container run |
| Cheats all score 0 | pass | 22 of 22 on the real images, including the four channel evasions and the seven reward-tamper probes |
| Privilege probe | pass | reports uid 1002 and `PermissionError` on all twelve paths: reward channel, ground truth, sealed trainer, graded corpus, pristine tree, tests, work file, its own tree, `/tmp`, `/dev/shm`, `/var/tmp`, `/app` |
| Alternative correct solutions = 1 | pass | 4 of 4 through the real verifier (`--variants`) |
| `corpus_check.py` | pass | every scenario keeps the position its aim describes under the graded corpus |
| `field_report.py` | pass | every cheat diverges; no graded field separates nothing |
| `variant_check.py` | pass | 4 of 4 clean |
| `preflight.py` | pass | clean |
| `harbor check` rubric | not run | `harbor` is not installed in this sandbox |

Two of the channel-evasion probes are container-only. The host emulation in `authoring/`
has a writable `/tmp` and no privileged reaper, so `cheat-side-channel-file` comes out
clean there and `cheat-daemon-holdout` fails for the wrong reason;
`tools/docker_trial2.py checkpoint-resume-drift --all` is the run that proves them, and it
does.

## Open questions and next steps

- The probe that rejected this task is the gate to re-run first. Every move in the judge's
  account is now a script in `cheat/` scoring 0 on the real images, and the two structural
  holes behind them are closed, but an adversary is not limited to the moves it already
  made.
- Difficulty was calibrated before the hardening and has not been re-probed. The editable
  surface, the reference solution and every cheat signature are unchanged, and
  `corpus_check.py` proves the fourteen scenarios still sit where their aims say, so the
  estimate of 1 to 2 solves of 8 carries over. It is an inference, not a measurement.
- `instruction.md` was re-measured after the rewrite: burstiness 0.951 against the two
  passing briefs' 0.938 and 0.926, 44 per cent short sentences, 17 per cent long, 1047
  words, and zero stock vocabulary, hedges, antithesis constructions, three-item lists,
  dash asides and first-person singular. `tools/textcheck.py` reports no findings against
  either reference. No measurement can certify a classifier verdict.
- `harbor check` has not been run; `harbor` is not installed here. Every other gate has.
