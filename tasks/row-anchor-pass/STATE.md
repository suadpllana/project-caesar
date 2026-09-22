# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a senior front-end engineer who owns the list virtualization layer of a desktop
application shell: the code that decides, for a document of tens of thousands of rows whose
heights are only known once they are on screen, which rows are rendered, where the pane scrolls
to after each event, and how a pinned group header interacts with both. You have shipped and
debugged scroll anchoring, sticky headers, measurement caches and the relayout loop that ties
them together.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable
- Contributor's relationship to it: not applicable
- License: not applicable
- Pinned commit: not applicable
- Load-bearing couplings: see "Where the facts live" below
- Identifier degradation done? The tree is authored, not vendored; identifiers are written in a
  legacy register (`pane/`, `geom`, `win`, `hold`, `band`, `est`, `hh`, `rid`) with no conversion
  table needed because nothing was renamed from an upstream source.
- Proper-noun sweep: no product, project or library name appears in the tree.
- Upstream-diff check: not applicable.

## Task summary

`/app` is the layout half of a virtualized list pane. A document is a sequence of groups; each
group has a header of known height and rows whose real heights are only learned when the row is
rendered, so until then the pane works from the group's per-row estimate. `/app/run_pane.py`
replays an event file - scrolls, jumps, viewport resizes, row inserts and row deletes - and prints
one line per frame: the offset the frame ended at, the pinned group and how tall its band came
out, the window of items the frame rendered, the item the frame held and the gap it held it at,
how many rows it measured and how many passes it ran. Six files under `/app/pane` are wrong. The
task is to make the pane's frames match the stated rules, inside a stated execution limit that the
shipped geometry cannot meet.

## Why it is hard

The published anchoring rule is coherent, is what the shipped pane implements, and agrees with the
specification on the majority of frames. It is the first plan anyone forms, and it is wrong in two
ways that do not show up in ordinary use: it anchors to the wrong item, and it treats the frame as
one adjustment rather than a loop whose own measurements move the thing it is solving for.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan the
  agent retrieves and the plan its prior supplies are the same plan - anchor to the first visible
  row, correct the offset by the height delta above it, render once - and that plan is correct on
  every frame where the band does not change, nothing is measured and no edit lands. The stated
  rules make the anchor the item under a pinned band whose height varies with the next header, and
  make the frame a bounded loop in which measuring changes the band, the band changes the solved
  offset, and the solved offset changes what gets measured. Neither of those can be reached by
  patching the first implementation: the correction stops being a delta and becomes a re-solve,
  and the driver stops being a sequence and becomes a fixed point with a cap.
- Tactics making that true (docs/DIFFICULTY.md): A1 A2 B2 C1 C3 C4, plus the route-around guard.
  A1: the published anchoring rule is the wrong one here and is right almost everywhere else. A2:
  the band, the anchor line and the held gap are described operationally and never named as scroll
  anchoring, sticky push-off or relayout passes. B2: nine rules hold at once and each changes what
  another means. C1: the ordinary frame that must not move is graded as hard as the frame that
  must. C3: the shipped walk over the flow is exactly correct and cannot finish the stated scale
  inside the stated limit. C4: every field of every frame is compared exactly, against hand
  documents and against documents generated after the agent's container is gone. The guard is that
  six files are collected and everything else, a new file beside them included, is replaced by the
  verifier's pristine copy.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my own first plan
  is the retrieved one - heights array, window from the offset, measure, sum the deltas above the
  first visible row, add to the offset, clamp, done. It is wrong at the anchor (the held item is
  the one containing the line under the band, not the first visible one), at the correction (a
  re-solve for a held gap, not a sum of deltas), at the driver (a bounded loop, not one pass), at
  the edit path (the hold is taken before the source changes and tracked with the tops it had
  then), and at the foot (re-derived per pass from a total the pass itself moved). I could not
  commit to the structure without first reading the tree to see which of those the shipped code
  already does.
- Estimated solves out of 8: 2 (design aimed at the hard edge of the 1-7 band)
- Difficulty record score (tools/difficultycheck.py, before Stage 2): 100/100 on the first attempt,
  2026-09-22, `authoring/row-anchor-pass/difficulty.toml`. Only warning: `gate.measured` is still
  a promise until the naive and expert timings are run, which happens at Stage 4.
