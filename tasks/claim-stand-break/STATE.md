# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 — Pre-flight and packaging`

## Assistant's assigned role

You are a storage engineer who works on the commit path of a keyed store: the part that decides
whether a transaction is still entitled to go through. Years of reading traces where the answer
a client was given stopped being true while the transaction that asked for it was still open,
and of the bookkeeping that has to survive a rollback to a savepoint.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository vendored)

## Task summary

`/app` is the commit path of a small keyed store, cut down to the part that decides whether a
transaction may go through. A program is a text file of ops: `open` starts a transaction, `get`
and `span` read, `put` and `del` change, `mark` and `back` are savepoint and rollback, `seal`
commits, `drop` abandons, and `look` prints committed rows. Every read and every change a
transaction makes is a claim, numbered from 0 in op order. A read claim stands while answering
it again - against the rows committed now, under the transaction's own changes that were made
before it and have not been undone - gives exactly what it gave. A change claim stands while it
has not been undone and no commit after the transaction's base has written its key. The moment
a standing claim stops standing the transaction is dead, which prints `dead <t> <i>` with the
lowest index that stopped at that moment, and a claim that stopped standing never stands again.
The six files under `/app/tx` ship wrong. The agent repairs them so every program prints what
the rules say, inside a 60 second limit over the whole graded set.

## Why it is hard

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the published plan for
  this shape - optimistic concurrency control with read-set validation - is version-based,
  set-based and runs once at commit. All three are wrong here, and each is wrong in a way that
  ordinary programs do not show: value comparison only matters when a key is restored, the
  recorded key set only matters when a rollback uncovers a key underneath the reader's own
  change, and commit-time checking only matters when the state moves and comes back. A plan
  formed from any retrieved source therefore passes casual testing and fails the graded set.
- Tactics making that true: A1, A2, B2, C1, C2, C3, C4. A1 the retrieved validation rule is version-based, set-based and runs once at commit, and all three are wrong here; A2 the brief never names read sets, predicate locks, phantoms or validation; B2 row limits, own-change cover, rollback, permanence and change claims each change what another means; C1 a same-value rewrite, a write past a filled scan and a rollback that uncovers nothing must all leave the transaction alive, so over-refusing fails as hard; C2 the engine in the tree is the wrong reading and no standard tool has these semantics; C3 answering a scan again to judge it is exactly correct and takes 362 seconds against a 60 second limit; C4 exact traces, all-or-nothing, over hand programs per rule plus a nonce population shaped around cover, rollback and restore.
- Assistant's attack on the plan: my own first plan was optimistic validation - base version,
  read set recorded per read minus my own written keys, write set, all checked at commit against
  versions stamped after the base. That plan is wrong three ways here and the third takes the
  structure apart rather than patching it: a read's dependence is not fixed when the read
  happens, because the reader's own earlier changes cover keys underneath them and a rollback to
  a mark takes that cover away after the fact, and a scan that filled its row limit does not
  depend on anything past the last row it returned. So the key set cannot be frozen, and the
  check cannot be driven from the claim side at commit time; it has to be derived at check time
  from the surviving change stack and driven from the keys that moved.
- Estimated solves out of 8: 2 (designed at the hard edge; the realized rate drifts up)
- Difficulty record score: 100/100 on the first record, 2026-09-22
  (`authoring/claim-stand-break/difficulty.toml`), one warning: the resource gate was declared
  before it was measured. Band is 95 to 100 (docs/DIFFICULTY-SCORE.md).
- Difficulty score anchor: not yet submitted; no pipeline anchor exists
- Score history: 2026-09-22 - first record, 100/100, in band, no hard stop.
- Leak audit: the shipped engine records a key set per read, which is the frozen reading itself
  and holds no scope end; the `dead` index is graded output rather than a hint, and is only
  right once the scope rule is; `/app/progs` ships inputs with no expected output; the store
  keeps version lists and the live key index, which are primitives the engine needs to answer a
  read, and nothing holds a scope, a standing set or a failing index; the two wide programs ship
  so the limit is measurable, and the fast path still has to be derived.
