# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a database kernel engineer who has worked on the lock manager of a storage engine: the
part that turns a request for a row into grants on the row, its block and its store, decides
what happens when two transactions want the same thing, and keeps the table small enough that
a request costs the same when four hundred transactions are open as when four are. Familiar
with intention locks, with the difference between a lock a transaction asked for and one it
holds only because something below it needs covering, and with the fact that what a service
does to the loser of a conflict is a policy rather than a law.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository)
- Contributor's relationship to it: not applicable
- License: not applicable
- Pinned commit: not applicable
- Load-bearing couplings found during research: not applicable
- Identifier degradation done: the agent-facing tree uses a legacy register (`lk/`, `mode`,
  `hold`, `give`, `keep`, `wide`, `step`, `say`, `name`, `read`, `ask`, `kn`, `ksub`, `who`);
  short, never misleading, and no name misdescribes what it holds. No conversion table is
  needed because nothing was vendored.
- Proper-noun sweep: nothing in the tree names a product, company, person or standard beyond
  the mode letters IS, IX, S, SIX and X, which are the public vocabulary of multi-granularity
  locking and are used honestly.
- Upstream-diff check: not applicable

## Task summary

The agent is handed a lock service for a three-level namespace - stores, blocks and keys - and
a grammar of programs that open transactions, take modes on resources, release them and finish.
The service runs, prints a trace and a closing report, and gets nine of its decisions wrong.
Six files under `/app/lk/` are collected; the driver, the parser, the namespace helpers, the
trace writer and the sample programs are the verifier's own copies and cannot be changed.

The service is not the textbook one. A conflicting holder younger than the requester gives its
grant up instead of the requester queueing - there is no queue anywhere - and the give-up takes
every grant that holder has below that resource with it. What the loser keeps is a claim, tried
again when the level that refused it moves, oldest transaction first and outermost resource
first. A transaction's mode at a store or a block is not a lock it took: it is the supremum of
the mode the program asked for there and the cover its own live grants below currently require,
so it falls when they go, and a fall can make the resource compatible for somebody who was
refused it earlier. On top of that a transaction holding more than the program's threshold in
grants under one node has them replaced by a grant at that node, which widens what it conflicts
with; the count that threshold is read against moves in both directions, because giving up and
retaking both change it.

## Why it is hard

The first plan is the published one and it is wrong in its structure, not in a detail: a granted
group and a FIFO wait queue per resource, intention locks acquired on the way down and held
until release, escalation on a count that only rises. Every piece of that has to come apart.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the retrieved plan is a
  lock table with queues, and this service has no queue, revokes from the holder rather than the
  requester, derives the ancestor modes instead of taking them, and reads its escalation
  threshold against a count that falls as well as rises. Each of those alone would be a patch;
  together they decide what the table is, and the ancestor rule in particular cannot be added to
  a one-mode-per-pair table at all.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4. A1: the memorised
  lock manager is a liability at the first decision point. A2: escalation, de-escalation,
  preemption and the supremum are described operationally and never named. B2: nine rules that
  each change what a correct implementation of the others looks like. C1: both sides of every
  fence are graded. C2: no engine behaves this way, and a take that raises only the asked mode
  prints nothing at all. C3: two measured scale families. C4: exact line-for-line grading
  against a population generated after the agent is gone.
- Assistant's attack on the plan: my first plan was `grants[(t, res)] = mode`, covers taken
  outermost-first as ordinary takes, claims as a list of what was lost, and a per-(transaction,
  parent) counter for the threshold. Three of those four are wrong. The mode at an ancestor is
  two quantities, not one; a claim is left only where an asked mode existed, so a retake
  re-derives the covers rather than restoring them and comes back narrower when part of the
  subtree is still blocked; and the threshold count moves down as well as up. I would have got
  the ordinary programs right and failed the programs where a cover has to fall.
- Estimated solves out of 8: 3 after the Stage 7 re-attack (range 1-5); the design was aimed
  at 1 and the number moved up for the reason below.
