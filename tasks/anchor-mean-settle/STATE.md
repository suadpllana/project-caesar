# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - pre-flight and packaging`

## Assistant's assigned role

A view-layer engineer who has maintained a virtualised list panel in a desktop-class
client: the part that decides how tall a row it has not rendered yet is assumed to be, what
a render pass is allowed to measure, and where the scroll position lands after the assumed
heights turn out to be wrong. Familiar with the fact that a panel which measures as it
renders has two coordinate systems that disagree - the one the user is looking at and the
one the index believes - and that reconciling them is the whole of the work.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The first prompt named no repository, so there is no
  vendored tree, no license question, no identifier degradation table and no upstream diff.
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): neither applies; the
  panel is authored here in full.

## Task summary

`/app` is a virtualised list panel cut down to the part that decides layout. A program is a
text file of ops: rows are imported, inserted, deleted, moved and re-texted, the panel is
re-widthed, the view is scrolled, a render pass measures what it can see, and three
questions ask the scroll position, the total height and which row is at the top of the view
with its offset from the view's top edge. A row that has not been measured is assumed to be
as tall as the mean of the rows that have been, so every measurement re-heights every
unmeasured row in the list. Six modules under `/app/pan` ship wrong. The task is to make
every program's trace come out right, inside a stated execution limit that the shipped
structure cannot meet.

## Why it is hard

The first plan is the one every virtualiser in the training data uses and the one the
retrievable sources show: a measured height per row, a fixed estimate for the rest, an
array of absolute offsets, a binary search for the visible window, and a scroll correction
equal to the anchor row's offset delta. Here the assumed height is a single global mean
over the measured rows, so measuring any row changes the height of every unmeasured row and
invalidates every stored offset at once - the array is not stale from the changed index
onward, it is stale everywhere. That is the first discovery, and it is a structural one: no
absolute offset can be stored at all.

The second discovery invalidates the implementation the first produces rather than adding a
case to it. A pass measures the lowest-indexed unmeasured row of the view and re-seats the
scroll position before it chooses the next one, so the set of rows a pass measures is a
fixed point and not the window it computed at the start: each measurement moves the mean,
which moves the anchor's offset, which moves the scroll position, which changes which rows
the view holds. A measure-the-window-then-compensate step, which is what the first plan
builds and what the retrievable libraries do, reports the wrong count and lands at the
wrong scroll position - and it does so only on the programs where the mean actually moves,
which the ordinary cases are careful not to be.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the correct plan needs two findings that cannot be made from the brief alone.
  The first is that a prefix
  offset factors into a measured-height sum plus an unmeasured count times one global
  scalar, so nothing positional may be stored. The second is that the render pass is an iteration
  whose window is recomputed after every single measurement. The first is arithmetic the
  agent has to do; the second only shows up when a measurement moves the mean far enough to
  change the window, which no ordinary scrolling program does.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, A3, B2, C1, C2, C3, C4.
  A1 the per-row height cache with a fixed estimate is the prior and
  is specifically wrong; A2 the mean, the pass loop and the re-seat are stated as behaviour
  and no estimate policy, anchoring concept or indexed structure is ever named; A3 prefix
  offsets must survive insertion and deletion at any index while never being stored, which
  neither the offset array nor a plain indexed tree over a fixed order gives; B2 fourteen
  stated rules hold at once and each changes what another means; C1 both sides of every
  fence are graded, so a defensive re-seat fails the everyday cases; C2 there is no layout
  engine in the image and nothing prints the mean, the anchor or any offset, so the only
  oracle available is the shipped engine, which is coherent and wrong; C3 walking the row
  list is exact and is what ships, and cannot finish the graded set inside the stated limit;
  C4 every event of every program is compared line for line against a sealed independent
  model over hand cases and nonce-generated families.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan was the retrievable one, and it was wrong in three places.
  It was a dict of measured heights, a fixed default for the rest, a prefix-offset array
  rebuilt from the lowest changed index, a binary search for the window, and `top +=
  new_off(anchor) - old_off(anchor)` after measuring the window. Three things in it are
  wrong here and I would not have found them before running cases: the default is not fixed
  but the floor mean of the measured rows, so the array is invalidated globally by any
  measurement and cannot exist; the pass is a fixed point, not a step, so the measured count
  and the landing position are both wrong; and the anchor's offset from the view's top edge
  is captured once for the whole pass, so a clamp at either end of the scroll range loses
  the residue instead of being absorbed into it. My first plan was not the correct one.
