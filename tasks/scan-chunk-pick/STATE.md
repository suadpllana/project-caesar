# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Easiness recovery round 3 - rebuilt for chunk sums and facts that act at once; strong local agents solve it 3 of 3, as they solve tasks the platform passed; a smaller-model stand-in for the easiness screen solves the round-2 design and fails this one; external easiness probe pending`

## Assistant's assigned role

You are a storage engineer on a columnar analytics engine: the scan layer that turns a segment
file and a filter into rows, decides which chunks are read off disk at all, and keeps the
per-chunk statistics that decision rests on. You have spent your time on pruning that is wrong
in the cheap direction, on dictionaries that stop being usable halfway through a chunk, and on
filter evaluation orders that are chosen while the scan is already running.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository supplied)

## Task summary

`/app` is the scan layer of a columnar store, cut down to the part that decides which chunks
are consulted and read. A segment file stores each column as a run of immutable chunks that carry
a header (row count, null count, a recorded low and high with an exactness flag) and a payload
that is either plain values or a dictionary with an overflow list, followed by row updates and
deletes made since the chunks were written. A query is a set of conditions plus the columns to
report. `/app/run_scan.py` prints, for each query, every dictionary consult and every chunk read
in the order they happen, then a digest of the surviving rows, then one line per reported column.
The shipped engine is ordinary predicate pushdown with a fixed condition order and merge-on-read
for the changes. The agent repairs six files under `/app/scn/`. (Rebuilt 2026-09-22 in the
easiness recovery below; the first design had no change overlay and no scale gate that bit.)

## Why it is hard

The surviving rows are easy and the read trace is not. A plan that decodes every chunk and
filters produces exactly the right digest, so the natural self-check confirms an engine whose
graded events are wrong from the first step.

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrieved plans are pushdown with a condition order and merge-on-read for a delta store, both of which treat the chunk as the unit of a decision; here a chunk is consulted or read only for live rows it still supplies, which the brief states as a cost rule rather than as a procedure, so its consequences in the filter step and above all in the report pass (header-fixed values, one-entry dictionaries, fully updated chunks) have to be derived; and the loop the brief describes is exactly correct and two orders of magnitude over the limit, while its fast replacement has to accept scores that rise as well as fall.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C3, C4 - the shipped engine is the memorised pushdown and merge-on-read plan (A1), no sentence names a delta store, delete vectors, zone maps, late materialization or adaptive reordering, and no sentence sequences the steps of the report pass (A2), an exact consult-and-read trace plus a wall clock forbid both the merge-on-read plan and the rescan loop (A3), the overlay, the reads, the exact counts, the order and the report form one chain (B2), updated rows that must still be read for the rest and chunks that must be skipped are both graded (C1), the only self-check is the surviving-row digest which the wrong plans also get right (C2), the wide shape makes the rescan loop 506 s per file against 1.3 s (C3), and every printed event of every query is compared over 47 hand files and 314 drawn after the agent is gone (C4).
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan would transcribe the per-pair procedure, merge the updates at read time and rescan the pairs; it is wrong at the report pass, where the cost rule skips chunks I would read, wrong at the filter step for chunks whose remaining rows all carry updates, and too slow at the loop, and the fast loop I would write first, a heap, is wrong again unless it re-validates a key after a read raises it.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 7 out of 8 (the honest reading of three local strong agents solving the round-3 design 3 of 3; aimed at 1 to 3 and not reached).
- Difficulty record score (tools/difficultycheck.py on authoring/scan-chunk-pick/difficulty.toml):
  100/100 for the first design, which the probe then solved 3 of 3 - the checker measures how
  well a design is articulated, not whether it is hard, and this is recorded as evidence of
  that. 100/100 again for the rebuilt design, measured against the built tree (405 environment
  lines, 6 editable files, 406 reference lines, 55 cheats, 2 variants).
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set -
  no submission of this task has been scored by the pipeline yet.
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22, 100, first
  record; 2026-09-22, easiness probe 3 of 3; 2026-09-22, 100, rebuilt record after the recovery.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing":
  - the read order: nothing in the tree records a decode order, an estimate or a survivor count;
    the file stores values, null counts, recorded bounds, an exactness flag, dictionary entries
    and an overflow list, and nothing else.
  - the header rules: the shipped engine calls every function it defines and defines none the
    wrong policy does not need, so there is no unused widener and no unused completeness test.
  - the answers: no expected trace, checksum or annotation ships beside the sample segments;
    the driver prints and nothing judges.
  - the scale boundary: the two large segments are inputs of the same grammar as the small ones
    and carry no marking that says which recomputation they are aimed at.
- Expert path, described step by step: run the shipped engine and see that it merges updates at
  read time and lets a header verdict take the whole chunk; split a chunk's live rows into those
  with an update in the column and those the chunk still supplies, test the first on their own
  values and put only the second to the header, a read already made, the dictionary and a read;
  work the same cost rule through the report pass (a read already made, a header that fixes every
  value, a one-entry dictionary with no nulls for its charge, a read); start the survivors without
  deleted rows; settle the carried header, dictionary and interpolation rules; time the wide
  shape, replace the rescan loop with a heap keyed exactly as the order, re-push every pending
  pair of each chunk whose count moved or that was read, and validate a popped key against the
  current score.
- Originality check: searched 2026-09-22 for public write-ups of adaptive per-chunk predicate
  ordering with dictionary pruning and inexact statistics, and for a benchmark task of this
  shape. The concepts are all documented - Parquet and DataFusion on zone maps and predicate
  pushdown, the column-store papers on late materialization, patents on compressed-block
  pruning - and no page describes this policy: re-choosing after every chunk, estimating a
  decoded chunk by exact counts, rounding recorded bounds inward, or charging a dictionary once
  per chunk. No public exercise, repository or write-up of the task was found.

## Easiness recovery, 2026-09-22 (probe: 3 of 3 solved)

Status: recovery active. The task is not submission-ready until a new external easiness probe
passes (`RAISE-DIFFICULTY.md`, exit gate).

### 1. The failure, captured

- Result: the easiness probe solved it 3 of 3.
- Trajectories: `probes/scan-chunk-pick/trial{1,2,3}-raw.txt` as supplied, and
  `trial{1,2,3}-own-words.md` with the pasted brief stripped so `leakcheck` does not grade the
  brief against itself. The transcripts carry no verdicts beyond "solved".
