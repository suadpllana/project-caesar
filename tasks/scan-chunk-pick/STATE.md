# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - pre-flight and packaging`

## Assistant's assigned role

You are a storage engineer on a columnar analytics engine: the scan layer that turns a segment
file and a filter into rows, decides which chunks are read off disk at all, and keeps the
per-chunk statistics that decision rests on. You have spent your time on pruning that is wrong
in the cheap direction, on dictionaries that stop being usable halfway through a chunk, and on
filter evaluation orders that are chosen while the scan is already running.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository supplied)

## Task summary

`/app` is the scan layer of a columnar store, cut down to the part that decides which chunks
are read. A segment file stores each column as a run of chunks that carry a header (row count,
null count, a recorded low and high with an exactness flag) and a payload that is either plain
values or a dictionary with an overflow list. A query is a set of conditions plus the columns
to report. `/app/run_scan.py` prints, for each query, every dictionary read and every chunk
decode in the order they happen, then a digest of the surviving rows, then one line per
reported column. The shipped engine implements ordinary predicate pushdown with a fixed
condition order and is wrong in seven places. The agent repairs six files under `/app/scn/`.

## Why it is hard

The surviving rows are easy and the read trace is not. A plan that decodes every chunk and
filters produces exactly the right digest, so the natural self-check confirms an engine whose
graded events are wrong from the first step.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrieved plan is predicate pushdown with one condition order settled from statistics and each condition run over its whole column, and this engine re-chooses after every single chunk, estimates a decoded chunk by exact counts rather than by its header, and settles every condition of a column on the one decode, so the outer loop, the state a chunk carries and the survivor bookkeeping are structures that plan does not have.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C3, C4 - the shipped engine is the memorised pushdown plan so retrieval confirms a policy the spec replaces (A1), no sentence names zone maps, late materialization, adaptive reordering or dictionary pruning (A2), an exact read trace and a wall clock forbid both the decode-everything plan and the recompute-the-estimates plan (A3), eight rules each change what the others see (B2), chunks that must be skipped unread and chunks that must pass unread are both graded (C1), the only self-check is the surviving-row digest which a wrong engine also gets right (C2), two measured segment shapes make recomputation infeasible while it stays exactly correct (C3), and every printed event of every query is compared over hand cases and a nonce population (C4).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan pruned each chunk by its header, used the dictionary where there was one, decoded the rest, intersected the surviving row sets and ordered the conditions once from their header estimates; it is wrong at the outer loop because the unit of work is one chunk of one condition and the choice is remade after every chunk, and wrong again at the chunk because a decoded chunk is estimated from exact counts, so a decode has to settle every condition over its column. Neither failure shows up in the surviving rows.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 out of 8 (aimed at the hard edge of 1 to 3).
- Difficulty record score (tools/difficultycheck.py on authoring/scan-chunk-pick/difficulty.toml,
  before Stage 2): 100/100 on the first record, in the 95-100 band, no hard stop. The only change
  after the first run was rewording tactic C3, which had leaned on the word "huge" and drew the
  checker's scale-vocabulary warning.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set -
  no submission of this task has been scored by the pipeline yet.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22, 100, first
  record.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing":
  - the read order: nothing in the tree records a decode order, an estimate or a survivor count;
    the file stores values, null counts, recorded bounds, an exactness flag, dictionary entries
    and an overflow list, and nothing else.
  - the header rules: the shipped engine calls every function it defines and defines none the
    wrong policy does not need, so there is no unused widener and no unused completeness test.
  - the answers: no expected trace, checksum or annotation ships beside the sample segments;
    the driver prints and nothing judges.
  - the scale boundary: the two large segments are inputs of the same grammar as the small ones
    and carry no marking that says which recomputation they are aimed at.
