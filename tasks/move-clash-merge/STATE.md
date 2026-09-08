# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are the engineer who owns the reconciler of a two-way file-sync client: the part that
takes the last agreed state of a tree, the workstation's copy of it and the server's copy of
it, decides what the agreed state should now be, and produces the operations each side has to
carry out. You have shipped and debugged move-aware sync, conflict copies, name collisions and
the ordering constraints that make a correct plan fail to apply.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, semantics authored here
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repo
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, no vendored code
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? House legacy-register names authored from scratch
  (`mrg/live.py`, `spot.py`, `name.py`, `book.py`, `step.py`); no conversion table needed
  because no upstream names exist
- Proper-noun sweep done? Nothing in the tree names a product, company or person; the two
  sides are called `L` and `R` in the data and "workstation" and "server" in the brief
- Upstream-diff check: not applicable

## Task summary

`/app` is the reconciler of a two-way sync engine. A scenario file gives the agreed record as
a tree of numbered nodes, then rounds of what each side did to its own copy - creations,
edits, renames, moves, removals - and a `sync` after each round. `/app/run_sync.py` replays a
scenario and prints, per round, the operations the engine emitted to each side in the order it
emitted them, then each side's tree afterwards. Five files under `/app/mrg` decide which nodes
the record keeps, where each one sits, how contested names are settled, what the record holds
and which numbers new nodes get, and the operation order. Those five ship wrong. Everything
else - the tree, the scenario reader, the operation applier, the driver - is frozen.

## Why it is hard

The rules are stated in full and each is small. What defeats a plan is that they decide each
other: survival decides placement, placement decides which names are contested, the numbers
handed to new nodes decide who wins a contest, and a file both sides wrote leaves behind a node
that has to exist and be numbered before the contest it takes part in is settled - which the
shipped pipeline cannot do, because it settles names before it makes that node. The emitted
operations are then graded in order against a frozen applier that checks preconditions by path,
so an engine that computes the right record and emits it in an order a filesystem will not
accept scores zero with a correct answer in hand.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the natural plan -
  classify each node, resolve conflicts, write out the differences - is the right shape and
  wrong in its order. The pipeline it will inherit settles names before the nodes that contest
  them exist, and the natural emission (compute the difference, then write it out) produces
  operations whose destination path names the right name under the wrong node, which the
  applier accepts and which silently builds a different tree. Neither shows up on the shipped
  scenarios; both are decided by cases the verifier constructs.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B1, B2, C1, C2, C4. A1 (change beats delete, placement settled per part with the server winning
  each part, a node moved into a folder the other side removed goes up rather than holding the
  folder open, the mark goes before the extension, the record folds case - every one inverts
  what a sync client is remembered to do), A2 (no term of art appears: no merge, no conflict
  copy, no reconciliation), B1 (the case rule lives in the applier, the identity of a node
  across rounds lives in the driver's re-keying, the numbering lives in the record module, and
  none of it is stated where the rule that needs it is), B2 (nine graded decisions that must
  hold together with no per-decision feedback), C1 (quiet rounds and one-sided changes must
  still emit exactly nothing and exactly the one operation), C2 (the runner prints what the
  submitted engine did and never what it should have done), C4 (exact all-or-nothing over
  literal corners and four generated families).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was to fix the five files one rule at a time in the order the shipped pipeline calls them,
  then emit the difference between each side and the record grouped by kind - removals, moves,
  creations, edits. That plan is wrong in three places I did not see until I had built it: the
  conflict node cannot be numbered or named inside a pipeline that has already settled names,
  so the pipeline itself has to move; a destination path resolves to whatever currently holds
  that name, so an emission that does not check which node the destination folder actually is
  builds a plausible tree that is not the record's; and a folder deleted on one side is held
  open only by the children the record put in it, which makes the walk up to the nearest
  surviving folder reachable rather than dead code.
- Estimated solves out of 8: 2 (design aimed at 1; range 1-3)
- Difficulty score anchor: not yet submitted
- Score history: none yet
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? The engine prints the two side trees but never
  the record, so the agent cannot compare its own merge against anything; no shipped file
  contains an expected trace; the shipped scenarios are chosen so that none of them separates
  the graded readings from each other; there is no field, count or filename from which a
  settled name, a survival decision or an operation order can be read off; `authoring/` never
  ships. The one thing the agent can check for itself is that its own emission reaches its own
  record, which is a mechanical constraint rather than an oracle on correctness.
