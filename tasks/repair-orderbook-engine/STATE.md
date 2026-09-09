# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one — anything not written here is lost.

## Current stage

`Stage 7 — Pre-flight and packaging`, under the RAISE-DIFFICULTY.md recovery procedure. The
recovery exit gate is not passed: it needs an external easiness probe on the rebuilt bundle.

## Assistant's assigned role

Senior matching-engine engineer for an exchange simulator: years of order-book repair work,
price-time priority, hidden quantity, stop activation and all-or-nothing admission, with the
run-audit and easiness-probe trajectories of this task as the supplied evidence.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, authored engine under `environment/app_src/`.

## Task summary

A compact Python matching engine (`mkt/` frozen driver, book, reader and emitter; `eng/` five
editable decision modules, four shipping wrong). A session is a text file of `new`/`pull`
messages under a `cap` band, a `mark` price and a `pace` selector. The agent repairs shown-slice
disclosure, the moving band, same-participant cancellation, all-or-nothing (`whole`) admission
with nested restoration, and parked-order firing under order pace and fill pace, so that every
event row and the final book match a sealed model on named, nonce-generated and large sessions
inside a 300-second worker limit.

## Why it is hard

The first coherent plan - journal or snapshot everything a `whole` touches, buffer its output,
restore all of it on failure, count admission under order pace where the shipped `room()`
suggests it - is right about everything except one stated rule: a firing is never taken back.
A `whole` that comes up short after a fill that fired a parked order restores the book, the
last price, quantities, disclosure state and the waiting queue, but not the parked set. What it
fired is announced after its cancellation line and run again, in arrival order, from full size,
at any nesting depth, and once more after each enclosing failure.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan: the environment and the model's prior both
  say "count, then walk" for order pace and "transaction" for fill pace, and both are wrong in
  the same invisible place. A counted admission fires nothing on a walk that would have failed.
  A transaction that restores the parked set fires and then takes it back. Both agree with the
  rules on every session where nothing parked sits in the failed walk's path, so ordinary
  testing and a self-written reference built on the same reading confirm them.
- Tactics making that true (docs/DIFFICULTY.md): A1 - the convention (AON rejects without side effects; rollback
  restores everything) is inverted for firings, and the shipped `room()` nudges toward the
  counted plan; B2 - the firing rule interacts with nesting (an inner whole's firings belong to
  every enclosing frame, on success and on failure), with the two paces (queue end versus
  before waiting siblings), with arrival order across fills, and with restoration of quantities
  (run again from full size); C1 - fenced from both sides by failed orders that made no fill,
  where the counted plan's output is exactly right; C2 - a self-built reference encodes the
  solver's own reading, so fuzzing cannot find a wrong one; C4 - 67 named cases, 300 small
  sessions in six shaped families including `spark` (order-pace wholes that fail after fills
  that fired, on a swept side kept supplied), 120 fill-pace sessions, five large sessions,
  all-or-nothing.
- Assistant's attack on the plan: first plan as a solver - journal undo, buffered replay, heaps
  for the parked set, precheck under order pace because the shipped module does it. Wrong on
  the firing rule in order pace (fires nothing), and after reading the rule, the natural
  per-frame fired list still loses firings inside a nested child that committed, and runs an
  order once when an enclosing failure needs it run again. Where I would have gone wrong: the
  merge-on-success, and keeping the precheck "because it is equivalent when nothing fires"
  without proving the equivalence holds only at zero.
- Estimated solves out of 8: 3 [design aim 1-2, before external evidence]
- Difficulty score anchor: not assigned (pre-recovery bundle passed easiness only through an
  undocumented sink rule; see the recovery entry)
- Score history: 2026-09-09 quality review failed `task name` only (renamed from
  `slice-trip-fill`); run audit failed `task specification` 5/8 and `difficulty crux` 5/8
  (sink rule undocumented); easiness probe 3/3 after the sink repair; recovery below.
