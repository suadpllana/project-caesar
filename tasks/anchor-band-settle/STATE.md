# Task state - anchor-band-settle

Working memory for this task. Updated after every stage. Assume the next session starts with no
memory of this one.

## Current stage

`Stage 6 - Anti-cheat` complete and `Stage 7 - Packaging` in progress (2026-09-22). Stages 1-5
are done: both pre-code records are in band on the built tree, the environment tree, reference,
sealed model and two correct variants are built, the instruction and the four task.toml prose
fields are written, and the trace walk is clean. All 45 cheats score 0 with the layer named for
each asserted by `cheat_report.py`, and the two correct variants score 1. Next: package with
`scripts/package.py`, run `zipcheck`, add the ledger entry, commit and push.

## Assistant's assigned role

A senior layout and scrolling engineer on a document-view toolkit: block flow layout, incremental
relayout driven by a change log, sticky positioning with section containment, and the
interaction between keeping the reader's place and headers that stick. Chosen by the assistant
from the seed (`prompts/frontend.md`); no repository was supplied.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task from the Frontend seed prompt
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable, no repository
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable, nothing vendored
- Pinned commit vendored into environment/app_src/ (.git stripped): not applicable
- Load-bearing couplings found during research (file paths): recorded at Stage 3 for the authored tree
- Identifier degradation done? not applicable to an authored tree; legacy-register naming is a design choice stated in `difficulty_explanation`
- Proper-noun sweep done? not applicable; the tree names no product, browser or project
- Upstream-diff check: not applicable, there is no upstream

## Task summary

`/app` is the layout and scrolling half of a document view. A program declares a tree of boxes
with integer heights inside one scrolling view, then runs frames; each frame applies a batch of
edits (a box resolves to its real height, a row is shut or opened, a box is added or dropped,
pinned or unpinned as a header, lifted out of the flow or put back, or the view is scrolled
explicitly) and then prints one line: the scroll offset after the frame and the box the view was
held by, or why holding was off, or that no box qualified. Four modules are editable: layout,
sticking, picking and holding. They ship as a coherent, wrong and slow first plan.

## Why it is hard

