# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - pre-flight` for everything the assistant owns. The environment, the sealed verifier,
the reference, the cheat suite and the correct variants are built and measured. Blocked on the
contributor for the candidate confirmation, the category and labels, the expert role, the
timeouts and - the real blocker - the instruction, which is currently an assistant draft and
must not ship until they have written and approved it (D1).

## Assistant's assigned role

TODO: awaiting the contributor's words. Working role adopted meanwhile: "You are a senior
engineer on a calculation engine - you own the evaluator and the layout of formula results in
a grid product, and you have spent years on the interaction between value-dependent result
shapes, obstruction and reference resolution."

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. Nothing has been cloned or vendored, so the ablation
  routine in docs/ABLATION.md does not apply. If the contributor supplies a repository the
  authored-on-top versus excision choice is owed to them before any candidate is settled.
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Not applicable - every identifier in this environment is
  authored here, in the legacy register described under "Decisions" below.
- Proper-noun sweep done? Not applicable - no provenance to strip. The environment names no
  product, company or standard beyond the ordinary arithmetic it implements.
- Upstream-diff check: not applicable

## Task summary

The environment is a small calculation engine for a grid of cells. A cell holds a number, a
formula, or nothing. Some formulas do not produce one number: they produce a rectangular block
of numbers whose size is decided by the values they were given, and that block occupies the
cells below and to the right of the cell that owns it. A block that would land on a cell that
already holds something, or on a cell another block has already taken, is refused, and its
owner reports a refusal instead. Reading a cell therefore does not mean reading its content -
it means finding whether a block reaches it first.

The shipped engine gets this wrong in the way every first implementation does: it derives a
dependency graph from the addresses written in the formulas, sorts it, evaluates in that order
and lays the blocks out afterwards. The agent repairs four policy files so that every printed
grid matches, on the scripts in the tree and on scripts it has not seen.

## Why it is hard

The natural plan is a two-phase one: work out what depends on what, evaluate in that order,
then place the blocks. Both phases are wrong, and each is wrong because of the other. What a
formula reads depends on which blocks were placed; which blocks were placed depends on the
values those formulas produced. The dependency graph is therefore not derivable from the text
of the formulas at all, and neither phase can run first.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the plan every agent
  writes first - collect references, topologically sort, evaluate, then lay out the blocks -
  is not merely incomplete here, it is unwritable, because the reference graph is a function
  of the values and the values are a function of the reference graph. The correct shape is a
  pair of mutually recursive queries (what is this cell's value; is this owner's block placed)
  memoised together, where the second is well-founded on address order and the first is not,
  so cycle classification differs between them. That structure is not what a retrieved
  calculation-engine description gives, and the deviation from it is not visible until the
  agent constructs a case where a block covers a cell that another formula reads.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C4.
  A1 (the memorised calculation-chain plan -
  build the graph, sort it, evaluate, then spill - is coherent, passes every simple case and
  is specifically wrong), A2 (the concept is described operationally as blocks that occupy
  cells; the term of art is never used, and the refusal, fall-through and cone rules are
  stated as behaviour), A3 (placement priority by address and value-dependent extents cannot
  both be satisfied by a single ordered pass), B2 (the reading rule, the refusal rule, the
  fall-through of a refused owner, empty-versus-zero, error skipping in ranges and error
  propagation in arithmetic all have to hold at once, and getting the reading rule right
  changes what a cycle is), C1 (the verifier fences both sides: blocks that must place and
  blocks that must be refused), C2 (the shipped runner reports the submitted policy's own
  answers and no correct answer exists anywhere in the tree), C4 (exact all-or-nothing grading
  over enumerated corners and seeded generated sheets).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is a dependency graph over the addresses each formula mentions, a topological evaluation
  with memoisation, and a placement sweep in address order afterwards, marking obstructed
  owners refused. That plan is wrong in three places and I would not have found any of them
  before writing code. First, a reference to a plain cell can resolve to a block value, so the
  reference graph has edges to owners that the formula never names - every owner in the cell's
  upper-left cone. Second, because a refused owner covers nothing, whether those edges exist
  at all depends on the refusal decision, which depends on values. Third, cycle detection over
  my static graph reports cycles that are not cycles and misses the real one, which is a
  formula that reads a cell its own block would cover. I can see where to start; I could not
  commit to the full plan without exploring, and my first plan is wrong where it matters.
