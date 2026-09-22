# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` (built 2026-09-22; container gates run, see the table)

## Assistant's assigned role

You are a storage-engine engineer who owns the lock manager of an embedded transactional
store: the part that decides which transaction holds which lock, in which mode, who waits
behind whom, when a pile of row locks is traded for one table lock, and who dies when a wait
cycle closes. You have written and debugged lock queues, escalation and deadlock victims, and
you know that fairness between waiters and holders is a policy rather than a law.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree is
  written here, not degraded from a source; identifiers are chosen in the legacy register directly
  (`lm/`, `held`, `wait`, `grant`, `esc`, `dead`, `settle`, `seq`, `tgt`) and no name misdescribes
  what it holds
- Proper-noun sweep done? No product, project, company or database name appears anywhere in the
  agent-facing tree; the domain terms that remain (lock, row, table, transaction, commit) are the
  ordinary vocabulary of the work and carry no provenance
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the lock manager of an embedded transactional store. A script file gives a threshold
and the ops of a set of transactions - lock a row or a whole table in shared or exclusive mode,
drop one lock, commit - and a round-robin driver runs the transactions one op at a time, a
transaction sitting out its turn while it waits for a lock. `/app/run_lm.py` prints a line for
each thing that happens: a grant, a wait, an escalation, a commit with the number of lock
records it released, a deadlock victim with the same number. The shipped manager is the
textbook one - a request waits only for holders, a queue per target is woken on release,
escalation queues for the table lock like any other request, the youngest transaction on a
cycle dies. The specification it has to meet is the store's own: a request also waits behind
every earlier waiting request it conflicts with, across the row and table level, unless that
waiter is itself waiting, directly or through other waits, on the requester; the manager
settles to a fixed point after every op; escalation is tried once, behind every waiter, and
taken now or given up; a table lock swallows the row records it covers and later rows under it
are granted without a record; the victim is the transaction on a cycle holding the fewest
records. The agent fixes the six files under `/app/lm/` so every script's trace matches.

## Why it is hard