- Expert path, step by step: read `run_tx.py` and the trace writer for the exact grammar and
  order; separate the two states a read is answered from (rows at the base, own changes before
  it); index every read and change by claim number and keep changes per key as an index-ordered
  stack; derive a read's scope at check time from that stack rather than freezing it; work out
  that a filled scan depends on everything up to its last row and a short one on its whole
  range; drive checks from the keys that moved rather than from the claims; hold the first
  failure permanently and report its index from both `dead` and `seal`; time the two wide
  programs and replace the per-claim rescan.
- Originality check: searched 2026-09-22 for optimistic concurrency control with read
  validation and savepoint interaction, and for range-scan limit phantom detection. The closest
  public material is forward-validation OCC (validation sends invalidations to active
  transactions), the Hyperledger Fabric phantom note that re-executes range queries at
  validation time, and PostgreSQL's savepoint and serializable-snapshot pages. All compare
  versions rather than values, freeze the read set at read time, and none says anything about a
  rollback widening it; Fabric's re-execution is the reading this task's limit kills. No public
  write-up of this combination was found, and nothing in the retained set touches transaction
  isolation.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace: walked 2026-09-22 into authoring/claim-stand-break/trace.md, and
  `python tools/tracecheck.py claim-stand-break` is clean. 53 rows under Graded assertions - 4
  test functions, 30 enumerated cases, 6 collected artifacts, the pristine overlay, the 60
  second clock and 11 rows splitting the sealed model into the rules it applies, each citing its
  lines. No NOT STATED row survived: two rows had none at first and both were repaired by
  rewording the instruction rather than by dropping the assertion - the sentence about which ops
  print nothing of their own, and the sentence about what a read is drawn from.
- Identifiability: 24 readings are written down as trees under
  authoring/claim-stand-break/readings/ and measured by measure_readings.py and by
  tools/readingcheck.py; every one is separated by the enumerated case named for it, and every
  one moves between 0.9% and 65% of a 108-program population. One reading that survived every
  program - a full re-test of the claims at the seal, on top of the eager checking - is not a
  wrong reading but a correct variant, kept as variants/ok-seal and required to score 1. One rule
  is measurably unobservable and is therefore not graded: a still-standing change of the reader's
  own hides the key underneath it at judging time, but any commit that writes such a key also
  ends the change claim covering it, whose index is always lower, so no program can print a
  difference. It is stated in the brief because a reader needs it to answer the read.
- Shortcut strategies scored: the shipped tree scores 0 and does not finish the set inside the
  clock; nothing printed at all matches 0 of the 396 graded programs; the most common
  line of each kind matches 0; every change landing at once and every transaction sealing ok
  matches 111, which is the everyday side of every fence; the worked example replayed matches 0;
  a forgery carrying the 30 frozen answers matches exactly those 30 and fails every generated
  program. All score 0. Two families were reshaped after this measurement first ran: the
  positional strategy had matched 27 of 40 `edge` programs and 24 of 40 `stale` ones, so those
  two families now fill their row limit deliberately and read the keys that have just moved,
  which took their dead lines from 13 to 29 and from 16 to 34.
- Independent implementation behind every tolerance and limit: the only limit is the 60 second
  wall clock on the whole graded set, validated against the sealed model (tests/seal/model.py,
  written apart) and three correct variants - variants/slow-walk at 4.6 s, variants/slow-over at
  2.4 s and variants/slow-sort at 0.9 s on the host over the same 396 programs, against the
  reference at 1.0 s on the host and 1.45 s inside the verifier container, which is 41x headroom.
  The reading the limit exists to rule out, answering a scan again from the rows, takes 362 s.
- Undecided decisions: the cold-reader pass was author-run on 2026-09-22, mechanically, over
  every printed token, and found six decisions the first draft left open, each now settled by a
  sentence - whether a scan shows the keys the transaction itself made; whether a key it deleted
  still uses up the row limit; whether a rollback takes reads back with the changes; whether the
  mark survives its own rollback; whether the deaths a commit causes print before or after the
  seal line and in what order; and what a dead transaction does with the ops that follow. The
  stronger form, a fresh session shown only the brief and the tree, was not run and is recorded
  here as not run.

## Verifier contract — FROZEN after Stage 2

Frozen 2026-09-22. Changing any line below changes what "correct" means and needs the
contributor's explicit approval.