- Estimated solves out of 8: 2 (design aimed at 1; the range I would defend is 1-4)
- Difficulty score anchor: TODO - not yet submitted
- Score history: none yet
- Leak audit (docs/DIFFICULTY.md): pending Stage 3. The standing rules for this build: the
  tree must not ship a cover map, an occupancy table, a placed/refused flag, a precomputed
  extent, or any field from which the reading rule can be reconstructed by a join; the shipped
  runner must print only what the submitted policy produced; no shipped case may come with its
  expected output.
- Expert path, described step by step: (1) run the shipped engine on both example scripts and
  read the printed grids; (2) read the frozen driver to learn that the policy is asked two
  questions, not one - the value of an owner and whether an owner is placed; (3) construct a
  sheet where a block covers a cell another formula reads, and watch the shipped engine read
  the cell's own content instead; (4) recognise that a block only ever extends down and right,
  so whether an owner is placed depends only on owners earlier in address order, and make that
  query the well-founded one; (5) make the value query recursive and memoised on top of it,
  with its own in-progress marking for cycles; (6) work the stated corners one at a time
  against the printed grid - refused owners covering nothing, holes inside a block, ranges
  skipping errors, empty reading as zero in arithmetic but not counting; (7) re-run both
  example scripts and hand-check the last lines.
- Originality check: searched 2026-09-07 for public write-ups of a calculation engine whose
  block extents are value-dependent and whose reference resolution runs through placement.
  Public material describes the product behaviour of spilled array results and the errors they
  raise (support pages, vendor blogs, two patents on array-shaped results), and there are
  open-source formula evaluators, but none states this task's rules and none is an exercise of
  this shape. The published behaviour differs from this engine's on the points that are
  graded, which is what makes retrieval a liability rather than a help. No public write-up of
  the task or a close variant was found.

## Verifier contract - FROZEN after Stage 2

Frozen on 2026-09-07 by the assistant, and awaiting the contributor's confirmation. Any change
after their confirmation needs their explicit approval, because it changes what correct means.

- Artifacts the agent produces: `/app/sheet/val.py`, `/app/sheet/see.py`, `/app/sheet/lay.py`,
  `/app/sheet/memo.py`. Nothing else is read from the agent's tree.
- What is checked: the exact sequence of lines `/app/run_sheet.py` prints, for every script in
  the graded set, compared string for string. 45 enumerated scripts, one per stated rule, plus
  five seeded generated families of 120 each (plain, stack, loop, hole, edge): 645 scripts,
  every one of which must match. Beyond the lines: the report carries the run's nonce, no script
  raised, every frozen function's digest matches one compiled from the untouched sources, every
  printed line came out of the driver's own code object, and the interpreter's own count of
  driver entries equals the number of lines.
- Tolerances: none. Exact string comparison, all-or-nothing.
- Ground truth, and where it lives: `tests/gt.json` for the enumerated scripts, root-owned and
  mode 600 inside the verifier image; the generated families are answered by `tests/oracle.py`,
  an independent model, also root-only. The grader re-derives every enumerated expectation from
  that model before grading anything, so the two cannot drift apart silently.
- Which Prong C tactics the contract uses: C1 (both sides fenced - blocks that must stand and
  blocks that must be refused, cells that must fall through and cells that must not, loops that
  must be reported and reads that must not be loops), C2 (no oracle anywhere the agent can
  reach: the shipped runner reports the submitted engine's own answers, and the expected answers
  exist only in the verifier image), C4 (exact, all-or-nothing, enumerated corners plus seeded
  families concentrated on the mechanisms).
- How the route-around is blocked: only the four policy files are declared, so the runtime, the
  parser, the sheet and the printing walk cannot be restructured; the grader hashes every frozen
  function as the run held it, and the executed tree is compared file by file against the
  untouched copy.

## Candidates put to the contributor

Three candidates were attacked before proposing. The first is the one built here.

1. `sheet-block-place` (recommended) - the grid calculation engine above. Strategic answer and
   attack recorded under "Why it is hard".
