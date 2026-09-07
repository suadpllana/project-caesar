# Task state

## Current stage

`Stage 7 - Pre-flight and packaging`, after a rebuild. Outstanding: `relevant_experience` in
`task.toml` still carries a DRAFT marker and needs the contributor's own words (D1).

## Assistant's assigned role

Not supplied in the contributor's words. Working persona: runtime engineer on a language
implementation, generational collectors, write barriers and weak maps.

## Source repository

- Repo URL: none - idea-based task.

## Task summary

`/app` is a small generational runtime: a nursery and an old space, objects with fields, frames
with named slots, a global table, a handle stack, pins, a weak reference table, a table of weak
key-value pairs, finalizers, and a remembered set fed by a write barrier. A program is a text
file of ops and `/app/run_prog.py` prints a line per event. Five files under `/app/col` decide
roots, reachability, finalizer retention, ageing and clearing; four ship wrong.

## Why it is hard

- Expert time estimate: 8 hours.
- Why a frontier agent cannot one-shot the plan: the rules are stated, but several facts the
  rules depend on are behaviours of the tree. The remembered set stores a value that is never
  refreshed, which is visible only in `mem/rset.py`; whether an object is in the nursery or old
  space depends on the ageing rule the agent is also writing; and the five modules consume each
  other's answers, so no one of them can be settled alone.
- Tactics making that true: A2, A3, B1, B2, C1, C2, C3, C4.
  A2 - the mechanisms are described operationally and never named: no "ephemeron", no
  "tricolor", no "resurrection", no "write barrier".
  A3 - the pair fixed point, the finalizer reprieve and the generational split have textbook
  answers that do not compose.
  B1 - the load-bearing facts are spread: the barrier's trigger in `mem/rset.py`, promotion in
  the module the agent is writing, root sources in `mem/roots.py`, staleness nowhere but in the
  interaction of the two.
  B2 - nine stated decisions whose interaction is the work; getting ageing right changes which
  space an object is in, which changes what the next collection traces.
  C1 - both fences: `plain-drop`, `all-live`, `weak-live` fail an over-conservative collector;
  `old-safe`, `rset-root`, `weak-old` fail an over-eager one.
  C2 - the shipped collector is wrong in four of five modules, so running it confirms nothing.
  C3 - a measured scaling boundary: the rescanning fixed point is exactly correct and takes past
  800 s on the graded set against 0.7 s indexed, with a stated 60 s limit.
  C4 - all-or-nothing over 25 hand programs and 312 nonce programs generated after the agent
  finishes.
- Assistant's attack on the plan: my first plan was reachability plus the pair fixed point plus
  finalizer retention, which is the previous version of this task and was rejected twice as not
  difficult. It is wrong here in three further places - it trusts the remembered set, it ages
  held objects, and it lets a minor collection speak about old space.
- Estimated solves out of 8: 3 (honest range 2 to 5).
- Leak audit, run as a procedure:
  - Can a shipped file reproduce a graded answer by a join, a sort or a field comparison? No.
    The shipped data is four programs with no expected output beside them.
  - Is any exposed pair of fields a witness? The heap exposes primitives the mutator wrote -
    `objs`, `flds`, `fin`, `space`, `age`, `pins`, `rset`, `pairs`, `weak`, `queue`, `done`.
    Nothing derived is stored: no reached flag, no colour, no retained count, no cached closure.
  - Does the worked example decide anything? `tiny.txt` shows the record format and one wrong
    line, which the brief names. It does not settle the remembered set, the pair cascade, the
    queue ordering or the clearing rules.
  - Is anything callable that was counted as difficulty? No. The five modules are what is being
    written.
- Expert path: read `ops.py` to find the five entry points and the order they are called in;
  read `mem/rset.py` and notice the recorded value is never refreshed; write roots for both
  collection kinds; write the walk with the pair table indexed by key; settle the queue before
  keeping; separate what survived from what is merely kept; carry that split into ageing and
  clearing; then the space rules - a minor collection traces, releases and clears only the
  nursery, but an old pair key is ready throughout.
- Originality check: the parts are documented separately. The conjunction with a stale
  remembered set, a generational split and the reprieve interacting is on no page, and the brief
  names none of the concepts.

## Verifier contract - FROZEN

- Artifacts: the five files under `/app/col/`.
- `plan.roots(h, full)`, `scan.reach(h, start, full, barred)`, `keep.settle(h, seen, full)`,
  `age.promote(h, seen, held)`, `wipe.wipe(h, seen, full)`, `wipe.release(h, seen, held, full)`.
- Graded: the nine decisions listed in the `tests/test_outputs.py` docstring.
- Never graded: traversal order, container types, the order within each returned collection (the
  runtime sorts), internal naming.
- Ground truth: `tests/gt.json` for 25 hand programs, frozen from the sealed model and
  cross-checked against the reference through the real runtime. Nonce programs are generated in
  the verifier and checked against `tests/model.py`. The grader asserts model and `gt.json` still
  agree before grading anything.

## Decisions and their reasons

- Rebuilt on the house shape after the quality review failed `difficult` twice. The previous
  version was 107 lines of environment with one editable file and shipped no engine; every
  retained passing task is 229-544 lines with 1-7 editable files and ships a working-but-wrong
  engine. The earlier removal of the shipped collector was an over-correction on my part.
- The remembered set stores the written value, not just the location. Storing only (source,
  field) made "trust the record" inexpressible, so the staleness reading could not be separated;
  with the value stored it moves 12% of a shaped population and is named by `rset-stale`.
- Terse identifiers kept but widened from the previous version - `ob` and `fl` became `objs` and
  `flds` - after the review called the naming friction rather than expertise.
- The scaling boundary survives the rebuild unchanged and is stated in the brief with the scale.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model | pass | 237 programs, two PYTHONHASHSEED values |
| Oracle scores 1 | pass | host emulation, 312 nonce programs |
| nop scores 0 | pass | the shipped tree is wrong in four of five modules |
| Correct variants score 1 | pass | `alt` (breadth-first), `mirror` (renamed) |
| Cheats score 0 | pass | 14 of 16 run; each caught by its own declared layer |
| Cheats needing a container | not run | `reward-daemon` needs fork, `privilege-probe` a second uid |
| Scaling boundary | measured | 0.7 s correct vs past 800 s rescanning, 60 s limit |
| `docker_trial --all` / `--variants` | not run | Docker is not installed on this machine |
| `imagecheck` | pass | 17 files, workdir /app, reference runs all four programs |

## Open questions and next steps

1. `relevant_experience` needs the contributor's words.
2. The two container-only cheats and the 60 s limit stay unverified in a container until Docker
   exists. The handover must say so.