The first plan is the textbook manager and it is what the tree already is; the rule that
replaces it makes waiting a property of the whole wait relation rather than of a queue, and the
rule after that makes what a transaction holds a different thing from what it asked for.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable lock manager grants whatever is compatible with the holders of a target, wakes that target's queue on release, queues an escalation like any other request and kills the youngest transaction on a cycle, and every one of those is wrong here at the first decision point. A request is behind every earlier conflicting waiter across the row and table level unless that waiter depends on it, which is a reachability question over the wait relation as it stands, so it has to be asked again after every op and a wait added on one table grants a request on another; escalation is evaluated behind every waiter and taken now or abandoned, and taking it collapses row records into a table record that changes what every later row waiter conflicts with, what later rows of that table cost, and the count the victim rule and the end line read. A per-target queue design has to be taken apart, not corrected, and the wrongness shows up only in the order of grant lines and in two numbers.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped tree is the textbook manager, the model's prior implemented faithfully, and it is the wrong answer; A2 the brief states what a request waits behind, what escalation tries and gives up and what a victim releases, and never names a wait-for graph, a soft edge, queue rearrangement, opportunistic escalation or multi-granularity locking; B2 six rules hold at once and each changes what a correct implementation of the others is; C1 both sides are graded, so holder-only granting and blanket queueing both fail; C3 the deep family makes a search-per-pair manager infeasible inside the stated limit while leaving it exactly correct, and the fast path follows from the invariant that nothing in the wait relation changes between two grants; C4 every script matches line for line against a population generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was a lock table keyed by target with holders and a FIFO queue per target, grant when compatible with the holders, wake the queue on release, a wait-for graph from waiters to holders with the youngest transaction as the victim, and escalation as a table request that queues when blocked. It is wrong four times over: a request is behind earlier waiters it conflicts with across the row and table level, so the queue is one order over the whole manager; the exception for a waiter that depends on the requester makes behind-or-not a question about the current wait relation, so the state has to be settled after every op rather than woken per target; escalation is never queued, is refused by any waiter that does not depend on the escalating transaction, and swallows the rows it covers, so holdings are records with coverage rather than a set of targets; and the victim is chosen by records held and then by recency, which the collapsed records change. A wait added anywhere can grant a request elsewhere, and a design that decides at arrival or on release passes every simple script and fails the late one. My own first reference, written from the contract with every rule right, then searched the relation afresh for every pair and took over 300 seconds on one deep script; the closure-per-pass form it was replaced by is the eighth step of the expert path.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8 (range 1-4), unchanged at the Stage 7 cold re-attack
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 98/100, in band, no hard stop; nothing was changed between attempts because there was only one. The two points not taken were the resource gate, declared absent until measured. At Stage 4 the deep family was measured - a search-per-pair manager over 300 seconds against 4.5 for the reference on one script - and the record now declares the gate as present and measured; with the tree built the same command measures 347 environment lines, 6 editable files and 399 reference lines and scores 100.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 record scored 98 before code; 100 after the gate was measured and the tree built
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent discover, name or verify it without reasoning? Answer must be "nothing": the frozen half is the parser, the round scheduler and the writer, and none of it computes a conflict, an edge or a reachability; the trace carries no sequence number or queue position; the sample scripts ship without their output and the brief quotes one line of one script, the wait line the fairness rule forces; the shipped holdings are a dict of targets with a mode and no coverage, so the record store has to be built; the shipped escalation counts grants in a tally and never decrements; `tools/onelinecheck.py` finds no exact rule at depth two for any of the four watched quantities (whether a request no holder blocks is granted, whether an escalation is taken, whether a request is covered, whether the victim is the oldest).
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the shipped scripts and read the quoted line to find which module decides that a request waits; rebuild holdings as records with a mode, an upgrade in place, coverage by a table record and release of the rows a table grant subsumes; replace the per-target queues with one sequence of waiting requests and an overlap test between a row and its table; write the grant rule as a reachability question over the wait relation, evaluated fresh from the current holders and waiters; write settling as a fixed point after every op - earliest grantable request first, escalation after each row grant, then the hard cycle and its victim; write escalation as a request evaluated behind every waiter, granted now or abandoned; choose the victim by records held and then by the most recent request; time the deep script and answer every dependence question of a settle pass from one closure of the relation, looking for a cycle only after an op has added a wait.
- Originality check: searched 2026-09-22 for the mechanism. What the literature carries is holder-only two-phase locking with a wait-for graph and a youngest or cheapest victim (every textbook), the PostgreSQL lock manager's soft and hard queue edges with queue rearrangement when a deadlock check runs, and SQL Server's and DB2's lock escalation at a fixed count, one skipping when blocked and one queueing. No public source evaluates behind-or-not from the wait relation after every op, refuses an escalation on account of a waiter, or grades the record count an escalation collapses. The retained bundles grade nothing of this shape: none is a lock manager and none has a wait relation; `tools/simcheck.py` reports that this task grades what no earlier one grades.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/lock-behind-escalate/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 90 rows walked - 4 test functions, 37 enumerated cases, 6 artifacts, the pristine overlay, the 600 second clock and 41 rules of the sealed model split one per rule with its lines - plus 20 readings and 4 shortcuts; no NOT STATED row survived, and `python tools/tracecheck.py lock-behind-escalate` is clean. One note remains and is structural: the readings table is built by emit.py at import, so the tool cannot read the names and they are cited by hand.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 21 readings were written as whole managers by `authoring/lock-behind-escalate/emit.py` and measured by `python tools/readingcheck.py lock-behind-escalate`. Twenty are separated by the enumerated set, and `cheat_report.py` asserts that each is caught by the case named for it, which holds for all twenty. The twenty-first, a request that waits behind later conflicting waiters as well, turned out to agree with the reference on every script: a later conflicting waiter is itself behind the request, so it always waits on the requester and the exception always applies. It is retired from the cheats and recorded in the trace as a reading that the published evidence does not need to rule out, because it is correct. Two hand cases were added when the first run showed gaps: `skip-soft-path`, where dependence runs through a waiter queued behind another waiter, and `soft-not-dead`, a cycle that closes only through a queued request; and `drop-table` gained a third transaction whose lines mark the rounds, because without it the wrong reading and the right one printed the same lines in the same order one round apart.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 in the container with 26 of 40 graded assertions failing, and on the host is wrong on 26 of 37 hand scripts and 220 of 320 sampled generated ones; `cheat-const-grant` (every request granted as it is made) scores 0, failing 22 hand scripts and 90 of 96 sampled generated ones; `cheat-victim-youngest` (always the youngest transaction dies) scores 0, failing `dead-fewest` and `dead-tie-recent` and 14 of 96 generated; `cheat-forge-hand` carries the frozen answers for all 37 hand scripts keyed by the script text read off the driver's frame, passes every hand script and fails 62 of 96 sampled generated ones. The layer report asserts the forgery passes all 37 and moves the generated population, so a forgery that had silently stopped firing would be reported.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/lock-behind-escalate/variants/ok-fix` and `.../ok-flat`, both written apart from the reference, take 6.8 and 5.2 seconds on the wide script and 7.5 and 29.7 seconds on the deep script against the 600 second clock on the whole set; the reference takes 3.3 and 4.5 seconds per script and 44 seconds for the whole set in the container. The sealed model, also written apart, agrees with the reference and both variants on 800 generated scripts plus the scale families. The search-per-pair manager in `authoring/lock-behind-escalate/naive` takes over 300 seconds on one deep script and is `cheat-slow-search`. There is no numeric tolerance: the trace is compared string for string.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. Six gaps were found and closed in the brief: what earlier means (a sentence on sequence numbers), whether a covered grant still triggers the escalation check (it does, and the brief says so), whether an escalation may be tried again on a release (only at the next row grant), whether the victim's count reads the collapsed records (the count is records released, a table record being one), the tie among victims, and where an `esc` line sits relative to the grant that brought it on. One sentence survives without a reading that contests it - that an escalation takes no sequence number - because nothing observable depends on it once the try never waits; it is kept because a solver asked to write the try as a request needs to know its number does not exist.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22 and unchanged since. The rules below are the whole contract; the sealed model
implements them apart from the reference, and no rule was changed while building. Two
clarifications were recorded, neither a change: an escalation try leaves the trigger count
untouched when it is refused (the rule says nothing else), and the settle's earliest-first order
is by sequence number of the waiting request (the only order the brief defines).

- Artifacts the agent produces: `/app/lm/held.py`, `/app/lm/wait.py`, `/app/lm/grant.py`,
  `/app/lm/esc.py`, `/app/lm/dead.py`, `/app/lm/settle.py`. Nothing else is collected; the
  verifier lays those six over its own pristine copy of the tree.
- What is checked: the stdout trace of every graded script, line for line, exactly. Thirty-seven
  enumerated scripts against `gt.json`, frozen before the grading file was written; 326
  generated scripts (eight small families at 40, three wide, three deep) against the sealed
  model, which must itself still reproduce `gt.json`.
- Tolerances: none. The only limit is the 600 second wall clock on the stage that runs submitted
  code, validated against two independently written correct implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory `chmod 700` before the privilege drop.

### The script

`cfg K` opens the file; K is the escalation threshold. Every other line is `T<n> lock <target>
<mode>`, `T<n> drop <target>` or `T<n> commit`. A target is a table (a name with no dot) or a
row of one (`<table>.<n>`). A mode is `s` or `x`. A transaction's ops are its lines in file
order; its last op is `commit`. Transactions are ordered by their first line.

### The driver (frozen)

Rounds. In a round the transactions are visited in order; one that is live, not waiting and
has an op left performs its next op and the manager settles. A transaction granted during a
settle acts at its next visit. The program ends when every transaction is done.

### The eleven graded decisions

1. Conflict: two locks conflict when their targets overlap (same target, or a table and one of
   its rows), they belong to different transactions, and they are not both `s`.
2. Behind: a request is granted only when no record held by another transaction conflicts
   with it and it is not behind any earlier waiting request it conflicts with; otherwise it
   waits. Sequence order is the order of `lock` ops.
3. Skip: a request is not behind an earlier conflicting waiter whose transaction waits,
   directly or through other waits, on the requester. V waits on U when V's waiting request
   conflicts with a record U holds, or with an earlier waiting request of U.
4. Settle: after every op, repeatedly, the earliest waiting request that is grantable is
   granted; when none is, a hard cycle (each transaction waiting on a record the next holds)
   costs its victim; until nothing changes.
5. Cover: a request for a target the transaction already holds in the same or a stronger mode,
   or a row under a table record of the same or stronger mode, is granted at once and records
   nothing. A request in `x` on a target held in `s` is an upgrade evaluated like any other
   request; granted, the record's mode becomes `x`.
6. Subsume: a granted table lock releases the transaction's row records on that table whose
   mode is the same or weaker.
7. Escalate: after any row grant to T on table A (real, upgrade or covered), if T holds K or
   more row records on A, T tries for A in mode `x` if any of those records is `x` and `s`
   otherwise, unless it already holds A in that mode or stronger.
8. Escalation is a request evaluated as if later than every waiting request, taken at once
   when grantable (applied as a table grant, printing `esc`) and otherwise abandoned until the
   next row grant on A; it never waits and takes no sequence number.
9. Victim: among the transactions on any hard cycle, the one holding the fewest records; a tie
   goes to the one whose waiting request is the most recent. It prints `dead T n`, releases
   its records, drops its request and is done.
10. Counts: `end T n` on commit and `dead T n` carry the number of records released; a table
    record counts one.
11. Drop: `drop` releases the transaction's record on exactly that target, and nothing when
    there is none; it prints nothing.

### The trace

`grant T target mode`, `wait T target mode`, `esc T table mode`, `end T n`, `dead T n`.
Nothing else. Within one op: the op's own line first, then the settle's lines in the order
the settle produced them; an `esc` line follows the grant that triggered it.

### Prong C, as built

C1 both sides: holder-only granting fails `behind-writer`; blanket queueing fails `plain-pass`;
never escalating fails `esc-trigger`; queueing a refused escalation fails `esc-abandon`. C2 no
oracle: the shipped tree prints a coherent trace for every script and no public manager has
these rules. C3 the deep family, measured. C4 exact traces over 37 enumerated plus 326 nonce
scripts. The route-around is blocked by collecting only the six files.

## Decisions and their reasons

- **Software / Databases.** The graded work is a lock manager: modes, wait queues, escalation,
  deadlock victims. No retained bundle is filed under Databases. `tools/catcheck.py` measures
  5108 software terms in `environment/` against 169 in the prose.
- **A round-robin driver instead of an interleaving given by the script.** A blocked client
  cannot issue its next statement, so the interleaving has to be derived from the semantics;
  a script that fixed it would have to say what a waiting transaction's next line means.
- **Behind-unless-depending as a static rule evaluated at every settle**, rather than queue
  rearrangement at detection time: it is statable in two sentences, deterministic, and makes
  the late case (a wait added elsewhere grants a request) a consequence rather than a rule.
- **Escalation as an abandoned request.** Queueing it would make the escalating transaction
  wait on its own count; abandoning it keeps escalation opportunistic and puts the waiter
  condition on the same footing as every other grant.
- **The victim by records, then recency.** Records rather than requests, so the collapse an
  escalation performs changes the choice; recency rather than age, against the textbook.
- **The word earlier in the behind rule is redundant and kept.** A later conflicting waiter
  always depends on the requester (it is behind the requester's own request), so dropping it
  changes no trace; it is kept because the sequence numbers also define which request the
  settle grants first, and a brief that defined them only there would read as an afterthought.
- **The scale family is a shape, not a size.** The first wide family at 600 transactions took
  the search-per-pair manager 71 seconds and the reference 14; it separated nothing that a
  clock could fairly cut. The deep family - a fan of readers soft-blocked behind one writer at
  the head of a long chain, with unrelated ops keeping the manager settling - is where a
  fresh search per pair costs the fan times the chain at every pass, and it is the gate.
- **Two shared kit files were rewritten rather than reused.** `tests/reap.py` and
  `tests/test.sh` are in my own words; `tests/test_outputs.py` was restructured around a
  record class after `tools/simcheck.py` measured 0.63 against `expert-defer-shed`. The two
  Dockerfiles remain near-identical to every retained bundle because their content is
  prescribed by the kit.
- **`tools/docker_trial.py` learned `DOCKER_TRIAL_NETWORK=host`.** This sandbox's docker
  daemon has no bridge network and no registry can be pulled from, so the base image is a
  local stand-in built from an Ubuntu rootfs and tagged `python:3.12-slim`, and builds and runs
  use the host network. The shipped Dockerfiles are used verbatim.

## Stage 7 re-attack, run cold on the finished bundle

Read the final brief with the built tree in front of me and tried to one-shot the plan.

- **Is the first plan still wrong?** The plan from the prior is the shipped tree, and it is
  wrong at the first decision point. The plan *after* reading the brief is right in outline,
  because every rule is stated; it is wrong in structure. A queue per target cannot hold a
  request that is behind a request on another target; a wake-on-release settle cannot grant
  the request that a wait elsewhere has just freed; a set of targets cannot count what a table
  lock collapsed; and an escalation that queues cannot be given up. The one place the brief
  could be read as method is the sentence that the try is judged as if made after every
  waiting request, and that is a rule, not a structure.
- **Are the load-bearing facts still distributed?** They are stated rather than hidden, which is
  the doctrine. What is not stated is which structures survive all of them at once, and that
  the natural search-per-pair form of the grant rule is a hundred times over the clock on the
  deep shape.
- **Did the instruction come to telegraph the method?** No. It states the outcome of each rule
  and never a data structure; `tools/hintcheck.py` is clean and the prose names no technique.
- **Updated estimate of solves out of 8: 2** (range 1 to 4), unchanged from Stage 1. Every rule
  is in the brief and a meticulous implementer who holds all eleven at once and then times the
  deep script wins; what remains against them is that there is no feedback on any of the eleven
  except one quoted line, the grading is all or nothing over 363 scripts, and the natural form of
  the reachability question is over the clock.

## Cold self-attack

The self-probe cannot be run by the author who wrote the model first: the brief, the model
and the reference were all in hand before any cold attempt could have been made, so a solve by
this session would measure memory. It is recorded as not run. Standing in its place: the
reading separations (twenty readings, each caught by its named case), the shortcut and forgery
results, the short-rule measurement (no graded quantity has an exact rule at depth two over
what the tree exposes), the measured gate, and the fact that the author's own first reference -
written with every rule right - fell over the clock.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py --build` with `DOCKER_TRIAL_NETWORK=host`; harbor is not installed here |
| No answer leaked into agent image | pass | `tools/imagecheck.py`: 14 files, no `tests/` or `solution/` content; `extraneouscheck` and `deadfieldcheck` clean; `forgecheck` finds the forgery probe and no ground truth in the agent tree |
| `harbor run -a oracle` = 1 | pass | `docker_trial.py lock-behind-escalate oracle`: reward 1, 40 tests in 44 s |
| `harbor run -a nop` = 0 | pass | `docker_trial.py lock-behind-escalate nop`: reward 0, 26 of 40 failing |
| Cheats all score 0 | pass | `docker_trial.py --all`: 34 of 34 trials behaved as required - oracle 1, nop 0, all 32 cheats 0. `cheat-slow-search` was killed by the 600 s clock and graded as no record; `probe-crash-worker`, `probe-malformed` and `probe-uncollected-file` left the grader with a planted, spoiled or missing record and scored 0 in under two seconds of grading |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `preflight.py` | pass | 0 errors; the 21 warnings are the method-call false positive on `put`, `rows`, `holders`, `on`, `add`, `remove`, `targets` (every one is called as a method) and the package-call notes every retained bundle trips |
| `harbor check` rubric | not run | no API key in this session; the manual quality review in docs/QUALITY-REVIEW.md was walked instead |

