# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a storage-engine engineer on the index layer of an embedded key-value store: page
layout, prefix-compressed pages, splits and joins, and the strings that divide neighbouring
pages. You have written and debugged page fit accounting, split-position selection and
underflow handling, and you know that the shortest-separator rule every textbook states at
split time is not the rule a store keeps when its pages have to be a pure function of the
keys they hold.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the
  tree is written here rather than degraded from a source; identifiers are chosen in the legacy
  register directly (`pg/`, `fit`, `cut`, `bound`, `join`, `step`, `seek`, `kids`, `seps`) and no
  name misdescribes what it holds
- Proper-noun sweep done? No product, project, company or engine name appears anywhere in the
  agent-facing tree; the domain words that remain (page, key, separator, leaf, capacity) are the
  ordinary vocabulary of index work and carry no provenance
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the page layer of an ordered index. A program is a text file that declares a page
capacity and a fill floor and then puts and deletes keys; `/app/run_idx.py` prints one line per
structural event. The shipped layer is the textbook one: a running byte counter per page, a cut
at the middle entry, a separator copied whole out of the right half at cut time and never looked
at again, and a join when two counters add up to no more than capacity. The specification is the
store's own. A page holds the common prefix of its entries once and only the remaining
characters of each, so its stored size is recomputed from the key set every time it changes; the
string between two neighbouring pages is always the shortest one greater than the last key on
the left and not greater than the first key on the right, so a delete that takes one of those
two keys rewrites it, often several levels up; and the position a page is cut at is scored on
the larger half and on what the promoted string costs the page above. The agent rewrites the five files under `/app/pg/` that decide
size, boundaries, cutting, joining and the order of the work in one operation.

## Why it is hard

The first plan is the textbook page layer and it is wrong at the first decision of every
operation; the rule that replaces it makes size non-additive, and the rule after that makes the
string between two pages a derived value whose upkeep the delete path has no place for.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised page layer keeps a used-bytes counter, cuts at the middle, and fixes a dividing string once at cut time, and every one of those is wrong here. Here the size of a page is a function of the key set it holds,
  so an insert that shortens the common prefix enlarges every other entry and two half-empty
  pages can be larger joined than apart; and the dividing string is a function of the two keys
  around it, so a delete that takes a page's least or greatest key rewrites a string that is
  often several levels up, shrinking a page the operation never reached and joining it to its
  sibling. A plan whose upward work is driven by splits and joins alone has no place to put
  that, and the scoring of a cut position reaches into the page above, so cutting is not a
  page-local decision either.
