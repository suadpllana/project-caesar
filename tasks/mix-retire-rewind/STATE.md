# Task state

Working memory for `mix-retire-rewind`. Assume the next session starts with no memory of this
one - anything not written here is lost. This file never ships.

## Current stage

`Stage 7 - Pre-flight and packaging`. Every local gate has been run; the container gates cannot
run in this session and are recorded as not run.

## Assistant's assigned role

Training-infrastructure engineer on the data path of a pretraining stack: blended corpora, token
caps, per-source epochs, gradient accumulation across a changing world size, and the
checkpoint seam where a prefetching loader and the trainer disagree about what has been
consumed. Comfortable with exact index arithmetic and with proving that a resumed run sees the
same samples in the same order as the one it replaced.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no repository vendored.
- Task shape chosen: authored-on-top does not apply; the environment is written from scratch.
- Contributor's relationship to it: n/a
- License, and why vendoring it is permitted: n/a
- Pinned commit vendored into environment/app_src/: n/a
- Load-bearing couplings found during research: see "Why it is hard"; they are inside the
  authored tree (`feed/mix.py` decides which source owns a slot, `feed/deck.py` decides what
  that source hands over, `feed/spot.py` and `feed/keep.py` decide what a record says and what
  a load rewinds to, and `feed/shuf.py` is frozen and defines the hand-over order).
- Identifier degradation: the tree is written directly in the legacy register (`feed/`, `mix`,
  `deck`, `draw`, `spot`, `deal`, `keep`, `shuf`, `trail`, `took`, `hold`, `pat`); there is no
  conversion table because there is no upstream.
- Proper-noun sweep: nothing to sweep; no product, project or vendor name occurs in the tree.
- Upstream-diff check: n/a - nothing to diff against.

## Task summary

`/app` is the feeder of a pretraining run: the part that decides which sample of which source
lands in which micro-batch of which rank, and what a run resumed from a checkpoint sees next.
Sources hand their samples over in a per-epoch order; a sample longer than the token cap is
passed over and the same source is asked again; a source with an epoch allowance retires when
that allowance is spent and its entries leave the mix; a checkpoint records both what the
trainer completed and what the feeder produced, and a load has to begin at the first of those
under the geometry that run was using. The shipped feeder walks the stream one slot at a time
and is wrong on nine decisions. The agent repairs six files so that every graded plan prints
exactly the right trace, and gets the whole set through 60 seconds - which nothing that visits
a slot can do, because the wide plans reach 200 million of them.

## Why it is hard

The first plan is the shipped shape with its mistakes taken out: cursors per source, the mix
read off the slot number, and a resume that replays the stream. It is semantically repairable
and it never finishes. The repair that follows - derive the state at a slot instead of walking
to it - is then invalidated by a rule stated one paragraph away: a source retires when its
allowance is spent and its entries leave the pattern, so there is no single pattern to count
against, each retirement slot has to be solved for inside the pattern that was live before it,
and every later one moves because the survivors take the slots the retired source was taking.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the correct plan is a derivation rather than an implementation of the stated rules.
  Every rule is stated and each is individually implementable; what is not stated is that the only structure satisfying all of
  them at the stated scale is a stretch timeline whose breakpoints are solved by inversion, with
  a delivered count turned into an epoch and a cursor by an invariant the agent has to notice (a
  permutation does not change a multiset, so every epoch of a source delivers the same number of
  samples). An agent that commits to the shipped walking shape - which is what the tree, the
  ordering of the brief and every published loader suggest - spends its budget before the first
  wide plan prints a line.
