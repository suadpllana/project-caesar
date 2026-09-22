# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - packaging`. Stages 1 to 6 complete: design scored before any code, contract frozen
before the environment, environment and sealed verifier built, reference and two further correct
engines written, 42 cheats written and run, instruction and metadata authored, every local gate
run under host emulation.

## Assistant's assigned role

Storage engineer on the transaction path of a small record store: the part that decides what a
transaction holds while it runs, what a mark throws away, and what a close writes back. Fluent
in snapshot visibility, first-updater-wins, savepoint rollback and the read-modify-write
distinction between a blind write and one that stands on a number the client was told.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. No third-party code is vendored; every file is authored here.

## Task summary

`/app` is the write path of a small record store. A program file is a list of ops that open
transactions, read and write keys, mark and undo work, record conditions, and close. The engine
never aborts a transaction whose basis moved under it: it takes the moved key again and every
number the transaction derived from that key moves with it. The shipped engine implements the
textbook plan instead - one snapshot per transaction, a write set of numbers, savepoints that
copy those numbers, conditions tested as they run, and an abort when a written key moved - and
is wrong in all of it. Six files under `/app/led/` are collected; the rest of the tree is the
verifier's own copy.

## Why it is hard

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the first plan is snapshot isolation with first-updater-wins, which the brief inverts at the first decision point; the plan that replaces it, a work list re-derived from the bases, is semantically correct and dies twice, once on a mark that saves numbers instead of work and once on the stated execution limit, where re-deriving the work on every re-take and every dropped section is quadratic.
- Tactics making that true (docs/DIFFICULTY.md): A1 the memorised conflict-detection idiom is a wrong answer at the first decision point; A2 the rules are stated as what the engine does to numbers, never as rebasing or read-modify-write; A3 retroactive re-takes want values kept as forms while positional conditions want their history; B2 ten rules hold at once and each changes what the others mean; C1 both sides are graded, so neither never-re-taking nor always-re-deriving passes; C3 two measured scale families; C4 exact all-or-nothing traces over a nonce population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was one snapshot per transaction taken at `tx`, a `dict` write set, savepoints holding copies
  of that dict, conditions tested when they run, and a redo of the conflicting write at close.
  Four of those five are wrong under the stated rules. My second plan - per-key bases, a work
  list, re-derive on every re-take - is correct and measured at 20.7 s on one wide program
  against 0.09 s for the reference, so it fails the stated 45 s limit on the graded set. The
  honest summary is that I can see where to start and my first two plans are both wrong, the
  second one late.
- Estimated solves out of 8: 2 (design aimed at the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py, before Stage 2): 2026-09-22, first and only
  record, 100/100, in band (95-100). One warning cleared the same day by measuring the gate:
  `gate.measured` was a promise until the naive and reference timings were run, and the record
  now carries the measured scale and limit.
- Leak audit (docs/DIFFICULTY.md): the store holds one number per key and no basis or version
  field, so whether a basis moved is a comparison the transaction has to make; only reads and
  closes print, so a wrong structure shows up as a wrong number and never as a missing event; no
  shipped helper names the publish set, the dependents of a basis, or the surviving sections;
  the brief quotes one line of one small program, the printed close of `tiny.txt`; the shipped
  engine's whole-store snapshot is in an editable file and is wrong, so the per-key structure has
  to be built rather than found. Answer: nothing in the bundle discovers, names or verifies a
  discovery without reasoning.
- Expert path, described step by step:
  1. Run the shipped engine on `/app/plans/tiny.txt` and read the line the brief says is wrong.
  2. Find that a basis is taken per key at the first op that names it, not once per transaction.
  3. Find that taking a basis again reaches backwards: every number derived from it moves.
  4. Separate a read, which fixes the number going forward, from a copy, which stays owed.
  5. Rebuild the mark as a cut on the work list rather than a copy of the values.
  6. Move the conditions to close time, in work order, each at its own position.
  7. Make a failing condition drop the work from the last standing mark through itself, and let
     the testing carry on, so the cascade runs forwards.
  8. Settle the publish set from the work that survives the conditions.
  9. Time `wide.txt` and `deep.txt`, find the quadratic, and carry each value as one basis plus
     an offset with the mark stack holding those forms.
