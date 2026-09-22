# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one — anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` (environment, reference, model, cheats and variants built; gates below)

## Assistant's assigned role

Storage-engine concurrency-control engineer: the person who owns the lock table of a
transactional engine — mode compatibility, the intention hierarchy, conversion queues, the
escalation path that swaps row locks for a table lock, and the wake pass that decides which
blocked session runs next.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? not applicable - the tree is authored here, in a terse legacy
  register (`lk/`, `ent`, `txn`, `ask`, `wake`, `lift`, `tell`) with no name that misdescribes
  what it holds
- Proper-noun sweep done? nothing carries provenance: no vendor, product or engine name appears
  in the tree, the modes and the hierarchy are public vocabulary
- Upstream-diff check: not applicable

## Task summary

`/app` is the lock table of a storage engine, cut down to the part that decides who holds what
and who runs next. A script gives a run of a workload: transactions begin, request locks on
tables and on rows of those tables in the five modes of the intention hierarchy, and commit.
The engine prints a line for each grant, each queued request, each felled transaction and each
raise, then a final dump of what every transaction holds, what is still queued and how many
requests were satisfied without taking a lock at all. The shipped engine is coherent and wrong:
it takes locks it already covers, releases every row on a raise rather than the covered ones,
fells any younger holder, wakes waiters entry by entry, and counts a tally that never goes
down. The agent rewrites seven files under `/app/lk/` so that the engine settles every script
the way the brief states, inside a 60 second limit over the whole graded set.

## Why it is hard

The rules are all in the brief. What is not in the brief is which structures survive all of
them at once. Two of them do the damage: a grant is a releasing operation (a table lock strips
the rows of that table it covers out of the holder's hand, and a request the holder already
covers takes nothing and is merely counted), and the wake pass is one global sweep in begin
order that restarts on every change rather than a walk of the entry that was just freed. The
first makes the row tally the escalation threshold reads move underneath every table grant; the
second makes any per-entry or recursive wake produce a different run as soon as one event frees
several entries, which a commit, a felling and a subsumption all do.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrieved and memorised lock manager is wrong here at four decision points, and none of the corrections is local. That plan brings the conflict matrix, a first-in queue per entry, a walk of the freed entry's queue on release, and escalation by swapping every row lock for a table lock. Against it: covering removes locks the plan takes, subsumption makes granting a releasing operation, the wake order is one global pass by begin position rather than per entry, and a holder is shielded from felling by a waiter on a different entry. A plan written before reading the tree commits to a per-entry wake loop and an append-only grant, and both have to be taken apart rather than patched.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, B2, C1, C3 and C4, with the route-around guard. A1 the documented escalation behaviour (all sub-table locks released, all counted) is inverted
  here; A2 covering, subsumption, standing and the frontier are stated as engine behaviour and
  never named; B2 eleven rules hold at once and each changes what a correct implementation of
  the others looks like; C1 both sides of felling, covering and the raise are graded; C3 two
  measured scale families kill the literal wake pass, the scanned tally and the scanned standing
  while leaving all three exactly correct; C4 line-for-line grading over a population generated
  from a seed drawn after the agent's container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  an entry object with a granted map and a first-in queue, a transaction object with its granted
  modes, take the intention lock then the row lock, and on release walk the freed entry's queue
  granting what now fits. That plan is wrong in three places that do not show up until cascades
  exist: it grants without releasing (so subsumption and the tally are missed), it wakes per
  entry (so a commit that frees two entries grants them in the wrong order), and it fells on raw
  age (so every shielded holder is felled). None of the three fails a one-entry test.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 scored 100/100 on 2026-09-22, in band, one warning that
  the gate timings were still a promise. No redesign was needed; the timings are measured at
  Stage 4 and the record's `measured` flag is flipped only after they are run.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set - first submission
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 design record 100/100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": releases print
  nothing, so subsumption is visible only through the final dump; no covered flag, row tally,
  standing or oldest-waiter field is stored anywhere in the tree; the covering relation ships as
  an editable table that is wrong, so it cannot be called; no sample script ships with its
  correct output, and the one line quoted in the brief is a report line.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  run the shipped scripts and find the module behind the quoted line; separate the four ways a
  request can end (covered, granted, queued, felled) into their own paths; derive that a table
  grant releases the rows it covers and rebuild the holder record as per-table buckets; replace
  the per-entry wake with one frontier re-picked by begin position after every change; carry the
  row request of a blocked intention request as a continuation on the transaction and drop it
  when the transaction is felled; settle the raise as a conversion that neither queues nor fells
  and is retried on each row grant at the threshold; derive a holder's standing from the other
  entries it holds; then time the wide and deep scripts and make the frontier a heap over
  touched entries, the tally a per-table count and the standing an aggregate.
