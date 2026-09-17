# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - packaged` (contract frozen 2026-09-16, bundle built 2026-09-17)

## Assistant's assigned role

You are a storage engine engineer who has worked on the claim service of a multi-user store:
the part that decides which job may touch which box and slot, what happens when a job holds so
many slots that the service swaps them for the box, and which job is given up when a set of jobs
end up waiting for each other. Comfortable with re-entrant claims, with conflict tests that span
two levels of a name space, and with the difference between an engine that is correct and one
that is affordable at the size a store actually runs at.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing is vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): none
- Load-bearing couplings found during research (file paths): written, not vendored - see "Why it is hard"
- Identifier degradation done? The tree is authored in the legacy register from the start
  (`hb/`, `fit`, `line`, `knot`, `lift`, `hold`, `say`); no conversion table is needed because no
  upstream names exist
- Proper-noun sweep done? Nothing in the tree names a product, person, company or standard
- Upstream-diff check: there is no upstream to diff against

## Task summary

The agent is given a claim service for a two-level store. Jobs take claims on boxes and on the
slots inside them, in mode r or w. The service decides at once, makes a job wait, lifts a job
that holds many slots of one box up to the box itself, and stops a job when a set of jobs have
come to wait for each other. Six files under `/app/hb/` decide those things and all six ship
wrong. The graded artifact is the event trace each program prints; every graded program must
match line for line, and the whole graded set has to run inside the stated limit.

## Why it is hard

The rules are all stated. What is not stated is which structures survive all of them at once,
and that is the work. A claim on a box and a claim on any of its slots conflict, so the unit of
decision is the family and not the node; a request its own job already covers is granted ahead of
a line it would otherwise join; a hold is a list of acquires rather than a mode, so a drop can
lower what a job holds without ending its hold; grants are ordered by one store-wide sequence, so
one end or one stop frees claims in several boxes at once and the grants they owe interleave
by that sequence rather than box by box;
and the relation that decides which job is stopped runs through waiting requests as well as
granted claims.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the recalled design is wrong here in four places at once. The recalled
  design for this problem is multiple granularity claiming with intent modes, per node lines and
  a wait-for graph over holders. This service has no intent modes, its grant order is not per
  node, and its waits-for relation includes older waiting requests, so the recalled structures
  are each wrong in a way that is invisible until a program puts two families in play at once.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, B2, C1, C3 and C4. A1 (the intent-mode prior is specifically wrong here), A2 (no term of art is used
  in the brief), B2 (thirteen rules hold at once with no per-rule feedback), C1 (both sides
  fenced: disjoint and compatible work must be granted at once), C3 (three correct but infeasible
  readings die on the stated limit), C4 (line-for-line comparison against frozen answers and a
  sealed model on a nonce population).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  a granted map plus a first-in-first-out line per node, a compatibility test against that node's
  granted modes, a per node drain on release, edges from a waiter to the jobs holding what it
  conflicts with, and a slot count that swaps into a box claim at the floor. That plan is wrong
  in four places: the conflict test has to span the family, coverage grants ahead of the line, the
  drain is one store-wide sequence rather than per node, and a lift that cannot be granted at
  once waits while still holding the slot claims it will give up.
- Estimated solves out of 8: 2 (designed for the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2): attempt 1 on 2026-09-16 scored 100/100, in band, no hard stop, one warning
  (gate.measured false - the timings are run before the brief states the limit).
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet anchored
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-16 first record, 100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the tree stores
  acquires and nothing derived from them - no per box count, no covering flag, no sequence number
  in any event, no helper that names the waits-for relation, no answer file beside any program,
  and the frozen answers and the model live in a directory the verifier locks before any
  submitted code runs.
- Expert path, described step by step: read the driver and printer to fix what a trace is; settle
  the hold as a list of acquires; settle the family conflict test with per box counts; settle
  coverage before the line; put waiting requests in one store-wide sequence and sweep the
  smallest grantable one to fixpoint; make the lift a box request that keeps its slot claims
  until granted, then frees them in slot order and grants its trigger by coverage; derive the
  waits-for relation from blockers of both kinds and stop the job on a cycle with the fewest
  acquires; then measure the wide programs and replace every family walk with an index.
