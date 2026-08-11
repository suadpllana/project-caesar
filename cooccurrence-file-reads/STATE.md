# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - second pass`. Rebuilt once after an easiness-probe failure, then repaired again
after the quality review failed it on determinism. Reference, nop and every cheat re-run
locally after both rounds.

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
| Timed run | 1200 files x 20 queries in 30 s | 1400 files x 24 queries in 60 s |
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
| complete search, filter narrowed once up front, pruned on committed values | 141.2 ms | 4743 s |
| reference: filter propagated as a constraint, settled before codes are committed | 0.063 ms | 2.1 s |

Budget is 60 s. The gap is three thousand, so it is a replan and not a tuning exercise, and it
does not show up until a lot of correct code exists. That is the Prong C late failure.

A fourth correctness trap turned up while building the measurement harness and is worth knowing:
a search that only forward-checks from the value it just committed never checks a pair whose two
fields were both already down to one candidate before the search started. It reads files it
should skip.

## The quality-review failure, and what fixed it

The review failed two blocking criteria, both the same fact: the reference's runtime on the
timed workload had a heavy tail across seeds. They measured 3.2 s to 236.1 s over ~35 seeds,
with one filter of one seed accounting for the 236 s. My own 14-seed sweep had not been large
enough to see it. Reproduced exactly: seed 1913820983, query 13, one file out of 1400 taking
150 s of the 163 s.

The cause was a missing decision about **what to branch on**. That query is an `or` of three
conjunctions. A requirement resting on several live arms narrows nothing while it rests there,
so the solver was committing codes -- sixteen candidates a field, twelve fields -- inside a
space the filter would have cut away had an arm been picked first. Settling open arms before
committing any code takes that query from 162.6 s to 0.07 s, same answer.

That ordering then earns a second simplification, which is what removes the rest of the
variance: once nothing rests on several arms, every requirement the filter makes has landed on
a field and cut it to the codes that meet it, so the filter is true on any choice inside the
domains. Only fields that take part in a recorded pair are left to settle, so fields in no pair
are never committed at all.

Measured after the fix, over **400 random seeds**: median 3.20 s, p90 3.67 s, p99 4.05 s,
max 4.23 s, worst single query 0.32 s. Budget raised from 30 s to 60 s for margin, which still
leaves the wrong plan 79x over. The grading model got the same fix and was swept the same way
over **200 seeds**: median 7.82 s, p90 9.16 s, p99 9.91 s, max 9.91 s (the review had measured
17 s to 213 s). So verifier runtime is no longer seed-dependent either, and every block now has
a kill limit that keeps the session inside the 2400 s verifier timeout whatever a submission
does.

Neither tail is *proven* away - both are measured away, with the worst observed case sitting
14x inside the budget for the reference and comfortably inside the verifier timeout for the
grading model.

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
  every answer, with a 60 s wall-clock budget measured from the parent process.
- The searching model is fenced from both sides: it verifies its own witness against the
  definitional checks before saying read, and a grading case throws sampled witnesses at the wide
  manifest to catch it skipping.

## Validation status

| Check | Status | Notes |
|---|---|---|
| `preflight.py` | pass | 3 warnings, all pre-existing and deliberate |
| Reference scores 1 | pass | 12 tests; timed block 3.2 s of 60 s |
| Timed block stable across seeds | pass | reference, 400 seeds: median 3.20 s, p99 4.05 s, max 4.23 s |
| Grading model stable across seeds | pass | oracle, 200 seeds: median 7.82 s, p99 9.91 s, max 9.91 s |
| Reference vs both models | pass | 400 filters vs brute force, 360 at twelve fields, 0 disagreements |
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
- Any future change to the search must be re-swept over several hundred seeds, not a dozen.
  A dozen was what let the tail through the first time.
