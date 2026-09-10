# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 6 - Anti-cheat` (environment, verifier, reference, instruction and metadata written;
local gates running)

## Assistant's assigned role

Storage-engine engineer who has worked on the coordination layer of a transactional store: the
service that hands out claims on items, decides which waiting transaction may go next, and
decides which one to cut when a set of them can no longer make progress. Familiar with mark
tables that are not the shared/exclusive family, with the difference between the mark a
transaction asked for and the mark it ends up holding, and with the fact that "who is waiting
for whom" is a question about what would happen if somebody left, not about who conflicts.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The first prompt carried no seed repository.
- Task shape chosen: authored-on-top does not apply; the environment is written from scratch.

## Task summary

`/app/hold/` is the coordination service of a storage engine. Transactions take claims on items
in one of five marks; a claim on an item the transaction already holds raises its mark; the
service sweeps an item whenever its claims or requests change, deciding which pending requests
to grant; and when the waiting transactions form a cycle it cuts one of them. The shipped
service runs and prints a trace, and is wrong in five modules at once. The agent rewrites
`mark.py`, `item.py`, `wait.py`, `cyc.py` and `txn.py` so that the trace matches the stated
rules on every program, inside a stated execution limit.

## Why it is hard

The wait relation is stated as a removal, not as a conflict: T waits for U when the sweep of
T's item, run with U's claims and U's request taken out, would grant T. Every retrievable
design builds the graph from conflicting holders, and that rule differs from the stated one in
three directions at once - it invents edges to holders whose departure would not help, it
misses edges to holders that conflict with nothing the waiter asked for, and it gives an edge
to each of several conflicting holders when none of them alone is the obstacle. The engine's
observable behaviour differs only in which transaction is cut, which happens late and only in
programs that reach a cycle.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the correct wait relation is not a rule
  to be recalled but a consequence of the sweep, and the sweep is
  itself decided by three rules the agent has to hold at once (the join of held and asked
  marks, self-exclusion, and the pin an ungrantable raise puts on the item). The first plan is
  a coherent, memorised lock manager whose edges are wrong in both directions; the wrongness
  shows up only as a different cut, several hundred steps in.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C3, C4. A1 the conflict-based wait-for graph is the memorised answer
  and agrees with the stated one on every item without a stuck raise; A2 the
  brief describes marks, raises, pinning and cutting operationally and never names them; B2 ten
  rules must hold together and several change what another means; C1 both sides are fenced, so
  cutting a phantom cycle fails as surely as missing a real one; C3 recomputing the whole
  relation after every step, and answering the removal question by enumeration, are both
  exactly correct and both miss the stated limit; C4 exact traces over enumerated programs plus
  generated families drawn from a seed the submission never sees, all-or-nothing.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was a granted set plus one wait queue per item, an aggregate mark for the grant test, edges
  from each waiter to every conflicting holder, a DFS cycle search on block, and cutting the
  youngest transaction. Worked by hand it is wrong at four of those five points. The aggregate
  mark cannot express self-exclusion because a join cannot be subtracted. The single queue
  cannot express raises served in first-take order ahead of fresh claims. The conflict edges
  are wrong in both directions - I built the three-transaction, two-item case below, where the
  conflict rule finds no cycle at all and the stated rule finds one. And the cut rule is fewest
  claims held, not youngest. I could not have committed to the right plan without working a
  stuck raise through by hand.
- Estimated solves out of 8: 2 (design target 1-3)
- Difficulty record score (tools/difficultycheck.py, before Stage 2): 97/100, in band, first
  attempt, no hard stop. Record at `authoring/claim-raise-cut/difficulty.toml`. The three
  points lost are the shape axis measuring an empty tree; it is re-run at Stage 7.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set;
  this is a new task and no pipeline anchor exists for it.
- Score history: 2026-09-10, 97, first record.
- Leak audit (docs/DIFFICULTY.md): the join of the mark table is the derivation the task is
  about, so only the pair table ships and no join table exists as data anywhere in the tree.
  The wait relation is never printed and no shipped function returns it. Whether an item is
  pinned is derived by the sweep, never stored. The tree ships programs and no expected traces;
  every expected trace lives in the sealed verifier and the graded programs are generated there
  from a seed drawn after the agent's container is gone. No shipped module carries an entry
  point the driver does not call.
