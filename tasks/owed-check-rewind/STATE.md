# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Final gates and packaging`. The two-container gates cannot be run in this session:
Docker's daemon starts, but the egress policy denies Docker Hub's blob CDN
(`production.cloudfront.docker.com`, HTTP 403), so no base image can be pulled and no image can be
built. Everything else has been run - see the validation table, and read every `host trial` row
as host emulation (`authoring/owed-check-rewind/host_trial.py`, which runs the real
`tests/test.sh` as root with the privilege drop, the clock, the sealed directory and the reaper)
rather than as container evidence. The platform's easiness probe has not run against this build.

## Assistant's assigned role

You are a database engine engineer who has worked on the statement layer of a relational engine:
constraint checking at the row, at the end of the statement and at commit, deferrable keys and
checks with SET CONSTRAINTS, referential actions and their order, and savepoints as marks in an
undo log. You know that what the standard says about when a constraint is checked is not what
every engine does, and that the owed checks of a transaction are state a rollback has to restore,
not something that can be read back off the rows.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, seeded from `prompts/databases.md`; no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree is
  written here, not degraded from a source; identifiers are chosen in the legacy register directly
- Proper-noun sweep done? No product, project or company name is to appear in the agent-facing tree;
  the domain words that remain (check, key, savepoint, deferred) are the ordinary vocabulary of the work
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the statement executor of a single-session relational store: a program declares
tables, row checks and foreign keys with a referential action, lists committed rows, and runs
transactions of inserts, updates, deletes, savepoints, releases, rollbacks to savepoints and mode
changes. The executor prints one line per statement: `ok` with the owed-check entries the
statement removed and added, `raise` naming the constraint, table and key, `error`, `aborted` or
`rollback`. The shipped executor implements the textbook plan: it checks everything over the
tables at the end of each statement, recomputes the owed checks from the rows, and copies the
database at every savepoint. The specification it has to meet keeps the owed checks as a ledger
that only a later look at an entry's own row or key changes, that a rollback to a savepoint puts
back exactly as it stood, entries in their old places, and that check points walk in declaration
order; row checks run at the write, restrict at the delete and key checks at the end of the
statement; cascades walk depth-first, whatever the key's mode. The agent fixes six files under
`/app/tx/`; the frozen half is the parser, the catalog, the line writer and the driver.

## Why it is hard