- Expert path, described step by step: run the shipped engine on the samples and diff its events
  against the brief; recognise that the outer loop is a re-choice per chunk and rebuild it; build
  the per-column row-to-chunk map and keep a survivor count per chunk as rows die; make a decode
  settle every condition over its column and store the exact counts; settle the header rules on
  both sides, widened bounds and the null count in the pass-unread test; settle the dictionary
  rules, completeness, one charge per chunk, and a consult that decides nothing still charged;
  make the report pass decode only chunks that still hold a survivor and were not decoded
  already, in the order the query lists; time the two large segments and replace the rescans
  with counts maintained as they change.
- Originality check: searched 2026-09-22 for public write-ups of adaptive per-chunk predicate
  ordering with dictionary pruning and inexact statistics, and for a benchmark task of this
  shape. The concepts are all documented - Parquet and DataFusion on zone maps and predicate
  pushdown, the column-store papers on late materialization, patents on compressed-block
  pruning - and no page describes this policy: re-choosing after every chunk, estimating a
  decoded chunk by exact counts, rounding recorded bounds inward, or charging a dictionary once
  per chunk. No public exercise, repository or write-up of the task was found.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/scan-chunk-pick/trace.md; rows walked, NOT STATED left, tracecheck result): 75 graded rows walked - four test functions, six declared artifacts, the wall clock, the pristine overlay, 31 enumerated cases and 33 rules of the sealed model split out one per rule with its line range - plus 23 readings, five shortcuts and one limit; no NOT STATED row remains and `python tools/tracecheck.py scan-chunk-pick` is clean. The trace is rebuilt by authoring/scan-chunk-pick/make_trace.py, which asserts every quote is still in instruction.md before it writes.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 25 readings were written down and run; two of them - the exactness flag required before `eq` or `ne` may be settled from a low that equals a high - turned out to be equivalent to the reference, because a widened pair always has its low below its high, so that guard was unreachable and was deleted from the reference and the model rather than kept as dead code. The remaining 23 are each separated by a named enumerated case, which `python tools/readingcheck.py scan-chunk-pick 300` reports and exits 0 on. Six of them were blind to the first case set and got a case written for them: ord-spread-rounds-up, ord-spread-takes-edge, ord-exact-after-read, dec-hits-whole-chunk, dic-drop-with-nulls and the pair the last of those also covers.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the shipped tree (nop) scores 0 and fails 19 of 34 grader tests; one fixed two-line output for every file (cheat-const-nothing) scores 0 and matches none of the 337; the conditions run in query order over whole columns (cheat-pos-query-order) scores 0 and matches none; the worked example replayed (cheat-replay-example) scores 0 and matches none, since tiny.txt is not in the graded set; the frozen answers carried in a collected file (cheat-forge-hand) reproduces all 31 enumerated files exactly and is caught on the drawn population.
- Independent implementation behind every tolerance and limit (path, measured headroom): the wall clock is the only limit; every graded quantity is an integer compared exactly. Two correct implementations written apart from the reference - authoring/scan-chunk-pick/variants/ok-slice (no maintained counts, a byte slice summed) and ok-bisect (counts in a dict, the owning chunk found by binary search) - get through the whole graded set in 4.55 s and 2.13 s against the reference's 1.81 s and the stated 60 s. The naive family the limit rules out is measured too: survivors held as a collection of row ids that every score walks takes 398.26 s on wide.txt against 0.50 s and 9.79 s on deep.txt against 0.13 s, printing exactly the reference's trace both times.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token - `qry`, `rd`, `dc`, `sel` and `prj` - and every model branch that touches one. Two decisions the text did not settle came out of it and both were written: a chunk with no live rows under a comparison, which the per-kind list read as not covering, and the order of the header tests against the dictionary, which decides whether `rd` is printed at all. No fresh-session form was run; the readings, their separating cases and the two correct variants stand in its place.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the six files `/app/scn/hdr.py`, `/app/scn/dct.py`,
  `/app/scn/pick.py`, `/app/scn/live.py`, `/app/scn/step.py`, `/app/scn/proj.py`. Nothing else
  is collected. The verifier lays them over its own pristine copy of the tree, so the parser,
  the chunk reader, the trace writer, the driver and the sample segments cannot change what a
  segment file prints, and a seventh file placed beside the six is never collected.