The shipped tree already is the first plan every "keep the scroll position" answer gives: before
the edits take the first box showing and its distance from the top of the view, after them put
it back at that distance in one pass, and pick afresh when it is gone. Here the distance is
measured below the bottom of the headers stuck at the offset being tried, stuck boxes can never
hold the view, a disqualified holder hands over to its nearest pre-frame container at that
container's own pre-frame distance, and the adjustment settles over at most four passes with the
smallest offset kept when they never agree. Every adjusted offset can stick or unstick a header,
which moves the reference line and can disqualify the holder halfway through the frame, so the
restore becomes a loop that resolves the holder again on every pass over a chain saved before any
edit. Then the scale: a full relayout per frame answers the scale programs exactly and cannot
finish inside the limit, so layout, tops and the stuck set all have to be found from a few
root-to-leaf paths.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan its
  prior and the best public page give (restore one saved distance once, S1 = S0 + (L1 - L0)) is
  wrong in its reference line, its single pass and its fallback; the correct plan is a bounded
  settle whose inputs (holder, distance, band) change from pass to pass, and it also has to be
  built on an incremental layout whose stuck-set query is derived from the geometry, not stated.
  The rules are all in the brief; which structures survive all of them at once is not.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C3, C4, plus the guard.
  A1: the prior and the spec are wrong on the reference line, the single pass, the fallback and
  offset zero. A2: the concept is described, never named. A3: restore-once, per-pass fallback and
  no full relayout pull three ways. B2: thirteen interacting rules. C1: ordinary frames fence the
  cautious over-correction. C2: no local oracle; one printed line per frame. C3: a full relayout
  per frame, or a scan of every header per pass, is exact and over the clock. C4: all-or-nothing
  over enumerated and generated programs. Guard: four collected files over a pristine tree.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my own first plan
  from the seed was the shipped one - record the first visible box's offset from the view top,
  restore it after the edits, clamp. It is wrong in five places that ordinary frames never show:
  the reference line is below the stuck band; the band at the adjusted offset differs from the
  band at the old one; a holder inside a header that sticks during the adjustment is disqualified
  mid-frame; the fallback's distance is its own, which only a chain saved before the edits can
  supply; and a full relayout per frame is exact but over the limit. Reading a brief that states
  every rule, I would write the loop correctly on the first try with maybe even odds; the part I
  would get wrong first is the stuck-set query at scale, which the brief cannot state without
  handing over the method.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1 to 3)
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml, before
  Stage 2; every attempt's score and what changed, until it reaches the band in
  docs/DIFFICULTY-SCORE.md): attempt 1 on 2026-09-22 scored 100/100 read as a pre-code design,
  in band, no hard stop. With the empty `tasks/anchor-band-settle/` folder present the checker
  measures a 0-line tree instead of reading the planned shape and reports 97/100, also in band;
  both numbers are recorded because both are what the tool printed. One warning: the resource
  gate is declared but not measured; Stage 4 measures it before any prose depends on it. Nothing
  was changed between attempts because there was one attempt.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not yet submitted
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-22 design record 100 (97 with the empty folder measured)
- Leak audit (docs/DIFFICULTY.md): the samples print one line per frame and the brief quotes one
  frame chosen by search so it separates no wrong reading of the loop, the stuck rule or the
  fallback; the shipped stick and pick modules implement the prior coherently and name nothing;
  the tree's change log records only the kind of each edit and the box it named; no pass count,
  band, distance or stuck set is printed anywhere. Answer: nothing, to be re-run as a procedure at
  Stage 6 with the built tree.
- Expert path, described step by step: read the grammar, the tree's edits and change log and the
  frame driver; make layout incremental (heights along each edit's ancestor chain, per-parent
  child offsets rebuilt where a child changed, tops on demand); write the stuck rule with the push
  from the section end and the band as the lowest bottom edge of stuck headers, found from boxes
  crossing the top strip; write the pre-frame pick below the band and record every chain box's
  distance; write the settle loop with per-pass resolution, clamping, the stop and the cap with
  the smallest offset; add the two switches and the no-holder line; time the scale programs and
  hand-trace small frames that stick, unstick, cycle and fall back mid-loop.
- Originality check: searched nine queries (listed in `authoring/anchor-band-settle/originality.toml`).
  Found the CSS Scroll Anchoring spec and WICG explainer, MDN, a WebKit implementation PR, Chromium
  review threads that strip sticky offsets before measuring, scroll-padding fixes for hash links
  behind sticky headers, a jitter postmortem, a tail-follow scroll box issue and a small
  preservePosition library. None settles against an offset-dependent band or falls back to a
  pre-frame container at its own distance; no twin task or simulator turned up.