- Leak audit: the shipped `hold.py` counts then walks and never restores - it nudges toward
  the wrong plan and decides nothing. `/app/sess/fill.txt` holds one successful whole; no
  shipped session has a failed whole that fired, so `run_book.py` output is never an oracle
  for the rule. `run_book.py` prints what the engine does, never an expected stream. No
  helper, field or comment names the firing rule; `Ord` has no arrival field, the parked
  sequence is the agent's to keep. `cheat/`, `tests/` and `solution/` are not in the agent
  image. Answer: nothing.
- Expert path: read the driver and book; trace `s1` and `s2` to the four wrong modules;
  rewrite disclosure, band and arrival-ordered firing; write admission as a real walk inside a
  frame in both paces, because the brief says a whole finds out by walking; keep the parked
  set out of the frame and record firings into every open frame; on failure restore, print
  `pul`, announce the frame's firings in arrival order and submit them again (queue under order
  pace, at once under fill pace); confirm on the nested and arrival-order hand traces; measure
  the large sessions and index the parked set.
- Originality check: stop-trigger irrevocability under an all-or-nothing rollback is a
  simulator policy of this task, not a documented venue rule; searched for the combination of
  iceberg disclosure priority, moving band, self-trade cancellation, nested AON rollback and
  committed triggers - no write-up.

## Verifier contract — FROZEN after Stage 2 (revised 2026-09-09 under the recovery, contributor's request)

- Artifacts the agent produces: `/app/eng/take.py`, `/app/eng/shown.py`, `/app/eng/hand.py`,
  `/app/eng/hold.py`, `/app/eng/trip.py`; every other file byte-compared to the pristine tree.
- What is checked: the exact ordered event stream and final book of every session in the
  plan - 67 named (`tests/cases.py`), 300 small in six families, 120 fill-pace, four large and
  one large fill-pace, all from a nonce made after the run - against `tests/oracle.py`; the
  named set also against `tests/gt.json`; live fingerprints of sealed functions; the sink
  frame check; the monitoring tally; worker and reaper exit statuses.
- The rule that changed: a `whole` that comes up short restores the book, last price,
  quantities, shown amounts, queue positions and waiting work, discards every printed line of
  its execution, prints `pul <id> whole`, then a `trp` line for every order fired inside that
  execution at any depth, in arrival order, and those orders execute again from full size -
  onto the end of the waiting queue under order pace, at once and before anything waiting on
  the failed order under fill pace. A fired whole that fails stays fired; an enclosing failure
  discards its cancellation line and runs it again with everything else fired inside it.
- Tolerances: none. All-or-nothing on every row.
- Ground truth: `tests/gt.json` (named cases, built by `authoring/repair-orderbook-engine/build_gt.py`,
  reference and model must agree before it is written); everything else computed by the
  sealed model after the run.

## Decisions and their reasons

- Firings are irrevocable, rather than any other committed class: it is one principle with
  consequences across nesting, both paces and ordering, and it turns the environment's own
  nudge (the counted admission) into the wrong plan without adding a corner case. Same-hand
  pulls as a second committed class were considered and rejected as a second journal class
  needing its own reprint rules - sprawl, not interaction.
- The reference keeps `room()` and calls it only as the zero test: a walk that would fill
  nothing fires nothing and restores nothing, so refusing it without walking is exactly
  equivalent, and `agree.py` confirms that over thousands of sessions against a model that
  never counts. Any other use of the count is the wrong plan.
- Arrival order for the post-cancellation batch, not firing order: "like any batch", the
  existing rule, stated in the brief. Firing order would make an unrestored waiting queue
  accidentally right under order pace.
- The output-channel contract (`out.row`, never `out.sink`) stays in the brief and in
  `run_book.py`: the run audit failed 5/8 on exactly that undocumented rule.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run (no Docker) | `tools/imagecheck.py` interprets the Dockerfile and runs the shipped programs |
