# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`, after a human-review rejection and its repair. The bundle
submitted on 2026-09-10 passed every automated gate (structural, AI check, similarity,
reference verification, quality review) and was rejected by human review on the verifier's
output channel. The repair of 2026-09-18 is below under "Human review 2026-09-10". The
contributor's instruction for that repair was to fix only the rejected point and not to touch
difficulty; the difficulty evidence that instruction leaves standing is recorded honestly in
"Why it is hard" and in "Open questions".

This folder is the submitted bundle, unpacked verbatim from the archive the platform judged,
with the repair applied on top. A later revision of the same task exists on the branch
`claude/rename-repair-orderbook-engine-oj2qz5` (two difficulty rebuilds of 2026-09-09: a firing
is never taken back, and a same-participant pull inside a failed whole stands). It was never
submitted, and none of it is in this folder.

## Assistant's assigned role

Assigned by the contributor 2026-09-07, verbatim: "You are a senior exchange-infrastructure
engineer; you have spent years inside single-threaded matching engines, order-book data
structures, and the rulebook corner cases that only show up in production replays."

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, authored engine under `environment/app_src/`.
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable.
- Contributor's relationship to it: n/a
- License, and why vendoring it is permitted: n/a
- Pinned commit vendored into environment/app_src/ (.git stripped): n/a
- Load-bearing couplings found during research (file paths): n/a
- Identifier degradation done? n/a - the tree is authored in the legacy register from the start.
- Proper-noun sweep done? The tree carries no venue, vendor or product names by construction.
- Upstream-diff check: n/a

## Task summary

`/app` is a single-instrument matching engine: `mkt/` is the frozen driver, book, reader and
emitter; `eng/` holds five editable decision modules, four of which ship wrong. A session file
is a list of `new`/`pull` messages under a `cap` band, a `mark` price and a `pace` selector;
`/app/run_book.py` replays one and prints an event line per fill, cancellation, disclosure and
activation, then the resting book. The agent repairs shown-slice disclosure, the moving band,
same-participant cancellation, all-or-nothing (`whole`) admission with restoration, and
parked-order firing under order pace and fill pace, so that every event row and the closing
book match a sealed model on 55 named sessions, 300 nonce order-pace sessions, 120 nonce
fill-pace sessions and five large ones, inside a 300-second worker limit.

## Why it is hard

The naive walk - take the opposite side best price first, fill each resting order, then look at
the parked orders, count capacity before an all-or-nothing order - is coherent and right on
ordinary sessions. The stated rules make it wrong in ways that change the shape of the walk
rather than adding a case to it, and fill pace then makes the read-only admission count that
is exactly right under order pace wrong.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the walk mutates the
  queue it is walking - a partially shown order rejoins the back of its own level the moment
  its shown part empties, and a same-participant resting order is pulled out from under the
  walk without moving the last price - so the iteration cannot be over a snapshot of the level;
  all-or-nothing admission needs the outcome of that same walk without any of its effects; and
  under fill pace a fired order runs inside the interrupted one, consuming or supplying the
  capacity it needed and moving the band it resumes against, so admission cannot be decided
  before the walk and a failed whole has to undo its descendants' work while a failed child
  keeps its own firing.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C3, C4. A1 - the
  retrievable plan (a price-time walk over a level list, fill each resting order, scan the
  stops afterwards, count capacity first) is specifically wrong. A2 - the concepts are stated
  as venue behaviour and never named; iceberg, self-trade prevention, fill-or-kill and
  limit-up-limit-down appear nowhere. A3 - a walk that mutates what it walks and an admission
  that needs its outcome without its effects, in both paces, have no single technique. B2 - six
  rules that change each other's meaning. C1 - both sides fenced by named cases. C2 - no
  oracle; the brief quotes only wrong printouts. C3 - two measured scale boundaries under a
  stated 300 s kill. C4 - exact all-or-nothing streams against a sealed model on nonce
  sessions.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): levels as a
  dict price -> deque; walk the opposite side in price order; fill min(remaining,
  resting.remaining) and pop when empty; after the incoming order finishes scan the parked list
  for anything tripped; for all-or-nothing sum the opposite side up to the limit and reject if
  short; under fill pace run fired orders when the parent finishes. Wrong in five places: the
  fill is bounded by the shown size and the order requeues; the count ignores same-participant
  pulls and a band that steps with the fills; the parked orders are asked after every fill, in
  arrival order; fired orders run before the parent continues under fill pace; and a static
  count cannot see what a child consumes or supplies. The version I would write first passes
  both shipped sessions.
