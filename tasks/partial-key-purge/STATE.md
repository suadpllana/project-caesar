# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one — anything not written here is lost.

## Current stage

`Stage 7 — Final gates and delivery` (2026-09-22). Stage 1 closed with originality 100 and
difficulty 100; Stage 2 froze the contract below; Stages 3-6 built and validated the bundle; the
final container sweep and packaging are recorded under Validation status.

## Assistant's assigned role

No role was assigned verbatim; the contributor's prompt made the assistant "the engineer, probe,
reviewer, and solver" and left the domain role to the assistant. Chosen role: a database engineer
who works on a relational engine's referential-integrity layer (match rules, referential actions,
constraint timing) and on the delete-impact tooling built over it. Later sessions resume in it.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): authored-on-top, in-house engine
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? not applicable; identifiers are written in a legacy register from the start
- Proper-noun sweep done? not applicable, nothing vendored
- Upstream-diff check: not applicable, there is no upstream

## Task summary

`/app` is a small row store with composite foreign references. A script declares tables, keys
and references (each with a match rule of simple, full or partial and a delete action of
cascade, restrict, noaction or setnull with an optional column list), gives rows, and then runs
deletes, dumps and audits. The shipped referential pass treats every reference as simple and
cascades row by row as each referenced row goes; the shipped audit replays a delete per row. The
agent rewrites five modules so that deletes remove, clear and refuse exactly as the brief states,
and so that the audit, which reports for every row what deleting that row alone would do, runs
inside the stated limit on stores of about thirty-six thousand rows with revision chains six to
seven thousand deep.