The first plan is the shipped one and it is wrong at the first rollback; the rule that replaces
it makes the owed checks history, and the programs a savepoint-per-statement client sends make
every copy of that history quadratic.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the prior and every course on transactions say owed checks are the constraint violations of the current rows, so a rollback restores the rows and recomputes them, and a savepoint is a copy; here an entry is changed only when a statement end looks at its own row or key, so an entry mended from elsewhere stays owed, a rollback must bring back entries cleared since the savepoint at the place they held, and a check point names the first owed entry in declaration order, which is not the newest violation or the first violating row; and the savepoint-wrapped and bulk-load programs make the copying plan quadratic, so the state layer has to be rebuilt as an undo log that restores entries, places and modes as exactly as the copy did, while row checks at the write and key checks at the statement end run on that same log.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, B2, C1, C2, C3, C4 - A1 the shipped executor is the textbook plan and it is wrong; A2 lazy mending, the causing side of a key violation and the place a rolled-back entry returns to are stated as behaviour, never as a structure; B2 about fifteen rules hold at once and several change what another prints; C1 both sides of every fence are graded; C2 no correct output ships and real engines judge and name differently; C3 savepoint-wrapped and bulk-load programs put copying and scanning implementations over the clock; C4 every line of every program is compared exactly against a population generated after the agent has finished.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was to keep the shipped shape - apply the writes and cascades, check every constraint over the tables at the end, keep the deferred violations as the set of rows that now violate, copy the database at each savepoint and recompute the set after a rollback. It is wrong three ways: an entry mended by inserting its missing key elsewhere stays owed until its own row is looked at again, so the owed set is not a function of the rows and a rollback past a check point brings back an entry whose row is fine; a check point names the first owed entry in declaration order and then in recording order, which after a rollback is the entry's old place and not its newest one; and on the savepoint-wrapped programs the copies are quadratic, so the state layer is rebuilt as an undo log, and that log has to restore every entry at its old place, drop every entry recorded since, and restore the modes, which is where an undo that re-adds a cleared entry at the end goes wrong. My plan after reading the rules was right in outline and wrong in two structures: where checks run inside a statement, and what a rollback restores.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop, one
  warning (resource gate declared but not measured). The gate was measured at Stage 2 and the
  record now says so. Stage 7 re-run on the built tree: 100/100, in band, no warnings - measured
  413 environment Python lines, 6 editable files, 423 reference lines, 53 cheats (39 semantic),
  2 variants.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 difficulty
  record 100 (design) and 100 (built tree); originality record 100 at Stage 1 and 100 with the
  built instruction
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": the sample programs ship
  without their correct output. The brief quotes one line of `progs/small.txt`; measured against
  all 39 wrong readings, that line decides one (`name-children`, how a key left behind is named,
  which the definitions state in a sentence of their own), three more differ only on unquoted
  lines of a file that ships without output, and 35 print `small.txt` identically. The shipped
  owed set is recomputed and ordered by key, so nothing orders entries by recording or remembers
  them across a rollback; nothing prints or stores a count of owed entries; the catalog carries
  only declared flags, never the modes in force, the ledger or a touch order; the key index the
  fast path needs is not shipped. `tools/onelinecheck.py` over `authoring/owed-check-rewind/decisions.py`:
  of four graded quantities only "does a check point raise" has a short rule (a violation that
  exists now is owed by some entry either way); which entry it names, how many entries a
  statement adds and how many a rollback brings back have none at depth two.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped programs and map which module parses, writes, checks, owes and restores; move row checks
  into the write path and restrict into the delete; walk referential actions depth-first in
  declaration order over the rows holding the key when each constraint is reached, recording the
  order rows and keys are first touched; rebuild the owed checks as a ledger of entries per
  constraint and row, or per constraint and key left behind, ordered by declaration then recording,
  changed only when a statement end looks at a touched row or key; settle set immediate and commit
  by walking the ledger in order, raising on the first entry still violated and changing nothing
  when one raises; replace savepoint copies with an undo log over rows, the key index, ledger
  entries with their places and modes; time the scale programs and replace table scans with the
  key index.