- Estimated solves out of 8: 3 (2 at Stage 1, revised up at Stage 7; the reason is in the re-attack below)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml,
  before Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-13 scored 100/100, in band (95-100), with
  one warning - `gate.measured` was still false. Nothing was changed to reach the band; the
  gate was then measured rather than promised and the record updated to `measured = true`,
  along with the input scale and limit that the measurement settled. Re-run at Stage 7 with
  the tree built: 100/100 again, measuring 248 environment lines, 6 editable files, 443
  reference lines, 34 cheats (26 of them semantic) and 3 variants, with no drift reported
  against the planned shape.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not
  set yet - no complete submission.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-13 record
  scored 100; no pipeline result yet.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing":
  - the mean estimate: never printed, and no op returns it. It is observable only folded
    into a total, a scroll position or a face offset, each of which also depends on the
    anchor rules and the pass rule.
  - the held anchor: no op prints it. `face` reports the first row intersecting the view
    from the current scroll position, which stops being the held anchor after any edit.
  - any row's offset: no op takes a row and prints its position, so the prefix arithmetic
    cannot be read off.
  - measurement state: no op reports whether a row has been measured; it is only inferable
    by reasoning about what a pass would have measured.
  - expected output: the tree ships op programs and no traces. The frozen answers and the
    independent model sit in `tests/seal/`, `chmod 700` before the privilege drop, so code
    running inside the verifier cannot read them either.
  - the pristine tree: lives under `tests/`, never copied into the agent image.
  - stored derivations: the row records hold primitives only - id, text length, measured
    flag, measured height - and the panel holds the width and the scroll position. No
    offset, total, mean, window or anchor position is stored anywhere the agent can read.
- Expert path, described step by step (the harder the aim, the more this guard must hold):
  1. read `pan/mtr.py` for the height function and the four constants, and `run_pan.py` for
     the op set and the order it calls the six editable modules in;
  2. write the mean down as an equation and notice a prefix offset is the measured heights
     before the row plus the unmeasured count before it times one global scalar;
  3. conclude nothing positional can be stored, and pick a structure carrying those two
     additive series under insertion and deletion at any index - blocks over the row list, a
     tree indexed by position, or slots with tombstones and a rebuild;
  4. implement the pass as measure-one-then-re-seat-then-recompute, and check the count
     against a hand trace where the first measurement moves the mean enough to change the
     window;
  5. settle the anchor rules: captured before any measurement, its offset from the view's
     top edge held for the whole pass, the clamp at either end losing the residue;
  6. settle the edit rules: re-seat against the held anchor on every edit, a move keeping
     both its measurement and its anchor role, a delete falling to the row that took the
     index, `set` dropping one measurement and `span` dropping all of them;
  7. run the two wide programs, see the shipped walk miss the limit, and replace anything
     that walks the row list per event.
- Originality check: searched 2026-09-13 for the combination. The components are each
  documented - measurement caches and `recomputeRowHeights` in react-virtualized, the
  measure/observe loop in TanStack Virtual, the CSS scroll-anchoring note on compensating a
  size change, and a Fenwick tree for dynamic prefix sums. No source describes this
  combination, and the one that comes closest is actively misleading: the libraries key a
  fixed estimate per item, which is exactly what makes an offset cache sound for them and
  wrong here. Searches run: "virtual list running average estimated row height scroll
  anchoring compensation measured rows invalidate offsets" and "virtualizer measure visible
  rows one at a time until window stabilizes fenwick prefix sum measured sum unmeasured
  count global estimate". Nothing in the retained set of this repository is near it: the
  only other Frontend task, `focus-return-point`, is about focus lifetime across nested
  render transactions and holds no geometry.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: exactly the six modules it may change -
  `/app/pan/grid.py`, `/app/pan/gues.py`, `/app/pan/seat.py`, `/app/pan/step.py`,
  `/app/pan/edit.py`, `/app/pan/ask.py`. Nothing else is read from the agent's container.
- What is checked: the verifier lays those six files over its own pristine copy of the tree
  and runs every graded program through it, comparing the printed trace line for line
  against expected output. All or nothing.
