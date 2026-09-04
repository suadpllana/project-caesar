# Task state

Working memory for `alias-settle-report`. Never ships: `package.py` drops it and no pipeline
gate reads it. It exists for the next session and for `preflight.py`.

## Current stage

`Stage 7 - gates`, on a **Stage 2 redesign of the mechanism** made 2026-09-04.

The first build cleared the structural check, the AI screen, the similarity screen and
reference verification on 2026-09-04; failed the quality review on `category and tags` and
was relabelled `Software / Algorithms`; then **failed the easiness probe 3 of 3** the same
day, in 2 to 7 minutes a trial, one correct write each followed by a self-built oracle.
Mode C: the graded question was a decidable predicate under a stated transition table, so
the definition was the rule and a complete specification was a brute-force oracle. No leak
patch applies to that; the mechanism had to change. Trajectories at
`probes/alias-settle-report/`.

What changed: **a line handed to the board takes its item off the desk**, and a tag says
nothing further about an item that has gone. The settling question is therefore no longer a
predicate over the visible state - the set of legal continuations now depends on the
policy's own filings, and the answer is the least self-consistent set of departures per
tick. See "The redesign that answered the mode-C rejection" in CLAUDE.md.

## Task summary

`Software / Algorithms`. The tree under `/app` is the filing end of an evaluation harness -
the setting is narrative, and the graded skill is a fixed point over a reachability question
under disequality constraints, which is what the category has to name. Runs post scores for
items under keys; matchers declare that two keys are one item, or that two keys are not; a
board must be handed exactly one line per key it watches, carrying the smallest key in that
key's item and the score of the first post the item holds. The graded decision is WHEN each
line may be written: at the first tick at which nothing that could still happen would move
it, and not before. Both directions are graded, so an eager policy and a conservative one
fail alike.

## Why it is hard

Three corrections, and the third invalidates the natural implementation of the second.

1. The question is about futures, not the present. Stated in the brief; an agent gets there.
2. Welding a chain welds every item on it into one, so a difference standing anywhere inside
   that group forbids the whole route. The condition is "is there a path whose entire vertex
   set is free of differences", a search over growing groups rather than a walk over edges.
3. **A filed item leaves.** So the cells that could still be welded on are not the cells
   standing now - they are the cells still standing once this tick's lines have gone, and
   which lines those are is the question being asked. Reach cannot be computed once from the
   book and consulted; it has to be answered against a set of departures that is itself being
   solved for, and the answer is the *smallest* self-consistent set, never the largest.

Measured against the reference on 400 generated sets:

| reading | sets it moves |
|---|---|
| the largest self-consistent set instead of the smallest | 87% |
| plain edge walk, no groups | 84% |
| differences ignored | 69% |
| a departed item still in reach | 46% |
| the difference checked between consecutive steps | 32% |
| only departures already recorded, so no line ever frees another on the same tick | 21% |
| the difference checked against the two ends of the route | 1% |

The rule all three probe agents wrote against the previous build, ported to the current
signature, scores **0**: wrong on 4 of the 33 enumerated sets and 48% of 200 generated ones.
It ships as `cheat-mistake-the-rule-that-beat-the-old-build`. All five `ok-*` variants still
score 1.

The agent's own check confirms the wrong answer rather than failing to reach it: an
enumeration of what the sources could still do has to know which items have left, which
depends on the policy under test, so it agrees with any policy that agrees with itself.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan every retrieved source supports is union-find plus plain reachability, which is right on every set carrying no difference and wrong on most of the rest, and the correction on top of it - that reach is a function of a departure set being solved for in the same breath - has no textbook shape at all; nothing the agent can run tells it so, because a self-built continuation oracle is driven by the policy under test and confirms whatever that policy does.
- Tactics making that true: prong A, A1, A2, prong B, B1, prong C, C1, C2, C4. The memorised dedup plan is a union-find and a closure and it is specifically wrong here; the concept is never named; the rule lives in behaviour spread over the book, the machine and the sweep with no comment anywhere; a wrong reading files a plausible trace and only the verifier disagrees; four must-still-work fences make overshooting fail too; three hundred sets are built from a nonce after the agent stops.
- Assistant's attack on the plan: my first plan was to mark every cell an open tag can reach,
  take the smallest key and the earliest post over that set, and file when neither beats what
  stands. That plan is wrong twice over. It treats the differences as noise when they bound
  which chains are possible; and it reads the reach off the book as it stands, when the book
  as it stands includes items that are leaving on this very tick.
- Estimated solves out of 8: 2 of 8, aimed at 1 and expected to drift up.
- Difficulty score anchor: not yet anchored - the first build was rejected on easiness before
  reaching the difficulty probe.
- Score history: 2026-09-03 built; 2026-09-04 quality review rejected on category, relabelled;
  2026-09-04 easiness 3 of 3; 2026-09-04 redesigned.
- Leak audit: no comment, docstring or `.md` file under `environment/`; `tools/deadfieldcheck.py`
  reports nothing written and never read - `bk.gone` and `bk.drop` are both read by `mc.step`
  and `mc.sweep`; the brief states the machine's behaviour and the input space and never the
  rule; `tools/hintcheck.py` and `tools/structcheck.py` are clean; the three shipped sets carry
  no expected output and `gt.json` is root-only in the verifier image. The brief's one worked
  exhibit fails on a stated rule (an earlier post in a reachable item), not on any of the three
  corrections, so grounding it gives none of them away.