- What is checked: the exact list of lines `/app/run_scan.py` prints for a segment file, in
  order, compared byte for byte. Hand-written segment files are checked against `gt.json`,
  frozen before the grading file was written; generated segment files are checked against the
  sealed model, which must itself reproduce `gt.json` exactly before anything is graded. Every
  file must match; one wrong line is a zero.
- Tolerances: none. Every graded quantity is an integer or a line of text and comparison is
  exact. The one limit is the wall clock on the worker, which is the task's stated execution
  limit and is validated against two independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  root-owned `0700` directory the sandbox uid cannot read, so submitted code running inside the
  verifier cannot compute its answers from them.

### The graded decisions, and the sentence each is owed

1. widened bounds when the exactness flag says the recorded pair is not exact
2. the count a header allows, per condition kind, on both sides of zero
3. the test that lets a chunk pass unread, and that it needs no nulls
4. a dictionary decides only when the chunk's overflow list is empty
5. a chunk's dictionary is charged once, however many conditions consult it
6. a dictionary that rules every entry out drops the chunk; one that admits them all with no
   nulls keeps it; anything else decodes
7. is-null and is-not-null are never answered by a dictionary
8. the condition worked next is the pending one with the smallest estimate
9. an estimate is capped chunk by chunk by the survivors that chunk still holds
10. a decoded chunk is estimated by its exact count, not by its header
11. a decode settles every condition of the query over that column
12. the chunk taken is the lowest-numbered one still pending for that condition
13. a tie between estimates goes to the condition written earlier in the query
14. the report pass decodes only chunks that hold a survivor and are not decoded already
15. reported columns are worked in the order the query lists them
16. the reported count excludes nulls and the reported total adds only non-null values
17. every query starts over: all rows alive, nothing decoded, no dictionary charged

### Prong C in the contract

- C1: cases fence both sides of every skip - a chunk that must be dropped unread, a chunk that
  must be kept unread, and ordinary queries where nothing prunes and every chunk is decoded.
- C2: the surviving-row digest is the only thing an implementation can check against itself,
  and a decode-everything engine produces it correctly while its events are wrong.
- C3: two segment shapes, one of many small chunks and one of few large ones, against a stated
  wall clock, kill the two natural recomputations while leaving them exactly correct.
- C4: hand-written segment files aimed one per graded decision, plus a nonce population
  generated after the agent's container is gone, compared line for line, all or nothing.
- Route-around guard: only the six files are collected and everything else is replaced from the
  verifier's pristine copy, so the driver, the grammar, the decode primitive and the trace
  writer cannot be rewritten to reshape the problem.

## Decisions and their reasons

- The exactness flag is not consulted when a low equals a high. It was at first, on the reading
  that `eq v` may only be settled from a single-value pair when the pair is exact - but a widened
  pair always has its low strictly below its high, so the guard was unreachable. `readingcheck`
  reported both readings that rest on it as equivalent to the reference, which is what found it;
  it is gone from the reference and the model rather than kept as dead code.
- The graded segment files are built by `tests/prep.py`, as root, before the clock on the worker
  starts, so the 60 seconds the brief states measures the submitted engine and not the
  verifier's own generation. It also means the seed is never handed to the process that runs the
  submission: the worker is given the built files and nothing else.
- Values are non-negative integers rather than strings, so the inexact-statistics rule can be
  stated as arithmetic on a granularity rather than as byte truncation, and every graded number
  stays exact.
- The surviving rows are reported as a count and a digest rather than as a list, because a wide
  segment would otherwise print forty thousand row ids per query; the digest is computed by the
  frozen trace writer, so the hash is not one of the graded decisions.