- Estimated solves out of 8: 8 - evidence, not a design aim. The platform's run audit on this
  exact bundle scored 3 of 8 with reward 1, and the other 5 had the semantics right and were
  failed only by the undocumented sink rule this repair removes (`RuntimeError('sink')` with
  exact rows otherwise); the local easiness probe on the bundle with the sink rule documented
  came back 3 of 3 (branch `claude/rename-repair-orderbook-engine-oj2qz5`,
  `probes/repair-orderbook-engine/`). The design aim recorded at Stage 1 was 3. The contributor
  instructed that difficulty not be touched in this repair; the rebuilt rules that address it
  are on that branch and are not in this folder.
- Difficulty record score (tools/difficultycheck.py on authoring/<slug>/difficulty.toml):
  transcribed 2026-09-18 from this file, the metadata, the cheat headers and the verifier
  docstrings; 94 before the hard stop, capped at 40 by `estimated_solves = 8`, which is the
  honest current number above and not the design's.
- Difficulty score anchor: not assigned
- Score history: 2026-09-07 created as `slice-trip-fill`; 2026-09-09 quality review failed
  `task name` only, renamed; 2026-09-10 submitted (84 files, 166.4 KB), structural, AI check,
  similarity, reference verification and quality review passed; run audit 3 of 8 solved with 5
  correct-but-refused on the sink rule; human review rejected the same day: "The verifier
  rejects correct buffered output because it requires Emit.row as the immediate caller - an
  undocumented restriction. A one-line routing change restores exact matches across all
  sessions. Document and demonstrate this requirement, or accept equivalent output paths, then
  rerun calibration."; 2026-09-18 repaired, below.
- Leak audit (docs/DIFFICULTY.md): (1) nothing in the tree is a function of the correct
  trajectory - no expected output ships, the brief quotes only WRONG printouts, no row count or
  digest of a correct run appears anywhere; (2) no stored derived quantity - `Ord` carries qty,
  shown size and remaining, all primitives; (3) no unused affordance - `Side.rear` was one and
  was deleted; (4) no manifest - `sess/` is five files found by listing a directory; (5) no
  self-labelling data; (6) no oracle - the engine prints what its own rules produce. Answer:
  nothing. `extraneouscheck`, `hintcheck`, `deadfieldcheck` clean on 2026-09-18.
- Expert path, described step by step: see the `Expert path` section below
- Originality check: searched 2026-09-07. Matching-engine architecture and the order-type
  vocabulary are public; no page describes a rulebook combining a shown-size requeue mid-walk,
  a same-participant cancellation that leaves the last price alone, a band from the last fill,
  activation per fill in arrival order and nested all-or-nothing rollback under fill-boundary
  execution of fired orders.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/<slug>/trace.md; rows walked, NOT STATED left, tracecheck result): 19 test functions, 55 enumerated cases, 5 artifacts, the 300 s clock, the sink and 27 model rules walked into `authoring/repair-orderbook-engine/trace.md` on 2026-09-18; one NOT STATED found - the sink's caller rule, which human review had already named - and closed by removing the rule and stating the output channel; `tools/tracecheck.py` clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 18 whole-engine readings, every one a shipped cheat, each ruled out by a quoted sentence and separated by the enumerated case named in the trace (`tools/readingcheck.py`: 18 separated, none blind; `cheat_report.py` asserts the named case for each). Two readings the published evidence does not rule out are correct and are held as variants that must score 1: admission by walking and restoring in both paces (`ok-undo-log`), and held-back rows committed straight into the sink (`ok-sink-replay`, `ok-relay-emitter`).
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): `authoring/repair-orderbook-engine/shortcuts.py` at the graded scale of 480 sessions - nop 0 (84 exact), a silent engine 0 (34), the previous reference from before fill pace 0 (351), rest-what-a-whole-could-not-fill 0 (87), gt.json replayed 0 (92).
- Independent implementation behind every tolerance and limit (path, measured headroom): the 300 s worker clock is the only limit; six correct variants under `authoring/repair-orderbook-engine/variants/` run the whole plan in 10.2-14.6 s on a 4-CPU host under Python 3.12, the reference in 10.4-11.3 s, `test.sh` verbatim with the privilege drop 14.9 s including grading - twenty-fold headroom.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run on 2026-09-18 against every graded output; the one decision the text left open was how a printed line reaches the grader, settled by the two sentences on `out.row` and the sink in paragraph 3; every convention (index base, at-or-above versus above for trips, ties by arrival, empty pulls, `-` for none, `mkt`/`part`/`whole` reasons, final-book order) is settled by a sentence quoted in the trace.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-07. Revised once, on 2026-09-18, on the contributor's instruction relaying the
human reviewer's stated option ("accept equivalent output paths"): the event sink accepts a
committed row from any caller. That is a change to how a row reaches the grader, not to what
a correct stream is.

