# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

You are a storage engineer who works on the space accounting of a copy-on-write store: what a
snapshot is keeping alive, what a clone shares with the dataset it came from, which of the two
is charged for a block both can reach, and why a quota refused a write that would have paid for
itself. Comfortable deriving what a snapshot holds from the history of the cells it covers
rather than from a copy of them.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository)
- Contributor's relationship to it: not applicable
- License: not applicable
- Pinned commit vendored into environment/app_src/: not applicable
- Load-bearing couplings found during research: not applicable
- Identifier degradation done? The tree is authored, not vendored. Identifiers are in a legacy
  register by choice (`led/`, `cell`, `hold`, `cost`, `gate`, `free`, `rc`, `sc`, `froze`,
  `thaw`, `spread`); none misdescribes what it holds, and `task.toml` says so as a design choice.
- Proper-noun sweep done? No vendor, product or project name appears anywhere in the tree; the
  vocabulary (line, still, graft, lift, drop, cap, charge) is authored for this task.
- Upstream-diff check: not applicable - nothing upstream to diff against.

## Task summary

`/app` is the space ledger of a copy-on-write store. A line is a mutable image, a map from cell
to block; `put` lays a fresh block on every cell of a range, `cut` takes a range out of the head,
`still` freezes a line, `graft` starts a new line from a still, `lift` changes a graft and the
line it was grafted from around, `drop` drops a still, `cap` puts a ceiling on a line, and `ask`
and `at` are the two questions. `/app/run_log.py` runs a program of those ops and prints a line
per refused put, per drop and per question. The six files under `/app/led` decide what a still
holds, who holds a block, what a line is charged, what a lift moves, whether a put fits its cap
and what a drop releases. Five of them ship a rule read the other way and the sixth ships the
right answers through a structure that cannot meet the limit, and the whole graded set has to
run inside a 60 second wall clock at sizes where the shipped structures cannot.

## Why it is hard

The charge of a line is the size of the blocks it holds that no other line holds, and "holds"
counts lines rather than places: a line with four stills over one block is one holder. A
reference count - the structure the tree ships and the one a first plan reaches for - answers
the other question. The repair that follows, a set of holder lines per block, is then spent by
`lift`, which moves stills from one line to another and so moves a charge with nothing written,
released or copied. And the structure that survives both is unaffordable if a still is a copy of
a map, which the stated scale forbids.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the first plan
  is the shipped one and is coherent: head maps, a copy per still, a count per block. It is wrong
  on the question the task is about (how many lines hold a block, not how many places), and the
  repair for that is then invalidated twice - by a lift moving stills between lines, and by a
  stated scale at which no still may be materialised at all. The plan that survives all three has
  to be derived from the rules, not retrieved: what a still holds is a window over a cell's
  chain, who holds a block is a question about still indexes and their current owners, and a
  charge is a running total settled at every event that can move one.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C3, C4, plus the guard.
  A1 is the prior: copy-on-write with a reference count per block, which is exactly wrong for the
  charge rule. A2 never names promotion, exclusive space or a version chain; the brief states
  behaviour. B2 is nine rules that interact: what a still holds decides who holds a block, who
  holds decides a charge, a charge decides whether a put is taken, and a lift moves all of it.
  C1 enumerates both sides of every fence - the puts that must still be taken, the drops that
  must still free. C3 is two measured scale families: a still that is a map dies on `wide`, a
  charge counted when it is asked for dies on `deep`. C4 grades 438 programs on exact traces,
  all-or-nothing, with the generated ones drawn after the agent is gone. The guard is the six
  editable files laid over the verifier's own pristine copy of everything else.
- Assistant's attack on the plan (its first plan, and where it is wrong): my first plan was head
  maps plus a copy per still plus a per-block reference count, with the charge read off the count.
  It is wrong at the first `ask` that follows a still, and the repair I would have reached for -
  a set of holding lines per block - is correct and unaffordable, because a graft and a still both
  have to touch every block they cover to maintain it. I could not have committed to the chain
  and window structure without first measuring what the copies cost.
- Estimated solves out of 8: 2 (designed for 1-3)
- Difficulty record score (tools/difficultycheck.py on authoring/still-graft-charge/difficulty.toml,
  before Stage 2): 100/100, in band on the first attempt, with one warning that the resource gate
  was not yet measured. The gate has since been measured and the record updated
  (`gate.measured = true`); the numbers are below.
- Difficulty score anchor (50 at first complete submission, approved by contributor): not set -
  this is the first submission of this task.