- Difficulty record score: `authoring/grant-widen-yield/difficulty.toml`, scored 2026-09-22
  before any code: **100/100, in band** (band 95-100, `docs/DIFFICULTY-SCORE.md`), one warning
  that the resource gate was still a promise. First and only attempt; nothing was changed to
  reach the number. Re-scored at Stage 7 against the built tree.
- Difficulty score anchor: not yet set by the contributor
- Score history: 2026-09-22, 100, first record, before any code. 2026-09-22, 100 again against
  the built tree: 347 environment lines (retained band 229-544), 6 editable files (band 1-7),
  611 reference lines (band 110-424, so above it), 43 cheats and 2 correct variants. The one
  drift the checker reported was the reference, planned at 320 and built at 611; the record now
  carries the measured number.
- Stage 7 re-attack, read cold against the finished brief: every rule is on the page, because
  the instruction contract requires it, so the honest question is whether a careful reader can
  write a structure in which all of them hold at once on the first attempt. My own first plan
  would still be a record per transaction and resource with a holder map beside it, claims in a
  dict and the sweep sorting them, and it would still be wrong in three places that no local
  test can show: the grants of a take have to be printed outermost first while the cover they
  create propagates inward to outward, so the natural write emits them backwards; a claim is
  left only where an asked mode existed, so a retake rebuilds a narrower cover than the one
  that was lost and a claim set recorded as what was lost blocks a third transaction two
  hundred lines later; and the sweep's membership is part of the answer rather than a speed
  choice, because a retake that ends in a refusal has already made younger holders give way.
  What moved my estimate up from 1 is that none of those is hidden - each has its sentence -
  and a very careful reader who builds from the rules rather than from the prior can get them.
  What keeps it below 8 is that there is no oracle of any kind: the brief publishes one
  nineteen-line trace, which decides the printed vocabulary and the two print orders and none
  of the twenty-nine wrong readings, and several of those readings move under two per cent of
  the population while all-or-nothing grading scores them zero. Three correct-but-naive
  structures also die on the clock. The instruction did not come to telegraph the method: it
  states what the service does to a program and never names escalation, de-escalation,
  preemption or the supremum.
- Leak audit: nothing in the agent-facing tree distinguishes an asked mode from a derived cover
  (the shipped hold table stores one mode per pair); no count of claims, grants or children is
  printed or stored; the namespace module holds parent, depth and ordering only; the widen
  decision is never cached; the one worked example in the brief was chosen to decide none of the
  readings the task turns on, which is checked by scoring every reading against it.
- Expert path: run the shipped service on the sample programs and find which module prints each
  line; derive from the brief that an ancestor's mode is a supremum over the asked mode and the
  live grants below; rebuild the hold table as an asked mode plus per-mode counts of the covers
  the children require; separate the two reasons a grant exists, because only an asked mode
  leaves a claim; write the give-up cascade deepest first and narrow the ancestors outward;
  make the sweep the claims due when it starts, oldest first then outermost; settle the widen
  rule against grants only, deepest level first, to a fixpoint, forcing nobody to give way; then
  time the wide programs and key the cover, the sweep and the widen scan on what the line
  touched.
- Originality check: searched 2026-09-22 for multi-granularity lock escalation, lock yield and
  reclaim, and implementation exercises. What comes back is the textbook chapter, vendor pages
  on lock escalation and intent locks, and shared-disk lock-manager patents that do describe
  yielding and reclaiming between members. None of them describes this protocol: age-ordered
  give-up with no queue, a claim that outranks arrival, a cascade down the subtree, a derived
  ancestor mode that falls on its own, or a threshold read against a count that moves both ways.
  The combination exists nowhere, and the pages that do exist push the reader toward the wrong
  structure.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace: `authoring/grant-widen-yield/trace.md`, 141 rows, written by
  `authoring/grant-widen-yield/make_trace.py`, which refuses to write a trace whose quotes
  are no longer in the brief. It walks all five test functions, all 44 enumerated cases, the
  six declared artifacts, the 60 s clock and 24 spans of the sealed model, one row per rule
  with its line range. No row was left NOT STATED: three decisions had no sentence when the
  walk began - that a refused retake prints nothing, that a claim is woken only by its own
  level moving, and that the widen rule does not run again after its own changes - and each
  got one. `python tools/tracecheck.py grant-widen-yield` is clean.