2. An offline synchronisation engine: replicas exchange bundles, tombstones are compacted, and
   a compaction that runs one step too early resurrects deleted records much later. Attacked:
   my first plan - version vectors, add-wins removal, a compaction watermark - is close enough
   to correct that the difficulty would have to come from authored deviations, and authored
   deviations that do not follow from the mechanism read as an arbitrary checklist. Rejected
   on that basis, and because tombstone reclamation sits close to the retained
   `reach-pair-sweep`.
3. A training data pipeline whose mid-epoch resumption must reproduce the stream exactly:
   shuffle buffer, packing residue, exclusion applied after the draw, and a changed world
   size on resume. Attacked: the correct plan - checkpoint the buffer, the generator state and
   the residue rather than the step count - is one a frontier agent forms immediately once it
   is told replay is infeasible, so the planning attack fails. Kept in reserve as an ML task.

## Decisions and their reasons

- Category and labels are the contributor's to choose. The assistant's reading of the
  guideline table is `Software` / `Algorithms`: the graded work is mutual recursion, ordering
  and memoisation over a grid, and the calculation-engine setting is the story, not the skill.
  Recorded here so the correction made to `alias-settle-report` is not repeated.
- The environment uses terse internal names in the register of real legacy code, and ships no
  comments or docstrings, per Stage 3 of AGENTS.md. This is stated in
  `difficulty_explanation` so the quality review does not read it as sloppiness.
- No resource gate (C3) in the first design. Two retained tasks pass without one
  (`guard-mark-unwind`, `focus-return-point`); the semantic conjunction carries this one. A
  measured scale family is held in reserve in case a `difficult` verdict says otherwise, and
  it must be measured before it is claimed, not assumed.
- The four editable files are the two queries, the arithmetic and the memo. Every one of them
  has to change; none is a one-file patch. Confirmed at Stage 3 by ablating each in turn.

## Validation status

Two evidence levels are distinguished throughout. **Container** means an image was built and a
trial run: none of that was possible in this session, because image pulls are refused by the
egress policy (the registry blob host answers 403 for every layer) and there is no local cache.
**Sealed host** means `tests/test.sh` itself was run, unmodified, at the paths it expects
(`/tests`, `/pristine`, `/app`, `/work`, `/logs`), as root, on a Python 3.12 virtualenv carrying
the same pinned pytest and ctrf plugin the verifier image installs - so the privilege drop, the
root-owned 700 reward directory, the mode-600 answers, the session, the wall clock and the
reaping are the shipped ones. It is not container evidence and is never reported as such.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | image pulls blocked; `tools/imagecheck.py` interprets the COPY lines against the context, assembles the tree the image would hold, drops the reference in and runs both shipped scripts: clean |
| No answer leaked into agent image | pass (inspection) | the shipped tree is 12 files: the runtime, the four policy files and two input scripts. No expected output anywhere; `tests/` and `solution/` are never copied into `environment/Dockerfile` |
| `harbor run -a oracle` = 1 | not run | harbor not installed (its images are unpullable here). Sealed host: reward 1, 13 tests passed, at the shipped RUN_COUNT of 120 |
| `harbor run -a nop` = 0 | not run | Sealed host: reward 0, 6 of 13 failed |
| Cheats all score 0 | pass (sealed host) | 14 of 14 scored 0, and each was either denied outright or caught by the named test - see `authoring/sheet-block-place/cheat_report.py` |
| Correct variants score 1 | pass (sealed host) | 3 of 3 (`ok-row-index`, `ok-one-memo`, `ok-thin-files`) |
| `preflight.py` | pass | no errors. The remaining warnings are the "unused public function" class, which fires on every retained bundle because the checker does not resolve `module.name()` calls; a direct scan of the shipped tree finds no unreferenced function or constant |
| `tools/readingcheck.py` | pass | 15 readings, every one separated by the enumerated case that names it; none blind, none equivalent |
| `tools/onelinecheck.py` | pass | no graded decision reproduced by a rule of depth <= 2 |
| `tools/forgecheck.py` | pass | `cheat-answer-key.sh` carries `gt.json` verbatim, reproduces all 45 enumerated scripts without computing anything, and still scores 0 |
| `tools/simcheck.py` | pass | no NEAR against any retained bundle; the one HIGH is `environment/Dockerfile`, which the retained bundles also flag against each other |
| `tools/solvecheck`, `deadfieldcheck`, `catcheck`, `hintcheck`, `structcheck`, `extraneouscheck`, `imagecheck` | pass | clean |
| `tools/textcheck.py` | two findings on the draft | too few short sentences, two hedging words - to be addressed in the instruction round with the contributor, whose text replaces the draft |
| `harbor check` rubric | not run | needs an API key, and harbor is not installed |
| Reference vs sealed model, differential | pass | 600 generated scripts, exact agreement, before the last generator change; 645 scripts agree in every sealed-host run since |

