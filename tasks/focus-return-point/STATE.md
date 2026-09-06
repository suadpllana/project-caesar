# focus-return-point

## Current state

Canonical retained task, promoted from the final render-transaction release on 2026-09-06.
The contributor reports that this version passed the easiness probe. The exact solve count and
the final probe trajectories are not present in this checkout, so the pass is recorded as
contributor-supplied evidence rather than reconstructed local evidence.

Category: Software / Frontend. Four editable artifacts, an 8-hour expert estimate, and a
14400-second agent allowance. No upstream repository was supplied or used.

## Verifier contract

The editable artifacts are:

- `/app/ui/focus.py`
- `/app/ui/keep.py`
- `/app/ui/reach.py`
- `/app/ui/mem.py`

The verifier compares the exact focus trail after every event and scores all cases
all-or-nothing. It has 89 literal histories, including 21 render-transaction histories, plus
300 general, 300 nested-scope, 150 id-reuse, and 300 render histories from versioned seeds.
The sealed flat-handle model must reproduce every literal trail before generated answers count.

Submitted code runs as an unprivileged uid in a pristine runtime with only the four artifacts
overlaid. The reward defaults to zero and remains root-owned. Frozen runtime hashes,
instrumentation, worker status, survivor cleanup, and the final report are checked before the
trusted grader awards a pass. The grader does not import submitted code.

## Difficulty argument

Why a frontier agent cannot one-shot the plan: neither of the two natural timing models is
correct. Applying every event immediately loses focus and mutates navigation memory during
transient renders. Deferring every event binds requests to replacement widgets, replays tree
mutations that already happened, and loses rollback history. Correctness requires a hybrid:
tree edits are immediate; focus intents bind to the current object instance; their effects wait
until the outer commit; abort restores the original objects and the matching deletion history.

That timing split interacts with three other systems:

- nested render frames, where an inner commit survives only until an outer abort;
- widget id reuse, where current name lookup and historical object identity must stay separate;
- navigation scopes, where Tab, arrows, group selection, modal returns, and per-composite branch
  memory have different boundaries.

Tactics making that true: A1, A3, B2, C1, and C4. B1 is deliberately not claimed: this is a compact toolkit and
fits in a few reads. Its difficulty comes from interacting rules that change one another's
meaning, not from file count or scenery. The route-around is blocked by the four-artifact overlay,
frozen runtime checks, and exact event trails.

Assistant's attack on the plan: a controller that journals all events is wrong because mutations already took
effect. A controller that journals only focus calls is still wrong unless requests retain object
identity, frame boundaries, and deletion records. That plan can look correct through ordinary
modal and navigation cases; the stale deletion position becomes visible only after an aborted
widget is restored, moved, and later loses a different ancestor.

Probe history: two earlier, smaller versions were each solved by two of three agents after a
two-read rewrite. The first added nested navigation, and the second added id lifetimes. Those
features entered the agents' first plan. The final version changed the planning problem by adding
nested render transactions and the binding-time/evaluation-time split. The contributor reports
that this final version passed.

Estimated solves out of 8: the exact count is unavailable; the contributor reports that the final
version landed inside the accepted easiness band.

## Expert path

Read the runtime snapshots and confirm that tree edits happen before the policy callback. Preserve
instance-bound focus intents and deletion positions in nested frames. On abort, restore the frame's
original objects and discard only that frame's pending effects and positions. On the outer commit,
validate retained focus, then replay intents in issue order against the final tree. Resolve modal
returns, group representatives, and composite branch memories by object lifetime and the correct
navigation scope, not by the latest widget id.

## Evidence retained

- 89 literal trails agree with hand derivations, the runtime reference, and the independent model.
- Reference and model agreed on all 1139 graded histories and 2000 additional render histories.
- All 68 pre-render literal outcomes were preserved.
- The pre-render reference fails 18 of the 21 render examples.
- Eight focused semantic mutations were rejected by the local runner and pytest suite.

These measurements establish behavioral separation and solvability. They are not a substitute for
the external solve-rate result. Docker, Harbor, and Linux isolation checks were unavailable on the
authoring host when this version was built; do not restate those gates as locally run.