- Graded decisions, and both sides of each fence:
   1 the assumed height of an unmeasured row is the floor mean of the measured rows' heights
     over the live rows, and the default only when none are measured
   2 that assumption applies to every unmeasured row, so a total and every offset move when
     any row is measured
   3 a pass measures the lowest-indexed unmeasured row of the view, re-seats, and recomputes
     the view before choosing the next - a fixed point, and `seen` counts what it measured
   4 the anchor is the first row intersecting the view, captured before the pass measures
     anything
   5 the anchor's offset from the view's top edge is held for the whole pass, so a clamp
     loses the residue rather than absorbing it
   6 a re-seat is clamped to the scroll range, which the total height decides
   7 `roll` clamps and then re-captures the anchor
   8 every edit re-seats against the held anchor
   9 deleting the anchor falls to the row that took its index, or to the new last row, and
     keeps the held offset
  10 a move keeps the row's measurement and its anchor role
  11 `set` drops that row's measurement, and with it a sample from the mean
  12 `span` drops every measurement, so the assumed height falls back to the default
  13 `face` names the first row intersecting the view and its offset from the view's top
     edge, which is zero or negative
  14 `tall` counts unmeasured rows at the assumed height
- Must-still-work side: a pass whose view is already measured prints `seen 0` and leaves the
  scroll position untouched; an edit below the last visible row changes the total and moves
  nothing; a `roll` on a fully measured list lands exactly at the clamped sum.
- Tolerances: none. Exact string equality on every line of every trace, in order.
- Ground truth, and where it lives: `tests/seal/gt.json` holds the frozen trace of every
  hand program; `tests/seal/model.py` is an independently written implementation used for
  the nonce-generated programs, and the grader first asserts that the model still reproduces
  `gt.json` exactly. Both sit in a directory locked `700` before the privilege drop.
- Prong C tactics the contract uses: C1 every decision is graded from both sides, so
  overshooting fails; C2 the shipped engine is the only oracle available and it is wrong,
  and nothing exposes the mean, the anchor or an offset; C3 the execution limit kills the
  exact row-list walk that ships; C4 hand cases per decision plus generated families from a
  seed drawn after the agent's container is gone, exact and all-or-nothing.
- Route-around guard: `artifacts` lists only the six modules. The runner, the height
  function, the event writer and the programs are overlaid from the verifier's pristine
  copy, so the op set, the height arithmetic and the trace format cannot be reshaped, and a
  submission cannot move work into a file the verifier does not take.

## Measurements

All host-side unless the row says container. The host emulation lays a set of the six modules
over a scratch copy of the shipped tree; it is not the gate, only the fast loop.

| what | number |
|---|---|
| three implementations agreeing (naive walk, blocked index, position tree) | 900 random programs, 0 disagreements |
| the same three over the hand cases and every generated family | 154 + 60 programs, 0 disagreements |
| the graded set | 439 programs: 35 hand, 400 generated small, 2 wide and 2 deep |
| reference over the whole graded set | 7.3 s against the 60 s limit, 8.2x headroom |
| sealed model over the whole graded set | 3.4 s |
| a prefix read by walking the row list, over the graded set | 216.9 s, 3.6x over the limit, and identical traces on all 439 |
| an array of absolute offsets rebuilt on every change | did not finish inside the 700 s it was given; identical traces on the 114 programs it was checked against |
| one `wide` program (120000 rows, 6000 ops): reference against the walk | 1.4 s against 52 to 56 s, 37 to 40x, traces identical |
| the untuned position tree, one wide and one deep program | 0.88 s and 0.86 s, so the gate does not turn on tuning a block size |
| peak memory, reference and tree, on the wide families | 30 to 50 MB of the 2048 MB the task is given, so the gate is time and nothing else |
| wrong readings written and separated | 24, each failed by the enumerated case named for its rule |
| `tools/readingcheck.py` | 24 readings, 35 enumerated, 40 generated: all separated by the enumerated set |
| `tools/onelinecheck.py` | 1 of 4 graded decisions has an exact rule at depth <= 2, 3 do not |
| correct variants through the same verifier | 3, all scoring 1 in the container |
| cheats | 34, every one scoring 0 at the layer it was written for |
| environment / reference / editable | 248 lines over 10 files / 443 lines / 6 files |

## Decisions and their reasons

- Three implementations exist and agree: the naive walk (the spec written the obvious way),
  the blocked index that became the reference, and a position-indexed tree that became the
  sealed model. That trio is the differential evidence for the semantics, and the first of
  them is also the resource-gate cheat.
- The assumed height is a floor mean rather than a rolling average, so every graded number is
  an exact integer and there is no tolerance anywhere.
