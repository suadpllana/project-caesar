# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` (every gate below run and recorded; packaged with `scripts/package.py`, ledger entry added with verdict `pending`, delivered on branch `claude/batch-pipeline-correction-plan-xeqeuh`; awaiting the platform)

## Assistant's assigned role

You are a data platform engineer who owns the batch layer of a warehouse: hourly and daily
partitioned datasets with a keep per dataset, roll-ups that summarise a day of hours, trailing
windows and steps that carry their own previous partition forward, and partitions that were
published outside the team and may no longer be rewritten. You have planned the recompute after
a vendor restated one source partition, by hand, when the intermediates it needed had already
been expired by retention and some of what it reached had already been published.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task from the seed in `prompts/data-engineering.md`, no third-party code vendored
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it (maintainer / contributor / production user, how long): not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): not applicable
- Identifier degradation done? Conversion table lives at solution/ (never in environment/): the tree
  is written here, not degraded from a source; identifiers are chosen in the legacy register
  directly and no name misdescribes what it holds
- Proper-noun sweep done? No product, project or company name is used anywhere; the vocabulary
  that remains (partition, keep, roll-up, pin, plan) is the ordinary vocabulary of the work
- Upstream-diff check: there is no upstream to diff against

## Task summary

`/app` is the planner a batch platform runs after a source partition is restated. A pipeline file
declares hourly and daily datasets, what each step reads (the same partition, the hours of its
day, a trailing window, or the previous period, its own included), how long each dataset keeps a
partition after it ends, which partitions are published and may not be rewritten, which daily
roll-ups may stand in for the hours they summarise, the current hour and the corrected partition.
The planner prints the plan: every partition rerun and how it reads its inputs, every expired
partition computed only for the plan, and every affected partition that is left as it stands
with the reason. The shipped planner is the orchestrator backfill - the downstream closure,
sorted, every partition rerun in full - and the agent fixes the planner modules so every
pipeline's plan matches.

## Why it is hard