- Difficulty score anchor: not yet submitted.
- Score history: 2026-09-22, 100, first record.
- Leak audit (docs/DIFFICULTY.md): the shipped geometry walks the flow with no cache, so the
  structure the fast path needs is not announced by the structure that ships; no expected output
  ships anywhere in the tree and the only correct output published is the single frame quoted in
  the brief; the per-frame measured count is path dependent and cannot be read off the window
  width; the row height function is shipped deliberately because true heights are not the secret -
  which rows have been measured is, and that is a property of the trajectory; nothing in the tree
  computes the band, the anchor line or the held gap except the live path the frame driver uses.
- Expert path, described step by step: run the shipped pane on the small document and diff its
  first frames against the frame the brief prints in full; re-derive the frame order (move, hold,
  edit, settle) from the brief; rebuild the band with the push-off against the next header and
  with it the anchor line and the sign of the gap; rebuild the held-item choice as the item
  containing the line; rebuild the driver as a bounded pass loop whose foot offset is re-derived
  from the total each pass; rebuild the edit path so the hold is taken before the source changes
  and tracked with the tops it had then; time the two large documents, find the walk over the flow
  dominating, and maintain group sums instead; re-run every document and check the per-frame
  measured counts and the closing total.
- Originality check: searched 2026-09-22 for "scroll anchoring virtualized list benchmark task
  agent evaluation" and for "scroll anchoring virtualized list sticky headers measurement pass
  fixed point implementation". What comes back is exactly the material the design is built to
  poison: the TanStack Virtual measurement and anchoring documentation, the CSS scroll anchoring
  specification thread, and the react-window and vue-virtual-scroll-list sticky-header issues. All
  of them anchor to the first visible element and correct by the accumulated delta in one pass.
  No public write-up of these rules exists, and no retained task in this repository works on list
  geometry: the nearest is `focus-return-point`, which is keyboard focus and render transactions,
  sharing no rule, no structure and no tag.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace: 79 rows in the graded-assertions table of `authoring/row-anchor-pass/trace.md`
  - 4 test functions, 34 enumerated documents, 6 collected artifacts, the 60 second clock, and 28
  rows splitting the sealed model into one row per rule it applies with its line range - plus 29
  readings, 4 shortcuts and the one limit. No row was left NOT STATED. Three rows grade the sealed
  side rather than the submission (the frozen-truth check, the family-coverage check, the model's
  own block sums) and are cited to the sentences that define the lines and the population they
  stand behind. `python tools/tracecheck.py row-anchor-pass` is clean.
- Identifiability: 29 readings enumerated from the four clusters, the model's prior, the behaviour
  of the shipped pane and both parses of each sentence. Every one is ruled out by a sentence of the
  brief, and every one is separated by at least one enumerated document, measured by
  `python tools/readingcheck.py row-anchor-pass` - no BLIND and no equivalent readings. None
  survives the published evidence, so no discriminating example had to be added beyond the single
  frame the brief prints. On a 54-document generated population the readings move between 1.9% (a
  line falling exactly on the total) and 100% of documents.
- Shortcut strategies scored: the shipped tree unchanged scores 0 and matches 0 of 34 enumerated
  documents; one fixed line for every frame scores 0 and matches 0 of 34; a pane that never
  corrects its offset scores 0 and matches 0 of 34; the frozen answers carried whole scores 0,
  matching all 34 enumerated documents and failing the generated ones, which are drawn from a seed
  the submission never saw.
- Independent implementation behind every tolerance and limit: the only limit is the 60 second wall
  clock on the whole graded set. Two correct implementations written apart from the reference,
  `authoring/row-anchor-pass/variants/ok-block` (blocks of groups, no tree anywhere) and
  `authoring/row-anchor-pass/variants/ok-hybrid` (one tree carrying both group sums, plain arrays
  inside a group), replay the 34 enumerated and 85 generated documents, including all six scale
  documents, in 3.9 s and 2.6 s. The reference takes 0.40 s on a wide document and 0.21 s on a deep
  one, 0.7% and 0.3% of the limit. The other side is `authoring/row-anchor-pass/naive/geom.py`,
  exactly correct and 325.4 s and 67.4 s on the same two documents.