## Open questions and next steps

The easiness probe has not been run: this session has no probe harness. The reading
separations, the layer report, the short-rule measurement, the measured gate and the cold
re-attack stand in its place, and the estimate above is what they support.

## What the isolation probes actually report, not just that they score 0

Run in the verifier image built from the final bundle, reading the worker's own record rather
than the reward:

- `cheat-probe-answer-key` first two trace lines: `gt PermissionError`, `model
  ModuleNotFoundError`. The frozen answers cannot be read and the sealed model cannot be
  imported by code running inside the verifier.
- `cheat-probe-privilege` first two trace lines: `uid 1002`, `reward PermissionError`. Submitted
  code is unprivileged and the reward is not writable by it.
- `/logs/verifier` is `drwx------ root root` at the moment the submission runs, `reward.txt`
  inside it is root-owned, and `/tests/seal` is `drwx------ root root`.

A zero alone would not have distinguished any of these from a probe whose patch never fired.

The final verifier image differs from the one the full suite ran on by two edits made after
that suite started: the reward path written literally in `tests/test.sh`, and
`tests/test_outputs.py` restructured around a record class. Oracle, nop and the nine probes
were re-run on the final image; the table above records that run.

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree both ways.** Every graded assertion has its row in
`authoring/lock-behind-escalate/trace.md` and `tracecheck` is clean. The converse was walked
by hand: every sentence of the brief is graded by the trace comparison, except the ones that
describe the environment rather than a behaviour - that `/app/scripts` holds four scripts, and
the sizes of the two shipped scale scripts. Those were re-derived from the tree: `wide.txt` is
400 transactions over 20 tables, `deep.txt` is 138 readers, a chain of 106, one writer and 217
others, 462 transactions in all; the generator's largest deep script is 551 transactions and
4005 ops, inside the stated bounds.