The first plan is the backfill every orchestrator documents and the shipped planner already is
it. It is wrong at the first published partition, at the first expired input and at the first
roll-up that stands in for a day, and the structure it is built on - a closure computed first
and sorted afterwards - cannot hold lines that lie outside the closure or a line whose presence
depends on whether its reader turned out to run.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): because the memorised and retrievable answer is to clear everything downstream of the corrected date and
  rerun it in dependency order, and that set is not the plan. A partition reached only through a
  published or unrecoverable partition is held, because nothing it reads as it reads it changed;
  an expired partition outside the closure is computed because a recompute that is actually made
  reads it; and a roll-up stands in for a day of expired hours only if it agrees once it has
  itself been settled. Which lines exist and in which order they run are outputs of a settle,
  and the closure-then-sort structure has to be taken apart rather than corrected.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1, A2, B2, C1, C3 and C4. A1 the shipped planner is the orchestrator backfill implemented
  faithfully; A2 demand-driven evaluation, the settle-then-emit split and the priority order over
  realized reads are described by what the platform does and never named; B2 ten decisions hold at
  once and the stand-in, publication and minimality rules each change which lines the others
  produce; C1 both sides are graded - pipelines where everything simply reruns, and pipelines
  where a publication or an unchanged window holds its readers; C3 two scale families make walking
  every partition from hour 0 (171.7 s for the graded set) and re-evaluating an expired partition
  for each read of it (still on the first scale pipeline at 430 s) infeasible against the 60 s
  limit and 6.0 s for the reference, while leaving both exactly correct; C4 every plan must match
  line for line over a population generated after the agent has finished. A third family I declared first - rescanning the pending lines for the next
  one - was measured at 1.6 s against 0.7 and does not bite, so it is not claimed.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  was to invert the read specs, walk the readers of the corrected partition to get the affected
  set, settle each affected partition in end-then-declaration order - held if published, lost if
  an input cannot be had, otherwise rerun - resolving each expired input recursively and adding
  the partition it computes to the plan as the recursion meets it, then sort the lines by end and
  declaration. It is wrong in three places that matter: a computed partition is added even when
  the partition that read it turns out to be held, because the recursion adds as it evaluates; a
  partition reached only through a published one is rerun as a partial rerun although nothing
  it reads changed; and a reader declared before the roll-up that stands in for it is settled before the
  roll-up's agreement is known and printed before the roll-up's rerun.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1 to 4)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 97/100, in band, no hard stop. The
  three points it lost are the shape axis reading the task folder, which held only this file at
  the time, as 0 environment and 0 reference lines; the planned shape (380 environment lines, 5
  editable files, 300 reference lines) is inside the retained band. Two warnings: the resource
  gate is declared and not yet measured, and the shape drift warning is the same empty folder.
  Attempt 2 the same day, after measuring the prototype, still 97: the gate is now measured (two
  naive families bite, a third did not and was dropped from the record), the hold reason for a
  partition whose reads did not change was renamed from stale to same and the partial run mode from
  pin to part so the words say what they mean, and the expert path now starts the walk at the
  corrected partition, which is what the measured gate requires. Attempt 3, at Stage 5 with the
  tree built, scored 100: the shape axis now reads the measured tree (234 environment lines, 5
  editable files, 296 reference lines) instead of an empty folder. At Stage 7, after the prose
  pass, the 24th reading and the corrected scale wording, 100 again with no warning.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 difficulty 97 twice at Stage 1, 100 at Stage 5 once the tree was measured, 100 at Stage 7; originality 100 at Stage 1, 100 at Stage 5 with the built instruction (nearest instruction `publish-settle-order`, cosine 0.230, shingle 0.006), 100 at Stage 7 after the prose pass. No pipeline re-anchor: not yet scored by the platform
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning? Answer must be "nothing": no plan executor or
  agreement checker ships; the sample pipelines ship without their plans and the brief quotes one
  line of one, an ordinary full rerun; no affected, changed or agreeing flag is printed or stored;
  a stand-in is its own declaration, never a read edge of the reader, so the declared reads never
  order a reader after its roll-up; the shipped existence helper applies the keep to every
  partition, so the published exemption comes only from the brief.
- Expert path, described step by step (the harder the aim, the more this guard must hold): run the
  shipped planner on the samples and find the module that owns the quoted line; rebuild the
  affected set over every partition the read specs name, expired or not, from the corrected partition up to now;
  write existence as ended by now and within the keep after its end, published partitions kept
  whatever their age; resolve each read - stored if it exists, the roll-up for a day with a
  missing hour if it exists and agrees, otherwise the missing partition computed for the plan,
  failing at a missing source partition; settle each partition once, roll-ups before the readers
  of their hours, into computable, changed and agreeing, and from those a run mode or hold
  reason; emit by demand, runs first and then every computed partition a made line reads; order
  the lines over the reads each actually makes with a heap on end and declaration; time the scale
  pipelines and make the settle iterative and shared.
- Originality check: searched 2026-09-22 with seven queries (listed in the record). Public
  material covers partition mappings between grains and backfilling a downstream range (Dagster),
  clear-downstream and date-range backfills (Airflow), idempotent partition overwrite, lineage
  blast radius, retention ladders from raw to roll-ups, and minimality with early cutoff over task
  graphs (the build-systems paper). None states when a roll-up may stand in for expired hours,
  what a published partition's readers read, or which expired partitions a plan computes and does
  not keep, and none produces a plan with modes or hold reasons.
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml, at
  Stage 1 before the difficulty record, again once instruction.md exists; every attempt's score,
  and the crowded archetype named - docs/ORIGINALITY.md): attempt 1 on 2026-09-22 scored 100/100,
  no hard stop; tags overlap nothing in the ledger, the substrate reuses no earlier substrate, and
  the mechanism sentence is 0.13 cosine from its nearest ledger entry (guard-mark-unwind). The
  crowded archetype named is "DAG scheduler with retries and backfills", on the Data engineering
  list; the departure is that its set to run is the downstream closure read from storage, which
  cannot produce holds, stand-ins or partitions computed only for the plan.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag),
  what overlaps, and which of the five surfaces separate them: `delta-view-retraction`. Both keep
  derived data in agreement with a changed source and punish rebuilding everything. All five
  surfaces separate: it folds deltas into one aggregate view and grades values against work
  ceilings; this plans partition recomputes across a multi-step pipeline and grades the plan
  lines, their modes and hold reasons and their order. `slab-fold-scope` shares only the label.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

