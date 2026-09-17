# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - pre-flight and packaging`.

## Assistant's assigned role

Client-sync engineer on a shared record store: the offline write path, the queue of changes a
user makes while the connection is down, the order those can be sent in once records depend on
ids the server has not handed out, and what has to be discarded when the server refuses one.
Tools are plain Python, a deterministic op-driven runtime and trace comparison.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. No repository was named in the first prompt and none is
  vendored, so the repo-based intake in `AGENTS.md` Stage 1 does not apply.

## Task summary

`/app` is the write path of an offline-capable client for a shared record store. A record has a
parent and integer fields. The user's changes (`new`, `set`, `add`, `mov`, `cut`) go on a queue;
`snd` sends what can be sent; `ok` and `no` carry the server's answers back; an `oth` line is a
change another client made and lands in the confirmed records directly; `ask` and `all` print
what the user sees. `/app/run_edit.py` replays a program and prints one line per event. Six
files under `/app/pend/` ship wrong and are the only ones collected. The agent makes the trace
match the stated rules, on 41 enumerated programs and 456 generated ones, inside a 60 second
clock that a service deriving the view per question cannot meet.

## Why it is hard

The plan the brief appears to ask for is the one every public write-up of this kind of client
describes, and it is wrong in four places that only show once a change has been held back.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan it
  would retrieve is wrong four ways. That plan (confirmed records plus a first-in-first-out queue, the view replayed per
  read, a refusal that drops the refused change) is specifically wrong here on four counts, and
  the structure that satisfies all the stated rules at once cannot be settled without working
  out how holding, the answer target, id order and the take-away change each other's meaning.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C3 and C4, plus the guard.
  A1: the retrievable sync-engine plan is the first plan and is wrong four ways; A2: the rules
  are stated operationally and the words rebase, outbox, optimistic and closure never appear; B2 ten graded decisions that interact and cannot
  be confirmed one at a time; C1 both sides fenced, with ordinary programs that a service
  holding back or dropping too much fails; C3 a measured resource gate - deriving the view per
  question is correct and takes 111 s on one wide program against a 60 s limit for the whole
  set; C4 every graded program compared line for line, all or nothing, over families shaped
  around each mechanism. Route-around guard: only the six named files under `/app/pend` are
  collected, the driver, the record store, the program reader, the printer and the id table are
  not, and the verifier lays the six over its own pristine copy.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was a dict of confirmed records, a FIFO list of unconfirmed changes, the view rebuilt by
  replaying the list over a copy of the records whenever a question is asked, a send that posts
  the list front to back, an acceptance that pops the front and folds it in, a refusal that pops
  the front and discards it. That plan is wrong at the answer target (an answer lands on the
  oldest change that went out, which is not the front once anything is held), at the id order
  (a creation takes its id at the answer, so a refusal of a sent change moves every id after
  it), at the take-away (a refusal takes a forward closure over shared records, and a removal of
  an unconfirmed record cancels its creation instead of queueing), and at the clock (the rebuild
  per question is 111 s on one graded program). The second finding, which invalidates the
  implementation rather than adding a case: what a queued removal takes is the records under it
  in the view at the moment it is laid over, so an arrival from another client changes what an
  already queued removal does - the view cannot be materialised when a change is made, and it
  cannot be derived per question either, so it has to be carried forward across the user's own
  changes and rebuilt only when the confirmed records or the queue move.
- Estimated solves out of 8: 3 (range 2-4). The design was aimed at 1; re-read cold at Stage 7
  with the built tree in front of me, the honest number is higher, because every rule is stated
  and a careful implementer can reach all ten decisions from the text alone. What keeps it inside
  the band is the conjunction rather than any one rule: ten decisions, no per-decision feedback,
  exact comparison over 497 programs, and a clock that a semantically perfect service misses by
  two to four times.
