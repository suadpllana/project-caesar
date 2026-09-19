# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 2 - Verifier contract` (frozen; environment work started)

## Assistant's assigned role

You are a training-infrastructure engineer on a sparse-layer runtime: the dispatch stage of a
mixture-of-experts layer under expert parallelism, where gate scores decide which expert
buffers a token enters, buffers are sized once per optimizer step and shared across the
microbatches of a gradient accumulation, and a device's buffer budget is smaller than the sum
of the buffers it holds. You have written and debugged token dispatch, capacity sizing and
load-balance accounting, and you know that what the published implementations do on overflow
is not what every runtime does.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree is
  written here, not degraded from a source; identifiers are chosen in the legacy register directly
  (`lay/`, `put`, `back`, `trim`, `tally`, `gsc`, `wl`, `mb`) and no name misdescribes what it holds
- Proper-noun sweep done? No product, project, company or framework name appears anywhere in the
  agent-facing tree; the domain terms that remain (expert, gate score, microbatch, bank) are the
  ordinary vocabulary of the work and carry no provenance
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the dispatch stage of a sparse layer: a step file gives gate scores for the tokens of
each microbatch of an optimizer step, and the runtime decides which expert buffers each token
enters, at which slot, and what is left on the residual path. The shipped service implements the
published behaviour - a token whose expert buffer is full is dropped - and the specification it
has to meet is the runtime's own: the arrival takes the slot of the weakest occupant that has
not yet been displaced this step, the displaced token loses every placement it holds from that
rank on, it comes back in the next microbatch with the expert it was refused struck out of its
ranking, and a device budget smaller than the buffers it holds removes placements once the step
is over. The agent fixes the seven files under `/app/lay/` so every program's trace matches.

## Why it is hard

The first plan is the published one and it is wrong at the first decision point; the rule that
replaces it makes placements revocable, and the rule after that makes want lists grow while
buffers do not.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable answer to a full expert buffer is to drop the token, and every public implementation settles routing into a table before dispatch and then applies a cumulative-sum capacity mask. Here the arrival displaces an occupant, so placements are revocable and buffers
  develop holes that later tokens fill; and a refused token is reconsidered with that expert
  struck out of its ranking, which lengthens its want list, so routing is produced by placement
  rather than consumed by it. A plan that settles routing first has to be taken apart, not
  corrected, and the wrongness shows up only in slot indices and in a balance number.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped service is the model's prior implemented faithfully and it is the wrong answer; A2 the prefix property, the widening effect and the shed cascade are stated as
  what the runtime does and never named, so their consequences must be derived; B2 seven rules
  hold at once and each changes what a correct implementation of the others looks like; C1 both
  sides are graded, so never displacing and displacing without the score test both fail; C3 a
  wide family makes the scanning implementations infeasible while leaving them exactly correct;
  C4 every program matches line for line against a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was
  to compute every token's want list once, count demand per expert, size the buffers, then walk
  the tokens appending into buffers and dropping the overflow, with a per-expert counter and a
  post-pass for the statistic. It is wrong three times over: a full expert does not turn the
  arrival away, so a counter cannot represent a buffer whose occupants leave; placements are a
  prefix of the want list, so a token that loses a rank loses every later rank and frees slots
  scattered across experts that the next arrival fills at the lowest free index; and a refused
  token's want list is recomputed with that expert struck out, which makes it longer, so the
  wanted totals the statistic is defined over grow during the step while the capacity sized from
  the first microbatch does not.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 3 of 8 (range 1-5), revised up from 2 at the Stage 7 cold re-attack because every rule is stated and a meticulous implementer wins
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-19 scored 100/100, in band, no hard stop; nothing
  was changed between attempts because there was only one. The single warning is that the resource
  gate is declared but not yet measured, which Stage 4 settles before any prose depends on it.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-19 record scored 100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": no per-expert load line
  is printed, so loads are recoverable only by summing the per-token lines; no displaced or
  deferred flag is a field on any shipped record; nothing counts demand per expert; the shipped
  buffer is an append counter, so the hole-filling structure has to be built rather than found;
  the sample programs ship without their correct output and the brief quotes one line of one
  program, which is a residual number rather than a decision the task turns on.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped programs and find which module owns the quoted line; derive from the contiguity rule
  that a token's placements are a prefix of its want list, so placement stops at the first expert
  it cannot enter; rebuild the buffer as slots with a free set, because displacement and deferral
  both free slots mid-step; make the want list a per-token value that placement rewrites, holding
  the full ranking once and a struck-out set beside it; settle the deferral queue, which carries
  only a token that lost or never got rank zero, in displacement order, ahead of the next
  microbatch's own tokens; write the shed as a bank-by-bank loop in index order whose removals
  cascade into later banks through the same contiguity rule; compute the statistic from the want
  lists as they finally stand and the placements as the shed left them; then time the wide
  programs and replace the buffer scans with a per-expert order over displaceable occupants and a
  free-slot heap.
