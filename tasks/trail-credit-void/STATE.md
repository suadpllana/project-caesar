# Task state

Working memory for this task. Assume the next session starts with no memory of this one -
anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

An evaluation-infrastructure engineer for agentic benchmarks: the person who owns the grading
half of a long-horizon benchmark - replaying a recorded run against a model of the workspace,
deciding when the run may be looked at, and turning a rubric of milestones into a number. The
role was selected by the assistant from the seed, not supplied by the contributor.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task.

## Task summary

`/app` is an offline grader for recorded agent runs. A trail file is one session: the records
every episode shares, then the episodes, each with its own milestone rubric, its violations and
the steps its run was cut into. The grader replays the steps, decides at which points the run may
be observed, credits milestones, takes credit back when a violation fires, charges a per-episode
action budget, and prints an event trace plus a per-episode and per-run report. The shipped grader
is the published, wrong one. The agent rewrites seven files under `/app/crd/` so every graded
trail prints exactly what the sealed model says, inside a 60 second limit for the whole graded
set.

## Why it is hard

The first plan is the one every checkpoint-scored benchmark publishes and the one the shipped tree
already implements: replay, copy the records per step so a failure can be put back, and at each
step evaluate the rubric against the records, crediting what holds whose prerequisites are in the
credited set, then test the violations and drop what a firing names. It is coherent, it is what
retrieval returns, and it is specifically wrong in two ways that ordinary running does not show.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the rules are all stated,
  but they invalidate each other's structures. Credit settles, so it is accumulated state and not
  a function of the records; a prerequisite counts only when it was credited at a *strictly
  earlier* observation, so a chain satisfied in one step is credited one link per observation and
  a failed step - having no observation - costs a layer; and a firing shuts the goal it names
  until that goal is observed unsatisfied while merely opening its dependants, so the credit book
  is three-valued and non-monotone. A plan that settles any one of those first has to be given up
  when the next arrives. On top of that, two measured scale families make the two obvious correct
  structures - a copy of the records per step and per observation, and a sweep of the rubric per
  observation - too slow while leaving them exactly correct.
- Tactics making that true: A1, A2, B2, C1, C3, C4. A1 (the published checkpoint-grader shape is coherent and specifically
  wrong - monotone credit derived from visible state), A2 (re-arming, transitive revocation, undo
  logging and write-set driven evaluation are described operationally and never named), B2 (ten
  graded decisions that change each other's meaning rather than sitting beside each other), C1
  (both sides fenced: `plain-all`, `step-ok-keeps`, `carry-normal`, `bud-exact-end` fail an engine
  that overshoots into caution), C3 (two measured scale families, 32.4 s and 22.1 s against 0.19 s
  and 0.69 s, limit 60 s for the whole set), C4 (exact line-for-line comparison over 37 enumerated
  and 366 nonce trails, all-or-nothing). Guard: seven collected files, everything else replaced by
  the verifier's pristine copy, a new file beside the seven never collected.
- Assistant's attack on the plan: my own first reference carried the `rearm-on-touch` bug - I
  drove the goals looked at during an observation off the records the step wrote, which is
  complete for every rule except one: a goal shut while its predicate *already* fails re-arms at
  the next observation without any record it reads changing. The naive full-rubric sweep found it
  on the wide trail, 347 lines against 333, and the shrunk case is now `void-rearm-false`. That is
  direct evidence that the first plan here is wrong somewhere that matters, written by the author
  who knew every rule.
- Estimated solves out of 8: 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py): 100/100 on the first attempt, in the 95-100
  band, one warning (the gate was unmeasured at that point). The gate was then measured and the
  record updated with the real numbers; the score stayed 100. No redesign was needed.
- Difficulty score anchor: not set - first submission of this task.
- Score history: 2026-09-22 design record 100/100 (before any code); gate measured the same day
  and the record's `naive_family`, `input_scale` and `measured` fields rewritten from the
  measurement rather than from the estimate.
- Leak audit: no artifact that is a function of the correct trajectory ships. Trail files carry
  only primitives - seeded record values, the rubric with weights and prerequisite ids, the
  violation predicates, the recorded actions - and never a credited set, an observation count, a
  cone, a write set or an episode score. The shipped grader keeps a plain credited set and
  recomputes from the records, so nothing in the tree names shutting, re-arming or the dependant
  cone. No helper returns the transitive dependants of a goal or the records a predicate reads;
  the prerequisite lists are parsed into plain fields and every consumer of them is a file the
  agent rewrites. `tiny.txt` was searched for rather than chosen (see below). The only functions
  in the tree are the ones the driver reaches; `preflight` reports 21 "defined but nothing calls
  it" warnings, which is the same false positive it reports 16 times on the retained
  `expert-defer-shed` - its heuristic does not resolve `module.func()` calls, and every function
  was confirmed reachable by hand.