- Originality check: searched for public write-ups - see "Originality" below.

## Originality

No public write-up covers this service. The public material closest to it is a database text or
vendor manual on multiple granularity claiming: intent modes, a compatibility table, a child
claim needing its parent intent claim, and a wait-for graph with victim selection. This service
has no intent modes at all, which is the point of the deviation: the work the intent mode does
in the retrieved design has to be rebuilt here as counts kept per box. Nothing in the retained
set of this repository uses this mechanism - the closest are `alias-settle-report` (union-find
over disequalities) and `slab-fold-scope` (a commit path with staged rollback), and neither
grades claim admission, a covering rule, a lift or a stuck set.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the six files `/app/hb/hold.py`, `/app/hb/fit.py`,
  `/app/hb/line.py`, `/app/hb/sweep.py`, `/app/hb/knot.py`, `/app/hb/lift.py`. Nothing else is
  collected; the rest of the tree is the verifier's pristine copy.
- What is checked: for every graded program, the exact list of event lines the service prints,
  compared line for line. Hand programs are checked against `gt.json`, frozen before the grading
  file was written; generated programs are checked against a sealed model, and the model is first
  checked against `gt.json` so a drifted model cannot redefine correct. The whole graded set runs
  under one wall clock which is also the task's execution limit.
- Tolerances: none. Exact string equality on every line, all-or-nothing over the whole set.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a directory
  `chmod 700` root-owned before any submitted code runs.

### The frozen rules, in the order the engine applies them

1. A store holds boxes named `b<N>`; a box holds slots named `b<N>:s<M>`. A claim names a box or
   a slot, in mode `r` or `w`. Two modes conflict when at least one of them is `w`.
2. A hold is a list of acquires. `take` adds one; `drop` removes the most recently added acquire
   on that node, printing `free` only when one was removed; the modes left decide everything.
3. The family of a node is the node itself, its box when it is a slot, and its slots when it is a
   box. A granted claim of another job in the family conflicts with a request when their modes
   conflict.
4. Coverage: a request by job J is granted at once, whatever else blocks it, when J already holds
   a claim on that node or on its box whose mode covers it - `w` covers a request in either mode,
   `r` covers a request in `r`.
5. Otherwise a request is granted when nothing blocks it. Blockers of a request in mode m by J:
   a granted claim of another job in the family whose mode conflicts with m, or a waiting request
   of another job in the family with a smaller sequence number whose mode conflicts with m.
6. A request that is blocked waits and takes the next sequence number, printing `wait`.
7. Lift: a request by J for a slot of box b, when J holds no covering claim on b and holds granted
   claims on four or more distinct slots of b, becomes a request for b instead, in mode `w` if
   the request or any of those claims is `w`, else `r`. It prints `lift`, then follows rules 4 to
   6 as an ordinary request for b.
8. When a lifted request is granted, J's acquires on every slot of b are released in ascending
   slot number order, each printing `free`, and the slot request that caused the lift is then
   granted, printing `grant`.
9. Sweep: after anything a job holds changes, the engine repeatedly grants the waiting request
   with the smallest sequence number that is now grantable under rules 4 and 5, until none is
   grantable. Grants print in the order they are made.
10. Stuck sets: with the sweep at its fixpoint, job J waits for job K when K is a blocker of J's
    waiting request under rule 5. While any job lies on a cycle of that relation, the engine stops
    one: among every job on any cycle, the one holding the fewest acquires counted with
    repetition, ties to the largest job number. Stopping prints `stop`, cancels its waiting
    request, and releases every acquire it holds in ascending node order, each printing `free`;
    the sweep then runs again and the check repeats.
11. A stopped job ignores every later line naming it.
12. `end` releases every acquire the job holds in ascending node order, each printing `free`, then
    prints `done`, then the sweep runs.
13. `show n` prints `at n` followed by each job holding n in ascending job number, each with its
    acquires as mode letters sorted with repetition.