- Artifacts the agent produces: exactly six files, `/app/tx/rows.py`, `/app/tx/view.py`,
  `/app/tx/log.py`, `/app/tx/scope.py`, `/app/tx/watch.py`, `/app/tx/seal.py`. Nothing else is
  collected. The verifier lays them over its own pristine copy of the tree, so the driver
  (`/app/run_tx.py`), the op parser, the trace writer (`/app/tx/say.py`) and the sample
  programs cannot change what a program prints, and a new file put beside the six is never read.
- What is checked: the exact list of lines a program prints, compared element by element. Thirty
  hand programs against `gt.json`, frozen before the grading file is written; a generated
  population of at least 300 programs against the sealed model, from a seed drawn inside the
  verifier after the agent's container is gone. Every program must match. The sealed model must
  reproduce `gt.json` exactly before anything is graded.
- Tolerances: none. Exact string equality on every line, and on the number of lines.
- Limits: the worker that runs the submitted engine over the whole graded set has a 60 second
  wall clock, stated in the instruction together with the size of the two wide programs. A
  correct engine that cannot get through the set in time scores 0.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  root-owned directory made 0700 before any submitted code runs. The submitted engine runs in
  the worker as uid 1002 and cannot read either.
- Graded decisions, each owed a sentence in the instruction: (1) what a `get` returns; (2) what
  a `span` returns, its key order, its row limit and its own-change cover; (3) claim numbering
  over `get`, `span`, `put` and `del` in op order, counting undone ops; (4) when a read claim
  stands, judged by value against the rows committed now under the changes that were made before
  it and have not been undone; (5) what a claim depends on - a point read its key, a filled scan
  everything up to its last row, a short scan its whole range; (6) when a change claim stands -
  not undone, and no commit after the base has written its key; (7) the three moments claims are
  checked: a claim being made, a commit going through, a rollback to a mark; (8) permanence, and
  the lowest index of the claims that stopped at that moment; (9) `seal`, its two outcomes, the
  order of the lines it causes, and the numbering of commits; (10) `back` and what it removes;
  (11) `look` over the committed rows.
- Prong C tactics in the contract: C1 both sides fenced (the ordinary cases that must still
  commit are enumerated hand programs); C2 no oracle ships; C3 the wall clock over the whole
  graded set with two wide families; C4 exact all-or-nothing comparison over hand programs and a
  nonce population.
- Route-around guard: `artifacts` lists the six `/app/tx` files and nothing else; everything
  else is replaced from the verifier's pristine copy, so the engine cannot be restructured
  around the printed contract or moved into a file that is not collected.

## Decisions and their reasons

- Read claims compare values and change claims compare versions. The asymmetry is deliberate and
  both sides are graded: a same-value rewrite by another transaction leaves a reader alive and
  ends a writer. It is stated plainly in the brief and separates two cheats.
- A rollback to a mark keeps the mark, and removes the changes made after it by position rather
  than by key, so a key written both before and after the mark keeps its earlier value.
- The claim index counts ops that were later undone, so indexes never shift.
- The shipped tree stores no cover end. The first build had `Claim.end` computed correctly in
  `hold.py` while the shipped `cover.ends` ignored it, which handed the agent the filled-scan
  rule for free; `deadfieldcheck` found the dead field and the leak behind it. The reference now
  derives the end in `cover.ends` from the rows and the row limit, and the shipped `view` no
  longer carries the claim index its body never used either.
- Verifier isolation is mandatory here because the verifier executes the submitted engine.
  `docs/VERIFIER-ISOLATION.md` is followed in full: unprivileged worker in its own session,
  root-owned 0700 reward channel written last, default-deny reward, sealed model and frozen
  answers unreadable by the worker uid, survivors reaped by uid, and ten probes in `cheat/`.
- One rule is not graded because it cannot be observed: a still-standing change of the reader's
  own hides the key underneath it when a claim is judged. Any commit that writes such a key also
  ends the change claim covering it, and that claim's index is always lower, so no program can
  print a difference. Measured, not assumed: the variant that drops the cover at judging time
  prints the reference's trace on every program of the population.

## Stage 7 re-attack (D7)