- Distinctness record score (tools/originalitycheck.py on authoring/<slug>/originality.toml): attempt
  1 on 2026-09-22 scored 100/100, no hard stop; tags overlap nothing in the ledger, the substrate
  reuses no earlier substrate, the mechanism sentence's nearest ledger entry is
  `alias-settle-report` at cosine 0.09. Crowded archetype named: virtualized or infinite lists
  (keeping the scroll position when content above changes is that archetype's famous subproblem);
  on the list, departure stated. The corpus half runs again once `instruction.md` exists.
- Nearest already-submitted task (from authoring/submissions.toml or the platform's own flag), what
  overlaps, and which of the five surfaces separate them: `focus-return-point` (Frontend). Overlap
  at its strongest: both edit a tree in batches and both decide what a disqualified node's role
  passes to. Separated on all five surfaces: mechanism (settled scroll offset vs focus holder),
  substrate (flow-laid document with sticky headers vs widget tree under a screen stack), graded
  output (offset and holder per frame vs focused id per event), failure mode (restore-once vs
  immediate/deferred focus), interaction (stuck band vs eligibility, against deferred effects vs
  instance identity). No events, focus, screens, keys or id reuse here, which keeps the question
  geometric as the seed asked.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): walked 2026-09-22 and `tools/tracecheck.py anchor-band-settle` is clean, with no NOT STATED rows.
  Every graded assertion, all 39 cases, the 4 artifacts, the 90 s clock and the driver/line format
  have a row quoting instruction.md word for word; all 33 readings have a row with the sentence and
  the case that separates each; the Shortcuts and Tolerances tables carry measured figures.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 33 readings, none survives the published evidence, each separated by its enumerated case.
  Built by asserted substitution in `authoring/anchor-band-settle/readings.py` (`--cases` all 33
  ok; `tools/readingcheck.py anchor-band-settle 40` all 33 separated, 0 blind). Two early readings
  (a stuck header shown below the band; descending a shut box) were unobservable and dropped rather
  than shipped as unseen rules. `tools/onelinecheck.py` OK: `fell_back` and `settle_offset` have no
  rule at depth <= 2; the control `scrolled_off` does (`is_scroll`), so the search works.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): all score 0; nop 15/39 enumerated, constant 0/39, positional first-box 1/39, replay 0/39.
  nop `0` from the shipped tree (host trial: worker times out on scale); constant `0 off scroll`
  (`cheat/cheat-const-lines.sh`); positional first-box (`cheat/cheat-pos-first-box.sh`); worked
  example replayed (`cheat/cheat-replay-small.sh`); plus a forgery carrying gt.json 39/39 enumerated
  and 0/390 generated (`cheat/cheat-forge-from-truth.sh`). No regeneration needed.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 90 s worker clock, measured against the sealed model and two correct variants, slowest at 4.8x headroom.
  Full graded set on this host: reference 5.1 s, `variants/ok-onefile` 6.7 s, `variants/ok-memo`
  18.7 s, a no-row-cache reading 19.3 s. Exact-but-naive: full relayout 489 s, header scan 471 s
  (5.2x and 5.4x over). Both variants score 1 end to end (`host_trial.py --variants`).
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run, and it leaves no decision undecided; every graded quantity traces to a quoted sentence that `tracecheck` confirms.
  The session that wrote the model wrote the walk, recorded as such in `trace.md`. A genuine
  fresh-reader pass was not run because the author is contaminated by having built the model; the
  reading separations and the no-oracle property (no browser, the real spec differs on purpose, one
  line per frame) stand in its place, as with `reach-pair-sweep`.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-22 (the clock value is the one Stage 4 measured; see "Resource gate" below).

- Artifacts the agent produces: `/app/view/lay.py`, `/app/view/stick.py`, `/app/view/pick.py`,
  `/app/view/hold.py`. Nothing else is read. The worker lays them over its own pristine copy of
  `environment/app_src` (`tests/pristine`); a file placed beside them is never collected.
- Interface: the frozen driver `view/frame.py` calls `hold.start(v)` once, then per frame
  `hold.before(v)`, applies the edits through the frozen tree (which appends `(kind, box, arg)`
  to `v.log`), calls `hold.after(v)` for `(offset, word)`, sets `v.s`, clears the log and prints
  `<n> <offset> <word>`. Every graded program runs through `view.frame.run` in one process, one
  after another.
- What is checked: every line of every program, exactly - 39 enumerated programs against
  `tests/seal/gt.json` (frozen from the model after the model and the plain full-relayout oracle
  `authoring/anchor-band-settle/naive.py` both produced every answer), and every program of 13
  shaped small families (30 each) and 2 scale families (3 each), generated from a seed drawn
  after the agent has finished, against the sealed model `tests/seal/model.py`. The grader first
  checks that the model reproduces gt.json and that the program file root wrote before the
  worker ran is byte-identical (sha256 kept in the root-only reward directory).