Node order is ascending box number, then the box itself before its slots, then ascending slot
number. Event lines: `grant <job> <node> <mode>`, `wait <job> <node> <mode>`,
`lift <job> <box> <mode>`, `free <job> <node>`, `stop <job>`, `done <job>`, `at <node> ...`.

Input invariant, stated in the brief: a program never gives a line for a job whose request is
waiting.

### Prong C tactics this contract uses

- C1: enumerated programs fence both sides of every rule - the disjoint and compatible cases that
  must be granted at once as well as the cases where a lift, a cycle or the sequence order bites.
- C2: the obvious oracle is denied. The shipped engine is wrong, no standard tool implements
  these rules, and the graded population is generated from a seed drawn after the agent's
  container is gone.
- C3: three correct but infeasible readings die on the stated limit - a conflict test that walks
  a box's slots at 179 s, a sweep that reconsiders every waiting request at 289 s, and a stuck
  check that runs after every operation at 628 s, against 3.0 s for the reference and a 60 s
  limit.
- C4: line-for-line comparison, all-or-nothing, over hand programs and a nonce population.
- Route-around guard: only the six files under `/app/hb/` are collected. The driver, the store,
  the printer and the dispatcher are the verifier's own copies, so the trace format and the
  operation set cannot be reshaped by the submission.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): walked in full, tracecheck clean. 4 test functions, 32 enumerated cases, 6 artifacts, the 60 s clock and 31 rules
  of the sealed model, each with the sentence it traces to. No NOT STATED rows remain;
  `python tools/tracecheck.py claim-cover-lift` is clean. The trace is generated by
  `authoring/claim-cover-lift/make_trace.py` so the cited sites cannot go stale silently.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): all 27 readings are separated. 27 wrong readings are written as whole submissions in `authoring/claim-cover-lift/emit.py`
  and measured by `tools/readingcheck.py`. All 27 are separated by an enumerated case. Two were
  found blind by that measurement and repaired rather than argued: a claim on a slot taken to
  cover a request for its box survived every case until `cover-up-only` was changed to hold the
  slot in w, and a lift floor counting acquires rather than distinct slots survived until
  `lift-repeat` was added from the shrunk counterexample the tool printed.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): every one scores 0. The shipped tree scores 0 and matches 13 of 32 enumerated programs and 7 of 48
  generated ones; granting every request at once scores 0 at 9 of 32 and 0 of 48; replaying the
  brief's own worked example scores 0 at 0 and 0; an answer key for all 32 enumerated programs
  scores 0, passing every one of them and failing the generated population. There is no earlier
  revision of the reference to score: the shipped tree is the engine it replaces.
- Independent implementation behind every tolerance and limit (path, measured headroom): two variants written apart, 15x headroom and better. The only limit is the 60 s clock on the graded run. `authoring/claim-cover-lift/variants/jobmajor`,
  written apart from the reference, settles the whole graded set in 4.1 s and
  `authoring/claim-cover-lift/variants/heapsweep` in 2.7 s, against 3.0 s for the reference; the
  three correct-but-walking readings take 179 s, 289 s and 628 s. The two variants were timed on
  the population as it stood before the wide family was widened, where the reference took 2.4 s
  rather than 3.0 s, so their headroom is of the same order. There are no float tolerances -
  comparison is exact string equality.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): two were found and both were written into the brief. Author-run, mechanically, over every printed token and the model branch behind
  it. Two decisions were left open and both were written into the brief: which node and mode the
  grant after a lift names, and what a show prints for a node nobody holds. Everything else was
  answerable from a quoted sentence. A fresh-session reading was not run; the author wrote the
  model, so a cold solve here would measure memory rather than the brief.

## Decisions and their reasons

- No intent modes. The conflict test spans the family directly, which is what makes the
  retrieved design wrong and turns the work an intent mode does into a structure the submission
  has to derive.
- The sweep is ordered by one store-wide sequence rather than per node. This is the rule that
  invalidates the per node line: an end or a stop frees claims in several boxes at once, and the
  grants those releases owe come out in one sequence rather than box by box.