| No answer leaked into agent image | pass | leak audit above; `extraneouscheck`, `hintcheck` clean |
| `harbor run -a oracle` = 1 | host emulation 1 | `authoring/repair-orderbook-engine/trial.py oracle`, 22.8 s of 300 |
| `harbor run -a nop` = 0 | host emulation 0 | |
| Cheats all score 0 | host emulation | 44 cheats, two sweeps; the three isolation probes needing a second uid or fork are reported not covered |
| Alternative correct variant = 1 | host emulation 1 | `variants/journal`: per-mutation journal, bisected parked lists, frames merge on close |
| `preflight.py` | run at Stage 7 | STATE.md now present |
| `harbor check` rubric | not run | manual self-review against docs/QUALITY-REVIEW.md |

## Easiness recovery 2026-09-09

### 1. Capture

- Probe result: 3 of 3 solved, after the run-audit repair of the same day. Trajectories:
  `probes/repair-orderbook-engine/trial-1.md`, `trial-2.md`, `trial-3.md`; commentary in
  `probes/repair-orderbook-engine/notes.md`. Run-audit summaries (8 trials, 3 reward 1, 5
  reward 0 on `RuntimeError('sink')` with correct semantics) are quoted in the contributor's
  message and summarised in notes.md.
- First plan, decisive discovery, final method - identical across the three: read the 132-line
  `eng/` tree in one call, list every defect by name, write all five files once (journal or
  snapshot undo, private row buffer replayed through `out.row`, heap-indexed parked set,
  fill-pace batches run inline through the driver's `submit`, precheck kept under order pace),
  build a deep-copy reference or an invariant check, fuzz, time, finish in 7-15 tool calls.
- Earliest point with enough information to commit: after the first `cat` of the tree. The
  brief's restoration list is a snapshot checklist, and no rule interacts with the default.
- Source of the plan: the instruction (every rule in one sentence, none contradicting the
  default) plus the shipped `room()` for the order-pace precheck. Not the examples, not the
  internet, not a verifier loophole.
- Existing tactics: A2 (nothing named), B2 (many rules), C4 (exact, nonce-generated). The
  tactic that failed: B2 without interaction - each rule was independently readable and
  independently checkable, "six easy tasks in a trenchcoat".
- Estimated solves before repair: 8 of 8 (the earlier easiness pass was the sink rule failing
  correct agents, which the run audit then rejected as a specification gap).

### 2. Classification

- The default plan was correct: every agent named journal/snapshot undo, buffered replay and
  an indexed parked set immediately (trial-1 lines 610-612, trial-2 line 219, trial-3 line 150).
- The instruction delivered the plan: the restoration list, and "parked orders" in it.
- The agent confirmed each step independently: a self-written reference from the same
  reading; trial-1's fuzzer found only implementation slips (dead-level barriers, a missing
  journal merge, trial-1 lines 1010-1130 and 1536).
- The naive method was fast enough: measured, and not repaired by scale - see candidate C below.

### 3. Candidates

- A (selected) - firings are irrevocable. Poisons the counted admission the environment
  suggests (fires nothing) and the transaction plan (re-parks); the committed set spans depth
  and survives inner success and inner failure; arrival order across fills; queue end versus
  before waiting siblings; run again from full size. Ordinary sessions unchanged. Expert path
  is one frame discipline. Attack: a careful reader implements it; the risk points are keeping
  the precheck as "equivalent", the merge-on-success, running once under nested failure, and
  fill-pace placement. Each is a named hand case and a measured reading.
- B (rejected) - same-participant pulls also committed. A second journal class with its own
  reprint-order rules; no new interaction, more prose. The reach-pair-sweep review warned
  against exactly this sprawl.
- C (rejected, measured) - a scale boundary making per-admission book copies infeasible. The
  reference's shallow queue copies cost about 0.2 ms per admission at the graded 9,200-order,
  1,700-episode scale; a boundary would need populations two orders of magnitude larger, and
  trial-1 already profiled and re-indexed the parked set in one step (16 s to 0.7 s). Journaling
  is a step, not a discovery.

### 4. Rebuild

- Stage 2: `tests/oracle.py` - order-pace trail keeps each fill's firings as an entry the
  rewind reads but does not reverse; fill-pace side keeps `flog`, a firing log no checkpoint
  truncates; failure prints `pul`, then `trp` in arrival order, then re-submits.