- Expert path, described step by step: read `run_sync.py` and `mrg/drive.py` to see that the
  record is the engine's own output carried into the next round and that the two sides are
  applied under different name rules; read `mrg/lay.py` to find that a destination is resolved
  by path and that removal needs an empty folder; work the brief's rules into the five files -
  survival with the upward pull, the two placement axes settled separately, the walk up to the
  nearest surviving folder, the loop break, numbering, the conflict node, the contest and the
  mark, then the emission; notice while writing the conflict node that it must be numbered and
  named, and move the numbering ahead of the naming; write the emission as a loop that emits
  only what can be carried out now, resolving destinations through the record's own parent
  rather than by name, with the push-aside for a wanted name; run the shipped scenarios and
  check by hand that quiet rounds stay quiet.
- Originality check: searched for public write-ups on move-aware sync reconciliation, rename
  cycles, name collisions and conflicted copies. The closest published work is Syncpal
  (Springer, 2019), which gives an architecture - reconcile per node, then order the operations
  against their preconditions - and the Unison manual, which is path-based and therefore
  specifically wrong here. No public source states this rule set: change beats delete, per-part
  placement with the server winning each part, the record's own children holding a folder open,
  the case-folded record, the mark before the extension, or the numbering order. No coding
  exercise or benchmark on this was found.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: `/app/mrg/live.py`, `/app/mrg/spot.py`, `/app/mrg/name.py`,
  `/app/mrg/book.py`, `/app/mrg/step.py`. Nothing else is read.
- What is checked: the printed trace of every scenario, line for line, in order. Per round and
  per side: one line for each emitted operation in the order emitted, then one line per node of
  each side's tree afterwards, sorted by path, carrying the path and the content (`-` for a
  folder). Scenarios are the literal set shipped in `tests/cases.py` plus four generated
  families built from the run nonce. Every line of every scenario must match.
- Tolerances: none. Exact string comparison, all or nothing.
- Ground truth, and where it lives: `tests/gt.json` for the literal set, frozen before the
  verifier was written, and `tests/model.py` - an independent implementation written from the
  brief - for the generated families. The grader checks the model against `gt.json` before it
  grades anything, so a drifted model cannot redefine correct. Both are root-only inside the
  verifier image; the process that runs submitted code cannot read either.

## Decisions and their reasons

- The record is never printed. Printing it would hand the agent a way to check its own merge
  against its own emission, which turns the emission into hill climbing. The two side trees are
  printed instead, so a wrong record is visible only through what it makes the sides do.
- Scenario operations name paths, not node numbers. That keeps a scenario valid whatever the
  engine does with it, and it is what a filesystem watcher actually reports.
- A removal names an empty folder or a file. Recursive removal as one operation would let an
  engine delete a folder holding a node that has to survive and recreate it afterwards, which
  is a second correct answer and would make the trace ambiguous.
- The generated scenarios are built by root before the run, using the sealed model to know each
  side's tree between rounds, and handed to the worker as text. A generator that could not
  predict the trees would emit operations that mostly do not apply.
- Both side trees are printed every round rather than once at the end. It costs lines and buys
  discrimination: a wrong operation order shows up in the round it happened.

## Stage 7 re-attack (D7)

Read the finished brief against the finished tree. The first plan is still the pipeline the
tree ships - classify, resolve, write out the difference - and it is still wrong in the same
three places, now with the code in front of it rather than a design note. Two of the three are
structural rather than rules: the second node a two-sided write leaves cannot be numbered or
named by a pipeline that settles names first, and a destination path resolves to whatever
stands under that name unless the emission goes through the record's own parent. Neither shows
on the three scenarios in the tree.

What the shipped material decides, measured rather than asserted:

- `authoring/move-clash-merge/shipcase.py` scored every candidate scenario by how many of the
  25 enumerated wrong readings it separates. The three that ship decide four between them, all
  of them in the emission, which is the one part a solver can already check for itself by
  seeing whether its own operations reach its own record. Nothing about survival, placement,
  contents, numbering or the name contest is decided by anything the agent can run.
- `tools/onelinecheck.py` over `authoring/move-clash-merge/decisions.py`: no graded decision -
  whether a node stays, whether a folder is held open, whether a node walks up, who keeps a
  contested name - is reproduced by an exact rule of depth two over the raw features the tree
  exposes.
- `authoring/move-clash-merge/readings.py`: each of the 25 readings is separated by a named
  enumerated scenario, and the loudest of them moves 53% of generated scenarios while the
  quietest moves none of them and is caught only by its hand case.

The cold self-probe was NOT run, and is recorded as not run rather than as passed. The order
here was brief, then reference, then sealed model, then verifier, so by the time a cold solve
could have happened both the answer and the model were in hand and the probe would have
measured memory. The reading separations and the shipped-scenario measurement above stand in
its place.