- Expert path, step by step:
  1. Read `run_crd.py` and `crd/spec.py` for the grammar, what is replaced, and what the shipped
     engine does; run `trails/tiny.txt` and line it up against the five lines in the brief.
  2. Rebuild `store.py` so a step is undone from a log of what it wrote rather than from a copy,
     and so the records written since the last observation are available without a diff.
  3. Move observation into `ep.py`: the end of ok steps only, plus an opening observation that
     records values and does nothing else.
  4. Rewrite `book.py` as three states per goal with prerequisites read from a count settled at
     the end of the previous observation.
  5. Write `void.py`: shut the named goal, open its transitive dependants, emit ascending.
  6. Re-arm: a shut goal is a candidate at the next observation whatever that observation touched.
  7. Budget per action including failed steps; cut the crossing step, roll it back, close, and
     undo the episode while the credit stands.
  8. Drive goals and violations off the records written and the prerequisites credited at the
     previous observation; time `wide.txt` and `deep.txt` against the 60 second limit.
- Originality check: searched 2026-09-22 for checkpoint-rubric graders with revocation, milestone
  credit that is taken back, and ordered-milestone agentic benchmark grading. What exists is the
  general shape - OSWorld-style partial progress, long-horizon terminal benchmarks with dense
  milestone grading, CTF partial-credit checkpoints, Snorkel's milestone evaluation write-up.
  Every one of them credits a milestone when its condition is seen and never takes credit back.
  No public material describes this policy conjunction, and a retrieved page makes the first plan
  more confident rather than more correct.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md)

- Instruction trace: `authoring/trail-credit-void/trace.md`, walked from
  `tools/tracecheck.py --skeleton`: every test function, every one of the 36 enumerated cases,
  every collected artifact, the wall clock, and every top-level function of the sealed model, each
  with the sentence of `instruction.md` that tells the agent about it. No `NOT STATED` rows
  remain. `python tools/tracecheck.py trail-credit-void` is clean.
- Identifiability: 22 readings enumerated from the four clusters, from the model's prior (the
  published checkpoint-grader shape), from the shipped broken engine, and from the author's own
  first reference. `tools/readingcheck.py` reports all 22 separated by a named enumerated case,
  with no BLIND and no equivalent rows. Three rounds were needed: `off-zero` and `up-strict` were
  BLIND until `pred-off-zero` and `pred-up-equal` were added, and `void-walk-order` came back
  equivalent because `list(set_of_small_ints)` already iterates in ascending order - the reading
  was rewritten to emit true discovery order and `void-ascending` was re-shaped so a stack walk
  reaches 0, 1, 3, 2.
- Shortcut strategies scored: the shipped tree unchanged (nop) scores 0; nothing-credited and
  everything-credited each score 0 and match 0 of the 403 graded trails; the worked example
  replayed scores 0 and matches exactly 1 of 403, which is `worked-tiny`, the trail whose answer
  the brief prints. All three are `cheat/` scripts and all three were run in the container.
- Independent implementation behind every tolerance and limit: the only limit is the 60 second
  wall clock on the graded set. It is validated against the sealed model (written apart from the
  reference) and against two correct variants under `authoring/trail-credit-void/`: `slow-snap`
  and `slow-sweep` are exactly correct and are the two naive families the limit kills. Measured
  headroom: reference 0.19 s on `wide` and 0.69 s on `deep`, so 3 of each plus 396 small trails
  come to about 3 s against 60.