- Shape of every run: 5 to 7 steps, 3 to 5 tool calls. One `cat` of the whole tree (368 lines),
  then a single Bash call that rewrote all six files, then the tiny file, then timing. No wrong
  intermediate version, no harness, no fuzzing.
- First plan, decisive discovery and final method were the same thing in all three: diff each
  paragraph of the brief against the module it describes. Trial 3's own summary lists the fixes
  one per file (`w` widening, null keep, `*` dictionaries, the static order, the O(n) count,
  the report pass), in the brief's paragraph order.
- Earliest commit point: after the first read. The plan existed before a single program ran.
- Where the plan came from: the brief. Every graded decision had a paragraph that stated the
  procedure (the pending pair, the score, the cap, what a read settles, the report pass), and
  each shipped module was wrong exactly where its paragraph said otherwise. `leakcheck` finds
  the brief's wording in two of three write-ups ("expected to leave the fewest rows alive", "a
  chunk holding any null is", "a chunk with no live rows counts"); the third is too terse to
  quote anything, which is itself the mode-C signature of a one-shot write.
- The scale gate never bit. Trials measured 0.53 to 0.82 s on wide.txt and 0.24 to 0.28 s on
  deep.txt against 60 s for the whole set; all three kept the loop as a full rescan of every
  pending pair after every step and still passed. The measured naive family (a row-id set
  walked per score) was a representation no agent chose.
- Tactics claimed and which failed in practice: A1/A2 failed because the brief stated the
  replacement policy procedurally; B2 failed because the rules were confirmable one paragraph
  at a time against one module each; C3 failed because it gated a representation nobody used;
  C2 held (no oracle) and did not matter, since transcription needs none.
- Estimated solves before: 2 of 8. Realized: 3 of 3. The estimate was wrong because it
  assumed the loop rewrite and "a read settles every condition" were plan-level discoveries;
  both were sentences.

### 2. Classification

| Failure mode | Evidence | Direction taken |
|---|---|---|
| The instruction delivered the plan | seven procedural paragraphs, one per module; leakcheck hits | state what the engine may know and when it may pay for a read, and let the procedure follow |
| The agent confirmed each step independently | each module's fix is readable off one paragraph | make the consequences of one principle land in four modules at once |
| The naive method was fast enough | rescan loop at 0.8 s against 60 s | a measured boundary on the loop itself, with a fast path whose keys move both ways |

### 3. Candidates

1. **Only restate the brief** (mode-A repair alone). Cheapest, and the measured effect on
   `share-register-screen`. Rejected as the whole repair: here nearly every sentence is a graded
   rule, so deleting sentences deletes contract. Kept as one part.
2. **A row-level update and delete overlay, with a parsimony principle.** A columnar store's
   chunks are immutable; changes sit beside them. A row's value comes from its update when it
   has one, a deleted row is never alive, and a chunk's header, dictionary and exact counts all
   describe the chunk as written. Stated as one principle - a chunk is consulted or read only
   when a row still alive takes its value in that column from it and nothing cheaper (its
   header, its dictionary, a read already made) can supply what is needed - it changes four
   modules at once: a header or dictionary verdict settles only the rows that still take their
   value from the chunk, a condition whose remaining rows all carry updates reads nothing, the
   report pass skips chunks whose survivors are all updated or whose header or one-entry
   dictionary already fixes every value, and the survivors start without the deleted rows.
   Attack: an agent that transcribes "header, then dictionary, then read" reads chunks nobody
   needs; one that overlays updates at decode time (the textbook merge-on-read) gets every
   surviving row right and the trace wrong. The first plan is reasonable; the principle
   invalidates the chunk as the unit of a decision.
3. **A measured scale boundary on the choice loop.** Chunks of twenty to sixty rows put about
   a thousand chunks in each column of the wide shape, so a full rescan of the pending pairs
   after every step is tens of seconds per query while exactly correct. The fast path is an
   incremental priority structure, and it has a boundary: a pair's score falls when rows die in
   any column whose partition overlaps it and rises when a read replaces a low interpolation
   with a higher exact count, so a structure that only ever lowers keys, or trusts a key it
   pushed before the read, picks the wrong pair.

Selected: 2 and 3 together, plus 1 applied to the brief as a whole. Prongs: A1 (merge-on-read
and "decide the chunk" are the priors, and both are wrong here), A2 (no term of art: delta
store, delete vector, late materialization are never named), B2 with real interaction (an
update changes whether a read happens, which changes which exact counts exist, which changes
the order, which changes what the report pass still has to read), C3 (measured below), C1/C4
unchanged in shape with new shaped families. The old winning plan is kept as a named cheat.

Honest attack on the repaired plan, as the probe agent: I would read the principle, implement
header/dictionary/read per pair with updates merged into the decoded values, and write a
rescan loop; the tiny example passes. Timing the wide file tells me the loop is too slow and I
reach for a heap; whether I remember that a read can raise a key depends on whether I think
about it. Whether I skip the read for a condition whose alive rows all carry updates, and skip
the report read for a pinned header or a one-entry dictionary, depends on whether I derive the
principle's consequences rather than matching paragraphs to modules - and there are no longer
paragraphs to match. I can see where to start; I would not commit to the full plan without
working through the principle, and my first plan would be wrong in the report pass.

Estimated solves after the repair: 3 of 8 (aimed at 1 to 3).

### 4. The rebuild, stage by stage

- Stage 2: the contract above, revised. The 31 old hand answers were re-derived under the new
  model and came out byte-identical; 16 hand files were added, one per new decision.
- Stage 3: the frozen parser learned `up C r v` and `del r` (`seg.up`, one dict per column;
  `seg.gone`). The shipped engine was given the textbook handling of them - updates laid over a
  chunk's values when it is read, deleted rows removed from the survivors - so the tree holds
  the merge-on-read plan coherently and a header verdict still takes the whole chunk. Its output
  on `tiny.txt` is still exactly the three wrong lines the brief quotes. `pair.txt` gained four
  updates and two deletes; `wide.txt` and `deep.txt` were regenerated at the new shapes.
  Environment: 405 Python lines over 11 modules, six editable and all six shipping wrong.
- Stage 4: the reference (`solution/`, 406 lines with `solve.sh`): `live.split` separates the
  rows a chunk still supplies from those carrying an update; `step.decide` asks the header, a
  read already made, the dictionary and a read only for the former; `proj` serves each wanted
  chunk by a read already made, a pinned header (`hdr.pinned`), a one-entry dictionary
  (`dct.single`, charged) or a read; `pick` is a heap keyed (score, condition position, chunk)
  with every pending pair of a dirty chunk re-pushed after each step and a popped key trusted
  only while it equals the current score.