- The thirteen graded decisions are listed at the head of `tests/test_outputs.py`: flow, the
  stuck rule with the section-end push and the strict comparison, the band as the lowest edge
  floored at zero, the pick region (empty once the band reaches the bottom of the view), the
  pick walk, the chain and its pre-edit distances, qualifying judged per pass, falling back,
  the pass target, settling (first pass from the old offset, stop on no movement, four passes,
  smallest offset held by the first pass to reach it), the scroll switch, the live switch with
  scroll outranking it, and the frame with nothing picked.
- Tolerances: none. Offsets are integers and every line is compared as a string.
- Execution limit: the whole worker (every program) runs under `timeout RUN_SECONDS` in
  `tests/test.sh`; a timeout loses the record and scores 0. The value is set from the Stage 4
  measurement and stated in the brief.
- Ground truth, and where it lives: `tests/seal/` (model and gt.json), `chmod 700` root-owned
  before the privilege drop, so submitted code can neither read the answers nor import the model.
- Isolation (docs/VERIFIER-ISOLATION.md applies: the verifier executes agent code): worker runs
  as uid 1002 in its own session under the clock; `/logs/verifier` is `install -d -m 700` before
  any agent code; reward defaults to 0 and is written last by root; survivors are reaped by uid;
  the grader parses the worker record defensively and derives everything from trusted inputs.

## Decisions and their reasons

- Category `Software`, label `Frontend`: the graded work is a view's layout and scroll behaviour;
  `Software/Systems` is retired and not considered.
- No id reuse and no move edit: both would pull the task toward widget-instance identity, the
  mechanism of `focus-return-point`. The question stays geometric.
- `live` is a declaration flag only, so "inside a live box" is fixed for the life of a box.
- A view at offset zero is held like any other, a deliberate departure from the spec's
  suppression at zero (A1); it gets its own enumerated case.
- Docker Hub's blob CDN is denied by this session's egress policy (403 on
  `production.cloudfront.docker.com`), so no base image can be pulled. Container trials use the
  kit's host emulation (adapted from `authoring/publish-settle-order/host_trial.py`) and are
  reported as host evidence, not container evidence. `harbor` 0.23.0 is installed.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | host emulation only | Docker Hub blobs blocked by egress policy; `imagecheck.py` interprets the Dockerfile and runs the 3 shipped programs: clean |
| No answer leaked into agent image | pass (host trial) | answer-key probe reads `/tests/seal` and the nonce only as PermissionError under uid 1002; `extraneouscheck`/`leakcheck --self` sanity ran |
| `harbor run -a oracle` = 1 | pass (host trial) | `host_trial.py oracle` reward 1 (44 passed); real Docker unavailable, host emulation used |
| `harbor run -a nop` = 0 | pass (host trial) | `host_trial.py nop` reward 0 (worker times out on scale) |
| Cheats all score 0 | pass | `host_trial.py`: oracle 1, nop 0, 6 probes 0; `cheat_report.py`: 45 cheats, 0 flagged, each caught by the layer named for it; both correct variants score 1 |
| `tracecheck.py` (every graded assertion traced) | clean | |
| `preflight.py` | no errors | 11 unused-public-function warnings are the package false positive (frame calls hold.*, hold calls lay/stick/pick, etc. via cross-module attribute calls); 1 warning is the ledger entry added at packaging |
| Gate/kit tools | pass | difficultycheck 100/IN BAND, originalitycheck 100/DISTINCT, hintcheck none, textcheck (short-sentence advisory only; contraction/first-person findings are possessives and the index metavariable `I`), structcheck none, catcheck none, deadfieldcheck clean, extraneouscheck clean, onelinecheck OK, readingcheck 0 blind, simcheck conceptual-distinct (Dockerfile boilerplate only), forgecheck pass, solvecheck clean, imagecheck none |
| `harbor check` rubric | not run remotely | Docker unavailable; the criteria are walked by hand below and by the kit gates above |