- Identifiability: 29 wrong readings are written down in `authoring/grant-widen-yield/emit.py`
  and measured by `python tools/readingcheck.py grant-widen-yield`, which reports all 29
  separated by a named enumerated case. Five were not, when first measured: four were blind to
  the enumerated set and the tool's shrunk counterexamples were shipped as `give-claim-asked`,
  `wide-claims-idle`, `wide-twice` and `wide-last`; one (`wide-blocks-first`, the widen rule
  applied to blocks before keys) reached nothing in 594 generated programs, so the shape that
  separates it - a transaction crossing the threshold at a block and at the store on the same
  line, which needs two claims retaking in one sweep - was derived by hand and shipped as
  `wide-deep-first`. The worked example in the brief decides none of the 29: it is
  `runs/one.txt`, whose trace turns on the printed vocabulary and the two print orders only.
- Shortcut strategies scored: the shipped tree (reward 0, fails 45 of 48 graded assertions and
  never finishes the scale families inside the clock); one fixed output for every program
  (reward 0, 0 of 414 programs right); every take granted at the resource it names and nothing
  else (reward 0, 0 of 414); the worked example replayed for every program (reward 0, 0 of
  414); and an answer key carrying all 44 frozen enumerated answers (reward 0, passes the
  enumerated set and fails everything generated). `authoring/grant-widen-yield/cheat_report.py`
  asserts which enumerated case catches each of the 33 semantic cheats and reports 0 findings.
- Independent implementation behind every tolerance and limit: there are no tolerances - every
  comparison is exact string equality. The one limit is the 60 s clock on the whole graded set,
  validated against two correct services written to the same contract with different internals
  (`authoring/grant-widen-yield/variants/walk` and `.../multiset`) and re-measured by
  `authoring/grant-widen-yield/timing.py`. 
- Undecided decisions from the cold-reader pass: four, found by walking every printed token
  back to a sentence in the author-run mechanical form, and each one written: that a retake refused by an older holder prints nothing while a program take prints
  `wait`; that the `wide` line carries the number of direct child grants replaced and is
  printed after the `free` lines and before the covers above it; that a drop of something the
  transaction neither holds nor claims prints nothing; and that the report orders resources
  with a store before its blocks and a block before its keys. The stronger form - a fresh
  session given only the brief and the agent tree - was not run, and is recorded as not run
  rather than claimed.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. Changing any line below changes what "correct" means and needs the
contributor's explicit approval.

- **Artifacts the agent produces**: exactly six files, read at their original absolute paths:
  `/app/lk/mode.py`, `/app/lk/hold.py`, `/app/lk/give.py`, `/app/lk/keep.py`, `/app/lk/wide.py`,
  `/app/lk/step.py`. Nothing else is read. A seventh file placed beside them is never collected.
- **What is checked**: the verifier lays the six files over its own pristine copy of the tree and
  runs `run_lk.run(text)` on every graded program. The value returned is compared line for line
  against the sealed model. All or nothing: one wrong line anywhere scores 0.
- **The graded population**: enumerated hand programs, one per graded decision plus the
  must-still-work side of each fence, checked against `tests/seal/gt.json` frozen before the
  grading file was written; plus programs generated inside the verifier from a seed drawn after
  the agent's container is gone, across families shaped at each decision point, including five
  wide and five crowded programs that carry the execution limit.