- Sealed model (`tests/seal/model.py`), rewritten apart from the reference: one module, the
  pending pairs in a segment tree of exact minima laid out in tie-break order, every row resolved
  against the update map on its own. Reference and model agree on all 47 hand files and on 1,254
  generated files over three seeds, including six wide and six deep.
- Generator: 14 small families (three new: `moved`, `pinned`, `gone`, plus `rise`) and the two
  scale shapes; 22 files per small family, 361 graded files in all.
- Stage 5: the brief was rewritten to state what a header and a dictionary can prove and what a
  consult and a read cost, instead of one procedural paragraph per module; the report pass has
  no enumerated steps, only the cost rule and what "fixes them" means. The one sentence
  `leakcheck` still finds in a probe write-up is the order rule, which is graded and has to be
  stated; it is kept, not reworded to quiet the checker.
- Stage 6: 38 readings, all separated by a named hand file (`readingcheck` exit 0, none
  equivalent to the reference); 55 cheats; `cheat_report.py` names the catching case for every
  semantic one. The old probe-winning solution (the previous reference, which all three agents'
  submissions matched) is kept at `authoring/scan-chunk-pick/probe_winner/` and ships as
  `cheat-chunk-is-unit.sh`: it fails 12 of 47 hand files and 263 of 308 small generated files,
  and its rescan loop cannot finish the wide shape inside the clock.

### 5. Measurements before the next probe

| What | Measured |
|---|---|
| reference, whole graded set (361 files, host) | 4.9 s |
| ok-slice / ok-tree, whole graded set (host) | 5.4 s / 8.0 s |
| reference, one wide file | 1.2 to 1.3 s over three seeds |
| rescan loop (reference estimate function), one wide file | 506 s |
| rescan loop with header estimates cached in lists, one wide file | 99.6 s and 99.9 s on two seeds |
| shipped tree on the graded set | 17 of 47 hand files, 0 of 308 small generated |
| positional shortcut (conditions in query order) | 42 of 47 hand files (single-condition files), 13 of 308 generated: reward 0 |
| constant output, replayed example | 0 of 47, 0 of 308 |
| forgery of the frozen answers | 47 of 47 hand, 0 of 308 generated |
| `onelinecheck` | no graded decision has an exact rule at depth 2 (before: the report pass did) |
| `difficultycheck` | 100 (the first design also scored 100 and was solved 3 of 3) |
| `originalitycheck` | 97, floor 90 |

## Easiness recovery, round 2, 2026-09-23 (probe: 2 of 3 solved)

Status: recovery active. The first repair moved the probe from 3 of 3 to 2 of 3; the exit gate
needs at most 1 of 3, so this is a second repair, not a pass.

### 1. The failure, captured

- Trajectories: `probes/scan-chunk-pick/round2/trial{1,2,3}-raw.txt` as supplied, and
  `trial{1,2,3}-own-words.md` with the brief stripped. The supplied files carry no verdicts;
  which trial failed is not recorded in them.
- Shapes: trial 1, 5 tool calls - read the tree, one Bash call rewriting all six files with a
  heap, hand-traced `pair.txt`. Trial 2, 14 calls - rewrote all six files, then wrote "an
  independent, spec-literal reference" and a random generator in `/tmp`, fuzzed 700 small files
  and six 2000-row wide-shaped files against it, all equal. Trial 3, 7 calls - rewrote all six,
  hand-traced `pair.txt`, checked `sel` and `prj` on the four shipped files with a brute force.
- Every fragment of output the three printed on the shipped files matches the reference (trial
  1's `sel`/`prj` lines on wide and deep, trial 2's first 40 lines of wide and deep, trial 3's
  first nine `rd` lines of wide). The failing trial therefore slipped on a corner only the graded
  set exercises; the transcripts do not show which one. Trial 1, the one that neither fuzzed nor
  brute-forced, is the likeliest.