Estimated solves after the re-attack: 2 (range 1-4), unchanged from Stage 1. The risk of
landing high is that the brief states every rule, so an agent that transcribes it sentence by
sentence and restructures the pipeline gets there; the risk of landing at zero is small,
because the reference passes every run and the expert path is short enough to describe.

## Instruction against verifier, both directions

Every wrong reading the cheat suite scores has a sentence in the brief that rules it out, and
every one of those sentences has an enumerated scenario that tests it.

| Reading | The sentence that rules it out | The scenario that tests it |
|---|---|---|
| removal-always-wins | "stays if the other side changed it at all" | folder-held-by-child |
| only-a-write-saves | "Content, name, the folder it sits in: any of the three counts" | gone-vs-name |
| folder-held-by-arrival | "a node moved in from elsewhere will not either" | folder-not-held-by-arrival |
| folder-held-by-mover | "a node that has moved out will not hold it" | folder-not-held-by-mover |
| workstation-move-whole | "settled apart from each other" | axes-apart |
| server-move-whole | "settled apart from each other" | axes-apart |
| workstation-wins-axis | "a part both sides changed differently takes what the server has" | both-moved |
| dead-folder-drops-to-root | "into the nearest folder above that one in the record that did" | holder-keeps |
| loop-breaks-server-side | "whose folder came from the workstation" | ring-two |
| loop-breaks-newest | "smallest number first" | ring-three |
| mark-after-extension | "before the last dot of the name" | mark-before-extension |
| names-contested-exactly | "Names differing only in case are one name" | case-contested |
| keeper-by-side-only | "the one the record already had in that folder under that name" | holder-keeps-when-gone |
| keeper-workstation-first | "the one the server holds ... or failing that the one the workstation holds" | two-new-one-name |
| second-node-keeps-name | "A second file never keeps the name" | two-second-nodes |
| second-node-after-names | "then the second files" and "Several nodes in one folder can want one name" | second-node-in-contest |
| second-node-carries-ours | "the bytes from the workstation stay with the node" | both-wrote-apart |
| same-bytes-still-conflict | "and those bytes when both wrote the same" | both-wrote-same |
| workstation-numbered-first | "the server first ... then the workstation" | server-numbered-first |
| numbered-as-made | "in ascending order of the paths those nodes have there" | new-nodes-in-path-order |
| emitted-by-kind | "Nothing is emitted before it can be carried out" | case-rename-on-side |
| destination-by-name | "the node the record puts the child under" | destination-is-a-node |
| nothing-pushed-aside | "move that something aside within the folder it is in" | folder-swap |
| written-before-placed | "Bytes are written only once the file sits where the record puts it" | written-after-placed |
| removals-emitted-last | "removals go before moves" | holder-keeps-when-gone |

## Validation status

Docker and harbor are not available in this environment. Everything below marked "host" was run
through `authoring/move-clash-merge/trial.py`, which drives the real `plant.py`, `runner.py` and
`test_outputs.py` and derives the reward the way `test.sh` does. It does not cover the privilege
drop to uid 1004, the root-owned 700 reward channel, the root-only mode bits, or /proc reaping;
the two probes aimed at those are reported as not covered rather than as passes.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | no Docker; `tools/imagecheck.py` assembles the tree the image would hold and runs the three shipped scenarios in it - clean |
| No answer leaked into agent image | pass | Dockerfile copies `app_src` only; nothing in `environment/` names the ground truth, the model or the solution |
| `harbor run -a oracle` = 1 | host: 1 | `trial.py oracle`, 354 scenarios |
| `harbor run -a nop` = 0 | host: 0 | `trial.py nop` |
| Correct variants score 1 | pass | `variants/flat` (everything in two files, flat records) and `variants/split` (survival and the contest moved into other files) both score 1 |
| Cheats all score 0 | pass | 35 of 35, and each attestation probe is refused by the test it was aimed at (`cheat_report.py`) |
| `preflight.py` | pass | no errors, 24 warnings, all of them the unused-public-function false positive for methods called through an instance |
| readings separated | pass | `tools/readingcheck.py`: 25 of 25 separated and named |
| answer shape | pass | `tools/onelinecheck.py`: no graded decision has a rule at depth <= 2 |
| forgery probe | pass | `tools/forgecheck.py`: `cheat-probe-forge-from-gt.sh` carries the frozen expectations and scores 0 |
| category, tags, files, similarity | pass | catcheck, extraneouscheck, solvecheck, deadfieldcheck, simcheck (no NEAR), structcheck, hintcheck, textcheck |
| `harbor check` rubric | not run | needs an API key, which this environment does not have |

## Open questions and next steps

Package, and run the Docker oracle and nop gates on a machine that has Docker before the bundle
is treated as verified.
