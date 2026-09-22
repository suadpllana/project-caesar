# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` (contract frozen below; oracle, nop and the cheat suite run in the containers)

## Assistant's assigned role

Backend engineer on the read path of a list API: the part that turns a table plus a client
cursor into a page, keeps the per-client scan position across edits to the underlying rows,
and holds the leftovers the service could not fit. Comfortable with ordered secondary
indexes, with cursor conventions and where they break under concurrent writes, and with the
difference between a page that is a slice of an ordered view and a page that is packed from
one.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository vendored)
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/: not applicable
- Load-bearing couplings found during research: not applicable
- Identifier degradation done? The tree is authored, not vendored, so there is no conversion
  table. Identifiers are written in a legacy register from the start (`lst/`, `seq`, `scr`,
  `owe`, `pg`, `edt`, `rep`, `mk`, `led`, `got`); every name is recoverable from what calls it
  and none misdescribes what it holds.
- Proper-noun sweep done? Nothing in the tree names a product, a company or a person; the
  only proper nouns are Python's own.
- Upstream-diff check: not applicable

## Task summary

`/app` is the read path of a list service. A list file gives a table of rows, the scrolls
(clients) reading it, the pages they ask for and the edits that happen between those pages.
Each row carries an id, a sort key, a tag and a weight; a scroll reads the rows carrying one
tag, in key-then-id order, and every page it is served carries at most a stated number of
rows and at most a stated weight.

The service ships broken. The work is to make it produce, for every list file, exactly the
pages and the closing report the stated rules define. Six files under `/app/lst` are
collected; the driver, the list-file parser, the trace writer and the sample lists are the
verifier's own copies and cannot be changed.

The rule the whole thing turns on is that a page is packed rather than sliced: a row the
scan has no weight left for is stepped over rather than ending the page, the scan mark moves
past it, and the row stands owed to that scroll until a later page hands it out. The owed
rows are drained ahead of the scan on the next page and count against the same limits, and
the service holds at most a stated total of owed weight across every scroll at once, so what
one scroll may step over depends on what the others are owed at that instant.

## Why it is hard

The first plan is the published one: a cursor holding the last row handed out, a forward
scan from it, and a pending list for leftovers. The service ships as that plan and the brief
states the two rules that make it wrong - the step-over and the shared hold - without
stating any of their consequences. Those consequences are the work: the mark is the last row
looked at rather than the last row handed out; owed membership is a recomputation over the
mark, the tag and the delivery memory rather than a log written when an edit happens; the
same scan that drains the ledger appends to it behind the entries it could not drain; and
the hold couples scrolls that a per-scroll pass treats as independent.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrieved and memorised answer to a row that does not fit a page is to end the page at it and resume from it, so the agent arrives with a cursor meaning the wrong thing, a pending list written by the wrong events, and a per-scroll pass that a shared hold makes unworkable.
  In longer form: the agent arrives with a cursor that means the wrong thing and a
  pending list written by the wrong events. Correcting the cursor is not enough, because the
  owed set is produced by the pass that consumes it and bounded by a quantity shared with
  every other scroll; a plan that survives has to be formed after reading how the two phases
  of a page, the mark, the ledger and the hold constrain one another, and the shipped service
  prints a coherent page for every list, so nothing in the environment says which reading is
  the right one.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C3, C4 - the pagination prior is a liability at the first decision point (A1); the stepping over, the owing and the hold are stated operationally and never named as a queue, a monotone mark or a shared budget (A2); ten rules hold at once and each changes what a correct implementation of the others looks like (B2); both sides are fenced, so a service that never steps over fails the heavy-row lists and one that always steps over fails the empty-page lists (C1); two measured scale families leave re-deriving the view per page and re-sorting it per edit exactly correct and outside the stated limit (C3); grading is line-for-line over a population generated inside the verifier from a seed drawn after the agent's container is gone (C4).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is the keyset one - the cursor is the last row delivered, the page ends at the first row that does not fit, leftovers go in a per-scroll pending list appended when an edit moves a row behind the cursor, and each scroll is handled on its own - and it is wrong at all four of those points.
  In longer form: it is wrong at the
  cursor (the mark is the last row looked at), wrong at the page (a row that does not fit is
  stepped over, not a stopping point), wrong at the ledger (membership is derived, so entries
  retire and re-enter at the end), and wrong at the shape (the hold is one number over every
  scroll). I could not have committed to the right structures without reading how those four
  interact.