- Tactics making that true (docs/DIFFICULTY.md): A1, B2, C2, C3 and C4, justified below.
  A1 is that the memorised resume continues from the loader cursor and the memorised blend is one fixed index map, both specifically wrong here; B2 (nine graded decisions that change each other's meaning: refill, epoch crossing,
  allowance, pattern rebuild, deal, record position, rollback, chaining, and the record format),
  C2 (the only thing runnable is a feeder wrong on all nine, no expected trace ships, and the
  graded plans come from a seed drawn after the agent container is gone), C3 (a slot-at-a-time
  feeder is right in every rule and needs 373 s for one graded plan against 60 s for the whole
  set), C4 (exact traces over enumerated corners plus eleven generated families, all or nothing).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is to repair the shipped walker in place - the refill, the deal, the retirement test, the
  record position and the rollback - and run the small plans. That plan is correct and
  unfinishable. My second plan is to derive the feeder state at a slot from the period of the
  pattern and the per-epoch delivery count, and I would write it against the opening pattern,
  because retirement is one sentence among nine. That is wrong from the first retirement onward
  and nothing in the tree says so, because the small plans still pass. The third plan, the
  stretch timeline with breakpoints solved in order, is the one that holds, and it replaces the
  counting helper, the state derivation and the rollback rather than patching them.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8, aimed at the hard edge.
- Difficulty record score (tools/difficultycheck.py on authoring/mix-retire-rewind/difficulty.toml,
  before Stage 2): 100/100 on the first attempt, 2026-09-19, band 95-100, no hard stop. There
  was no earlier attempt: the design was measured in `authoring/mix-retire-rewind/proto/` before
  the record was written, and the record states what was measured. Re-run at Stage 7 against the
  built tree: 100/100, no drift reported.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set -
  no contributor anchoring exchange has happened for this task.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-19 100/100, first
  and only record to date; re-measured against the built tree the same day, unchanged.
- Leak audit (docs/DIFFICULTY.md): run as a script rather than as a feeling
  (`authoring/mix-retire-rewind/leakprobe.py`, 180 generated plans). The delivered count taken
  against the pattern as the plan wrote it reproduces the graded counts on 74.4% of probes and
  fails wherever a retirement has happened; the record epoch as delivered over samples is right
  40-44% of the time; the base a load begins at, guessed from the produced step count times any
  plausible width, is right 6.9% of the time; the shipped feeder reproduces a graded trace on
  7.2% of plans. No stage is reproducible by a no-reasoning expression, and under all-or-nothing
  grading none of those fractions is a pass. Separately: the count of samples inside the cap is
  not a field anywhere - only raw token lengths ship; no retirement slot, stretch table or
  delivered count is recorded in the tree; no expected trace ships and the brief quotes one line
  of one small plan, which settles the rank deal and the printed format and nothing else; the
  shipped feeder has no helper that counts a source over a stretch, because it walks; and the
  per-source cursors in a checkpoint record are the feeder state at the feeder position, which is
  the wrong slot to resume from, so reading them off is a losing reading rather than a shortcut.
- Expert path, described step by step: run the shipped feeder on the small plan and compare its
  last line with the one the brief quotes; read the six collected files against the stated rules
  and repair the refill, the epoch crossing, the record position and the deal; time the two wide
  plans and abandon walking; count a source over a stretch from the period of the pattern; turn a
  delivered count into an epoch and a cursor using the per-epoch delivery count; solve each
  retirement slot inside the pattern that was live before it and rebuild the pattern for the next
  stretch; rewind a load to the last step the trainer completed under the geometry that run was
  using, carrying the base through a chained load; re-run the small plans for exact traces and
  both wide plans against the clock.
- Originality check: searched 2026-09-19 for deterministic resumable loaders over blended
  sources, for epoch-capped mixtures with renormalisation, and for the prefetch-ahead checkpoint
  bug. What exists: elastic-determinism notes for streaming dataset libraries (a canonical sample
  order independent of world size), blended-dataset index maps in training frameworks (an index
  map built for the whole run and looked up), published epoch capping of mixtures, and several
  framework issues about a loader checkpointing a cursor that ran ahead of the trainer, fixed by
  clamping to the completed step count. None of them plans this task: the run here is longer than
  any index map that fits the memory cap, the mix changes part way through when a source retires,
  and the derivation that survives both is in no page found. `tools/simcheck.py` reports no
  shipped file near another bundle and no earlier task grading what this one grades.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace: walked from the verifier into `authoring/mix-retire-rewind/trace.md`, and
  `python tools/tracecheck.py mix-retire-rewind` is clean. It covers 4 test functions, 37 enumerated plans, 20 rules
  of the sealed model each with its line range, 6 collected files, the 60 s clock, the memory cap
  and the exactness of the comparison. Every row cites a sentence; two rows were added to the
  instruction because the walk found them missing (a `show` names a step the trainer has already
  taken, and the position in a sample id is counted from zero).
  `python tools/tracecheck.py mix-retire-rewind` is clean.