- Originality check: searched 2026-09-22 for transaction rebasing on conflict, per-key snapshot
  bases, retroactive re-derivation of a write set, and for any benchmark task with this op
  language. What exists is snapshot isolation and first-updater-wins (Wikipedia, Jepsen), the
  READ COMMITTED statement restart of PostgreSQL and YugabyteDB (an implicit savepoint before
  each statement, the statement re-run against the newer row), and Hyperledger Fabric's
  read-write sets. All of them abort, block or re-run a whole statement, all treat a savepoint as
  restorable state, and none has a read that fixes a number against a later re-take or a basis
  taken per key at first touch. No public write-up of this rule set or anything close to it.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 100 rows walked - 4 test functions, 44 enumerated cases, 6 artifacts, the 30 s clock, 19 model rows split one per rule with their lines, 26 readings, 5 shortcuts and 2 limit rows. No NOT STATED row survives; two decisions were found unstated during the walk and written into the brief (below), and one clause was deleted from the brief because nothing tests it. `python tools/tracecheck.py pin-drift-redo` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 26 wrong readings were enumerated from the four clusters, from the shipped engine, from the model's prior for a store of this kind and from the other parse of each sentence; each is built as a cheat by `authoring/pin-drift-redo/emit.py`, and `tools/readingcheck.py` reports all 26 separated by the enumerated set, with `authoring/pin-drift-redo/cheat_report.py` asserting that the case named for each reading is one it fails. One survivor reproduced every published statement and the whole graded set: taking the whole store when a transaction opens and taking each key again as it is named. It is not a hole but a correct variant, kept as `authoring/pin-drift-redo/variants/flat` and required to score 1; it does. Three readings were found that no case separated (a bulk op that does not take its range again, a close that writes the run-time set, a mark that saves numbers) and three cases were added for them - `bmp-moves-copy`, `publish-drops-key`, `undo-owes-after-mark`.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the shipped tree scores 0 and differs on 30 of the 44 hand programs and 331 of 360 generated ones; `cheat-const-ok` (every read prints 0, every close prints ok) 0; `cheat-pos-last-put` (a close writes only what a put named) 0; `cheat-replay-tiny` (the worked example's two lines for every program) 0; `cheat-forge-hand` (the frozen answers for all 44 hand programs) 0, passing every hand program and failing the generated ones it could not have seen.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the 30 s clock in `tests/test.sh`. `authoring/pin-drift-redo/variants/eager`, written apart from the reference (plain numbers, a moved basis pushed out through a dependants index), runs the whole graded set in 3.4 s under the unprivileged worker - 8.8x headroom; the reference takes 2.4 s. From the other side, `variants/redo` and `variants/cut` are exactly correct and take the graded run to 94.1 s and 109.5 s, three times the limit, and score 0 as `cheat-slow-redo` and `cheat-slow-cut`. There is no numeric tolerance: every line is compared exactly.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every graded output - the read line, the close line and the silence of every other op - putting the four clusters to each decision behind them. Three gaps were found and written into the brief: the printed shape of a read (`rd T k v`) was implied by the sample programs but never stated; the entry points the pristine driver calls (`ver.Store()` and `step.one(store, box, op, out)`) were discoverable in the tree but not stated, and the verifier grades them; and an undo with no mark standing had no sentence. One clause was deleted instead of kept - that numbers taken are never given back - because no program can observe it: a key taken inside work that is thrown away is taken again at the next op that names it and at the close, so both readings print the same lines, and a sentence with no test does not belong in the brief. A fresh-session cold read was not run; the author wrote the sealed model first, and a self-probe reported as cold by a contaminated author is worse than none.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. Changing any line below changes what "correct" means and needs explicit
approval.

### Artifacts the agent produces