- Originality check: searched 2026-09-22. What exists publicly is the PostgreSQL manual for SET
  CONSTRAINTS, SAVEPOINT and ROLLBACK TO SAVEPOINT (a set immediate is retroactive; a rollback
  restores the transaction state) and its after-trigger queue in trigger.c (the deferred event list
  is truncated and fired events are un-marked when a savepoint is rolled back); SQLite's foreign key
  source, which keeps deferred violations as one counter saved and restored by savepoints and so
  can name no row and no order; Apache Derby DERBY-6670, a bug where violation information was lost
  when a dropped table came back through a rollback to a savepoint; blog posts on deferrable keys
  that stop at "checked at commit"; a Django thread on keys not checked at the end of nested atomic
  blocks. None reports owed checks per statement, keeps mended entries owed, names a violation from
  its causing side under a stated action walk, or restores an order a later check point walks.
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml, at
  Stage 1 before the difficulty record, again once instruction.md exists; every attempt's score,
  and the crowded archetype named - docs/ORIGINALITY.md): attempt 1 on 2026-09-22 scored 100/100,
  distinct, no hard stop; tags overlap nothing in the ledger, the substrate reuses no earlier
  substrate, the mechanism sentence is 0.14 cosine from its nearest ledger entry
  (scope-hold-release). Re-run with the built instruction: 100/100; nearest instruction in the
  corpus of 13 is slab-fold-scope at cosine 0.238 and shingle 0.010, against ceilings of 0.28 and
  0.05. Crowded archetype named: write-ahead log and crash recovery (savepoints and partial
  rollback belong to recovery), on the list, with the departure that there is no log, no crash and
  no second session and what is graded is the ledger of owed checks and its order.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag),
  what overlaps, and which of the five surfaces separate them: focus-return-point. What overlaps,
  stated at its strongest: both keep bookkeeping whose effect is deferred to an outer commit, and
  both need a nested abort to restore that bookkeeping as it stood rather than recompute it. All
  five surfaces separate: mechanism (focus restoration against owed constraint checks), substrate
  (widget toolkit against relational statement executor), graded output (focus holder per event
  against a ledger change or a raise per statement), failure mode (immediate or wholly deferred
  focus effects against recomputed owed checks and database copies), interaction (instance-bound
  requests against deletion history, against savepoint restore of an ordered ledger against
  declaration-order check points).

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): authoring/owed-check-rewind/trace.md walks 105 graded rows - the four test functions, the comparison, all 50 hand programs, the six artifacts, the overlay, the clock and every rule the sealed model applies, cited by line - with 0 NOT STATED; `python tools/tracecheck.py owed-check-rewind` is clean (its one note is that readings are cited by hand, which they are).
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 39 wrong readings, each the reference with one decision changed, built by authoring/owed-check-rewind/emit.py; `tools/readingcheck.py` separates all 39 with the 50 hand programs, and `cheat_report.py` asserts each one is caught by the hand program named for it (0 findings). None survives the published evidence either: the worked example decides one reading, `name-children`, and the rule it decides is stated in its own sentence.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all 0. The shipped tree (nop) is killed at the 60 s clock with no record, and without a clock prints a wrong line in 23 of 50 hand programs and 127 of 144 sampled generated ones; constant `ok` fails 44 of 50 hand and 144 of 144 sampled; the positional prior made whole (owed checks recomputed from the rows, `cheat-recompute-ledger`) moves 63 of 144 sampled and is caught by `rewind-cleared-back`; the replayed answers (`cheat-forge-hand`, carrying gt.json verbatim) pass all 50 hand programs and fail 54 of 144 sampled generated ones.
- Independent implementation behind every tolerance and limit (path, measured headroom): there is no tolerance, only string equality, and the model, the reference and the two correct variants written apart (authoring/owed-check-rewind/variants/ok-journal, ok-queue) print identical lines on 1,320 generated programs over four seeds and all 50 hand programs. The one limit, 60 s on stage one, has the variants at 13.8 s and 7.8 s per 330-program population in process against 8.5 s for the reference, and the whole host-emulated stage one for the reference at 7 to 8 s of a 14 s trial; the exactly-correct naive executors need 73 s (scan) and 168 s (copy) on one wrap program and 79 s (ledger copy) on one load program, and each scored 0 at the clock in the host trial.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, not a fresh session (no subagents, by instruction, and the author wrote the model first), and every candidate was measured as a reading on generated programs before deciding. Four decisions were open and each now has a sentence and a hand program: whether a rollback lists an entry it only moved (moved 83 of 324 generated programs; "An entry in the ledger both before and after a statement is in neither list, even if its place has changed", `replace-place`); whether a deferred key's cascade or setnull waits with its check (48 of 216; "in declaration order and whatever their modes", new case `action-deferred`); whether a row written again while still violating is owed afresh (26 of 216; "An entry that is still a violation stays where it stands", new case `rewrite-keeps-place`); whether `set C immediate` on a constraint that is not deferrable is an error (10 of 216; "In any `set`, ...", new case `set-immediate-nondeferrable`). Four more were checked and found decided already: a raising `set` or a `key` raise aborts (caught by `failset-atomic` and `key-dup`), holders go in increasing key order (`walk-touch-order`), and a check point names the first entry still violated, not the first entry (seven cases).

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22, before any environment editable file or reference line existed. The model and
two correct executors written apart (`authoring/owed-check-rewind/variants/ok-journal`, a closure
journal with a bisect-sorted ledger; `.../ok-queue`, an append-only event queue with a kill log)
printed identical lines on 660 generated programs over two seeds and all 47 hand programs of the
time before the freeze. The fifteen graded decisions are restated at the head of
`tests/test_outputs.py`, which is the file a reviewer reads.