- Identifiability: 24 readings written down and every one separated by an enumerated plan.
  They live in `authoring/mix-retire-rewind/readings.py`, enumerated from
  the four clusters applied to every rule, from the shipped feeder, and from the two readings
  only a walking feeder can hold. `python tools/readingcheck.py mix-retire-rewind 90` reports all
  24 separated by an enumerated plan and none equivalent. The boundary reading (a sample exactly
  at the cap) and the mix reading (a retirement inside a printed step) were blind on the first
  run; `cap-exactly-at-cap` and `mix-retire-inside-step` were added for them, and the generator
  was shaped to land on the cap boundary and to print every step of a run that retires a source,
  which lifted their coverage from 1 and 2 plans in 90 to 292 and 29 plans in 411.
- Shortcut strategies scored: the nop, a constant, a positional rule and the replayed example, every one of them 0.
  The nop is killed by the clock on the wide plans and differs on every line of
  the small ones; a constant sample everywhere is caught by `cap-all-but-one` and 408 of 411
  generated plans; always the first sample of the owning source is caught by `cap-exactly-at-cap`
  and 403 of 411; the quoted line replayed is caught by `cap-all-but-one` and all 411. The
  forgery carrying every frozen answer passes all 37 enumerated plans and fails all 411 it could
  not have seen.
- Independent implementation behind every tolerance and limit (path, measured headroom): five feeders written apart from the reference, about 300x of headroom.
  The 60-second limit is validated against
  `authoring/mix-retire-rewind/slow/walk`, `slow/stream`, `slow/fold`, `variants/bisect` and
  `variants/backscan`. The reference settles all 448 graded plans in 0.19 s of worker time with a
  19 MB peak resident set, and both variants score 1 through the real verifier; the three slow
  feeders are all correct on 179 plans each and all three are killed by the clock. The walker
  does the first 2000 of 780000 steps of one wide plan in 0.96 s, which is 373 s for that plan
  alone. Headroom for a correct derivation is about 300x, which is what stops the limit from
  grading an implementation choice.
