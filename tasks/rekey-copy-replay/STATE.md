# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a database platform engineer who has run live table rebuilds in production: chunked
copies of a source table that is still taking writes, a change journal replayed behind the
copy, and the cutover that has to be exact. You have had to do one where the new table was
keyed differently from the old, which the mainstream tools decline to do.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository vendored)

## Task summary

`/app` is the rebuild half of a service that copies a table into a new one while writes keep
arriving at the old one. The new table is keyed by the first two of a row's three fields, the
source by an integer. A program file interleaves source writes with chunks of the copy and
partial replays of the change journal, and `/app/run_reb.py` prints a line for everything that
happens. The shipped engine is coherent and wrong: it chunks by key range, keeps one mark for
the whole rebuild, holds journal entries it should drop, collapses the difference between
holding a key and queueing for one, and counts the closing line over every row it knows. Six
files under `/app/reb/` are the agent's to fix; the rest of the tree is replaced by the
verifier's copy.

## Why it is hard

The first plan applies every entry the copy cursor has already passed and drops the rest. It is
the published shape and it is wrong twice: a chunk read is newer than the entries written
before it, so an entry behind the cursor can still be stale and has to be judged against the
mark of the reach covering its key; and because the new key is read off two fields, an ordinary
field update is a move whose old key is the one the rebuild holds rather than the one the
source now names. The second finding is what forces a rebuild rather than a patch: moves free
keys, freed keys go to the smallest source key set aside for them, and the walk sets rows aside
on the same terms as the replay, so the queue is fed in two orders and drained in a third.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the retrieved shape
  applies every entry behind the cursor and keys the rebuild like the source, and both halves
  are specifically wrong here; the structures the rules seem to ask for (one start position, a
  row map plus a key map, a queue in arrival order, a scan for the next chunk) each survive the
  ordinary programs and fail a constructed one or the stated limit.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C3, C4. A1 the published
  replay rule is the liability. A2 nothing is named: the brief speaks of a walk, a reach, a mark
  and a row set aside. B2 thirteen small rules that change each other's meaning. C1 every entry
  prints why it was dropped, so playing safe fails the ordinary programs. C3 the two large
  families make the obvious structures hundreds of millions of comparisons against a stated
  sixty second limit. C4 exact all-or-nothing comparison over 360 programs, 330 of them
  generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where it is wrong): my first plan was a
  row map plus a new-key map, a single journal pointer, and "apply what is behind the cursor".
  It is wrong on staleness (no mark per reach), on moves (the old key taken from the entry
  rather than from what the rebuild holds), and on the queue tie-break; and its chunk selection
  and mark lookup are both scans, which the measured limit kills.
- Estimated solves out of 8: 3 (2 at design time; re-estimated at Stage 7, see the re-attack below)
- Difficulty record score (tools/difficultycheck.py): attempt 1, a grid recalculation design
  scored 100/100 and was then killed on the search test - two public repositories implement its
  exact contention, blocking and round-cap rules, so `helps_plan` was true, a hard stop. Attempt
  2, this design, scores 100/100 on 2026-09-22 with the resource gate measured.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not
  applicable - no pipeline anchor has been set for this task.
- Score history: 2026-09-22, 100/100, first and only scored version of this design.
- Leak audit (docs/DIFFICULTY.md): the store keeps source rows and journal entries as written
  and nothing else; reaches, marks, new keys, the held map and the queue order are all derived
  and none ships as a field. No shipped helper answers "which rows are waiting on this pair" -
  the shipped queue is one flat list with no index. The shipped engine's own trace is not an
  oracle: it disagrees with the brief on the one line the brief quotes. The brief quotes one
  line of one program rather than a whole trace, and every line format is fixed by the frozen
  `/app/reb/say.py`, so no worked example is needed to pin the format. No artifact that is a
  function of the correct trajectory ships.
- Expert path, described step by step: read `run_reb.py` and the `reb` package; run
  `progs/tiny.txt` and `progs/pair.txt` and find where the shipped engine and the brief part
  company; build the walk (next C present keys above the cursor, cursor on the largest taken,
  reach written down); make the mark per reach and the entry verdict a lookup into that list;
  carry the row as the rebuild holds it so a move knows the pair it is leaving; give each pair
  its own ordered queue fed by both the walk and the replay; time `wide.txt` and `deep.txt`,
  find the chunk scan and the reach scan quadratic, and replace both with the forward walk the
  cursor's monotonicity allows.