## Why it is hard

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan: the natural plan is the engine every solver knows (a null switches a reference off, each lost parent settles its children at once, clearing takes effect as it happens, the audit replays a delete per row), and the stated rules make a row's fate depend on a whole set of rows (a partial row goes only once every row it matched is gone, rows matching one another keep each other); once that is implemented the audit is correct and far too slow, and the structure that makes it fast (removal sets are the subtrees of one ownership tree) holds only outside loops of mutual matches and has no place for rows of tables with two cascading references, so the second discovery forces a new audit design, not a patch.
- Tactics making that true: A1 (the familiar engine treats half-null rows as inert and cascades row by row), A2 (least fixed point, ownership tree and lowest common owners are described, never named), A3 (a retained-set computation is wrong on loops and has no place for two-cascade rows; replay is right but slow; they must be joined), B2 (match rules, fixpoint, pre-statement matching, column-list clearing, restrict against noaction timing, end checks and refusal naming all hold at once), C1 (both too much and too little removal are graded, and plain simple cascades must stay exactly right), C3 (the correct per-row replay is quadratic on the deep stores), C4 (every line of every script over hand scripts and a nonce population shaped around half-null rows, shared matches, loops and deep chains)
- Assistant's attack on the plan: my own first plan was the recursive cascade taught the three match rules plus an audit that replays each delete on a copy; it is wrong on pre-statement matching (clearing fed back), on loops (rows matching each other were removed with their outside support), on restrict against noaction, and it cannot finish the deep stores; my second plan, a standard dominator tree over the match graph, is wrong on loops (reachability frees what the least fixed point keeps) and misses the two-cascade rows entirely
- Estimated solves out of 8: 2 (range 1-3)
- Difficulty record score: 2026-09-22, 100/100 IN BAND on the first complete record; revised the same day when insert and update were dropped from the statement set (wrong reading on unique-key swaps replaced by one on key columns cleared to null, expert path step replaced by end-state checks after clearing, second discovery restated with the two-cascade rows as unions of chains); re-scored 100/100
- Difficulty score anchor: not yet set (set at first complete submission)
- Score history: 2026-09-22 originality 100 (DISTINCT), difficulty 100 (IN BAND), revised record 100; at the final gates, originality 100 with the built instruction (nearest brief alias-settle-report, cosine 0.233, shingle 0.000 over 13 documents) and 100 with `--corpus` over 20 historical briefs from git history (nearest reach-pair-sweep, cosine 0.208, shingle 0.003 over 33 documents); difficulty 100 on the measured tree (372 environment lines, 5 editable files, 554 reference lines, 34 cheats, 2 module-form variants)
- Leak audit: nothing. Rows carry only an id and values; the frozen store keeps rows by id and no index over values; no expected output ships; helper names never name owners, dominators or ancestors; the shipped audit is a replay of the wrong delete and confirms nothing
- Expert path: see authoring/partial-key-purge/difficulty.toml [plan].expert_path, nine steps from reading the shipped pass to joining the ownership tree with the loop replay
- Originality check: searched MATCH PARTIAL implementations (none implement its actions), composite-key half-null footguns, cascade-delete previews (Django's collector: one object, simple keys), retained sets and dominator trees (reachability, wrong on loops); nothing plans the task
- Distinctness record score: 2026-09-22, 100/100 DISTINCT; crowded archetype named: garbage-collector retained sets (Languages list), no Databases entry fits
- Nearest already-submitted task: reach-pair-sweep (loss of support propagated through references); separated on mechanism, substrate, graded output, failure mode and interaction

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): authoring/partial-key-purge/trace.md walks 5 test functions, 25 hand cases, 5 artifacts, the 180 s clock, the exit-status, output-cap and encoding conditions of tests/worker.py, the standard-library condition, and 20 rule rows of tests/seal/model.py; three NOT STATED found on the walk were fixed in the instruction (a run ending in an error counts as wrong; no package outside the standard library can be relied on; a restrict reference also fails by the end-state conditions); 0 NOT STATED left; `python tools/tracecheck.py partial-key-purge` clean (2026-09-22)
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 18 wrong readings written as whole solvers in authoring/partial-key-purge/readings.py, from the shipped engine (simple-for-all, row-by-row clearing), the model's prior (retained-set audit, reachability, restrict/noaction timing swapped), the four clusters (named rows not counted, cleared only if changed, held counts zero, name by row first, clear all columns) and the other parse of each rule (no self-match, fork needs both, full half-null accepted, key null allowed, end check before clearing, restrict only by losing, audit sums children); every one is ruled out by a quoted sentence and separated by a named hand case (tools/readingcheck.py: 18/18 separated, 0 BLIND, 0 equivalent); the survivors that agree with the reference on everything are the three correct implementations kept as variants
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all score 0 in the capped Docker trial; fraction matched on the 25 hand scripts and 300 small nonce scripts (authoring/partial-key-purge/shortcuts.py): shipped tree 4/25 and 45/300, constant 0/25 and 1/300, named-only 1/25 and 21/300, refuse-first 0/25 and 1/300, worked example replayed 0/25 and 0/300
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 180 s clock on the whole graded run; on the final images under 1 CPU and 2 GB, authoring/partial-key-purge/variants/chk (iterative dominators, Euler tour, replay below 2000 rows) ran it in 63 s (2.9x headroom), authoring/partial-key-purge/variants/walk (explicit chain walks instead of marks) in 48 s and the reference in 39 s; the per-row replay floor (authoring/partial-key-purge/time_naive.py, removal counting only, flat arrays) is 820 s for the three deep scripts on the host
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically (no fresh session: this session may not spawn one); every printed token of delete, dump and audit lines was put through the four clusters; three decisions were open and each got a sentence: whether a restrict reference can fail at the end state (sentence rewritten, hand case restrict-broken-by-clear added), whether a run that exits with an error but printed the right lines passes (sentence added), whether packages outside the standard library are there (sentence reworded after the walk found pytest in the verifier image); every other question was answered by a quote recorded in trace.md

## Verifier contract — FROZEN 2026-09-22 (end of Stage 2)

Frozen after the brute force (authoring/partial-key-purge/brute.py), the sealed model
(tests/seal/model.py), the reference (solution/) and a second correct variant
(authoring/partial-key-purge/variants/chk/) agreed on every script checked: 1500 shaped small
scripts plus 150 random ones for the model, 400 for the reference, 800 for the variant through
its replay path and 800 through its forced fast path, and model = reference = variant on 20
medium chain scripts and 3 deep ones. Changes from here need the contributor's approval.

- Artifacts the agent produces: `/app/db/match.py`, `/app/db/drop.py`, `/app/db/clear.py`,
  `/app/db/hold.py`, `/app/db/audit.py`. Nothing else is collected; the driver `/app/run_db.py`,
  the reader `/app/db/parse.py`, the store `/app/db/rows.py`, the printer `/app/db/say.py` and
  `/app/db/__init__.py` are the verifier's pristine copies. The driver calls
  `drop.delete(store, table, ids)` (returns `("ok", removed, cleared)` or
  `("refused", name, id)`) and `audit.audit(store)` (returns `(table, id, removed, cleared,
  held)` per row, in output order). Only the standard library is available at grading.