- First plan, decisive discovery, final method: the same for all three again - read the brief
  once and derive the whole engine. All three planned the heap before timing anything ("with a
  heap-based scheduler for the pending pairs", trial 1's first sentence after reading), and all
  three derived the report pass's cost-rule consequences on first read (trial 3: "Added header
  value-fixing for projection (all null, or no nulls with equal bounds)"; trial 1: "ignored the
  header and dictionary as cheaper sources of values").
- Where the plan came from: the brief, but no longer its wording - `leakcheck` finds one phrase
  in one write-up. The dominant mode is C, the specification checked against itself: trial 2's
  spec-literal reference plus fuzzing, trial 3's brute force. A self-built brute force catches
  implementation slips and cannot catch a misreading, because it is built from the same reading.
- What failed in practice: stating rules as a cost principle hid nothing (A2 did not bite); the
  scale gate was planned around on first read (C3 gave no late discovery); the overlay rules were
  individually derivable and confirmable against a brute force.

### 2. Classification

| Failure mode | Evidence | Direction taken |
|---|---|---|
| C: the specification checked against itself | trial 2's spec-literal reference and fuzz; trial 3's brute force | put the difficulty in how the state is owned and composed, where a misreading is shared by the brute force |
| The default plan was correct | all three wrote the whole engine on first read | make the chunk, which every agent took as the unit, stop being the unit of reading, counting and trusting |
| The instruction delivered the plan | only one leaked phrase | kept the principle-style statements; no new step lists |

### 3. Candidates

1. More overlay rules (snapshot visibility, commit order). Rejected: each is a local rule a
   brute force confirms.
2. Disjunctions across columns. Rejected: a decision unit of row fragments across misaligned
   partitions is deep, but the order and cost rules for it cannot be stated in the length the
   brief has left without becoming a procedure again.
3. **Pages inside chunks, with page headers and sums, a dictionary that covers only the pages
   written against it, and partial reads**, plus **one memory per file** so a later query builds
   on what earlier ones paid for. Selected. Both are how real column stores behave (a page index
   with a dictionary that falls back part-way through a column chunk; a scan session that keeps
   what it has read), and together they take apart the one structure all three agents relied on:
   a chunk is no longer read, counted or trusted whole, and a query no longer owns its state.
   Consequences a solver has to derive and a brute force built from a misreading shares: a
   chunk's count is exact on the pages read and a spread on the rest; the dictionary's verdict
   applies to index pages only, and "every entry passes" still reads a page holding a null; a
   later query counts remembered pages exactly from its start, which reorders what it pays for;
   pages the report pass read serve the next query; and the report answers a page from its
   header's sum only while the rows it wants are every row of the page, which a delete, an
   update or a death in another column quietly breaks.

### 4. The rebuild

- Grammar: `ch C p` / `ch C d m entries` opens a chunk; `pg n u mn mx x s f tokens` lines are its
  pages (`f` is `v` or `i`); `up`, `del`, `qry`/`prd`/`prj`/`end` unchanged. `dc` prints three
  numbers (column, chunk, page). The driver calls `live.fresh(seg)` once per file and passes the
  memory to `live.start(seg, q, mem)`.
- Shipped engine: the chunk-as-unit plan, coherently - page headers merged into chunk statistics,
  a chunk read whole, the dictionary trusted for a whole `d` chunk and charged per consult,
  updates merged at read time, every query starting from nothing, a fixed condition order, a
  report that reads every chunk in index order. On `tiny.txt` it prints exactly the three wrong
  lines the brief quotes.
- Reference (`solution/`), sealed model (rewritten apart: segment tree, counts summed afresh from
  pages), generator (14 small families reshaped for pages, fallback pages and multi-query files,
  plus the two scale shapes), 60 hand files (the 47 earlier ones converted - each old chunk one
  page, a literal-token chunk a dictionary chunk whose page fell back - plus 13 new), 49 readings
  all separated by a named hand file (`readingcheck` exit 0), 66 cheats, two correct variants.
- The earlier answers moved, as a contract change must: 44 of the 47 converted files gained the
  page number in `dc`, and 13 changed further, every one explained by the two new rules (a whole
  report page answered by its sum instead of a read, and a second query not re-reading or
  re-charging).

### 5. Measurements

| What | Measured |
|---|---|
| reference vs model | agree on 60 hand files and 948 generated files over four seeds (924 small, twelve wide, twelve deep) |
| reference, whole graded set (374 files, host) | 7.6 s |
| ok-slice / ok-tree, whole graded set (host) | 10.0 s / 12.3 s |
| reference, one wide file | 2.1 to 2.3 s |
| rescan loop, one wide file | 142.5 s |
| previous design (`cheat-chunk-is-unit`) | 34 of 60 hand, 7 of 308 small generated: reward 0 |
| shipped tree | 9 of 60 hand, 0 of 308 small generated |
| readings moving the most small generated files | no memory 70.7%, report reads not remembered 51.4%, dictionary for all-index chunks only 42.9%, no page sums 26.1%, charges reset per query 25.7% |
| `onelinecheck` | no graded decision has an exact rule at depth 2 |

Estimated solves after this repair: 2 of 8, easiness probe 0 or 1 of 3. The risk on the other
side is real and recorded: the engine is now larger and every rule is stated once; a fresh-session
cold read is run below before anything ships.

## Easiness recovery, round 3, 2026-09-23 (local calibration: 3 of 3 solved)

Status: recovery active. The round-2 rebuild was not sent to the external probe. Three local
agents were run on it first, and all three solved it, so it went back to the design stage.

### 1. The failure, captured

- Probes: three fresh local agents, each given only the brief (paths rewritten to a scratch copy
  of `app_src/`) and that tree. No verifier, no reference, no model. Afterwards each agent's six
  files were graded the way the worker and grader do: the 60 hand files against `gt.json` and
  the 314 generated files of a fresh seed against the sealed model.
- Result: 3 of 3 pass, every file right, 4.4 s for the whole set for the slowest. Wall time
  was 16 to 25 minutes each against a 14400 s budget.
- Shape, the same in all three: read the tree, write a model straight from the brief, rewrite
  the six files around a heap, generate random segment files and diff the engine against the
  model (the third ran about 33,000 files, some shaped like wide and deep), hand-trace
  `pair.txt`. One ran a mutation check against its own model as well.
- First plan, decisive discovery and final method were one and the same. The earliest commit
  point was the first read of the brief.
- Where the plan came from: the brief. Every rule of round 2 is stated as a rule. The report's
  answers are listed one by one, and so is the order within a page. Memory, counts and order
  are stated too. A model built by transcription is right, so fuzzing against it confirms the
  engine rule by rule. This is mode C with nothing standing in its way.
- Tactics that failed in practice: A2 (principle before procedure), because the brief printed
  the procedure beside the principle; B2, because every rule could be confirmed against a model
  the agent wrote itself; C3, because the heap was planned on first read again.
- Estimated solves before: 2 of 8. Realized locally: 3 of 3, in under half an hour each.

### 2. Classification

| Failure mode | Evidence | Direction taken |
|---|---|---|
| C: the specification checked against itself | all three: literal model plus fuzzing | put a load-bearing decision where the brief states facts and a limit on reads, so which reads are owed must be derived; a self-built model is then only as right as the derivation |
| The instruction delivered the plan | the report's answers listed one by one; the per-page order spelled out | state what is known and when a read is owed; list no answers |
| The default plan was correct | every first engine settled only the condition being applied | what is known acts at once, on every condition |

### 3. Candidates

1. A page header settles what all three of its facts prove, so its sum narrows its bounds.
   Rejected as the main lever. Under an exact header the recorded low and high are attained,
   so the sum can never narrow them; it bites only on widened pages with few values.
2. Many queries per file, with the clock on the per-query loop. Rejected: the fast path is
   engineering (batching deaths, skipping loops with nothing to pay for), not an invariant, and
   a tuned heap gets close enough to squeeze under.
3. **Sums move from pages to chunks, and the report reads a page only when its line cannot be
   told without it**, plus **what is known acts at once**. Selected. A page no longer says what
   it sums to; its chunk does. The report owes a read of a page some of whose live rows it
   needs, but pages whose rows are all live need no read when every other page of the chunk
   has a known sum, because the chunk's sum less those gives theirs together. One page whose
   rows are all dead and whose sum is unknown blocks that, and then every such page must be
   read, since a page with no live row can never be read. Which pages are dead and unknown is
   decided by the filter: a page killed whole by its header stays unknown, and a page read
   before its rows died does not. So the filter's reads, the dictionary's pinning of a
   one-entry chunk and the file's memory all feed the report, and the first plan (answer each
   page on its own, the way every agent did) reads pages the chunk sum answers and skips none
   of the ones it must. A one-entry dictionary, consulted when that spares a read, tells the sum
   of every index page of its chunk, dead or alive, so a consult for one page can unblock
   another. In the filter, a row dies the moment what is known shows it fails any condition:
   headers, updated values, remembered pages and consulted dictionaries act on every condition
   at the query's start and after every consult and read, which retires the per-condition
   settlement every agent wrote first.