- The view height, the line height, the padding and the default assumed height are constants
  in the frozen `mtr.py`: the agent reads the arithmetic and cannot change it.
- The limit was calibrated in both directions rather than once. The first population gave the
  reference 9.1 s and the walk 165.5 s against 60 s - decisive against a slow machine and thin
  against a fast one, because a machine three times quicker than this one would bring the walk
  in under the limit. Two changes fixed both ends: the `deep` family now measures the band at
  the far end of the list, so each of its 9000 front edits moves a row the view is held against
  the whole length of the list away rather than eighty rows away, and two programs of each wide
  size are graded instead of three. The result is 7.3 s against 216.9 s - 8.2x of headroom for a
  correct panel and 3.6x of margin against the exact one that walks. Trying to make the wide
  family more expensive by pinning the view at the bottom did the opposite (54 s to 43 s): the
  naive cost is the number of re-seats times the depth of the view, and a view parked at the
  bottom measures nothing after its first pass.
- The shipped tree is the first plan, built out: a fixed assumed height, a prefix read by
  walking the row list, no clamp, no re-seat on an edit, a pass that measures its window in
  one step, a move read as a delete and an insert, and a total that counts only what has been
  measured. It runs, it is coherent, and it is wrong in eleven places.
- `probe-*` cheats are laid over a base that does not do the work (the reference with a fixed
  assumed height). The first three of them were built over the correct reference and came back
  reward 1 - honestly, by doing the work, which proves nothing about the isolation. Each probe
  now shouts a distinctive line if its attack lands and prints a denial when it does not, and
  `cheat_report.py` asserts the denial rather than the reward.
- Two kit checks were reporting false positives on every retained bundle and are fixed at the
  class rather than for this task: `preflight.py` counted a call through the module that owns
  it (`grid.hit(p)`) as no call at all, so every function in a package of modules that call
  each other was reported unused - 12 to 23 warnings per retained bundle, and the two genuine
  ones here were invisible among them; and it knew `echo 1 >` but not `printf '1\n' >` as a
  reward write. `build_gt.py` now hashes each case's ops beside its answer, so a retuned
  program is reported as a rewrite while an answer that moves on an unchanged program still
  stops the run. `docker_trial.py --variants` looked only inside the bundle, where the quality
  review does not allow authoring material to live.
- An unobservable distinction found by the cheat suite and reclassified rather than fixed: an
  op naming a row that is not in the list may re-seat or not, and no program can tell, because
  re-seating is idempotent in every reachable state. It is `authoring/variants/ok-miss-seats`
  and scores 1, not a cheat.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | container; `tools/docker_trial.py` builds both images from the shipped Dockerfiles |
| No answer leaked into agent image | pass | `tools/imagecheck.py`: 23 files, workdir /app, nothing from `tests/` or `solution/`; no `.md`, no comment, no docstring anywhere in `app_src` |
| oracle = 1 | pass | container, 38 tests, 5.6 s. harbor is absent here, so `tools/docker_trial.py` stands in - same two images, same shipped `tests/test.sh` |
| nop = 0 | pass | container, 1 passed and 37 errors: the shipped panel is both wrong and over the limit |
| Cheats all score 0 | pass | container, 34 of 34, each at the layer it was written for (`authoring/anchor-mean-settle/cheat_report.py`) |
| Correct variants = 1 | pass | container, 3 of 3 |
| `preflight.py` | pass | no errors, no warnings |
| `tools/extraneouscheck.py` | pass | every shipped file reachable, distinct and host-free |
| `tools/solvecheck.py` `deadfieldcheck.py` `hintcheck.py` `structcheck.py` | pass | clean |
| `tools/catcheck.py` | pass | software vocabulary: 38 environment hits, 133 in prose |
| `tools/forgecheck.py` | pass | the forgery carries `gt.json` and scores 0 |
| `tools/readingcheck.py` | pass | 24 readings, all separated by the enumerated set |
| `tools/onelinecheck.py` | pass | 1 of 4 graded decisions short, 3 not |
| `tools/simcheck.py` | one known finding | `environment/Dockerfile` at 1.000 against three retained bundles; see the note below |
| `tools/difficultycheck.py` | pass | 100/100 before code and again with the tree measured |
| `tools/prosecheck.py` | pass | worst shared phrasing with any retained bundle: 4 six-word runs in the metadata, 5 in the brief |
| `harbor check` rubric | not run | harbor is not installed here and it needs an API key |
| `tools/leakcheck.py` | not run | no probe trajectories exist for this task |