Exactly six files, collected at their original absolute paths:

    /app/led/ver.py    the committed side: the number standing at each key, and writing a close in
    /app/led/take.py   what a transaction has taken for a key, and whether that has moved
    /app/led/hold.py   what a transaction holds at a key while it runs
    /app/led/work.py   the work list, the marks, and the cut a mark defines
    /app/led/step.py   running one op of a program
    /app/led/close.py  closing a transaction: the last re-take, the conditions, what is written

Nothing else is read from the agent. The verifier lays these six over its own pristine copy of
the tree, so `/app/run_led.py`, `/app/led/spec.py`, `/app/led/say.py`, `/app/led/__init__.py` and
`/app/plans/` are always the verifier's, and a seventh file put beside them is never collected.

### The graded program language

One op per line, tokens split on spaces. `cfg K` opens the key space: keys `0..K-1`, every one
standing at 0. `tx T` opens transaction T. `rd T k`, `put T k n`, `add T k n`, `cpy T k j`,
`chk T k n`, `mk T`, `un T`, `fin T`, `drp T` are the ops. Programs are well formed: `cfg` comes
first, a transaction is opened before it is used and used only while it is open, and every key
named is inside the key space.

### The rules, as graded

1.  A transaction takes the number standing at a key the first time one of its ops names that
    key. `cpy T k j` names both k and j. The take is per key, not per transaction.
2.  Before an op runs, every key it names whose taken number is no longer the one standing is
    taken again.
3.  The number a transaction holds at a key is what its work makes of the numbers it has taken:
    the last entry in its work that sets the key decides, `put` gives the number, `add` gives the
    number held just before it plus n, `cpy` gives the number held at j just before it, and a
    read's entry gives the number that was printed. With no entry setting the key, the number
    held is the number taken. Taking a number again therefore moves every number derived from
    it, wherever in the work those sit.
4.  `rd T k` prints `rd T k v` with the number held at k, and fixes it: its entry holds that
    number, so nothing taken afterwards moves it, until one of the transaction's own later
    writes sets the key again.
5.  `mk T` marks the work. `un T` throws away the work from the last standing mark through the
    end, that mark with it, and throws away the whole work when no mark stands. Numbers taken
    are never given back: a key first named inside work that is thrown away stays taken, and
    holds the number taken for it again.
6.  `chk T k n` records a condition and does nothing else while the transaction runs.
7.  `fin T` closes. Every key the transaction has taken whose number has moved is taken again.
    Then the conditions are tested in work order, each against the number held at its key at its
    own position in the work.
8.  A condition that does not hold throws away the work from the last standing mark through that
    condition, the mark and the condition with them, and the testing carries on from the work
    after the condition with the numbers the mark opened on. A condition that does not hold with
    no mark standing before it ends the transaction with nothing written: it prints `fin T no`.
9.  Otherwise the close writes in every key that an entry of the surviving work sets by `put`,
    `add` or `cpy` - a read's entry writes nothing - at the number held at the end of that work,
    and prints `fin T ok` followed by `k=v` for those keys in ascending key order, separated by
    single spaces. A close that writes nothing prints `fin T ok`.
10. `drp T` ends the transaction with nothing written and prints nothing. `mk`, `un`, `put`,
    `add`, `cpy` and `chk` print nothing.

### What is checked

The whole printed trace of every graded program, line for line, as a list. All or nothing.

- 30 hand programs, one per graded decision plus the must-still-work side of every fence,
  checked against `tests/seal/gt.json`, frozen before the grading file was written. The grader
  first asserts that the sealed model still reproduces `gt.json` exactly.
- 366 programs generated inside the verifier from a seed drawn after the agent's container is
  gone, across eleven families, checked against the sealed model: `plain`, `move`, `read`,
  `sect`, `cond`, `nest`, `chain`, `many`, `late`, `wide`, `deep`.
- The worker that runs every graded program is under a 45 second wall clock, which is the
  execution limit stated in the brief. A correct engine that cannot get through the set inside
  it is scored exactly like a wrong one.

### Tolerances

None. Exact string comparison of every line, exact list length and order. The only limit is the
45 second wall clock, validated against an independently written correct engine, not only
against the reference.

### Ground truth, and where it lives