- Artifacts the agent produces: `/app/tx/heap.py`, `/app/tx/act.py`, `/app/tx/chk.py`,
  `/app/tx/owe.py`, `/app/tx/sp.py`, `/app/tx/sess.py`. Nothing else is collected; the verifier
  lays those six over its own pristine copy of the tree, so the driver `run_tx.py`, the parser
  `tx/prog.py`, the catalog `tx/cat.py` and the line writer `tx/say.py` are always the shipped ones.
- What is checked: the printout of every graded program, one line per statement, compared
  exactly. 50 enumerated programs against `tests/seal/gt.json`, frozen from the model; 330
  generated programs (36 of each of nine small families and 3 of each of two scale families)
  against the sealed model, which must itself still reproduce `gt.json` first.
- Tolerances: none - string equality per line. The one limit is the 60 second wall clock on the
  stage that runs submitted code, stated in the brief and measured against two independent
  correct executors and the exactly-correct naive ones.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory made `chmod 700` before the privilege drop.

### Changes after the freeze - test data and wording, never a decision

- `imm-order` was rebuilt because it did not separate the reading it was named for; its frozen
  answer moved (`raise cy a 1` to `raise dz b 1`) because its program changed, and the other 46
  answers held byte-for-byte through `build_gt.py`.
- The `walk` family generator was rebuilt around seven configurations, each the smallest schema in
  which one question about the walk has two answers; the family still yields 36 programs.
- The cold-reader pass (above) added four sentences to the brief and three hand programs
  (`action-deferred`, `rewrite-keeps-place`, `set-immediate-nondeferrable`). None changes a graded
  decision: each states what decisions 5, 8, 11 and 14 already said and what the model, the
  reference and both variants already printed. `build_gt.py` reported three answers ADDED and none
  MOVED. The restated decisions 5 and 14 at the head of `tests/test_outputs.py` were reworded to
  match, in the same number of lines, so no cited line moved.
- The reference was compacted from 464 to 423 lines (docstrings, and the timing lines of
  `solve.sh`); the only code change is `Act.__init__` calling `start()`. Agreement re-run after it.

### The fifteen graded decisions

1. Key: an insert of a present key raises `key` on it at once; an update or delete of a missing
   key does nothing.
2. Check predicates: notnull is violated by null; min N by a value below N, never by null.
3. Key predicates: a child row whose column is not null and names no parent row; a parent key
   left behind when no parent row has it and some child still holds it.
4. Row checks at the write: each insert, update and setnull checks the row at once against every
   immediate check of its table, in declaration order.
5. The action walk: keys referring to the table in declaration order, whatever their modes; rows
   holding the key when that key is reached, in key order; cascade depth-first; setnull writes;
   restrict raises on the deleted key at once; noaction nothing.
6. Key checks at the statement end: immediate keys in declaration order over rows written and
   parent keys deleted, first-touch order; first violation raises, named child row or parent key.
7. A statement that raises leaves nothing behind and aborts the transaction.
8. Owing: at a statement end each deferred constraint judges the rows and keys the statement
   touched - gains an entry when violated and not owed, loses it when owed and not violated,
   keeps it in place when owed and still violated; nothing else changes an entry, so a row
   mended from elsewhere stays owed.
9. Ledger order: declaration order, then the order entries were made.
10. Check points: set immediate and commit walk the entries they cover in ledger order; the first
    still violated raises and nothing changes (a commit also rolls back); otherwise all are
    removed and listed.
11. Modes: declared modes at every begin; set changes deferrable ones; naming a non-deferrable
    constraint in any set is an error; `all` covers deferrable ones only.