### 4. The rebuild

- Grammar: a chunk line carries its sum, `ch C p s` and `ch C d s m e1 ... em`; a page line no
  longer does, `pg n u mn mx x f ...`. Everything else as before. The frozen parser moved the
  field; the shipped engine never used a page sum, so it runs unchanged and prints the same
  three wrong lines on `tiny.txt`.
- Filter: a row dies the moment what is known shows it fails a condition. What is known of a
  row's value is its update, its page's header, its page's values once read and, for an `i`
  page, its chunk's dictionary once consulted. So at a query's start every condition is put to
  all of those, and after every consult and every read what was learned is put to every
  condition over the column at once. A pair is pending while a live row takes its value from one
  of its chunk's pages without the condition settled; applying it takes those pages in order,
  the dictionary first for a comparison on an `i` page not yet consulted, then a read.
- Report: a page is read only for rows it supplies and only when the line could not be worked
  out without it even if every other page it could read were read. What works it out: pages
  read, all-null pages, one-value pages (their sum is known whatever their nulls), a known
  one-entry dictionary, null counts and chunk sums. So the wholly live pages of a chunk are told
  together by the chunk's sum, unless a dead page has an unknown sum, which blocks the split and
  sends them all to a read. A one-entry dictionary is consulted before its chunk's reads when one
  of its `i` pages supplies a row and knowing it spares a read. Reads in chunk and page order.
- Reference, sealed model (rewritten apart: each row's fate asked afresh, segment tree, the
  report's reads found by a literal per-page necessity test), two correct variants (settlement
  per row, stamped heap / segment tree), generator (a seventeenth family, `block`: a banded
  column whose range conditions kill some pages of the reported columns whole and keep others
  whole; constant pages holding nulls inside mixed chunks), shipped samples regenerated.
- Hand set: the 60 files converted mechanically (page sums moved onto their chunks; five inherited
  exact headers whose recorded pair was wider than the values tightened, with no answer and no
  separation changing), `prj-whole-page-sum` renamed `prj-dead-page-blocks-sum` because under the
  new rules it pins blocking, and 22 new files: 5 `flt-`, 10 `prj-`, 2 `ord-`, 2 `upd-`, 1 `dec-`,
  1 `mem-` and 1 for the one-entry consult needing a live row. Every hand file passes
  `authoring/scan-chunk-pick/segcheck.py` (sums, null counts, recorded pairs and indexes are what
  the values give); writing it caught two chunk sums I had typed wrong.
- Readings: 61, rewritten against the new reference, plus the round-2 design kept as
  `previous()` in the new grammar (`authoring/scan-chunk-pick/v3/`). `hunt.py` searches a tiny
  space for the smallest file separating a reading and shrinks it; the reducer no longer drops a
  query's only condition.

### 5. Measurements

| What | Measured |
|---|---|
| reference vs model | agree on 82 hand files and 1,908 generated files of the final generator over four seeds (1,890 small, nine wide, nine deep) |
| reference, ok-slice, ok-tree, whole 418-file graded set, 1 CPU and 2 GB container | 7.1 s, 9.7 s, 9.7 s |
| rescan loop, one wide file (host) | 139.6 s, identical trace, against 1.6 s for the reference |
| readings moving the most small generated files | free facts late 43%, header late 19%, memory late 15%, no chunk sum 33%, last page only 14%, dead pages ignored 12%, consult always 18% |
| `readingcheck` | all 61 separated by a named hand file |
| `cheat_report.py` | 78 cheats, 0 without an enumerated case (slow-rescan by clock, probes in containers) |
| previous design (`cheat-previous-design`) | 45 of 82 hand, 117 of 330 small generated: reward 0 |
| shipped tree | 8 of 82 hand, 0 of 330 small generated |
| container oracle | reward 1, 85 tests |

### 6. Local calibration of this rebuild