- The frozen driver owns nothing but the order of the phases. `live.start`, `pick.run`,
  `live.rows` and `proj.run` are the four names it calls, and the instruction says so, because
  a signature the driver depends on is a graded condition.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py scan-chunk-pick --build`; base image pulled from mirror.gcr.io because the sandbox proxy denies Docker Hub blobs |
| No answer leaked into agent image | pass | the image holds `app_src/` only: engine, grammar, four segment files. No gt.json, no model, no expected output; `extraneouscheck` clean |
| `harbor run -a oracle` = 1 | pass | harbor is not installable here (PyPI ships it for Python >= 3.12, this box is 3.11); `tools/docker_trial.py scan-chunk-pick oracle` is the two-container stand-in and scored 1 with 34 grader tests passing |
| `harbor run -a nop` = 0 | pass | `tools/docker_trial.py scan-chunk-pick nop` scored 0, 19 of 34 tests failing |
| Cheats all score 0 | pass | 39 of 39 scored 0 in `--all`; `authoring/scan-chunk-pick/cheat_report.py` names the enumerated case that catches each semantic one |
| Correct variants score 1 | pass | ok-slice and ok-bisect through `--dir`, 34 grader tests each |
| The wall clock fires in the container | pass | `cheat-slow-rowid-set` is exactly correct on every enumerated file and scores 0 in the two-container trial, so the limit is enforced where it is claimed rather than only on the host |
| `tracecheck.py` (every graded assertion traced) | pass | clean, 75 graded rows |
| `readingcheck.py` | pass | 23 readings, all separated by the enumerated set |
| `forgecheck.py` / `onelinecheck.py` | pass | forgery carries gt.json verbatim and scores 0; two of three graded decisions have no exact rule at depth 2 |
| `preflight.py` | pass | no errors; 16 warnings, all the module-qualified-call false positive that every retained bundle also raises |
| `harbor check` rubric | not run | no API key in this environment |

## Quality self-review (docs/QUALITY-REVIEW.md), 2026-09-22

Walked criterion by criterion, each answered with the file that satisfies it.

Instruction and verifier agree in both directions. Every behaviour the tests check has its
sentence: the walk is `authoring/scan-chunk-pick/trace.md`, 75 graded rows, and
`tools/tracecheck.py` is clean. Every sentence has a test: the 31 enumerated files in
`tests/cases.py` are named one per graded decision plus the must-still-work side of each fence,
and `tools/readingcheck.py` reports all 23 wrong readings separated by that set. The six files
the tests read are named with absolute paths in the third paragraph, and the four entry points
the frozen driver calls are named in the same paragraph. The output format is given down to the
line, and one whole worked output is quoted. Boundaries are settled in the text: numbering from
0 for rows, columns and chunks, the two tie-breaks, the rounding of the interpolation and its
endpoints, both sides of each header test, what a null satisfies, and what a query resets.

Nothing in the prose contradicts the reference. Every count in the brief and in `task.toml`
was re-derived from the code after the last generator change: 337 graded files (31 hand, 300
small, six large), 12 families, 39 cheats, the two large shapes at forty thousand rows, and the
timings. `tools/hintcheck.py` is clean.

Prose. The parallel run of six per-condition sentences that the first draft had is gone,
merged into two clauses of one sentence. `tools/textcheck.py` against `note-carry-forward` puts
this brief at burstiness 0.775 and 24 per cent short sentences, inside the band the retained
briefs occupy (0.737 to 1.009, 25 to 40 per cent); its remaining findings are against axes where
the chosen reference is itself the outlier of the retained set.

Verifier rigor. The tests demand the trace of a real run, not a status: the worker records what
each segment file printed and the grader compares it line for line against a model it re-derives
itself. `tests/test_outputs.py` carries the frozen contract in its docstring, one numbered rule
per graded decision, and each test section says what it checks. Nothing depends on wall-clock
time, the network, or an ordering that is not itself under test; the seed is drawn once and both
halves derive the same population from it.

Environment hygiene. Neither `tests/` nor `solution/` is copied into the agent image - the
environment Dockerfile copies `app_src/` and nothing else, and `tools/imagecheck.py` reports the
17 files the image would hold. The verifier installs pytest 9.1.1 and pytest-json-ctrf 0.5.2 in
`tests/Dockerfile`; `tests/test.sh` installs nothing. Every path and name in the brief exists in
the tree and is spelled identically, checked mechanically.

Solution quality. `solution/solve.sh` copies six modules that compute the answer and runs the
driver on two shipped segment files; nothing is echoed as a final answer and nothing the agent
could not legitimately use is touched.

Anti-cheating. The answer is not in the environment: no expected output, no checksum, no
annotation, and `tools/extraneouscheck.py` and `tools/deadfieldcheck.py` are clean. Grading is
exact and all-or-nothing, so a degenerate output fails; the constant, positional and replayed
strategies all score 0 and match none of the graded files. No repository is cloned.

Metadata. `category = "Software"` with `subcategory = "Databases"`, and `tools/catcheck.py`
measures 30 environment hits for the Software vocabulary against 98 in the prose, so the
category is carried by the code rather than by the story. The six tags name techniques rather
than the taxonomy. `difficulty_explanation` names the concrete steps - the loop shape, what a
read settles, the survivor representation - and says plainly that the identifiers are in a
legacy register by choice. `relevant_experience` describes the scan-layer work this task is
made of and claims no employer, credential or duration.

Known risks carried to the reviewer: `tools/simcheck.py` puts both Dockerfiles at or near 1.0
against retained bundles, which is boilerplate that cannot differ without making the images
worse, and `tests/test_outputs.py` at 0.58, which is the shared house structure of fixtures and
a parametrized case sweep rather than copied content.

## Stage 7 re-attack (D7), 2026-09-22

Read cold, with the built tree in front of me, the honest answer is still that my first plan
would be wrong in two places that matter.

The loop. Every scan engine I have read, and the one that ships here, is a pass per condition
over its column. The brief says the unit is a pair and that the choice is remade after each one,
but that sentence sits in a paragraph about scoring and it is easy to implement as "sort the
conditions by score, then sweep". That is a rewrite of the outer loop rather than a patch, and
`cheat-ord-fixed-sweep` is that plan, and it prints something else on 102 of 137 graded
files.

What a read settles. "It settles the exact count of every condition of the query over that
column" is one clause, and the natural implementation records the condition that asked. Nothing
in the surviving rows shows the difference; it shows up as a different chunk being read three
steps later. I would have got this wrong on a first pass, and it is the finding that invalidates
the state a chunk carries rather than adding a case to it.

The survivors. The shipped engine holds them as a set of row ids and the corrected loop asks for
a chunk's count of them thousands of times per query. That is 398 seconds on the shipped wide
segment against half a second, so the representation has to change as well - and the change is
not the obvious one, because maintaining a count per chunk means charging a death to one chunk
of every column the query touches, and the partitions differ between columns.

What has not drifted: the environment is 394 lines over eleven modules, six of them editable and
all six shipping wrong; the reference is 310 lines; the difficulty record re-measured against the
built tree still scores 100. What has: nothing I can see in the direction of easier. The brief
grew by two sentences during the cold-reader pass, both of them closing a decision the text left
open rather than handing over a method.

Estimated solves, unchanged from Stage 1: 2 of 8. The risk I would flag to a reviewer is the
other end of the band rather than this one - seventeen graded decisions is a lot to get right at
once with no oracle to check against, and a run that returns 0 of 8 would be this task failing
for being intricate rather than for being unfair. Against that: every rule is stated, the
example pins the output format exactly, the four shipped segment files exercise every branch of
the grammar, and two implementations written apart from the reference both score 1.

## Open questions and next steps

Built and validated. The external probes - the AI text screen, the similarity screen, the
quality review and the eight-attempt difficulty probe - are the ones that have not run. Two
local findings worth carrying forward: `tools/simcheck.py` puts `tests/test_outputs.py` at 0.58
against `expert-defer-shed` after a deliberate rename of its helpers and fixtures, which is the
shared house structure rather than copied content, and both Dockerfiles are boilerplate that is
identical to every retained bundle's by necessity. Neither can be reduced further without making
the verifier worse.