- Script grammar (one item per line, blank lines and `#` lines ignored; declarations, then rows,
  then statements):
  - `table <name> <col>...`
  - `key <name> <table> <col>...`
  - `ref <name> <table> <col>... -> <key> <simple|full|partial> <cascade|restrict|noaction|setnull> [<col>...]`
    (a column list after the action only for `setnull`; it names some of the reference's columns)
  - `row <table> <id> <value>...` with `-` for null
  - `delete <table> <id>...`, `dump <table>`, `audit`
  Guarantees: names distinct across tables, keys and references; ids positive and unique per
  table; the given rows satisfy every key (no null key column, no two rows equal on a key) and
  every reference (not broken; a reference that is not inert matches at least one row); a delete
  names distinct rows present at that point; no reference names a key of a table that has two or
  more cascade references.
- Semantics:
  - A reference is inert for a row whose referencing columns are all null, and under `simple`
    also for a row with any of them null. Under `full` a row with some but not all null is broken.
    Otherwise the row matches every row of the key's table whose key columns equal its non-null
    referencing columns, pairwise in order. A row can match itself.
  - A row loses a reference when it matched at least one row through it before the statement
    and every row it matched is removed. Matching always uses the values from before the
    statement.
  - Removed: the named rows and every row that loses a cascade reference; the smallest such set
    (rows that match only one another keep each other; a row matching itself keeps itself).
  - Cleared: every row not removed that loses a setnull reference has that reference's listed
    columns (all its columns when none are listed) set to null; clearing never changes the
    removed set. Every such row counts as cleared, even if the columns already held null.
  - Refused (nothing changes) when a row, removed or not, loses a restrict reference; or when,
    after removal and clearing, a remaining row is broken under a reference, matches no
    remaining row through a reference that is not inert for it (values after clearing, of both
    rows), or has a null in a column of a key.
  - Refusal names the failing key or reference declared first in the script and the smallest id
    of a row failing it.
- Output, one line per item, nothing else:
  - delete: `ok <removed> <cleared>` or `refused <name> <id>`
  - dump: `<table> <id> <value>...` per row, ids ascending, `-` for null (no line for an empty table)
  - audit: `<table> <id> <removed> <cleared> <ok|held>` for every row, tables in declaration
    order and ids ascending, each line what `delete <table> <id>` alone would give, counts
    included when it would be refused; the store is unchanged.
- What is checked: stdout of the pristine driver, one fresh interpreter per script, on every
  graded script equals the expected text exactly. Hand scripts (`tests/cases/`) against
  `tests/seal/gt.json`; a nonce population generated as root before the worker starts
  (`tests/seal/gen.py`: 30 scripts in each of ten small families and 3 `deep` scripts of about
  36,000 rows with four revision chains 6,000-7,000 deep) against the sealed model. The whole
  graded set runs in one worker under a 180 second wall clock, declared 1 CPU and 2048 MB.
- Tolerances: none; exact text.
- Ground truth, and where it lives: `tests/seal/gt.json` (hand scripts, built by the model and
  checked against the reference, the variant and the brute force); the nonce population is
  generated and answered inside the verifier by `tests/seal/`, which is chmod 700 before any
  agent code runs.
- Measured at freeze (this machine, Xeon 2.1 GHz, Python 3.11, fresh interpreter per script):
  start-up 26 ms per small script; per deep script the reference 2.7 s, the variant 7.5 s, the
  model 7.3 s; peak memory about 90-100 MB. The per-row replay floor (removal counting only,
  array-based, the fastest form of the naive family) is 820 s for the three deep scripts; the
  model's own correct replay extrapolates to about 730 s for one audit of the earlier,
  shallower deep shape. Container timings are re-measured at Stage 4.

## Decisions and their reasons

- Insert and update were designed and dropped before the contract froze (2026-09-22): they
  added end-state checks the delete already needs, one rule (unique keys at statement end)
  whose only interesting case needs a multi-row update, and roughly a thousand characters of
  brief, against a 10000-character cap, for no new interaction. Deletes, dumps and audits carry
  every interaction in the design record.
- Rows of a table with two cascade references (an OR of two loss conditions) are never
  referenced, by guarantee. With that, they are leaves: their removal is a union of two chains
  of the ownership tree. Allowing references to them makes the removal structure an AND-OR graph
  with no tree, which no expert path within ten hours covers.
- Key columns may be cleared, and the end check refuses a null in a key column. That gives
  setnull over an identifying column a defined meaning with one sentence rather than a
  declaration-time prohibition. Re-checking the rows that matched a row whose key was cleared is
  unobservable (the key always fails first in declaration order) and is kept only for fidelity.
- A row that matches itself through its cascade reference is a root of the ownership tree, not
  a loop member: nothing outside it can remove it and what its own delete removes is its
  subtree. Treating it as a loop made a whole chain one strongly connected component and the
  model quadratic (95 s per deep script) before the fix.
- The deep family was reshaped twice before the freeze, both times on a measurement: the first
  shape cut the chains with self-matching rows and pairs, so the mean removed set was 35 rows
  and an optimised replay could have fitted the clock; the current shape keeps four chains of
  6,000-7,000 deep with loops, pairs and guards in short documents and at the tail of one long
  chain, and the replay floor is 820 s for the three deep scripts.
- The clock is 180 s for the whole graded run, measured before freezing and re-measured on the
  final images: reference 39 s, walk variant 48 s, chk variant 63 s, replay floor 820 s (host). A variant that walks chains instead of summing marks also
  fits, so the brief and metadata claim only that clearing and refusal have to be read off the
  tree, not how.
- The worker never imports agent code and never stages the tree: root stages the pristine tree
  with the five files, root-owned and read-only, before the worker starts, and root writes the
  nonce scripts and their answers (the answers into the chmod 700 seal). The worker streams one
  JSON line per script, so a run cut by the clock still grades its hand cases individually.
- Boilerplate (both Dockerfiles, reap.py) was rewritten in this task's own terms after simcheck
  measured them at 0.99-1.00 against retained bundles; they now sit below the 0.75 line.
- textcheck against the retained briefs: no finding against 8 of 12 (publish-settle-order,
  token-seam-emit, guard-mark-unwind, expert-defer-shed, focus-return-point, scope-hold-release,
  share-register-screen, alias-settle-report); burstiness 0.814 is under note-carry-forward's
  0.824 floor and the two outliers' (1.009, 1.112), and the type-token ratio 0.310 is under two
  references', because a spec has to repeat its nouns. Left there rather than bend rule sentences.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | Docker 29.3.1 here; the test image builds with a local accommodation only (authoring/partial-key-purge/local_trial.py drops the apt step because deb.debian.org answers 403 to this sandbox); the shipped Dockerfiles are unchanged |
| No answer leaked into agent image | pass | tools/imagecheck.py assembles the image, 14 files, runs the four samples with the reference; tools/extraneouscheck.py clean |
| `harbor run -a oracle` = 1 | pass (docker, not harbor) | tools/docker_trial.py flow via local_trial.py, --cpus 1 --memory 2g: reward 1, 28 passed; harbor 0.23.0 is installed but was not run, because its build would hit the same blocked apt mirror |
| `harbor run -a nop` = 0 | pass (docker) | reward 0, 21 failed / 7 passed (the 4 hand cases the shipped engine gets right plus the 3 sealed-side checks) |
| Cheats all score 0 | see Stage 6 | authoring/partial-key-purge/cheat_report.py asserts the layer per cheat |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass with warnings | the unused-function warnings are false positives: the functions are reached through attribute calls (`parse.read`, `store.get`, `match.ups`), which the check's `(?<![\w.])` pattern does not count |
| `harbor check` rubric | not run | manual criterion-by-criterion review recorded under Stage 7 |

## Cold self-attack (Stage 7) - author-run, contaminated

The author wrote the sealed model and the reference before this pass, and this session may not
start a fresh one, so this is not a cold solve and is not reported as one (CLAUDE.md: a
self-probe reported as cold by a contaminated author is worse than none). What it can still
measure: whether the brief alone fixes the semantics, and where the plan the brief induces fails.

- Setup: instruction.md and environment/app_src copied to a scratch directory; the first plan
  written down before any code (match per null pattern with indexes; counters for the removed
  set on pre-statement values; clearing after; restrict on loss, everything else at the end;
  naming by declaration then id; audit by running the delete plan per row), then implemented in
  fresh code from the brief's sentences without opening tests/ or solution/.
- Semantics: the brief-derived implementation agrees with the brute force on 600 generated
  scripts across all ten small families and the random fuzz, so no graded rule needed the model
  to settle it.
- Where it fails: `deep.txt` does not finish in 300 s (it prints nothing; the first statement is
  an audit), against 180 s for the whole graded set. The plan is right everywhere and fails the
  scale gate, which is where the design puts the second discovery. It is the same family as
  `cheat/cheat-replay-audit.sh`, which passes every hand case and is stopped by the clock.
- Rules confirmed independently: every rule could be confirmed against the brute force on small
  stores; none could be confirmed about the audit's fast path except by building it.

## Manual quality review (docs/QUALITY-REVIEW.md), 2026-09-22

- Instruction and verifier agree both ways: authoring/partial-key-purge/trace.md walks every test
  function, hand case, worker condition and model rule to a quoted sentence (tracecheck clean);
  every rule in instruction.md has a hand case or a generated family that exercises it.
- Collected files named with absolute paths (instruction.md paragraph 2); the result shapes are
  fixed by the pristine driver and printer, which the brief says are put back as shipped.
- Boundaries: removed counts include the named rows; cleared counts rows, once each, even when the
  columns were already null; refusal ties break by declaration order then smallest id; an empty
  table dumps nothing; audit lines run tables in declaration order and ids ascending; held lines
  still carry their counts. Each has its sentence and a hand case.
- Counts re-derived from the code after the last change: four sample scripts; about 36,000 rows
  per deep store (deep.txt 36,066; graded 35,900-37,200); chains 6,000-7,000 deep; three deep
  scripts; 300 small nonce scripts plus 25 hand scripts ("a little over three hundred"); 180 s;
  the worked example's third line `ok 2 0` shipped and `ok 3 0` correct.
- Prose: textcheck findings recorded under Decisions; no run of same-opener sentences on
  re-reading; each requirement stated once.
- Verifier rigor: outputs of real runs compared with sealed answers; test_outputs.py opens with the
  frozen contract and sections its tests; the nonce population and the model are deterministic
  across hash seeds (checked); the one clock is the stated execution limit.
- Environment hygiene: environment/Dockerfile copies app_src only; test dependencies are baked in
  tests/Dockerfile with == pins; no apt pins; every path named in the brief exists
  (tools/imagecheck.py ran the four samples in the assembled image).
- Solution: solve.sh copies the five reference modules and runs two samples; nothing is echoed.
- Anti-cheating: no answer in the image; exact comparison; 34 cheats including a gt.json forgery,
  a corrupted report and the reward-tamper probes (results under Validation status).
- Metadata: Software / Databases; five specific tags that do not restate the label; the
  difficulty explanation names the steps that fail and the legacy-register naming as a choice;
  the solution and verification explanations describe the built bundle; relevant_experience is
  grounded in the work this bundle demonstrates; 10 expert hours matches the design record.

## Harbor

`harbor run -p tasks/partial-key-purge -a oracle -e docker -o <scratch>` (harbor 0.23.0) built the
agent image and ran the oracle agent, then failed building the verifier image: `apt-get update`
got `403 Forbidden` from the Debian mirror (egress policy of this sandbox, recorded in the proxy's
relay failures). Not retried. The equivalent two-container flow (tools/docker_trial.py through
authoring/partial-key-purge/local_trial.py, which drops only the apt step locally) is the
container evidence recorded above.

## Infrastructure notes (Stage 0)

- Docker: the daemon was not running; started with `dockerd` in the background. Pulling
  `python:3.12-slim` from Docker Hub failed with 403 on the blob CDN
  (`production.cloudfront.docker.com`, egress policy); not retried. Pulled
  `mirror.gcr.io/library/python:3.12-slim` and tagged it `python:3.12-slim` locally.
- Harbor: absent; installed with `uv tool install harbor` (0.23.0).

## Open questions and next steps

- Stage 3: shipped wrong modules and samples, Dockerfiles, test.sh/worker/reap/make/grader,
  hand scripts and gt.json, solve.sh; host trial and Docker oracle/nop.