- Tactics making that true (prong A poison, prong B withholding, prong C late failure): A1, A2, B2, C1, C2, C3 and C4 - poison, withholding and late failure together. A1 the shipped layer is the model's prior implemented faithfully and it
  is the wrong answer at every decision; A2 the brief states that a page holds its common prefix
  once and that every dividing string is at all times the shortest one, and never says that
  sizes are therefore non-additive, that only a delete can move a string, or that the one to
  rewrite may be several levels up, so all three consequences must be derived; B2 ten decisions hold at once and getting the size rule right
  changes what the join test and the cut score mean; C1 both sides are graded, so cutting a page
  that fits once its prefix is credited fails as surely as leaving one that does not; C2 no
  library implements these rules and on keys that share no prefixes the shipped layer and the
  specified one agree line for line; C3 restoring the invariant over the whole index after
  every operation stays exactly correct and was measured at 373.0 seconds against the
  reference's 1.7 on the identical graded population, against a stated limit of 120; C4 every program is compared line for line against a population
  generated after the agent is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was a used-bytes counter per page, a cut at the middle entry when the counter passes capacity,
  the first key of the right half handed up as the separator, and a join when two counters sum to
  no more than capacity. It is wrong four times over: the counter cannot express a page whose
  entries change size when a neighbour arrives; the middle is not where the store cuts, and the
  score it does use reads the page above; the separator is three characters where the counter
  plan copies eight, and it is re-derived on operations that split nothing; and the join test is
  over the union of two key sets, which can be larger than either page suggests. The plan I would
  write after reading the brief is right in outline, because every rule is stated, and wrong in
  structure: a remove-then-rebalance-upward loop has nowhere to run the rewriting of a dividing
  string, the string to rewrite is often in an ancestor rather than the parent, and the rewrite
  has to run before the floor test or the page above is not joined.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 of 8
  (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100, in band, no hard stop. There
  was only one attempt, so nothing changed between attempts. Its one warning, that the resource
  gate was declared and not measured, was closed at Stage 4 and the record now carries the
  measured numbers. Re-run at Stage 7 against the built tree it scores 100 again, measuring 324
  environment lines, 5 editable files and 354 reference lines with no drift.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 record scored 100
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": no event carries a
  size, a fill level or a common prefix, so the size rule cannot be checked against anything the
  runtime prints; the frozen page record holds only the sorted key list, the child list and the
  separator list, so no prefix and no size is a field to read off; the frozen core has no
  shortest-separating-string helper, and the one that exists ships wrong, returning the whole
  key; the sample programs ship without their traces and the graded population is generated after
  the run, so nothing scores an intermediate state; the run prints no page count and no depth, so
  the structural result is visible only as the events the agent's own rules produced.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped programs and read which module prints each kind of line; replace the used-bytes counter
  with a size computed from the key set and its common prefix; notice that the common prefix of a
  sorted run is the common prefix of its two end keys, which is what makes the size cheap; derive
  the separator rule and write the repair that runs when a page's first or last key moves; order
  the work in one operation so repair happens before the page is tested against capacity; rewrite
  the cut so every position is scored on both halves and on what the promoted string costs the
  page above, with the stated ties; rewrite the join test over the union of the two key sets and
  carry the cascade upward, including the internal join that brings the dividing string down and
  the fold of a root left with one child; then time the two large programs and replace the
  tree-wide separator sweep and the whole-page prefix scan with repair along the descent path and
  an end-key prefix.
- Originality check: searched 2026-09-22 for the mechanism. The literature carries prefix
  truncation and suffix truncation together in Bayer and Unterauer's prefix B-tree paper, the
  shortest-separator rule applied once at split time, split positions chosen to yield a short
  separator in storage-engine notes and source comments, and an observation in a recent
  space-management paper that prefix compression can let two underfull nodes fit in one. Not one
  of them rewrites a separator after a page has been cut, tests capacity against a size
  recomputed under the page's current prefix, or scores a cut position by the bytes the promoted
  string adds to the page above. The best retrievable page hands over a model in which boundaries
  change only when a page splits, which is wrong here in the direction that matters.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. The walk is
`authoring/page-bound-cut/trace.md`.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 72 rows walked - 4 test functions, 31 enumerated cases, 5 artifacts, the 120 second clock, 20 rules of the sealed model split one per rule with its line range, and 10 event formats - plus 22 readings and 5 shortcuts. No NOT STATED row survived, and `python tools/tracecheck.py page-bound-cut` is clean. The trace is generated by `authoring/page-bound-cut/trace.py`, which asserts every quote is in `instruction.md` verbatim before it writes, so a reworded brief fails there rather than at the checker. One note remains and is structural: readings.py builds its table from emit.py, so the tool cannot read a literal name list and the readings are cited by hand.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 22 readings were written as patched engines by `authoring/page-bound-cut/emit.py` and measured by `python tools/readingcheck.py page-bound-cut 260`. All 22 are separated by the enumerated set. Twenty-one of the cases were found rather than chosen: `pick.py` drew small programs from the shipped families until one made the reading disagree with the reference, then shrank it one operation at a time, giving cases of 2 to 17 operations. The twenty-second, the root folding twice in one operation, needed 71 targeted draws before one appeared. Four candidate readings were dropped after measurement because nothing can separate them: two are unobservable (the root is kept out of the join by the walk, not by the floor test) and two describe a situation that never arises (a half still over capacity after a cut, in 0 of 4600 programs), and the last is now settled by a sentence instead.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop scores 0 with 28 of 34 assertions failing; `cheat-const-quiet`, which prints no structural event at all, scores 0 and moves every program of a 30-program sample; `cheat-pos-low` and `cheat-pos-high` score 0 and move 30 of 30; `cheat-forge-hand` carries the frozen traces of all 31 enumerated programs in a table over the shipped engine, reproduces every one of them and fails the generated sample. Its first version keyed the table on `id(tr)`, and an object id is handed out again once the tree before it has gone, so it reproduced 4 of 31 and its zero would have said nothing. `cheat_report.py` asserts the count, which is how that was caught.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/page-bound-cut/variants/ok-list` and `.../ok-worklist`, both written apart from the reference, settle the whole graded population in 20.7 s and 1.8 s against the reference's 1.7 s and the stated 120 second limit, all three printing the identical 197066 lines. The exactly-correct `variants/slow-sweep`, which restores the invariant over the whole tree instead of locating the string that moved, takes 373.0 s on the same population. There is no numeric tolerance: the trace is compared string for string.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token. Seven gaps were found and closed in the brief: which of the two strings beside a removed page goes, what happens when a removal empties the page above it, that an emptied root leaf stays, that the root is never joined, that a page still over capacity after a cut is left alone, the order in which the fresh half and the fresh root take their ids, and that a freed id is handed out again. One sentence carries no reading that contests it - that page ids come from one pool for every kind of page - and it is kept because the ids are graded and the agent is owed the fact.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. A later change to any of this changes what "correct" means and needs the
contributor's explicit approval.

- Artifacts the agent produces: `/app/pg/fit.py`, `/app/pg/bound.py`, `/app/pg/cut.py`,
  `/app/pg/join.py`, `/app/pg/step.py`. Nothing else is collected; the verifier lays those five
  files over its own pristine copy of the tree and runs the programs from there.
- What is checked: the stdout trace of every graded program, line for line, exactly. Enumerated
  programs against `tests/seal/gt.json`, frozen before the grading file was written; generated
  programs against the sealed model, which must itself still reproduce `gt.json`.
- Tolerances: none, the trace is compared string for string. The only limit is the wall clock on
  the stage that runs submitted code, validated against two independently written correct
  implementations.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory `chmod 700` before the privilege drop.

### The graded decisions, each with the instruction sentence it is owed

1. **Stored size.** Header bytes, per-child bytes on an internal page, the common prefix of the
   entries once, and two bytes plus the remaining characters for each entry. Sentence: the size
   formula, stated with its constants.
2. **Capacity and floor.** Over capacity is strictly greater; under the floor is strictly less
   and never applies to the root. Sentence: both tests with their strictness and the root
   exemption.
3. **Separator derivation.** The shortest string greater than the greatest key to its left and
   not greater than the least key to its right. Sentence: that definition.
4. **Boundary repair.** Every separator is that string at all times after an operation, so one
   is derived again whenever either defining key moves, and a line is printed only when the value
   changes. Sentence: the invariant, plus that only a change prints.
5. **Order inside one operation.** Repair runs before the page is tested for capacity or the
   floor. Sentence: the order.
6. **Cut scoring.** Every position that leaves at least one entry on each side is scored on the
   two halves plus what the promoted string adds to the page above, or to the new root when the
   cut page is the root. Sentence: the candidate set and the three terms.
7. **Cut ties and recursion.** Lowest score, then the nearer-equal entry counts, then the smaller
   position; a half still over capacity is cut again, the left one first. Sentence: the tie order
   and the re-cut.
8. **Join.** A page under the floor takes its right sibling if the joined page is within
   capacity, otherwise its left sibling on the same test, otherwise it stays; the right page's
   entries move into the left one and the right page is freed; an internal join brings the
   dividing string down. Sentence: the choice order, the test and the internal case.
9. **The emptied leaf.** A leaf other than the root that loses its last key is removed, and of
   the two strings beside it the left one goes when it has a left neighbour. Sentence: that rule.
10. **Upward pass, root creation and fold.** The pages from the leaf to the root are tested in
    that order; a cut of the root makes a new root after the right half is allocated; a root left
    with one child is replaced by that child. Sentence: the walk, the allocation order and the
    fold.
11. **Page ids.** A new page takes the smallest positive integer not in use. Frozen in the store,
    and still owed a sentence because the ids are graded.

### Prong C tactics this contract uses, and the route-around guard

- C1 both sides: enumerated programs where a page that fits must not be cut and a pair that does
  not fit must not be joined, beside the programs where the opposite holds.
- C2 the obvious oracle is denied: no size, prefix or fill level is ever printed, and the sample
  programs ship without their traces.
- C3 the resource gate: two large programs whose declared capacity makes pages hold hundreds of
  entries, where a whole-page prefix scan and a tree-wide separator sweep stay exactly correct
  and go over the clock.
- C4 all or nothing over enumerated corners and a population generated after the agent is gone.
- Guard: only the five policy files are collected. The page record, the id pool, the descent, the
  event writer, the program parser and the driver are the verifier's own copy, so the trace
  format, the page identities and the allocation order cannot be reshaped.

## Decisions and their reasons

- **Software / Databases, not Algorithms.** The graded work is index page layout: fit accounting
  under prefix compression, split position, separators and underflow. `delta-view-retraction` is
  the other Databases bundle and its mechanism is incremental aggregate maintenance, which shares
  nothing with this.
- **Capacity and floor are declared per program.** A store's page size is configuration, and the
  small programs need pages of a dozen entries while the resource gate needs pages of hundreds.
  One global constant could not do both.
- **The dividing string is rewritten, not fixed at cut time.** This is the whole A2 tactic: the
  rule is one sentence and its consequences are the second discovery. Measured on the shipped
  families: a put can never move a string, because any key that routes into a page is already at
  or above the string above it, so an implementation that rewrites on puts is merely slow; a
  delete of a page extreme or the removal of an emptied page can, 674 times over the 104-program
  population; and 206 of the 4767 sites found were an ancestor rather than the parent.
- **An emptied leaf is removed rather than left in place.** Leaving it would make a separator's
  defining key absent and force the repair and join passes to alternate to a fixpoint; removing
  it keeps one repair pass and one resize pass per operation.
- **Puts only grow pages and deletes only shrink them.** A cut adds a string and a rewrite only
  ever shortens one, so a put needs only the capacity pass and a delete only the floor pass. That
  is a consequence of the rules rather than a rule, and it is what lets one pass handle each
  direction.
- **A non-root page left with one child is legal.** Replacing it by its child would make its
  subtree one level shallower than its siblings, and the next join at that level would then put
  a leaf and an internal page together. That defect was caught by an invariant check during the
  build. The tree loses height only at the root, and a page that holds nothing at all is removed,
  which cascades without unbalancing anything.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py --build`; harbor is not installed in this session |
| No answer leaked into agent image | pass | `imagecheck` assembles the 15 files the image would hold and runs all four shipped programs in it; `extraneouscheck`, `deadfieldcheck` and `forgecheck` clean |
| `harbor run -a oracle` = 1 | pass | `docker_trial.py page-bound-cut oracle`: reward 1, 34 tests in 5.6 s |
| `harbor run -a nop` = 0 | pass | `docker_trial.py page-bound-cut nop`: reward 0, 28 of 34 failing |
| Cheats all score 0 | pass | `docker_trial.py --all`: 37/37, being the oracle, the nop and 35 cheats |
| Correct variants score 1 | pass | `--dir .../variants/ok-list` and `.../ok-worklist`, both reward 1, 34 tests |
| `tracecheck.py` (every graded assertion traced) | pass | clean, 72 rows |
| `readingcheck.py` | pass | 22 readings, every one separated by the enumerated set |
| `onelinecheck.py` | pass | no graded decision is reproduced by a rule at depth 2 or less |
| `preflight.py` | pass | 0 errors |
| `harbor check` rubric | not run | no API key in this session; the manual review in docs/QUALITY-REVIEW.md was walked instead |

## Stage 7 re-attack, run cold on the finished bundle

Read the final brief with the built tree in front of me and tried to one-shot the plan.

- **Is the first plan still wrong?** The plan from the prior is a used-bytes counter, a cut at
  the middle entry, a dividing string copied out of the right half at cut time and a join when
  two counters add up. That is the shipped layer, and it is wrong at the first decision of
  every operation. The plan *after* reading the brief is right in outline, because every rule
  is stated; it is wrong in structure. A running total cannot represent a page whose entries
  change size when a neighbour arrives. A delete path that removes and then rebalances upward
  has no place to put the rewriting of a dividing string, and the string to rewrite is often
  not in the parent - 206 of the 4767 sites measured over the population are an ancestor
  reached by climbing. A cut scored on the page alone gets the position wrong whenever the
  promoted string changes the common prefix of the page above. And the natural reading of an
  invariant stated over the whole index is to restore it over the whole index, which is
  exactly correct and 3.1 times over the stated limit. `tools/onelinecheck.py` measures the
  same thing from the other side: none of the four graded quantities - the cut position, the
  capacity test, the join side and the length of a dividing string - has an exact rule at
  depth two over anything the tree exposes.
- **Are the load-bearing facts still distributed?** They are stated rather than hidden, which
  is the doctrine: nothing is withheld. What is not stated is which structures survive all ten
  rules at once, and that is unchanged since Stage 1.
- **Did the instruction come to telegraph the method?** No. It states the outcome of each rule
  and never a data structure. `tools/hintcheck.py` is clean, and the one sentence that came
  close - that a put can only put a page over capacity and a delete only under the floor - was
  taken out when I noticed it hands over half of the second discovery.
- **Updated estimate of solves out of 8: 2** (range 1 to 4), unchanged from Stage 1. The honest
  argument against a lower number is that every rule is in the brief and a meticulous
  implementer who holds all ten at once wins. The argument against a higher one is that
  nothing printed is a size, a fill level or a common prefix, so no decision has feedback; the
  grading is all or nothing over 153 programs; and the implementation the invariant invites is
  over the clock.

## What the isolation probes report, not just that they score 0

Read out of the verifier container, from the worker's own stderr rather than from the reward:

- `cheat-probe-answer-key`: `gt PermissionError`, `model ModuleNotFoundError`. The frozen
  answers cannot be read and the sealed model cannot be imported by code running inside the
  verifier.
- `cheat-probe-privilege`: `uid 1002`, `reward PermissionError`. Submitted code is
  unprivileged and the reward is not writable by it.
- `cheat-probe-kit`: `kit PermissionError`. The case table cannot be rewritten from inside.
- `cheat-probe-late-reward`: `left over from stage one, killed: 1`. The double-forked survivor
  was reaped, and `/logs/verifier` is `drwx------ root` while the submission runs.
- `cheat-probe-plant` reports `record PLANTED` and still scores 0, because the grader rebuilds
  the population from its own copy of the seed and checks a digest of each program.
- `cheat-probe-shrink` reports `generator SHRUNK` and still scores 0, for the same reason.
- `cheat-probe-crash` exits the worker cleanly after planting, so stage one exits 0 and the
  grader is what refuses; `cheat-probe-malformed` leaves garbage behind the worker's own write
  and the defensive parse turns it into a failure rather than a crash past the verdict.

## Open questions and next steps

The easiness probe has not been run: this session has no probe harness, and a self-probe by
the author who wrote the model would measure memory rather than difficulty. The reading
separations, the layer report, the answer-shape measurement and the cold re-attack below stand
in its place, and the estimate is what they support.

## Quality self-review (docs/QUALITY-REVIEW.md, walked criterion by criterion)

**Instruction and verifier agree both ways.** Every graded assertion has its row in
`authoring/page-bound-cut/trace.md` and `tracecheck` is clean. The converse was walked by
hand: every sentence of the brief is graded by the trace comparison, except three that
describe the environment rather than a behaviour - that four sample programs sit under
`/app/progs`, that one of them is the size of the large graded ones, and the note that ids
come from one pool for every kind of page. The first two were re-derived from the tree, and
the third is a fact the graded ids depend on.

**Counts.** Re-derived from the code rather than from memory after the last generator change:
31 enumerated programs, 122 generated (fifteen families at eight plus the two large ones),
153 in all, 197066 trace lines, 120 seconds, capacity 32 to 160, floor 10 to capacity minus one. The
two large programs are about 93200 and about 61300 operations; the brief says about 93000 and about 60000,
and the second figure was corrected from the generator rather than from the plan.

**Boundaries.** Two strict inequalities (capacity and floor), one tie (the cut position), one
index base (a string's position counts from 0), the empty page, the empty root leaf, the root
that is never joined and the id that is handed out again are all settled in the text, and each
has an enumerated case named for it.

**Verifier rigor.** The tests run the submitted modules over a pristine copy and compare the
whole trace; nothing is taken on the submission's word. `tests/test_outputs.py` opens with the
frozen contract and is sectioned by what each block checks. The only wall-clock dependence is
the stated 120 second limit, measured at 5.8 times the headroom on the slowest of two
independently written correct implementations.

**Environment hygiene.** `environment/Dockerfile` copies `app_src/` and nothing else; pytest is
pinned at 9.1.1 with ctrf 0.5.2 in `tests/Dockerfile` only; no apt package is pinned;
`imagecheck` assembles the 15 files the image would hold and runs all four shipped programs in
it. No comment or docstring appears anywhere under `environment/`.

**Solution quality.** `solution/solve.sh` copies five source files into place and runs three
programs; it computes nothing by hand and writes no answer.

**Anti-cheating.** The trace carries no size, fill level or common prefix, so no graded
quantity can be fitted to a printed number; the generated programs do not exist until the seed
is drawn after the agent's container is gone; `forgecheck` finds one forgery probe and no
ground truth in the agent tree; the sealed directory is 0700 root-owned before the privilege
drop, and the probes report `PermissionError` rather than only a zero.

**Metadata.** Software / Databases is a row of the guideline table; `tools/catcheck.py`
measures 85 storage-software terms in `environment/` against 75 in the prose, so the category
is carried by the code and not by the story; the five tags name techniques rather than the
taxonomy; `difficulty_explanation` names the concrete step and states the legacy-register
naming as a design choice; `expert_time_estimate_hours` is 9, consistent with the claim.

**Known risks a reviewer should see.** `tools/textcheck.py` reports the brief's type-token
ratio at 0.252 against 0.300 for the reference; the two retained briefs closest in shape read
0.258 and 0.260, and the figure is what a rule specification over a six-word domain vocabulary
gives. Burstiness is 0.956, inside the retained band of 0.74 to 1.11. `tools/simcheck.py`
flags only the two Dockerfiles, whose content is prescribed by the kit; `test.sh`, `reap.py`,
`worker.py` and `test_outputs.py` are below its threshold and are mine. `harbor check` was not
run: no API key is available in this session, and harbor is not installed, so every container
result above comes from `tools/docker_trial.py`, which builds both images and runs the same
two-container trial.