## Quality self-review, criterion by criterion (docs/QUALITY-REVIEW.md)

Instruction and verifier agreement, both directions:

- Every behaviour the tests check has a sentence. The fourteen graded decisions are listed in
  the docstring of `tests/test_outputs.py`; each maps to a clause of `instruction.md` - the
  assumed height and its default to paragraph 1, the total to paragraph 3, the scroll range
  and the clamp to paragraph 3, the held row, its distance, the re-capture on a scroll and the
  clamp residue to paragraph 4, the pass and its count to paragraph 5, the delete fallback, the
  move, the re-text and the width change to paragraph 6, `face` to paragraph 7, and the trace
  format to paragraph 8. The one rule that is not a graded decision, that naming a row which is
  not in the list does nothing, is in paragraph 1 and is tested by `gone-name`.
- Every behaviour the instruction promises has a test. Each of the above has an enumerated
  case named for it in `tests/cases.py`, and `authoring/anchor-mean-settle/readings.py` shows
  the wrong reading of each rule failing the case named for that rule.
- Every file the tests read is named absolutely in the instruction: the six paths of
  `artifacts` in `task.toml` are the six in paragraph 2, spelled identically.
- The output format is exact: paragraph 8 gives all four line shapes, and `pan/say.py` is
  frozen, so the format cannot drift from the brief.

Instruction prose: read cold as prose, twice. One parallel pair was rewritten (two
consecutive sentences of the form "X costs a row its measurement"); the op list in paragraph
1 is a deliberate enumeration inside one sentence rather than a run. `tools/hintcheck.py` and
`tools/structcheck.py` are clean, and the words `anchor`, `estimate`, `prefix` and `cache`
appear nowhere in the brief - `index` appears four times and always means a position in the
list, which is what the op set calls it.

The second reading was a measurement rather than a judgement, and it found a real problem.
Calibrating against the retained bundles had turned into copying them: the shipped metadata
shared 221 six-word runs with `slab-fold-scope`'s `verification_explanation` and 94 with its
`difficulty_explanation`, and the brief shared 83 with its instruction - whole sentences with
a noun swapped, in the two fields the similarity and AI-text screens actually read. All four
metadata fields and the brief's framing sentences were rewritten from the facts. The worst
overlap with any retained bundle is now 4 six-word runs in the metadata and 5 in the brief,
measured by `tools/prosecheck.py`, which was written for this and then corrected by its own
calibration: run across the whole repository it shows the retained set sharing between 0 and
417 runs, with the 417 between two bundles the contributor reports as passed, so it reports
the numbers rather than gating on them. The rewrite stands on its own ground - a passage
carried over wholesale is not this task's prose whatever the screens tolerate - and the claim
that the passing bundles sit at 15 to 17 was an artefact of comparing three of them instead of
eleven.

Verifier rigor: the tests demand a trace produced by running the submitted modules over 440
programs, not a state the submission could write; `tests/test_outputs.py` has a docstring per
section saying which behaviour it checks, and the sealed model carries the contract restated as
it implements it. Nothing depends on wall-clock time inside the assertions, on the network, or
on ordering that is not itself under test; the nonce seed changes the population but the
verdict is the same on every run, which the three correct variants scoring 1 demonstrates.

Environment hygiene: `environment/Dockerfile` copies `app_src/` and nothing else - no path
under `tests/` or `solution/` is reachable from it, which `tools/imagecheck.py` confirms by
assembling what the image would hold (23 files, workdir /app). Test dependencies are pinned in
`tests/Dockerfile` at the canonical `pytest==9.1.1` and `pytest-json-ctrf==0.5.2`; `test.sh`
installs nothing and touches no network. Every path and name in the brief exists in the tree
and is spelled the same, which `tools/extraneouscheck.py` and `scripts/preflight.py` both
check.

Solution quality: `solution/solve.sh` copies the six modules beside it into `/app/pan/` and
then runs the shipped example, so the answer is computed by the panel rather than written out;
the reference is stored once, not inlined. It uses nothing the agent could not use - the same
six files, the same frozen runner.

Anti-cheating: the answer is not in the tree. No op prints the assumed height, the held row or
any row's offset; the frozen answers and the model sit in `tests/seal/`, `chmod 700` before the
privilege drop, and `cheat-probe-answer-key` shows the read denied. There is no repository, no
git history and no cache in the image. Tolerances are exact string equality, so a degenerate
output fails; `nop` scores 0 and the forgery carrying every frozen answer scores 0 on the
programs it could not have seen.