- Estimated solves out of 8: 2 (design target 1-3, the hard edge)
- Difficulty record score (tools/difficultycheck.py on authoring/page-pass-owe/difficulty.toml,
  before Stage 2): attempt 1 on 2026-09-22 scored 100/100, in band (95-100), with one warning
  that the gate was not yet measured. Re-run at Stage 7 against the built tree: 100/100, no
  warning, measuring 276 environment lines of Python, 6 editable files, 367 reference lines,
  44 cheats and 2 variants - all inside the retained band and no drift to report.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set;
  no pipeline score received for this task yet.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22, 100, first
  complete record.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing":
  - the mark: never printed. A page prints only the ids it handed out, so the mark is
    recoverable only by reproducing the scan that set it.
  - owed membership: no shipped helper answers it, no field records it, and owed numbers
    appear once, in the closing report, so no page gives feedback while the run is going.
  - the owed weight standing: the shipped code sums the ledgers where it needs the number,
    so nothing carries it as a field, and it is never printed except as the single closing
    total. Summing was measured and is not what the gate kills - carrying it is an
    optimisation the task does not require, and both correct variants sum per-scroll totals.
  - delivery memory: a row record carries an id, a key, a tag and a weight and nothing else.
  - the sample lists: shipped without expected output. One line of one sample is quoted in
    the brief and it fixes the order of two rows sharing a key, which is a convention rather
    than a decision the task turns on.
  - derived quantities: the list file carries ids, keys, tags, weights, the scroll limits and
    the hold, which are primitives. Places, the per-tag order, marks, ledgers, owed weight,
    delivery memory and every number in the closing report are derived and none ships.
- Expert path, described step by step:
  1. Run the shipped service on `/app/lists/tiny.txt` and read the line the brief says is
     wrong; it lands in the module that decides the order.
  2. Settle that a place is the key and then the id, and that a scroll's view is the global
     order cut down to the rows carrying its tag at the moment it looks.
  3. Rebuild the view as one ordered index per tag, because a scan has to resume at the mark
     rather than walk the table from the front.
  4. Derive that the mark never goes backwards - only the scan moves it, and only forwards -
     and use that to resume a scan by search instead of by walking.
  5. Make the ledger an ordered structure whose membership is recomputed from the mark, the
     tag and the delivery memory, with retirement on an edit and re-entry at the end.
  6. Carry the owed weight standing across every scroll, as one total or as a sum over
     per-scroll totals, because the step-over test reads it on every scan step.
  7. Settle the two phases of a page, their shared limits, and the rule for a page that has
     handed out nothing, which spends the whole weight on one row.
  8. Write the closing report from the view and the delivery memory as they finally stand,
     not from counters kept during the run.
  9. Time the wide and deep lists and replace the per-page re-derivation of the view, the
     per-test sum over the ledgers and the per-edit sweep over every scroll.
- Originality check: searched for public write-ups of the mechanism on 2026-09-22. What
  exists is the keyset/seek-method pagination literature, the cursor-connection conventions
  of the public list APIs, and engineering posts on cursor instability under concurrent
  writes; all of them end a page at its boundary, define the cursor as the last row
  delivered, and answer instability with a snapshot or an accepted loss. Nothing found steps
  over a row and owes it, drains the leftovers ahead of the next scan against the same
  limits, or shares one owed-weight hold across every open cursor. The combination is
  authored here and does not match any retained task in this repository: the nearest by
  category is `delta-view-retraction`, which maintains aggregates under retraction and shares
  no mechanism with a packed page, a scan mark or a shared hold.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed
model and test.sh line by line into authoring/page-pass-owe/trace.md, start it with
`python tools/tracecheck.py page-pass-owe --skeleton`, and keep
`python tools/tracecheck.py page-pass-owe` clean.

- Instruction trace (authoring/page-pass-owe/trace.md; rows walked, NOT STATED left, tracecheck result): 88 rows walked - 4 test functions, 34 enumerated cases, 6 collected artifacts plus the not-collected rule, the 60 s clock, and one row per rule of the sealed model with its line range - no NOT STATED rows left, and `python tools/tracecheck.py page-pass-owe` is clean.
  Two rows needed a sentence written for them rather than found: the collection boundary
  ("a new file put beside those six included") and the empty-page rule reaching the scan as
  well as the ledger ("Throughout both halves").
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 28 readings were written down as file-level patches in `authoring/page-pass-owe/readings.py` and driven against the enumerated set by `tools/readingcheck.py`; 26 were separated on the first run and 2 survived it.
  The two survivors were both boundary readings the text settled but no case tested: the hold
  tested strictly (`<` rather than `<=`) and the stepped-over allowance tested strictly. The
  checker's shrunk counterexamples were replaced by two hand cases built for the boundary,
  `hold-exact` and `over-exact`, after which every reading is separated by the case named for
  it. No reading that reproduces all the published evidence disagrees with the reference on
  the graded set.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 and matches 1 of 366 generated programs and 0 of 34 hand cases; `cheat-const-nothing` (every page empty, every count zero) 0 and 0 of 34; `cheat-pos-first-rows` (the first n rows of the table in arrival order) 0 and 0 of 34; `cheat-const-tiny` (the worked example replayed) 0 and 1 of 34, the one it was copied from; `cheat-forge-hand` (the frozen answers carried in the submission) 0, matching all 34 hand cases and 0 of 366 generated.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 60 s clock is validated by `authoring/page-pass-owe/variants/stamped/` and `authoring/page-pass-owe/variants/linked/`, both written apart from the reference, at 2.5 s and 3.4 s over the generated set against the 60 s limit; the reference is 2.0 s. There is no numeric tolerance - the whole trace is compared byte for byte - and the second implementation behind that is `tests/seal/model.py`, which disagrees with the reference on 0 of 366 generated programs and 0 of 34 hand cases.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, put mechanically over every printed token - the ids of a `pg` line, and d, o, u and w of the closing report - by listing the model branches that can move each and asking the four clusters of each branch. Five decisions came back unsettled and each got a sentence.
  The five: whether the empty-page rule applies in the ledger half as well as the scan half
  ("Throughout both halves"); whether it applies when the hold is full ("whatever the hold
  stands at"); whether a row already handed out could be forced out by it ("takes the row it
  would otherwise leave behind", which names the step-over case rather than the passed-by
  one); whether the hold stops the scan before or after the mark moves ("the mark does not
  move past that row"); and whether d counts rows or hand-outs ("d rows handed out to it over
  the whole run", with `rep-d` fixing the dropped-row case). A fresh session seeing only the
  brief and the agent-facing tree was not run; this is the author-run form.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval. Frozen
2026-09-22.

- Artifacts the agent produces: exactly six files, each collected at its original absolute
  path - `/app/lst/seq.py`, `/app/lst/scr.py`, `/app/lst/owe.py`, `/app/lst/pg.py`,
  `/app/lst/edt.py`, `/app/lst/rep.py`. Nothing else is read from the agent's container. The
  verifier lays those six over a pristine copy of the rest of the tree, so `run_lst.py`,
  `lst/__init__.py`, `lst/spec.py`, `lst/say.py` and the sample lists are the verifier's own
  and a file placed beside the six is never collected.

- The list-file grammar, one run per file, lines in order:
  - `cfg <H>` exactly once and first: H is the hold, the greatest owed weight the service
    carries across every scroll at once.
  - `row <id> <k> <g> <w>`: a row present before anything runs.
  - `open <s> <g> <n> <c>`: scroll s reads tag g, its pages carry at most n rows and at most
    c weight.
  - `next <s>`: serve scroll s a page.
  - `add <id> <k> <g> <w>`, `move <id> <k>`, `tag <id> <g>`, `drop <id>`: edits.
  - ids are unique over the whole file and are never reused, including after `drop`.

- The graded decisions, and what each means:
  1. Place order. The place of a row is its key and then its id; smaller key first, and among
     equal keys smaller id first.
  2. View. A scroll reading tag g sees exactly the rows carrying tag g at the moment it looks.
  3. Ledger phase. A page first drains the scroll's ledger strictly from the front: while the
     page has room and weight left, the entry at the front is handed out if its weight is at
     most the weight left, and otherwise the phase stops.
  4. Empty-page rule. A page that has handed out nothing takes the row it is looking at
     whatever its weight, and the page's weight is spent to nothing by doing so.
  5. Scan phase. The scan takes the rows of the view whose place is strictly after the mark,
     in place order. A row already handed out to this scroll is passed by. A row whose weight
     is at most the weight left is handed out. Otherwise the row is stepped over and comes to
     be owed. The scan stops when the page holds n rows, when its weight is spent, when the
     rows it has stepped over in this page weigh c or more, when the view has no further row,
     or when the hold has no room for the row it is looking at.
  6. Mark. The mark is the place of the last row the scan looked at. Draining the ledger never
     moves it, a page whose scan looked at nothing leaves it where it was, and a scroll opens
     with its mark before every place. When the hold stops the scan, the mark does not move
     past the row that stopped it.
  7. Owed membership, derived. A row is owed to a scroll when it carries the scroll's tag, its
     place is at or before the scroll's mark, and the scroll has not been handed it. The
     ledger lists the rows owed to a scroll in the order they came to be owed; a row that
     stops being owed leaves the ledger, and a row that comes to be owed again enters at the
     end.
  8. The hold. The service carries at most H weight of owed rows across every scroll at once.
     A scan steps over a row only while the weight already owed plus that row's weight is at
     most H. The hold governs only what a scan may step over; an edit that brings a row to be
     owed is not held back by it.
  9. Delivery memory. Permanent, by row id, per scroll. A row handed out to a scroll is never
     handed to that scroll again, and it survives the row leaving the view and coming back.
  10. The closing report. After the last line of the file, for each scroll in ascending scroll
      number, `sc <s> <d> <o> <u>`: d rows handed out over the whole run, o rows owed now, u
      rows in the view now that the scroll has not been handed. Then one line `tot <w>`, the
      total weight of the rows owed across every scroll.

- Printed output, and nothing else: `pg <s>` followed by the ids in the order they were handed
  out, one line per `next`; a page that hands out nothing prints `pg <s>` alone. Then the
  closing report.

- What is checked: every line of stdout, in order, byte for byte, against an independently
  written sealed model, for every graded list file. All-or-nothing.

- Tolerances: none. Exact string comparison of the whole trace. The one limit is the wall
  clock: the whole graded set must finish within 60 seconds, stated in the instruction.

- Ground truth, and where it lives: `tests/seal/model.py` (the independently written model)
  and `tests/seal/gt.json` (the frozen answers for the enumerated hand lists), in a directory
  `chmod 700` before the privilege drop so submitted code cannot read it. The grader first
  asserts the model still reproduces `gt.json` exactly, then compares the submission's traces
  against the model on the enumerated lists and on a population generated inside the verifier
  from a seed drawn after the agent's container is gone.

- Prong C tactics the contract uses: C1 (every rule is fenced from both sides by enumerated
  lists), C3 (the wide and deep families), C4 (exact all-or-nothing comparison over enumerated
  corners plus a shaped generated population).

- Route-around guard: six collected files, everything else replaced by the verifier's pristine
  copy, so the output format, the list grammar and the driver cannot be reshaped and a new
  module beside the six is never collected.

## Decisions and their reasons

- The module that owns the order was called `ord.py` when the contract was frozen and is
  `seq.py` in the tree. `ord` shadows a Python builtin, which made `from lst import ord` read
  as a mistake. The file set, its size and what each file owns are unchanged, so this is a
  rename inside the contract rather than a change to what correct means.
- The frozen contract carried a clause saying that rows coming to be owed at the same moment
  enter the ledger in place order. Nothing can reach it: the scan owes at most one row at a
  time and in place order already, and an edit touches one row. A sentence no test can reach
  is a sentence the instruction must not carry, so the clause was dropped from both.

- The page emits rows in the order they were handed out (ledger entries in ledger order, then
  scan rows in place order) rather than in place order. Emitting in place order would hide the
  ledger order from the trace and make two readings of the ledger indistinguishable; the
  contract doc requires that two readings reproducing all published evidence must not disagree
  on the graded set.
- The hold governs only the scan, not edits. Holding edits back would make owed membership
  stateful (a row would have to remember it was refused), and the derived definition in
  decision 7 is what forces the ledger to be recomputed rather than logged.
- The scan is bounded by three separate quantities (rows handed out, weight left, weight
  stepped over) rather than by a single one, because a scan bounded only by rows handed out
  would step over the whole remaining view whenever nothing fits.
- Ids are never reused. Identity games are `focus-return-point`'s mechanism, and reusing ids
  here would add a second axis without adding a second discovery.
- One run per list file. A reset rule would add prose without adding an interaction.
- Every isolation probe carries the shipped service rather than the reference. The first
  build wrapped the reference, which meant a probe whose attack was blocked still printed
  the right answers and scored 1 - proving nothing about the isolation and breaking the gate
  that says every cheat scores 0. With a wrong engine underneath, the only route to a 1 is
  the attack landing. The one probe that keeps a working service is the uncollected-file one,
  because the boundary it tests is whether that file is collected at all.
- The answer-key probe loads `tests/seal/model.py` and answers from it when it can. It cannot,
  because the directory is 0700 and root-owned before the privilege drop, so it falls back to
  the shipped service and fails on the enumerated cases. That is the form that would score 1
  if the seal were readable, which a probe that merely opens the file and writes a note would
  not.

## Stage 7 re-attack, and the honest estimate

Read the final brief again with the built tree in front of me. I cannot run a cold solve:
I wrote the sealed model, so any plan I form now measures memory rather than difficulty,
and a self-probe reported as cold by a contaminated author is worse than none. What stands
in its place is measured rather than asserted.

- The shipped service is the first plan, and it prints a coherent page for every list file
  it is given. Running it confirms only that it runs: the one line the brief quotes settles
  the order of two rows sharing a key and nothing else.
- Twenty-eight plausible-but-wrong readings were written down as file-level patches and
  driven against the enumerated set. Twenty-six were separated on the first run. That is
  twenty-eight distinct implementations that satisfy a careless reading of the same stated
  rules, which is the measurement behind the claim that the plan is not one-shot.
- The two that survived were both boundary readings - the hold tested strictly and the
  stepped-over allowance tested strictly. A survivor that the published evidence does not
  rule out is a contract gap, not difficulty, so both were closed with an enumerated case at
  the boundary rather than left to carry weight.
- No graded decision is reproducible by an exact rule of two terms or fewer over values the
  service already has in hand (`tools/onelinecheck.py`, four questions, 5546 samples).
- Every branch the rules define actually fires in the generated population. Over 180 small
  programs the scan hands out 2252 rows, steps over 1055, takes 62 under the empty-page rule,
  is stopped 72 times by the hold and passes by 7 rows it had already handed; the ledger hands
  out 836 and stops at its front 260 times; 149 rows come to be owed by an edit. The thinnest
  of those, a row moved forward across a mark after it was handed out, is one in twenty-six
  programs, which is roughly fourteen of the three hundred and sixty small files in a graded
  set, and `scan-skip` pins it exactly whatever the draw.
- The gate rejects two implementations that are exactly correct: 153.9 s and 126.7 s over
  the six scale files against a 60 s limit, with the reference at 1.9 s and the two
  independent correct variants at 2.5 s and 3.4 s. The first of those is the closest thing
  to a cold solve this session can produce honestly: it is the shipped service with every
  stated rule fixed and its view left in the shape it ships in, which is what a careful
  literal reading of the brief produces, and it scores 0.

Where the risk is, stated plainly. Every rule is in the brief, and an agent that implements
each sentence literally - a per-tag ordered index, a bisect resume, membership recomputed
rather than logged - passes. That is the path to a solve and it is a real one; the task
rests on how many of the ten rules a first implementation gets exactly right with no
feedback of any kind, rather than on any of them being hidden. The derived-membership rule
is the weakest of the claims, because it is stated in one sentence and an agent that reads
it literally gets it without discovering anything. The scale gate is the strongest, because
it kills two implementations that are semantically perfect.

The estimate stays at 2 of 8. The re-attack did not lower it and did not raise it above the
band; if anything it widened my own uncertainty to roughly 2 to 4, which is inside the band
in both directions.

## Quality self-review (docs/QUALITY-REVIEW.md), criterion by criterion

- Every behaviour the tests check is described in the instruction: the walk is
  `authoring/page-pass-owe/trace.md`, 88 rows, and `tools/tracecheck.py` is clean.
- Every behaviour the instruction promises is tested: each of the ten graded decisions has
  at least one enumerated list file named for it in `tests/cases.py`, and the Readings table
  names the case that separates each wrong reading.
- Output files named with absolute paths: the six collected files are named in the third
  paragraph of `instruction.md` and listed in `artifacts`.
- Exact schema specified: the list-file grammar is the first paragraph and the printed
  format is the second-to-last.
- Boundaries and conventions settled: place order and its tie (`order-tie`), `<=` at the
  weight left (`scan-weight`), `>=` at the stepped-over allowance (`over-exact`), `<=` at
  the hold (`hold-exact`), the empty-page rule on both sides (`empty-head`, `empty-not`),
  and the empty page printing its scroll alone (`plain-run`).
- Every graded quantity defined: d, o, u and w each have a clause in the report paragraph,
  and `rep-d`, `rep-u` and `rep-tot` fix what each excludes.
- Nothing contradicts the reference: every number in `instruction.md` and in the three
  explanation fields was re-derived from `tests/gen.py` and from the timing runs after the
  scale change, not carried over.
- Verifier requirements in the text: the six collected files, the pristine overlay, the
  uncollected seventh file, and the 60 second clock.
- Test code structured and commented: `tests/test_outputs.py` carries the frozen contract as
  its docstring and one section per source of evidence.
- Tests deterministic: the population is seeded from a nonce and compared against the model;
  no wall-clock dependence except the stated limit, which is the graded limit itself.
- Neither `tests/` nor `solution/` is copied into the agent image: `environment/Dockerfile`
  copies `app_src/` and nothing else.
- Pinned packages: `pytest==9.1.1` and `pytest-json-ctrf==0.5.2` in `tests/Dockerfile`; the
  agent image installs nothing.
- No dangling references: `tools/imagecheck.py` assembles what the image would hold, drops
  the reference in and runs all four shipped list files - clean.
- Solution computes the answer: `solve.sh` copies six source files beside it and runs the
  service on two sample lists.
- The answer cannot be read out of the environment: `tools/extraneouscheck.py` and
  `tools/deadfieldcheck.py` are clean, and the leak audit above lists what was considered.
- Category and tags: Software / Databases, with `tools/catcheck.py` measuring the category's
  vocabulary at 160045 hits in the environment against 154 in the prose. The six tags name
  mechanisms, not the taxonomy.
- Metadata: the three explanation fields describe the measured behaviour of this bundle, and
  `relevant_experience` claims only what building this task evidences.
- Known risk, reviewed and left: `tools/simcheck.py` reports `environment/Dockerfile` and
  `tests/Dockerfile` as near-identical to the retained bundles, and `tests/test.sh` at 0.675.
  All three are prescribed shapes - `docs/RULES.md` fixes the base image, the pytest pins,
  the artifact-parent mkdirs and the reward path, and `docs/VERIFIER-ISOLATION.md` fixes the
  two-stage order. `tests/reap.py` and `tests/test_outputs.py` were rewritten after simcheck
  flagged them as copies; the remaining three cannot be varied without breaking a rule. The
  same tool reports that this task grades nothing an earlier one grades.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Difficulty record in band | pass | 100/100 before code, 100/100 again at Stage 7 against the built tree |
| `preflight.py` | pass | no errors; 19 warnings, all the same unused-public-function false positive the retained bundles carry, because the check does not count a call written `owe.front(sc)` |
| `tracecheck.py` | pass | clean; 94 rows |
| `extraneouscheck.py` | pass | every shipped file reachable, distinct and host-free |
| `deadfieldcheck.py` | pass | clean after the unread scroll number was removed from the record |
| `catcheck.py` | pass | software vocabulary: 160045 hits in the environment against 159 in the prose |
| `hintcheck.py` | pass | none |
| `structcheck.py` | pass | none |
| `solvecheck.py` | pass | clean |
| `onelinecheck.py` | pass | four graded decisions, 5546 samples, none reproduced by a rule of two terms or fewer |
| `readingcheck.py` | pass | 34 readings, all separated by an enumerated case; every enumerated case separates at least one |
| `forgecheck.py` | pass | `cheat-forge-hand.sh` carries `gt.json` verbatim; the layer report grades all 50 |
| `simcheck.py` | reviewed | conceptually distinct from every retained task. `environment/Dockerfile`, `tests/Dockerfile` and `tests/test.sh` stay near-identical because their shape is prescribed; `tests/reap.py` and `tests/test_outputs.py` were rewritten after being flagged as copies |
| `textcheck.py` | pass | against `expert-defer-shed`: no finding on any axis after the instruction was reworked for possessives, short sentences, paragraph variance and one oxford triad |
| `imagecheck.py` | pass | the image would hold 14 files; the reference dropped in runs all four shipped list files |
| Reference against the sealed model | pass | 0 disagreements over 366 generated list files and 34 hand cases |
| Two independent correct variants | pass | 0 disagreements each; 2.5 s and 3.4 s against the 60 s limit |
| Resource gate measured | pass | reference 1.9 s over the six scale files; view re-derived per page 153.9 s; view re-sorted per edit 126.7 s |
| Agent image builds | pass | `tools/docker_trial.py --build` |
| No answer leaked into agent image | pass | `environment/Dockerfile` copies `app_src/` only; `imagecheck` lists what the image holds |
| `docker_trial.py` oracle = 1 | pass | 37 tests passed, reward 1 |
| `docker_trial.py` nop = 0 | pass | 1 passed, 36 errors, reward 0 |
| Cheat layer report | pass | 50 of 50 caught by the layer written for them |
| Cheats all score 0 in the container | pending | the full two-container sweep is running on the final set of 50 |
| `harbor check` rubric | not run | harbor is not installed in this environment; every other gate was run instead |

## Open questions and next steps

Next: build the environment (Stage 3), then the sealed model and the reference (Stage 4),
then measure the wide and deep timings so the resource gate stops being a promise.