- **Tolerances**: none. Exact string equality on every trace line and on the closing report.
- **Limits**: the submitted service has 60 seconds of wall clock for the whole graded set, which
  is also the task's execution limit and is stated in the brief. Measured 2026-09-22 on this
  host by `authoring/grant-widen-yield/timing.py`: the reference settles one wide program in
  0.22 s, one crowded program in 1.45 s, and all 414 graded programs in 7.89 s of the 60. The
  three correct-but-naive readings on the same two programs take 14.97 s (cover recomputed by
  rescanning the children), 20.96 s (every standing claim looked at on every line) and 26.27 s
  / over 200 s (the widen threshold tested for every transaction and resource). Each ships as a
  cheat and each scores 0.
- **Ground truth, and where it lives**: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  root-owned `chmod 700` directory the sandbox uid cannot read. The grader asserts the model
  still reproduces `gt.json` exactly before it judges anything.
- **Graded decisions** (each owed a sentence in the instruction):
  1. the compatibility table and the supremum over the five modes
  2. the cover a mode requires of the resource above it, and that an ancestor's mode is the
     supremum of the asked mode and the covers its live grants require
  3. acquisition level by level from the store inward with no look-ahead; a younger conflicting
     holder gives way, an older one refuses, and what was given up stays given up
  4. the give-up cascade: the node and every grant below it, deepest first, then the ancestors
     narrowed outward
  5. a claim is left only where an asked mode existed, at the asked mode
  6. a claim is due when made and when the level that refused it moves; a sweep takes the claims
     due when it starts, oldest transaction first then outermost resource, each tried once
  7. the widen rule: grants only, above the threshold, at the supremum, forcing nobody to give
     way, deepest level first, in transaction order, to a fixpoint, after the sweep
  8. release and finish: the subtree and the claims under it, deepest first, then narrowing
  9. the printed vocabulary and its order: `hold` outermost first on a grant, `give` deepest
     first, `thin`, `free`, `wait`, `wide` with its count, `shut`, and the closing `own`/`due`
     report in transaction order then namespace order
- **Prong C tactics used**: C1 (every fence graded from both sides; the ordinary programs where
  nobody gives way and nothing narrows), C2 (no external oracle behaves this way; the asked-mode
  rise is silent), C3 (the two measured scale families above), C4 (exact all-or-nothing over a
  nonce population shaped per decision).
- **Route-around guard**: `artifacts` names the six files and nothing else. The driver, parser,
  namespace helpers, trace writer and sample programs are the verifier's pristine copies, so the
  output format, the program grammar and the report cannot be reshaped, and a new file beside
  the six is never read. The frozen driver calls `step.run(text)`, `book.held(t)`,
  `book.eff(t, res)`, `due.held(t)` and `due.owed(t, res)`, so those five entry points are part
  of the contract and are stated in the brief.

## Decisions and their reasons

- **No wait queue at all.** An earlier sketch had a FIFO queue beside the granted group. It was
  cut because it is exactly the structure the model's prior supplies for free; the claim set,
  ordered by age and depth rather than arrival, is the same problem with the retrieved answer
  removed.
- **A sweep is the claims due when it starts, and a claim is due only when the level that
  refused it moves.** This started as an optimisation and had to become part of the contract: a
  retake that ends in a refusal is not a quiet event, because it walks its chain making younger
  holders give way before it finds the older holder that stops it. Which claims are tried
  therefore changes the output, so it is specified rather than left to the implementation.
  Sweeping every claim on every line is a wrong reading and a cheat; scanning every claim to
  ask whether its level moved is a correct reading and one of the measured scale failures.
- **Retakes preempt, like any other take.** Making them passive would have made the sweep a
  pure optimisation, but it would also have removed the case the task is built around: a claim
  left long ago taking a whole subtree away from a transaction it never met.
- **The widen rule forces nobody to give way.** It is the service tidying its own table, so a
  node somebody else is sitting on simply stays fragmented. This also keeps the rule from
  becoming a second preemption mechanism.
- **`holder-walk` is a correct variant, not a scale failure.** Asking each holder in turn
  whether it is compatible, rather than counting holders by mode, measured 0.22 s and 1.94 s
  against the reference's 0.22 s and 1.45 s. It is kept as one of the correct variants that
  must score 1, and no claim is made that it is too slow.

## Validation status