## Measured readings (authoring/sheet-block-place/readings.py)

Fifteen complete engines an agent could plausibly ship, each the reference with one decision
replaced, measured on 60 generated scripts per family. Share of scripts each moves, and the
enumerated case that names it:

| reading | moves | named by |
|---|---|---|
| the tree as it ships | 100% | 19 enumerated cases |
| `face-content-first` | 100% | owner-shows-its-first-value |
| `lay-own-cell-counts` | 100% | owner-cell-is-not-in-the-way |
| `lay-undecided-is-free` | 87% | read-into-own-quadrant |
| `memo-loop-marks-one` | 72% | loop-swallows-what-it-passed-through |
| `val-grow-fills-holes` | 70% | grow-keeps-a-hole |
| `face-last-owner` | 60% | owner-order-decides-a-loop |
| `lay-clip-at-edge` | 60% | block-past-the-last-row |
| `val-cnt-counts-empty` | 60% | count-ignores-empty |
| `val-loop-is-skippable` | 57% | loop-does-not-stop-at-a-sum |
| `lay-overlap-allowed` | 43% | overlap-earliest-wins |
| `val-sum-propagates` | 20% | sum-steps-over-a-refusal |
| `val-at-gap-zero` | 13% | at-on-an-empty-cell |
| `val-cnt-skips-errors` | 12% | count-includes-a-refusal |
| `val-block-arith-is-error` | 7% | block-in-arithmetic |
| `val-error-right-first` | 5% | left-error-wins |

Two of these had no separating hand case when first measured and two more were mislabelled.
The cases were searched for rather than guessed (`authoring/sheet-block-place/find_case.py`
draws small scripts and shrinks the ones that separate); `owner-order-decides-a-loop` and
`loop-swallows-what-it-passed-through` came out of that search, and both are corners worth
having for their own sake.

Two more findings came from asserting the layer rather than the reward. `cheat-crash-after-plant`
and `cheat-malformed-output` were written against file descriptor 9 and kept scoring 0 after the
verifier moved the report to descriptor 8 - they had stopped attacking anything, and only the
marker check said so. And `cheat-plant-verdict` scored 1 when it was built on the reference
policy, because writing to a descriptor the runner then truncates and rewrites is not an attack;
it is now a denial test against the report and reward paths themselves.

## The re-attack on the finished task (D7)

Read cold, the draft brief handed over more than the rules. Two sentences explained the
*consequence* of the reading rule rather than stating the rule - that a block only grows down
and right, so a read into a cell's own quadrant is self-referential, and that reads up, right on
an earlier row, or down on an earlier column are fine. Those are exactly the derivation the
agent should have to make from the reading rule and the placement rule, which are both stated in
full immediately above. Both sentences are cut. The rules they were explaining are unchanged and
still tested, by `read-into-own-quadrant`, `read-same-row-to-the-right`,
`read-up-and-right-is-fine` and `read-down-and-left-is-fine`.

The symptom paragraph was also cut back: it now says what the printout shows and what the cell
should have been, and no longer diagnoses why the shipped engine got it wrong.

Estimated solves after the re-attack: unchanged at 2 (range 1-4).

## The cold self-probe: not run, and why

It cannot honestly be run here. The order of work was design, then reference, then sealed model,
then environment, so by the time a scratch copy of the brief and the tree existed the assistant
had written every rule and every answer. A cold solve by this author would measure memory, and a
self-probe reported as passed by a contaminated author is worse than no self-probe. What stands
in its place is measured rather than asserted: fifteen wrong readings each separated by a named
case and by the generated families, a shipped engine that moves 100% of scripts, an answer-key
carrier that reproduces every enumerated script and still scores 0, and no oracle anywhere in
the agent's tree.


