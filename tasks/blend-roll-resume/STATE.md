# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one — anything not written here is lost.

## Current stage

`Stage 7 — Pre-flight and packaging`

## Assistant's assigned role

You are a training-infrastructure engineer on a large pretraining stack: the data plane rather
than the model. You own the blended sample feed — the mixture manifest, the per-source
permutations, the draw schedule that turns weights into an interleaving, the rank/micro-batch
layout under gradient accumulation, and the checkpoint that has to make a restarted run pick up
exactly where the dead one left off. You have debugged runs that silently re-trained data after
a resume, and runs where a corpus that had been retired came back because it was restored out of
a checkpoint instead of read from the manifest.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? not applicable - the tree is authored here, so no upstream names exist
- Proper-noun sweep done? Nothing in the tree names a product, project, company or person
- Upstream-diff check: not applicable, there is no upstream

## Task summary

`/app` is the sample feed of a training run: it turns a run script into the exact stream of
samples handed to each rank. Sources are declared with a size, a weight and a cap on how many
epochs they may serve. Draws are interleaved by a stated draw rule, each source serves its
samples in a per-epoch permutation, a capped source leaves the blend when it finishes its last
epoch, weights change mid-run, and the trainer checkpoints, dies and restarts at a different
number of ranks, micro-batch size and accumulation depth. The shipped feed is wrong in six files
and can only reach a queried step by replaying every step, which the stated limit forbids at the
stated scale. The agent makes it right and makes it affordable.

## Why it is hard

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the plan every account of
  resumable training supplies - keep cursors, reshuffle per epoch, fast-forward by replaying what
  was consumed, restore the sampler with the checkpoint - is coherent, is what the shipped feed
  already does, and is wrong three ways at once here. It replays, and a query names a step
  millions of steps in. It restores the mixture out of the checkpoint, and this spec makes the
  mixture durable and the sampler state not. And it reads a running draw total, where the rule
  reads a counter that goes back to zero every time the blend changes. None of that is visible
  until the agent has built the thing and run it against a script it did not write.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4 - in this task's terms:
  - A1: every retrievable account of resuming a data feed restores the sampler state and the
    mixture together and fast-forwards by replaying; both are specifically wrong here.
  - A2: the draw rule is written as smallest counter over weight with the earlier source taking a
    tie, and the cap rule as leaving instead of starting another epoch. Stride scheduling,
    virtual time, deficit and fair queueing are never named, so recognising that the schedule can
    be inverted at all is the discovery.
  - B2: ten rules hold at once and several change what another means (the pairs are listed in the
    difficulty record; `tools/onelinecheck.py` measures that none of the four graded quantities
    has an exact rule at depth two over the raw fields the tree exposes).
  - C1: both sides of the resume fence are graded - a restart that always rebases the counters
    fails `back-plain` and `back-hold`, and one that never rebases fails `back-rebase` and
    `back-swap`.
  - C2: no query exposes a counter, a draw index or the source a draw went to; the only local
    check is the shipped feed, wrong in six places, or a simulator the agent writes from its own
    reading of the rules, which confirms the speed-up and nothing about the semantics.
  - C3: the step-by-step reading is exactly correct and cannot reach a step millions in inside
    the stated 60 second limit. Measured below.
  - C4: exact lines, all-or-nothing, over 31 enumerated scripts plus 363 generated from a seed
    drawn after the agent's container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  a per-source cursor and epoch, a heap keyed by counter over weight, a step loop that draws
  `ranks*micro*accum` samples and hands them out, and a checkpoint holding the cursors and the
  step number. That plan is semantically right about the draw order and the permutation and wrong
  about three things I would only find later: that the counters are per blend rather than per run,
  that the checkpoint must not bring a departed source back, and that no amount of optimising a
  step loop reaches step three million. The repair for the last is not an optimisation, it is a
  different program: solve for the draw counts at an arbitrary point, then discover that a
  departure rebases the counters so the solution holds only inside one segment, and rebuild the
  run as a walk over segments bounded by departures, weight changes and script lines.
