# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

Build-tooling engineer on an incremental rebuild service: the part that decides whether a step
has to run again, what a run is allowed to remember about the last one, and what a recorded
dependency is worth once the workspace has moved on. Comfortable with content digests, with
schedulers that discover dependencies while they run rather than before, and with the
difference between a rebuild that is correct and one that finishes.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? The tree is authored, not vendored. Names are short and in a
  legacy register (`keep`, `mark`, `hold`, `wake`, `rec`, `seen`) but never misleading; no
  conversion table is needed because no upstream names exist.
- Proper-noun sweep done? No proper noun appears anywhere in the agent-facing tree; the tree is
  original and carries no provenance.
- Upstream-diff check: there is no upstream to diff against.

## Task summary

The agent lands in a small incremental rebuild service. A program file describes a workspace of
files, a set of steps whose scripts read files, look for files, pull other steps and emit a
value, and a sequence of rounds that edit the workspace and request steps. The service prints a
trace: which steps ran, and how each request ended. The shipped service implements the ordinary
plan - a map of paths to digests per step, a visited set per round, rebuild anything whose
inputs moved - and that plan is wrong in eight of the eleven places the brief settles, plus a
store bug and a digest recomputed at every comparison.
The agent rewrites the five files under `/app/eng` that carry the engine.

## Why it is hard

The rules are all stated. What is not stated, and what the work actually is, is which structures
survive all of them together. A record cannot be a map from path to digest, because a look and a
read on the same path are different observations and a pull sits between them in an order that
decides which steps run. A verdict cannot be a boolean for the round, because it is only worth
anything at the write count it was taken at, and the same structure decides whether a second
request rebuilds, reports `stuck`, or quietly hands back a stale value. The diamond programs
make the memo compulsory, so the solver reaches for it as a performance fix and then owns a
correctness decision it did not know it was making.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): its first plan
  is the declared-graph rebuild every build system in its training data implements, and here
  nothing is declared, checking a dependency is the thing that runs steps, and a step that has
  already run this round and then goes stale is an error rather than a second run. The plan has
  to be formed from the interaction of those rules, and the rule that breaks it a second time -
  a verdict is a fact about a write count, not about a round - only shows up once the first
  implementation exists and the diamond programs force a memo into it.
- Tactics making that true: A1, A2, B2, C1, C3, C4. A1 the make and bazel prior of a declared
  graph is specifically wrong here. A2 the suspending scheduler, early cutoff, negative caching
  and absence tracking are all described as behaviour and none of them is named. B2 eleven
  graded decisions that change each other's meaning. C1 both sides of every rule are graded and
  `stuck` is fenced against an ordinary rebuild. C3 diamond programs make a check that forgets
  its verdict exponential while leaving its trace identical. C4 exact all-or-nothing traces over
  hand programs plus programs generated inside the verifier after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was a recursive `up(step)` that checks a per-step map of read paths to digests plus the set of
  steps it pulled, rebuilds on any mismatch, and memoises with a visited set for the round. It is
  wrong three times over: the map loses the order that decides which steps a check runs, the
  visited set cannot tell a step that was checked from one that ran and so never reports `stuck`,
  and treating a pull as invalid whenever the pulled step rebuilt removes cutoff. I only saw the
  second of those after writing the first version and asking what the memo was actually claiming.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8
  (design band 1 to 3, aimed at the hard edge)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): 100/100 on the first record, in band, no hard stop (2026-09-22).
  The record was written after the resource gate was measured, not before.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet
  submitted; no anchor exists.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 first record
  100/100.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the sample programs
  ship without expected output and none of them separates a wrong reading; the shipped engine is
  one coherent wrong reading rather than a partly correct one, so agreeing with it proves
  nothing; no file lists which of the five collected files are defective; the trace prints round
  numbers, run lines and one outcome per request and never a record, a verdict or a write count;
  every graded quantity is derived while a program runs and is stored nowhere.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run
  the shipped service on the sample programs and read the frozen driver for the trace vocabulary;
  work out that a record has to be an ordered list of four observation kinds; rewrite the check
  as an ordered walk that stops at the first failure and sends a pull observation back into the
  scheduler; split per-step state into record, value or reason, the write count of the last sound
  verdict, and whether the step ran this round; derive that a verdict holds while the write count
  is unchanged and memoise on it; make an output write advance the count only when the bytes
  change; keep the partial record of a failed run so the absence it died on is what revives it;
  fence `stuck` against an ordinary rebuild on hand programs.