Every graded assertion traces to a sentence in the instruction. Walk the tests, the sealed model
and test.sh line by line into authoring/<slug>/trace.md, start it with
`python tools/tracecheck.py <slug> --skeleton`, and keep `python tools/tracecheck.py <slug>` clean.
`preflight.py` errors while any line below is unanswered.

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 87 graded rows walked - the four test functions and the stage-one record parser, the worker's collection and its driver call, the 60 second clock, the one process and the 2048 MB, 30 enumerated cases, 5 artifacts, and the sealed model split into 42 rows, one per rule with its lines - plus 24 readings, 7 shortcut strategies and 2 limits. No NOT STATED row survived and `python tools/tracecheck.py restate-hold-plan` is clean, re-run after the Stage 7 prose pass re-quoted every row whose sentence it reworded.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 24 readings are written as whole planners by `authoring/restate-hold-plan/emit.py` and measured by `python tools/readingcheck.py restate-hold-plan`: all 24 are separated by the enumerated set, and `cheat_report.py` asserts that each fails the case named for its rule (0 findings). None survives the published evidence: each is ruled out by a sentence quoted in the trace. Over a sample of 150 generated pipelines they move from 1 per cent (sort-then-fix order) to 87 per cent (a window's readers taken backwards); the rare ones are rare because ten families dilute them, and in the family that exercises each one most, every reading moves at least 15 per cent of 20 programs (a same-held partition agreeing, in `stand`) and most move 25 to 100 per cent. The 24th reading, a roll-up standing in inside a partition computed for a rerun making that rerun `sub`, came out of the Stage 7 re-attack: the brief said `sub` "when a roll-up stood in for hours" without saying whose computation, the frozen `stand-in-temp` plan answered it (`run w 7 full`), and the sentence now reads "when it read a roll-up in place of hours". `stand-in-temp` separates it and it moves 45 per cent of the `edge` family.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): the nop matches 7 of 30 enumerated plans and 25 of 150 sampled generated ones (all 15 plain, 5 pins, 4 cross, 1 chain); an empty plan matches 0 and 0; every reached partition held as same matches 3 and 0; the closure rerun in full (positional) matches 5 and 25; the quoted line replayed matches 0 and 0; the forgery carrying every frozen enumerated plan matches 30 and 25. Host-trial scores are recorded under Validation status.
- Independent implementation behind every tolerance and limit (path, measured headroom): `authoring/restate-hold-plan/variants/ok-recursive` and `.../ok-forward`, both written apart from `solution/`, plan the whole graded set in 4.0 and 5.9 seconds against the 60 second clock (the reference 6.0), ten times inside it, and peak at 57 and 60 MB on the largest sample against 2048 MB. The two naive but exactly correct families take 171.7 seconds (every partition from hour 0) and over 430 seconds on the first scale pipeline alone (no memo). There is no numeric tolerance: plans are compared line for line.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, mechanically, over every printed token (line kind, dataset, partition number, mode or reason, and the order). Five gaps were found in the first draft and closed with a sentence each: which of lost and same wins when both hold (now 'otherwise held as same'), what a held partition's agreement is, that a published partition exists only once it has ended, how the driver hands rows back and joins them, and the memory the graded run has. The keep boundary got a worked example because the author's own hand derivation missed it once; the other conventions (hour 0, the day before for x-1, the tie between equal ends) were already settled by a sentence. The Stage 7 cold re-read found one more, whose stand-in makes a rerun `sub`, and closed it the same way (see Identifiability).

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22. The sealed model is `tests/seal/model.py`; every rule below carries the
number its code carries there (R1-R15), and `authoring/restate-hold-plan/hand.py` holds a
by-hand derivation of every enumerated plan that the model was checked against before
`gt.json` was frozen (30 of 30 agree; the one first disagreement was an off-by-one in the hand
derivation at a keep boundary, which is why that boundary gets its own sentence and example).

