# Task state: focus-return-point

Working memory for this task. Never ships, never a deliverable.

## Current stage

`Stage 7 - gates and self-probe` (built 2026-09-04 in one session from the accepted
proposal; not yet submitted)

## Assistant's assigned role

You are the engineer who owns the focus controller of a terminal UI toolkit: tab order,
modal screens, focus restoration after dialogs close, and everything that goes wrong when
the widget holding focus is removed under the user.

## Source repository

- Repo URL: none - idea-based task
- Seed: the focus-loss bug class in UI toolkits (browser engines' sequential focus
  navigation starting point; dialog restore-on-close stacks in Qt, Textual and design
  systems). Synthetic toolkit written here; nothing vendored.

## Task summary

A toolkit `ui/` with a frozen core (`core.py`, `decl.py`, `node.py`) and four editable
policy files (`focus.py`, `keep.py`, `reach.py`, `mem.py`). A script declares screens and
widgets and then fires events: keys, focus requests, screen push/pop, tree mutations. The
graded artifact is the trail: the widget holding focus after every event, or `none`.

## Why it is hard

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the plan every
  toolkit and every agent starts from is a stack of restore targets plus "start from the
  top" when focus is lost, and both halves are wrong here. Every deferred landing (return
  target, held request, lost place) is a question about the tree at the moment the landing
  happens, and a screen popped out of order leaves the screen above holding a target inside
  a screen that no longer exists, which a stack pops wrongly and a lazy per-screen record
  cannot resolve without chaining through the dead screen's own return. Twelve interacting
  stated rules ride on top, four of them needing state no single event supplies.
- Tactics making that true: A1, B2, C1, C2, C4 - the stack-and-top-of-form default is
  specifically wrong (A1); twelve rules interact under the same records (B2); every fence
  has a must-still-work side in the enumerated set (C1); no browser, no second
  implementation and no expected output in the tree (C2); 300 nonce-generated scripts,
  all-or-nothing (C4).
- Assistant's attack on the plan: my first plan is a screen stack storing the focused widget at push, an origin saved on removal, a pending request
  per screen, memory per composite - two hours to a green self-harness. Wrong in two places
  that matter: it converts a disturbed return target at the moment of the disturbance
  (wrong when it is enabled again before the pop) and it pops a stack (wrong on
  out-of-order pops). The self-harness confirms every stated rule and neither of those,
  because no script one thinks to write undoes a mutation under a push or pops from the
  middle.
- Estimated solves out of 8: 2 of 8, designed for the hard edge
- Difficulty score anchor: not yet scored
- Score history: none yet
- Leak audit: no field written and never read (`tools/deadfieldcheck.py` clean); no
  shipped validator; no manifest; no expected output; identifiers degraded uniformly
  (`fo`, `st`, `nd`, `kids`, `fl`, `grp`, `scr`, `keep`, `mem`, `reach`); the detached
  node keeps a stale `par` pointer, which is realistic and is what the reference reads a
  dropped descendant's place off; the drop index is passed on the event because the
  stated rule needs it. onelinecheck: the pop landing has no rule at depth 2; the group
  stop rule is short and is a stated rule with a cheat.
- Expert path: run the two shipped scripts, see focus fall to the first stop after the
  dropped row (1 h); fix reach and groups (1 h); write the lazy landing resolver over
  points, chained through dropped containers and dead screens (2 h); rebuild return as a
  per-screen record with held requests on top (1.5 h); composite memory and back symmetry
  (1 h); fuzz own reading of the brief and clean up (1.5 h).
- Originality check: browser focus-navigation-starting-point behaviour and dialog
  restore stacks are documented; no page describes this rule set (out-of-order pops
  chaining, lazy re-enabled targets, points that do not move) and there is no browser in
  the container to diff against.

## Verifier contract - FROZEN

- Artifacts: `/app/ui/focus.py`, `/app/ui/keep.py`, `/app/ui/reach.py`, `/app/ui/mem.py`
- What is checked: the trail of every script, exactly; 42 enumerated (gt.json, derived by
  hand in `authoring/handcheck.py` and re-proved by `tests/oracle.py`) plus 300 generated
  from the run nonce and graded by the sealed model after the run.
- Real work (graded): the trail. Implementation choice (never graded): record storage,
  point representation, number of tree consultations, policy entry count.
- Tolerances: none.
- Integrity: pristine-tree hash with file count asserted, compiled fingerprints of frozen
  functions, sink refusing any caller but `Ui.step`, `sys.monitoring` tally on `Ui.step`
  equal to the row count and still armed, nonce in the report.
- Ground truth: `tests/gt.json`, root-only, written by `authoring/build_gt.py` only when
  the reference, the model and the hand-derived trails agree.

## Reference timing

Reference on the 42 cases plus 300 generated scripts: about 4 s on this sandbox in the
runner (no speed regime; nothing is timed).

## Decisions and their reasons

- No speed regime: the difficulty is history-dependent semantics, not a resource gate.
- `held-applied-now` dropped from the cheat suite: a request that leaks focus onto a
  screen below records a return into the screen being pushed and the resolver loops
  forever; the reading is not one the brief invites.
- The policy-entry tally is not graded: a correct policy may re-enter its own `on`.
- `back` entering a composite lands on the memory (mirror of `tab`), stated in the brief.

## Gates

See the handover in the session reply and CLAUDE.md for what ran and what did not.