- Originality check: searched 2026-09-22. The two mainstream online rebuild tools are well
  documented; one refuses a rebuild whose unique key does not cover the same columns in the
  same order, the other warns it falls back to an unindexed match. Neither states what a replay
  does when a field update moves a row under the new key, which is the whole of this task. The
  first design this session (a grid recalculation engine) was killed at this step because two
  public repositories already implement its exact rules; that is recorded above.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (rows walked, NOT STATED left, tracecheck result): the walk is in
  authoring/rekey-copy-replay/trace.md, built from the tracecheck skeleton - every test function, the 34
  enumerated cases, the six collected artifacts, the 60 second clock, every top-level function
  of the sealed model split into one row per rule it applies, and every wrong reading in
  `authoring/rekey-copy-replay/readings.py`. No NOT STATED rows remain; `python
  tools/tracecheck.py rekey-copy-replay` is clean.
- Identifiability: fourteen readings are enumerated in `readings.py` from the four clusters,
  the model's prior
  and the shipped engine's own behaviour. None survives the published evidence while disagreeing
  with the reference on the graded set; each is separated by a named hand case, measured by
  `tools/readingcheck.py`.
- Shortcut strategies scored: the shipped tree unchanged, a constant closing line, the
  replayed output of the quoted example, always-first and arrival-order positional strategies -
  all score 0, and the fraction of programs each matches is recorded in
  `authoring/rekey-copy-replay/cheat_report.txt`.
- Independent implementation behind every tolerance and limit: the 60 second clock is
  validated against `authoring/rekey-copy-replay/naive/`, a correct
  implementation with the obvious structures, and against the sealed model. Measured on this
  machine: reference 3.4 s for the six large programs, naive 176.3 s for the same six, model
  3.2 s for all 330 generated programs.