- Score history: 2026-09-17, 100/100 at Stage 1 (record written before any code); re-run at
  Stage 7 against the built tree.
- Leak audit (docs/DIFFICULTY.md): for each mechanism, what in the bundle could let an agent
  discover, name or verify it without reasoning?
  - The charge rule: nothing in the tree stores an owner, a holder set or a charged-to field.
    The shipped `Blk` carries `num`, `size` and two counts, all of which the shipped code
    maintains and uses; none of them is the answer.
  - What a still holds: the shipped still is a copy of the head, which is the naive structure and
    not the derivation. No file records a window, a birth or a death.
  - The lift: the shipped `tree.lift` moves the wrong set of stills, so reading it gives the wrong
    rule; the right one is only in the brief.
  - The scale boundary: `progs/wide.txt` and `progs/deep.txt` ship as inputs so the agent can time
    itself. They carry no expected output, and the brief states the limit and the sizes, so
    nothing here is hidden that the verifier grades.
  - No expected output ships anywhere in `environment/`; `gt.json` and the model are inside
    `tests/seal`, which `tests/Dockerfile` locks to root before the privilege drop.
  - The worked example in the brief was searched for rather than chosen: of the small programs
    whose shipped trace differs from the truth in exactly one line, `progs/tiny.txt` is one that
    decides only one of the nineteen wrong readings (`charge-refs`), and that rule is stated in
    the brief in any case.
- Expert path, described step by step:
  1. Run the shipped tree on `progs/tiny.txt` and `progs/pair.txt`, and find which of the six
     files decides each line of the trace.
  2. Replace the map per still with a chain per cell - block, the still counter it began at, the
     one it ended at - so that what a still holds is a window rather than a copy.
  3. Answer "who holds this block" from the entries it sits in: the line itself while an entry is
     open, plus the owners of the stills taken on that line whose index falls in the window.
  4. Keep the graft forest as an origin still per line and an ordered still list per line, and
     make a lift move the prefix, swap the two origins, and re-settle the blocks the moved stills
     were holding.
  5. Keep each line's charge as a running total settled at every event that can change a block's
     holders - a write, a cut, a graft, a lift, a drop - and never counted when it is asked for.
  6. Decide a put by letting the write stand and reading the charge, then taking the write back
     if it does not fit, so that what the put releases pays for what it adds.
  7. Run the shipped wide and deep programs against the clock before believing any of it.
- Originality check: searched for public write-ups of snapshot and clone space accounting on
  2026-09-17. What exists is vendor documentation for how a filesystem reports used, referenced
  and exclusive space, and what promoting a clone does to who is charged. That documentation
  describes a product's reporting, not this rule set: no page states a charge that counts lines
  rather than places, a lift defined as moving the prefix of a still list and swapping origins, or
  a quota measured against the charge a write would leave. The task is authored; the search test
  is answered in `authoring/still-graft-charge/difficulty.toml` under `[search]`.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace: 71 rows in authoring/still-graft-charge/trace.md, no NOT STATED left,
  `tracecheck` clean. 71 rows walked - every test function, all 27 enumerated cases, the 10
  top-level model branches, the six collected artifacts, the wall clock, the memory cap and all
  19 wrong readings. No `NOT STATED` rows remain; two decisions were unstated on the first pass
  and both were written into the brief (see the cold-reader line below).
  `python tools/tracecheck.py still-graft-charge` is clean.
- Identifiability: 19 readings enumerated, none survived the published evidence, each separated
  by a named case. 19 readings are written down and run in `authoring/still-graft-charge/readings.py`.
  Every one is separated by an enumerated case, and `readingcheck` names which: `cap-fit` for the
  two cap arithmetics, `put-number` for the number a refused put does not take, `cap-still` and
  `cap-cross` for the three charge readings, `lift-prefix` and `lift-swap` for the four lift
  readings, `drop-busy`, `drop-graft` and `cut-hold` for the four drop readings, `still-frozen`
  for the two still readings, and `cap-cross` and `cut-hold` for the two release readings. None
  survived, so no reading needed promoting to a correct variant.
- Shortcut strategies scored: nop 0, constant 0, positional 0, replayed example 0, and the
  fraction of cases each matches is below. The nop is the shipped tree and scores 0, matching 0 of 438 programs (it also fails
  the clock). A constant ledger that prints nothing scores 0 and matches only the programs whose
  correct trace is empty, which the enumerated set has none of. The replayed example is
  `cheat-forge-from-truth`, which carries the frozen answers to all 27 enumerated programs,
  reproduces every one of them, and scores 0 on the generated population it could not have seen.