- A lift that cannot be granted at once waits rather than being abandoned. Abandoning would make
  the lift a local decision; waiting makes it a claim that blocks others while the job still
  holds what it will give up, which is where the cycles come from.
- Cycle detection is defined over every job on any cycle, not over the cycle a search happens to
  find, so the victim does not depend on traversal order and two correct implementations agree.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | every container registry is denied by this session's egress policy (403 on Docker Hub's blob CDN, ECR, ghcr and quay), so no image could be pulled or built |
| Image contents without Docker | pass | `tools/imagecheck.py`: the image would hold 16 files, workdir /app; the reference dropped in runs all four shipped programs |
| No answer leaked into agent image | pass | `extraneouscheck` clean; the tree holds no gt, no model, no expected output; the seal is `chmod 700` before any agent code runs |
| `harbor run -a oracle` = 1 | host emulation | harbor is not installed here. `authoring/claim-cover-lift/host_trial.py oracle` runs `tests/test.sh` verbatim as root with the privilege drop, the locked reward channel and the artifact upload emulated: reward 1, 35 tests passed |
| `harbor run -a nop` = 0 | host emulation | reward 0, 20 failed 15 passed |
| Cheats all score 0 | pass, host emulation | 42 of 42 score 0, and all 42 are caught by the layer they were built for (`authoring/claim-cover-lift/cheat_report.py`): each wrong reading by the enumerated case named for it, the three correct-but-slow readings by the clock, the answer key by the generated population alone, and the three record-destroying probes by the grader's own record checks |
| Correct variants score 1 | pass, host emulation | both `jobmajor` and `heapsweep` score 1 through the full two-stage trial, and agree with the sealed model on 102 programs including the wide families |
| Readings separated | pass | 27 of 27 wrong readings separated by an enumerated case (`tools/readingcheck.py`) |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | clean |
| `structcheck` / `hintcheck` / `catcheck` / `solvecheck` / `deadfieldcheck` / `extraneouscheck` / `imagecheck` / `forgecheck` | pass | none |
| `simcheck` | known overlap | `environment/Dockerfile` scores 0.82 against three retained bundles; the retained bundles score 1.000 against each other on the same file, so a six-line Dockerfile that copies a source tree is the floor, not a copy. Nothing else is flagged, and the conceptual check reports that this task grades what no earlier one does |
| `harbor check` rubric | not run | no API key in this session |
| Reference against the model, other seeds | pass | three further seeds, 70 programs each, no mismatch |
| `difficultycheck` on the built tree | 100/100 | measured 364 environment lines, 6 editable files, 405 reference lines, 42 cheats, 2 variants |
| `package.py` + `zipcheck` | pass | 93 entries, no clutter, `.sh` files 755, the org name only in `[task] name`, no CRLF |

## Cold self-attack (Stage 6)

Run as the mechanical cold-reader pass above rather than as a cold solve, and recorded as such:
the author wrote the sealed model before the brief, so a self-solve would measure memory. What
stands in its place is measured rather than asserted - 27 wrong readings each separated by a
named case, four shortcut strategies scored, an answer key that passes every enumerated program
and fails the generated one, and two independently written correct services that score 1.

The honest first plan, written before the environment existed and recorded in the difficulty
record: a granted map and a first-in-first-out line per node, a conflict test against that node's
granted modes, a per node drain on release, waits-for edges to the jobs holding what the waiter
conflicts with, and a slot count that swaps into a box claim at the floor. Four of those five are
wrong here, and the two that matter - the family test and the store-wide grant order - are wrong
in ways that only show up when two boxes are in play at once or when a box is large.

## Quality self-review (docs/QUALITY-REVIEW.md, criterion by criterion)

Instruction against verifier, both directions:
- every graded behaviour is described: `authoring/claim-cover-lift/trace.md` carries a row for
  each of the 4 test functions, the 32 enumerated cases, the 6 collected files, the 60 s clock
  and 31 rules of the sealed model, each with the sentence it traces to; `tracecheck` is clean.
- every promised behaviour is tested: each rule has its enumerated case (the case names in
  `tests/cases.py` are the rule names) and the generated population re-tests all of them.
