# Task state

Working memory for `unit-take-bind`. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - packaged` (2026-09-07). `tasks/unit-take-bind.zip` built and checked.

## Assistant's assigned role

Language-tooling engineer on the front half of a compiler: the parser, the module graph and the
name binder, plus the editor service that has to answer "what does this name mean here" on a
half-saved tree. The bugs that cost most in that seat are binding bugs that are invisible on
small inputs and change meaning on large ones.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, authored machine
- Task shape chosen: not applicable (no vendored repository)
- Everything under `environment/app_src/` was written for this task; no upstream to diff against.

## Task summary

A small binder for a module language. A program is a flat list of declarations: a unit `own`s a
name, `als`es a name to a unit, `pull`s one name or every name from a source, `shut`s a name out
of wide pulls, `hide`s it from every pull, and `ask`s what a name means. Every name a unit could
mean carries a rank - 0 for a local declaration, and one more than the larger of the source
reading's rank and the rank the name already holds in the source unit for anything pulled. A
name is settled from its lowest-ranked candidates alone: all of them agreeing on one origin binds
it, two origins make it a clash, and a clash is terminal and carries nothing onward.

The shipped binder is four files under `/app/res/` - `step.py` costs a candidate and resolves a
pull's source name, `show.py` says which names each kind of pull can reach, `pick.py` settles a
candidate set, `turn.py` drives the settlement. All four ship wrong. The agent replaces them so
`run_prog.py` prints the right answer for every `ask`.

## Why it is hard

The rules are all stated, and the natural implementation of the stated rules is wrong. Binding
is a fixed point, so the reflex is a relaxation loop: recompute each unit's bindings from the
current state, keep the lowest rank seen, repeat until nothing moves. That loop is correct while
every name has one origin. Clash breaks it: a clash removes a binding rather than adding one, so
a name that settled to one origin early in a sweep, was carried onward by the units visited after
it, and only became contested later leaves those carried bindings standing. Nothing in the trace
says so - the wrong answer is a plausible origin at a plausible rank, on programs where the
right answer is that the name means nothing at all.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the rules describe a fixed point and the plan they invite is a relaxation loop, which is correct until clashes exist and silently wrong afterwards, so the settlement order turns out to be part of the semantics rather than an implementation detail - and that only becomes visible after the clash rule is already implemented, which makes it a replan rather than a patch.
- Tactics making that true (docs/DIFFICULTY.md): A1 A2 A3 B1 B2 C1 C2 C4, prong A prong B prong C. In full: A1 the fixed-point reflex is specifically wrong
  here and every retrievable resolver describes exactly that reflex; A2 the settlement is
  described operationally - lowest-ranked candidates, decided once, never resting on a later
  fact - and never named; A3 the cost rule pairs a shortest-path quantity with a non-monotone
  contest rule, which no single standard technique settles; B1 the rank rule, the two readings of
  a source name, and the reach of each kind of pull live in four files that consume each other's
  answers, and the shipped driver's shape is the thing that has to be thrown away; B2 ten rules
  hold at once and each changes what another means - a clash removes visibility, which changes
  ranks, which changes which candidates tie; C1 both sides of every fence are graded, so a binder
  that clashes whenever it sees two candidates fails as hard as one that never clashes (measured
  over three nonces: 25.9-32.1% and 23.7-25.1% of the population respectively); C2 the shipped
  engine is the only oracle and it is wrong on about a third of the population, so running it
  proves nothing; C4 all-or-nothing over 37
  enumerated programs and 318 generated from a nonce drawn after the agent has finished.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was "parse; per unit collect candidates; iterate to a fixed point recomputing each unit from the current state; per name take the minimum rank; if the minimum-rank candidates share an origin bind it, else clash".
  That is the `in-place-sweep` reading in
  `authoring/unit-take-bind/readings.py`. It is wrong on 7.3-9.6% of the graded population,
  depending on the nonce, and scores 0, because a binding carried onward before the second route to its name arrives is
  never withdrawn. The repair is not a patch to the loop - it is settling strictly by increasing
  rank, so no conclusion ever rests on a fact settled later, which is a different driver.
- Estimated solves out of 8: 3 (design target was 1-2; revised upward after the Stage 7
  re-attack, because every rule has to be stated for fairness and the well-foundedness
  sentence lets a careful reader derive the settlement order without experimenting. The
  remaining bar is the conjunction: ten rules, all-or-nothing, over 355 programs)
- Difficulty score anchor: not yet anchored - first complete submission
- Score history: 2026-09-07 first build; no pipeline result yet
- Leak audit (docs/DIFFICULTY.md): the agent tree ships no expected outputs, no ground truth and
  no second implementation, so nothing in it can name or verify a decision. `progs/*.txt` are
  inputs only. Every field on `Unit` is read by the shipped engine (`deadfieldcheck`), and no
  helper exists that the engine does not call. The `res/tell.py` formatter ships correct and is
  not editable, which fixes the output shape without disclosing any rule. A script that tries to
  reproduce the graded answer from the shipped files without applying the rules gets the shipped
  engine's answer, which is wrong on a third of the population - recorded under Decisions below.
- Expert path, described step by step: read `prog/read.py` and `prog/unit.py` for what a
  declaration becomes; read `prog/deck.py` for how a settled binding is keyed; write the cost
  rule and the two source readings into `step.py`; write the two reach rules into `show.py`;
  write the origin-agreement rule into `pick.py`; then find that the shipped driver cannot
  express a terminal clash without retracting what it already carried, and rewrite `turn.py` to
  settle one rank at a time from facts of lower rank only; check against hand-built programs
  where a name is reachable twice at the same rank and twice at different ranks.
- Originality check: searched 2026-09-07. The closest public material is Rust RFC 1560 and the
  rustc dev guide, which describe a work-list resolver, glob shadowing and ambiguity-if-used.
  Two designs were dropped before this one for failing exactly this test: a merge-on-read table
  task whose graded decisions are the Iceberg v2 spec plus an open `apache/iceberg-go` issue,
  and a first pass at this task built on Rust's own precedence rules. The rules kept here are
  authored and differ from every published resolver in the load-bearing places - precedence is
  by rank alone with no explicit-beats-wide rule, a source name has two readings that both
  contribute candidates, ambiguity is terminal rather than deferred to use, and `shut` and
  `hide` split the two kinds of pull - so a retrieved resolver plans the wrong binder.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-07, before the verifier was written.

- Artifacts the agent produces: `/app/res/step.py`, `/app/res/show.py`, `/app/res/pick.py`,
  `/app/res/turn.py`. Nothing else is read.
- What is checked: the verifier overlays those four files onto its own pristine copy of the
  tree and runs every graded program through `run_prog.py`'s pipeline. The printed lines are
  compared exactly, in order, against the sealed answer. All-or-nothing.
- Interfaces held fixed: `step.cost(rs, rv)`, `step.srcs(deck, prog, u, s)`,
  `show.out_all(deck, prog, vn)`, `show.out_one(deck, prog, vn, x)`, `pick.settle(cands)`,
  `turn.run(prog)`. Everything else about the four files is the agent's choice.
- Tolerances: none. Exact string equality on every line of every program.
- Ground truth: `tests/gt.json` for the enumerated programs, frozen from `tests/model.py` by
  `authoring/unit-take-bind/build_gt.py`. Generated programs are settled by `tests/model.py`
  inside the verifier. The grader asserts the model still reproduces `gt.json` before grading
  anything, so a drifted model cannot redefine correct.
- Graded decisions: (1) a local `own` is rank 0 at its own unit; (2) `als` is rank 0 and binds
  only when its target is a declared unit; (3) a pulled candidate costs one more than the larger
  of the source reading's rank and the name's rank in the source; (4) a source name has one
  reading per unit it can denote - the program unit of that name at rank 0, and any unit the name
  is bound to in the pulling unit at that binding's rank; (5) a wide pull reaches names that are
  neither hidden nor shut; (6) a narrow pull reaches names that are not hidden, shut included;
  (7) only the lowest-ranked candidates decide; (8) agreement on one origin binds, two origins
  clash; (9) a clash is terminal and carries nothing onward, by either kind of pull; (10) a
  binding is decided once, from facts of lower rank only, so declaration order never moves it.

## Decisions and their reasons

- **No resource gate (C3).** Measured: the per-rank sweep against the event-driven settlement on
  chain programs is 3.7x at 60 units and 19.1x at 360 units, and reaching a 60-second sweep needs
  roughly 2800 units. The gap is a generic delta optimisation rather than a domain invariant, so
  it would have graded execution rather than the plan. `docs/DIFFICULTY.md` allows a compact task
  without B1-scale or C3 when the semantic conjunction is real; `focus-return-point` is the
  precedent. Recorded so a later session does not add a timeout and call it difficulty.
- **`res/tell.py` ships correct and is not editable.** It fixes the trace format, so no
  submission loses on formatting, and it discloses no rule - it only names the four outcomes,
  which the instruction states anyway. It also keeps every editable file one that genuinely
  needs work.
- **The shipped driver has an iteration bound.** Without it the shipped relaxation does not
  terminate on some generated programs, which would have made the do-nothing trial a timeout
  rather than a failure. The bound is written the way legacy code carries one.
- **Alias tags sometimes collide with unit and item names in the generator.** Without the
  collision the two source readings never tie and two of the misreadings moved nothing.
- **Declaration order is shuffled in every generated family.** The rules never mention order,
  so a settlement that depends on it is wrong, and shuffling is what makes that observable.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference agrees with sealed model | pass | 318 generated + 37 hand programs, 0 disagreements |
| Every misreading separated | pass | 16 readings, all moved, each named by a hand case |
| Shipped tree is wrong | pass | 112-135 of 355 across ten nonces, terminates in 0.2s |
| Reference agrees with sealed model | pass | 318 generated + 37 enumerated, 0 disagreements |
| `readingcheck` | pass | all 16 readings separated by a named enumerated program |
| `onelinecheck` | pass | no graded decision has an exact rule at depth <= 2 |
| Docker image build | BLOCKED | registry blob CDNs refused by egress policy (403 on CONNECT) |
| oracle = 1 | pass | shipped `tests/test.sh` at /tests, /work, /logs/verifier, /app |
| nop = 0 | pass | same run; 17 of 41 graded tests fail |
| Four correct variants = 1 | pass | ok-heap, ok-jacobi, ok-renamed, ok-shapes |
| 25 cheats = 0 | pass | `cheat_report.py`: each caught by the check that should catch it |
| Isolation layer asserted | pass | `probecheck.py`: 9 denials as uid 1002, survivor reaped |
| No answer leaked into agent image | pass | `imagecheck.py`; tree holds no expected outputs |
| `preflight.py` | pass | no errors, no warnings |
| `harbor check` rubric | not run | harbor is not installed in this container |
| `zipcheck` on the archive | pass | 77 entries, no clutter, .sh modes 0755 |
| Quality self-review | pass | docs/QUALITY-REVIEW.md, criterion by criterion |
| Oracle determinism | pass | six runs, a fresh nonce each, reward 1 every time |

## Stage 7 re-attack (D7), 2026-09-07

Read the finished instruction cold. The first plan is still the relaxation loop, and it is
still wrong - `late-clash` and the `late` family catch it, and the cheat generated from it
scores 0. What changed against the Stage 1 estimate is that the well-foundedness sentence
("settled once, out of facts that cost strictly less than it does") has to be in the brief for
the semantics to be determinate, and a careful reader can derive the settlement order from it
without experimenting. So the honest number moved from 2 to 3.

The load-bearing facts are still distributed: what a declaration becomes is in `prog/read.py`,
how a settled binding is keyed is in `prog/deck.py`, the shape the driver has to lose is in
`res/turn.py`, and the two source readings only make sense once `prog/unit.py` shows that a
unit exists because a line names it. Nothing in the tree names or verifies a decision.

Residual risk, stated plainly: this is a compact task whose rules are all disclosed, so it
sits nearer the easy edge of the band than the hard one. It has no resource gate, by the
measurement recorded above.

## Open questions and next steps

- Package, run `zipcheck` on the archive, and hand over. The container gates could not be run
  here; the emulation at the container's own paths is the strongest evidence available in this
  session and is labelled as such wherever it is reported.