Container evidence is not available in this session: the egress policy denies Docker Hub's
blob CDN (`production.cloudfront.docker.com:443`, confirmed twice through the session proxy),
so no base image can be pulled and neither `harbor` nor `tools/docker_trial.py` can build.
Everything below marked *host* was run by `authoring/grant-widen-yield/host_trial.py`, which
runs `tests/test.sh` verbatim as root and does reproduce the privilege drop to uid 1002, the
session and wall clock around the worker, the root-owned 0700 reward channel, the sealed
directory the sandbox uid cannot read, the survivor reap and the reward written last. It does
not reproduce the image build or the platform's artifact upload.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | registry blocked; `tools/imagecheck.py` assembles what the image would hold and runs the reference in it - clean, 29 files |
| No answer leaked into agent image | pass | `extraneouscheck`, `deadfieldcheck` and `imagecheck` clean; nothing under `environment/` distinguishes an asked mode from a derived cover |
| oracle = 1 | pass (host) | 48 of 48 graded assertions, 100 s |
| nop = 0 | pass (host) | 45 of 48 fail |
| Cheats all score 0 | pass (host) | 47 of 47. The 35 semantic and shortcut cheats came from one `--all` sweep; the nine probes and the three too-slow readings were re-run after the probes were rebuilt (see below) |
| Correct variants score 1 | pass (host) | `walk` and `multiset`, 44 enumerated and 64 generated programs each, no mismatch |
| `tracecheck.py` | clean | 141 rows |
| `readingcheck.py` | clean | 29 of 29 readings separated |
| `onelinecheck.py` | clean | none of the four graded decisions has an exact rule at depth 2 |
| `forgecheck.py` | clean | 0 findings from `cheat_report.py` |
| `extraneouscheck` / `deadfieldcheck` / `solvecheck` / `catcheck` / `hintcheck` | clean | catcheck: environment 97, prose 87 for Software |
| `structcheck` / `textcheck` | clean | textcheck against `expert-defer-shed`: irregular on every axis |
| `simcheck` | two known findings | `environment/Dockerfile` is byte-identical to three retained ones, because a seven-line base image has nothing task-specific to say; `tests/test_outputs.py` scores 0.61 against two retained graders because the two-stage harness is this repository's house pattern. The conceptual verdict is the one that matters: "this task does not grade what any earlier one grades" |
| `preflight.py` | see below | |
| rubric review | manual | walked criterion by criterion below; `harbor check` needs an API key that is not present here |
| `package.py` / `zipcheck` | clean | 88 entries, 47 cheats, no STATE.md, no caches, `.sh` files at 0755 |
| `difficultycheck` on the built tree | 100/100 | 347 environment lines, 6 editable files, 611 reference lines |

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree, both ways.** Every graded assertion has its row in
`authoring/grant-widen-yield/trace.md` and `tracecheck` is clean; every sentence of the brief
has a case, which is what the 44 enumerated names are for. The walk found three graded rules
with no sentence and each was written rather than dropped: that a refused take leaves its claim
at the mode it asked for, that a take which succeeds clears the claim it had there, and that
widening takes what sat under the replaced children with it. Boundaries are settled in the
text: ties go to the oldest transaction and then to resource name, the widen rule reads *more
than* the threshold and `wide-under-limit` grades the other side, a drop of something neither
held nor claimed does nothing, and resource order is stated as a store before its blocks and a
block before its keys. The six collected paths, the five entry points the frozen driver calls
and the 60 s clock are all in the brief. No two readings that reproduce the brief and its one
published trace disagree on the graded set: 29 were enumerated and all 29 are separated.

**Prose.** Rewritten once after `structcheck` reported a labelled requirement bucket and a
nineteen-line code block, neither of which any retained brief carries; the worked example is
now quoted inline the way `expert-defer-shed` quotes its one wrong line. `textcheck` against
that brief reports the candidate at least as irregular on every axis. Each requirement is
stated once.