- Originality check: searched 2026-09-19 for the mechanism. What the literature carries is
  capacity-factor routing with drop-on-overflow (GShard, Switch Transformer and the dispatch-mask
  implementations that follow them), batch-priority routing which reorders which tokens are
  dropped, expert-choice routing which inverts who selects whom, and dropless routing which
  removes the capacity bound. Request-level deferral at a layer boundary exists in serving work,
  but no public source has a higher-scoring arrival take a full buffer's slot, the displaced token
  return in a later microbatch with that expert struck out, or a device budget remove placements
  after the step. The best retrievable page gives a plan that is wrong at all three points.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/expert-defer-shed/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 44 rows walked - 4 test functions, 7 artifacts, the pristine overlay, the 60 second clock and 31 rules of the sealed model split one per rule with its lines - plus 22 readings and 5 shortcuts; no NOT STATED row survived, and `python tools/tracecheck.py expert-defer-shed` is clean. Two notes remain and are structural: the case table is a dict of tuples and the readings table is built by emit.py, so neither name list can be read by the tool and both are cited by hand.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 22 readings were written as whole engines by `authoring/expert-defer-shed/emit.py` and measured by `python tools/readingcheck.py expert-defer-shed`. All 22 are separated by the enumerated set; one, `defer-any-short`, was BLIND on the first run and `defer-keeps-prefix` was written for it from the shrunk counterexample the tool printed. `cheat_report.py` then asserts that each reading is caught by the case named for it, which holds for all 22, and reports how much of the generated population each moves: 15 per cent at the least (shed-tie-low) and 100 per cent at the most.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 with 29 of 33 graded assertions failing; `cheat-const-nothing` scores 0 and matches no enumerated program and none of 108 sampled generated ones; `cheat-pos-top-only` scores 0, failing 11 enumerated and 106 of 108 generated; `cheat-forge-hand` carries the frozen answers for all 30 enumerated programs over the shipped engine, passes every one of them and fails the generated population. Its first version sat on the reference and moved 0 of 108 programs, which is how the layer report caught that it was not a forgery at all.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/expert-defer-shed/variants/ok-mask` and `.../ok-flat`, both written apart from the reference, settle the six scale programs in 2.9 and 3.0 seconds against the 60 second clock, a factor of twenty. The sealed model, also written apart, agrees with both on 276 programs including the scale families. There is no numeric tolerance: the trace is compared string for string.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. Five gaps were found and closed in the brief: the tie in the ranking, the tie among equal occupants, the two ties in the shed, and that a step does not inherit anything from the one before it. One sentence survives the pass without a reading that contests it - "The arrival takes that exact slot" - because at a full expert the victim's slot is also the lowest free one once it is given back, so no implementation can disagree; it is kept because the slot index is graded and the agent is owed the fact.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-19 and unchanged since. Nine graded decisions, the trace format and the artifact
list are recorded in the section of the same name in the design record
`authoring/expert-defer-shed/difficulty.toml` and restated in `tests/test_outputs.py`, which is
the file a reviewer reads.

- Artifacts the agent produces: `/app/lay/gate.py`, `/app/lay/cap.py`, `/app/lay/buf.py`,
  `/app/lay/back.py`, `/app/lay/put.py`, `/app/lay/trim.py`, `/app/lay/tally.py`. Nothing else is
  collected; the verifier lays those seven over its own pristine copy of the tree.
- What is checked: the stdout trace of every graded step file, line for line, exactly. Thirty
  enumerated programs against `gt.json`, frozen before the grading file was written; 366
  generated programs against the sealed model, which must itself still reproduce `gt.json`.
- Tolerances: none. The only limit is the 60 second wall clock on the stage that runs submitted
  code, validated against two independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory `chmod 700` before the privilege drop.

### The nine graded decisions

1. Ranking by gate score descending, ties to the smaller expert index, and the want list as the
   shortest prefix reaching the threshold - the whole ranking when it falls short.
2. Capacity from the first microbatch's wanted places, the microbatch count and the expert
   count, rounded up; the bank budget from that, the bank width and the share, rounded up.
3. Prefix placement at the lowest free slot, stopping at the first expert it cannot enter.
4. Displacement: the lowest-scoring occupant not already displaced this step, ties to the larger
   slot, and only when the arrival scores strictly higher.
5. Contiguity: a lost rank takes every later rank with it.
6. Deferral: only a rank-zero loss is queued, in the order the losses happened; a loss in the
   last microbatch is held and prints nothing.
7. Striking out: an expert that refused a token leaves its ranking for the rest of the step, and
   the want list is recomputed over what is left.
8. The bank shed after the last microbatch, in bank index order, weakest first, cascading.
9. The residual off the final want list, and the balance number pairing final demand with kept
   places.

## Decisions and their reasons

- **ML / Training, not ML / Inference.** The graded work is the dispatch stage of a training
  step: buffers sized per optimizer step, microbatches of a gradient accumulation, a
  load-balance statistic. `token-seam-emit` already occupies ML / Inference.
- **Displacement rather than dropping.** This is the whole A1 tactic: the shipped service drops,
  which is what every public implementation does and what a model writes from memory.
- **The queue carries only rank-zero losses.** A token that keeps a prefix is not queued. This is
  what makes the prefix property load-bearing rather than decorative.
- **Capacity from the first microbatch.** Buffers are allocated before a step runs and sized from
  a probe, which is realistic and puts the sizing clock and the pressure clock out of step.
- **The shed runs after the step, not as a guard during it.** A guard would make the bank budget a
  local test; running it afterwards means the final state is not the streaming state and the
  cascade can cross banks.
- **The domain's own words are kept in the code.** `tools/catcheck.py` measured zero
  machine-learning vocabulary in `environment/` against 71 assertions of it in the prose, which is
  the mechanical form of the finding that rejected `alias-settle-report`. Routing weights are
  called weights and tokens are called tokens; the degradation rule is about proper nouns and
  names that announce a trap, not about the vocabulary of the work. It reads 45 now.
- **Two shared kit files were rewritten rather than reused.** `tests/reap.py` and `tests/test.sh`
  measured 0.995 and 0.999 against `slab-fold-scope` on `tools/simcheck.py`. Both are mine now and
  neither appears in the report. The two Dockerfiles remain near-identical to every retained
  bundle because their content is prescribed by the kit - the canonical pytest pins, the artifact
  parents each on their own RUN line, `COPY . /tests/` - and there is nothing in them to author.

## Stage 7 re-attack, run cold on the finished bundle

Read the final brief with the built tree in front of me and tried to one-shot the plan.

- **Is the first plan still wrong?** The plan from the prior is: rank, take the top experts to the
  threshold, size a buffer per expert, walk the tokens appending, drop the overflow. That is the
  shipped service, and it is wrong at the first decision point. The plan *after* reading the brief
  is right in outline, because every rule is stated; it is wrong in structure. A counter-based
  buffer cannot hold a buffer whose occupants leave, a routing table settled before dispatch
  cannot hold want lists that placement rewrites, and an append-only allocator cannot fill the
  holes contiguity leaves. `tools/onelinecheck.py` measures the same thing from the other side:
  three of the four graded quantities have no exact rule at depth two over anything the tree
  exposes, and the one that does is the queue rule, which is stated plainly and covered by a cheat.
- **Are the load-bearing facts still distributed?** They are stated rather than hidden, which is
  the doctrine: nothing is withheld. What is not stated is which structures survive all of them at
  once, and that is unchanged since Stage 1.
- **Did the instruction come to telegraph the method?** No. It states the outcome of each rule and
  never a data structure; `tools/hintcheck.py` is clean and the prose names no technique.
- **Updated estimate of solves out of 8: 3** (range 1 to 5), up from 2 at Stage 1. The honest
  reason for the move is that every rule is in the brief and a meticulous implementer who holds
  all nine at once wins; what remains against them is that there is no feedback on any of the
  nine except one quoted line, the grading is all or nothing over 396 programs, and the natural
  scanning implementation is 40 to 240 times over the clock.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py --build`; harbor is not installed here |