- Artifacts the agent produces: `/app/plan/keep.py`, `/app/plan/reach.py`, `/app/plan/look.py`,
  `/app/plan/settle.py`, `/app/plan/order.py`. Nothing else is collected; the verifier lays those
  five over its own pristine copy of the tree, so the driver `/app/run_plan.py`, the parser
  `/app/plan/pipe.py`, the time arithmetic `/app/plan/span.py` and the sample pipelines cannot
  change what a pipeline prints, and a new file beside the five is never collected.
- What is checked: the printed plan of every graded pipeline, line for line and exactly. Thirty
  enumerated pipelines against `gt.json`; 408 generated pipelines (40 of each of ten small
  families, 4 of each of two large ones) against the sealed model, which must itself still
  reproduce `gt.json`. The generator draws its seed inside the verifier after the agent is gone.
- Tolerances: none. The one limit is the 60 second wall clock on the stage that runs submitted
  code, over the whole graded set; it is validated against two independently written correct
  planners (the model and `authoring/restate-hold-plan/variants/`), not only the reference.
- Ground truth, and where it lives: `tests/seal/model.py` and `tests/seal/gt.json`, in a
  directory made `chmod 700` before the privilege drop.

### The graded decisions, and the sentence each is owed

1. **The pipeline file** (R1, R2): `now`, `src`, `step` with its reads, `stand`, `pin`, `fix`;
   declaration order; the four reads `x`, `x/d`, `x~w`, `x-1` and exactly which partitions each
   names. Sentence: one per declaration and one per read, with the previous-period read defined
   as the latest partition of x that ends at or before this one starts.
2. **Spans** (R3): hourly h spans [h, h+1), daily d spans [24d, 24d+24); a partition ends at the
   end of its span. Sentence: stated once, with hour 0 as the start of history.
3. **Reads before hour 0** (R4): dropped, never computed and never lost. Sentence: "a read that
   falls before hour 0 reads nothing there".
4. **Existence** (R5): ended by now, and published or now < end + keep. The corrected partition
   exists. Sentence: the inequality written out, with a worked boundary.
5. **What the correction reaches** (R6): the corrected partition and every partition of a step
   that has ended by now and reads a reached one by its declared reads, whether or not the
   partitions between exist. Sentence: stated with "whether or not" explicit.
6. **The line of a reached partition that exists** (R8, R9): published - `hold pinned`; cannot be
   computed - `hold lost`; nothing it reads changed - `hold same`; otherwise a run. Sentence: the
   three reasons in that precedence.
7. **Changed and agrees** (R7, R8): the corrected partition changed and agrees; a rerun changed,
   and agrees when everything it read agrees; a partition computed for the plan changed when
   anything it read changed and agrees when everything it read agrees; a held reached partition
   is unchanged and does not agree; an unreached partition is unchanged and agrees. Sentence:
   both flags defined over "what it read", including computed partitions and roll-ups.
8. **The run mode** (R10): `part` when anything it read does not agree, else `sub` when a
   roll-up stood in, else `full`. Sentence: the precedence stated.
9. **Roll-ups** (R11): `stand r x` - when a computation reads `x/d` for a day and any hour of it
   does not exist, the roll-up's partition of that day is read instead of all 24, provided it
   exists and agrees; otherwise existing hours are read and missing ones computed; never for the
   roll-up's own computation. Sentence: each of the four conditions.