- Originality check: searched 2026-09-22 for multi-granularity lock managers, intention locks,
  escalation semantics and public lock-manager assignments. The pieces are documented
  everywhere - the five-mode matrix, top-down intention acquisition, the escalation threshold -
  and a well-known university assignment ships a lock manager with upgrade rules whose solutions
  are public. None of it describes this engine: vendor documentation states that escalation
  releases *every* sub-table lock and that *every* sub-table lock counts toward the threshold,
  which is the opposite of the rule here, and nothing public wakes waiters in one global pass by
  begin position or shields a holder by a waiter on another entry. The retrievable material is
  therefore the first plan this task is built to break.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 93 rows walked - 4 test functions, 38 enumerated cases, 7 collected files, the new-file guard, the entry points, the 60 second clock and 30 rules of the sealed model, each split out of the method that applies it and cited by line. No row was left NOT STATED; three quotes were re-cut after the prose pass split their sentences. `python tools/tracecheck.py lock-cover-wake` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 32 readings were written down as whole engines (`authoring/lock-cover-wake/emit.py`) from the four clusters, the shipped engine's own behaviour and the vendor documentation that says the opposite of the covering rule. Every one is ruled out by a sentence and separated by the enumerated case named for it - `tools/readingcheck.py lock-cover-wake` reports 32 of 32 separated, and `cheat_report.py` reports 0 findings with each reading moving between 2 and 120 of 120 shaped generated scripts. Three further readings are exactly correct and separated only by the clock; they are recorded under Tolerances rather than as wrong readings. Two survivors were promoted to correct variants and must score 1.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): nop 0 (the shipped engine fails 25 of 38 enumerated and 38 of 40 generated); one fixed output for every script 0 (38 of 38, 120 of 120); every request granted at once 0 (19 of 38, 112 of 120); the frozen answers replayed by script hash 0 (passes 38 of 38 enumerated, fails 120 of 120 generated). None of them matches a majority of cases, so no strategy is close.
- Independent implementation behind every tolerance and limit (path, measured headroom): the only limit is the clock on the worker. It is validated against `tests/seal/model.py` and the two correct variants under `authoring/lock-cover-wake/variants/`, all written apart from the reference; see the Validation table for the measured seconds.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. Four decisions the first draft left open were written in: that the entry being asked for does not count toward a holder's standing (the `other than the one being asked for` clause, with case `fell-skip`), that a waiting head fells nobody (case `wake-nofell`), that a conversion may pass queued new requests but not queued conversions (cases `conv-jump` and `conv-behind`), and that a resource taken again after being released is reported at the end of the acquisition order (case `rep-order`). The conflict matrix and the covering lattice were each checked back against the implementation by a script rather than by eye, after one draft stated the matrix wrongly for IS against SIX.

## Verifier contract — FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: the seven files it may change, collected at their own paths -
  `/app/lk/mode.py`, `/app/lk/ent.py`, `/app/lk/txn.py`, `/app/lk/ask.py`, `/app/lk/wake.py`,
  `/app/lk/lift.py`, `/app/lk/tell.py`. Nothing else is collected; a new file placed beside them
  is never read.
- What is checked: the verifier lays those seven files over its own pristine copy of the tree and
  runs every graded script through the shipped driver, comparing the printed lines exactly and in
  order. Thirty-one hand-written scripts, one per graded decision plus the must-still-work side of
  each fence, are checked against `gt.json`, frozen before the grading file was written; a
  generated population, produced inside the verifier from a seed drawn after the agent's container
  is gone, is checked against the sealed model. The sealed model must also reproduce `gt.json`
  exactly before anything is graded. Every script must match; one wrong line scores 0.