- Artifacts the agent produces: `/app/eng/take.py`, `/app/eng/shown.py`, `/app/eng/hand.py`,
  `/app/eng/hold.py`, `/app/eng/trip.py`. They are overlaid onto a pristine copy of the tree;
  one the agent never wrote simply is not there and the shipped file stands.
- What is checked: the ordered event stream and closing book of every session, exactly - 55
  enumerated (`tests/cases.py`, expected rows in `tests/gt.json`), 300 nonce order-pace
  sessions in five shaped families, 120 nonce fill-pace sessions, four large sessions in two
  shapes and one large fill-pace session, all against `tests/oracle.py`. Integrity: the tree
  outside the five artifacts byte-identical to pristine; sealed function fingerprints at import
  and after each session; the interpreter's count of entries into the sink equal to the row
  count with the instrumentation still armed; `walk`, `avail`, `blocks`, `admit` and `check`
  each entered somewhere; the run nonce in the report; the worker and the reaper exiting 0.
- Tolerances: none. Exact integer and string comparison throughout.
- Ground truth, and where it lives: `tests/oracle.py`, an independent implementation of the
  rules, and `tests/gt.json` as a tripwire on it. Both root-only inside the verifier image.
- The scale bound is the wall clock on the run (300 s kill), never a duration compared in the
  grader.

## Expert path, step by step

1. Run the shipped sessions, read the printout against the stated rules, find the visible
   defects: a resting order handing over more than it shows, a walk that stops one level in.
2. Read `mkt/drv.py` and `mkt/bk.py` to establish what is sealed and that the work is the five
   files under `eng/`.
3. Bound the fill by the shown size and requeue the re-disclosed order at the back; notice the
   level mutates under the walk, so ask the book for its front on every pass.
4. Read the last price on every pass; confirm a same-participant pull leaves it alone.
5. Decide all-or-nothing admission under order pace with a read-only pass carrying a shadow
   last price, or walk and restore; under fill pace only the second works, inside a frame that
   restores descendants and keeps a failed child's firing.
6. Ask the parked orders after every fill and take the ones that fire in arrival order; under
   fill pace run that batch after the resting order's removal or disclosure and before the
   interrupted order continues.
7. Time `wide.txt` and `book.txt`; index the parked set by trip price and keep admission from
   copying the book.

## Human review 2026-09-10, and the repair of 2026-09-18

The rejection, verbatim: "The verifier rejects correct buffered output because it requires
Emit.row as the immediate caller - an undocumented restriction. A one-line routing change
restores exact matches across all sessions. Document and demonstrate this requirement, or
accept equivalent output paths, then rerun calibration."

