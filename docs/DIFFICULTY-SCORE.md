# The difficulty score, and the band a new task must reach before code

`tools/difficultycheck.py` scores a task design out of 100 and compares it with the tasks
`README.md` lists as passed. It is the pre-code gate: an idea is written down as a difficulty
record, scored, and only a record inside the band goes on to Stage 2. Everything below is the
rubric, the calibration that set the band, and the rules for using it honestly.

## Why a number

The difficulty band is decided at plan time (`docs/DIFFICULTY.md`), and every rejection this
repository has recorded on `difficult` or on easiness was visible in the design before any code
existed: a first plan that was the correct one, a second finding that only added a case, rules
that could each be confirmed alone, a brief that stated the method, a reference of forty lines.
The passing tasks share one shape, written up in `docs/PASSING-TASK-RESEARCH.md` as ten intake
questions. The checker turns those questions into fields and the shape into points, so the
comparison with the passing set happens on the day the idea is formed instead of at the review.

## The record

The record lives at `authoring/<slug>/difficulty.toml`, outside the bundle, and never ships.
`template/difficulty.toml` documents every field. Before a slug exists the record can live
anywhere and be scored by path. The sections:

| section | what it holds | intake question |
|---|---|---|
| `task` | slug, expert hours, estimated solves out of 8 | 10 |
| `plan` | the first plan and its source, the breaking rule, the second discovery and whether it forces a replan, the author's cold attack, the expert path | 1, 2, 3, 10 |
| `search` | the best page a probe agent retrieves, whether it plans the task, where the spec departs from it | - |
| `tactics` | each tactic from `docs/DIFFICULTY.md` the design uses, justified in this task's terms, plus the route-around guard | - |
| `decisions` | how many decisions are graded, which pairs interact and why, whether the agent can confirm them one at a time | - |
| `fences` | the ordinary case, the late adversarial case, the denied oracle | 5, 6 |
| `leaks` | what could reveal a discovery and how each is closed; that no derivation ships | 4 |
| `gate` | the resource gate with its naive family, invariant, scale and limit, or why none exists | 7 |
| `cheats` | wrong readings with a hand case each; correct variants | 8, 9 |
| `shape` | planned environment lines, editable files, reference lines; measured from the tree once it exists | - |

## The rubric

| axis | max | what earns it |
|---|---|---|
| planning attack | 22 | a concrete first plan with a named source, the breaking rule, a second discovery distinct from it, and `replan` rather than `patch` |
| search test | 8 | the best page named, it does not plan the task, the deviation stated |
| tactics | 12 | up to five tactics justified in the task's terms across at least two prongs, plus the guard |
| rule interaction | 15 | three or more graded decisions, interacting pairs with reasons, no per-decision feedback |
| fences and late failure | 10 | ordinary case, late case, denied oracle |
| leak audit | 9 | three candidates each closed, primitives stated, no shipped oracle |
| resource gate | 5 | naive family, invariant, scale and limit; or a reason none fits |
| cheats and variants | 6 | six or more wrong readings with hand cases; two correct variants |
| solvability | 7 | five or more expert-path steps; solves estimated at 1 to 3 |
| shape | 6 | expert hours of six or more; 200 or more environment lines; 100 or more reference lines; 1 to 7 editable files |

Hard stops cap the score at 40 whatever the axes add up to: the author's first plan is the
correct one, the best page plans the task, an oracle ships, the expert path has fewer than three
steps, solves are estimated at 0 or 8, or the expert estimate is under two hours. Each is a
sentence from the doctrine that ends the design on its own.

Vocabulary that does not create difficulty - many files, large repository, obscure, random
names, short timeout, more cases - is reported wherever a tactic rests on it, and scores nothing.

## Calibration, 2026-09-09

Records for the six passed tasks whose bundles are in this checkout were transcribed from
their `STATE.md`, `task.toml` explanations, cheat headers and verifier docstrings, with the
sources listed in each record. Nothing was written into a record that its sources do not say.