Three fresh local agents on this design, exactly as before: 3 of 3 pass, graded on the 82 hand
files and 336 generated files of two fresh seeds, 0 wrong. They took about 31 minutes each
against 16 to 25 for the page design. Evidence is in `probes/scan-chunk-pick/round4-local/`.
Same shape as before: engine first, then a slow literal model from the brief (one decided the
report's reads in its model by enumeration), then 10,800 to 30,000 random files through both.
All three named the same readings as the ones they had to choose and chose as the brief says.

What this says: a rule the brief states precisely, as a principle or as a step, is one a strong
agent transcribes into a model and checks its engine against; this design stops the
per-condition, per-page first plan, but it does not stop an agent who writes the model before
the engine. The external easiness screen runs low-effort agents, which in round 2 mostly did
not write a model (one of three fuzzed); the rules they now have to get right unaided are more
and subtler than the ones one of them already missed. The eight-attempt difficulty probe runs
strong agents, and on this evidence it would come back at or near 8 of 8. (Section 7 revises
this: the same agents solve tasks the platform passed about as readily.)

### 7. What the local probes measure

Neither local measurement meant much until it was run on something whose external result is
known, so both were.

Strong agents, the difficulty probe's class. The same prompt, model and effort that solved this
design 3 of 3 were run on two retained tasks the platform passed, two agents each, graded by each
task's own verifier in the container and re-run against fresh nonces
(`probes/scan-chunk-pick/calibration/`): `guard-mark-unwind` 2 of 2, each right on nine runs;
`alias-settle-report` 1 of 2, one right on seven runs and the other wrong on three runs in nine,
having read an equal score the other way. About half an hour each, as here, and the three solves
of this design are right on the 82 hand files and six generated seeds each. So these agents
solve tasks inside the band about three times in four, and 3 of 3 here does not separate this
design from them: section 6's "at or near 8 of 8" was the ceiling of the instrument, not a
measurement of the task.

Smaller agents, a stand-in for the low-effort screen. The same prompt on a smaller model, run on
this design and on the round-2 design the external screen solved 2 of 3
(`probes/scan-chunk-pick/round4-smaller/`, `probes/scan-chunk-pick/round2-smaller/`):

| Design | External screen | Stand-in |
|---|---|---|
| round 2 | 2 of 3 solved | 2 of 2 finished runs solved, each right on five verifier runs (33 and 54 minutes); the third ended on an output-token error before writing code |
| this design | not yet run | 0 of 3 solved, wrong on 19, 17 and 13 of the 82 hand files (53, 66 and 123 minutes; the third is the rerun of a run that ended on an output-token error before writing code) |

The stand-in solves what the screen solved and fails this, on the rules this round added: facts
acting at once, exact counts after a read, the report told by chunk sums, the report's consult.
All three failures checked only the numbers on `sel` and `prj` against a brute force, which cannot
see which pages were read; the round-2 solves had no such rule to miss.

What it says, as far as it goes: the easiness screen is likelier to pass than on any earlier
design, and the difficulty probe is no likelier to come back 8 of 8 than it was for the two
tasks calibrated on. Neither is a pass. The exit gate is still the external probe.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/scan-chunk-pick/trace.md; rows walked, NOT STATED left, tracecheck result): rebuilt for recovery round 3 by `authoring/scan-chunk-pick/make_trace.py`, which asserts every quote is still in instruction.md: 124 graded rows - four test functions, six artifacts, the clock, the overlay, 82 enumerated cases and the sealed model split one rule per row with its line range - plus 61 readings, six shortcuts and the limit. No NOT STATED row. `python tools/tracecheck.py scan-chunk-pick` is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 61 readings written as patches that must fire; none equivalent to the reference; every one separated by a named hand file (`readingcheck` and a direct run over the 82 files). Fourteen were blind to the converted hand set and four were separated by nothing at first (two heap readings, a consult settling only its own page, and a report consult made for a dead page); `authoring/scan-chunk-pick/hunt.py` and two shaped searches found the smallest separating files, which are the new cases. The three local agents independently named the same three decisions as the ones the brief makes them think about - the dictionary's verdict over all its entries, "the live rows that chunk holds" counted with updated rows, and when the report consults - and all three read them as the reference does.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): shipped tree 8 of 82 hand and 0 of 330 small generated files; constant output 0 and 0; conditions in query order 72 of 82 hand (mostly single-condition files) and 11 of 330; worked example replayed 0 and 0; forgery keyed on query history 82 of 82 hand and 0 of 330; the previous design 45 of 82 and 117 of 330. All reward 0.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 60 s clock only. `variants/ok-slice` and `variants/ok-tree`, written apart from the reference, run the whole 418-file set in 9.7 s each in a 1-CPU, 2 GB python:3.12-slim container, against the reference's 7.1 s.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): three fresh local agents read the round-3 brief cold as solvers and reported the decisions they had to choose; none was left open by the text, and all three chose as the reference does. The earlier cold reader's finding (a read of an `i` page does not consult the dictionary) is still stated and still pinned by `pg-read-consults-dict`.

## Verifier contract - FROZEN after Stage 2 (revised in both easiness recoveries)

The contributor asked, after each probe, for the task to be made harder; each request is the
approval for the revision that followed, which changes what "correct" means. Revision two
(2026-09-23): the grammar became chunks of pages (`ch` then `pg` lines, `dc` printing three
numbers), a dictionary speaks only for its `i` pages, pages are read singly, the file keeps one
memory across its queries, and the report pass answers a whole page from its header's sum. The
47 hand files carried over were converted mechanically and their answers re-derived; every
change beyond the page number in `dc` is one of the two new rules at work. Revision three
(2026-09-23, same request): the sum moved from the page line to the chunk line, what is known
acts at once on every condition, and the report reads a page only when its line could not be
worked out without it. Of the 60 hand files, 56 kept their answers byte for byte; the four that
moved are each explained by a new rule, and one was renamed for what it now pins.

- Artifacts the agent produces: the six files `/app/scn/hdr.py`, `/app/scn/dct.py`,
  `/app/scn/pick.py`, `/app/scn/live.py`, `/app/scn/step.py`, `/app/scn/proj.py`. Nothing else
  is collected; the verifier lays them over its own pristine copy of the tree.
- What is checked: the exact list of lines `/app/run_scan.py` prints for a segment file, in
  order. 82 hand-written files against `gt.json`; 336 generated ones (22 of each of 15 small
  families, 3 of each of 2 scale shapes) against the sealed model, which must itself reproduce
  `gt.json` before anything is graded. Every file must match.
- Tolerances: none. The one limit is the 60 s wall clock on the worker, stated in the brief and
  validated against two correct implementations written apart from the reference.
- Ground truth: `tests/seal/model.py` and `tests/seal/gt.json`, in a root-owned `0700` directory.

### The graded decisions, and the sentence each is owed

1. the grammar: chunks and their pages in row order, a chunk's sum on its line, page numbering,
   `i` and `v` pages
2. widened page bounds when the exactness flag is off; no bounds for an all-null page
3. what a page header proves (fails all / holds all) from its null count and bounds
4. a consulted dictionary speaks only for `i` pages and only for comparisons; its two verdicts,
   with a null on the page keeping an all-pass verdict from settling it
5. a row's value is its update if it has one; a deleted row is never alive; a page's header,
   reads, exact counts and its chunk's sum describe it as written
6. what is known of a row's value, and that a row dies the moment it shows a failure - at a
   query's start and after every consult and every read, on every condition
7. the pending pair: a live row supplied by the chunk's pages, unsettled; applying it takes those
   pages in order, the dictionary first for a comparison on an `i` page, however little it
   settles, then a read
8. one memory per file: pages read and dictionaries consulted stay known, print once
9. a page read settles the exact count of every condition over its column on it, as written; a
   page read before a query starts counts exactly from its start; spread otherwise; a chunk's
   count is the sum over its pages
10. the spread formula, its rounding and its endpoints
11. the score (smaller of live rows and count) and the two tie-breaks
12. `sel`: count and digest of live rows
13. the report: named order with repeats; a page read only for rows it supplies and only when
    the line cannot be worked out without it even with every other page it could read read;
    what works it out (pages read, all-null pages, one-value pages, a known one-entry
    dictionary, null counts, chunk sums); the one-entry consult when it spares a read; reads in
    chunk and page order
14. the reported count excludes nulls and the sum adds non-null current values
15. every query starts with every non-deleted row alive
16. the 60 s clock, one Python 3.12 process, standard library only

### Prong C in the contract

- C1: both sides of every skip - pages dropped or kept unread, pages read singly while their
  neighbours are settled free, report pages answered free and pages that must still be read.
- C2: the surviving rows are the only thing an implementation can check against itself, and the
  chunk-as-unit engine produces them correctly while its list of reads is wrong.
- C3: the wide shape, measured - the rescan loop 139.6 s for one file against 1.6 s for the
  reference and 60 s for the whole graded set.