Run 2026-09-22 against the finished bundle, mechanically, because the author cannot un-know the
model. The first plan the brief and the tree produce is still wrong, and in more than one place:

- The brief defines standing as "answering it again the same way ... would return exactly what it
  returned". Implemented literally that is a re-answer of the scan, which is exactly correct and
  takes 362 seconds against the 60 second limit. The repair is not a faster re-answer: it is the
  equivalence that a scan can only move at a key inside what it was drawn from, which turns the
  check from claim-driven into key-driven. That is a replan of the checking path, and it is paid
  for after the semantics are already right, which is as late as it gets.
- A rollback is one of the three moments a claim is judged, and the keys it moves are the ones it
  uncovered. An engine that judges only at commits is right on every program that does not have a
  reader whose own change was rolled back out from under a read - 6.5% of the population, and the
  `off-cover` case.
- The index reported is the lowest of the claims that stopped at that moment. Reporting the first
  one noticed is right until a scan with a lower index and a point read with a higher one break
  together, which is 12% of the population.
- The value/version asymmetry costs a submission both ways: judging a read by version ends a
  reader that should live, judging a change by value keeps a writer that should die.

Are the load-bearing facts still distributed? Honestly, no: the tree is 398 lines and fits in one
attention window, so B1 is not claimed and is not in the record. The difficulty is the conjunction
and the clock, not the size.

Did the instruction come to telegraph the method? It states every rule and no method. The
worked example was searched for rather than chosen: of 4000 candidates it is among the shortest
whose shipped output differs from the reference and which decides no reading the brief leaves to
derivation. It does decide two readings - that a claim is judged when it is made, and that the
first break is the one reported - and both are settled by a sentence anyway.