10. **Computed for the plan** (R12, R13): a partition that does not exist is computed from its
    own reads, once, when a computation reads it; a missing source partition cannot be computed
    and the computation that needs it fails; a `temp` line exists for every partition computed
    for a made run or for another printed temp, and for nothing else. Sentence: the demand rule
    stated plainly, including that a held partition's reads print nothing.
11. **The order** (R14, R15): runs and temps first, each after every line of what it read
    (including a roll-up it read in place of hours); of the lines that may come next, the one
    whose partition ends first, then the one whose dataset is declared first. Then the holds by
    end, then declaration. Sentence: the rule, and the output format of each line kind.
12. **The execution limit**: the whole graded set within 60 seconds; the brief states the scale
    of the two large families and ships one instance of each shape for timing.

### Prong C, and the route-around

- C1: `plain-rerun`, `pinned-unreached` and the `plain` family must print every reached
  partition as a full rerun; `pinned-hold`, `pinned-window-same`, `temp-only-for-reruns` and the
  `pins` family must hold. Over-eager and over-conservative planners both fail.
- C2: the shipped planner prints a coherent plan for every pipeline; the natural self-check,
  replaying a plan on a toy value model, is satisfied by a plan that reruns everything, so it
  confirms none of the minimality, mode, hold or order decisions.
- C3: the `long` and `deep` families. Measured before freezing, on one program each of the first
  sizing: the model settled `long` in 0.76 s and `deep` in 0.43 s, walking every partition from
  hour 0 took 14.4 and 5.6 s, and re-evaluating an expired partition for each read of it took
  75.7 s on `long` and did not finish `deep` in twenty minutes. Over a whole graded set that
  sizing let the hour-0 walk fit the clock at 48.8 s, so the families were enlarged before the
  instruction was written - three years of history instead of two, a second thirty-day window in
  `long`, a thirty-day window in `deep`, four programs of each - and measured again over the whole
  set: reference 6.0 s, correct variants 4.0 and 5.9 s, the hour-0 walk 171.7 s, the re-walk still
  on its first scale pipeline at 430 s.
- C4: all-or-nothing over 438 pipelines, the 408 generated ones drawn after the agent is gone.
- Route-around: five collected files over a pristine tree; the driver's call shape
  `order(pp, settle(pp, reach(pp)))` is frozen, so the plan cannot be produced by any other
  path; the worker records a signature of every program so a submission cannot alter the
  pipeline it is graded on.

## Decisions and their reasons

- **Software / Data engineering.** The graded work is planning recomputes over a partitioned batch
  pipeline; nothing about it is a database engine or an algorithm exercise.
- **No container evidence in this session.** Docker runs here once the daemon is started, but the
  egress policy denies Docker Hub's blob CDN (`production.cloudfront.docker.com`, 403), so no base
  image can be pulled. The verifier is exercised by a host emulation that runs `tests/test.sh`
  verbatim as root with the real privilege drop, as `publish-settle-order` did for the same reason;
  that is recorded wherever a result is reported, and container results are not claimed.

## Validation status

Every result below comes from this session, and none of it is container evidence: the egress
policy answers 403 for Docker Hub's blob CDN, so no image was built. The two-stage runs are
`authoring/restate-hold-plan/host_trial.py`, which runs `tests/test.sh` verbatim as root on this
host with the real drop to uid 1002, the 60 second clock, the locked 0700 reward directory and
sealed side, the survivor reap and the reward written last, over only the five declared artifacts
laid on the verifier's own tree, with Python 3.12 and the pinned pytest from a venv.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | base image cannot be pulled here (egress 403); `tools/imagecheck.py` assembles the image's `/app` from the COPY and WORKDIR lines, places the reference and runs all three sample pipelines: clean |
| No answer leaked into agent image | checked on the tree | the image copies only `app_src/`: the driver, the frozen parser and time arithmetic, the five shipped-wrong planner files and three pipelines without plans; `extraneouscheck`, `forgecheck` and `solvecheck` clean |
| `harbor run -a oracle` = 1 | host emulation: 1 | 33 of 33 tests; run twice, before and after the cheats were rebuilt |
| `harbor run -a nop` = 0 | host emulation: 0 | stage one runs out of the 60 s clock (exit 124); without the clock the shipped planner matches 7 of 30 enumerated plans |
| Cheats all score 0 | host emulation: 39 of 39 | each for its own reason, below; both correct variants score 1 |
| `tracecheck.py` (every graded assertion traced) | clean | 87 graded rows, 24 readings, 7 shortcuts, 2 limits |
| `preflight.py` | clean | 0 errors, 0 warnings once the ledger entry was added |
| `harbor check` rubric | not run | no harbor binary and no API key in this session; the criterion-by-criterion self-review below stands in for it |