- the collected files are named with absolute paths in the brief, and nothing else is read.
- the output format is specified event by event, including the empty `at` line.
- boundaries: the floor is "four or more", the line test is "a smaller sequence number", conflict
  is "at least one of them is w", coverage is stated in both directions, ties in the victim rule
  go "to the largest job number", and node and job order compare numbers as numbers.
- graded quantities defined: an acquire, a sequence number, the lift floor, the acquire count the
  victim rule reads, and the mode letters a query prints.
- counts in the brief and the metadata were re-derived from `tests/gen.py` and `tests/cases.py`
  after the last generator change, not from memory.
- verifier requirements in the text: the six collected files, the entry points `ops.py` calls,
  the pristine overlay, the wall clock, the CPU and the memory.
- identifiability: 27 readings, each separated by an enumerated case; the dumbest strategies and
  an answer key all score 0; the limit is validated by two independently written variants.

Instruction prose: `tools/textcheck.py` against `slab-fold-scope` reported an even cadence, too
few short sentences, two oxford triads, a hedge and a high apostrophe density. The triads were
"b1, b2 and so on" and "j1, j2 and so on" and are gone; the hedge was "rather than one per node"
and is now "not one per node"; long rules were split into short sentences and two paragraphs
were divided, which took burstiness from 0.59 to 0.67 and contractions from 6.2 to 3.5 per
thousand words. Two findings are left and both are the genre: a rule spec repeats its domain
nouns, so the type-token ratio stays at 0.25 against a narrative brief's 0.35, and its cadence
stays more even than prose that tells a story. Widening either would mean saying a requirement
twice in different words, which is the thing the manual warns against. Read end to end for runs
of same-structured sentences. Two openers were
rewritten ("A job waits for another job" and the example paragraph) and one sentence was
rephrased because it said a take adds an acquire when it is a grant that does. No headings, no
bullets, no code block, plain ASCII.

Verifier rigor: the tests grade a trace produced by running the submitted service over a
pristine copy of the tree (`tests/worker.py`), never a report it wrote; `tests/test_outputs.py`
is commented section by section and its frozen contract is stated at the top; the population is
seeded, and the seed is the only wall-clock dependence besides the stated limit.

Environment hygiene: `environment/Dockerfile` copies `app_src/` and nothing else; the verifier
installs its own pins (`pytest==9.1.1`, `pytest-json-ctrf==0.5.2`) at build time and fetches
nothing at trial time; every path and symbol named in the brief exists in the tree, checked
mechanically.

Solution quality: `solution/solve.sh` copies six files that compute the answer and then runs two
shipped programs; nothing is echoed into place as an answer.

Anti-cheating: the tree holds no ground truth, no expected output and no `.git`; the seal is
`chmod 700` before any agent code runs; comparison is exact; a submission carrying the frozen
answers for every enumerated program scores 0 on the generated population.

Metadata: category `Software`, subcategory `Databases`, six tags naming the mechanisms rather
than the taxonomy; `difficulty_explanation` names the structures that break and says the legacy
register and the stripped documentation are deliberate; `solution_explanation` describes the
method file by file; `verification_explanation` says what each layer proves; `relevant_experience`
is written from this task's own domain; ten hours is consistent with six editable files and
thirteen graded decisions.

## Known risks to flag to a reviewer

- No container evidence. Every gate that would normally run under Docker ran under the host
  emulation in `authoring/claim-cover-lift/host_trial.py`, which runs `tests/test.sh` verbatim as
  root and reproduces the privilege drop, the locked reward channel, the survivor reap and the
  artifact upload, but not the image build or the filesystem isolation between the two stages.
  `tools/imagecheck.py` stands in for the build by assembling what the image would hold and
  running the shipped programs against it.
- The execution limit was measured on this host. The reference has about 25x headroom and the
  slowest correct variant about 15x, so the margin survives slower hardware, but the numbers in
  the brief and the metadata are from here.
- `environment/Dockerfile` is close to the retained bundles' by similarity. It is six lines of
  required boilerplate and the retained bundles are identical to each other on it.

## Open questions and next steps

Package and deliver. Nothing is waiting on the contributor.