- Difficulty record score (tools/difficultycheck.py on authoring/queue-hold-drop/difficulty.toml,
  before Stage 2): 100/100 on the first scored record, 2026-09-17, inside the 95-100 band. One
  warning at that point: `gate.measured` was false. The gate was then measured (below) and the
  record updated. No other attempt was needed; nothing about the design changed between the
  score and the build except the take-away rule (see Decisions).
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set -
  this task has not been submitted.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-17, 100/100,
  first record. 2026-09-17 at Stage 7, re-measured against the built tree.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning?
  - The reach of a removal: records carry a parent and nothing else. No subtree, no descendant
    count and no child list is stored anywhere in the tree, so the question can only be answered
    by walking parent links at the moment it is asked.
  - Holding and the take-away: a queue entry carries its kind, the one or two record names it
    mentions and whether it has gone out. There is no dependency field, no position marker and
    no pair of counters whose difference names the answer target; both relations are derived
    from the names each time they are needed.
  - The ids: `bind.py` holds a name-to-id map and a set of names that arrived carrying one.
    Nothing records when an id was handed out or which change caused it.
  - Shipped programs: `/app/progs` holds four programs and no expected output. The only correct
    line published anywhere is the one the brief gives as its worked example, and that example
    was searched for rather than chosen (`authoring/queue-hold-drop/find_example.py`): of 327
    small candidates that the shipped service gets wrong, the one that ships decides exactly one
    of the 23 wrong readings, and that reading is `lay-upsert`, whose rule the brief states
    outright.
  - Dead fields: `tools/deadfieldcheck.py` is clean on the built tree.
  - Answer: nothing. No artifact in the agent's tree is a function of the correct trajectory.
- Expert path, described step by step:
  1. Run the shipped service on `tiny.txt` and `pair.txt` and read the six collected files
     against the brief to find where each rule lives.
  2. Split the state properly: confirmed records, a queue whose entries know whether they have
     gone out, and a view derived from both.
  3. Settle the vocabulary the rules are written in - which record a change is about and which
     it names - because holding and the take-away are both expressed in it.
  4. Work the holding relation out as a forward sweep with a growing set of record names, and
     the take-away as the same sweep from the position of the change that went.
  5. Move the id from the send to the answer, and make the answer target the oldest change that
     has gone out and is still queued.
  6. Make the removal and the move ask the view for the subtree at the moment the change is laid
     over, and give the cancellation the same take-away.
  7. Carry the view forward across the user's changes and rebuild it when the confirmed records
     or the queue move; time `wide.txt` and `deep.txt` against the 60 second limit.
- Originality check: searched 2026-09-17 for the public material a probe agent would retrieve:
  Replicache's rebase documentation, TanStack DB's mutation guide, and a long tail of
  offline-first outbox write-ups and repository issues. They describe the scaffolding (a
  confirmed base, pending mutations replayed over it, temporary ids swapped when creates come
  back) and they plan the four decisions this task grades the wrong way: they replay the pending
  list on every read, drop only the rejected mutation, treat the queue as first-in-first-out,
  and push creates first to collect id mappings. No page describes this rule set. The task is
  not a reskin of any retained bundle: the retained set has no sync, replication or client write
  path, and the mechanism here (two orders over one queue, plus a reach settled at replay time)
  is not the mechanism of any of them.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 119 rows in `authoring/queue-hold-drop/trace.md`, written by
  `authoring/queue-hold-drop/make_trace.py`, which fails if a quote is not in `instruction.md`
  or an enumerated case has no row. Rows: 4 test functions, 41 enumerated cases, 6 collected
  artifacts, the 60 s clock, 14 rules of the sealed model split one row per rule with its lines,
  23 readings, 4 shortcut strategies, 1 tolerance. No NOT STATED rows remain.
  `python tools/tracecheck.py queue-hold-drop` is clean.