Other gates, all run at Stage 7 on the final bundle: `originalitycheck` 100 (instruction nearest
`publish-settle-order`, cosine 0.229, shingle 0.006), `difficultycheck` 100 on the measured tree,
`readingcheck` 24 of 24 separated, `cheat_report.py` 0 findings, `onelinecheck` no short rule for
any of the four line decisions, `simcheck` 8 HIGH rows on Dockerfile boilerplate and no NEAR
(retained bundles that passed show 2 to 10) with no conceptual overlap, `hintcheck`,
`structcheck`, `deadfieldcheck`, `catcheck` (software: environment 49, prose 62), `solvecheck`,
`extraneouscheck`, `forgecheck` and `imagecheck` clean, `textcheck` against a passed brief no
finding, `sync_pristine.py --check` and `make_pipes.py --check` clean. Determinism: the graded
population and the plans of the reference and the model are byte-identical under five hash seeds
(0, 1, 7, 4242, random), and the reference equals the model on all 438 pipelines of that seed.

### Stage 6 - the cheats in the host trial

The first full run scored every cheat 0, but twelve of them only because stage one ran out of the
clock: the probes, the shortcuts, the forgery and one reading sat on the shipped planner, whose
reach indexes every partition from hour 0. A 0 on the clock proves nothing about what the cheat
tampered with (CLAUDE.md: assert the layer, never just the reward), so they were rebuilt on the
shipped planner with only its reach made fast - checked to print the same plan as the shipped one
on 180 pipelines - and `temp-per-reader` counts its readers once instead of rescanning. In the
second run only the nop and the two deliberately slow planners exit 124:

- 24 wrong readings: stage one finishes, and each fails between 2 and 26 of 33 tests, always
  including the case named for it in `cheat_report.py`.
- `slow-every-hour`, `slow-rewalk`: exactly correct, stage one killed at 60 s.
- `const-nothing` 31 of 33 fail, `const-same` 28, `replay-quoted` 31; `forge-enumerated` passes
  all 30 enumerated plans and fails only the generated set.
- `probe-answer-key`: `gt PermissionError`, `model ModuleNotFoundError`, then graded as the
  shipped planner (24 fail). `probe-privilege`: runs as `uid 1002`, `reward PermissionError`.
  `probe-late-reward`: 100 survivors reaped, reward 0. `probe-plant-record`,
  `probe-rewrite-grader`, `probe-shrink-population`: the tampering fails and the plans are graded
  (24 fail each). `probe-crash-after-plant`: 31 fail. `probe-malformed`: the record does not parse
  and 31 tests error. `probe-extra-file`: the hidden module is not collected, the planner cannot
  import it and stage one exits 1.

## Stage 7 - re-attack against the finished bundle

Read cold with the shipped tree in front of me, the first plan is still the backfill the tree
implements. The quoted line says only that the correction must travel through an expired `clk`,
and the obvious repair - let the shipped reach walk through expired partitions and keep the rest -
fits no pipeline with a publication, a roll-up or an expired input a rerun needs, and still
indexes every partition from hour 0, which the scale families put at 171.7 s against 60.