- Expert path, described step by step: run the shipped service on the shipped programs and read
  what it prints for a raise; read the pair table and derive the join, since no rank over the
  five marks reproduces it; rebuild the item as two ordered groups, raises first in first-take
  order, with the pin an ungrantable raise puts on fresh claims; make every grant test exclude
  the asking transaction's own claims; write the wait relation from the removal definition and
  check it by hand against a fresh claim standing behind a stuck raise; derive that a single
  departure unblocks a request only when it was the only obstacle, which is what turns the
  removal into a small candidate set; find cycles, cut by fewest claims held, release, sweep
  again and repeat until no cycle is left; when the wide programs miss the limit, recompute the
  relation only for the items a step touched.
- Originality check: searched 2026-09-10 for the removal formulation of the wait relation and
  for conversion-queue lock manager designs. What is retrievable is the granted-queue plus
  convert-queue design, a starvation barrier, a wait-for graph built from conflicting holders
  and "abort the youngest", in transaction-processing texts and in public course projects with
  published solutions. None of it states the removal definition, the five-mark table used here,
  first-take ordering of raises, the pin rule, or the fewest-claims cut. The retrievable design
  is the poisoned prior, not the answer.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: `/app/hold/mark.py`, `/app/hold/item.py`, `/app/hold/wait.py`,
  `/app/hold/cyc.py`, `/app/hold/txn.py`. Nothing else is read from the agent's container.
- What is checked: the verifier lays those five files over its own pristine copy of the tree
  and runs `/app/run.py` on each graded program. The trace the run writes to stdout must equal
  the sealed model's trace line for line, for every graded program, and the whole graded set
  must finish inside the stated wall clock. All or nothing.
- Ground truth: two independent sources that must agree. `tests/seal/model.py` is a sealed
  reimplementation of the rules, written from the contract rather than from the reference, and
  `tests/seal/gt.json` freezes the model's trace for every enumerated program. The grader
  asserts the model still reproduces `gt.json` before it grades anything, so a drifted model
  cannot redefine correct. Generated programs are graded against the model alone, from a seed
  drawn after the agent's container is gone.
- Tolerances: none. Exact string equality on every trace line, and the execution limit is a
  hard wall clock over the whole graded set.

### The rules the contract grades

1. Marks are `scan`, `edit`, `grow`, `pin`, `seal`. `hold/tab.py` ships the pair table of
   marks that may stand together on one item, held by different transactions. The table is
   frozen and is the only mark data that ships.
2. The mark a request is tested in is the join of the marks the asking transaction already
   holds on that item and the mark it asked for: the least mark that excludes everything all of
   them exclude. Every set of marks in this table has exactly one such mark (checked). No rank
   over the five marks reproduces the join: `join(scan, pin) = edit` and `join(edit, grow) = seal`.
3. A request is grantable when its mark stands with every claim held by every *other*
   transaction on the item. The asking transaction's own claims are not tested against.
4. A sweep of an item walks the raises first - requests by transactions that already hold the
   item - in the order those transactions first took the item, granting each that is grantable
   and passing over each that is not. It then walks the fresh requests in request order,
   granting while grantable and stopping at the first that is not. If any raise was passed
   over, no fresh request is granted at all.
5. A grant appends the asked mark to the asking transaction's claim stack for the item; its
   effective mark is the join of that stack. A drop removes the last entry of the stack.
6. T, with a pending request on item k, waits for U when the sweep of k, run on the current
   state with every claim U holds and every request U has removed from the service, grants T's
   request. U is any live transaction other than T's own.
7. After every program step, once every transaction granted by that step has run as far as it
   can, the service looks for a cycle in that relation. While one exists it cuts the
   transaction on a cycle holding claims on the fewest items, breaking ties by the later
   pending request and then by the larger transaction number.
8. A cut releases every claim of the victim, cancels its pending request, discards its backlog,
   and makes every later step of that transaction a no-op. Released items are swept in the
   order the victim first took them.
9. A transaction whose request is granted is appended to a ready list and resumes in grant
   order, one at a time, each running its backlog until it blocks, ends, or runs out.