- Originality check: searched for public write-ups of this combination on 2026-09-22. The nearest
  public material is the Build Systems a la Carte paper and the Shake manual, which describe
  suspending schedulers, early cutoff and existence tracking. Neither makes checking effectful,
  neither keeps a failed run's partial record, neither allows reading a produced file without
  depending on its producer, and neither turns a step that goes stale after it has already run
  into an error. No retained task in this repository works on rebuild scheduling: the nearest are
  `publish-settle-order` (activation order of extension units) and `slab-fold-scope` (commit
  validation over compaction rewrites), and neither shares a mechanism with this one.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 63 rows walked, no NOT STATED row left, tracecheck clean.
  63 rows under Graded assertions - 4 test functions, 31 enumerated cases, 5 collected artifacts,
  the 60 s clock, the overlay, and one row per rule the sealed model applies with its line range -
  plus 21 reading rows, 6 shortcut rows and 2 tolerance rows. No NOT STATED row was left: the two
  the walk found were written into the instruction instead (which step `stuck` names, and that the
  frozen driver reaches the five files through the names they already carry).
  `python tools/tracecheck.py pull-check-stale` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 21 readings enumerated, none survives, each separated by its enumerated case.
  21 readings written as whole engines in `authoring/pull-check-stale/readings.py` and run over the
  generated population. Every one is ruled out by a sentence and separated by the enumerated case
  named for it (`tools/readingcheck.py`, clean); each moves between 1 and 77 of 112 generated
  programs, so none survives on the graded set. Three candidate readings turned out not to be
  readings at all because nothing separates them - advancing the change count on a write that moves
  no bytes, recomputing a digest at every comparison, and checking the live chain after the verdict
  rather than before - so they were promoted to correct variants instead, and
  `authoring/pull-check-stale/variants/ok-loose` carries the first two and scores 1.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all six score 0, with the cases each matched below.
  all 0. The nop misses 15 of 33 hand programs and 192 of 308 generated; one fixed outcome, the first
  seeded word, every step run on every request, and the worked example replayed each miss all 33
  hand programs and all 308 generated ones; the answer-key forgery reproduces 25 of the 33 hand
  programs and misses all 308 it could not have seen.
- Independent implementation behind every tolerance and limit (path, measured headroom): two independent engines under authoring/pull-check-stale/variants, 0.1 s against the 60 s clock.
  the only limit is the 60 s wall clock on the whole graded set.
  `authoring/pull-check-stale/variants/ok-flat` (an explicit-stack scheduler written apart from the
  reference) and `authoring/pull-check-stale/variants/ok-loose` (no digest cache at all) both get
  through all 341 programs in 0.1 s. The naive family the clock exists to stop,
  `authoring/pull-check-stale/variants/slow-nomemo`, produces identical traces and takes 217 s and
  88 s on the two deep programs alone. There is no numeric tolerance anywhere: traces are compared
  as strings, line for line.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run; two found and both written into the instruction.
  author-run, mechanically, over every printed token. Two decisions the text did not settle, both
  now written: `stuck <name>` did not say which step it names, which matters because
  `stuck-inside-run` requests `outer` and prints `stuck a`; and nothing said the frozen driver
  reaches the five files by the names they already carry, which is a required-exports condition the
  verifier enforces. Everything else answered from a quoted sentence: round numbering from one, the
  run line printed as a run begins, the value of `emit *`, both failure reasons, the loop chain's
  ends, what counts as having run, and that nothing else is printed. A fresh-session reader was not
  available, so the stronger form of this pass did not run.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval. Frozen 2026-09-22.

- Artifacts the agent produces: the five engine files it may change, read back at their original
  paths - `/app/eng/keep.py`, `/app/eng/mark.py`, `/app/eng/hold.py`, `/app/eng/step.py`,
  `/app/eng/wake.py`. Nothing else is collected; a sixth file placed beside them is never read.
- What is checked: the verifier overlays those five files on its own pristine copy of the tree
  and, for every graded program, compares the trace the service prints - line for line, exact
  string match - against the sealed model. Every program must match; one line anywhere scores 0.
  The graded set is the enumerated programs in `tests/cases.py`, whose answers are frozen in
  `tests/seal/gt.json`, plus programs generated inside the verifier from a seed drawn after the
  agent's container is gone. The whole graded run is bounded by one wall clock, stated in the
  brief, which is the resource gate.
- Tolerances: none. Exact line-for-line comparison of the printed trace, all or nothing.
- Ground truth, and where it lives: `tests/seal/model.py`, written independently of
  `solution/`, with the enumerated answers frozen in `tests/seal/gt.json`. `tests/seal/` is
  root-owned and `chmod 700` before the privilege drop, so code running inside the verifier
  cannot read the model or the answers. The grader asserts the model still reproduces `gt.json`
  before it grades anything.

### The eleven graded decisions, and the sentence each is owed

1. A record is the ordered list of the observations a run made, of four kinds.
2. Checking takes the observations in order and stops at the first that fails; a pull
   observation is checked by bringing the named step up to date, so checking runs steps.
3. A verdict is worth something only at the write count it was taken at.
4. A step runs at most once per round; one that has already run and is found stale ends the
   request with `stuck`.
5. A write advances the count only when the bytes change, which is what makes cutoff work.
6. A look records whether the path was there, not what was in it.
7. A read of an absent path ends the run with `missing`, and the absence is the last entry of
   the record that is kept.
8. A step that died stays dead until an entry of its partial record fails; a pull of a dead
   step ends the puller with `via`, and the dead observation holds whatever the reason.
9. A read of a path some step emits is bytes, not a dependency, and never brings that step up
   to date.