- Undecided decisions: three gaps came out of the cold-reader pass and each is now a sentence.
  The pass was author-run, mechanically, as the four steps of docs/INSTRUCTION-CONTRACT.md:
  every printed token listed, every model branch that touches it listed, the four clusters put to
  each as questions. The three are: whether a sample exactly
  at the cap is delivered ("at most the cap"), the index base of the position in a sample id
  ("counted from zero"), and whether a `show` may name a step the trainer has not reached ("A
  `show` names a step the trainer has already taken"). A fresh session that saw only the brief and
  the tree was not run; the author wrote the model first and cannot un-know it, so the stronger
  form is recorded as not run rather than reported as passed.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-19. Changing any line below changes what "correct" means and needs the
contributor's explicit approval. Nothing below has changed since it was frozen.

- Artifacts the agent produces: exactly six files, `/app/feed/mix.py`, `/app/feed/deck.py`,
  `/app/feed/draw.py`, `/app/feed/spot.py`, `/app/feed/deal.py`, `/app/feed/keep.py`. Nothing
  else is read from the agent container. The verifier lays those six over its own pristine copy
  of the tree, so the driver, the plan reader, the hand-over order and the line format are the
  verifier's, not the agent's.
- What is checked: every graded plan is run through the shipped driver and its printed trace is
  compared line for line, all or nothing. Nine decisions are graded:
  1. a sample whose token length is over the cap is passed over, does not fill the slot, and the
     same source is asked again;
  2. a cursor that runs off the end of an epoch continues at the start of the next one, under
     that epoch's hand-over order, and the samples over the cap that trail an epoch are passed
     over only when the source is next asked;
  3. a source retires the moment it delivers the last sample its allowance covers, and an
     allowance of zero never retires;
  4. a retired source's entries leave the pattern, the survivors keep their order, and the next
     slot begins a new stretch whose offsets are counted from it;
  5. slot offset o of a step goes to rank `o % world`, and each rank's slots fill its
     accumulation micro-batches in order;
  6. a checkpoint record names the base, the steps the trainer completed, the steps the feeder
     produced, and every source's state at the feeder's position;
  7. the state a record names is the one the feeder is in before the slot it names is filled,
     and a retired source prints as `gone`;
  8. a load begins at the slot after the last step the trainer completed, under the geometry
     that run was using, not at the feeder's produced position;
  9. a load carries the base of the run it came from, so a chained load composes.
  Plus the execution limit: the whole graded set has 60 seconds of wall clock on the process
  that runs the submitted files, and 2048 MB.
- Tolerances: none. Exact string equality on every printed line, and an exact set of lines.
- Ground truth, and where it lives: `tests/seal/gt.json` holds frozen traces for the 37
  enumerated plans and `tests/seal/model.py` is an independently written feeder; both sit in a
  root-owned `chmod 700` directory the submitted code cannot read. The 411 nonce plans are
  generated inside the verifier from a seed drawn after the agent container is gone and graded
  against the model, and the grader first asserts the model still reproduces `gt.json` exactly.
- Prong C tactics in the contract: C1 (both sides of every fence are enumerated), C2 (no expected
  output ships; graded plans are generated after the fact), C3 (the 60-second limit, measured
  against five correct implementations), C4 (exact traces over enumerated corners plus eleven
  generated families, all or nothing).
- Route-around guard: `artifacts` names the six files and nothing else, so the driver, the plan
  format, the hand-over order and the printed line format cannot be reshaped; the pristine
  overlay means a change anywhere else in the tree is simply not carried.

## Decisions and their reasons

- The feeder state is defined as a function of the absolute slot index, and every query in the
  plan language asks for a slot. That is what makes the derived implementation possible at all,
  and it is why the walker is exactly right and exactly too slow.
- The hand-over order (`/app/feed/shuf.py`) is frozen and not collected. It defines the shuffle,
  so naming it in the brief is enough; freezing it stops the task from turning into a
  random-number-reproduction exercise.
- Source lengths are written inline in the plan file, so a generated plan is self-contained (the
  verifier writes nonce plans as text and nothing else) and the raw lengths stay the only shipped
  primitive.
- Sources are capped at 400 samples even in the wide plans: the scale that kills a walker is the
  slot count, not the corpus size, and a small corpus keeps the epoch count high, which is what
  the per-epoch invariant is for.
- Category is `Software / Data engineering`, not `ML / Training`, although the setting is a
  pretraining feeder. `tools/catcheck.py` measured zero ML tokens in `environment/` against 91 in
  the prose, which is the exact shape of the 2026-09-04 rejection of `alias-settle-report`: the
  graded work is stream and index arithmetic over a data pipeline, and the category names the
  skill the graded decisions need rather than where the story is set. Software vocabulary is
  present in the tree (10 hits) and the tags name the mechanisms rather than the taxonomy.
- The four harness files that a new bundle tends to inherit byte for byte - both Dockerfiles,
  `tests/test.sh` and `tests/reap.py` - were rewritten rather than copied, after
  `tools/simcheck.py` reported four of them at 0.98 to 1.00 against retained bundles. The
  isolation discipline is unchanged; the files are this task's own. The environment Dockerfile now
  also runs the smallest shipped plan at build time, so a tree that cannot run fails the build
  rather than the trial.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | the Docker daemon runs in this session, but image pulls are denied by the egress policy (403 on CONNECT to the registry blob CDN), so no base image exists to build from. `tools/imagecheck.py` stands in: it assembles what the image would hold (16 files, workdir /app), drops the reference in and runs all four shipped plans - clean |
| No answer leaked into agent image | pass | `tools/extraneouscheck.py` clean; `tools/deadfieldcheck.py` clean; `tools/leakprobe.py` reports no stage reproducible without reasoning; `tests/` and `solution/` are copied nowhere into `environment/` |
| `harbor run -a oracle` = 1 | not run | harbor is not installed and its gates need the same registry. Host emulation (`authoring/mix-retire-rewind/host_trial.py`, which runs `tests/test.sh` verbatim as root with the privilege drop, the locked reward channel, the survivor reap and the artifact-only upload) returns reward 1, 40 tests passed, 0.22 s |
| `harbor run -a nop` = 0 | not run | same; host emulation returns reward 0, the worker killed by the 60 s clock with no record to grade |
| Cheats all score 0 | pass | 40 of 40 through the host emulation, each caught by the layer it was written for (`authoring/mix-retire-rewind/cheat_report.py`): 22 wrong readings by the enumerated plan named for each, 5 correct-and-too-slow feeders by the clock, 3 shortcut strategies and 9 probes by an enumerated plan, and the forgery by the 411 plans it could not have seen |
| Correct variants score 1 | pass | 2 of 2 (`variants/bisect`, `variants/backscan`) through the host emulation |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `readingcheck.py` | pass | 24 readings, all separated by an enumerated plan, none equivalent |
| `onelinecheck.py` | pass | 5 of 7 graded quantities have no exact rule at depth <= 2; the two that do (the rank of an offset and the base a load begins at) are stated conventions and each has cheats |
| `difficultycheck.py` | pass | 100/100 against the built tree, in band, no drift over a third |
| `preflight.py` | pass | clean |
| `catcheck.py` | pass | after the category correction recorded above |
| `hintcheck.py`, `structcheck.py`, `solvecheck.py` | pass | clean |
| `simcheck.py` | pass | no shipped file near another bundle after the harness rewrite; no earlier task grades what this one grades |
| `forgecheck.py` | pass | the forgery carries `gt.json` verbatim, is recognised as an answer-key carrier, and scores 0; the check also re-runs the whole 40-cheat suite, 0 findings |
| `textcheck.py` | read | against `slab-fold-scope` the only finding left is a narrower type-token ratio (0.263 against 0.347), which is a length artifact: the retained briefs of comparable length sit at 0.258 to 0.320, and this one is 1084 words. Every other axis is inside the retained band |
| `zipcheck.py` on the archive | pass | `tasks/mix-retire-rewind.zip`, 91 entries, no STATE.md, no caches, every `.sh` at 755, no CRLF, one top-level directory |
| `harbor check` rubric | not run | no API key in this session |
| easiness probe | not run | external; no probe harness in this session. A self-probe is not reported as passed: the author wrote the sealed model first and cannot un-know it (CLAUDE.md, 2026-09-07). What stands in its place is the reading separation, the leak audit script, the no-oracle property and the cold-reader pass above |

## Packaging

`python scripts/package.py tasks/mix-retire-rewind` refuses on errors and reported none;
`python tools/zipcheck.py mix-retire-rewind` is clean on the built archive. The oracle and the
nop were re-run through the host emulation after the harness files were rewritten: reward 1 with
40 tests passed in 0.23 s, and reward 0 with the worker killed by the clock.

## Open questions and next steps

- The container gates (image build, harbor oracle and nop) and the easiness and quality probes
  are the outstanding evidence. Everything runnable here has been run.
- If the easiness probe solves this task, the trajectory to look for first is a feeder that
  derived the state but counted against the opening pattern and still passed: that would mean the
  retirement families in the generated population are too thin, not that the brief leaked.
  `authoring/mix-retire-rewind/cheat_report.py` prints the per-reading population movement, and
  `draw-ignores-retire` at 29 of 411 is the thinnest.
