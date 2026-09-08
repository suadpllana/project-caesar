# Task state

Working memory for `span-close-step`. Assume the next session starts with no memory of this
one - anything not written here is lost. This file never ships in the zip.

## Current stage

`Stage 7 - pre-flight and packaging`. Every local gate has been run; the container gates
cannot be run in this workspace (see "Infrastructure", below).

## Assistant's assigned role

You are a training-infrastructure engineer: you own the data path and the optimizer step of a
training loop - packing, accumulation, clipping, the schedule, the checkpoint - rather than the
model architecture. You have debugged loss curves that moved when nothing about the data moved.

## Source repository

- Repo URL: none - idea-based task.
- Task shape: authored from scratch; no vendored code, so no license, pinning, identifier
  degradation or upstream-diff question arises.

## Task summary

The agent is given a small pure-Python trainer in `/app`. Documents are packed end to end into
fixed-length sequences, so a document is often read across several optimizer steps; the step
consumes a fixed number of sequences, split across accumulation groups and workers. Six policy
files decide what a step does: which documents settled in it, what a settled document's loss and
gradient are, how the step is normalized and clipped, whether the step is taken and what it does
to the parameters, which settled documents go back on the stream for another pass, and what a
checkpoint carries. The shipped versions of all six are coherent and wrong. The verifier runs the
submitted trainer over literal and nonce run scripts in a pristine tree and compares every printed
line exactly.

## Why it is hard

- Expert time estimate: 8 hours.
- Why a frontier agent cannot one-shot the plan (the strategic answer): the plan it forms first is
  the streaming one that the shipped trainer already implements - score each token as its
  micro-batch arrives and fold it into per-document statistics - which is what the published
  accounts of accumulation under a memory bound describe, is correct for every document that
  begins and ends inside one step, and is wrong for one read across steps, because a sum of scores
  taken at different parameter points is not the objective at any of them; and the requeue rule
  makes the packing depend on the trainer's own losses, so a plan that settles the data layout up
  front is wrong in a second, independent way that only shows several steps after the decision
  that caused it.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C4. A1 - the memorized
  accumulation idiom is specifically wrong here and the shipped tree implements it
  convincingly; A2 - the objective, the
  settlement rule and the requeue loop are stated operationally and never named, so no search term
  reaches them as a unit; A3 - bounded per-document state and a single-parameter-point objective
  pull against each other and are reconciled only by dropping the statistics and rescoring at
  settlement; B2 - eleven rules that hold simultaneously and interact (settlement feeds the
  divisor, the divisor feeds the loss, the loss feeds the requeue, the requeue feeds the packing,
  the packing feeds settlement); C1 - both sides fenced, with a family in which nothing straddles a
  step and nothing is requeued, so a cautious reading cannot pass by refusing to act; C2 - the
  shipped runner reports the submitted trainer's own behaviour and is not an oracle for any graded
  decision; C4 - exact all-or-nothing comparison of every printed line over 25 literal and 385
  nonce scripts drawn after the agent has finished.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was
  to keep per-open-document streaming statistics with the customary rescaling, finish a document
  when its last token goes past, average the finished documents, clip, step, and serialize the
  statistics into the checkpoint. It is wrong in the place the task is built on: the statistics
  are taken under parameters that have since moved, so the loss reported for a document read
  across two updates is the loss of no model. Correcting it does not patch the fold, it deletes
  it - the document has to be scored from its tokens at settlement - which inverts the memory
  argument that motivated the fold. My plan was also wrong a second time, later: I would have
  computed the packing once, and the requeue rule makes the sequence boundaries depend on losses
  the trainer has not produced yet.
- Estimated solves out of 8: 2 (designed for the hard edge; the realized rate drifts up).
- Difficulty score anchor: not yet submitted, so no anchor.
- Score history: none yet.
- Leak audit (docs/DIFFICULTY.md), mechanism by mechanism, what in the bundle would let an agent
  discover, name or verify it without reasoning:
  - Settlement and the held step: nothing. `tools/onelinecheck.py` finds an exact two-term rule
    for both, which is correct and intended - they are stated plainly in the instruction and are
    not where the difficulty lives.
  - The requeue decision and whether a step clips: nothing. Both were measured as having no exact
    rule at depth <= 2 over the state an agent can read at that moment, because both need the
    loss, which needs the objective read the right way.
  - The objective at one parameter point: nothing shipped derives it. There is no expected-output
    file, no journal, no counter, and no pair of exposed quantities that reconstructs a loss.
  - Answer material: the frozen answers, the generator and the sealed model live in
    `tests/seal/`, which is root-only in the verifier image, and the nonce is never copied into
    the sandbox. `cheat-answer-key.sh` and `cheat-forge-from-gt.sh` measure both halves.
  - Unused affordances: preflight warns about every cross-module entry point (`feed.add`,
    `feat.vec` and so on) because its detector does not follow attribute calls; each is called
    through `ops.py` or the policy. The retained bundles carry the identical warnings.