- Undecided decisions from the cold-reader pass: author-run, recorded in the trace. Four
  were open on the first draft
  and each got a sentence: whether a reach includes the key the cursor was on, the bounds on
  keys, fields and C, that a `same` applies to a row that is only set aside as well as one
  holding its pair, and that a program is graded exactly as it stands.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/reb/walk.py`, `/app/reb/mark.py`, `/app/reb/sift.py`,
  `/app/reb/place.py`, `/app/reb/wait.py`, `/app/reb/tally.py`. Nothing else is read.
- What is checked: the exact list of printed lines for 30 hand programs against `gt.json` and
  for 330 generated programs against the sealed model, plus the sealed model against `gt.json`,
  plus every family being represented. All or nothing.
- Tolerances: none. Exact string comparison of every line.
- Ground truth, and where it lives: `tests/seal/gt.json` and `tests/seal/model.py`, in a
  root-owned directory made 0700 before any submitted code runs.

## Decisions and their reasons

- The six editable files are wired together by the frozen `run_reb.py`, and `say.py` fixes every
  line format. That is the route-around guard: the program grammar and the printed shape cannot
  be reshaped into something the default plan handles.
- `progs/` is excluded from `tests/pristine/`, because the worker feeds program text directly and
  the two large files would double the verifier image for nothing. `authoring/sync.py --check`
  enforces the rest.
- The first design of this session was killed on the search test before any code existed. Do not
  revive a spreadsheet spill task in this repository; two public implementations state its rules.

## Validation status

harbor is not installed in this environment, so the two-container gates were run with
`tools/docker_trial.py`, which reproduces what the platform does: it builds both images, runs
the agent script in the agent image, pulls the six declared artifacts out, uploads them into
the verifier image at their original absolute paths, runs `tests/test.sh` and reads
`/logs/verifier/reward.txt`. Docker Hub's blob host is blocked by this sandbox's egress policy,
so the `python:3.12-slim` base was pulled from `mirror.gcr.io` and tagged locally; both
Dockerfiles ship verbatim.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `docker_trial.py --build` |
| No answer leaked into agent image | pass | `tools/imagecheck.py`: 25 files, workdir /app, nothing from tests/ or solution/ |
| oracle = 1 (container) | pass | 39 tests passed in 5.9 s |
| nop = 0 (container) | pass | the shipped tree fails every hand program |
| Cheats all score 0 | pass | 36/36 trials behaved as required: oracle, nop and all 34 cheats |
| Correct variants score 1 | pass | `variants/empty-notes` and `variants/bucketed`, 39 tests passed each |
| The resource gate bites end to end | pass | `authoring/rekey-copy-replay/naive/`, identical semantics with the obvious structures, scores 0 in the container: the worker is killed by the 60 s clock and 35 cases error |
| Isolation proved, not assumed | pass | `authoring/rekey-copy-replay/probe_notes.py`: the probe ran as uid 1002 and was denied `/logs/verifier/reward.txt`, `/logs/verifier/per` and `/tests/test_outputs.py`; the answer-key probe was denied `/tests/seal/gt.json` and `/tests/seal/model.py`; the probe that rewrote its own copy of the family size left the authoritative one at 36 |
| `readingcheck.py` | pass | 19 wrong readings, each separated by a named enumerated case |
| `cheat_report.py` | pass | 0 findings: every semantic cheat is caught by the case named for its rule |
| `forgecheck.py` | pass | `cheat-forge-hand.sh` carries every frozen answer and scores 0 |
| `onelinecheck.py` | pass | the entry verdict has no exact rule at depth 2 over exposed fields |
| `tracecheck.py` | pass | clean |
| `difficultycheck.py` | pass | 100/100 on the measured tree, no drift |
| `preflight.py` | pass | no errors; 27 warnings, all the same false positive - its unused-function detector does not count a call made through an instance, and the retained bundles carry 16 to 23 of them |
| `simcheck.py` | pass | conceptual: this task does not grade what any earlier one grades |
| `textcheck.py` / `structcheck.py` | pass | no findings against the retained reference |
| `harbor check` rubric | not run | harbor is not installed and no API key is present |

## Stage 7 re-attack on the finished task

Read cold, with the built tree in front of me, the brief does let a patient reader write a
correct semantic plan in outline. Every rule is stated, because every graded assertion has to
have its sentence. So the honest question is not whether the plan can be formed but whether the
structures it implies survive, and three things still bite.

The shipped tree is wrong in six places and coherently so, which is what a solver who patches
rather than rebuilds inherits: one mark for the whole rebuild, a chunk that is a key range, an
entry above the cursor kept for later, a row set aside treated as one that is holding, a queue
in arrival order, and a closing line over every row known. Four of those produce sensible
looking traces on the programs a solver writes by hand.

The conjunction is thirteen graded rules under all-or-nothing grading, several of which only
part company on a constructed program: a mark that is not the newest, a delete of a row that
was moved since it was copied, a smaller source key set aside after a larger one. Measured on
ninety generated programs, the two thinnest wrong readings still move nine and ten of them, and
one wrong rule anywhere scores 0.

The gate is measured rather than asserted: the same answers take 3.4 seconds one way and 176.3
seconds the other, against a stated 60.

Is the first plan still wrong somewhere that matters? Yes, but less than at design time: the
brief has to state the rules, and a careful reader gets the semantics. The load-bearing
unstated part is which structures carry them, and `tools/onelinecheck.py` confirms the one the
task rests on - the entry verdict - is not reproducible by any rule of two terms over the
fields the tree exposes.

Estimated solves, updated: 3 of 8, against 2 at design time. The design aimed at the hard edge
and the build drifted the usual way: stating every rule for the instruction contract is what
moved it. It stays inside the band and I would not package it if the honest number were 0 or
above 7.

## Residual risk to flag to a reviewer

- The easiness probe has not been run. Nothing local can stand in for it, and the author wrote
  the sealed model before the environment, so no cold self-solve is available either. What
  stands in its place is measured rather than predicted: every wrong reading separated by a
  named case, no shipped oracle, and the resource gate measured at 52x.
- `sheet-block-place` and `move-clash-merge` passed the AI review but their bundles are not in
  this checkout, so this task's originality could not be compared against their mechanisms.
- `tests/test_outputs.py` scores 0.60 to 0.70 on `tools/simcheck.py` against three retained
  bundles. That is the shared pytest and sealed-model scaffolding this repository uses for every
  trace-graded task, not shared subject matter; the conceptual verdict is clean.

## Open questions and next steps

Packaged: `tasks/rekey-copy-replay.zip`, 79 entries, `tools/zipcheck.py` clean, `solve.sh` and
`test.sh` carrying mode 755. Nothing remains before submission except the pipeline's own gates.