- Stage 3: environment unchanged except the earlier `run_book.py` sink check; the shipped
  `hold.py` (count, walk, cancel the remainder, restore nothing) still decides nothing.
- Stage 4: `solution/hold.py` - frames in both paces, `room()` only as the zero test, firings
  recorded into every open frame, restore then announce then re-run; `solution/trip.py` reports
  each firing with its arrival sequence.
- Stage 5: `instruction.md` whole paragraph rewritten; `task.toml` explanations re-derived.
- Stage 6: the previous reference is `cheat-whole-takes-back-firings`; ten reading cheats
  generated from the new reference by `authoring/repair-orderbook-engine/cheats.py`, each one
  exact replacement; `readings.py` measures each and asserts its named hand case catches it.
  Twelve new hand cases (`tests/cases.py`, section "what a failed whole fired"); four existing
  fill cases renamed because their names asserted the old restoration. `spark` was first
  written inside `one()` and starved itself - its same-side day orders rested on the swept
  side and the wholes found nothing to fill (9/50 sessions moved); `spark_one` keeps the
  walked side supplied (20/50).
- Stage 7: below.

### 5. Measurements (host emulation, `RUN_SMALL=300 RUN_DEEP=4`, nonce `readings`, final generator)

Sessions each reading gets wrong, out of 300 order-pace small (six families of 50), 120
fill-pace small, five large, and 67 hand cases. Reward is 0 for every row; the last column
is the hand case `readings.py` asserts catches it.

| reading | order-pace small | fill-pace small | large | hand | named by |
|---|---|---|---|---|---|
| whole-prechecks (count under order pace) | 26 (spark 20) | 0 | 0 | 3 | whole-keeps-what-it-fired |
| whole-takes-back-firings (previous reference) | 26 | 65 | 1 | 19 | whole-keeps-what-it-fired |
| fired-reparked | 26 | 65 | 1 | 19 | whole-keeps-what-it-fired |
| fired-vanish | 26 | 65 | 1 | 19 | whole-keeps-what-it-fired |
| trp-left-inside | 26 | 65 | 1 | 19 | whole-keeps-what-it-fired |
| fired-before-cancel | 26 | 65 | 1 | 19 | whole-keeps-what-it-fired |
| fired-in-firing-order | 1 | 18 | 0 | 1 | whole-fired-batch-is-arrival-order |
| fired-inner-frame-lost | 0 | 11 | 0 | 2 | fill-successful-child-firings-run-again |
| fired-once | 0 | 4 | 0 | 1 | fill-nested-failure-fires-again |
| fired-after-siblings | 0 | 13 | 0 | 2 | fill-fired-batch-precedes-waiting-siblings |
| fired-keeps-fills | 0 | 40 | 1 | 10 | fill-refired-order-starts-over |
| fired-run-at-once-in-order-pace | 0 | 0 | 0 | 1 | whole-fired-waits-its-turn |
| fired-announced-one-at-a-time | 0 | 53 | 0 | 4 | fill-refired-order-fires-more |

Two readings are quiet in the generated population and live on their hand cases: running the
batch at once under order pace differs only when the failed whole was itself waiting with
others behind it, and firing order differs from arrival order only when a failed walk crosses
two trips at different fills in reversed arrival. Both are in the verifier as named cases; a
quiet reading still scores 0. The 31 earlier cheats (disclosure, band, same hand, the old
admission readings, fill-boundary ordering, forgery and isolation probes) all still score 0.

Reference 1 (20.8-22.8 s of 300), nop 0, journal variant 1 (19.0 s). Model and reference agree
on 2,769 + 1,270 + 1,207 generated sessions across the generator's three versions; the journal
variant agrees on 1,419 + 970.

### 6. Exit gate

Not passed. Needs the external easiness probe on the rebuilt archive. Local gates and the
cold self-attack are recorded above; the honest estimate is 3 of 8. If the probe returns
8 of 8 again, the next diagnosis starts from the trajectories, not from another rule: the
suspects, in order, are the brief's whole paragraph handing over the frame discipline, and
the hand-case names in `cases.py` (not shipped to the agent, but read by reviewers).
