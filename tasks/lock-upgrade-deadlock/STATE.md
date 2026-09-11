# Task state

Working memory for this task. Updated after every stage; assume the next session starts with no
memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`, after the difficulty recovery recorded below (platform
difficulty probe 0 of 8 on 2026-09-10, Fable 5.1 at xhigh effort; the easiness probe before it
was 0 of 3) and the 2026-09-11 rename recorded under "Quality review - 2026-09-11 (task
name)". The bundle was submitted as `claim-raise-cut` until then; the probes and the quality
review below were run under that name. Docker's daemon is not available in this session, so the two-container gates are
replaced by `authoring/lock-upgrade-deadlock/host_trial.py`, which runs `tests/test.sh` verbatim as
root with the privilege drop, the sealed directory, the wall clock and the reap all in force;
read the `host trial` rows of the validation table as host emulation rather than container
evidence. The recovery's exit gate is the platform's own probes against this build, which have
not been run; the recovery is therefore **pending** at gate 1 of section 6 of
`RAISE-DIFFICULTY.md`, and this bundle is the candidate for it.

## Assistant's assigned role

Storage-engine engineer on the coordination layer of a transactional store: the part that hands
out claims on items, decides which waiting transaction may go next when one is given back, and
decides which transaction to take out when a set of them can no longer make progress.

## Source repository

- Repo URL: none - idea-based task.
- Task shape: not repo-based, so neither authored-on-top nor ablation applies.

## Task summary

`/app` is a claim service. A program is a text file of `take`, `drop` and `end` steps over
transactions and items; `/app/run.py` prints one event per line (`give`, `wait`, `free`, `cut`,
`done`). Five marks stand together or not according to a pair table in `/app/hold/tab.py`; the
mark covering a set of marks is the least mark excluding everything they all exclude. A take by a
holder is a raise, tested in the cover of its stack and the asked mark, against the mark every
other transaction holds there and never its own claims. A sweep serves raises first, in the order
their transactions came to hold the item, passing over those that fail, and a passed-over raise
pins the item against every first-time claim; first-time claims are served in request order up to
the first that fails. A transaction waits for another when the sweep of its item would grant its
request once the other one is taken out with its claims and its request. After each program step,
once the line of granted transactions has run, the service cuts transactions while the relation
has a ring: fewest items held, then the later request, then the larger number; a cut takes the
victim's request and claims out and sweeps its items in hold order and then the item it waited on.
The five modules under `/app/hold/` (`mark`, `item`, `wait`, `cyc`, `txn`) ship wrong in nine
ways; the verifier overlays them on its own pristine tree and compares every trace line for line
against a sealed model, over 27 enumerated programs and 412 generated from a seed drawn after the
agent's container is gone, inside a 60 s wall clock for the whole set.

## Why it is hard

- Expert time estimate: 10 hours.
- Why a frontier agent cannot one-shot the plan (the strategic answer): the first plan is the
  textbook lock manager - one held mark per item, one wait queue, an edge from each waiter to
  every holder whose mark conflicts with what it asked for, a cycle search, the youngest on the
  cycle killed - and four of its five parts are wrong here in ways the brief states without
  naming: a request is tested with its own claims removed against a cover that cannot be
  un-covered, so the item has no single mark; raises are served ahead of first-time claims in
  hold order rather than request order, so there is no single queue; a passed-over raise pins the
  item against claims nothing held excludes; and the wait relation is defined by removal, not by
  conflict, which differs from the conflict edge in three directions at once behind a pinned
  item (`edge-miss`, `edge-phantom`, `edge-share`). None of that is confirmable one rule at a
  time: the trace never shows the relation, and a conflict-edge engine agrees with the service on
  every item without a raise outstanding, so it passes ordinary testing and cuts a different
  transaction hundreds of steps in. Then the limit decides what a correct structure may cost:
  rebuilding the relation for every item that holds a request, or asking the removal question
  of every live transaction, takes 172 to 242 s against 60 s for the set.
- Tactics making that true: A1, A2, A3, B2, C1, C2, C3, C4.
  A1 (the textbook wait-for graph and the youngest-victim rule are
  the model's prior and both are wrong as specified), A2 (nothing is named: no lock manager, no
  wait-for graph, no lock conversion, no deadlock; the brief says what stands, what is swept,
  who waits), A3 (raises served in hold order ahead of first-time claims served in request order
  is a queue no single discipline gives), B2 (nine graded decisions across five modules, the pin
  and the removal definition changing what "waits" means for each other, no per-decision
  feedback), C1 (both fences on every axis - `pin-fresh` against `raise-pass`, `edge-miss`
  against `edge-phantom` and `edge-share`, `cut-fewest` against `cut-late`, `resume-line`
  against `resume-shed`, `plain-flow` for the overconservative engine), C2 (no expected trace
  ships; the bug report is one line of one program), C3 (four correct-but-slow readings measured
  at 172 to 242 s against the 60 s limit, reference 5.5 s), C4 (27 enumerated programs and 412
  nonce programs in twelve shaped families, all-or-nothing).
- Assistant's attack on the plan: my first plan, read cold, is the textbook one above plus a
  literal removal simulation for the wait relation once I read the definition. That plan is
  wrong in the four places the strategic answer lists, and even with the definition in hand I
  would have made every live transaction a removal candidate and lost the set to the limit
  (measured: 181 s), so the fast path - only a transaction present on the item can change its
  sweep, and holders carrying one mark with no request are interchangeable - has to be derived
  before the plan fits. The three xhigh trajectories on file show the same route: each agent
  formed the textbook plan, replaced it after reading the brief, and reached the pruning by
  profiling. Where all three then fell is recorded under the recovery below, and it was not
  difficulty.
- Estimated solves out of 8: 4 (honest range 2 to 6). Before the repair the realized rate was 0
  of 8 on a defect, and the three trajectories read as three solves once the defect is gone, so
  the top of the band is the live risk now; the next lever if the probe returns 8 is recorded
  under "Open questions".
- Difficulty record score (tools/difficultycheck.py on authoring/lock-upgrade-deadlock/difficulty.toml):
  see "Score history".
- Difficulty score anchor: not yet submitted.
- Score history: difficulty probe 2026-09-10, 0 of 8 solved, on the bundle as uploaded
  (`claimraisecut.zip`); easiness probe before it, 0 of 3. Repaired bundle submitted
  2026-09-11 as `claim-raise-cut`: structural, AI, similarity and reference verification all
  passed; quality review (claude-fable-5-1) failed one blocking criterion, `task name`, and
  passed every other criterion listed (agentic, anti cheat robustness, binary reward, category
  and tags, ctrf reporting, and the rest of the rubric).
- Leak audit (docs/DIFFICULTY.md), run as a procedure:
  - Can a shipped file reproduce a graded answer by a join, a sort or a field comparison? No.
    The tree ships seven programs and no expected trace for any of them; the answer is a trace
    produced by running a program, and nothing in the tree stores one.
  - Is there a stored derived quantity? No. `Item` holds `stack`, `first`, `eff` and `pend`;
    `Tx` holds `order`, `nk`, `req` and `back`. The cover, the counts, the relation and the
    victim are all the agent's to compute; `tab.py` is the pair table and nothing derived from
    it (no rank, no cover table, no exclusion sets).
  - Unused affordances? None: `tools/deadfieldcheck.py` and preflight's unused-function check
    are clean; every function in the five modules is on the shipped live path.
  - Manifests, self-labelling data? None. Artifact that is a function of the correct
    trajectory? No - `gt.json` and the model sit under `tests/seal/`, `chmod 700` before any
    agent code runs, and the answer-key probe reports `PermissionError`.
  - Per-axis confirmation before commit? No - one trace per program, all-or-nothing.
- Expert path, described step by step: read `tab.py` and derive, per mark, the set it excludes;
  define the cover as the least mark whose exclusion set contains the union, check it is unique
  for every subset and folds pairwise; keep a stack per transaction per item and a count of
  holders per effective mark; write the sweep as raises in `first` order against a working copy
  of the counts with the asker's own mark taken off, a pass-over flag, then first-time claims
  in request order until one fails; write the removal question as the same sweep with one
  transaction left out, and prune the candidates to the item's requesters plus one holder per
  distinct mark; keep a set of items whose claims or requests moved and rebuild only their rows
  of the relation; find every transaction on a ring with Tarjan from the changed rows and pick
  by (items held, -request seq, -number); drive the program with a list the granted transactions
  join at the back and run from after the step; time `progs/many.txt` and `progs/spread.txt`
  against the graded scale and check the sum against 60 s.
- Originality check: searched 2026-09-10 for the composite (lock conversion tested against a
  join over a non-standard compatibility table, conversions served in hold order ahead of fresh
  requests, a stuck conversion blocking compatible fresh requests, a wait-for relation defined
  by removal rather than conflict, victim by fewest items then later request). The neighbouring
  real machinery is retrievable - Gray's lock modes, conversion queues in System R and its
  descendants, wait-for-graph deadlock detection - and none of it defines waiting by removal or
  serves conversions in hold order. No write-up of this combination was found.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/hold/mark.py`, `/app/hold/item.py`, `/app/hold/wait.py`,
  `/app/hold/cyc.py`, `/app/hold/txn.py`; nothing else is read.