10. A successful run records the bytes it wrote to its output path.
11. A cycle is the live pull stack, not the recorded pull graph.

## Decisions and their reasons

- The parser, the digest, the trace writer and the driver are frozen and overlaid from the
  verifier's pristine copy. They are not collected, so the program grammar and the output format
  cannot be redefined and an engine hidden in a sixth file is never read. This is the
  route-around guard.
- `emit *` takes its value from the frozen digest module rather than from anything the agent
  writes, so no submission can fail for hashing differently. Only the decision of which values
  reach it is graded.
- The store is a plain dict of path to text inside the process; there is no real filesystem, so
  a program is reproducible and a wall clock measures the engine rather than the disk.
- Failure is a first-class state with a reason string rather than an exception, because the
  reason is printed and a dead step's record has to survive it.
- The resource gate was measured before the design depended on it: a diamond program of depth 20
  over four rounds runs in 0.001 s with the verdict memo and 15.4 s without it, with 16.8 million
  checks against 844 and byte-identical traces. Each extra level doubles the second number.

## Stage 7 re-attack (D7)

Read cold, with the built tree in front of me, the first plan I would write is still a recursive
`up(step)` over a per-step map of read paths to digests, with a set of the steps already brought
up to date this round. Against the finished brief that plan is wrong in three ways it does not
announce: the map cannot hold a look and a read on the same path as different observations, nor
the order that decides which steps a walk runs; the set cannot tell a step that was checked from
one that ran, so it reports no `stuck` and hands back stale values; and the set is not keyed on
anything, so it says nothing about a verdict going out of date inside a round.

The load-bearing facts are still distributed - the shipped service no longer carries the
checked-against-ran distinction at all, since the `built` set that used to expose it was deleted
once `decisions.py` showed it was a one-field answer to the `stuck` rule - and the brief states
the rules without stating a structure. The clock forces the memo, and the memo is where the
correctness rule lives, so speed and correctness are the same choice.

This attack is by the author who wrote the model, so it measures memory as much as difficulty
(CLAUDE.md, reach-pair-sweep). It is recorded as author-run and contaminated. Standing in its
place: 21 wrong readings each written as a whole engine and each separated by an enumerated case;
`tools/onelinecheck.py` finding no exact rule of two terms or fewer for three of the four graded
quantities; and a measured scale boundary of 217 s against 0.003 s on identical traces.

Estimated solves, updated: 2 of 8. No local evidence moved it from the Stage 1 figure.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no Docker daemon and no harbor in this session |
| Image contents and reference run, interpreted from the Dockerfile | pass | `tools/imagecheck.py`: 14 files, workdir /app, reference placed into 5 files, all 4 shipped programs run |
| No answer leaked into agent image | pass | environment/ copies only app_src; nothing from tests/ or solution/; `extraneouscheck` clean |
| `harbor run -a oracle` = 1 | emulated | `authoring/pull-check-stale/host_trial.py oracle` = 1, worker 0.1 s of 60 s. Container evidence still owed |
| `harbor run -a nop` = 0 | emulated | same harness, nop = 0, 15 of 33 hand programs and 192 of 308 generated wrong |
| Cheats all score 0 | emulated | 38 of 38 score 0 through the same harness, each caught by a named test (`cheat_report.py`) |
| Correct variants score 1 | emulated | `ok-flat` and `ok-loose` both 1 |
| Reference against the sealed model | pass | 590 generated programs over seven seeds plus the 33 hand cases, 0 mismatches |
| Wrong readings separated | pass | `tools/readingcheck.py`, 21 of 21 separated by an enumerated case |
| Short-rule check on the graded decisions | pass | `tools/onelinecheck.py`: 3 of 4 have no rule at depth <= 2 |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | no errors; one warning, reviewed below |
| `difficultycheck.py` on the built tree | pass | 100/100, in band, no drift finding |
| `forgecheck.py` | pass | the answer-key carrier is present and scores 0 |
| `structcheck`, `hintcheck`, `catcheck`, `solvecheck`, `deadfieldcheck`, `extraneouscheck` | pass | clean |
| `simcheck` | reviewed | only the 7-line environment/Dockerfile is NEAR, and it is already identical across three retained bundles |
| `harbor check` rubric | not run | no API key |

The one preflight warning is `say.py: stuck() is defined but nothing in the environment calls
it`. It is true and intended: the frozen trace writer carries one method per line the contract
defines, and the shipped service never reaches the `stuck` one, which is one of its defects. The
instruction states the `stuck` outcome, so nothing is handed over by the method existing.

## Open questions and next steps

The container gates are the only thing this session could not run: no Docker daemon and no
harbor binary. Everything the host emulation can reach was run, and it exercises the same
worker, the same sealed grader and the same wall clock - but not the privilege drop, the
root-owned 0700 reward channel, or the reaping of survivors. The eleven probe cheats score 0
here for the honest reason that they do no work; that they are also contained is the thing only
a container run proves. Run `python tools/docker_trial.py pull-check-stale --all` on a machine
with Docker before submitting.