- Identifiability (readings enumerated, which survived, what separated them): 23 wrong readings are written as patches of the reference in
  `authoring/queue-hold-drop/emit.py` and measured by `tools/readingcheck.py queue-hold-drop`.
  All 23 are separated by a named enumerated case; the run also reports which. Two survived the
  first case set - `gone-both` (the take-away spreading backwards) and `stop-only` (a
  cancellation that leaves what followed) - and `gone-front` and `stop-away` were written to
  separate them. No two readings that reproduce the published evidence disagree on the graded
  set: every survivor either fails a case or is a correct variant, and the two correct variants
  both score 1.
- Shortcut strategies scored (nop, constant, positional, replayed example): all four score 0.
  The nop scores 0 in the container. A constant trace scores 0 and matches no
  enumerated program, since no two of the 41 traces are equal and the graded traces run from 1
  to 60011 lines. The positional strategies are shipped as cheats: `ans-front` (answer the front
  of the queue), `hold-new-free` (send a creation regardless of its parent) and `gone-one` (take
  one change per refusal), each 0 and each caught by a named case. The replayed worked example
  is `cheat-forge-from-truth`: it reproduces all 41 enumerated traces and is wrong on 196 of 200
  generated programs.
- Independent implementation behind every tolerance and limit (path, measured headroom): two correct services written apart from the reference, against the one limit there is.
  That limit is the 60 s wall clock in `tests/test.sh`.
  `authoring/queue-hold-drop/variants/walk` walks every record's chain of parents instead of
  indexing children; `authoring/queue-hold-drop/variants/eager` holds the view as a
  copy-on-write overlay on the confirmed records. Measured: 1.2 s and 1.0 s over the graded
  shapes against the reference's 1.0 s, and 1.28 s for all 497 programs inside the verifier
  image. The same contract with the view derived per question takes 111.0 s on one wide program
  and 48.3 s on one deep program, and the two shipped as cheats take 251.1 s and 220.1 s over
  two of the six scale programs.
- Undecided decisions from the cold-reader pass (author-run): seven, each now settled.
  Every graded token was listed and put through the four clusters. Seven decisions the first
  draft left open, each now settled by a sentence: whether a field set to zero prints (it does -
  "A field nothing has set holds zero" plus the `say-fields` case); whether the parent of a top
  record prints as `-` or as a word; whether the `ack` of a creation shows the new id or the old
  name; whether the take-away reaches backwards over the queue; whether a removal of an
  unconfirmed record whose creation has already gone out cancels (it does not - the sentence
  says "whose creation is still on the queue"); the order `all` prints records in; and whether
  a change that has gone out but has not been answered is still laid over the view. The stronger
  form - a fresh session reading only the brief and the tree - was not run, because this session
  wrote the sealed model and cannot un-know it.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/pend/line.py`, `/app/pend/fold.py`, `/app/pend/hold.py`,
  `/app/pend/view.py`, `/app/pend/lay.py`, `/app/pend/reach.py`. Nothing else is read.
- What is checked: the printed trace of every graded program, line for line, all or nothing.
  41 enumerated programs against `tests/seal/gt.json`, frozen before the grader was written;
  456 programs generated inside the verifier from a seed drawn after the agent's container is
  gone, against `tests/seal/model.py`; and the model is required to reproduce `gt.json` exactly
  before anything is graded. The worker runs under a 60 s wall clock, which is the task's stated
  execution limit.
- Tolerances: none. Comparison is exact string equality on every line.
- Ground truth, and where it lives: `tests/seal/`, `chmod 700`, root-owned, unreadable by the
  uid that runs the submitted code.

Prong C tactics used, and the route-around: C1 (both sides of every fence enumerated), C2 (no
oracle ships - the shipped service is wrong in all six collected files, so agreeing with it
proves nothing), C3 (the 60 s clock, measured), C4 (seeded generation over twelve shaped
families plus enumerated corners, all or nothing). Route-around: `artifacts` lists exactly the
six files; the driver, the dispatch, the record store, the program reader, the printer and the
id table are the verifier's own copies.

## Decisions and their reasons

- The take-away and the holding relation were unified during Stage 3. The first form seeded both
  from every record a change names, which made a cancellation of `new a p` remove later changes
  about the parent `p` as well - correct under the rule as stated, and hard to defend. Both are
  now seeded from the record the taken or held change is *about*, and both grow by the record
  each taken or held change is about. This is the one contract change made after the record was
  scored; it happened before any answer was frozen, and `build_gt.py` has reported the enumerated
  answers unchanged on every run since.
- `Chg` and `Rec` carry no `__slots__`, so a submitted service may attach whatever state its own
  structure needs. The shipped frozen files declare no caching field, because a field nothing
  reads is a clue (`tools/deadfieldcheck.py`).
- `bind.py` and `say.py` are frozen rather than collected. The rules they would otherwise carry -
  the id numbering and the field order - are still graded, because a submitted `view.py` can
  format its own lines and a submitted `fold.py` decides when an id is handed out; freezing the
  mechanics keeps the contract about the decisions rather than about string formatting.
- Both the reference and the sealed model carry the view forward and rebuild it when the
  confirmed records move. That is forced by the clock, not by a shared reading of the rules, and
  it is the one structure they share; everywhere else they differ (records as objects against
  two-slot lists, a child index against an ancestor walk, a surviving list against an index set).
- The scale families were sized after measuring, not before: 20000 queued changes with a
  question after each, and a 12000 record tree with 8000 questions, put the per-question rebuild
  at 111 s and 48.3 s against the 60 s limit while the reference stays near 1 s.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py queue-hold-drop --build` |