- Undecided decisions from the cold-reader pass (author-run, the mechanical form): every printed token was listed, then every
  model branch that touches it, then the four clusters put to each as questions. Four gaps were
  found and closed in the text: that a record standing at zero has a value (so `off` does not
  hold), that `up` is "at least", that `back` needs the value to be strictly smaller, and that the
  opening observation neither credits nor fires. A fresh-session cold read was not run; this is
  the author-run form and is recorded as such.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/crd/store.py`, `pred.py`, `obs.py`, `book.py`, `void.py`,
  `ep.py`, `tally.py`. Nothing else is read.
- What is checked: the exact list of lines `run_crd.run(text)` returns for each graded trail,
  compared line for line. 37 enumerated trails against `tests/seal/gt.json`; 366 nonce trails
  against `tests/seal/model.py`; the model is first asserted to reproduce `gt.json`.
- Tolerances: none. Exact comparison. The one limit is the 60 second wall clock on the worker.
- Ground truth: `tests/seal/gt.json` (frozen) and `tests/seal/model.py` (independent), both in a
  root-owned `chmod 700` directory the sandbox uid cannot read.

## Decisions and their reasons

- Category `Software` / `Algorithms`, after first filing it as `ML` / `Evaluation` and then
  measuring the claim. The story is an agentic-benchmark grader, and ML / Evaluation was the empty
  cell, which is exactly the attraction that got `alias-settle-report` rejected on 2026-09-04:
  "nothing about the work requires ML knowledge, and the evaluation harness framing is narrative".
  The measurement settles it. Grepping the agent-facing tree for the ML vocabulary
  (`model|train|infer|tensor|gradient|logit|token|epoch|neural|embed|vocab|bpe`) returns **zero**
  hits here, against 5 for the retained `token-seam-emit`; an agent solving this needs no ML
  knowledge at all. `catcheck` now measures software vocabulary at 83 in the environment and 86 in
  the prose, in the band of the retained Software tasks (46/217 and 103/125). The graded work is a
  deterministic engine: an undo-logged store, a three-state credit book under ordering
  constraints, a transitive dependant cone and a budgeted driver. That is Algorithms. It is the
  third task in that cell, and it shares no mechanism with the other two (record linkage under
  disequality, diff alignment across revisions). `Software / Systems` is retired and was never a
  candidate.
- The worked example is graded. The brief prints the five correct lines of `trails/tiny.txt`, so
  those lines are a promise; `worked-tiny` is that trail byte for byte, added as the thirty-seventh
  hand case. `build_gt.py` reported 1 new and 0 moved, which is the proof that adding it redefined
  nothing.
- Seven editable files rather than fewer: each carries graded work, and the retained passing band
  is 1-7.
- The opening observation credits nothing. The alternative - crediting at the baseline - was
  rejected because it makes a seeded rubric score without the run doing anything, which is not
  what a benchmark means by a milestone.
- `tiny.txt` was searched for, not chosen: 700 candidate trails were run under the reference and
  under all 22 wrong readings, and the one that ships decides **zero** of them while still showing
  a mark, a fire, a void, an episode line and a run line. The brief can therefore print its five
  correct lines without handing over a load-bearing rule.
- The deep family was resized twice. At 2600 goals over 11000 steps the rubric sweep ran in 2.7 s
  and the gate did not bite; at 3200 goals with a single-parent chain it ran in 16.7 s, still not
  decisive against 60 s for three of them. It ships at 4600 goals with up to three parents each,
  where the sweep takes 22.9 s and three of them alone exceed the limit.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `docker build` on `environment/`, and `tools/imagecheck.py` |
| No answer leaked into agent image | pass | no `gt.json`, no model, no reference in the image |
| oracle = 1 | pass | `tools/docker_trial.py trail-credit-void oracle` |
| nop = 0 | pass | `tools/docker_trial.py trail-credit-void nop` |
| Cheats all score 0 | pass | 37 of 37 |
| Correct variants score 1 | pass | 2 of 2 |
| `readingcheck.py` | pass | 22 readings, all separated by a named case, no BLIND or equivalent |
| `tracecheck.py` | pass | clean |
| `preflight.py` | pass | no errors |
| `harbor check` rubric | not run | `harbor` is not installed in this environment and no API key is present |
| `onelinecheck.py` | pass | no graded decision has an exact rule at depth <= 2 |
| `forgecheck.py` | pass | `cheat-forge-hand` carries `gt.json` itself and scores 0 |
| `difficultycheck.py` at Stage 7 | pass | 100/100 on the measured tree, 393 env lines, 7 editable, 263 reference, no drift |
| `textcheck.py` against a passed brief | pass | at least as irregular as the reference on every axis |
| `simcheck.py` | reviewed | `tests/test_outputs.py` 0.638 and the Dockerfiles 0.88-1.00 against retained tasks; the retained `expert-defer-shed` scores 0.60-0.69 and 0.88-1.00 against its own neighbours, so this is the shared harness shape, not copied prose. Conceptual similarity: none |

## Stage 7 re-attack, against the finished task

Read cold, the brief states every rule, and that is the honest risk: a meticulous agent that
implements each sentence as written gets most of them right. What it does not get from the brief
is which structures survive all of them together, and two things stay invisible while it tests
locally.

The first is the re-arm completeness hole. The performance requirement pushes every serious
implementation towards driving an observation off the records the step wrote, and that design
silently loses any goal shut while its predicate already fails - the author's own first reference
had exactly this, found only by diffing against a full-rubric sweep on the wide trail. Nothing in
the tree tells a solver their goal stopped coming back. The second is the layering rule: crediting
a chain to a fixed point instead of one link per observation agrees with the correct reading on
every trail where a step satisfies one goal at a time, which is most trails a solver writes by
hand.

Neither is a case that ordinary testing constructs, and there is no oracle: the engine prints what
it decided, never what was expected. Against that, the brief is complete and the expert path is
eight concrete steps, so this is not heading for zero.

Estimate after the re-attack: unchanged at 2 of 8, range 1 to 4. The instruction did not come to
telegraph the method - it states rules and never a structure - and the load-bearing facts stayed
distributed, because the seven files each consume the one before them. `difficultycheck` re-run on
the built tree scores 100 with no drift reported.

## Open questions and next steps

- `harbor` is unavailable here; `tools/docker_trial.py` reproduces the two-image trial with
  docker directly, including the privilege drop and the locked reward channel.
- The easiness probe has not been run - it is a platform gate. The design was aimed at the hard
  edge and the author's own first reference was wrong on a rule the probe will meet.