| No answer leaked into agent image | pass | `tools/imagecheck.py`: 15 files, no `tests/` or `solution/` content; `extraneouscheck` and `deadfieldcheck` clean |
| `harbor run -a oracle` = 1 | pass | `docker_trial.py expert-defer-shed oracle`: reward 1, 33 tests in 5.1 s |
| `harbor run -a nop` = 0 | pass | `docker_trial.py expert-defer-shed nop`: reward 0, 29 of 33 failing |
| Cheats all score 0 | pass | `docker_trial.py --all`, 37 cheats; one earlier FAIL (`probe-late-reward`) was the probe sitting on the reference and is fixed |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | 0 errors; the remaining warnings are the package-call false positive every retained bundle trips and the `printf` reward write |
| `harbor check` rubric | not run | no API key in this session; the manual quality review in docs/QUALITY-REVIEW.md was walked instead |

## Open questions and next steps

The easiness probe has not been run: this session has no probe harness, and a self-probe by the
author who wrote the model would measure memory rather than difficulty. The reading separations,
the layer report, the answer-shape measurement and the cold re-attack stand in its place, and the
estimate above is what they support.

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree both ways.** Every graded assertion has its row in
`authoring/expert-defer-shed/trace.md` and `tracecheck` is clean. The converse was walked by
hand: every sentence of the brief is graded by the trace comparison, except two that describe
the environment rather than a behaviour - that `/app/plans` holds four step files, and the two
sizes of the scale programs. Both were re-derived from the tree: 28000 tokens over four
microbatches and 21600 over nine, buffers 4440 and 6219 slots deep.