12. Savepoints: rollback to S restores rows, ledger (membership and every entry's place) and
    modes as when the latest S was made, keeps S, drops later ones, ends an aborted state;
    release S drops S and every later savepoint.
13. Errors and the aborted state: unknown savepoint names are errors; an aborted transaction
    prints `aborted` for everything but rollback, rollback to and commit; commit there rolls
    back and prints `rollback`.
14. The listing: an ok line lists removed entries in the order they stood, then added entries
    in ledger order, by membership - an entry there before and after is in neither list; commit
    and rollback remove every entry.
15. The clock: the whole graded set inside 60 seconds on the stage that runs submitted code.

### The resource gate, measured 2026-09-22 before any prose depended on it

Per scale program, on this machine, with exactly-correct naive executors built on the model
(scratch timing, every one agreeing line for line with the model on smaller programs first):
`wrap` - model 0.61 s, children found by scanning 73 s, rows and ledger copied at every
savepoint and statement 168 s, rows undone but ledger copied at each savepoint 3.3 s; `load` -
model 0.98 s, scanning 1.0 s, ledger copied 79 s, everything copied 308 s. Every naive family is
over the 60 second clock on a single program of one family, and the graded set holds three of
each. Final numbers per 330-program population, in process: reference 8.5 s, ok-journal 13.8 s,
ok-queue 7.8 s. The three exactly-correct cheats built on the reference (`slow-copy`,
`slow-scan`, `slow-ledger`) are killed at the clock in the host trial.

## Stage 7 re-attack

Read cold, the brief hands over the rules and nothing else, and the first plan it supports is the
shipped one repaired rule by rule: move the row check into the write, restrict into the walk,
name the left-behind key on the parent side as the worked example shows, and keep recomputing the
owed set from the rows. That plan survives every hand program that has no savepoint in it and
fails the first one that rolls back past a check point, because the entry that comes back is one
no scan of the rows can see. The second plan - snapshot the ledger with the rows - is exactly
right and dies at the clock on both scale shapes. What remains is the structure: one journal
restoring rows, the holder index, entries with their numbers and modes, with the ledger's order
computed from what the journal restores.

Are the load-bearing facts still distributed? The catalog exposes only declared flags; the
ledger, the touch order and the modes in force live nowhere in the frozen half. Has the instruction
come to telegraph the method? It states the limit and the input scale, as a measured C3 must, and
never an index, a journal or a key; the four sentences the cold-reader pass added state behaviour
(what is listed, when an action runs, what an entry keeps), not representation.

The self-probe proper was not run, and is recorded as not run: the author wrote the sealed model
before the environment existed, so a cold solve would measure memory, and a self-probe reported
as passed by a contaminated author is worse than none. The reading separations, the layer
report, the no-short-rule result and the measured clock stand in its place.

Estimated solves out of 8 after the re-attack: 2 (honest range 1 to 4).

## Decisions and their reasons

- **Software / Databases.** The graded work is a relational statement executor: constraint timing,
  deferred checking, referential actions and savepoints. `delta-view-retraction` is the other task
  under this label and grades incremental aggregates; none of its substrate or tags is reused.
- **One session, no concurrency.** Deliberate, and what keeps the task off the crowded half of the
  Databases list (MVCC, isolation, locking).
- **Owed checks change only when a statement end looks at their own row or key.** This is the
  rule that makes the ledger history rather than a function of the rows, and it is what a real
  engine's deferred queue does: a queued check is not withdrawn because something elsewhere fixed
  it; it is judged when it is next looked at.
- **A key violation is named from the side that caused it.** A child written against a missing key
  is named by the child row; a parent deleted while still held is named by the parent key. Two
  children holding one deleted key are one entry, not two. Real engines report both forms.
- **Row checks at the write, restrict at the delete, key checks at the statement end, actions
  whatever the mode.** This is what practitioners meet in real engines (PostgreSQL defers only the
  check of a deferrable key, never its action) and what the standard's single "end of statement"
  hides.
- **The listing is by membership.** A rollback that moves an entry back to its old place lists
  nothing for it; the place shows up at the next check point, which is where it is graded.
- **The brief was split into shorter sentences** after `tools/textcheck.py` measured it against
  every retained brief: short sentences 13% to 29%, burstiness 0.721 to 0.761 (retained passing
  briefs range 0.601 to 1.112). No rule was removed or reworded in meaning.
- **Both Dockerfiles were rewritten** after `tools/simcheck.py` found `environment/Dockerfile`
  byte-identical to three retained bundles; one HIGH (0.591, a five-line file) remains.
- **Environment tooling note.** Docker starts in this session, but the egress policy denies Docker
  Hub's blob CDN (`production.cloudfront.docker.com`, HTTP 403), so no base image can be pulled and
  `tools/docker_trial.py` cannot build. Container gates are replaced by a host emulation modelled on
  `authoring/publish-settle-order/host_trial.py`, reported as host emulation, never as container
  evidence. `harbor` is not installed and no API key is present for `harbor check`.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model vs two variants | pass | 1,320 generated programs over four seeds and 50 hand programs, 0 disagreements |
| Frozen answers additive | pass | `build_gt.py`: 3 added, 0 moved after the cold-reader pass |
| `tools/readingcheck.py` | pass | 39 readings, all separated by the 50 hand programs |
| `cheat_report.py` | pass | every reading caught by the case named for it; 0 findings |
| `tools/tracecheck.py` | pass | clean; 105 graded rows, 40 reading rows |
| `tools/onelinecheck.py` | pass | 1 of 4 graded quantities short (whether a check point raises), 3 not |
| `tools/forgecheck.py` | pass | `cheat-forge-hand` carries gt.json verbatim, passes all 50 hand programs, and scores 0 on the generated population |
| `tools/imagecheck.py` | pass | 16 files in the image; the reference runs all five shipped programs inside it |
| `tools/extraneouscheck.py` | pass | clean |
| `tools/deadfieldcheck.py` | pass | clean |
| `tools/catcheck.py`, `tools/hintcheck.py`, `tools/structcheck.py` | pass | none |
| `tools/textcheck.py` | pass with note | burstiness 0.744 and 28% short sentences; no finding against `expert-defer-shed` or `focus-return-point`, burstiness below some other single references, inside the retained range (0.601 to 1.112) |
| `tools/simcheck.py` | pass with note | one HIGH on a five-line Dockerfile; nothing conceptual |
| `tools/solvecheck.py` | pass | clean |
| `tools/originalitycheck.py` | pass | 100/100 with the built instruction |
| `tools/difficultycheck.py` | pass | 100/100 on the built tree |
| host trial oracle = 1 | pass | 53 tests passed, 14.3 s; stage one alone takes 7 to 8 s for 380 programs |
| host trial nop = 0 | pass | killed at the 60 s clock, no record |
| host trial cheats = 0 | pass | 55 of 55 trials as required (oracle, nop, 53 cheats); the three exactly-correct slow cheats and `recompute-ledger` die at the clock with no record |
| Isolation probes | pass | answer key: `PermissionError` on gt.json, `ModuleNotFoundError` on the model; privilege: uid 2201, `PermissionError` on the reward; grader rewrite and generator rewrite: `PermissionError`; shrunken `each` rewritten in scratch only, graded population intact; planted record overwritten by the real one; early exit with a planted record: 51 failures; spoiled record: no readable record; late reward: reaped before it wrote; uncollected file: no record, the overlay has no `tx/own.py` |
| host trial variants = 1 | pass | `ok-journal` 19.2 s and `ok-queue` 14.1 s per trial, 53 tests passed each |
| `preflight.py` | pass | no errors; 27 warnings, every one "defined but nothing calls it" on a method or module function reached through an attribute (checked by grep); the one real dead function, `Heap.cell` in the shipped tree, was removed |
| `package.py` + `tools/zipcheck.py` | pass | `tasks/owed-check-rewind.zip`, 100 entries, no STATE, authoring or cache files, no CRLF, both `.sh` entry points executable; zipcheck clean |
| Docker oracle/nop | BLOCKED | image pull denied by the egress policy in this session |
| `harbor check` rubric | not run | no API key; manual quality review instead |
| Easiness probe | PENDING | the platform's probe has not run against this build |

## Open questions and next steps

Packaged and recorded in `authoring/submissions.toml` as pending on 2026-09-22. Still open:
the real Docker oracle and nop gates (blocked here by the egress policy), `harbor check` (no API
key), and the platform's easiness probe. When the platform answers, record its verdict and any
flag with its wording in the ledger and here.