- Estimated solves out of 8: 2 (designing for the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py on authoring/blend-roll-resume/difficulty.toml):
  attempt 1 on 2026-09-15 scored 97/100 before any code (the three points lost were the `shape`
  axis measuring an empty task folder). Re-run at Stage 7 against the built tree: 100/100, with
  236 environment Python lines, 6 editable files, 291 reference lines, 36 cheats and 2 variants.
  No hard stop at either point.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-15, 97 on the
  design; 2026-09-15, 100 on the built tree after the gate timings were measured and the record's
  planned sizes were replaced by the measured ones.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning?
  - The draw rule: the shipped `pick` reads the counter but never rebases it, so the quantity it
    holds is the wrong one, and nothing in the tree derives the right one. No op returns a
    counter, a draw index, or which source a draw went to.
  - The departure boundary: no field records a departure step; `done` lines are output the agent
    must produce, not data the tree ships.
  - The checkpoint rule: `keep` ships storing the blend and restoring it, which is the wrong
    reading; the manifest (`mix/book.py`) and the run state (`mix/hold.py`) are separate frozen
    records, and which of the two a value belongs to is stated in the brief and nowhere else.
  - The scale boundary: the shipped feed replays, so it demonstrates the problem and not the
    answer; `progs/wide.txt` is at the stated size and the shipped feed cannot finish it.
  - The permutation: `perm.py` is shipped correct and frozen. It turns a seed, a source index and
    an epoch into an order and knows nothing about the blend, the counters or the schedule. It is
    the primitive the task is not about, and shipping it stops the task being a guessing game.
  - Ground truth, the sealed model and the pristine tree exist only in the verifier image, in a
    directory locked to root at mode 700 before any submitted code runs. Measured: the
    answer-key probe records `PermissionError(13)` and the privilege probe records uid 1002 with
    `PermissionError` on the reward file, the sealed model and the grader.
  - Measured rather than asserted: `tools/onelinecheck.py` finds no exact rule at depth two for
    any of the four graded quantities, over the raw fields the tree exposes at the moment of the
    decision. An earlier run did find one - the counters stand iff the weight total holds - which
    was a real hole: no script traded two weights. `back-swap` and a `late`-family shape now do,
    and `cheat-rebase-by-sum` is the reading kept as a cheat.
- Expert path, described step by step:
  1. run the shipped feed on `progs/tiny.txt` and reproduce the line the brief calls wrong;
  2. read the frozen driver for the op language, what the two state records hold, and what a
     query is allowed to change;
  3. settle the draw rule: counters are per blend, and the tie at a segment start always falls to
     the earliest declared source;
  4. derive the count of draws a source has taken after N draws of a segment, by binary search on
     the virtual time the N-th draw sits at;
  5. read the same relation the other way to get the draw at which a capped source takes its last
     permitted sample, and take the earliest such draw as the segment end;
  6. rebuild the run as a walk over segments bounded by departures, weight changes and script
     lines, so the cost follows the number of blend changes rather than the number of steps;
  7. settle the checkpoint against the manifest: restore epochs, cursors and counters, leave
     departures and weight changes standing, rebase the counters only when the two disagree;
  8. materialise a permutation only for the step a query names, and settle that one step draw by
     draw so a departure inside it lands in the right place;
  9. generate wide scripts at the stated scale and time the step-by-step reading against the limit.