- Graded decisions, each owed a sentence in the instruction:
  1. a request for a mode the transaction already covers, on that resource or on the row's table,
     takes no lock, prints nothing and is counted
  2. a row request needs the intention on its table first, and the row request is made when that
     intention request is granted, not when the command is read
  3. a request by a transaction that already holds the resource converts to the cover of the two
     modes and is tested against the modes the other transactions hold
  4. a new request may not pass a queued request; a conversion may, except past a queued conversion
  5. a request that cannot be granted fells every conflicting holder the requester began before
     the holder's standing, in begin order
  6. a holder's standing is the earliest begin among itself and the transactions waiting on the
     other entries it holds
  7. the queue holds conversions ahead of new requests, each class in request order
  8. after any change the engine goes back over every waiting head, oldest transaction first, and
     restarts on every grant and every felling
  9. a table grant releases the rows of that table the new mode covers, and only those
  10. a row grant that leaves the transaction at the threshold raises its table lock once, without
      queueing and without felling, and abandons the raise silently when the table is held against it
  11. a command naming a transaction that is waiting, felled or committed is passed over
  12. the report: state word and the locks in acquisition order per transaction in begin order,
      then the queues in resource order, then the covered count
- Tolerances: none. Exact line-for-line comparison of the printed trace and report. The only
  limit is the wall clock on the stage that runs submitted code, which is the execution limit the
  brief states: 60 seconds for the whole graded set.
- Ground truth, and where it lives: `tests/seal/model.py` (an independently written
  implementation) and `tests/seal/gt.json` (the frozen answers for the hand scripts), in a
  root-owned directory made `chmod 700` before any submitted code runs.
- Prong C tactics in the contract: C1 both sides of felling, covering, the raise and the queue
  rules are enumerated; C2 no public engine behaves this way and nothing in the tree records a
  correct run, so "run it and see" confirms only that it runs; C3 the wide and deep families
  make the literal wake pass, the scanned tally and the scanned standing infeasible while leaving
  them exactly correct; C4 line-for-line grading over a nonce population shaped per decision.
- Route-around guard: only the seven files are collected, and the verifier runs them over its own
  copy of the driver, the parser, the line builders and the sample scripts, so the script grammar
  and the output format cannot be reshaped, and a new module beside the seven is never read.

## Decisions and their reasons

- Category is `Software / Databases`: the graded work is a lock table - mode lattice, intention
  hierarchy, conversion queues, escalation - and the environment is full of that machinery rather
  than of a story about it.
- The line builders (`lk/log.py`), the script parser (`lk/read.py`) and the driver
  (`/app/run_lk.py`) are frozen and not collected, so a format slip cannot fail a run for a
  reason that is not the task.
- Modes are the five of the intention hierarchy. Rows take S and X only, tables take all five;
  that keeps the covering relation one order instead of two.
- Felling is age-based rather than cycle-detected: a finite script needs no liveness guarantee,
  the final dump shows whoever is still waiting, and age ordering gives the standing rule
  something to modify.
- Commands for a transaction that is waiting are passed over rather than held: holding them
  would put the script's order under the engine's control and make every trace depend on it.

## Quality self-review (docs/QUALITY-REVIEW.md, criterion by criterion)

Instruction against verifier, both directions:
- Every behaviour the tests check is described: the walk is `authoring/lock-cover-wake/trace.md`,
  95 rows, `tracecheck` clean.
- Every behaviour the brief promises is tested: the two sample scripts the brief points at are
  graded as they ship (`plan-tiny`, `plan-pair`), which is what closed the one gap - the line the
  brief quotes had no test until then.
- The collected files are named with absolute paths in the brief, and so are the entry points the
  driver uses (`instruction.md` paragraph 3).
- The schema is the line formats, stated down to the separators and the order of the report.
- Boundaries: `E or more`, conversions ahead of new requests and each class in request order,
  holders felled in begin order, the standing excluding the entry being asked for, resources
  ascending with a table ahead of its rows, acquisition order with a retaken resource last.
- Graded quantities defined: `cov <n>` is the number of requests that took no lock; the four
  state words are enumerated.
- Counts re-derived from the code after every generator change: forty hand scripts, three hundred
  generated small ones, three of each scale family.