| No answer leaked into agent image | pass | `tests/` and `solution/` are never copied in; `/app` holds the service and four programs with no expected output |
| `docker_trial.py ... oracle` = 1 | pass | 44 tests passed; worker ran all 497 programs in 1.28 s |
| `docker_trial.py ... nop` = 0 | pass | the shipped service is wrong and does not finish inside the clock |
| Cheats all score 0 | see report | `authoring/queue-hold-drop/docker_all.txt` |
| Correct variants score 1 | pass on the host | walk and eager, 167 programs each, 0 differences |
| `readingcheck.py` | pass | 23 of 23 readings separated by a named case |
| `tracecheck.py` | pass | clean, 119 rows |
| `preflight.py` | see report | run at Stage 7 |
| `harbor check` rubric | not run | harbor is not installed in this environment |

## Stage 7 re-attack (D7), done against the built tree

Read the final brief cold and tried to one-shot the plan with the environment open. The plan I
form now is the right one, because I wrote the reference; what that exercise can still show is
where a cold implementer slips, and there are five places: the holding spread (a change whose own
records all carry ids can still be held), the answer target (the oldest change that went out is
not the front), the reach of a queued removal (settled when it is laid over, not when it is made),
the cancellation of an unconfirmed creation, and the clock. Each is one sentence in the brief and
none of them announces itself in the shipped code.

Two checks stand in for what the re-attack cannot do from inside this session.
`tools/onelinecheck.py` finds no rule of two terms or fewer, over the fields the environment
exposes, for any of the four graded quantities it measures - which changes go out, which change an
answer lands on, how many a refusal takes, and how many records a removal takes. And every one of
the 23 wrong readings is separated by an enumerated case, so a wrong reading fails with the name
of the rule it broke rather than as noise.

The load-bearing facts did not flatten during the build: the six editable files still consume each
other in order, and the environment measures 257 lines against a retained band of 224 to 544, with
the graded patch at 214 lines against 110 to 424. `tools/difficultycheck.py` scores the built
bundle at 100.

## Open questions and next steps

- `harbor` is not available here; `tools/docker_trial.py` is the two-image substitute and is what
  every container result above comes from.
- The easiness probe has not been run. Nothing in this repository can run it, and no local result
  substitutes for it.