- C4: 82 hand files aimed one per decision, plus 336 generated after the agent's container is
  gone, compared line for line, all or nothing.
- Route-around guard: only the six files are collected.

## Decisions and their reasons

- The exactness flag is not consulted when a low equals a high. It was at first, on the reading
  that `eq v` may only be settled from a single-value pair when the pair is exact - but a widened
  pair always has its low strictly below its high, so the guard was unreachable. `readingcheck`
  reported both readings that rest on it as equivalent to the reference, which is what found it;
  it is gone from the reference and the model rather than kept as dead code.
- The graded segment files are built by `tests/prep.py`, as root, before the clock on the worker
  starts, so the 60 seconds the brief states measures the submitted engine and not the
  verifier's own generation. It also means the seed is never handed to the process that runs the
  submission: the worker is given the built files and nothing else.
- Values are non-negative integers rather than strings, so the inexact-statistics rule can be
  stated as arithmetic on a granularity rather than as byte truncation, and every graded number
  stays exact.
- The surviving rows are reported as a count and a digest rather than as a list, because a wide
  segment would otherwise print forty thousand row ids per query; the digest is computed by the
  frozen trace writer, so the hash is not one of the graded decisions.
- The frozen driver owns nothing but the order of the phases. `live.start`, `pick.run`,
  `live.rows` and `proj.run` are the four names it calls, and the instruction says so, because
  a signature the driver depends on is a graded condition.

- (Recovery) The change overlay is stated as a cost rule and two facts about what a header and a
  dictionary can prove, not as steps. Every graded consequence still traces to a sentence -
  the trace cites the rule plus the definition it acts on - but none of the report pass's three
  skips is spelled out as a case. That is the Prong A repair for a brief that had delivered the
  plan paragraph by paragraph.
- (Recovery) A read's exact counts are taken over the chunk as written, deleted rows and old
  values included, and the header spread likewise ignores updates. The rule is that everything
  a chunk says about itself describes the chunk as written; the estimate is allowed to be wrong,
  and one convention for all three statistics keeps it one sentence.
- (Recovery) The scale gate moved from the survivor representation, which no agent chose, to
  the choice loop, which all three wrote as a rescan. It was measured on both sides before the
  brief stated it: the first reshaping (chunks of 20 to 60 rows) left the cached rescan at 7 to
  18 s per file, close enough to squeeze three files under 60 s, so the wide shape went to
  sixty thousand rows in chunks of ten to twenty-four.

- (Recovery 2) Dictionary fallback is per page and one-way, as a writer does it: a `d` chunk's
  index pages come first and any fallback pages after, and the generator never writes an index
  page after a fallback page. The brief states "pages are taken in order", so the printed order
  inside a pair is fixed either way; with index pages first, a dictionary consult always comes
  before the reads of the same pair, so no reading about "consult first versus page order" is
  graded - they cannot differ on any file this grammar produces from the generator.
- (Recovery 2) The report pass answers a page from its header's sum only when the rows it wants
  are every row of the page. A combined inference - a header bound plus a dictionary's entries
  pinning one value - is deliberately not part of the contract; the brief lists the header's
  three answers and the dictionary's one explicitly rather than leaving "answers" to be derived,
  so there is exactly one reading.
- (Recovery 2) The file's memory is owned by an object the driver makes once per file and hands
  to every `live.start`, not by module state keyed on the segment. Keyed state would work across
  one file and silently break across the 374 files one process runs, which would make the task
  hard for a reason that is not the task.
- (Recovery 2) The forgery cheat keys its answers on the whole query history of a file, not on
  one query, because with a memory the same segment and query can owe different lines after
  different earlier queries; keyed on one query it failed to reproduce a hand file, which would
  have made it a weaker proof than it claims to be.

- (Recovery 3) The chunk's sum is not part of what the filter knows about a row's value; the
  brief lists that knowledge in one sentence and the sum is not in it. With an exact header the
  recorded low and high are attained, so a page's sum can never narrow its bounds; it narrows a
  widened page only, and measured as a rule it moved 1.1% of small generated files and one of six
  large ones. Too thin to carry difficulty, and one more thing to state, so it stays out.
- (Recovery 3) What works out the report's line is a closed list in the brief: pages read,
  all-null pages, one-value pages, a known one-entry dictionary, null counts, chunk sums. Bounds
  other than a single value are not on it, so a solver cannot be asked to squeeze a page's sum
  between its bounds and the chunk's sum. On this generator it could not matter anyway: a
  widened header is written only when the inward rounding does not cross, so no page is constant
  at a widened edge, and without that no unknown page's sum is ever pinned by the bounds.
- (Recovery 3) The report consults only a one-entry dictionary, and only when knowing its entry
  leaves the chunk fewer reads. A dictionary with more entries can never tell a page's sum or a
  partial page's figures, so consulting it could only add a line; the rule says so rather than
  leaving "cheaper" to be argued.
- (Recovery 3) Every hand file now goes through `segcheck.py` before it is frozen. It exists
  because two sums were typed wrong while the new cases were being written, which would have
  graded arithmetic that no writer could produce.