- Independent implementation behind every tolerance and limit: the sealed model and the two
  correct variants, measured at 11x headroom under the clock. The only
  limits are the 60 second wall clock and the 2048 MB cap on the worker, and both are validated
  against `tests/seal/model.py`, written apart from the reference, and against the three correct
  variants under `authoring/still-graft-charge/variants/`. The reference settles all 438 graded
  programs in 5.2 s against the 60 s clock (11x headroom); the sealed model, which is slower by
  design, settles the same set well inside the verifier's own 900 s budget.
- Undecided decisions from the cold-reader pass: three, each given a sentence - whether a refused
  put takes a number, whether the cap comparison is strict, and whether a dropped still can be
  named again. The pass was author-run, mechanically, over every printed token. Two decisions were
  undecided by the first draft and each got a sentence: whether a refused put takes a number
  ("lays no block, takes no number, and leaves the line as it was"), and whether the cap
  comparison is strict at the boundary ("is at most the cap"). Two more were checked and were
  already settled: the range convention ("both included") and what `at` prints when the head
  holds nothing ("`at L k -`").

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/led/cell.py`, `/app/led/hold.py`, `/app/led/cost.py`,
  `/app/led/tree.py`, `/app/led/gate.py`, `/app/led/free.py`. Nothing else is read.
- What is checked: the exact printed trace of every graded program, line for line. 27 enumerated
  programs against `tests/seal/gt.json`, 411 generated programs against `tests/seal/model.py`,
  with the seed drawn after the agent's container is gone. The worker runs the whole set in one
  process under a 60 s wall clock; a run that does not finish scores 0.
- Tolerances: none. Every comparison is exact.
- Ground truth, and where it lives: `tests/seal/gt.json`, frozen by
  `authoring/still-graft-charge/build_gt.py` from the sealed model and checked against
  `authoring/still-graft-charge/brute.py`. `tests/seal` is root-owned and `chmod 700` before the
  privilege drop.

Graded decisions, nine of them, each with the sentence that carries it:

1. what a put lays and what the head stops holding
2. what a still holds, and that nothing later changes it
3. what a graft's head starts as, and how it diverges
4. who holds a block, and the charge that follows from it
5. what a lift moves and what it does to the two origins
6. what a drop is refused
7. what a drop releases
8. what a cap measures, and what a refused put leaves behind
9. what a cut stops holding, and what that releases

## Decisions and their reasons

- The charge counts holder **lines**, not places. That single choice is what makes the shipped
  reference count structurally unable to answer, and it is stated plainly in the brief.
- A still costs nothing to take. That is the invariant the fast path rests on: a still taken on a
  line adds no holder the line did not already have, so no block changes hands. It is not stated
  as a hint anywhere; it follows from the holder rule.
- `lift` moves the prefix of the still list and swaps the origins, so a line can become a graft of
  the line it was grafted from. That is what makes a charge move without a byte moving.
- The two scale families are separate on purpose: `wide` kills a still that is a map, `deep` kills
  a charge counted when it is asked for. A single family would have let one of the two naive
  structures through.
- The verifier lays the six submitted files over its own pristine copy, so nothing else the agent
  touched can change a trace. `authoring/still-graft-charge/sync.py --check` keeps that copy in
  step with `environment/app_src`.
- Host emulation, not containers: this machine cannot pull a base image (see Validation status),
  so the trials were run by `authoring/still-graft-charge/host_trial.py`, which runs the shipped
  `tests/test.sh` unchanged with the trees laid at `/app` and `/tests`.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run (blocked) | `docker pull` is denied by this session's egress policy: `production.cloudfront.docker.com` answers 403 through the proxy, so no base image can be fetched and neither image can be built here. `tools/imagecheck.py` interprets the Dockerfile against the build context instead: the image would hold 15 files, workdir `/app`, and the reference runs all four shipped programs from the assembled tree. |
| No answer leaked into agent image | pass | `extraneouscheck`, `hintcheck` and a read of every shipped file: no expected output, no `gt.json`, no model, no `.md`, no docstrings or comments under `environment/`. |
| `harbor run -a oracle` = 1 | pass (host emulation) | `host_trial.py oracle` -> reward 1, 30 tests passed, worker 5.2 s of the 60 s clock. Harbor itself is not installed here. |
| `harbor run -a nop` = 0 | pass (host emulation) | `host_trial.py nop` -> reward 0; the shipped tree is both wrong and over the clock. |
| Cheats all score 0 | pass (host emulation) | 34 of 34 trials behaved as required in one run: oracle 1, nop 0, and all 32 cheats 0, including three that are exactly correct and too slow and nine isolation probes. |
| Correct variants score 1 | pass (host emulation) | 2 of 2, after one of them had to be repaired: `ok-runs` first cut its per-line owner runs at every question and ran out the 60 s clock, which is the gate doing its job on a structure that is correct and O(stills) per holder query. Caching the runs until a still moves brought it to 20 s. |
| `readingcheck.py` | pass | 19 readings, every one separated by a named enumerated case. |
| `cheat_report.py` | pass | every reading caught by the enumerated program named for it, the three slow families measured against the limit, and the forgery reproducing all 27 enumerated programs and failing the rest. |
| `tracecheck.py` | pass | clean: 71 rows, no NOT STATED, every quote still in the brief. |
| `onelinecheck.py` | pass | no exact rule at depth two for the charge or for a refused put; what a drop releases has one, because a release is a refcount question. |
| `imagecheck.py` | pass | the image would hold 15 files at workdir /app, and the reference runs all four shipped programs from the assembled tree. |
| `catcheck.py` / `extraneouscheck.py` / `hintcheck.py` / `deadfieldcheck.py` / `solvecheck.py` / `structcheck.py` | pass | clean. |
| `simcheck.py` | pass on the conceptual axis | this task grades what no earlier one grades. The harness files (`test.sh`, `reap.py`, both Dockerfiles, the shape of `test_outputs.py`) are near-identical to the retained bundles, which is the repo's standard isolation shape: the retained bundles report the same similarity against each other. |
| `difficultycheck.py` at Stage 7 | pass | 100/100 with the tree measured rather than declared: 255 environment lines, 6 editable files, 401 reference lines. |
| `preflight.py` | pass | 0 errors; the 21 warnings are the same false-positive class the retained bundles carry (cross-module calls read as unused, and a `printf`-written reward). |
| `harbor check` rubric | not run | no API key in this session, and `harbor` is not installed. |

Measured, on this machine, with `authoring/still-graft-charge/timings.py`:

| implementation | correct? | whole graded set | wide | deep |
|---|---|---|---|---|
| reference | yes | 5.2 s of the 60 s clock | 0.46 s | 0.55 s |
| `ok-predict`, the cap decided by arithmetic | yes | inside the clock | - | - |
| `ok-runs`, holders off a per-line run list | yes | inside the clock once the runs are cut only when a still moves; over it when they were cut per question | - | - |
| a still that is a copy of the head (`slow-copy`) | yes | over the clock | 94.7 s, and 100.6 s on a second draw | 0.6 s |
| a charge counted when it is asked for (`slow-scan`) | yes | over the clock | 2.2 s | 1630.2 s |
| the first plan carried through (`slow-plain`) | yes | over the clock | did not finish inside 300 s | did not finish inside 300 s |

Each of the three unaffordable structures is exactly correct on everything it finishes, and each
is killed by one family and not the other, which is why there are two families.

## Cold self-attack

Not run, and recorded as not run. The order here was brief, then reference, then sealed model,
then environment, so by the time a scratch copy of the agent-visible tree existed the author had
written the answer three times over. A cold solve by this session would have measured memory.

What stands in its place, and what it is worth:

- the nineteen wrong readings in `authoring/still-graft-charge/readings.py`, every one separated
  by an enumerated case that names the rule it breaks;
- `tools/onelinecheck.py`, which finds no exact rule at depth two for the charge or for a refused
  put over anything the shipped tree exposes, and finds one for what a drop releases;
- the measured scale boundary, which kills two correct structures a solver could hold;
- the worked example, searched for rather than chosen, which decides one of the nineteen readings
  and that one is stated plainly in the brief.

None of that is a probe. The estimate of 2 solves out of 8 is a judgement.

## Open questions and next steps

- The container gates could not be run here. Everything that does not need a registry was run
  instead: the offline image interpretation, the real `tests/test.sh` on the host with the
  privilege drop and the reaper, and every cheat and variant through it. A session with registry
  access should run `python tools/docker_trial.py still-graft-charge --all` and
  `--variants` before submission, and nothing else is expected to change.
- No probe has been run against this task. The estimate of 2 solves out of 8 is a judgement, not
  a measurement.
