# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a compiler front-end engineer who has worked on the binder: the stage that decides
which declaration each call means, after names are resolved and before anything is emitted.
You have lived with overload sets, subtype lattices, generic instantiation and the bookkeeping
a speculative resolution needs, and with the difference between a resolution that is correct
and one that finishes on a declaration set of real depth.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. Nothing is vendored; the environment is authored here.

## Task summary

`/app` is the call-binding stage of a small front end. A program file declares kinds, the rise
steps between them, entries (some with an open slot and a bound), values, and the expressions
to bind. `/app/run_bind.py` prints one line per call bound, one per pin kept, one per
expression, and a tally. The shipped binder is the plan everyone writes first - settle what
each argument stands at, then rank the entries that fit by total cost - and it is wrong in ten
places. Six files under `/app/res` are editable; everything else is replaced by the verifier's
own copy.

## Why it is hard

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): every rule is stated and the rules are mutually recursive in a way the structure the tree ships with cannot hold.
  A call in a slot is bound asking for that slot's kind and its result is compared against that
  same kind, so no argument has a kind until the candidate under test supplies one and the
  bottom-up pass has to be turned inside out. The winner is decided by a componentwise
  comparison rather than by a total, so two entries whose costs cross are ambiguous however the
  totals compare. An open entry keeps the kind its first kept trial settled it at while a beaten
  trial leaves nothing behind, which forces exploration to be speculative with a layer per
  trial. Then the deep family makes the exploration all of that implies exponential, and the
  memo that fixes it has to be keyed by the pins in force or it answers one trial from a world
  another trial discarded.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3 and C4, across all three prongs.
  A1: the prior says the arguments are typed before the candidates are ranked and the result
  type plays no part in the choice, and both are inverted here and stated plainly. A2: the
  comparison, the inference and the pin are stated as what the stage does and never named. B2:
  ten rules hold at once and each changes what a correct implementation of the others looks
  like. C1: both sides are fenced, so an over-cautious binder that calls a call ambiguous
  whenever two entries survive fails the ordinary programs. C2: the natural check is a real
  compiler, which disagrees at the result cost and has no pin at all, and the shipped binder
  answers coherently for every program. C3: the deep family, where exactly correct without a
  memo is 330 s on one program against a 60 s limit for 358. C4: line for line over 358
  programs, generated from a seed drawn after the container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was to bind the arguments once, collect the entries that fit, add up the rise steps and take
  the cheapest, inferring an open entry's kind from its first open slot. That plan is wrong at
  three of its four steps and I would not have found the pin discipline before writing the
  recursion. Writing the reference I hit the structural trap myself: the memo was keyed by the
  call's number inside its expression, and since those numbers repeat across expressions the
  second expression was answered from the first. That is now the `memo-asks` case and the
  `memo-site` cheat.
- Estimated solves out of 8: 2 (designed at the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py, before Stage 2): 100/100 on the first
  record, inside the 95-100 band, one warning that the gate was not yet measured. It has since
  been measured (330 s against 60 s) and the record updated.
- Leak audit (docs/DIFFICULTY.md): the program files carry kinds, rise edges, entries, bounds,
  values and expressions, which are primitives; the rise distances, candidate sets, costs,
  settled kinds, pins and the tally are all derived and none of them ships. No step table, no
  pinned kind stored on an entry, no precomputed candidate set, no expected output beside the
  sample programs. The one record quoted in the brief is `tiny.txt`, whose only wrong lines in
  the shipped tree are the order of two bind lines and the tally; it decides no wrong reading
  that an enumerated case does not also decide. Verified by script
  (`authoring/widen-pin-bind/leakscan.py`, 0 findings): no correct output line of any shipped
  program appears anywhere else in the tree, no shipped file names the verifier's own material,
  and every line of every shipped program file starts with one of the six declared ops, so
  nothing in the data is a quantity computed from the rest of it.
- Expert path, described step by step: run the shipped binder on the four sample programs and
  find the module that prints the wrong line; derive from the result-cost rule that a call in a
  slot cannot be bound before the candidate above it is chosen; replace the total with a
  componentwise comparison; thread the pins through a trial as a layer that is kept or dropped
  whole; settle the open kind as the single least common kind and check it against the bound;
  put the kept pins and the bind lines in the stated order; time `deep.txt`, find the
  re-exploration, and memoise on the call, the kind it was asked for and the pins in force;
  re-run the small programs to confirm the memo changed no answer.