- What is checked: the twelve numbered rules in the docstring of `tests/test_outputs.py`. The
  worker overlays the five modules on `tests/pristine/`, imports the service fresh per program,
  runs 27 hand programs (`tests/cases.py`) and 412 nonce programs (`tests/gen.py`, seed drawn
  after the agent's container is gone), unprivileged, under a 60 s wall clock; the grader
  compares every trace line for line against `tests/seal/gt.json` (hand) and the sealed model
  (nonce), after asserting the model still reproduces `gt.json`.
- Tolerances: none; every line of every program.
- Ground truth, and where it lives: `tests/seal/gt.json`, frozen from `tests/seal/model.py`
  by `authoring/lock-upgrade-deadlock/build_gt.py`, which refuses to move a frozen answer. Both under
  `chmod 700` before any agent code runs.
- 2026-09-10 recovery, additive: two hand cases (`resume-line`, `resume-shed`) were added and
  the 25 frozen answers came out byte-identical; the model did not change. What "correct" means
  did not move - the brief now states the behaviour the model always had.

## Difficulty recovery - 2026-09-10 (difficulty probe 0 of 8)

### 1. The failure, captured before editing

- Probe result: 0 of 8 solved, Fable 5.1 at xhigh effort, 14400 s each; marked unverifiable.
  The easiness probe before it: 0 of 3.
- Trajectories: three of the eight, under `probes/lock-upgrade-deadlock/`, with the brief stripped
  from the top of each so `tools/leakcheck.py` compares the agent's words against the brief
  rather than the brief against itself: `2026-09-10-difficulty-1-9itDemL.txt` (43 steps),
  `2026-09-10-difficulty-2-N6jw6Cg.txt` (34 steps), `2026-09-10-difficulty-3-RrPppes.txt`
  (19 steps). The other five are not available.
- Each agent's route: all three read the brief and the five modules, listed the shipped
  defects against the sentences they violate, and rewrote all five modules; all three then
  wrote a slow literal model of the brief in `/tmp` and fuzzed the rewrite against it (400 to
  4,000 programs, hundreds of cuts) with zero mismatches; all three generated the two large
  shapes at graded scale and timed them at 0.1 to 0.6 s each; all three then listed the
  points on which they had made a judgment call, and every one of those lists names the
  resumption order. Trial 1: "resumption is depth-first". Trial 2's driver resumes each granted
  transaction inside the sweep that granted it. Trial 3: "nested cascades run before the outer
  transaction continues". None of them ran out of time or budget; each ended with a
  fuzz-verified engine it believed correct.
- Earliest point at which each had enough information to commit: after reading the brief and
  the five files, before running a program, for every decision the brief states. The decision
  they all got wrong is the one the brief did not state.
- Where the plan came from: the brief, for every stated rule (leakcheck finds two rule phrases
  quoted back in trial 1 and nothing in trials 2 and 3, which is agents restating rules in
  docstrings, not a plan taken from prose); the shipped tree, for the one rule the brief left
  open - `pass_over` in the shipped `txn.py` runs a granted transaction's backlog inside the
  sweep that granted it, nested, and the agents kept that structure while fixing everything
  around it.
- Existing tactics and the one that failed in practice: A1, A2, A3, B2, C1, C2, C3, C4 as
  listed above; the one that failed was C1 on the resumption axis - `resume-order` and
  `resume-run` fence "on the spot" against "in grant order" and nothing fenced "nested" against
  "one line", because that reading was never written down (CLAUDE.md, 2026-09-07: a reading you
  cannot express is a reading you cannot test).
- Estimated solves out of 8 at the time: 2 to 5 in the metadata; realized 0.

### 2. Classification

| Failure mode | Evidence | Direction taken |
|---|---|---|
| The brief left a graded behaviour unstated | "When a sweep grants several, they resume in the order they were granted, one at a time, each running the steps it was holding until it is stopped again" does not say what happens to what a running transaction grants; the sealed model appends it to one FIFO line, the shipped `txn.py` runs it nested, and every trajectory chose nested | State the line. This is the defect RAISE-DIFFICULTY rule 2 forbids ("never create difficulty through ambiguity"); the 0 of 8 is a defect, not difficulty |
| A stated rule read two ways | "stands beside every claim held by every other transaction": per-claim or the held mark? Trial 2 measured the two readings apart on 5 of 300 programs and chose the held mark, as the model does | Say "the mark every other transaction holds", and note that `pin-lift` already fences the per-claim reading |
| `wait` line named "the mark it is asking in" | Read as the asked mark rather than the tested mark it moves 43.6 % of the population; `join-pair` fences it, and no trajectory misread it | Say "the mark the request is tested in" |

Measured with `authoring/lock-upgrade-deadlock/altmodel.py` (the sealed model with each reading
opened up by a flag; with no flag set it reproduces the model on every program) over the
verifier's own generator, 400 ordinary programs plus 8 reduced heavy ones:

| reading | first hand case | programs moved |
|---|---|---|
| nested resumption (what the trajectories built) | none | 83 of 408, 20.3 % |
| a batch granted mid-run goes to the front of the line | none | 52 of 408, 12.7 % |
| per-claim test instead of the held mark | `pin-lift` | 16 of 408, 3.9 % |
| `wait` shows the asked mark | `join-pair` | 178 of 408, 43.6 % |
| ring check after every resumed step too | `cut-again` | 44 of 408, 10.8 % |
| look again after a cut before the line runs | none | 0 - not separable on this population |
| sweep an item again after its own grants | none | 0 - a grant never makes a failed raise stand, since the cover only grows |

The heavy families cannot move under any resumption reading: in `crowd` every raise by the
crowd is granted on the spot and the 25 queued claims have no later steps; in `wide` the tail
transactions hold private items and the paired waiters have no later steps. Checked at reduced
scale in the same run.

### 3. The repair, and why it is not a hint

The brief now states the line: a granted transaction joins the back of one line; the line runs
once the step that filled it is over, every sweep of the step included, from the front, one at
a time, never interrupted; whatever a running transaction grants joins the back behind
everything granted before it; the line is empty before the service looks for a ring, after a
step and after a cut alike. It also says the test is against the mark each other transaction
holds, never the claims under it, and that the `wait` line shows the mark the request is tested
in. Every one of those is a statement of behaviour the sealed model already had, and none of
them touches the decisions the task rests on: the cover, the self-excluded test, hold-order
raises, the pin, the removal-defined relation, the victim key, the cut loop, the limit. A
low-effort agent that patches the shipped tree still keeps the conflict-edge relation, the
single mark and the single queue, and still fails `edge-miss`, `pin-fresh` and `raise-order`.

Fences added so the readings are named when they fail: `resume-line` (t2 frees kb for t4 while
t3 stands granted ahead of t4; the model runs t2's next step, then t3, then t4; nested runs t4 at
once, front-of-line runs t4 before t3) and `resume-shed` (an ending transaction's second item is
swept before the transaction its first sweep granted runs a step). Two cheats carry the readings
as the reference with one file swapped: `cheat-resume-nest.sh` and `cheat-resume-front.sh`,
emitted from `authoring/lock-upgrade-deadlock/readings/` by `emit_cheats.py`. The frozen-answer
forgery was regenerated for 27 programs by `emit_forge.py`.

### 4. Rebuild, from the earliest affected stage

Stage 2: contract unchanged in substance, two hand cases added additively (`build_gt.py`: 25
kept byte-identical, 2 added). Stage 3: environment untouched (`tests/pristine` diffed identical
to `environment/app_src`). Stage 4: reference untouched; it agrees with the model on all 27 hand
programs and 400 generated ones (`readings.py`). Stage 5: three passages of the brief rewritten,
the count 437 re-derived to 439, rule 10 of the frozen contract restated, the three metadata
explanations re-derived (27 hand programs, 36 cheats, 22 wrong readings, the two new fences).
Stage 6: every wrong reading in `cheat/` is now expressed as a reading and run through the hand
set; each is separated (table in `readings.py` output, recorded in "Validation status"). Stage
7: below.

### 5. The measured repair

See the validation table. The two readings the trajectories built are caught by `resume-line`
and move 20.8 % and 13.0 % of a 400-program population under the reference; no reading in the
cheat set survives the hand set; the reference scores 1 through the host trial and the no-op 0.

### 6. Cold self-attack after the repair

Read cold, the repaired brief gives me the textbook plan first and the removal definition
second, and my first implementation of the definition would try every live transaction and
lose the set to the limit; the line rule is now one sentence I would implement as a deque
without a second thought, which is the point - it was never where the difficulty was. What is
left is what the retained passing tasks rest on: a first plan that is coherently wrong in four
places the brief states, no per-decision feedback, and a fast path that has to be derived from
an invariant of the item. Honest reading of the three trajectories: each would pass this brief.
The realized rate is therefore likely to land high in the band, and the record says so rather
than claiming a 1-of-8 design that the evidence does not support.

## Quality review - 2026-09-11 (task name)

The repaired bundle went through the pipeline as `claim-raise-cut` on 2026-09-11 at 06:57:
structural checks, the AI check, similarity and reference verification all passed; the quality
review (model claude-fable-5-1, 07:03) failed exactly one blocking criterion, `task name`:

    'claim-raise-cut' is 3 words and kebab-case but uses the task's internal euphemisms
    (claim=lock, raise=conversion, cut=abort), so a reader scanning CI logs cannot tell this
    is a lock-manager deadlock task without opening files. Something like
    lock-upgrade-deadlock would be self-describing; the obfuscated vocabulary is only needed
    inside the instruction, not in the folder name.

Every other criterion the review lists passed. The repair is the reviewer's own suggestion,
`lock-upgrade-deadlock`: `[task] name` in `task.toml`, the task, authoring and probe
directories, every path in the authoring kit, and this file. Nothing the agent can see
changed - the slug appears in no shipped file but `task.toml`, which the environment image
does not carry - so the A2 tactic (the brief names no lock, conversion or deadlock) is
untouched, and the three trajectories show the agents naming the concept themselves in the
first minute anyway. The env-variable prefix `CRC_` in `tests/worker.py` and
`tests/test_outputs.py` is left alone: it is an override hook for the authoring harness, not a
name a reader meets. Recorded in `docs/QUALITY-REVIEW.md`, with a preflight warning that fires
when a slug shares no word with the task's tags; the retained bundles trip it too, and they
were accepted under the earlier reviewer, so it warns and does not error.

## Decisions and their reasons

- The resumption line is stated as behaviour (one line, back and front), not as a structure or
  a technique, and the model was not changed to a less obvious order: a rule chosen for being
  non-default would be difficulty through an arbitrary corner, which the doctrine rejects, and
  it would have moved frozen answers.
- The per-claim reading is stated closed even though `pin-lift` already fences it: the sentence
  "every claim held by every other transaction" literally suggested it, and a fenced ambiguity
  is still an ambiguity.
- The two equivalent readings (look again before the line runs; re-sweep after grants) are not
  fenced because nothing on the population separates them; the first is stated anyway, for
  free, and the second is a theorem of the cover growing.
- The forgery probe was regenerated rather than left at 25 answers, so it still proves what the
  verification explanation says: every hand case passes and the nonce population fails.
- A reading whose answer depends on iteration order gets a hand case anyway, and the report
  asks the shaped family to catch it: `cut-one-ring` finds "the first ring" from a set of
  names, so no fixed program can make the wrong ring come first in every process; `ring-pair`
  names the reading when it does, and the `ring` family of 40 nonce programs is the fence that
  never misses.
- Cheats are asserted by layer, never by reward alone (`cheat_report.py`): the named hand case
  must be among the failing ones, the limit must be what cut a slow reading off, the reap must
  have found the survivor, and the three channel probes that leave nothing readable are judged
  by the report itself trying the same writes as uid 1002.

## Validation status

All rows dated 2026-09-10 on the repaired build, re-run on 2026-09-11 after the rename where
marked; the rename touched `task.toml` (`[task] name`) and nothing else the verifier or the
agent reads. `host trial` rows are `authoring/lock-upgrade-deadlock/
host_trial.py` (tests/test.sh verbatim as root, uid 1002 for the worker, sealed directory, wall
clock, reap), not container evidence.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no Docker daemon in this session; `tools/imagecheck.py` clean (COPY audit, 16 files) |
| No answer leaked into agent image | passed | leak audit above; `deadfieldcheck` clean; `tests/` and `solution/` never copied |
| host trial oracle = 1 | passed | 30 passed, worker exit 0; re-run 2026-09-11 from the renamed authoring directory, 30 passed |
| host trial nop = 0 | passed | the shipped tree is cut off by the limit (exit 124) on the heavy families; 1 passed, 29 errors |
| host trial, both correct variants = 1 | passed | `variants/ok-whole-ring` (Kosaraju over the whole relation whenever any row moved, no changed-root pruning) and `variants/ok-set-marks` (exclusion sets, join by closure, holders in sets behind an overlay), 30 passed each; both also agree with the model on 27 hand and 300 generated programs in-process |
| Cheats all score 0, by the named layer | passed, 36 of 36 | `cheat_report.py`: 18 wrong readings caught by the hand case named for them; 4 wrong readings (`edge-and`, `edge-conflict`, `pin-bar`, `raise-ask-mark`) cut off by the limit on the heavy families first and caught by their hand case in-process; 4 right-and-slow readings cut off by the limit; `cut-one-ring` order-dependent (below); 10 probes each by its channel - seal unreadable as uid 1002, forgery passes all 27 hand cases and fails the nonce test, hang and plant cut off, malformed and altered records named by the grader, writes to `/tests` and `/logs/verifier` denied as uid 1002, 878 survivors reaped, all 439 records present after the shrink |
| `cut-one-ring` | order-dependent | it iterates a set of names, so which ring it finds first changes with the hash seed: `ring-pair` caught it in the readings harness, `cut-again` in the first trial, neither in the second, and the nonce `ring` family (40 programs, up to three rings each) caught it in every run (27 of 412 nonce programs in the first). The hand case stays; the report requires the nonce failure |
| readingcheck | passed | 22 readings, each separated by a hand case (`tools/readingcheck.py lock-upgrade-deadlock 200`, re-run 2026-09-11 at 100 rounds); `resume-nest` and `resume-front` by `resume-line` |
| readings against the population | recorded | `readings.py --per 40`: nested 20.8 %, front 13.0 %, conflict edges 27.5 %, join by rank 66.0 %, own claims counted 75.0 %, resume on the spot 46.8 %, cut youngest 26.0 %, drop clears 25.8 %, pin none 10.8 %, shed by name 6.5 %, raise order 3.5 %, cut-no-wake 2.2 % |
| difficultycheck | 99 / 100, in band (re-scored 2026-09-11 under the new slug) | measured tree 334 environment lines, 5 editable files, 452 reference lines, 36 cheats, 2 variants; solvability 6 of 7 because the honest estimate is 4, above the 1-to-3 the rubric rewards |
| preflight | no errors | re-run 2026-09-11 after the rename: warnings only - entry points `run.py` calls (`step`, the `Trace` methods) reported as uncalled inside the tree, the verifier executes agent code (the probes exist for that); the new slug-versus-tags warning is quiet on `lock-upgrade-deadlock` and fires on a copy named `claim-raise-cut` |
| extraneouscheck, hintcheck, catcheck, deadfieldcheck, solvecheck, imagecheck | passed | |
| simcheck | NEAR on Dockerfiles and test.sh | the house harness files shared with retained bundles; this bundle cleared the platform's similarity screen in that form; conceptual axis clean |
| structcheck | passed | |
| textcheck vs `note-carry-forward` | three findings | burstiness 0.805, paragraph sd 37.2, type-token 0.258; the brief as uploaded measured 0.818, 29.4 and 0.273 on the same axes and cleared the platform's AI screen, so the edit moved none of them by more than the noise between two readings |
| leakcheck on the three trajectories | two rule phrases in trial 1 | rules restated in the agent's docstrings; the task was not solved, so no plan leaked |
| worker timings | measured | `time_all.py`, the worker alone over 439 programs, one CPU of this host: reference 5.5 s; right-and-slow `whole-rebuild` 180.2 s, `all-live` 180.6 s, `per-participant` 172.1 s, `candidate-verify` 241.6 s; variants `ok-set-marks` 10.5 s, `ok-whole-ring` 9.2 s; the prose quotes these numbers |
| package + zipcheck | passed | `tasks/lock-upgrade-deadlock.zip`, 87 entries, zipcheck clean, rebuilt 2026-09-11 after the rename; the earlier `claim-raise-cut.zip` is removed |
| `harbor check` rubric | not run | no API key here |

## Open questions and next steps

- Run the platform probes on this build. The exit gate of the recovery is external.
- If the difficulty probe returns 8 of 8: the next lever is a measured C3 family, not more
  rules. Trial 1 found it on its own: one item with thousands of raises stuck behind one
  blocker, where answering the removal question per requester costs the square of the queue
  (its first engine took 67 s on that shape, 0.25 s after grouping raises by held and tested
  mark). The reference and the sealed model both answer per requester today, so shipping that
  family means rebuilding both around the grouping invariant and re-freezing nothing (the hand
  answers would not move). Recorded here as the lever, not built, because it changes what the
  task is about only for agents that already have the semantics, which is the case the current
  evidence says is likely.
- If it returns 0 of 8 again: the diagnosis above is wrong somewhere, and the next trajectory
  analysis must start from the sealed model, reading by reading, with `altmodel.py`.