| task | score | evidence for the pass |
|---|---|---|
| `note-carry-forward` | 100 | contributor reported, nine trajectories retained |
| `focus-return-point` | 98 | contributor reported |
| `alias-settle-report` | 96 | contributor reported, easiness and difficulty probes |
| `delta-view-retraction` | 96 | easiness pass recorded in state |
| `guard-mark-unwind` | 96 | passed all nine gates 2026-09-01 |
| `share-register-screen` | 95 | contributor reported |

Band: **95 to 100**, median 96. `BAND_FLOOR` in the checker is 95. The five passed tasks without
a bundle here (`concurrent-commit-rules`, `sheet-block-place`, `move-clash-merge`,
`heap-file-replacement`, `late-dimension-updates`) have no record and do not move the band;
add one only when their bundle or state is supplied, never reconstructed from the slug.

The calibration is two-sided. `authoring/controls/` holds records of designs the pipeline
rejected, transcribed from the same state files, and each must score below the floor:

| control | score | what the pipeline said |
|---|---|---|
| `scope-hold-release-2026-09-07` | 59 | quality review, `difficult`: the complete plan is available without exploration; each decision maps to one small function; B2 is only a checklist |
| `note-carry-forward-round3` | 48 | quality review, `difficult`: the work reduces to a per-revision walk and one predicate change; 98-line reference, one insight |
| `publish-settle-order-first-build` | 40, hard stop | quality review, `difficult`: roughly 100 lines across five files; the two inventions are standard techniques |
| `alias-settle-report-first-build` | 40, hard stop | easiness 2 of 3: the definition itself supplied the algorithmic plan |

The four tasks in `tasks/` that have not passed the pipeline are scored for context, not
calibration; the external probe is the authority on them:

| pending task | score | state |
|---|---|---|
| `publish-settle-order` | 98 | easiness recovery pending the platform probe |
| `reach-pair-sweep` | 96 | rebuilt after two `difficult` rejections; not yet resubmitted |
| `token-seam-emit` | 96 | packaged, external result not yet recorded |
| `scope-hold-release` | 89 | below the band with no hard stop: its state commits to no solve estimate for the rollback design, no answer on per-decision feedback, and no cold attack saying the first plan is wrong - which is the same "material difficulty risk" the state itself records |

The gap between the weakest pass and the strongest rejection is 36 points. What separates them
is not prose volume: the controls lose on a missing second discovery, `patch` instead of
`replan`, no interacting pairs, per-decision feedback, a thin leak audit and a small reference.

`python tools/difficultycheck.py --calibrate` reprints both tables and fails when the band
constants in the checker no longer match the passed set or when any control reaches the floor.
Re-run it after any change to the rubric, to a passed task's record, or to the README pass list,
and update the constants and this file together.

## How to use it, and how not to

1. **Before Stage 2.** Copy `template/difficulty.toml` to `authoring/<slug>/difficulty.toml`,
   answer every field from the idea, and run the checker. Below 95: read the repair list under
   each axis, go back to `docs/DIFFICULTY.md`, and redesign or replace the idea. Record every
   attempt's score and what changed in `STATE.md`. Only a record at or above the floor with no
   hard stop proceeds to the verifier contract.
2. **At Stage 7.** Run it again. The tree shape is now measured rather than declared, and a
   drift over 35 per cent between the planned and built sizes is reported. A design that scored
   96 on paper and 88 after the build has flattened somewhere the report names.
3. **Never tune the record to the score.** The checker reads fields, lengths and counts; it
   cannot tell a true second discovery from an invented one. Every claim in the record is
   restated in `STATE.md`, checked by the cold self-attack, and finally by the probe. A padded
   record produces a number and a rejection. The controls exist so that a rubric loose enough to
   pass padding is caught the next time `--calibrate` runs.
4. **A score in the band is necessary, not sufficient.** It says the design has every part the
   passing tasks have. The probe decides whether those parts are real.