10. `end` releases every claim in first-take order and finishes the transaction.

### Prong C tactics in the contract, and the route-around guard

- C1: enumerated programs fence both sides of every rule. `plain` and `crowd` programs have no
  cycle at all, so an engine that cuts on a phantom cycle fails them; `knot` programs have one,
  so an engine that misses it fails those.
- C2: the obvious oracle is denied. The relation is never printed, no installed lock manager
  implements these marks or these rules, and the trace of the shipped service is wrong, so
  running it confirms only self-consistency.
- C3: two families are correct-but-infeasible - rebuilding the relation for every pending
  request after every step, and answering the removal question by trying every participant.
  Both produce the reference's traces exactly and both miss the limit. Measured before the
  design depends on them (see the measurement section once run).
- C4: enumerated programs aimed at each graded decision, plus generated families from a seed
  drawn after the run, exact traces, all or nothing.
- Route-around guard: only the five modules are taken. `run.py`, `hold/tab.py`, `hold/out.py`
  and `hold/__init__.py` are frozen and the verifier uses its own copies, so the program format,
  the trace format and the mark table cannot be moved, and the task cannot be reshaped into
  emitting an answer file.

## Decisions and their reasons

- The wait relation is a single removal, not a minimal blocking set. With two conflicting
  holders neither departure alone would grant the request, so there is no edge and no cut. That
  is a policy - cut only when one departure provably unblocks - and it is stated in the brief.
  It also makes the memorised AND-wait graph over-cut, which is a graded difference.
- Raises are passed over rather than barring later raises, so one stuck raise does not stop
  another transaction from raising. The pin applies to fresh claims only.
- The mark table was chosen so that the domination order is a lattice but not a chain: `scan`
  and `pin` dominate nothing, `join(scan, pin) = edit`, `join(edit, grow) = seal`. Verified by
  enumerating every non-empty subset.

## What was built, and what it measures

Three implementations of the contract were written apart and made to agree:
`tasks/claim-raise-cut/solution/` (the reference, five modules), `tests/seal/model.py` (the
sealed model, different structures throughout - exclusion sets against a memoised pair join, a
holder index of sets against per-mark counts, Kosaraju over the whole relation against Tarjan
from the edges that changed, a version stamp per item against a set of items to revisit), and
`authoring/claim-raise-cut/slow.py`, the literal reading of rules 6 and 7 with nothing optimised.
Reference and model agree on 3,280 generated programs plus the enumerated set; all three agree on
the enumerated set and on 288 small generated programs. The three-way run is what says the
reference's candidate classes and the model's participant groups never change an answer.

### The resource gate, measured (2026-09-10)

437 programs, 92,000 steps, one CPU, `LIMIT=60` in `tests/test.sh`:

| service | seconds | verdict |
|---|---|---|
| reference | 5.3 | passes with 11x headroom |
| whole relation searched for rings on every step | 9.4 | passes; a correct variant, not a cheat |
| relation rebuilt for every item that holds a request | 179.0 | fails |
| removal asked of every participant, one at a time | 181.2 | fails |
| removal asked of every live transaction | 192.5 | fails |

All five produce exactly the reference's traces. The limit is the only thing separating them,
and each fast path follows from an invariant: a sweep reads its own item and nothing else; a
transaction absent from the item cannot change that item's sweep; holders carrying the same mark
with no request of their own are interchangeable in it. The first three families are shipped as
cheats and the fourth as a correct variant.

### Wrong readings

`authoring/claim-raise-cut/make_readings.py` builds twenty whole-service readings, each the
reference with one decision taken the other way. Measured over the generated population
(`readings.py`), they move between 1.4% and 71% of programs, and `tools/readingcheck.py` reports
every one of them separated by an enumerated case. `cut-one-ring` - considering one ring rather
than comparing across all of them - is separated only when the implementation's own traversal
reaches the wrong ring first, which is a per-process fact about set iteration order; it is
caught by `cut-again` or `ring-pair` depending on the run, and it moves 8.5% of the population,
so the graded set catches it with near certainty rather than by construction. That is recorded
here rather than papered over.

