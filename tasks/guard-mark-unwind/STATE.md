# Task state

Working memory for this task. Never ships - `package.py` excludes it and no pipeline gate
reads it. It exists for the next session and for `preflight.py`.

## Current stage

`Stage 7 — repairing pipeline rejections`. Submitted 2026-08-31, failed the quality review on
one blocking criterion (solution quality); repaired the same day. Resubmitted and cleared the
easiness probe, then failed the **difficulty probe 0 of 8** on 2026-09-01. Recalibrated; see
"Decisions" below and the difficulty-rejection section in CLAUDE.md.

## Assistant's assigned role

You maintain async runtimes and the task queues on top of them, so most of your hard bugs are
cancellation bugs.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. Seed is the simplified-priority-restore class of bug
  documented by FreeRTOS and the structured-concurrency cancellation semantics in Trio and
  anyio; nothing is vendored and the simulator is written here.
- Task shape chosen: authored-on-top, self-contained simulator.
- Upstream-diff check: no upstream exists, so there is nothing to diff against.

## Task summary

The tree is a working cooperative runtime whose cancellation semantics are the ones a
single-delivery cancellation token gives you. Seven decisions are wrong across three editable
files. The agent rebuilds them so that no op of a program runs inside a guard the fiber can
see that has been marked.

## Why it is hard

The wrongness is coherent rather than broken, and it is the shape almost every mainstream
async library has, so it is the shape a frontier agent reconstructs from its prior.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer — required): the natural fix for the first discovery is what the shipped code already does, and it is right until a mark lands while a cut is already travelling, so the second discovery invalidates the natural implementation of the first, and neither shows up as a crash.
- Tactics making that true: prong A, since the retrieved cancellation-token answer is specifically wrong here, and prong C, since a wrong reading survives to the verifier as one extra token in an otherwise perfect trace.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): the first plan stamps the chosen guard onto the exception and matches it by identity at the boundary, which passes every test anyone would write and fails whenever a second guard is marked mid-unwind.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 1 of 8, on the hard edge.
- Difficulty score anchor: not yet anchored.
- Score history: 2026-08-31 submitted, quality review failed on solution quality only;
  2026-09-01 easiness passed and difficulty came back 0 of 8, recalibrated by stating the
  input space in the brief.
- Leak audit (docs/DIFFICULTY.md): the runtime ships no expected output, no comments and no
  self-describing names; the graded set is three hundred programs generated inside the verifier
  from a nonce made after the agent has finished, so a rule fitted to the shipped programs
  carries no information about the rest.
- Expert path, described step by step: read the op set and the two-phase wait out of the loop;
  drive the shipped programs and notice the token emitted inside a guard that is already marked;
  derive the window rule from the shield behaviour; rebuild delivery to name the outermost
  marked guard; find that the stamped guard goes stale mid-unwind and move the resting decision
  to each guard as it closes; then the band rules, holding while children are alive so the
  answer is recomputed when the last child ends.
- Originality check: searched for public write-ups of this failure mode; the FreeRTOS and Zephyr
  discussions describe the priority-restore variant, not this one.

## Verifier contract — FROZEN after Stage 2

- Artifacts the agent produces: `/app/kern/pick.py`, `stop.py`, `knot.py`, `wake.py`.
- What is checked: the ordered event trace and every fiber's emitted token list, exactly, with
  no partial credit, over twenty-eight enumerated programs and three hundred generated inside
  the verifier from a run-time nonce.
- Tolerances: none. Exact equality on both axes.
- Ground truth, and where it lives: `tests/gt.json` for the enumerated set, root-only; the
  generated set is graded by `tests/oracle.py`, a sealed second implementation, after the run.
- Deliberately not graded: how often a submission consults the chain, what it caches, and which
  data structures it keeps. Those are implementation choice, and six variants disagree on them.

## Decisions and their reasons