Metadata: `category = "Software"` with `subcategory = "Frontend"`, a label from that row of the
guideline table, and the graded work is view-layer geometry rather than a story about one -
`tools/catcheck.py` measures 38 environment hits for the category's vocabulary against 133 in
the prose. The five tags name this task's mechanisms and none of them restates the category or
the subcategory. `difficulty_explanation` names the concrete step that breaks, says the tree is
deliberately compact and says the identifiers are deliberately terse.
`expert_time_estimate_hours = 10` is consistent with a 443-line reference over six files and
two structures to choose between.

## Stage 7 re-attack on the finished task (D7)

Read cold with the built tree in front of me, the questions the manual asks:

- **Is the first plan still wrong?** Yes, and for the reason it was designed to be. The brief
  states the assumption plainly, and the plan the statement invites is still the library one:
  a height per row, an estimate for the rest, offsets in an array, the visible window by
  search, a correction by the held row's change of offset. What the brief does not say, and
  what no sentence of it can be made to say without handing over the answer, is that the
  assumption being one figure for the whole panel makes every stored offset wrong after any
  measurement. That is a derivation, and it is the first thing an implementation has to get
  right before anything else it does is worth doing.
- **Are the load-bearing facts still distributed?** This task never claimed B1 and does not
  claim it now: the tree is 248 lines and readable in one sitting. What is distributed is the
  consequence rather than the fact - the assumption lives in `gues.py`, what it invalidates
  lives in `grid.py`, what that costs lives in the 60 second limit, and what the limit rules
  out decides the shape of `seat.py` and `step.py`.
- **Did the instruction come to telegraph the method?** No. The words `anchor`, `estimate`,
  `prefix` and `cache` appear nowhere in it; `index` appears four times and always means a
  position in the list. It states every rule and no structure.
- **Did debugging flatten anything?** Two things were added rather than removed during the
  build, both because a measurement said so: `clamp-hold`, after the readings report found a
  rule no enumerated case named, and `del-tail`, after `onelinecheck` showed the delete
  fallback reducing to one field because the branch where the deleted row was last was never
  reached. Nothing was simplified to make a gate pass.
- **Updated estimate of solves out of 8: 3, up from 2.** The reason for the revision, stated
  plainly: the expert path here is also a grinding path. An agent that writes the obvious
  implementation from the brief, writes a second one, and fuzzes them against each other will
  find every semantic mistake without needing the insight - that is exactly how one of the
  three easiness trajectories on `publish-settle-order` got there. The insight is still needed
  for the limit, and the limit is what the naive form misses by 2.75x over the whole set, but I
  will not claim a 1 for a task whose semantics can be reached by differential fuzzing. Still
  inside the band, and the zero-solve risk is low because that path is concrete.

## The cold self-attack, and why it is recorded as not run

Not run, and it must not be reported as passed. The order here was idea, then difficulty
record, then contract, then environment, then reference: by the time an agent-visible copy
existed I had already made both discoveries, so a cold solve by me would have measured memory
rather than difficulty. What stands in its place is written down and checkable: the 24 wrong
readings, each separated by the enumerated case named for its rule; the shape of the answer
measured by `onelinecheck` (three of four graded quantities have no exact rule at depth two);
the leak audit above, with nothing in the tree printing the assumption, the anchor or any
offset; and the two slow families measured to be exactly correct and outside the limit. The
external easiness probe is the authority on this task's difficulty, and nothing here claims
otherwise.

## Open questions and next steps

- No probe trajectories exist for this task, so `tools/leakcheck.py` has nothing to read.
- `harbor` is not installed in this environment and `harbor check` needs an API key, so
  neither was run. The oracle, nop, variant and cheat rows above come from
  `tools/docker_trial.py` and `authoring/anchor-mean-settle/cheat_report.py`, which build both
  images with the shipped Dockerfiles and run the shipped `tests/test.sh`.
- `tools/simcheck.py` reports `environment/Dockerfile` at 1.000 against three retained
  bundles. It is seven lines of boilerplate that every bundle needs and that the retained set
  already shipped at the same figure; `tests/test.sh`, `tests/Dockerfile` and `tests/reap.py`
  were rewritten rather than copied after it flagged them, and `tests/test_outputs.py` sits at
  0.648, inside the range the retained bundles occupy against each other.