- Originality check: searched 2026-09-15 for resumable data loading across a changed world size,
  stateful blended samplers, per-epoch reshuffling, and closed-form inversion of weighted
  round-robin schedules. What exists is the substrate: framework pages on saving sampler state
  with the checkpoint and fast-forwarding by skipping consumed batches (MindSpore/MindFormers,
  HuggingFace `skip_first_batches`, VISSL's stateful sampler, NeMo and Megatron blended datasets),
  and the scheduling literature on stride and smooth weighted round robin. None of it plans this
  task: no page has per-blend counters that rebase, a durable mixture against a rolled-back
  sampler, a cap that removes a source mid-step, or a requirement to reach an arbitrary step
  without replaying. The retrieved fast-forward - replay, and scale the skip with the batch size -
  is specifically wrong here. No write-up of this combination was found.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace: authoring/blend-roll-resume/trace.md, walked from the verifier, no row
  left NOT STATED, `tracecheck` clean. 4 test functions, 31 enumerated cases, 6
  artifacts, the 60 s clock, and every top-level unit of the sealed model split into one row per
  rule it applies with its line range. No row was left NOT STATED. Three rows had no sentence on
  the first pass and were repaired rather than dropped: the frozen-truth check and the
  family-coverage check now cite the sentences that stand behind them, and the exact-comparison
  row now names the independent implementations on disk. `python tools/tracecheck.py
  blend-roll-resume` is clean.
- Identifiability: 23 readings enumerated, 21 of them separated by the enumerated set and 2
  ruled out by the clock alone. They are built as directories of editable files by
  `make_readings.py`, which asserts every patch fired. `tools/readingcheck.py` reports all 21
  semantic readings separated by the enumerated set, and `reading_matrix.py` lists every case
  that fails each, so the claims in `task.toml` are measured rather than remembered. The two that
  nothing separates - taking every draw, and inverting once per step - read every rule correctly
  and differ only in cost; they are ruled out by the clock and ship as cheats. Two further
  readings were discarded before being built because the published text settles them: that a
  query might report the step just taken, and that a restart might reshuffle.
- Shortcut strategies scored: nop, constant, positional and the replayed example all score 0.
  The shipped tree matched 10 of 190 scripts and its big family alone
  exceeds the clock; a constant micro-batch matched 0; always the first live source matched 1;
  the published example line replayed matched 0; the frozen answers carried reproduced all 31
  enumerated scripts and matched 125 of 190, failing only the generated population.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 60 s
  clock is validated by `tests/seal/model.py` and by two correct variants written apart from the
  reference, `authoring/blend-roll-resume/variants/ok-bisect` and `.../ok-reach`. The whole
  graded set of 394 scripts takes 0.065 s under the reference; both variants reproduce the model
  on all 394. Against that: the step-by-step reading runs at about 812 thousand draws a second
  (20,480,000 draws in 25.2 s measured), and one graded wide script asks for between 600 million
  and 4 thousand million draws; the per-step reading takes 0.561 s for 20,000 steps, which
  extrapolates to 84 s for one three-million-step script. The nop trial is killed by the clock at
  61 s wall. There is no numeric tolerance anywhere: every comparison is exact string equality.
- Undecided decisions from the cold-reader pass: four, each given a sentence; the pass was
  author-run, mechanically, over every graded output. The four decisions that had no
  sentence on the first pass and each got one: that a source starts at epoch 0 with its cursor at
  0; that steps are numbered from 0 across the whole script; that a `wt` rebases whatever weight
  it names, the one already in force included; and that the six files are the only ones taken,
  every other file being a clean copy. The worked example was chosen to settle the layout
  convention and the print format and nothing else - it is the only line of `progs/tiny.txt` on
  which the shipped feed and the reference differ. A fresh-session cold read was not run: this
  session wrote the model, and a self-probe reported as cold by a contaminated author is worse
  than none.

## Verifier contract — FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the six files `/app/mix/deck.py`, `/app/mix/pick.py`,
  `/app/mix/walk.py`, `/app/mix/lay.py`, `/app/mix/keep.py` and `/app/mix/turn.py`. Nothing else
  is read from the agent's container.
- What is checked: the verifier lays those six over its own pristine copy of `/app`, runs every
  graded script through the frozen driver, and compares the printed lines exactly, in order, all
  or nothing. Enumerated scripts are checked against frozen answers in `tests/seal/gt.json`;
  scripts generated inside the verifier from a nonce drawn after the agent's container is gone
  are checked against the sealed model, which must itself still reproduce `gt.json`.
- Graded decisions, ten:
  1. a draw goes to the live source with the smallest counter over weight, the earlier declared
     source taking a tie;
  2. every live source's counter returns to 0 whenever the blend changes, and a draw increments
     only the counter of the source it went to;
  3. a draw takes the sample at the source's cursor in its current epoch's permutation and
     advances the cursor, a cursor reaching the source's size starting the next epoch at 0;
  4. a source with a cap leaves the blend instead of starting the epoch numbered by its cap, at
     the draw that takes its last permitted sample, before any further draw;
  5. `done` is printed at that moment, carrying the source, the step holding that draw, and the
     number of that draw inside the step;
  6. draw `i` of a step goes to rank `(i // micro) % ranks`, slot `i // (micro * ranks)`, place
     `i % micro`, and the draw order does not depend on any of the three;
  7. `stop` puts the step index, the epochs, the cursors and the counters back to the checkpoint;
     the live set and the weights are not restored;
  8. the restored counters stand when the live set and the weights match the ones the checkpoint
     was written under, and are all 0 when they do not;
  9. `feed` reports the step the run is about to take and changes nothing, printing no `done`
     line for a departure inside that step;
  10. a source declared since the checkpoint was written keeps its own epoch and cursor.
- Tolerances: none. Every comparison is exact string equality on the printed lines. The only
  limit is the wall clock on the stage that runs the submitted feed, which is also the task's
  stated execution limit.
- Ground truth, and where it lives: `tests/seal/gt.json`, frozen from `tests/seal/model.py`, both
  under a directory at mode 700 owned by root before any submitted code runs.
- Prong C tactics in the contract: C1 (both sides of the resume fence enumerated), C2 (no query
  exposes a counter or a source choice; nonce scripts generated after the container is gone),
  C3 (the wall clock on the worker at the stated scale), C4 (exact lines, all-or-nothing).
- Route-around guard: only the six files are artifacts. The driver, the op language, the
  permutation, the two state records and the line writer are the verifier's own pristine copy, so
  a submission cannot move the work into a file the verifier does not take, nor change what a
  script means.

## Decisions and their reasons

- The permutation is shipped correct and frozen. The task is the schedule, not the shuffle.
- The first declared source always has an unlimited cap, so the blend is never empty. This
  removes an edge case that would have cost a rule without adding an interaction.
- The seed is declared once per script rather than per run: changing it at a restart would change
  the permutation of an epoch already half consumed, which is a different task.
- `ep` was renamed to `epoch` and `wt` to `weight` in the tree on 2026-09-15, and the sample a
  draw takes is now called `sample`. The terse names were honest but cryptic, and `catcheck`
  measured 3 category hits in the environment against 81 in the prose, which is the mechanical
  shape of the finding that rejected `alias-settle-report`'s ML label. After the rename it is 32.
  The op is still `wt`: the rename went through a token regex that also hit the op-dispatch
  string in the sealed model and the brute-force engine, which broke both until it was caught and
  reverted for that one literal. `gt.json` came out byte-identical across both renames, which is
  the proof they changed nothing.
- The category is ML / Training: the graded work is the correctness of a training run's sample
  feed across checkpoint and restart, which is what "training loops and checkpointing" names, and
  the environment carries the machinery (ranks, micro-batches, accumulation, epochs, weights,
  permutations, checkpoints) rather than only the story.
- `environment/Dockerfile` stays near-identical to the retained bundles at 0.917 similarity. It is
  nine lines of content the rules fix - base image, the two determinism environment variables, a
  workdir and one COPY - so there is nothing left to vary honestly. `tests/Dockerfile`, `test.sh`
  and `reap.py` were rewritten rather than carried over, which took them from 0.99 to 0.73-0.77
  and out of the NEAR band. `simcheck` reports the conceptual verdict that matters: this task
  does not grade what any earlier one grades.
- Two probe cheats were rebuilt on 2026-09-15 because six of them scored 1: they carried the
  reference and an attack, so when the attack failed the run passed on its own merits and proved
  nothing about the isolation. Every probe now carries a fast wrong layout, so a reward of 1
  could only have come from the attack.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | Docker Hub's blob CDN is denied by this session's egress policy (403 on production.cloudfront.docker.com, and the ECR mirror too), so no image could be pulled or built here |
| No answer leaked into agent image | pass | `tools/imagecheck.py` assembles what the image would hold from the Dockerfile and `.dockerignore`, drops the reference in and runs all four shipped scripts: 19 files, workdir `/app`, nothing from `tests/` or `solution/` |
| `harbor run -a oracle` = 1 | pass, host emulation | harbor is not installed here and the images cannot be pulled. `authoring/blend-roll-resume/host_trial.py` runs the shipped `tests/test.sh` verbatim at the real paths, including the privilege drop to uid 1002, the locked root-owned reward channel, the sealed directory at mode 700, the clock and the reaper. Oracle: 33 passed, reward 1 |
| `harbor run -a nop` = 0 | pass, host emulation | reward 0; the shipped feed is killed by the 60 s clock at 61 s wall and leaves no record |
| Cheats all score 0 | pass, host emulation | 36 of 36, and `cheat_report.py` asserts the layer that caught each one rather than only the reward |
| Correct variants score 1 | pass | `ok-bisect` and `ok-reach` reproduce the sealed model on all 394 graded scripts |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | no errors; 14 warnings, of which 12 are the generic unused-public-function notice every retained bundle also raises |
| `difficultycheck.py` | pass | 100/100 on the built tree |
| `readingcheck.py` | pass | every semantic reading separated by the enumerated set |
| `onelinecheck.py` | pass | no graded decision is reproduced by a rule at depth two |
| `forgecheck.py` | pass | the answer-key carrier is present and scores 0 |
| `catcheck.py`, `hintcheck.py`, `structcheck.py`, `solvecheck.py`, `deadfieldcheck.py`, `extraneouscheck.py` | pass | |
| `simcheck.py` | reviewed | `environment/Dockerfile` stays NEAR against three retained bundles; see the decision above |
| `harbor check` rubric | not run | needs an API key, and harbor is not installed here |
| `zipcheck.py` on the built archive | pass | 89 entries, no findings; `scripts/package.py` refused nothing |
| Manual quality review (docs/QUALITY-REVIEW.md) | pass, recorded below | |

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

- Instruction and verifier agree in both directions: `trace.md` walks every test function,
  enumerated case, model rule, artifact and the clock into a sentence and `tracecheck` is clean;
  each of the ten graded decisions has an enumerated case, and `reading_matrix.py` names which
  case fails which wrong reading. The six artifacts are named with absolute paths in
  `instruction.md`, and the tests read nothing else.
- Boundaries settled in the text: draws, steps, samples and the permutation all counted from 0;
  the cursor turns over on reaching `n`; the cap is the epoch not started; a tie falls to the
  earlier declaration; a cap of 0 is no limit; ranks and slots are below their bounds.
- Counts re-derived from the code rather than remembered after every generator change: 394 graded
  scripts, 31 enumerated and 363 generated, three of them at the wide size; `progs/wide.txt` at
  3,100,000 steps and a little over 2.15 thousand million draws with a departure on each side of
  its restart; the worked example line reproduced from the shipped tree.
- Prose: read end to end as prose rather than as a spec. Two runs of same-shaped sentences were
  broken (the cap sentence now leads with its condition, and the output paragraph no longer opens
  three sentences the same way). The remaining density is the cadence of a technical brief and
  matches the retained bundles.
- Verifier rigor: the graded evidence is 394 printed traces produced by running the submitted
  modules, not an exit code or a report the agent writes; `test_outputs.py` opens with the frozen
  contract, listing all ten graded decisions and what is implementation choice; nothing depends on
  wall-clock time except the stated execution limit.
- Environment hygiene: `environment/Dockerfile` copies only `app_src/`; `imagecheck` assembles the
  image contents and finds 19 files and nothing from `tests/` or `solution/`; both Python pins use
  `==`, no apt package is pinned, and `test.sh` touches no network. Every `/app/...` path named in
  the instruction exists in the tree, checked mechanically.
- Solution quality: `solve.sh` copies the six reference modules into place and runs the engine on
  three shipped scripts; it writes no answer and reads nothing the agent could not.
- Anti-cheating: 36 cheats score 0, including the forgery carrying every frozen answer; comparison
  is exact string equality; no repository is cloned.
- Metadata: ML / Training with five tags naming this task's mechanisms; `catcheck` measures 32
  category hits in the environment against 84 in the prose, so the label is carried by the code;
  the difficulty explanation names the concrete step and states the naming register as a design
  choice; ten hours is consistent with the claim.
- Known risk to flag to a reviewer: `environment/Dockerfile` is 0.917 similar to three retained
  bundles because its nine lines are the ones the rules fix. And the two images were never built
  here - see the row above.

## Open questions and next steps

Container evidence is the one gap: every gate below the image boundary has been run, and the two
image builds have not, because this session cannot pull a base image. A session with registry
access should run `python tools/docker_trial.py blend-roll-resume --all` before the bundle is
submitted; nothing in the tree has changed since the host emulation passed, so that is a
confirmation rather than a repair.