- Readings: 32 enumerated, every one separated by the case named for it, none left undecided.

Prose: `tools/textcheck.py` against the retained brief leaves four findings (burstiness,
paragraph spread, one three-item list, vocabulary), which is the band the retained briefs sit in
(`slab-fold-scope` one, `token-seam-emit` three). Each requirement is stated once.

Verifier rigor: the tests run the submitted engine over 346 scripts and compare printed lines;
`test_outputs.py` carries the frozen contract in its docstring and each test says which rule it
pins. Nothing depends on wall-clock time except the stated execution limit, and the seed is drawn
once and read by both halves.

Environment hygiene: `environment/Dockerfile` copies `app_src/` and nothing else; the verifier
toolchain is baked into `tests/Dockerfile` at the canonical pins; `preflight` reports no errors;
`imagecheck` assembles what the image would hold and runs the four shipped scripts through it.

Solution quality: `solution/solve.sh` copies the seven reference files into place and runs two of
the shipped scripts. It computes; nothing is echoed.

Anti-cheating: no correct output ships, the covering relation ships wrong so it cannot be called,
`forgecheck` finds the one deliberate forgery and nothing else, and the answer key is unreadable
by the uid that runs submitted code (`authoring/lock-cover-wake/isolation.py`, 0 findings).

Metadata: `Software / Databases` with six tags naming the mechanisms rather than the taxonomy;
the difficulty explanation names the concrete steps and says the terse register is deliberate;
the timing numbers in it are the measured ones.

## Stage 7 re-attack (D7), run against the built task

Read cold, the brief hands over a plan and I would write it without hesitating: an entry object
with its holders and two queues, a transaction object with its locks and its rows per table, a
request path with four ends, a pass over the waiting heads in begin order, subsumption on a table
grant, a raise hook after a row grant, a report. That plan is right in outline, because the
contract rule says every graded assertion has its sentence and this brief keeps it.

What I would get wrong on the first pass, and what the measurements say about each:

- the cascade. A grant releases locks, a continuation makes a new request inside the pass and a
  felling destroys a transaction inside it, so the pass restarts and the frontier grows while it
  is drained. My first implementation would wake the entry that was just freed. That reading
  moves 15 of 120 shaped scripts, and on `wake-oldest` it changes not the order of two lines but
  whether a transaction survives.
- the standing. It is an aggregate over the holder's *other* entries, so it has to be able to
  leave one out. Reading it as the holder's own begin moves 13 of 120; letting the entry being
  asked for shield its own holder moves 4.
- the covered request. It takes no lock, so it never reaches the count the limit is read from.
  Two readings of that move 73 and 2.
- the continuation. Making the row request when the command is read rather than when the
  intention is granted moves 40 of 120.

Then the clock. The reference gets through the graded set in 3 seconds; the literal wake pass and
the walked row count each need more than 300 seconds on a single script, and the walked standing
136 seconds over the three deep ones. A correct engine that keeps none of the three structures
does not finish, and nothing in the tree says which structure it is missing.

Is the estimate still 2 of 8? Yes, with the range 1 to 4. The risk that moved during the build is
the zero end rather than the eight end: eleven graded decisions under all-or-nothing grading over
346 scripts is unforgiving, and the only feedback a wrong reading gets is one line of one sample
script. Against that, every rule is stated, the reference is 435 lines across seven files, and two
independently written engines reached the same answers, so the expert path is real and short
enough to walk in a day.

The cold self-probe is recorded as NOT RUN. This session wrote the model, so a self-solve would
measure memory rather than difficulty, and a self-probe reported as cold by a contaminated author
is worse than none. Standing in its place: the 32 reading separations, the four shortcut
strategies scored at 0, `onelinecheck` finding no graded decision with a rule at depth two, and
the fact that the two correct variants were written from the contract rather than from the
reference and needed no change to score 1.

## Validation status

