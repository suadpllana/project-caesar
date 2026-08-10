# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - re-attack after an easiness-probe failure`. The task was rebuilt; the reference,
the nop and every cheat have been re-run locally.

## Why this rebuild happened

The first shape of the task used five fields and eight codes. That is `8**5 = 32768` possible
choices, and a probe agent represented the whole joint space exactly as a 32768-bit Python
integer: one bit set per choice. A file's summary became one such integer (the pairwise relations
intersected inside the joint space), the filter became another, and the answer was
`(file & filter) != 0`. Every trap in the design evaporated at once:

- pairwise-versus-joint stopped mattering, because the joint space was represented directly;
- the resource gate stopped mattering, because 24000 questions is 24000 big-integer ANDs.

Opus 5 solved it 3 times out of 3. The lesson is in the shape, not the wording: **if the joint
space fits in memory, no amount of careful specification makes the problem hard.**

## What changed

| | before | after |
|---|---|---|
| Fields | 5 (`a`-`e`) | 12 (`a`-`l`) |
| Codes | 0-7 | 0-15 |
| Third candidate | none | a field the summary lists under `unset` may be given nothing |
| Filter semantics | two-valued | three-valued; a condition on an unset field is neither, and `not` leaves that alone |
| Pair records | always binding | say nothing about a choice where either side is unset |
| Joint space | 32768 | `17**12`, about 5.8e14 |
| Timed run | 1200 files x 20 queries in 30 s | 1400 files x 24 queries in 30 s |
| Instruction | ended with a paragraph flagging where the trap is | that paragraph is gone; the rule is still stated in full under "When a file has to be read" |

The removed paragraph withheld no fact. It named where a reader would go wrong, which is the
plan, and handing over the plan is what the difficulty doctrine says not to do.

## Why it is hard now (measured, not asserted)

On the small graded block, 972 file-and-filter questions, truth from the model that tries every
choice:

| Wrong plan | wrong | direction |
|---|---|---|
| narrowing to a fixed point, no search | 74 (7.6%) | read when the truth says skip |
| never taking a field unset | 74 (7.6%) | skip when the truth says read |
| holding the pairs against an unset side | 74 (7.6%) | skip when the truth says read |
| two-valued filter, unset reads false | 34 (3.5%) | read when the truth says skip |

And the clock, measured on a slice of the real timed workload (`scratchpad/slowplan.py`):

| Plan | per question | over the timed run (33600 questions) |
|---|---|---|
| complete search, filter narrowed once up front, pruned on committed values | 137.7 ms | 4628 s |
| reference: filter propagated as a constraint, to a fixed point, at every step | 0.046 ms | 1.5 s |

Budget is 30 s. The gap is three thousand, so it is a replan and not a tuning exercise, and it
does not show up until a lot of correct code exists. That is the Prong C late failure.

A fourth correctness trap turned up while building the measurement harness and is worth knowing:
a search that only forward-checks from the value it just committed never checks a pair whose two
fields were both already down to one candidate before the search started. It reads files it
should skip.

- Expert time estimate: 12 hours
- Estimated solves out of 8: 2 to 3
- Prong A: the memorized plan for summary-based file skipping is narrowing, and narrowing is
  specifically wrong here. Prong C: the correct-and-slow plan is fatal and only fails late.
  Prong B is thin - the environment is empty by design, as it was in the accepted first version.

## Verifier contract - FROZEN

- Artifact: `/app/file_reads.py`, holding `files_to_read(manifest, filter_expr)` and `Reader`.
- Small block: 18 files x 54 filters, inside four fields, graded by trying every choice.
- Wide block: 420 files x 260 filters, all twelve fields, graded by the searching model.
- Timed block: 1400 files x 24 queries from a seed root draws at run time, graded on a digest of
  every answer, with a 30 s wall-clock budget measured from the parent process.
- The searching model is fenced from both sides: it verifies its own witness against the
  definitional checks before saying read, and a grading case throws sampled witnesses at the wide
  manifest to catch it skipping.

## Validation status

| Check | Status | Notes |
|---|---|---|
| `preflight.py` | pass | 3 warnings, all pre-existing and deliberate |
| Reference scores 1 | pass | 12 tests, whole verifier run 91 s, timed block 3.2 s of 30 s |
| nop scores 0 | pass | |
| `cheat/read_everything.py` | pass (0) | |
| `cheat/read_nothing.py` | pass (0) | |
| `cheat/take_the_answers.py` | pass (0) | |
| Docker images build | not run | Docker Hub is unreachable from this machine (403 on the registry CDN); the verifier was run at its real absolute paths with the same two unprivileged accounts instead, via `scratchpad/runverifier.sh` |

## Open questions and next steps

- Build both images and run `harbor run -a oracle` and `-a nop` on a machine that can reach
  Docker Hub. Nothing in the Dockerfiles changed, but this has not been executed here.
- The `metadata` prose in `task.toml` is the contributor's own voice and carries the new
  measurements; it needs the contributor to read it back before submission.