- Expert path, described step by step:
  1. Run both shipped scripts, read `ops.py` to see the six seams and what each returns, read
     `feed.py` to see that the stream is a flat token queue cut into fixed sequences.
  2. Notice that `pick.take` scores tokens as they arrive and that `fold.one` finishes from those
     statistics; work out that this is only the objective when a document is read inside one step.
  3. Replace the statistics with token counting in `pick.py` and a from-scratch scoring in
     `fold.py`, using `feat.vec` and the length and target in `feed.info`.
  4. Fix the divisor and the reported length in `norm.py`; fence the two by hand on a script with
     one document and several micro-batches.
  5. Fix `turn.py`: hold on nothing settled, read the rate before the count advances, take the
     average after the update with the warming decay.
  6. Fix `again.py`: per-document threshold, allowance along the chain, append at the tail; check
     against a script where the same name is declared twice.
  7. Fix `keep.py` last, because what a checkpoint carries is decided by what the other five now
     keep in `run.st`.
- Originality check: searched on 2026-09-08 for the combination and for each part. Accumulation
  loss-normalization bugs, sequence packing, and streaming log-sum-exp are each written up widely;
  nothing describes a per-document objective settled at the step that finishes the document, with
  a loss-driven requeue loop feeding back into the packing. No public write-up of this task or a
  close variant. No retained task in this repository grades anything similar: `tools/simcheck.py`
  reports "this task does not grade what any earlier one grades".

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/train/pick.py`, `/app/train/fold.py`, `/app/train/norm.py`,
  `/app/train/turn.py`, `/app/train/again.py`, `/app/train/keep.py`. Nothing else is read.
- What is checked: the exact sequence of printed lines for every run script, all-or-nothing, over
  25 literal scripts frozen in `tests/seal/gt.json` and 385 nonce scripts generated from a
  per-trial nonce after the agent has finished. The nine graded decisions are listed at the top of
  `tests/seal/test_outputs.py`.
- Tolerances: none. Printed numbers carry six digits after the point; the generator keeps only
  scripts whose unrounded clip and requeue decisions stand at least 1e-6 from their boundaries and
  whose printed values stand at least 1e-9 from a rounding edge, so no graded line turns on an
  implementation's rounding noise. Measured over 385 scripts: tightest margin 3.2e-4, nearest
  rounding edge 1.0e-9.
- Ground truth, and where it lives: `tests/seal/gt.json` for the literal scripts, frozen from the
  sealed model and cross-checked against the reference; `tests/seal/model.py` for everything else.
  Both are root-only in the verifier image.
- Prong C tactics used: C1 (the `plain` family and the `unclipped-step` case fence the
  must-still-work side), C2 (the shipped runner reports the submitted trainer, not the truth),
  C4 (exact, all-or-nothing, seven shaped families plus enumerated corners).
- Route-around guard: `artifacts` names only the six policy files. The runtime, the runner and the
  scripts are the verifier's own pristine copies, so the agent cannot restructure the problem.

## Decisions and their reasons

- Six editable files rather than one, because the graded decisions genuinely live in different
  places and fixing one changes what the next receives. Measured against the retained bundles:
  1 to 7 editable files, 229 to 544 environment lines; this is 6 files and 310 lines.
- No resource gate. The difficulty is semantic, and a timeout here would punish a correct
  implementation rather than a naive one - `note-carry-forward`'s lesson is to profile before
  inventing a budget, and there is nothing here whose naive form is measurably infeasible.
- Category `ML / Training`, not `Software / Systems`. The graded decisions need to know that a
  gradient is evaluated at one parameter point, that the divisor defines the objective, that a
  schedule is keyed to optimizer steps, that clipping precedes momentum and an average follows the
  update. `tools/catcheck.py`: environment 18 hits, prose 94.
- The trainer package is named `train`, not degraded further. Degrading names is for facts that
  would otherwise be handed over; the name of the training package hands over nothing, and the
  category has to be visible in the tree rather than only in the story.
- `tests/seal/` is root-only. The worker executes agent code in a process that has `/tests` on its
  import path, so the model, the generator, the frozen answers and the nonce would all have been
  importable. The scripts for a trial are now chosen by a root-only stage before the worker starts
  and handed over as a list; the worker has nothing to derive an expected trace from.
- Two repo tools were taught about that layout rather than the layout bent to suit them:
  `tools/forgecheck.py` now falls back to `tests/seal/gt.json`, and `scripts/preflight.py` looks
  for `test_outputs.py` anywhere under `tests/`. Two tools disagreeing about where a file lives is
  how this kit produced a confident wrong answer once before.

## Evidence

Everything below was run in this workspace. Host emulation means
`authoring/span-close-step/trial.py`, which reproduces the grading faithfully - same worker, same
pytest module, same nonce generation after the agent finishes - and does not reproduce the
isolation (no privilege drop, no locked reward channel, no survivor sweep).

- Reference against the sealed model: 385 nonce scripts, 9648 graded lines, 0 disagreements
  (`agree.py`). 25 literal scripts agree as well and are frozen from that agreement.
- Oracle and nop, host emulation: reward 1 and reward 0.
- 17 whole-solver wrong readings (`readings.py`): every one separated, moving between 5.5% and
  100% of the nonce population. `tools/readingcheck.py` confirms each is also separated by a named
  literal case, so a failure says which rule broke.
- 5 independent correct implementations (`variants.py`): each 410 of 410 scripts and trial reward
  1. They differ in how open documents are stored, how settlement order is derived, whether the
  objective uses the customary shift by the largest score, and what shape the checkpoint takes.
- 19 cheats, all reward 0, each with the test that caught it recorded (`cheat_report.py`):
  12 wrong readings, 6 attacks on the verifier, and one forgery carrying every frozen answer.
- `tools/onelinecheck.py`: the requeue decision and the clip decision have no exact rule at depth
  <= 2 over readable state; settlement and holding do, as intended.
- `tools/imagecheck.py`: the image would hold 15 files at `/app`; the reference dropped in runs
  both shipped scripts.
- `tools/forgecheck.py`: the forgery probe is recognised as carrying ground truth and the whole
  cheat suite scores 0 through it.
- `authoring/span-close-step/sealcheck.py`: the verifier's `tests/` staged under the mode bits
  `tests/Dockerfile` applies, then read from uid 1002 through `setpriv`. The model, the generator,
  the case list and the frozen answers are all unreachable; `worker.py` and the pristine tree, the
  two things the worker legitimately needs, are readable. This is real uid-based evidence for the
  seal without a container; it says nothing about the locked reward channel or the survivor sweep,
  which need one.
- `tools/textcheck.py` against the brief that passed the screen: no axis is more regular than the
  reference. `tools/structcheck.py` and `tools/hintcheck.py`: clean.
- `scripts/preflight.py`: no errors. `catcheck`, `solvecheck`, `deadfieldcheck`,
  `extraneouscheck`: clean.
- `scripts/package.py` then `tools/zipcheck.py`: 67 entries, no findings, no cache or state files
  in the archive.
- `tools/simcheck.py`: NEAR on `environment/Dockerfile` (five lines of boilerplate identical
  across every retained bundle), `tests/Dockerfile` and `tests/test.sh`. `tests/reap.py` was
  rewritten after simcheck flagged it as a near copy. Conceptually distinct from every earlier
  task.

## Infrastructure

Docker's daemon runs in this workspace but the egress policy blocks the registry CDN
(`403` on `production.cloudfront.docker.com`), so no base image can be pulled and neither image
can be built. `harbor` is not installed. The container gates - `harbor run -a oracle`, `-a nop`,
`tools/docker_trial.py` - are therefore **not run**, and with them the three things only a
container can show: the privilege drop, the root-only reward channel, and the survivor sweep. The
reward-tamper cheats are written and score 0 under host emulation, where they cannot mean what
they mean in a container. This is the single largest residual risk in the bundle and the handover
says so.

## Stage 7 re-attack, against the finished bundle

Read the final brief cold and tried to one-shot the plan with the real tree in front of me. The
six-file plan does form: count tokens per open document and settle at the length, rescore at
settlement from `feat.vec`, mean over the settled, report before clipping, hold on nothing
settled, rate before the count advances, average after, allowance along the chain, append at the
tail, checkpoint whatever the other five kept. That is the plan, and the brief states every rule
that goes into it - which is the design, not a leak: nothing here is withheld and every deviation
is on the page. What the brief does not hand over is the reconciliation. Settlement order has to
be recovered from what `pick` can actually see, the checkpoint's contents are decided by choices
the other five files have not made yet when you start, and the requeue rule puts the packing under
the trainer's own output, so a plan that fixes the data layout first is wrong in a way that
surfaces several steps later. Eleven rules are graded together, all-or-nothing, over 410 scripts.

The honest risk, stated rather than argued away: the reference is 89 lines of code across six
files. That is comparable to `guard-mark-unwind` (105) and well above the ~40 lines the quality
review called too little work when it failed `reach-pair-sweep` on `difficult`, but it is at the
low end of the retained band, and the environment at 310 lines is in the lower half of 229-544.
If this task comes back solved 8 times, the repair is not more rules - it is a mechanism the
brief can state without also stating how to satisfy it.

Estimate after the re-attack: unchanged at 2 of 8, with the realized rate expected to drift up.

## Self-probe

Not run, and it could not have been: the author wrote the contract, the shipped wrong trainer and
the sealed model, so a cold solve by this session would measure memory rather than difficulty. In
its place stand the reading separations (17 of 17 separated, each by a named case), the
`onelinecheck` result (the two decisions that carry the task have no short rule), and the
measurement that the shipped tree is wrong on 90% of the population in the one dimension the first
plan gets wrong.

## Remaining

- Container gates, if a workspace with a reachable registry becomes available. `tests/test.sh`
  and both Dockerfiles are the files no local gate executes: they are syntax-checked, LF-only, and
  read by `tools/imagecheck.py`, but they have never been run.
- The external easiness and difficulty probes.