### Two defects the differential found, both in the reference

- Dirty items were popped from the cached relation and rebuilt in one interleaved pass, so an
  item processed later could delete the edges an earlier item had just added. Set iteration order
  decided whether a program hit it. Fixed by two passes: pop every dirty item's old entries
  first, then rebuild them all.
- The roots for the incremental ring search were cleared before the cut rather than after it, so
  when one step left two rings, cutting the first left the second with no root to be found from.
  Fixed by clearing the roots only on the clean exit.

Both were found by the reference-versus-model run, neither by any hand case, and the second is
now `cut-again` and `ring-pair` in the enumerated set.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference agrees with the sealed model | pass | 3,280 generated programs, 0 mismatches |
| Three-way agreement with the naive reading | pass | enumerated set plus 288 generated |
| Resource gate measured | pass | table above; naive families at 3.0x, 3.0x and 3.2x the limit |
| `onelinecheck` | pass | no graded decision has an exact rule at depth <= 2 |
| `readingcheck` | pass | 20 readings, every one separated by an enumerated case |
| `catcheck` | pass | software vocabulary: 256 in the environment, 58 in the prose |
| `deadfieldcheck` / `extraneouscheck` / `solvecheck` / `hintcheck` | pass | clean |
| `simcheck` | judged | Dockerfiles are near-identical to the retained bundles' by necessity; the same pairs sit at 0.88-0.99 between tasks that passed. `reap.py` was rewritten after it came out at 0.96 |
| `preflight.py` | pass | no errors; the unused-function warnings are the tool not resolving method calls, and the two genuine ones were deleted |
| Host trial, reference | pass | reward 1, worker 6.7 s against the 60 s limit |
| Host trial, shipped tree | pass | reward 0, killed by the limit |
| Container oracle | pass | reward 1, 28 tests, 62 s |
| Container nop | pass | reward 0; the shipped service is killed by the limit and the grader has no record to read |
| Container correct variants | pass | all three score 1: 9.1 s, 10.1 s and 10.4 s of the 60 s limit |
| Container probes | pass | all ten score 0 |
| Cheats all score 0 | pass | 34 of 34 score 0. Twenty wrong readings caught by the enumerated case named for each; four of those - the conflict rule, the AND rule, the barrier and granting a raise in the mark it asked for - are also slow, so at full scale the limit reaches them first and `small_scale.py` confirms the case with the large families removed. Four correct-but-slow families caught by the limit alone. Ten probes: the forgery is caught by the generated population and by nothing else, which is what it was written to show |
| `harbor check` rubric | not run | no model API key in this environment; every other gate was run |
| `textcheck` against the passed set | judged | burstiness 0.818 against a passing band of 0.79-0.92, short sentences 32% against 23-40%, paragraph variance 29.4 against a band whose floor is 29.7 |

## Stage 7 re-attack, read cold against the finished bundle

The instruction states every rule, which is the house style and the fair one, so the question is
what a frontier agent still has to work out. Reading the final brief as the probe agent will:

The first plan it induces is a lock manager, and most of its shape is delivered - two ordered
groups per item, a claim stack, a join over the pair table, a cut rule with its tie-breaks. What
is not delivered is anything about the wait relation except its definition, and the definition is
one sentence whose consequences are the task. An implementer who believes the definition is a
paraphrase of the familiar rule writes the conflict test, which is the natural shortcut and is
wrong in three directions: it invents edges behind a pinned item, misses edges to holders that
exclude nothing the waiter asked for, and gives an edge to each of several conflicting holders
where the definition gives none. Nothing in the trace shows the relation, so that shortcut passes
every ordinary program and then cuts the wrong transaction hundreds of steps in. That is the
part of the design I would still expect a careful agent to get wrong, and it is why `edge-miss`,
`edge-phantom` and `edge-share` are enumerated rather than left to the generated set.

The second half is the limit, and it is not a semantic replan: an agent that implements the
definition literally is correct and misses the limit by three to four times. Getting inside it
needs three separate readings of the same invariant - a sweep reads its own item, only a
transaction present on the item can change that sweep, and holders carrying the same mark with no
request of their own are interchangeable in it. The third is the one that bites hardest: taking
the removal question to the participants but not collapsing them still takes 181 seconds, and
taking it to the holders whose marks exclude the request takes 243, because a raise stuck across
a crowd excludes the whole crowd.