**Verifier rigor.** The tests run the submitted service and compare what it printed; there is
no exit code and no state the agent could write directly. `tests/test_outputs.py` carries the
frozen contract at the top and one section per group of behaviour. Determinism: the nonce seed
changes per run but the verdict does not, because the model recomputes the answer for whatever
was generated, and the reference and the model agree over 15,000 fuzz programs plus every
enumerated and generated one.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; neither
`tests/` nor `solution/` is reachable from it. pytest is pinned at 9.1.1 with
`pytest-json-ctrf==0.5.2` in `tests/Dockerfile`, and nothing installs at trial time. Every path
and name the brief mentions exists and is spelled the same: checked by hand and by
`imagecheck`, which assembles the image contents and runs the reference inside them.

**Solution quality.** `solution/solve.sh` copies the six reference files into place and runs
the service on two sample programs; it computes nothing by echoing an answer, and it uses only
what the agent has.

**Anti-cheating.** Nothing under `environment/` distinguishes an asked mode from a derived
cover, which is the load-bearing distinction; no count of claims, grants or children is stored
or printed; there is no git history, cache or data file. Comparison is exact string equality,
so a degenerate output fails: the constant, positional and replay strategies each match 0 of
414 programs.

**Metadata.** `Software` / `Databases`, and `catcheck` measures the category's vocabulary at 97
occurrences in the environment against 87 in the prose, so the label is the work rather than
the story. The six tags name mechanisms, not the taxonomy. `difficulty_explanation` names the
concrete structure a frontier agent gets wrong and says plainly that the legacy register is a
design choice. Nine expert hours is consistent with a 611-line reference across six files, two
of which have to be rebuilt rather than corrected.

**One defect this review found and fixed.** The nine verifier probes were first built as the
*reference* with an attack wired into it, and five of them scored 1. Nothing was wrong with the
verifier: the probe's attack had failed and the correct service underneath had done the work,
so the trial measured nothing. A probe has to sit on a service that cannot pass on its own, and
they now sit on the reference with one rule read the other way, which fails all 44 enumerated
programs by itself. Rebuilt that way all nine score 0, which is what makes them evidence: the
sealed model is unreadable to uid 1002, a double-forked survivor cannot write the reward, the
reward file cannot be written directly, the generator and the grading file cannot be rewritten,
a planted or spoiled worker record does not become a pass, the seed and the family size cannot
be rewritten to shrink the exam, and the worker cannot regain privilege.

**Known risks a reviewer should see.** No container evidence was possible here (the registry is
blocked), so the isolation is demonstrated by the host harness rather than by a two-image
trial. `simcheck` reports `environment/Dockerfile` byte-identical to three retained ones and
`tests/test_outputs.py` at 0.61 against two retained graders; both are this repository's house
pattern rather than copied content, and the tool's own conceptual verdict is that this task
does not grade what any earlier one grades. `preflight` reports 27 warnings, all of the form
"public function nothing calls": its caller detection does not follow `mode.sup(...)` through a
`from lk import mode`, and the retained `expert-defer-shed` produces 16 of the same.

## Open questions and next steps

The bundle is complete and packaged. What is left is what this session cannot do:

1. **Container evidence.** `tools/docker_trial.py` could not run here because the egress policy
   denies `production.cloudfront.docker.com:443`. A session with registry access should run
   `python3 tools/docker_trial.py grant-widen-yield --build`, then `oracle`, `nop`, `--all` and
   `--variants`, and replace the host rows in the table above. Nothing in the bundle is expected
   to behave differently - the host harness runs `tests/test.sh` verbatim - but container
   evidence is container evidence.
2. **The rubric review by a model.** `harbor check` needs a provider key that is not present.
3. **The easiness probe.** Not run, and not simulated: the author wrote the reference, so a
   self-probe here would measure memory rather than difficulty (CLAUDE.md). The estimate of 3
   solves in 8 is the Stage 7 re-attack above, and it is a judgement, not a measurement. If the
   probe rejects the task, `RAISE-DIFFICULTY.md` applies and the winning trajectory becomes a
   cheat before anything else changes.