- Originality check: searched for public write-ups of this rule set. Overload resolution by
  partial ordering, target-typed argument resolution and generic instantiation are each
  documented (the C++ standard, the JLS, blog posts on why a call is ambiguous), but no source
  carries this conjunction: the result cost as the last component of the same vector, the
  single least common rise target as the inference rule, and an entry that keeps the kind its
  first kept use gave it. The retained tasks in this repository were read: none touches static
  resolution.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/widen-pin-bind/trace.md; rows walked, NOT STATED left, tracecheck result): tracecheck is clean, no NOT STATED rows remain.
  55 graded rows - 4 test functions, 32 enumerated cases, 6 artifacts, the
  60 s clock and 12 rows splitting the sealed model into the rules it applies - plus 24 reading
  rows, 6 shortcut rows and 1 tolerance row. No NOT STATED rows remain; two rows grade the
  verifier against itself and say so. `python tools/tracecheck.py widen-pin-bind` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 25 readings were implemented and run against the reference.
  24 are separated by an enumerated case, measured
  rather than argued, and each moves between 3.1% and 89.6% of a generated sample. The
  twenty-fifth - an expression with no binding printing what its trials bound - turned out to be
  unobservable, because the frozen trace writer decides it, so it was dropped rather than
  shipped as a cheat that cannot fail. No two readings that reproduce the published evidence
  disagree on the graded set.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): every one of them scored 0 through the real verifier.
  Of a 102-program sample, the shipped tree reproduces 18, no-binding-for-everything 8, the worked example replayed 1, always-the-first-entry 43, always-the-last 44,
  and the answer key for all 32 enumerated programs 38.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 60 s clock, and three implementations written apart from the reference were timed against it.
  `authoring/widen-pin-bind/variants/undo-log` (0.23 s),
  `authoring/widen-pin-bind/variants/front-set` (0.46 s) and `tests/seal/model.py` all finish
  the 358-program set, against 0.43 s for the reference: 130 to 260 times headroom.
  `authoring/widen-pin-bind/slow/walk.py`, exactly correct with no memo, takes 330 s on one
  `deep` program alone.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, put mechanically to every printed token.
  It found four decisions
  the first draft left open, each now settled by a sentence: whether a name standing on its own
  is a value ("every expression is a call, and every call has at least one argument, so a name
  standing on its own is a value"); what a call asked for nothing pays for its result ("which is
  nothing when the call was asked for nothing"); whether a nested call that comes back ambiguous
  differs from one with no binding ("so does a call in a slot that comes back ambiguous or with
  no binding"); and whether an open entry with no open slot can be settled from its bound ("an
  open entry with no open slot is never taken").

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/res/kind.py`, `/app/res/pick.py`, `/app/res/pin.py`,
  `/app/res/cost.py`, `/app/res/best.py`, `/app/res/walk.py`. Nothing else is collected.
- What is checked: the exact lines `/app/run_bind.py` prints for every graded program, over the
  verifier's own pristine copy of the tree with those six files laid over it. 32 enumerated
  programs against `tests/seal/gt.json`, frozen before the grading file was written; 326
  generated inside the verifier from a seed drawn after the agent's container is gone.
- Tolerances: none. Exact line-for-line comparison, all or nothing. The one limit is the 60 s
  wall clock on the half that runs the submission.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  root-owned directory made 0700 before any submitted line runs. The grader asserts the model
  still reproduces the frozen answers before it grades anything.

## Decisions and their reasons

- The graded quantity is a trace rather than a single answer, so a wrong reading fails on the
  line it owns rather than on a summary number.
- The tally exists so the costs are graded directly: two cost rules can produce the same winners
  and different numbers, and `path-tally` is exactly that program.
- The deep family uses plain entries only, so the pins do not change during the exploration and
  the memo is fully effective; the pin-and-memo interaction is exercised by `stale`, `pins` and
  the `memo-pins` case instead. Shaping it the other way would have made the gate unreachable
  for a correct binder.
- `fail-prints` was dropped rather than shipped: the frozen trace writer decides it, so the
  cheat would have scored 1 for an honest reason.
- Docker and harbor are not available in this container, so the two-image gates were run through
  `authoring/widen-pin-bind/host_trial.py`, which reproduces the platform's staging and the
  verifier's isolation on this host. This is host emulation, not container evidence.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no Docker here; `tools/imagecheck.py` assembles what the image would hold and runs the shipped programs in it: clean |
| No answer leaked into agent image | pass | `authoring/widen-pin-bind/leakscan.py`: 0 findings |
| `harbor run -a oracle` = 1 | emulated | host_trial oracle: reward 1, 35 tests passed |
| `harbor run -a nop` = 0 | emulated | host_trial nop: reward 0, 21 of 35 tests failed |
| Cheats all score 0 | pass | 41 cheats through host_trial, each with the layer that caught it asserted (`cheat_report.py`) |
| Correct variants score 1 | pass | `variants/undo-log` and `variants/front-set`, both reward 1 |
| Wrong readings separated | pass | `tools/readingcheck.py`: 24 of 24 by an enumerated case |
| Answer shape not a one-liner | pass | `tools/onelinecheck.py`: no graded decision has a rule at depth <= 2 |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | no errors, 14 warnings, all of the "public function nothing calls" kind that every retained bundle also carries |
| `difficultycheck.py` at Stage 7 | pass | 100/100 on the measured tree, no drift |
| `harbor check` rubric | not run | no API key in this container |

## Open questions and next steps

None outstanding. The remaining risk is that this was validated by host emulation rather than
by the real two-container trial, which is recorded above rather than papered over.