Are the load-bearing facts still distributed? Every rule has its sentence, as the contract
requires, and the cold-reader additions each define a printed token rather than a structure. What
the brief never says is how the rules combine: that a roll-up's agreement has to be settled before
any reader of its hours, computed partitions included; that whether a computed partition is
printed is known only once its reader's line is; that where a line goes depends on how each of its
reads resolved; that the walk can start at the corrected partition because every read looks back.

Did the brief come to telegraph the method? It names no algorithm. The order paragraph describes
what a priority queue over realised reads produces, which is the definition of the graded order
and cannot be left out, and "Two things are known of every partition a computation reads" says
the flags exist, which a reader needs in order to decide any line at all. Neither says to settle
before emitting, to settle roll-ups first, or where to start the walk.

Two defects found and fixed. The `sub` sentence did not say whose stand-in counts; it now says
the rerun's own, and the other reading is the 24th cheat. And the brief said `long` is corrected
"under two weeks back" when the generator puts the correction 8.0 to 15.0 days back; the brief,
the generator's docstring and the difficulty record now say eight to fifteen days. The prose pass
also broke three runs of same-shaped sentences - the four read forms, the five flag sentences and
the print formats - without changing a rule; the trace was re-quoted and is clean.

Honest estimate after the re-attack: 2 of 8 (range 1 to 4), unchanged. Every rule can be
implemented from its sentence, so an agent that reads with care and builds a memoised evaluator
from the brief can pass; what stands between that and the reward is getting all twelve decisions
exactly right with one quoted line of feedback, over 438 all-or-nothing plans, inside the clock.
The realised rate on a task whose rules are all stated has drifted up before (`publish-settle-order`
in CLAUDE.md), so the top of the range is the risk to watch.

Self-probe: not run. I wrote the sealed model before the environment, so a cold solve by me would
measure memory, and the contributor's instruction rules out a fresh subagent. As for
`reach-pair-sweep`, the reading separations (24 of 24, each by a named case), the layer report (0
findings) and the absence of any oracle in the tree stand in its place.

## Quality self-review (docs/QUALITY-REVIEW.md, criterion by criterion)

Instruction and verifier agreement:
- Every tested behaviour is described: each of the 87 graded rows of `authoring/restate-hold-plan/trace.md`
  quotes its sentence, and `tracecheck` is clean.
- Every promise is tested: the pipeline format and read forms (`instruction.md:3`) by
  `prev-cross`, `prehistory`, `temp-window` and every family; existence and reach (`:5`) by
  `keep-edge`, `keep-published`, `reach-through-expired`, `reach-bounded-by-now`; the line kinds
  (`:7`) by `pinned-hold`, `lost-source`, `lost-before-same`; computing and roll-ups (`:9`) by
  `temp-window`, `temp-once`, the six `stand-*` cases; the two flags (`:11`) by `same-disagrees`,
  `pinned-part`, `temp-only-for-reruns`; the formats (`:13`) by `mode-part-over-sub` and
  `lost-temps-unprinted`; the order (`:15`) by `order-after-roll-up` and `holds-last`; the
  collected files (`:19`) by `tests/worker.py:21` and `probe-extra-file`; the limits (`:21`) by
  `tests/test.sh:39-40` and `task.toml:194-195`.
- Output named with its path: the five artifacts at `instruction.md:19`, matching `task.toml:3-9`.
- Exact schema: the three line formats at `instruction.md:13`, the row join at `:19`, and the
  driver that joins them is frozen in the verifier's pristine tree.
- Boundaries and conventions: hour 0 and the spans (`:3`), `x-1` across grains with both examples
  (`:3`), reads before hour 0 (`:3`), `end <= now < end + keep` with a worked boundary (`:5`), ties
  by declaration (`:15`).
- Every graded quantity defined with its exclusions: exactly one line per reached existing step
  partition (`:7`), nothing for a partition computed only for a held one (`:13`), nothing else
  printed (`:15`).