**Counts.** Re-derived from the code after the last generator change: 37 enumerated scripts,
326 generated (eight small families at 40 plus three of each scale family), ten families, 600
seconds. Every enumerated case name that `task.toml` mentions exists in `cases.ORDER`, and
every `/app` path the brief names exists in the shipped tree.

**Boundaries.** Earlier by sequence number, the tie among victims, the mode of an escalation,
whether a covered grant counts, the empty drop, and the order of lines within one op are all
settled in the text, and each has an enumerated case named for it.

**Verifier rigor.** The tests run the submitted modules over a pristine copy and compare the
whole trace; nothing is taken on the submission's word. `tests/test_outputs.py` opens with the
frozen contract and is sectioned by what each block checks. The only wall-clock dependence is
the stated 600 second limit, measured at twenty times the headroom for the reference and at
least three for both independent implementations.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; pytest is
pinned at 9.1.1 with ctrf 0.5.2 in `tests/Dockerfile` only; no apt package is pinned;
`tools/imagecheck.py` assembles what the image would hold (14 files) and runs the four shipped
scripts in it.

**Solution quality.** `solution/solve.sh` copies six source files into place and runs two
scripts; it computes nothing by hand and writes no answer.

**Anti-cheating.** `tools/forgecheck.py` finds one forgery probe and no ground truth in the
agent tree; the sealed directory is 0700 before the privilege drop and `cheat-probe-answer-key`
reports the exception rather than the file.

**Metadata.** Software / Databases is a row of the guideline table; the six tags name
techniques rather than the taxonomy; `difficulty_explanation` names the concrete step and
states the legacy-register naming as a design choice; `expert_time_estimate_hours` is 8,
consistent with the claim.

**Known risks a reviewer should see.** The two Dockerfiles remain near-identical to every
retained bundle because their content is prescribed by the kit. `harbor check` was not run: no
API key is available in this session. The easiness probe was not run.
