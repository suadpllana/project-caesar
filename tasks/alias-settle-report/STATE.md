# Task state

Working memory for `alias-settle-report`. Never ships: `package.py` drops it and no pipeline
gate reads it. It exists for the next session and for `preflight.py`.

## Current stage

`Stage 7 - gates`. Built end to end on 2026-09-03. Cleared the structural check, the AI
screen, the similarity screen and reference verification on 2026-09-04; failed the quality
review on `category and tags` and was relabelled `Software / Algorithms`. Every other rubric
row passed. See "The category rejection" in CLAUDE.md.

## Task summary

`Software / Algorithms`. The tree under `/app` is the filing end of an evaluation harness -
the setting is narrative, and the graded skill is union-find reachability under disequality
constraints, which is what the category has to name. Runs post
scores for items under keys; matchers declare that two keys are one item, or that two keys are
not; a board must be handed exactly one line per key it watches, carrying the smallest key in
that key's item and the score of the first post the item holds. The graded decision is WHEN
each line may be written: at the first tick at which nothing that could still happen would move
it, and not before. Both directions are graded, so an eager policy and a conservative one fail
alike.

## Why it is hard

The line can move two ways, and both are questions about futures rather than about the present.
A still-open tag can weld another item on, bringing a smaller key or an earlier post with it; a
still-open run can post ahead of the post that stands. Working out which welds are still
possible is the whole task, and the natural answer - reachability over the cells that open tags
touch - is wrong. Welding a chain welds everything on the chain into one item, so a declared
difference standing anywhere inside that group makes the whole route impossible. The question
is therefore not "is there a path" but "is there a path whose entire vertex set is free of
differences", which is a search over growing groups rather than a walk over edges. Measured on
400 generated sets: ignoring differences moves 63% of them, checking them against the wrong
pair of cells moves 15%, and both look impeccable on a set with a single tag in it.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan every retrieved source supports is union-find plus plain reachability, which is right on every set carrying no difference and wrong on a third of the rest, and nothing the agent can run tells it so, because the machine prints whatever rule it is handed and no expected output exists anywhere in the tree.
- Tactics making that true: prong A, A1, A2, prong B, B1, prong C, C1, C2, C4. The memorised dedup plan is a union-find and a closure and it is specifically wrong here; the concept is never named; the rule lives in behaviour spread over the book, the machine and the sweep with no comment anywhere; a wrong reading files a plausible trace and only the verifier disagrees; four must-still-work fences make overshooting fail too; three hundred sets are built from a nonce after the agent stops.
- Assistant's attack on the plan: my first plan was to mark every cell an open tag can reach,
  take the smallest key and the earliest post over that set, and file when neither beats what
  stands. That plan is wrong because it treats the differences as noise; they bound which
  chains are possible, and a policy that ignores them holds lines back that were settled ticks
  earlier, which is graded as hard as filing early.
- Estimated solves out of 8: 2 of 8, aimed at 1 and expected to drift up.
- Difficulty score anchor: not yet anchored - first submission.
- Score history: 2026-09-03, built, no pipeline result yet.
- Leak audit: no comment, docstring or `.md` file under `environment/`; no field records what a
  difference rules out; `tools/deadfieldcheck.py` reports nothing written and never read;
  `tools/onelinecheck.py` reports no exact rule at depth <= 2 for the filing decision over
  thirteen exposed features including the difference-blind reach; the brief states the input
  space and never the rule; the three shipped sets carry no expected output and `gt.json` is
  root-only in the verifier image.
- Expert path, described step by step: read `bind/mc.py` to see that the sweep asks `hold.firm`
  per watched cell each tick; read `bind/bk.py` to see what a tag pool and a bar actually are;
  establish from the brief that the line has two halves and that either can move; work out that
  a still-open tag makes any two cells it touches one declaration apart and that chains compose;
  write the reach as a closure and watch the fences fail; realise that a chain welds its whole
  vertex set and that a difference anywhere inside it forbids the route; rewrite the reach as a
  search over growing difference-free groups; add the pending-post half; check against the
  three shipped sets and against sets written by hand.
- Originality check: searched for public write-ups of record linkage with disequality
  constraints under an earliest-safe-decision rule. Union-find with disequality is written up;
  what is not is the question this task asks, which is when a canonical name is final given
  that the merges still to come are bounded by the differences already declared.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/bind/rch.py`, `/app/bind/hold.py`, `/app/bind/card.py`,
  `/app/bind/seq.py`.
- What is checked: the ordered rows the machine emitted, exactly, per set; and the filing table
  the machine collected beside them, as a cross-check. 29 enumerated sets plus 300 generated
  from `RUN_NONCE` inside the verifier container. Four attestations: the executed tree against
  the pristine copy, the sealed machine functions against digests compiled from the pristine
  sources, the interpreter's emitter count against the row count with the instrumentation still
  armed, and the run nonce.
- Tolerances: none. All or nothing.
- Ground truth, and where it lives: `tests/gt.json` for the enumerated sets, written by
  `authoring/build_gt.py` from `tests/oracle.py` and only after the reference and the model
  have agreed on 900 generated sets. The generated sets are graded against the model directly.

## Decisions and their reasons

- The interpreter's counts of entries into `span`, `firm`, `card` and `queue` are floors, never
  equalities, because `authoring/variants/ok-reach-inline` folds the reach search into the
  readiness test and enters `span` zero times while being correct.
- `card.py` and `seq.py` ship correct. The brief says not all four need changing; establishing
  which is part of the work.
- Every key the board watches is posted for at least once, and every source shuts before the
  set ends. Both are stated in the brief. Without them a line's existence would depend on the
  future and the obligation would not be well defined.

## Gates run

`sync`, `build_gt` (900 sets), `fuzz`, `emit`, `make_variants`, `variant_check`, `field_report`,
`cheat_report`, `determinism`, `tiecheck`, `normalise`, `docker_trial2 --all` (28/28),
`docker_trial2 --variants` (4/4), `readingcheck` (13/13 separated), `onelinecheck`,
`deadfieldcheck`, `solvecheck`, `forgecheck`, `hintcheck`, `simcheck`, `structcheck`,
`textcheck`, `preflight`, `package`, `zipcheck`.

## Gates NOT run

The three-agent local probe. `harbor check` (harbor is not installed here).