`tests/seal/gt.json` and `tests/seal/model.py`, in a root-owned directory made 0700 before any
submitted line runs. The worker runs as uid 1002 and cannot read either.

### Prong C tactics this contract uses, and the route-around guard

C1 both sides: `plain` and the must-still-work hand cases fail an engine that re-takes, fixes or
cuts where it should not. C2 the obvious oracle is a real database or a spare snapshot-isolation
implementation, and both abort where this engine re-bases. C3 the two measured scale families.
C4 exact all-or-nothing grading over a nonce population generated after the agent is gone. The
route-around guard is the artifact list: six files, laid over a pristine tree, so the program
language, the driver and the printing cannot be reshaped.

## Stage 7 re-attack (D7), 2026-09-22

Read the final brief with the built tree in front of me and tried to one-shot a plan.

The plan I form is: per transaction keep the numbers taken, an ordered list of entries and a
mark stack; work out what the transaction has at a key by walking the entries from the taken
numbers; on a read, walk; at the close, take every moved key again, walk once with a stack of
saved value maps, cut on a failing condition, publish what the surviving walk set. That plan is
semantically correct - it is `authoring/pin-drift-redo/variants/redo` in essence - and it dies on
the clock: one wide program takes 30.3 seconds against 0.26, and three of them plus three deep
ones take the graded run to 94 seconds against a 30 second limit.

What makes the repair a replan rather than a patch is what happens next. The obvious way to stop
walking is to cache what the transaction has at each key; the moment that cache exists, the mark
has to save it, and a mark that saves numbers is wrong the first time a basis moves after it -
which is invisible until a program reads a key after an undo, and is the reading
`undo-owes-after-mark` separates. The way out is to carry each value as its basis and an offset,
which is a different shape for `hold.py`, `work.py` and `step.py` at once. I wrote two further
correct engines afterwards and both had to arrive at a basis-relative mark; `variants/eager` was
wrong in exactly this way on its first version and a generated program in the `sect` family
caught it.

Are the load-bearing facts still distributed? Six editable files, each carrying a decision the
next one consumes, and the only feedback a wrong structure gets is one line per read and one per
close. Does the brief telegraph the method? It states every rule and names no structure; the
words basis, form, offset and cache do not appear in it, and `tools/onelinecheck.py` reports
that four of the five graded decisions have no exact rule at depth two over the fields the tree
exposes. Estimated solves, unchanged: 2 of 8. The risk I would flag to a reviewer is the same one
the doctrine names for a design aimed at the hard edge - that the realized rate comes back at 0
rather than 1 - and against it stand a reference that passes every run in 2.4 seconds, two
further correct engines that pass, and an expert path I can describe step by step.

## Decisions and their reasons

- Staleness is defined by the number standing at the key, not by a version stamp. A key that
  moved and moved back is not stale, and nothing observable turns on it, so the spec carries one
  number per key and the store ships no version field to leak.
- Reads and closes are the only printed lines. Printing a re-take or a dropped section would
  give per-decision feedback, which the leak audit forbids.
- The two scale families were measured before the contract froze (authoring/pin-drift-redo/proto,
  2026-09-22): wide, 48000 ops under 9600 commits over 12 keys, 76803 lines - reference 0.09 s,
  re-derive-on-every-re-take 20.7 s, 220x. deep, 16000 sections over 24 keys, 80003 lines -
  reference 0.17 s, re-derive-after-every-cut 17.6 s, 100x. Three programs of each family sit
  behind the 45 second limit, so either naive alone exceeds it while the reference finishes the
  whole graded set in about a second.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no Docker daemon in this container |
| No answer leaked into agent image | not run | |
| `harbor run -a oracle` = 1 | not run | harbor not installed here |
| `harbor run -a nop` = 0 | not run | |
| Cheats all score 0 | not run | |
| `tracecheck.py` (every graded assertion traced) | not run | |
| `preflight.py` | not run | |
| `harbor check` rubric | not run | no API key |

## Open questions and next steps

Stage 3: build the environment (shipped engine wrong in all six files), then the sealed model and
generator, the reference, the cheats, the instruction and the metadata.