- Undecided decisions from the cold-reader pass: author-run, mechanically, over every printed
  field, and again over the whole brief once the tree was built. It found eight decisions the
  drafts left open, each now settled by a sentence: which
  edge of the visible test is strict (now two explicit inequalities); whether a header standing
  exactly at the offset has pinned (now "at or before the offset"); the sign of the gap (now "the
  top of that item less the line. It is zero or negative"); which pass the reported band and window
  come from (now "both as the last pass worked them out"); whether the hold is printed on a frame
  that followed the foot (now stated explicitly); and whether a measured row that was later deleted
  still counts in the closing total (now "whether or not it is still in the document"); the offset
  a run begins at (now "The pane starts at offset 0."); and which bounds the real-height formula
  reads (now "over the bounds its group declares"). No fresh-session form was run, and the reading
  separations stand in its place.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. It does not change without the contributor's explicit approval.

- Artifacts the agent produces: `/app/pane/geom.py`, `/app/pane/band.py`, `/app/pane/win.py`,
  `/app/pane/hold.py`, `/app/pane/move.py`, `/app/pane/frame.py`. Nothing else is collected; the
  rest of the tree is replaced by the verifier's pristine copy before a program runs, including a
  new file placed beside those six.
- What is checked: the full printed trace of every graded event file, compared line for line.
  Each frame line is `f <i> s <S> g <gid> b <B> w <first> <last> h <key> <gap> m <k> p <n>` and the
  closing line is `end s <S> t <total> m <k>`.
- Tolerances: none. Exact string equality over the whole trace, all or nothing, plus the 60 second
  wall clock on the worker that runs every graded program.
- Ground truth, and where it lives: 32 hand programs frozen in `tests/seal/gt.json`; generated
  programs checked against `tests/seal/model.py`, an independently written implementation. Both
  live in `/tests/seal`, mode 700 and root owned, so the unprivileged worker cannot read them.

### The frozen semantics

A document is one or more groups in flow order. A group carries an id, a header height, a per-row
estimate and the bounds its rows' real heights are drawn from. The flow is, group by group, the
group's header followed by its rows. A header's height is its declared height. A row's height is
its real height once the row has been measured and its group's estimate before that. A row's real
height is `lo + (rid * 2654435761) % (hi - lo + 1)`, where `rid` is the row's id. Row ids are
handed out from zero in the order rows are created: every row of the document lines in order, then
the rows created by each insert as it is replayed.

`top(i)` is the sum of the heights of the items before `i`; `total` is the sum of all of them. The
offset always lies in `[0, foot]` where `foot = max(0, total - V)`.

The sticky group is the last group whose header top is at or below the offset. Let `nxt` be the
top of the next group's header, or `total` when the sticky group is the last. The band height is
`min(hh, nxt - offset)`. The anchor line is at `offset + band`.

An item is visible when `top < offset + V` and `top + height > offset`. The window runs from `K`
items before the first visible item to `K` items after the last, clamped to the flow.

The held item is the one whose span contains the anchor line, and the last item when the line
falls on `total`. The gap is `top(held) - line`, so it is zero or negative.

A frame runs in this order.

1. Movement. `scroll d` adds `d` to the offset; `go p` sets it to `p`; `size v` sets the viewport
   height; an insert or a delete moves nothing. The offset is then clamped.
2. The foot flag is read: true when the offset now equals `foot`.
3. The hold is taken: band, line, held item and gap, from the geometry as it now stands.
4. The edit is applied. When the held item is removed, the hold becomes the first surviving item
   after it in the order before the edit, or the last surviving item before it when none follows,
   and the gap moves by the difference of the two tops as they stood before the edit.
5. The frame settles, at most `P` passes. Each pass computes the band and the window from the
   current offset, measures every unmeasured row in the window, then sets the offset: to
   `max(0, total - V)` when the foot flag is set, otherwise to `top(held) - gap - band` clamped,
   where `band` is the one this pass computed. The frame is settled when a pass measured nothing
   and left the offset where it was.
6. The line is printed. The offset is the one the frame ended at; the group, band and window are
   the last pass's; the held item and gap are the ones taken in step 3 and carried through step 4;
   `m` counts the rows this frame measured; `p` counts the passes run.

### Where the facts live (Prong B)

- `pane/geom.py` - flow indexing, item tops, the total, and the search from an offset to an item.
- `pane/band.py` - the sticky group and the band height with its push-off.
- `pane/win.py` - the visible test, the overscan on both sides and the measuring sweep.
- `pane/hold.py` - the held item, the gap and the tracking of both across an edit.
- `pane/move.py` - the movement step, the clamp and the foot flag.
- `pane/frame.py` - the settle loop, its stop condition and the reported line.
- Frozen: `pane/spec.py` (grammar), `pane/src.py` (document, row ids, real heights, raw edits),
  `pane/say.py` (the line format), `run_pane.py` (the driver).

## Stage 7 re-attack (D7), 2026-09-22

Read cold, with the built tree in front of me, the honest answer is that the plan is *stated* and
the structure is not. Every rule is in the brief, so a careful reader does not have to discover
anything; what they have to do is hold nine rules that change each other's meaning while replacing
the structure the shipped pane is built on. That is the shape `expert-defer-shed` and
`slab-fold-scope` ship, and it is what the brief says in its own words.

Where a strong agent still slips, measured against the wrong-reading population:

- it implements its prior instead of the sentence. "Puts the offset at the top of the held item,
  less the gap, less the band that pass worked out" and "correct the offset by the height delta
  above the anchor" agree on most frames, so the prior survives a read-through and fails on the
  frames where an edit or the band moved.
- it recomputes the band after the measuring rather than using the one the pass rendered with
  (19 of 72 generated documents move).
- it reports a band and window worked out after the offset settled rather than the last pass's
  (13 of 72).
- it takes the hold after the edit, or carries the gap with post-edit tops (25 and 7 of 72).
- it decides the foot once per frame rather than once per pass (42 of 72).
- it lays out once (68 of 72).

All-or-nothing over 355 documents means one slip anywhere is a zero, and the only local feedback is
the single frame the brief prints, which settles 7 of the 29 wrong readings and none of the
load-bearing ones.

Is the first plan still wrong? Yes - the retrieved and remembered plan is the delta correction in
one pass, and it is wrong at the anchor, at the correction, at the driver, at the edit path and at
the foot. Are the load-bearing facts still distributed? This task claims B2, not B1: the tree is
370 lines across ten files and an agent reads all of it, exactly as `focus-return-point` does. The
difficulty is the conjunction and the structural rebuild, and the metadata says so rather than
claiming difficulty from file count. Did the instruction come to telegraph the method? It states
what each printed number must be and never how to hold the flow, when to re-solve or what to cache;
the scale sentence names the limit and the input size, which is required, and not the invariant the
fast path follows from.

Estimated solves, updated: 2 of 8. Unchanged from the design estimate. The residual risk I would
flag to a reviewer is the zero-solve side rather than the too-easy side: ten graded decisions under
exact grading is a conjunction, and the arithmetic in `docs/DIFFICULTY.md` says a true 1-in-8
returns zero about a third of the time. Against that, the expert path is concrete, the reference
passes every run, and two independently written correct panes also score 1, so the task is solvable
by a route a real engineer takes.

## Decisions and their reasons

- The line format lives in the frozen `say.py` so that a formatting slip cannot fail a program for
  a reason that is not the task; every value on the line is still graded.
- The document always has at least one group, so the flow is never empty and there is always a
  sticky group and a held item. That removes a whole class of corner cases the contract would
  otherwise have to settle without adding difficulty.
- Real heights come from a stated arithmetic function of the row id rather than from the file, so
  a sixty-thousand-row document is a few hundred bytes and the agent can hold the whole document
  in its head. The heights are not the secret; which rows have been measured is.
- The band uses the push-off against the next header because it is what makes the band height vary
  with a measurement inside the current group, which is the coupling the second discovery rests on.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | NOT RUN | the egress policy denies Docker Hub's blob CDN (`production.cloudfront.docker.com` answers 403 to CONNECT), so no base image can be pulled and neither image can be built here |
| `tools/imagecheck.py` (what the image would hold) | pass | interprets the COPY lines against the build context, drops the reference in and replays all four shipped documents: 15 files, workdir /app, no finding |
| No answer leaked into agent image | pass | `extraneouscheck` clean; nothing from `tests/` or `solution/` is copied; the only correct output anywhere the agent can reach is the one frame quoted in the brief |
| `harbor run -a oracle` = 1 | stood in for | harbor is not installed and Docker cannot pull; `authoring/row-anchor-pass/host_trial.py` runs `tests/test.sh` verbatim as root with the real privilege drop: oracle reward=1, 37 passed |
| `harbor run -a nop` = 0 | stood in for | same runner: nop reward=0 (the shipped pane does not finish the scale families inside the 60 s clock, so the worker is killed and the record is lost) |
| Cheats all score 0 | pass | 43/43 trials behaved: oracle 1, nop 0, and every one of the 41 cheats 0, through `host_trial.py --all` on 2026-09-22 |
| Correct variants score 1 | pass | 2/2: `ok-block` (blocks of groups, no tree) and `ok-hybrid` (one tree over both group sums, plain arrays inside a group) each scored 1 |
| `cheat_report.py` (which case catches which cheat) | pass | 0 findings: every semantic cheat is failed by the enumerated document named for it |
| `readingcheck.py` | pass | 29 readings, all separated by the enumerated set, none BLIND or equivalent |
| `onelinecheck.py` | pass | 1 of 5 graded decisions has an exact rule at depth <= 2 (the settle stop, `got == moved and got == 0`), and two cheats cover it; the other four have none |
| `forgecheck.py` | pass | `cheat-forge-hand.sh` carries the frozen answers verbatim and scores 0 |
| `tracecheck.py` (every graded assertion traced) | pass | clean |
| `difficultycheck.py` on the built tree | pass | 100/100, in band; 370 environment lines, 6 editable files, 386 reference lines |
| `preflight.py` | pass | no errors, 24 warnings (method calls the unused-function check cannot see through, as on every retained bundle) |
| `catcheck`, `structcheck`, `deadfieldcheck`, `extraneouscheck`, `solvecheck`, `simcheck` | pass | `simcheck` reports the two Dockerfiles as near-identical to retained bundles, which is shared boilerplate, and says the task grades nothing an earlier one grades |
| `harbor check` rubric | NOT RUN | needs an API key, which this session does not have |

## What the isolation probes reported

Run through `host_trial.py`, which executes `tests/test.sh` verbatim as root, so the privilege
drop, the locked reward channel and the survivor reap are the real ones.

- `probe-privilege` printed `uid=1002 euid=1002` and `Permission denied` for
  `/logs/verifier/reward.txt`, `/tests/test_outputs.py`, `/tests/gen.py` and
  `/logs/verifier/nonce`.
- `probe-answer-key` printed `Permission denied` for `/tests/seal/gt.json` and
  `/tests/seal/model.py`, and `No module named 'model'` for the import.
- `probe-crash-worker` planted an empty record and exited the worker clean at the first document;
  the worker's own exit status was 0 and the reward still came out 0, because the grader derives
  the verdict itself and refused the planted record.
- `probe-plant-report` planted the same record from a double-forked survivor after the run; same
  result.
- `probe-late-reward` slept past the run and could not write the reward at all.
- `probe-malformed` is the reference with a record of the wrong shape: 35 tests failed, 2 passed,
  reward 0. It is built on correct work on purpose, so its 0 can only mean the grader refused the
  record.
- `probe-uncollected-file` is the reference with its driver moved to a seventh file beside the
  six: 36 errors, reward 0, because that file is never collected.
- `probe-disarm-grader` and `probe-shrink-set` could not write `/tests` or the privileged copy of
  the seed and the family size.

A note on the rest: the shipped pane does not finish the scale families inside the 60 second
clock, so probes built on it score 0 for two reasons at once. The two whose defence only shows on
a run that finishes are built on the reference instead, which is what makes their 0 mean
something.

## Open questions and next steps

The bundle is built, validated and packaged. What is not done here, and cannot be:

- no container evidence. The egress policy in this session denies Docker Hub's blob CDN, so
  neither image was built and `tools/docker_trial.py` could not run. Everything above is host
  emulation running the real `tests/test.sh`; `tools/imagecheck.py` covers the part of the image
  build that has bitten this repository before (a COPY source that no longer exists).
- `harbor check` was not run; there is no API key in this session.
- the easiness and difficulty probes are the platform's, and nothing local predicts them. The
  honest estimate is 2 of 8, and the risk I would flag is the zero-solve side.