- Expert path, described step by step: read `bind/mc.py` to see that the sweep asks
  `hold.firm` per watched cell each tick, and that a filing calls `bk.drop`; read `bind/bk.py`
  and `mc.step` to see what `gone` then does to a later declaration; establish from the brief
  that the line has two halves and that either can move; work out that a still-open tag makes
  any two cells it touches one declaration apart and that chains compose; write the reach as a
  closure and watch the fences fail; realise that a chain welds its whole vertex set and that a
  difference anywhere inside it forbids the route; rewrite the reach as a search over growing
  difference-free groups; add the pending-post half; then find that a cell which is going this
  tick cannot weld onto anything, that this is what frees the next line, and that assuming
  everything which looks ready is going over-files badly; settle the tick as the smallest
  self-consistent set.
- Originality check: searched for public write-ups of record linkage with disequality
  constraints under an earliest-safe-decision rule. Union-find with disequality is written up.
  What is not is the question this task asks: when a canonical name is final, given that the
  merges still to come are bounded both by the differences already declared and by which names
  are being finalised in the same breath.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/bind/rch.py`, `/app/bind/hold.py`, `/app/bind/card.py`,
  `/app/bind/seq.py`.
- What is checked: the ordered rows the machine emitted, exactly, per set; and the filing table
  the machine collected beside them, as a cross-check. 33 enumerated sets plus 300 generated
  from `RUN_NONCE` inside the verifier container. Four attestations: the executed tree against
  the pristine copy, the sealed machine functions against digests compiled from the pristine
  sources, the interpreter's emitter count against the row count with the instrumentation still
  armed, and the run nonce.
- Tolerances: none. All or nothing.
- Ground truth, and where it lives: `tests/gt.json` for the enumerated sets, written by
  `authoring/build_gt.py` from `tests/oracle.py` and only after the reference and the model
  have agreed on 900 generated sets. The generated sets are graded against the model directly.

## Decisions and their reasons

- Posts always land, including for a key already handed over. Only the tags are told to stop.
  If posts were refused too, whether a watched key ever got its post would depend on the policy
  under test, and `tests/gen.py` must not run the machine, so the input-space guarantee that
  every watched key is posted for could not be maintained.
- `mc.sweep` takes one pass, computing every line's contents before any item is dropped. It
  does not iterate. Iterating there would hand the fixed point to the submission for free; and
  computing the contents first is what lets two watched keys on one item each earn their line.
- The interpreter's counts of entries into `span`, `firm`, `card` and `queue` are floors, never
  equalities, because `authoring/variants/ok-reach-inline` folds the reach search into the
  readiness test and enters `span` zero times.
- `card.py` and `seq.py` ship correct. The brief says not all four need changing; establishing
  which is part of the work.
- Three readings measured dead and deliberately not shipped as cheats: a departed item cut from
  the answer but still available as a route, a tag pool not stripped of departed keys, and
  retiring the watched key rather than its whole item. All three are unreachable under the
  stated input space rather than merely rare, so the matching branches were taken out of the
  reference instead - the ground truth came back identical, which is what says the removal was
  behaviour-preserving.

## The second quality-review rejection, 2026-09-04

`no extraneous files`, on the redesigned bundle, with every other rubric row passing
including `difficult`, `anti cheat robustness` and `category and tags`. The `authoring/`
directory is development tooling nothing in the build, run, solve or verify path requires.

Fixed by not shipping it: `tools/packbundle.py` stages the tree without `authoring/` and hands
the staged copy to the kit's `package.py`. 111 entries became 72. The extracted archive, with
no `authoring/` in it at all, was rebuilt into both images and scored oracle 1 (738 tests) and
nop 0, which is the check that matters. `tools/zipcheck.py` now fails any archive shipping the
directory.

Two real defects the reviewer found inside it, both now fixed: `readings.py:reductions()`
computed `keep` and immediately overwrote it, and `readings.py` duplicated `emit.py`'s mistake
definitions. `readings.py` now derives them from `emit.MISTAKES`, which also took
`readingcheck` from 16 readings to 18, all separated.

Four prose references in the SHIPPED files pointed at `authoring/` and were reworded, since a
bundle that names a directory it does not contain has a fresh complaint waiting.

Note the criterion has run-to-run variance: `guard-mark-unwind` shipped 35 authoring files and
`share-register-screen` 40, and both cleared this same review. The repair removes exposure; it
is not proof of what decided this one.

## Gates run

The real two-image trial on this Linux sandbox with Docker up: **32 of 32** (oracle 1, nop 0,
thirty cheats 0) and **5 of 5** variants at reward 1, 738 tests apiece. Every mistake cheat
fails a handful of row tests rather than dying on an import, and `all-that-look-ready` fails
431 of 738. `forgecheck` 30 of 30 with the answer-key probe recognised and scoring 0.

Host gates: `sync`, `build_gt` (900 sets), `fuzz` (600), `emit`, `make_variants`,
`variant_check` (5/5), `readingcheck` (16/16 separated), `onelinecheck` (no exact rule at
depth <= 2 for the filing decision), `deadfieldcheck`, `catcheck`, `solvecheck`, `hintcheck`,
`structcheck`, `textcheck` (clean against four briefs that passed the AI screen),
`determinism` (three hash seeds), `tiecheck` (433 sets), `simcheck` (no shipped file close to
another bundle's; conceptually clear), `preflight` (no errors), `normalise`, `package`,
`zipcheck` (111 entries, none), `zipfix --check` (every entry Unix).

## Gates NOT run

**The three-agent local probe.** The task owner asked on 2026-09-04 that probes not be run,
because they consume the account's usage. The redesign is therefore justified by measurement
of the wrong readings rather than by a probe result, and that is a real gap: no agent has been
put in front of this build. Run it before resubmitting if the budget allows.

`harbor check` (harbor is not installed here).