- **The reference lives in exactly one place: `solution/*.py`, beside `solve.sh`.** The first
  submission had `emit.py` inline all three files into `solve.sh` as heredocs *and* keep
  byte-identical copies in `solution/ref/`, which is what failed the quality review. `solve.sh`
  now resolves its own directory and copies them in, the way `typeahead-query-controller` does -
  the only solve.sh in this repo to have cleared that review. The platform hands the oracle
  agent the whole `solution/` directory, so files beside `solve.sh` are readable at run time.
  Do not re-inline them: `tools/solvecheck.py` fails the bundle if anyone does.
- `kern/wake.py` is declared as an artifact and needs no change. That is deliberate - part of
  the work is establishing that a file which may be edited does not have to be.
- **The agent's real chain is eight decisions, not seven.** The shipped tree is already
  correct on 15 of the 27 enumerated cases; the other 12 come from eight distinct decisions,
  six of which the brief states outright. The two it does not state are the ones the task is
  built on and they stay underived: delivery to the outermost marked guard in view, and the
  resting guard decided as each guard closes rather than when the cut was raised.
- **The 0-of-8 repair states the input space, never the rule.** Three sentences say that a
  mark can land while a cut is already travelling and that the graded programs do it, plus
  the positive wake rule whose negative fence was the only half stated. Nothing says where
  the cut then rests. Do not add that sentence later - it is the whole task.
- **Two defects came out of the failing trajectory (2026-09-01), both mine, both fixed.**
  The brief said "Errors are not marks. No guard takes an error, marked or not." and never
  said that a child ending on an error marks the band's own guard; the agent set `reap` to
  return False, flagged it as its one guess, and lost 140 of 300 programs. And `Gd.own` /
  `Gd.kind` were written by loop.py and read by nothing - no frozen file, no cheat, no
  variant, not the reference - so the agent treated them as a hint and invented a band-skip
  rule worth another 73 of 300. The fields are deleted and the error rule is stated. Do not
  reintroduce either: a dead field is a false affordance, and it is worse than dead code
  because it looks like a clue.
- The same trajectory got the **hard** discovery right (resting decided as each guard closes)
  and lost on the peripheral two. That is the evidence the difficulty is in the right place
  and the losses were unfairness, not depth.
- **A fourth cause came out of the local three-agent probe.** The one agent that finished
  passed all 27 enumerated cases and failed 6 of 300 random programs; adding `if not g.hit:
  return False` to its `stop.py` took it to reward 1. The undecided rule was whether an
  unmarked guard can absorb a travelling cut. It is now stated in the brief and pinned by
  `unmarked-guard-passes-it`, a shrunk 21-line counterexample, inside the delivery sweep.
  The lesson for the next task: one enumerated case per rule did NOT separate this reading -
  write the wrong reading as a policy file and differential it, or the hole stays invisible.
- `cheat-spawn-order` differs from the reference on **1 program of 427**. It is stated in the
  brief so it is fair, but it is a lottery ticket under all-or-nothing grading. If this needs
  another notch of solve rate, shipping that ordering already correct is the cheapest place
  to take it from, since it costs no difficulty.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `docker_trial2.py --build` |
| No answer leaked into agent image | pass | sweep cheat finds nothing |
| `harbor run -a oracle` = 1 | pass | real two-image trial, reward 1 |
| `harbor run -a nop` = 0 | pass | real two-image trial, reward 0 |
| Cheats all score 0 | pass | 24 of 24, in the container |
| Variants all score 1 | pass | 6 of 6, in the container |
| `preflight.py` | pass | see handover |
| `solvecheck.py` | pass | clean |
| `harbor check` rubric | not run | harbor is not installed here |

## Open questions and next steps

The other six tasks in `tasks/` carry the same solve.sh defect this one was rejected for -
`tools/solvecheck.py --all` names them. None has been repaired; that is a decision for the
contributor, since each needs its own repackage and re-trial.