Estimated solves after the re-attack: 2 of 8, unchanged. The reference path is concrete and every
rule is stated, so an expert gets there; the way to lose is to be right about the rules and wrong
about the structure, which is what the clock and the three check moments punish.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py claim-stand-break --build`, both images |
| No answer leaked into agent image | pass | `tools/imagecheck.py` clean; no gt.json, model or solution under environment/ |
| oracle = 1 (tools/docker_trial.py) | pass | 33 tests passed, reward 1, worker 1.45 s of its 60 s |
| nop = 0 | pass | reward 0; the shipped engine also runs out of clock (182 s for the set) |
| Cheats all score 0 | pass | 40 cheats through the two-image trial: 30 in one sweep, the 10 probes re-run after they were rebuilt |
| Correct variants score 1 | pass | ok-seal, slow-walk, slow-over and slow-sort each scored 1 in the container |
| `tracecheck.py` | pass | clean |
| `readingcheck.py` | pass | 24 readings, every one separated by its enumerated case |
| `cheat_report.py` | pass | every semantic cheat caught by the case named for it, 0 findings |
| `forgecheck.py` | pass | forgery carrying the 30 frozen answers, 0 findings |
| `onelinecheck.py` | pass | span-stands has no exact rule at depth <= 2 |
| `solvecheck.py` / `extraneouscheck.py` / `catcheck.py` / `hintcheck.py` | pass | clean |
| `structcheck.py` on the instruction | pass | 887 words, 11 paragraphs, no findings |
| `simcheck.py` | pass | conceptual: grades what no earlier task grades. The environment Dockerfile matches other bundles because it is six lines of required boilerplate |
| `difficultycheck.py` (Stage 7, measured) | pass | 100/100; 398 environment lines, 6 editable files, 421 reference lines |
| `preflight.py` | pass | 0 errors; 16 warnings, all the unused-public-function false positive that attribute calls produce (the retained `expert-defer-shed` has 16 of the same) |
| `harbor check` rubric | not run | harbor is not installed in this environment |

## Isolation, measured rather than argued

The first build of the ten probes put the tamper on top of the reference engine, and seven of
them scored 1 - not because the isolation failed but because the engine underneath did the work
and earned the reward honestly. A probe whose base can pass proves nothing, so all ten were
rebuilt on an engine that prints nothing at all: the only way one of them can score 1 now is a
tamper that worked. All ten score 0.

What the sandbox uid can actually reach was then measured directly, inside the verifier image,
as uid 1002 under the same `setpriv` the grader uses:

    /logs/verifier/reward.txt   read blocked  write blocked
    /logs/verifier/nonce        read blocked  write blocked
    /tests/seal/gt.json         read blocked  write blocked
    /tests/seal/model.py        read blocked  write blocked
    /tests/seal (listing)       blocked
    /tests/gen.py               readable      write blocked
    /tests/test_outputs.py      readable      write blocked

The generator is readable because the worker imports it; nothing that holds an answer is.

## Quality self-review (docs/QUALITY-REVIEW.md, run 2026-09-22)

Answered criterion by criterion with the file that satisfies it, not with "looks fine".

- Every behavior the tests check is described in the instruction, and every sentence has a test:
  `authoring/claim-stand-break/trace.md`, 53 rows, `tracecheck` clean. The converse was checked by
  reading the brief sentence by sentence against the case list; the only sentences with no test of
  their own are the input guarantees (key and value range, n at least 1, ids used once), which
  bound the input rather than ask anything of the agent.
- Every collected file is named with its absolute path in the instruction: `task.toml` artifacts
  against the paragraph beginning "The files you may change are".
- The schema of what is printed is in the instruction, down to the separators and the order:
  the paragraph beginning "The lines are", against `environment/app_src/tx/say.py`, which is
  frozen and not collected.
- Boundaries and conventions are settled in the text: claims numbered from 0, the row limit as
  "the first n rows", ties on the death order by "lowest transaction number first", the empty
  cases printing `-`, and the read printing before the line its op causes.
- Every graded quantity is defined, including what it excludes: what a read is drawn from, what a
  change claim stands on, and that a change taken back claims nothing.
- Nothing in the instruction or the metadata contradicts the reference, and every count was
  re-derived from `tests/gen.py` and `tests/cases.py` after the last generator change: 30 hand
  programs, 360 generated small ones, 3 deep and 3 wide, 396 in total; wide is 90 scans over
  30000 keys with 2600 rows against 1200 commits; deep is 6000 claims against 3000 commits.
- Verifier requirements are in the text: the six collected files, the pristine overlay, that a
  new file beside them is never read, and the 60 second clock.
- No two readings that reproduce the published evidence disagree on the graded set:
  `tools/readingcheck.py`, 24 readings, each separated by its enumerated case.
- Instruction prose: read aloud once. One run of five identically shaped sentences in the opening
  paragraph (one per op) was rewritten into three sentences with different joins. The two
  sentences that define a read claim and a change claim stay parallel, because the parallel is
  the contrast being drawn.
- Verifier rigor: the tests run the submitted engine and compare whole traces, so nothing can be
  asserted that was not executed (`tests/worker.py`, `tests/test_outputs.py`). The test code
  carries the frozen contract as its module docstring. The only wall-clock dependence is the
  stated execution limit, and the reference has 41x headroom inside the container.
- Environment hygiene: `environment/Dockerfile` copies `app_src/` and nothing else - no `tests/`,
  no `solution/`, no pip. The verifier pins `pytest==9.1.1` and `pytest-json-ctrf==0.5.2` and
  installs nothing at trial time. Every path named in the instruction exists in the tree, spelled
  the same way (checked by `tools/imagecheck.py`, which assembles what the image would hold).
- Solution quality: `solution/solve.sh` copies the six reference files into place and runs two
  shipped programs; it computes nothing by echoing an answer.
- Anti-cheating: the answer is not reachable from the environment (`tools/imagecheck.py`), the
  comparison is exact, and a submission that carries the 30 frozen answers fails on the generated
  population (`cheat-forge-hand.sh`, `tools/forgecheck.py`).
- Metadata: category `Software` with subcategory `Databases`, and `tools/catcheck.py` measures
  122 environment hits for that vocabulary against 144 in the prose, so the label is the work
  rather than the story. Five tags, none of them restating the category or subcategory.
  `difficulty_explanation` names the concrete step and says plainly that the identifiers are in a
  legacy register by choice. `expert_time_estimate_hours` is 9, which matches the nine rules the
  verifier lists as graded and the measured scaling work on top of them.

## Open questions and next steps

Build the environment, then measure the resource gate before the design depends on it.