## Validation status (after recovery round 3, 2026-09-23)

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py scan-chunk-pick --build`; dockerd started in this sandbox, base image pulled from mirror.gcr.io |
| No answer leaked into agent image | pass | `app_src/` only: engine, grammar, four segment files; `extraneouscheck` clean |
| oracle = 1 (two-container stand-in for harbor) | pass | 85 grader tests; harbor not installable here (needs Python >= 3.12) |
| nop = 0 | pass | on the host the shipped engine matches 8 of the 82 hand files and 0 of 330 small generated files |
| Cheats all score 0 | pass | `--all` in three shards plus the first eleven: 80 of 80 trials behaved as required (oracle, nop, 78 cheats); `cheat_report.py` names the catching hand file for every semantic cheat, 0 uncaught |
| Correct variants score 1 | pass | ok-slice and ok-tree, both rewritten for the round-3 contract, via `--dir`, 85 tests each |
| Wall clock headroom | pass | 418 files at 1 CPU / 2 GB in a container: reference 7.1 s, ok-slice 9.7 s, ok-tree 9.7 s, against 60 s; the rescan cheat does not finish |
| Reference agrees with the sealed model | pass | 82 hand files and 1,908 generated files over several seeds, byte for byte |
| `tracecheck.py` | pass | clean, 124 graded rows |
| `readingcheck.py` | pass | 61 readings, all separated by a named hand file, exit 0 |
| `onelinecheck.py` / `forgecheck.py` | pass | no decision with an exact rule at depth 2; the forgery carries gt.json and scores 0 |
| `preflight.py` | pass | no errors; warnings are the module-qualified-call false positive |
| `zipcheck.py` | pass | 128 entries, nothing stray |
| `difficultycheck.py` / `originalitycheck.py` | 100 / 97 | see the recovery sections for why 100 is not evidence |
| `harbor check` rubric | not run | no API key in this environment |
| Local calibration (three strong agents, full brief) | 3 of 3 solved | round 3, section 6; the same agents solve two tasks the platform passed 3 of 4 (section 7), so this does not place the task above the band |
| Smaller-model stand-in for the easiness screen | 0 of 3 solved | wrong on 19, 17 and 13 of the 82 hand files; the same stand-in solves the round-2 design 2 of 2 finished runs; round 3, section 7 |
| External easiness probe | not run | the recovery exit gate; required before calling the task ready |

## Quality self-review (docs/QUALITY-REVIEW.md), after the recovery, 2026-09-22

Instruction and verifier agree in both directions: `authoring/scan-chunk-pick/trace.md`, 89
graded rows, `tracecheck` clean; every enumerated file is named for the decision it pins and
`readingcheck` separates all 38 readings with the enumerated set. The six collected files are
named by absolute path, the four driver entry points are named, the clock, the single process,
Python 3.12 and the standard-library-only condition are stated, and the output format is quoted
down to the line with a whole worked example. Boundaries settled in text: 0-based rows, columns,
chunks and queries; inclusive bounds; widening; the spread's rounding and endpoints; both
tie-breaks; chunk order and repeats in the report; what a query resets.

No prose contradicts the reference. Counts re-derived from the code after the last generator
change: 47 hand files, 22 per small family, 14 small families plus 2 scale shapes, 308 small
and 6 large generated, 361 in all, 55 cheats (38 readings), 60 s; the shipped wide file's
chunk sizes and the deep file's were re-measured after the cold reader flagged them.
`hintcheck` clean, `structcheck` clean. `textcheck` against `note-carry-forward`: burstiness
0.757, 24% short sentences, no dash asides, contractions 2.2/kw - inside the band the retained
briefs occupy; vocabulary is narrower than that reference, as it was before the recovery.

Verifier rigor, environment hygiene and anti-cheating are unchanged in structure: the worker
runs the submission unprivileged under the clock and records what it printed; the grader, as
root, compares every line against `gt.json` and the sealed model; the reward defaults to 0 and
is written by the privileged stage. `extraneouscheck`, `deadfieldcheck` and `solvecheck` are
clean; `onelinecheck` finds no graded decision with a short exact rule; the forgery carrying
`gt.json` scores 0. Stray `__pycache__` directories left by host runs were deleted from the
agent tree and from `tests/`.

Metadata: `difficulty_explanation`, `solution_explanation` and `verification_explanation` were
rewritten for the rebuilt bundle and every number in them re-derived; the tag
`late-materialization` was replaced by `delta-overlay`, which names the new mechanism;
`relevant_experience` gained the changes-beside-immutable-chunks experience and claims no
employer, credential or duration. `catcheck`: Software vocabulary 31 in the environment, 125 in
the prose. `originalitycheck` 97.

Known risks carried to the reviewer: the environment is small enough to read in one sitting
and B1 is not claimed; the difficulty rests on deriving the cost rule's consequences and on the
scale gate. `simcheck` findings on the Dockerfiles and the test file are house boilerplate, as
before the recovery.

## Stage 7 re-attack (D7), after recovery round 3, 2026-09-23

Read cold with the rebuilt tree in front of me, as the probe agent would. My first plan is the
one every agent wrote for the page design: settle one condition per pair, read what it cannot
settle, remember pages across queries, pick pairs from a heap, and answer each reported page on
its own. It passes `tiny.txt`. Three things make it wrong, none visible in the surviving rows:

1. What is known acts at once. A header, an update or a remembered page on another condition
   kills rows before a pair reads for them (`flt-header-kills-other-column`), and a consult
   settles every index page of its chunk for every comparison
   (`flt-consult-settles-whole-chunk`). The late reading moves 43% of small generated files.
2. The report's reads are a per-chunk decision, not a per-page one. Wholly live pages are told
   together by the chunk's sum (`prj-chunk-sum-together`), unless a dead page's sum is unknown
   (`prj-chunk-sum-blocked`), and whether it is known depends on how the filter killed it.
3. The one-entry consult is made only when it spares a read, which can happen through a dead
   page (`prj-consult-spares-read`), and never for a chunk whose index pages supply nothing.

What makes it easy, measured rather than guessed: three strong local agents solved it 3 of 3
in about half an hour each, by writing a slow literal model from the brief before or after the
engine and fuzzing one against the other. Every rule here is stated precisely, as a principle
or as a step, so the literal model is right and the fuzzing finds every coding slip. The
difficulty that remains for such an agent is the reading itself, and all three read it right.
What it asks of a low-effort agent that does not write a model is more than before: two
principles whose consequences have to be worked out unaided, in a report pass that no longer
works page by page.

Estimated solves: 7 of 8 for the eight-attempt difficulty probe, with the uncertainty of the
tasks it was calibrated on (round 3, section 7): the local strong agents solve those about three
times in four and this 3 of 3, so they cannot place it inside the band or above it. For the
easiness screen, the smaller-model stand-in that solves the round-2 design fails this one 0 of
3.

## Open questions and next steps

Rebuilt for recovery round 3 and validated locally; the external easiness probe has not been
run on it. Recovery ends only when it passes (`RAISE-DIFFICULTY.md`, exit gate). The quality
review, AI-text screen, similarity screen and eight-attempt difficulty probe are also still to
run. `harbor check` was not run (no API key here).

The risk carried forward is the other side of the band. Strong local agents solve this design
3 of 3, so the eight-attempt difficulty probe may come back 8 of 8 even if the low-effort
easiness screen passes; the same agents solve two tasks the platform passed about three times in
four (round 3, section 7), so that risk is the ordinary one for a task inside the band, not a
measured excess. If the probe does come back 8 of 8, two directions were weighed and not taken
this round, both recorded so the next session does not re-derive them: a page's sum, once its chunk pins it,
narrowing what its header proves in the filter (measured at 1.1% of files - too thin), and a
scale family with many queries per file, where the fast path is batching and caching rather
than an invariant (engineering an agent grinds through, not a plan it has to find).