What it was. `tests/runner.py` built the event sink as a closure that raised
`RuntimeError("sink")` unless the calling frame was `Emit.row`'s code object. A correct
engine that holds a whole order's lines back in a private buffer and, on success, hands each
buffered tuple to `out.sink` directly fails every fill-pace session with a successful whole,
and `test_the_run_completed` reports the run raised. Reproduced here before the repair with
`authoring/repair-orderbook-engine/variants/ok-sink-replay` (the reference with that one
routing change): reward 0, five tests failed, every other test passed. No sentence in the
instruction mentioned the sink. The platform's run audit had already reported the same defect
as `task specification` 5 of 8 before the human review.

Why the second option. The caller check had no anti-forgery value: agent code chooses a row's
cells whichever route it takes, so `out.row("trd", 0, 0, 0, 0)` and `out.sink(("trd", 0, 0,
0, 0))` are the same forgery, and both are caught by the sealed model on sessions that did not
exist when the submission was written. What the check graded was a routing choice, which the
verifier's own contract says is deliberately not graded. Documenting it would have preserved a
rule that fails correct work for no reason a reviewer could be given. Accepting equivalent
output paths removes the rule; the anti-forgery evidence is unchanged - nonce sessions, the
sealed model, the decision tally, the fingerprints, the row count against the interpreter's
count of entries into the sink.

What changed.
- `tests/runner.py`: `sink_for()` appends `tuple(row)` from any caller; the docstrings say
  why. No other verifier logic changed.
- `tests/test_outputs.py`: three docstrings no longer claim rows are refused by route.
- `instruction.md`, paragraph 3: two sentences state the output channel - everything printed
  is a call of `out.row` on the emitter the driver hands in, `run_book.py` and the grader
  collect what reaches the sink behind it and nothing else, and a held-back line may go out
  through `out.row` or be handed to the sink as the tuple `row` would have built.
- `task.toml`, `verification_explanation`: the sink accepts a committed row from any caller.
- `cheat/cheat-forge-into-sink.sh`: new probe on the shipped tree that hands a forged row
  straight to the sink on every walk; scores 0 by the session comparison. The header of
  `cheat-forge-rows.sh` no longer refers to the removed rule.
- `tests/gt.json`: byte-identical content, rewritten with LF - the submitted archive carried it
  CRLF, which the platform accepted and `zipcheck` would not.
- `tests/pristine/` and `environment/` unchanged.