## Quality self-review (docs/QUALITY-REVIEW.md), criterion by criterion

**Instruction and verifier agree, in both directions.** Every test group maps to a stated
sentence: `test_a_block_occupies_and_is_refused` to the paragraph beginning "A block belongs to
the cell"; `test_a_block_stays_inside_the_sheet` to "refused if the rectangle would leave the
sheet" and the count-bounds sentence; `test_the_loop_rule` to the loop paragraph;
`test_reading_a_cell` to "Reading a cell is therefore not reading its content" and to the
arithmetic paragraph; `test_the_shape_preserving_functions` to the function paragraph. In the
other direction, every promise is tested: the sixty-command ceiling, the ten-by-twenty sheet and
the two commands by `test_the_scripts_stay_inside_the_stated_bounds`; "nothing outside the four
files is read" and "the rest stay as they are" by `test_the_executed_tree_is_the_shipped_tree`
and `test_frozen_functions_were_the_shipped_ones`. The four artifacts are named with absolute
paths, and the printed line's shape is stated and then shown verbatim.

**Dangling references.** Checked mechanically: every `/app/...` path the instruction names
exists in the shipped tree, every one of the ten function names appears in the brief, and the
example line quoted in the brief is byte-identical to what the shipped engine prints for that
command. The example is the shipped engine's *wrong* output, so it is a symptom, not an oracle.

**Verifier rigor.** The tests demand evidence rather than a report: the frozen functions are
hashed as the run held them and compared with digests compiled from the untouched sources, the
executed tree is compared file by file, a printed line is accepted only from the driver's own
code object, and the interpreter's own count of driver entries must equal the number of lines.
Test code is grouped and commented by the behaviour it checks. Nothing depends on wall clock,
network or unordered iteration; the families are seeded and the enumerated expectations are
pinned in gt.json.

**Environment hygiene.** `environment/Dockerfile` copies `app_src` and nothing else; neither
`tests/` nor `solution/` is reachable from it. Every Python package is pinned with `==` and no
apt package is installed at all. The agent-facing tree carries no comments, docstrings, README
or `.md` file.

**Solution quality.** `solution/solve.sh` copies the four reference files into the tree and runs
the engine over the shipped scripts; it computes, and it uses nothing the agent could not.

**Anti-cheating.** The answers are not in the environment: the tree is the runtime, the four
policy files and two input scripts, with no expected output anywhere. Grading is exact, so a
degenerate output fails. Nothing clones a repository. And the strongest evidence is measured
rather than asserted: a submission carrying gt.json verbatim reproduces all 45 enumerated
scripts and still scores 0.

**Metadata.** Category and subcategory are `Software` / `Algorithms` - the graded work is mutual
recursion, ordering and memoisation, and the calculation engine is the setting; `catcheck`
measures 74 environment hits for that vocabulary against 80 in the prose. Tags name mechanisms,
not the taxonomy. `difficulty_explanation` names the step that breaks - the dependency graph
that cannot be built - and says plainly that the terse naming and the absent comments are a
design choice. `solution_explanation` describes the method actually implemented and was re-read
against the code after the last change to it. `verification_explanation` quotes counts that were
re-derived from the code rather than remembered. `expert_time_estimate_hours` is 8.
`relevant_experience` is a draft and is the contributor's to write: it must not ship as written.

## Open questions and next steps

Batched for the contributor, once: which candidate; category and label from the guideline
table plus approval of the proposed tags; the domain-expert role in their words; whether they
have a repository to mine; the agent timeout and their own expert-time estimate; and then the
instruction itself in their words, against the fact sheet the assistant will hand over.

Infrastructure, reported plainly: Docker's daemon runs in this session but image pulls are
refused by the egress policy (the registry blob host answers 403), and there is no local image
cache, so no container evidence can be produced here. `harbor` is not installed for the same
reason. Everything below the container line - host emulation through `tools/docker_trial.py`,
`tools/imagecheck.py`, the cheat suite, the variant suite and `preflight.py` - does run, and
every result will be labelled for which of the two it is.