**Counts.** Re-derived from the code rather than from memory after the last generator change:
30 enumerated programs, 366 generated (nine small families at 40 plus three of each scale
family), eleven families, 60 seconds. Every enumerated case name that `task.toml` mentions
exists in `cases.ORDER`, and every `/app` path the brief names exists in the shipped tree.

**Boundaries.** Three ties (the ranking, the displacement candidate, the shed), one strict
inequality, two roundings, one index base, the empty want list and the last microbatch are all
settled in the text, and each has an enumerated case named for it.

**Verifier rigor.** The tests run the submitted modules over a pristine copy and compare the
whole trace; nothing is taken on the submission's word. `tests/test_outputs.py` opens with the
frozen contract and is sectioned by what each block checks. The only wall-clock dependence is
the stated 60 second limit, measured at twenty times the headroom on two independent
implementations.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; pytest is
pinned at 9.1.1 with ctrf 0.5.2 in `tests/Dockerfile` only; no apt package is pinned;
`tools/imagecheck.py` assembles what the image would hold (15 files) and runs the four shipped
programs in it.

**Solution quality.** `solution/solve.sh` copies seven source files into place and runs two
programs; it computes nothing by hand and writes no answer.

**Anti-cheating.** `tools/forgecheck.py` finds one forgery probe and no ground truth in the
agent tree; `deadfieldcheck` and `extraneouscheck` are clean; the sealed directory is 0700
before the privilege drop and `cheat-probe-answer-key` reports the exception rather than the
file.

**Metadata.** ML / Training is a row of the guideline table; `tools/catcheck.py` measures 45
machine-learning terms in `environment/` against 71 in the prose; the six tags name techniques
rather than the taxonomy; `difficulty_explanation` names the concrete step and states the
legacy-register naming as a design choice; `expert_time_estimate_hours` is 9, consistent with
the claim.

**Known risks a reviewer should see.** `tools/textcheck.py` still reports the brief's burstiness
at 0.761 against 1.009 for `slab-fold-scope`, which is one reference whose figure is carried by
a single 109-word sentence; the cadence was reworked once and further chasing that number would
cost clarity. The two Dockerfiles remain near-identical to every retained bundle because their
content is prescribed by the kit. `harbor check` was not run: no API key is available in this
session.

## Two properties of the scale families a later session should know

`wide` prints no queue line at all. That is not a gap in the generator: the weakest occupant of
a full expert is almost always a token for which that expert is a later rank, because a token
whose first expert it is scores high there, so the losses fall at later ranks and nothing is
queued. `wide` saturates the buffers hard - 15177 of its 28000 tokens end with an unmet want -
so displacement and the contiguity cascade run hot in it, and `deep` carries deferral instead,
with 15092 queue lines over 21600 tokens. Between them both halves of the mechanism are under
the clock; neither family alone would be.

The shipped `wide.txt` and `deep.txt` are different instances from the graded ones, drawn from
the same family builders at a fixed authoring seed, so timing them locally measures the real
shapes without handing over a program the run will be graded on.

## What the isolation probes actually report, not just that they score 0

Run in the verifier image, reading the worker's own record rather than the reward:

- `cheat-probe-answer-key` first two trace lines: `gt PermissionError`, `model
  ModuleNotFoundError`. The frozen answers cannot be read and the sealed model cannot be
  imported by code running inside the verifier.
- `cheat-probe-privilege` first two trace lines: `uid 1002`, `reward PermissionError`. Submitted
  code is unprivileged and the reward is not writable by it.
- `/logs/verifier` is `drwx------ root root` at the moment the submission runs, and
  `reward.txt` inside it is root-owned.

A zero alone would not have distinguished any of these from a probe whose patch never fired.