- No contradiction or stale count: 438 = 8 + 400 + 30 (`gen.BIG_EACH`, `EACH=40` in `test.sh`, 30
  in `cases.py`); three pipeline files ship; three years, thirty-day windows, eight to fifteen
  days, a keep of a day - all re-derived from `tests/gen.py` at Stage 7; the metadata's 171.7 s,
  430 s, 6.0 s, 4.0 and 5.9 s, 39 cheats (24 + 2 + 3 + 1 + 9) and 408 generated pipelines match the
  measurements above.
- Verifier requirements in the text: collected files, the pristine copy and the driver's call
  shape (`:19`), one process, one CPU, 2048 MB and 60 seconds (`:21`). No internal field names:
  the agent returns rows and the frozen driver prints them.
- Readings, shortcuts and tolerances: 24 of 24 readings separated; every constant, positional and
  replayed strategy scores 0; no numeric tolerance, and the clock was validated by two planners
  written apart from the reference.

Instruction prose: the three runs of same-shaped sentences were rewritten at Stage 7; `textcheck`
against a brief that passed the screen reports the candidate at least as irregular on every axis;
each requirement is stated once; the register is plain and in the contributor's first person
plural throughout ("our batch platform", "our own copy").

Verifier rigour: the grade is the plan the submitted code printed for each pipeline, produced by
`tests/worker.py` in stage one as uid 1002 and bound to its pipeline by a digest the grader
recomputes (`tests/test_outputs.py:112-116` and `126-137`), never an exit code; each test sits
under a comment naming what it checks, and the module docstring (`tests/test_outputs.py:1-34`)
states the whole contract; the population is
fixed by its seed and measured identical under five hash seeds, and the one clock has ten times
headroom over both correct variants.

Environment hygiene: `environment/Dockerfile` copies only `app_src/`; pytest 9.1.1 and ctrf 0.5.2
are pinned with `==` in `tests/Dockerfile`; no apt package; every path and name the brief uses
exists as spelled - `/app/run_plan.py`, `/app/pipes/{small,long,deep}.txt`, the five planner
files, and `raw`, `clk`, `ses` and hour 610 in `small.txt`.

Solution quality: `solution/solve.sh` copies the five planner files, which are programs, and runs
the planner on `small.txt`; nothing writes a plan directly, and nothing outside the brief and the
tree is used.

Anti-cheating: no plan ships anywhere in the image; `gt.json` and the model sit in `tests/seal`,
locked 0700 before the privilege drop (`tests/test.sh:26`); comparison is exact; there is no
repository history in the image.

Metadata: `Software` / `Data engineering` (`task.toml:158-160`; `catcheck` clean); six specific
tags, none restating the category (`task.toml:162-169`); `difficulty_explanation` names the three
concrete wrong steps (`task.toml:22-34`) and says the legacy register and missing comments are
deliberate (`task.toml:57-62`); `solution_explanation` gives the method in the order the files depend on each
other and why; `verification_explanation` maps each fence to its case; `relevant_experience` is
specific to recompute planning; `expert_time_estimate_hours = 9` matches the difficulty record.

## Residual risks

- No container evidence. Oracle, nop, cheats and variants ran in a host emulation of the two-stage
  platform; the image builds and the platform's artifact transfer were never exercised here.
- `harbor check` was not run (no harbor, no key), so the rubric pass above is the author's reading.
- No cold self-probe, for the reason above; the estimate of 2 rests on the design, the separations
  and the measured scaling boundary rather than on a solve attempt.
- The environment is 234 Python lines, near the bottom of the retained band (229 to 544), on
  purpose: the difficulty is in the plan, and the graded patch of about 300 lines is mid-band.
- Every rule is stated. That is what the contract requires, and it is also the condition under
  which `publish-settle-order`'s realised rate drifted up.

## Next steps

Wait for the platform's verdict and record it in `authoring/submissions.toml`. If the easiness
probe rejects the task, follow `RAISE-DIFFICULTY.md` before touching anything else.