Docker is installed here but the egress policy denies the registry's blob host
(`production.cloudfront.docker.com`, 403 on CONNECT), so neither image can be built in this
session and `tools/docker_trial.py` cannot run. Everything below that says "host emulation" was
run by `authoring/lock-cover-wake/host_trial.py`, which stages the same `/app`, `/tests`, `/work`
and `/logs/verifier`, runs the shipped `tests/test.sh` with the same privilege drop and the same
wall clock, and reads the same `reward.txt`. It does not prove the image build; `tools/imagecheck.py`
covers that by interpreting the Dockerfiles against `.dockerignore`, assembling what the image
would hold and running the four shipped scripts through it.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | registry blocked; `imagecheck` assembles the tree the Dockerfile would produce (15 files, workdir /app) and runs all four sample scripts through it, clean |
| No answer leaked into agent image | pass | `environment/Dockerfile` copies `app_src/` only; `extraneouscheck`, `deadfieldcheck` and `forgecheck` clean; `Ent.old` and `Item.cont` were removed from the shipped tree after the leak audit found them written and never read |
| `harbor run -a oracle` = 1 | pass (host emulation) | reward 1, 43 tests passed in 2.87 s; the worker gets through all 346 scripts in 3.0 s against the 60 s limit |
| `harbor run -a nop` = 0 | pass (host emulation) | reward 0 |
| Cheats all score 0 | pass (host emulation) | 46 of 46, including 9 isolation probes, 3 correct-but-slow readings, 2 shortcut strategies and the answer-key forgery |
| Correct variants score 1 | pass (host emulation) | `ok-flat` and `ok-lazy`, both reward 1 |
| Isolation, asserted at the layer | pass | `authoring/lock-cover-wake/isolation.py`: reward directory and sealed directory root-owned 0700; the sandbox uid is denied the frozen answers, the model, the reward, the grader, the generator and the authoritative seed |
| Reference against the sealed model | pass | 0 differences over 86 shaped scripts and 400 random ones; the model reproduces `gt.json` byte for byte |
| Execution limit measured | pass | reference 3.0 s for the whole set; the wake pass taken literally is over 300 s on one wide script, the walked row count over 300 s on one deep script, the walked standing 45 s per deep script (136 s over the three) |
| `readingcheck.py` (32 wrong readings separated) | pass | every reading failed by the enumerated case named for it |
| `onelinecheck.py` (no short rule) | pass | none of the four graded decisions has an exact rule at depth <= 2 |
| `tracecheck.py` (every graded assertion traced) | pass | 95 rows, clean |
| `difficultycheck.py` | pass | 100/100 at Stage 7 on the measured tree (412 environment lines, 7 editable files, 435 reference lines) |
| `preflight.py` | pass | no errors; 40 warnings, all of them the unused-public-function rule reading method calls it cannot see (a separate audit that counts dotted calls finds nothing unreachable) |
| `catcheck` / `hintcheck` / `structcheck` / `simcheck` / `solvecheck` / `extraneouscheck` / `deadfieldcheck` / `forgecheck` | pass | `simcheck` reports the environment Dockerfile as near-identical to other bundles, which is the canonical four-line image, and reports the task as conceptually distinct from every earlier one |
| `textcheck` prose | 4 findings | burstiness, paragraph spread, one three-item list and vocabulary width, the same band the retained briefs sit in |
| `harbor check` rubric | not run | no API key in this session |
| External easiness probe | not run | it is the platform's gate; the local stand-ins are the reading separations, the shortcut scores and the cold attack recorded above |

## Open questions and next steps

Built and validated as far as this session can reach. What is left for a session with working
infrastructure, in order:

1. `python tools/docker_trial.py lock-cover-wake --all` once a registry is reachable, to repeat
   the oracle, the nop and the 46 cheats inside the two real images. The host emulation ran the
   same `test.sh` with the same privilege drop, so what this adds is the image build.
2. `harbor check` with an API key.
3. The platform's easiness and difficulty probes, which are the gates no local check replaces.

Two things a later session should not undo. The mode counts kept beside each entry's holders are
not decoration: without them the conflict test is linear in the holders, and one hot table in the
deep family carries six thousand - it cost the reference 36 seconds of a 60 second budget before
they were added, which would have failed a correct engine on a slower machine rather than a wrong
one. And `tests/cases.py` grades the two sample scripts exactly as they ship; `make_plans.py`
asserts they have not drifted apart, because the line the brief quotes is only tested through
`plan-tiny`.