## Quality review self-check (docs/QUALITY-REVIEW.md, walked 2026-09-22)

- Instruction <-> verifier agreement: every graded assertion traces to a quoted sentence
  (`tracecheck` clean); every promised behaviour is tested (13 decisions, 39 cases, 390+6
  generated); the four artifact paths are named with absolute paths; the output schema
  (`<n> <offset> <word>`) is stated; boundaries are settled (half-open rows, strict stick
  comparison, offset 0 held, clamping into the post-edit range, ties by smallest offset then first
  pass); no two readings that fit the published evidence disagree on the graded set
  (`readingcheck`), the dumb strategies score 0, and the 90 s clock is validated by two independent
  implementations.
- Instruction prose: the switch paragraph's opener run was broken (two sentences reworded, their
  trace quotes updated); each requirement is stated once; cadence measured against a passing brief
  (`textcheck`: burstiness 0.85 vs 0.88, model-tells 0; the residual short-sentence advisory is the
  only finding, and the earlier first-person and contraction findings were the index metavariable
  `I` and ordinary possessives).
- Verifier rigor: the grader never runs agent code, reads the worker's record defensively, recomputes
  truth from the sealed model, and checks the program file's sha; tests are deterministic (a seed
  fixed by test.sh, no wall-clock or network dependence in grading).
- Environment hygiene: neither `tests/` nor `solution/` is copied into the agent image
  (`environment/Dockerfile` copies `app_src/` only; `extraneouscheck`/`imagecheck` confirm); pytest
  is pinned with `==` in `tests/Dockerfile`; no dangling names (`imagecheck` runs the shipped
  programs).
- Solution quality: `solution/solve.sh` copies the four modules into place and runs the programs
  through the real driver - it computes, it does not echo answers; it uses nothing the agent could
  not.
- Anti-cheating: the answer is not in the tree (the shipped modules implement the wrong plan; the
  change log stores only edit kinds and ids; no pass count, band or distance is printed); a
  constant or first-box output fails; the forgery carrying gt.json scores 0 on the post-seed
  population; the six isolation probes score 0.
- Metadata: `category = Software`, `subcategory = Frontend` (a label in that row); five specific
  tags, none restating the category; `difficulty_explanation` names the concrete step
  (the mid-settle fallback and the band fixed point) and states the legacy-register naming as a
  design choice; `solution_explanation` and `verification_explanation` describe the real method.

## Open questions and next steps

Stage 7 remaining: package with `scripts/package.py`, run `tools/zipcheck.py` on the archive,
add the ledger row to `authoring/submissions.toml` (verdict `pending`), walk the quality review
criterion by criterion, check for stray `__pycache__`, then commit and push to
`claude/scroll-anchoring-mutations-sticky-3slrop`. No PR unless asked.

Cheat inventory (45): 33 wrong readings (each caught by its enumerated case), 2 exact-but-slow
families (full-relayout, scan-headers; caught by the 90 s clock), 3 dumb shortcuts (const-lines,
pos-first-box, replay-small; caught by the enumerated grading), 1 forgery carrying gt.json
(caught by the generated population), 6 isolation probes (answer-key, privilege, shrink-set,
late-reward, forge-report, crash-worker; all reward 0 under the two-container host trial). The
emitters are `emit.py`, `emit_shortcuts.py`, `emit_forge.py`, `emit_probes.py`; the attribution
report is `cheat_report.py`; re-run `emit.py` after any change to `readings.py` or the reference.

Note on the verifier files: `tests/reap.py` and `tests/test.sh` were rewritten in this session
to be this task's own expression (they had been too close to `expert-defer-shed`); behaviour and
all paths are unchanged, `simcheck` now flags only the shared Dockerfile boilerplate, and the
oracle still scores 1.