Demonstrated. `ok-sink-replay` and `ok-relay-emitter` (a private emitter class of the
solver's own that commits its held rows itself) score 1 after the repair; both were first
written without a `sink` on the buffer and failed for their own reason, because a nested
whole's `out` is the parent's buffer, which is a property of a correct buffered
implementation and not of the verifier. `cheat-forge-into-sink` and `cheat-forge-rows` score 0.

## Decisions and their reasons

- 2026-09-07. Candidate chosen after attacking three; category Software / Algorithms rather
  than Operations / Finance because the graded work is queue maintenance, walk order over a
  mutating structure and an activation cascade.
- 2026-09-07. Stage 7 re-attack found every rule individually implementable from the brief and
  added the two measured scale boundaries (a parked-by-scan form over 400 s, a copy-per-order
  admission 192 s on one graded session) rather than more prose.
- 2026-09-18. The sink rule is removed, not documented (above). The instruction states the
  output channel anyway, because the contract requires the output location to be stated
  whether or not a route is refused.
- 2026-09-18. Difficulty is not touched, on the contributor's instruction. The evidence that
  the recalibration will come back too easy is recorded above and reported to them; the rebuilt
  rules on the other branch are the prepared answer if it does.
- 2026-09-18. `hand.py` still ships correct and the reference still ships no `hand.py`; the
  authoring tree builder falls back to the shipped module for any file a policy does not carry,
  which is what the verifier's overlay does.

## Validation status

Docker's client is present here but its daemon is not, so the two-image trial could not run.
Two host emulations stand in: `authoring/repair-orderbook-engine/trial.py` (the real runner
over the real plan, the real grader, no privilege drop) and `host_trial.py` (`tests/test.sh`
verbatim as root, with the uid-1002 drop, the root-owned reward channel, the /proc reap, on
Python 3.12 with the pinned pytest). Nonce sessions were regenerated for each run.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run (no Docker daemon) | `tools/imagecheck.py` assembled the image from the Dockerfile, dropped the reference in and drove all five shipped sessions: clean |
| No answer leaked into agent image | pass | leak audit above; `extraneouscheck`, `hintcheck`, `deadfieldcheck`, `catcheck`, `solvecheck` clean 2026-09-18 |
| `harbor run -a oracle` = 1 | host 1 | `trial.py oracle` 11.3 s; `host_trial.py oracle` 19 passed, 14.9 s |
| `harbor run -a nop` = 0 | host 0 | both emulations |
| Cheats all score 0 | pass (host) | 32 cheats; `cheat_report.py` asserts the catching layer for every one, the named hand case for the 18 readings; the three probes needing the privilege drop plus five more run under `host_trial.py`, all 0 |
| Correct variants score 1 | pass (host) | 6 of 6, including the two that commit through the sink directly |
| `readingcheck.py` | pass | 18 readings separated by the enumerated set, none blind |
| `tracecheck.py` (every graded assertion traced) | pass | clean, `authoring/repair-orderbook-engine/trace.md` |
| Reference vs sealed model | pass | `agree.py`: 1858 generated sessions in both paces plus the large shapes, 0 differ, 0 raised; `build_gt.py` rebuilt `gt.json` from both and it is content-identical to the submitted one |
| Shortcut strategies | pass | five strategies, all 0, `shortcuts.py` |
| `preflight.py` | pass | no errors; warnings are the retained author identity and the entry-point functions the driver reaches from outside the tree |
| `structcheck.py` / `textcheck.py` | pass | structure clean; cadence unchanged by the repair (burstiness 0.615 submitted, 0.617 now, against 0.79-0.88 in two retained briefs; the submitted brief passed the AI screen at that number) |
| `difficultycheck.py` | 40 (94 before the hard stop) | the stop is the honest solve estimate above, not the record's articulation |
| `simcheck.py` | as before | `tests/test.sh` 0.598 against `guard-mark-unwind`: the shared isolation architecture, left alone deliberately |
| `onelinecheck.py` | not run | `authoring/decisions.py` was written for the pre-fill-pace model and is not carried forward |
| `harbor check` rubric | not run | no provider API key |
| Packaged archive | pass | `scripts/package.py`, then `tools/zipcheck.py` and `tools/zipfix.py --check` |

## Quality self-review (docs/QUALITY-REVIEW.md, 2026-09-18)

Instruction <-> verifier agreement: every test function, enumerated case, artifact, clock and
model rule has a quoted sentence in the trace, and the one verifier requirement that had none
is gone. Prose: the two added sentences follow the brief's register (`out`, the driver, "the
run we grade with"); `structcheck` clean; the cadence numbers are the submitted brief's.
Verifier rigor: unchanged except that the sink no longer grades a route; rows are still
compared exactly against a sealed model on nonce sessions, the decision tally and fingerprints
still hold, and `test_instrumentation_intact` still requires the interpreter's count of sink
entries to equal the rows reported. Environment hygiene: unchanged; `environment/Dockerfile`
copies `app_src/` only. Solution: unchanged, computes everything. Anti-cheating: 32 cheats
score 0 with the catching layer asserted, including a new probe that pushes forged rows
straight into the sink. Metadata: `verification_explanation` re-derived; counts unchanged (55
named, 300, 120, four large, one large fill-pace, nineteen tests).

Known risks to flag: the recalibration is expected to come back above the band (evidence
above); the container gates did not run here; `tests/test.sh` sits at 0.598 mechanical
similarity against `guard-mark-unwind` on shared isolation plumbing.

## Open questions and next steps

- Resubmit the archive at `tasks/repair-orderbook-engine.zip`. The platform will rerun the
  calibration, as the reviewer said.
- If the recalibration comes back 8 of 8, the prepared answer is the rebuilt rulebook on
  `claude/rename-repair-orderbook-engine-oj2qz5` (STATE.md there, two recovery entries, 74
  named cases, 52 cheats, a journal variant), which carries the same sink repair in its
  documented form and would need this repair's form instead.
