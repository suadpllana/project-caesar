# Task state

Working memory for `lane-yield-drift`. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - packaged` (every local and container gate below has been run; the external probes have not)

## Assistant's assigned role

You are the engineer who owns the periodic-job runner of a data platform: the component that
decides which recurring job starts on the single serial worker, when, in site-local time, under
per-site run caps and maintenance windows. You have carried the pager for the two nights a year
when the clocks move and the runner either skips a job or runs it twice.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The first prompt named no repository.
- Task shape chosen: not applicable (no vendored repository, so neither authored-on-top nor
  ablation per `docs/ABLATION.md`). The environment is authored from scratch.
- Contributor's relationship to it: not applicable
- License: not applicable
- Pinned commit: not applicable
- Load-bearing couplings: authored, listed under "Prong B" below
- Identifier degradation done? The tree uses short legacy-register names (`zt`, `due`, `gate`,
  `lane`, `tod`, `off`) chosen for this task; there is no upstream project and therefore no
  conversion table. No proper nouns, no product names, no real zone names.
- Upstream-diff check: not applicable - nothing to diff against.

## Task summary

The agent is given a job runner. A plan file declares zones (a base offset and a list of
offset shifts), pools (a zone and a daily cap on started runs), and jobs (a zone, a distinct
priority, a pool, a duration, a local start/stop window, a cadence mode, a cadence step and an
anchor). One worker - the lane - runs one job at a time and never interrupts a started run.
The runner prints an exact event trace: `skip`, `drop`, `start` and `end`, with the job, the
occurrence index and the absolute minute. The shipped runner works and is wrong in nine graded
places spread over four files. The agent repairs those four files; the verifier runs the repaired
runner on plans it has never seen and compares every line.

## Why it is hard

The obvious decomposition - expand each job's occurrences, convert them to instants, merge, then
walk the merged list - cannot be written at all, because one of the two cadence modes takes its
next occurrence from the instant its previous occurrence was actually attempted, and that instant
is decided by the lane. Expansion and arbitration are the same loop. On top of that the lane's
choice can change at four kinds of instant, only two of which the shipped loop visits, and the
graded quantities are settled by the interaction of rules that live in four different modules.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): its first plan
  is a per-job expansion phase followed by a merge and a forward sweep, which is the shape every
  cron-like scheduler in its training data has. That phase cannot exist here: follow-mode
  occurrences are defined from the attempt instant of the previous occurrence, which the lane
  decides, so the calendar and the arbitration are mutually dependent and have to be solved in one
  interleaved pass. It cannot find that out from the brief alone either, because what breaks is
  the structure, not a rule: every individual rule is stated and each looks independently
  implementable.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C4. A1 (the prior for recurring work is absolute
  interval arithmetic plus a library's default handling of impossible and repeated local times;
  the spec inverts the repeated-time default, pins the impossible-time default, and re-anchors a
  missed run from the attempt rather than the nominal), A2 (the brief describes the lane, the
  attempt anchor and the cap ledger as behaviour and never uses the words misfire, fold or
  arbitration, so no search term names the combination), B2 (twelve graded rules across the zone
  table, both cadence modes, the window, overlap suppression, the cap ledger and the lane hold at
  once, and the only observable is one exact trace), C1 (plans with no contention and no shift
  must still produce every ordinary run, so an overconservative planner that defers or drops
  whenever a window is tight fails the everyday side), C2 (the shipped runner prints the broken
  planner's own answer and the zone table is invented, so nothing the agent can run tells it
  whether a reading is right), C4 (exact all-or-nothing grading over enumerated plans aimed at
  each rule plus nonce-generated families shaped at the shifts and at lane contention).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  to expand every job's recurrences over the horizon, resolve each local time through the zone
  table, discard the ones whose window does not admit them, merge everything into one list ordered
  by instant, and sweep forward with a cursor at the end of the last run, pushing each overlapping
  run to the cursor. That plan is wrong twice. It starts the wrong job whenever two occurrences are
  waiting together, because the lane re-chooses by priority when it frees rather than honouring
  nominal order; and its expansion phase cannot be written for follow-mode jobs at all, because
  their later occurrences are defined from the attempt instant of the earlier ones. I would find
  the first from the brief and the second only after the first implementation was already built
  around a phase that has to be deleted.
- Estimated solves out of 8: 2 (designed for the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py, before Stage 2): 98/100 on the first attempt,
  2026-09-16, `authoring/lane-yield-drift/difficulty.toml`. In band (95 to 100). The two points
  not scored are the resource-gate axis, recorded as `present = false` with the reason: every
  correct planner walks the same decision instants once, so no naive-but-correct family exists for
  a limit to kill, and a limit would tax the expert path equally.
- Difficulty score anchor: not yet submitted; no contributor-approved anchor.
- Score history: 2026-09-16, 98, first complete record.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning?
  - The cadence rules: the shipped `due` module implements the wrong time base for both modes, so
    reading it hands over a plausible answer, not the answer. No file stores a next-run instant.
  - The zone resolution: the shift table stores only transition instants and offsets. The two
    shipped plans carry shifts, but no expected output ships anywhere, and no real zone name
    appears, so the rules cannot be looked up.
  - The attempt anchor: nothing in a plan file records when a job last ran. The plan files carry
    anchors, cadence steps, windows, durations, priorities, pools and caps, and nothing else.
  - The cap ledger: the pool's zone is a field on the pool, and the job's zone is a field on the
    job. The fact that the two can differ is visible; which one the ledger uses is not stored
    anywhere, and the shipped ledger uses the wrong one.
  - The graded plans: generated in the verifier from a per-run nonce after the agent has finished,
    so no shipped input is a graded input.
  - Answer: nothing. Re-run after every environment change.
- Expert path, described step by step:
  1. Run the shipped runner on both plans and read the trace format and the module boundaries.
  2. Read `zt` and find where an instant is chosen for a local time the shift table makes
     impossible or repeated, and compare both choices against the brief.
  3. Read `due` and separate the two cadence modes by their time base - wall-clock minutes for one,
     elapsed minutes from the attempt for the other.
  4. Establish that follow-mode occurrences cannot be enumerated before the lane has placed the
     earlier ones, and restructure the planner so each job is advanced lazily from its own placed
     history instead of expanded up front.
  5. Enumerate every instant at which the lane's choice can change - an arrival, an end, a window
     opening, a pool-day boundary - and drive the loop from that set rather than from arrivals and
     ends alone.
  6. Settle the three outcomes an occurrence can have and which of them move the attempt anchor.
  7. Key the pool ledger by the pool's local day rather than the job's, and charge it at the start.
  8. Re-run both shipped plans and check the ordinary runs are unchanged before trusting the
     contended ones.
- Originality check: searched 2026-09-16. The pieces are each documented - the time zone
  database's notes on gaps and repeated local times, job-scheduler documentation for missed-run
  policies, and the queueing literature on non-preemptive priority service. Nothing found describes
  this combination, and the closest single page found ("Calendar Recurrence for Persistent Agents:
  DST, Missed Runs, and Occurrence Identity", zylos.ai, 2026-09-13) could not be read because the
  domain is blocked by this sandbox's egress policy; from its title and the search snippet it
  covers recurrence semantics only - no lane, no priority arbitration, no pool cap - and it states
  the two conventions this spec deliberately departs from (repeated local time resolved to the
  earlier instant; missed runs either all fired or all dropped). A second search for a published
  exercise or benchmark of this shape returned nothing related. The task's difficulty does not rest
  on recurrence trivia: the recurrence conventions are stated outright in the brief, and the lane
  feedback is what carries it.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/lane-yield-drift/trace.md and its tracecheck result): clean, 64 rows walked - 7 test functions, 21 enumerated cases, 4 collected artifacts, the
  graded run's 600 s clock and 31 rows for the branches of the sealed model that can move a
  printed token, each split to one row per rule with its line range. No row was left NOT STATED;
  two decisions were unstated on the first pass and both were written into the instruction rather
  than dropped from grading (see the cold-reader row below). `python tools/tracecheck.py
  lane-yield-drift` is clean.
- Identifiability (readings enumerated, which survived, what separated them): 17 readings, none survived from the four clusters, from the model's prior for recurring
  work, and from what the shipped planner itself does. Each is a whole planner in
  `authoring/lane-yield-drift/readings.py`, and none survives the published evidence: every one
  is ruled out by a quoted sentence in the trace's Readings table and separated by a named
  enumerated case, confirmed by `casecheck.py` (17 of 17 caught by their named case). Measured on
  240 generated plans they move between 1.2 per cent (lane-top-only) and 68.8 per cent
  (dead-inclusive) of the population; none moves nothing. Two earlier readings were replaced
  because they were degenerate rather than plausible: a window test inclusive at the closing
  minute made the shipped boundary walk loop forever, and settling deadlines before arrivals
  stranded every occurrence due outside its window.
- Shortcut strategies scored (nop, constant, positional, replayed example): all six scored 0 in the container and are in the trace's Shortcuts table - the
  shipped tree (11 of 27 tests fail), an empty trace, every occurrence dropped on its nominal,
  only the first job, every occurrence started on its nominal, and the printout in the brief
  replayed. None matches a single plan of the 321, because the brief prints the shipped planner's
  wrong trace rather than a correct one, so there is no correct output anywhere to replay.
- Independent implementation behind every tolerance and limit: tests/seal/model.py and two variants, measured below. The only
  limit is the 600 s clock `tests/test.sh` puts on the graded run. Validated against
  `tests/seal/model.py` (written apart from the reference) and both correct variants under
  `authoring/lane-yield-drift/variants/`: on the full 321-plan population of 16030 events the
  sealed model takes 0.09 s inside the verifier image, the reference 0.08 s, ok-heap 0.09 s and
  ok-tick 0.10 s. Nothing else is a tolerance - every graded quantity is an integer compared
  exactly.
- Undecided decisions from the cold-reader pass: two, both given a sentence rather than dropped from grading. Author-run, the mechanical form - every graded token listed, then every model
  branch that touches it, then the four clusters put to each as questions. Two decisions could
  only be answered by reading the model and both got a sentence: whether a run may start on the
  minute its window closes (now "up to but not including the first instant after that which its
  job does not admit"), and what the occurrence number counts (now "counting the ones that are
  skipped and the ones that are dropped"). A third, whether the occurrence number is 0-based, was
  a convention with no difficulty in it and is given outright. The stronger form - a fresh session
  shown only the instruction and the agent tree - was not run, and is recorded as not run rather
  than claimed.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-16. Changing any of it changes what "correct" means and needs explicit approval.

### Artifacts the agent produces

Exactly four files, collected at their original absolute paths and nothing else:

    /app/sked/zt.py
    /app/sked/due.py
    /app/sked/gate.py
    /app/sked/lane.py

Everything else in `/app` is restored from a pristine copy before the graded run, so a change
anywhere else has no effect.

### The model, in full

All times are integer minutes. Absolute time is minutes from the plan's epoch; local time is
absolute plus the zone's offset at that absolute minute.

1. **Offsets.** A zone has a base offset and a list of shifts `(at, new_offset)` with strictly
   increasing `at`. `off(z, t)` is the offset of the last shift with `at <= t`, else the base.
   `loc(z, t) = t + off(z, t)`.
2. **Resolving a local minute.** For a local minute `L` in zone `z`, let
   `C = { t : loc(z, t) == L }`. If `C` is non-empty the instant is `max(C)`. If `C` is empty the
   instant is the smallest `t` with `loc(z, t) > L`.
3. **Clock cadence.** Occurrence `k` of a clock-mode job has nominal local minute
   `anchor + k * step`, resolved by rule 2 in the job's zone.
4. **Follow cadence.** Occurrence 0 of a follow-mode job has nominal local minute `anchor`,
   resolved by rule 2. Occurrence `k+1` has nominal instant `attempt(k) + step`, in absolute
   minutes, with no local-time resolution.
5. **Attempt.** `attempt(k)` is the start instant if occurrence `k` started, and the drop instant
   if it was dropped. A skipped occurrence has no attempt and cannot occur in follow mode.
6. **Window.** `tod(z, t) = loc(z, t) mod 1440`. A job admits instant `t` when
   `open <= tod(job.zone, t) < close`. Inputs satisfy `0 <= open < close <= 1440` and
   `close - open <= 1320`.
7. **Admission window and deadline.** For an occurrence with nominal instant `n`, `a` is the
   smallest `t >= n` the job admits and `d` is the smallest `t > a` the job does not admit. The
   occurrence may start only in `[a, d)`. If it has not started by `d` it is dropped at `d`.
8. **Overlap.** When an occurrence's nominal instant arrives while the same job has an occurrence
   that has neither ended, dropped nor been skipped, the arriving occurrence is skipped at that
   instant. Follow-mode inputs satisfy `step > duration`, so follow-mode occurrences never skip.
9. **Lane.** One run at a time; a started run holds the lane for `duration` minutes and is never
   interrupted.
10. **Arbitration.** At an instant when the lane is free, among the occurrences that have arrived,
    are not yet started, dropped or skipped, are admitted at that instant, and whose pool has cap
    left for that instant's pool day, the one whose job has the smallest priority number starts.
    Priorities are distinct across jobs. If none qualifies the lane stays free.
11. **Pool cap.** A pool's day at instant `t` is `floor(loc(pool.zone, t) / 1440)`. Each pool
    starts at most `cap` runs per pool day. The charge is made at the start instant.
12. **Order within one instant.** Ends complete, then arrivals are recorded or skipped, then
    deadlines drop, then the lane starts at most one run. Durations are at least 1 minute, so at
    most one start happens per instant.
13. **Occurrence index.** `k` counts every occurrence of a job in order from 0, including skipped
    and dropped ones.
14. **Horizon.** A plan declares `horizon H`. Every event with instant `< H` is emitted and no
    event with instant `>= H` is. A run that starts before `H` and would end at or after `H`
    prints its `start` and no `end`.

### What is checked

The exact printed trace, line for line, for every plan in the graded set. One line per event:

    <kind> <job> <k> <t>

with `kind` in `skip`, `drop`, `start`, `end`. Lines are ordered by `t` ascending, then by kind in
the order `end`, `skip`, `drop`, `start`, then by ascending job priority. All-or-nothing: one wrong
line anywhere scores 0.

The graded set is enumerated plans with hand-derived answers, frozen in `tests/gt.json`, plus
plans generated in the verifier from a per-run nonce, answered by the sealed model.

### Tolerances

None. Every quantity is an integer and every comparison is exact.

### Ground truth, and where it lives

`tests/seal/model.py`, an implementation written independently of `solution/`, and
`tests/gt.json`, the frozen answers for the enumerated plans. Both are root-only inside the
verifier image; `tests/seal/` is mode 700 so the unprivileged worker cannot read it.

### Prong C tactics this contract uses, and the route-around guard

- C1: the enumerated set contains contention-free, shift-free plans whose ordinary runs must all
  appear, so a planner that defers or drops defensively fails.
- C2: no expected output ships; the shipped runner prints the broken planner's answer; the zone
  table is invented so no library reproduces it; graded plans are generated after the run.
- C4: exact all-or-nothing over enumerated corners plus nonce-generated families shaped around
  shifts, contention, cap exhaustion and window closes.
- Route-around: `artifacts` declares exactly the four planner modules. The parser, the record
  types, the trace writer and the entry point are restored from a pristine copy and their function
  bodies are hashed in the verifier, so the task cannot be reshaped into "write my own runner".

## Decisions and their reasons

- Minutes-from-epoch rather than civil dates: the whole model stays integer arithmetic, the
  verifier needs no calendar library, and the zone table can be invented rather than borrowed, so
  no public data reproduces it.
- Category `Software`, subcategory `Algorithms`: the graded work is integer time arithmetic,
  ordering and a constrained simulation. The job-runner setting is narrative. `Systems` is retired
  for new tasks and would have been the other candidate.
- Two cadence modes rather than one: the contrast between wall-clock and elapsed-time advancement
  is what makes the prior a liability, and follow mode is what makes the expansion phase
  impossible.
- The pool cap is keyed to the pool's zone, not the job's: it gives a stated rule whose consequence
  (a per-job calendar date cannot be used) is invisible until a pool spans two zones.

## Validation status

Container results are from `python tools/docker_trial.py`, which builds both images and runs the
two-container trial the platform runs; `harbor` is not installed in this checkout.

| Check | Status | Notes |
|---|---|---|
| Difficulty record in band | pass | 98/100 before any code, 2026-09-16 |
| Difficulty record, re-measured at Stage 7 | pass | 98/100 on the built tree: 378 environment py lines, 4 editable files, 266 reference lines, 32 cheats, 2 variants; no drift reported |
| Agent image builds | pass | container |
| No answer leaked into agent image | pass | `imagecheck` assembles what the image would hold (12 files), drops the reference in and runs both shipped plans; `extraneouscheck` clean; no expected output ships |
| oracle = 1 | pass | container, 27 tests passed |
| nop = 0 | pass | container, 11 of 27 fail |
| Correct variants = 1 | pass | container, ok-heap and ok-tick both 1 |
| Cheats all score 0 | pass | container, 32 of 32, and `cheat_report.py` names the test that caught each |
| Isolation facts | pass | worker runs as uid 1004; reward.txt, gt.json, tests/seal/model.py, the grader and the worker's report are all PermissionError for read and for write |
| `forgecheck` | pass | `cheat-probe-answer-key.sh` carries the frozen answers verbatim, reproduces all 21 of them, and is caught only by `test_generated_families` |
| `readingcheck` | pass | 17 of 17 readings separated by an enumerated case; none blind, none equivalent |
| `onelinecheck` | pass | no graded quantity has an exact rule at depth <= 2 over the plan's raw fields |
| `deadfieldcheck` | pass | one finding fixed: `adm` was written and never read, so `gate.window` became `gate.dead_at` returning the deadline alone |
| `catcheck` | pass | Software vocabulary present in the environment (29 hits) as well as the prose |
| `hintcheck` / `structcheck` / `solvecheck` / `extraneouscheck` | pass | no findings |
| `simcheck` | judged | conceptually distinct from every retained task; the Dockerfile similarity it reports is the shared minimal shape of a python-slim image and was not manufactured by copying |
| `textcheck` | judged | no finding against `focus-return-point`. Against `note-carry-forward` it reports four: the contraction density is entirely possessives (`site's`, `plan's`) and is not a contraction at all, the narrower vocabulary is the contract's own discipline of one term per concept, and the paragraph-length spread is measured against a brief carrying one very long paragraph |
| `tracecheck.py` | pass | clean, 64 rows |
| `preflight.py` | pass | no errors; 15 warnings, all the cross-module false positive that a retained passing bundle also produces 15 of |
| rubric self-review | pass | walked criterion by criterion; two findings fixed - a stale cheat count in `verification_explanation` and two relative paths in the instruction |
| easiness probe | not run | external |
| cold self-probe | not run | this session wrote the model, so a cold solve here would measure memory rather than difficulty; recorded as not run rather than claimed (CLAUDE.md, 2026-09-06) |

## Stage 7 re-attack

Read cold, the brief is complete, and that is deliberate: a careful reader can derive the shape of
the answer - a forward loop over the instants at which the worker's choice can change, with each
job advanced from its own history. The brief says the worker is never interrupted and says a
follow job takes its next occurrence from the previous attempt, so the expansion phase is
visibly unwritable to anyone who reads both sentences together. What is not one-shot is landing
all twelve graded decisions at once with no signal: the set of decision instants is a consequence
of one sentence rather than a list, the deadline has to walk the shift table rather than be
computed, the cap is keyed to a zone the job does not have, and the three outcomes differ in
which of them moves the attempt anchor. Each is a plausible mistake with a whole planner written
for it under `readings.py`, and all-or-nothing grading turns any one of them into a zero.

Estimated solves, updated: 2 of 8, unchanged. The honest risk is at both ends. Toward easy: a
systematic agent that works the twelve decisions one at a time against the brief can get them
all, and the brief hides none of them. Toward unverifiable: there is no oracle anywhere, so an
agent that is wrong about one boundary never finds out. The load-bearing facts are still
distributed - the shift table, the two cadence modes, the admission walk, the ledger key and the
decision instants live in four modules and none of them can be settled from the brief alone
without reading what the shipped planner already does. The instruction does not telegraph the
method: it states outcomes, and the one worked printout in it is the shipped planner's wrong
answer, not a correct one.

## Open questions and next steps

Nothing is blocked locally. What remains is external: the platform's structural, similarity,
reference-verification, anti-cheat, quality and 8-attempt difficulty gates. If the easiness probe
rejects it, stop packaging and run `RAISE-DIFFICULTY.md` from trajectory capture onward; the
winning method becomes a cheat and the repair is a semantic replan, not more cases.