Honest estimate after the build: 2 of 8, with a range of 2 to 4. That is the number in the
record. The risk I would flag to a reviewer is the one above: the semantic difficulty rests on
the consequences of a stated definition rather than on anything withheld, so an agent that reads
the definition carefully and refuses the familiar shortcut gets the semantics right and then has
only the measured limit to clear. The counterweights are that the shortcut is what the whole
literature says, that the trace gives no feedback on the relation, and that the limit is real
rather than nominal.

The cold self-probe was not run. Every rule here was designed before the environment existed, so
a solve by this author measures memory rather than difficulty, and a self-probe reported as
passed by a contaminated author is worse than none. What stands in its place is the reading
separation table, which is a measurement of what a wrong plan costs, and the fact that four
correct-but-naive implementations of the stated rules were written and all four missed the limit.

## Quality self-review, criterion by criterion (docs/QUALITY-REVIEW.md)

- Every behaviour the tests check is described in the instruction: the twelve numbered rules in
  `tests/test_outputs.py` map to paragraphs 4 to 11 of `instruction.md`, and the trace format in
  paragraph 12 to `hold/out.py`.
- Every behaviour the instruction promises is tested: each rule has an enumerated case named for
  it in `tests/cases.py`, and `tools/readingcheck.py` confirms each case separates the reading it
  is named for.
- Output paths: the graded files are the five under `/app/hold/` and the instruction names all
  five with absolute paths.
- Schema: the program format and every trace line are specified in the instruction.
- Prose: no headings, no bullets, plain ASCII, each requirement stated once. Read through for
  runs of same-shaped sentences; the rule paragraphs deliberately vary opener and length.
- Verifier rigor: the tests demand the trace of an actual run of the submitted modules over
  programs generated after the agent's container is gone; `test_outputs.py` is commented section
  by section; nothing depends on wall-clock time except the declared execution limit, and the
  generated population is seeded.
- Environment hygiene: `environment/Dockerfile` copies `app_src/` only; `tests/` and `solution/`
  are not in that context. The verifier installs `pytest==9.1.1` and `pytest-json-ctrf==0.5.2` at
  build time and reaches no network at trial time. No apt package is installed at all: `setpriv`,
  `setsid` and `timeout` are already in the base image and `reap.py` reads `/proc` rather than
  calling `pkill`.
- Dangling references: `turn.txt`, `hold/mark.py`, `hold/item.py`, `hold/wait.py`, `hold/cyc.py`,
  `hold/txn.py`, `hold/tab.py`, `hold/out.py`, `run.py` and the worked-example line all checked
  against the tree by running it.
- Solution quality: `solve.sh` copies five modules and runs the service on two shipped programs;
  it computes nothing by echo.
- Anti-cheating: no expected trace ships; the mark table ships but its join does not; the sealed
  model and the frozen answers sit in a `chmod 700` directory owned by root.
- Metadata: category Software, subcategory Databases from that row, six tags naming the actual
  mechanisms rather than the taxonomy, ten expert hours, and the legacy naming is declared in
  `difficulty_explanation` as a design choice.

## Three probes that scored 0 for the wrong reason

Worth recording because the reward said nothing about it in any of the three cases:

- The forgery rebound `Svc = Forge` and then called `Svc.step(self, st)` inside `Forge.step`,
  which resolves the global name at call time, so it recursed instead of forging. It scored 0 by
  crashing. Fixed by holding the base class in `_BASE` before the rebinding; it now passes all
  twenty-five enumerated programs and fails only the generated ones, which is the whole point of
  it.
- The hang and the malformed-record probes spliced a second `step` into the class body ahead of
  the original, and the original, being later, won. Both scored 0 as ordinary wrong services.
  Both now rebind `Svc.step` after the class instead.

The layer report is what found all three. A cheat suite graded on reward alone would have
reported thirty-four clean zeroes and proved nothing about the isolation.

## Open questions and next steps

Package and deliver. `harbor check` was not run: no model API key is available here.
