# Task state

Working memory for this task. Updated after every stage; assume the next session starts with no
memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`, after the easiness recovery recorded below (probe 2 of 3
on 2026-09-13). The two-container gates cannot be run in this session: `docker` is installed but
no daemon is reachable, so no image can be built. Everything else has been run on the host - see
the validation table, and read the `host trial` rows as host emulation rather than container
evidence. The recovery's exit gate is the platform's own easiness probe, which has not yet been
run against this build; the recovery is therefore **pending** at gate 1 of section 6 of
`RAISE-DIFFICULTY.md`, and this bundle is the candidate for it.

The bundle that was probed is byte-for-byte the first commit of this task on this branch
(`fix-layered-config: import the bundle the easiness probe solved 2 of 3`); it carried no
`STATE.md`, so the sections below were written during the recovery from the bundle, the three
trajectories and the measurements made here.

## Assistant's assigned role

Configuration-language engineer on a deployment tool's settings service: the kind that composes
a plan of layered edits, keeps every intermediate view, and answers questions about any of them
exactly, with copies, template instances and now live windows over a subtree.

## Source repository

- Repo URL: none - idea-based task.
- Task shape: not repo-based, so neither authored-on-top nor ablation applies.

## Task summary

`/app` is a settings service cut down to composing a plan and answering questions about it. A
plan is layers of entries - `put`, `cut`, `mix`, `map`, `tie`, each with an optional guard -
followed by questions, `ask` and `tot`, each optionally naming a layer count. Expressions are
`lit`, `now`, `old`, `sum`, `top` and `pick`. The frozen half is the parser (`cfg/lex.py`), the
output writer (`cfg/say.py`) and the driver (`run_plan.py`); the six files under `/app/cfg` that
decide the store, the definitions, the layer roll, the evaluator and the answers all ship
working and wrong. The graded artifact is those six files; the verifier overlays them onto its
own copy of the tree and compares the printed line of every question exactly.

## Why it is hard

- Expert time estimate: 9 hours.
- Why a frontier agent cannot one-shot the plan (the strategic answer): the brief states every
  rule, and the structures the rules seem to ask for are the standard ones - an immutable tree
  of definitions with a count on every node, a copy that shares the source's node, an
  installation that wraps that node with a lazy path rewrite, values remembered by definition
  and view. The easiness probe showed three agents writing exactly that on sight, and it was
  the right plan for everything but the window. A `tie` makes what a node means depend on the
  view it is read in. Four consequences follow, none of them stated as a rule: a node can no
  longer carry its own count (what shows under a tied prefix is the source's structure minus
  what the destination's writes hide); a copy of a tied subtree cannot be a shared pointer, and
  must resolve the ties beneath it in the view that was current when it was taken; a lookup
  must follow full paths rather than settle a source prefix first, or it stops at a prefix it
  is merely passing twice; and the count formula that makes the wide family affordable is
  exact only where no lookup cut itself off. A brute-force model of the brief gets all of this
  for free and transfers nothing about the structures that replace the first plan.
- Tactics making that true: A1, A2, A3, B2, C1, C2, C3, C4.
  A1 - the prior for a live window is a pointer resolved at lookup time, and for counting it
  is either a stored count or an enumeration; the first is wrong, the second is correct and
  dies. The prior for freezing a window is to capture the node it points at, which keeps the
  ties beneath it live.
  A2 - nothing is named: no prototype, no delegation, no inheritance, no overlay, no tombstone,
  no hash-consing. The brief says what a path shows and when.
  A3 - a count that is affordable over twenty thousand inherited paths, a copy that is O(1)
  over a doubling window, and a lookup that is exact through rings have no single structure
  that gives all three; the pair walk over written nodes, the captured logical node and the
  per-path chain each come from a different reading of the same rules.
  B2 - the six modules must agree on one notion of what a path shows: the store resolves it,
  the definitions are moved by it, the roll clears by it, the evaluator reads through it and
  the answers count it. All six ship wrong, and the shipped tie is wrong in four ways at once
  (no move, one level, no mask, no count).
  C1 - both fences on every new axis: `tie-follows-source` against `tie-mix-freezes`,
  `tie-cut-masks` against `tie-put-at-mask-root`, `tie-under-copy-is-live` against
  `tie-frozen-below-copy`, `tie-ring-through-ancestor` against `tie-ring-twice-through-one-tie`,
  `tie-empty-source` against `tie-clears-destination`.
  C2 - no oracle: the shipped `tied.txt` prints wrong lines, a spec-derived brute-force model is
  right for free and confirms nothing about the fast structures, and the two execution
  boundaries are the only feedback a wrong structure gets.
  C3 - two measured boundaries with derivable fast paths (numbers in the recovery entry below):
  counting by enumeration against the pair walk over written nodes, and freezing by writing
  out against capturing the logical node.
  C4 - all-or-nothing over 85 enumerated plans and 692 nonce plans (17 shaped families of 40
  and 4 scale families of 3), generated inside the verifier from a seed drawn after the agent's
  container is gone.
- Assistant's attack on the plan: my first plan, read cold, is the one the three probe agents
  wrote plus "a tie node holding the source path, resolved when a lookup passes it". That plan
  is wrong in four places that the brief states and I did not connect on the first pass: I
  would have counted by enumerating what shows (correct, dead on wide.txt); I would have frozen
  a tie by capturing the node its source points at (the ties beneath it stay live, which
  `tie-frozen-below-copy` fails); I would have resolved a tie by settling its source prefix
  first (which is what my own first reference did, and the fuzz caught it on the fourth
  program of a shape I had not imagined: a lookup that passes the same prefix twice on the way
  to a written path); and I would have subtracted what the destination hides from what the
  source counts without noticing that the subtraction is inexact once a lookup has cut itself
  off (the fuzz caught that too, on a three-way ring). Each of these was found by running a
  program I did not write by hand.
- Estimated solves out of 8 after the easiness repair: 2 (honest range 1 to 4). Measured before
  it: 2 of 3, which reads as 5 to 7.
- Difficulty score anchor: `authoring/fix-layered-config/difficulty.toml`, scored after the
  build; see the recovery entry.
- Score history: easiness probe 2026-09-13, 2 of 3 solved, on the imported bundle.
- Leak audit (docs/DIFFICULTY.md), run as a procedure:
  - Can a shipped file reproduce a graded answer by a join, a sort or a field comparison? No.
    The tree ships six plans and no expected line for any of them; the one line the brief
    quotes (`num site 1`) is the count of a two-path plan with no tie.
  - Is there a stored derived quantity? No. The shipped store is a dict of written definitions
    and a dict of tie destinations to sources, which is what the plan said; no count, no
    logical node, no moved definition, no mask and no captured view ships. Every one of them is
    the agent's to invent.
  - Unused affordances? `pile.tie`, `pile.find` and `pile.count` are on the live path through
    `roll.py`, `work.py` and `ans.py`; nothing in `cfg/` is defined and uncalled (the preflight
    warning that said otherwise was the linter missing module-qualified calls, fixed in this
    session and checked clean on the retained bundles).
  - Manifests? None. Self-labelling data? None. Any artifact that is a function of the correct
    trajectory? No - `gt.json` and the sealed model are baked into the verifier image only, in
    `tests/seal` chmod 700 before any agent code runs. Free join keys or callable difficulty?
    The shipped service is callable and wrong, which is the opposite. Per-axis confirmation
    before commit? No - one trace per plan, all-or-nothing.
- Expert path, described step by step: read `run_plan.py` and `cfg/lex.py` to learn the op set
  and that a tie carries a source and a destination that may not overlap; read the shipped
  `cfg/pile.py` and notice the store is a dict with a one-level tie lookup and no notion of a
  mask; write an immutable tree with markers at cleared, tied and copied paths; define what a
  path shows as its written node plus what the nearest marker above makes it inherit, and
  follow that path by path with the paths already visited carried along; give each tie and
  each installation one moved definition per source definition; capture a copy as the logical
  node it was given, in the view it was given in; count by the correction walk over written
  nodes and fall back to enumeration where a lookup cut itself off; key values and circularity
  by definition identity and view; time `plans/wide.txt` and the doubling plans, multiply by
  three, and check the whole batch against the limit.
- Originality check: searched again on 2026-09-13 for the composite (layered configuration
  with copies, template installation and a live window over a subtree; a window that moves
  path references; masks that outlive a later write; a copy of a window frozen in the view it
  was taken in; counting what shows under a window). The neighbouring real machinery is
  retrievable - prototype delegation in JavaScript, overlays in Nix, `extends` in Jsonnet and
  CUE, tombstones in overlay filesystems - and none of it states this rule set, and the graded
  object is this service's exact trace.

## Verifier contract - FROZEN

- Artifacts the agent produces: `/app/cfg/pile.py`, `/app/cfg/past.py`, `/app/cfg/made.py`,
  `/app/cfg/roll.py`, `/app/cfg/work.py`, `/app/cfg/ans.py`. Nothing else is read from the
  agent.
- What is checked: the verifier overlays those six files onto its own pristine copy of the
  tree, runs every graded plan through `run_plan.main`, and compares the printed lines
  exactly. 85 enumerated plans are checked against `tests/seal/gt.json`; 692 plans generated
  from a nonce drawn at verification time (seventeen shaped families of 40 - `per=40` in
  `tests/test.sh`, which every count in the prose is derived from - and four scale families of
  3) are checked against `tests/seal/model.py`. The model must reproduce `gt.json` exactly
  before anything else is graded. Every plan must match.
- The rules are the eighteen numbered sweeps in `tests/cases.py`. Sweeps 13 to 18 (the tie)
  were added on 2026-09-13; every one of the 61 answers frozen before that date came out
  byte-identical afterwards, which `authoring/fix-layered-config/build_gt.py` checks on every
  run. Two rules that the old contract left to a promise are now stated and graded: a path of
  more than twenty-four segments shows nothing, and `tot` counts only paths of at most
  twenty-four segments. No frozen answer moved under them.
- Tolerances: none. Exact string equality on an ordered list of lines.
- Execution limit: the worker that runs the submitted service has a 60 second wall clock,
  stated in the instruction. Exceeding it is scored 0.
- Ground truth: `tests/seal/gt.json`, built by `authoring/fix-layered-config/build_gt.py` from
  the sealed model and checked against the reference; baked into the verifier image only, in a
  directory `chmod 700` before any agent code runs.
- Isolation: the worker runs as uid 1002 in its own session under `timeout`, `/logs/verifier`
  is root-owned and `chmod 700` before any agent code runs, the reward defaults to 0 and is
  written last by the privileged stage, survivors are reaped by uid, and the grader never
  executes agent code.
- Prong C tactics used: C1 (both fences enumerated on every axis), C2 (no oracle - all six
  shipped modules are wrong and a brute-force model transfers nothing), C3 (two measured
  boundaries against the execution limit), C4 (nonce-generated population plus enumerated
  corners, all-or-nothing).
- Route-around guard: only the six files are declared artifacts, so the parser (with its
  overlap rejection), the output writer and the driver cannot be reshaped by the agent.

## Easiness recovery - 2026-09-13 (probe 2 of 3)

### 1. The failure, captured before editing

The easiness probe ran three trials against the imported bundle and two of them solved it.
The trajectories are `probes/fix-layered-config/2026-09-13-easiness-1.txt`, `-2.txt` and
`-3.txt`, each with the brief removed from the top so `tools/leakcheck.py` is not circular;
commentary is in `probes/fix-layered-config/notes.md`. The files carry no verdicts, so which
trial failed, and on what, cannot be read from them and is not claimed.

Each agent's route, in its own words condensed:

- **Trial 1.** First plan: read the six editable files and the frozen tree, run the five
  plans, list every shipped defect against the sentence of the brief it breaks (count of
  interior paths, `ask` at the final view, guards mid-layer, `mix` not clearing and re-dating,
  `old` at the writing layer, right side first, `pick` by subtree, `map` never run). Decisive
  discovery: none needed - one timing of `wide.txt` and the persistent trie with a count per
  node, a pointer-shared `mix` and a lazy `map` wrapper was its first idea; a second pass made
  fresh puts edit nodes in place for the wide prefix. Final method: six files in one pass, hand
  cases of its own for ties of the same shapes the brief lists, done in a short session.
- **Trial 2.** First plan: the same list from reading the code, then all six files rewritten
  before any experiment, around the same trie with per-node counts, a shared `mix` subtree, a
  lazy `map` node and a trampolined evaluator memoised per (definition, view). Decisive
  discovery: none - it wrote a brute-force model of the brief and fuzzed 1,900 random plans
  against it, so every rule was confirmed against its own reading of the rules.
- **Trial 3.** The same plan again, in one write, checked on the five shipped plans and one
  synthetic 21-copy `map` plan, done fastest of the three.

Earliest point at which each had enough to commit to the winning plan: the end of the first
read of the tree, before any plan was run. The plan came from the instruction's rule list and
the shape of the tree - six modules, one per concern - not from an example, a helper, a public
source or a verifier loophole; `tools/leakcheck.py` finds nothing above the floor in any of the
three, so the wording was not the leak.

Tactics on record before this probe (from the imported `task.toml`): A1, B2, C1, C2, C3, C4.
The ones that failed in practice: B2, because every rule was implementable on its own and the
structures each rule wants are the standard ones, so the conjunction was a checklist; C2,
because a brief that states every rule is a complete specification of a brute-force oracle,
and trial 2 wrote one; and C3, because the fast structures the boundaries demanded - a count on
every node, a shared subtree - were each agent's first idea.

Estimated solves out of 8 before this repair: 6 (honest range 5 to 7), from 2 of 3 measured.

### 2. Classification of the winning route

Two rows of the table in `RAISE-DIFFICULTY.md` apply.

- **The default plan was correct.** All three named the state model on sight: an immutable
  trie with a count on every node (`solution/pile.py` of the imported bundle, `Node.n`), a
  pointer-shared `mix` (`_graft(cleared, dst, 0, made.carried(_down(cleared, src), at))`), a
  lazy projection for `map` (the `View` class), and a memo keyed by (definition, view root)
  (`solution/work.py`). Required direction: a specified interaction that makes that coherent
  prior wrong.
- **The instruction delivered the decomposition.** Each rule of the brief maps onto one
  shipped defect, so reading the two side by side is the plan. The doctrine forbids hiding a
  rule, so the direction is not to withhold one: it is to add behaviour whose stated rules are
  simple and whose consequences break the structures above.

Not applicable: no route-around was found, the naive method was not fast enough (both scale
boundaries were real and every agent rebuilt around them), and the verifier accepted no false
solution. One defect of the probed bundle was found on the way and is recorded here because
it bears on what the cheats were evidence of: 29 of its 42 cheat scripts embedded a reference
older than the one it shipped (the pre-`map` solution, with no `map` at all), so their zero
scores were attributable to the missing operation rather than to the decision each was named
for. Every cheat is now regenerated from the current reference by a scripted edit that must
fire, and the layer that catches each is asserted.

### 3. The semantic replan - candidates, attacked

**Candidate A: a live window, `tie`.** The destination shows the source as it stands, path
references moved as `map` moves them, until written over; a removal under it masks; a copy of
it is frozen in the view it was taken in; a lookup follows paths and stops where it comes back
to one. Attacked: the brute-force model gets every part of this for free (walk the path, follow
the tie, keep a set of paths seen), which is the point - nothing in a spec-derived oracle warns
that the fast structures are dead. The stored count cannot express what shows; the shared
pointer cannot freeze a window; the lazy wrapper keyed on a node cannot resolve a tie in the
view that was current when the copy was taken; the memo keyed on identity needs one moved
definition per source definition per tie, or circularity through a tie is never found. Expert
path: markers on written nodes, logical nodes per (view, path), a correction walk over written
nodes for the count, a captured logical node for a copy, per-path chains for rings. **Selected.**

**Candidate B: withdrawing a layer.** An op that takes an earlier layer out of the plan, with
every later view recomposed as if it had never been. Attacked: replay is both the brute force
and the fast path, since the persistent structure makes recomposition cheap; every consequence
is a re-run, not a replan. Rejected - grinding, not planning depth.

**Candidate C: counting only paths that answer an integer.** Attacked: the fast path is the
obvious one (memoise the count per node and view), and no structure is invalidated - the count
per node just gains a view in its key. Rejected as a patch.

Tactics after the repair: A1, A2, A3, B2, C1, C2, C3, C4, as listed under "Why it is hard".

### 4. What was rebuilt

Stage 2 first: the contract gained the tie and kept every existing rule unchanged in meaning,
so the 61 enumerated answers frozen before the change had to come out byte-identical
afterwards. They did - `build_gt.py` checks it on every run.

- `environment/app_src`: `tie` added to the parser (`cfg/lex.py`, with the overlap rejection),
  `cfg/pile.py` reshaped around a dict of definitions and a dict of ties with a one-level
  lookup and no mask, `cfg/roll.py` dispatching it; `plans/wide.txt` regenerated with the tie
  the brief describes; `plans/tied.txt` added. Environment: 385 lines of Python, six editable
  files; `tests/pristine` re-synced and checked.
- `solution/`: rewritten around logical nodes - 460 lines against 285.
- `tests/seal/model.py`: rewritten independently on the same contract as a written tree read by
  path, with the rules taken literally (a `seen` set of paths per lookup, a count that
  enumerates what shows with the budget as the well-founded measure and a shortcut for regions
  with nothing written beneath). The two were fuzzed against each other on 11,900 shaped random
  plans across four generators (eight roots at depth three; three roots at depth four, which
  makes rings common; four roots at depth five, which makes sources deeper than destinations
  common) with zero disagreements at the end; three disagreements found on the way are in
  section 6.
- `tests/gen.py`: five shaped tie families (`tielive`, `tiechain`, `tiefreeze`, `tiering`,
  `tieinterference`), a fourth scale family (`tiedeep`), and the tie threaded through `wide`.
- `tests/cases.py`: 24 enumerated tie plans in six sweeps, both fences on each axis.
- `cheat/`: 54 scripts, all regenerated: 40 wrong readings, 3 correct-but-slow readings, 9
  verifier probes and the forgery.

### 5. The old winning implementation, kept as a cheat

The probe agents' architecture is what the reference still is for every operation but the tie,
so it survives as several cheats rather than one: `tie-mix-stays-live` is the pointer-shared
copy applied to a window, `tie-copy-below-live` is the lazy wrapper keyed on a node,
`tie-ring-cuts-region` is the source-prefix resolution my own first reference had, and
`slow-enumerate` is the count every trajectory's first idea would produce for what shows under
a tie. `tie-chain-composes`, `tie-frozen-below-copy`, `tie-ring-deep-source` and the execution
limit catch them in that order.

### 6. Measurement of the repair

Three disagreements between the reference and the model, found by the fuzz and each fixed in
whichever side was wrong, are the evidence that the tie's consequences are not derivable from
the rules by inspection:

- `tie a f; tie e a; put f.v now e.z; tie f e; tot a` - the model subtracted what the enclosing
  region shows at `f.v` from a base it had cut to zero. The model's counter was rewritten as the
  literal enumeration, well-founded on the budget, with no subtraction at all.
- a source deeper than its destination - the reference resolved a tie's source prefix before
  descending, and cut a lookup that merely passed the same prefix twice on its way to a written
  path; the model looped forever because nothing bounded the growing path. The reference now
  follows full paths; both now apply the twenty-four-segment bound to every path a lookup
  reaches, and the rule is stated in the brief.
- `tie-count-bound` - both fast counters carried a budget across a shortcut into a region whose
  own path leaves less below the bound, and counted two paths that show nothing. The literal
  enumeration said 43 where both said 45; the budget is now clamped at every node's own path.

Timings of the correct-but-slow readings, one plan of each scale family, against the reference
(host, Python 3.11, guard 100 s): recorded in `authoring/fix-layered-config/timing.txt` and
quoted in the difficulty record.

Readings: 40 wrong readings each separated by a named enumerated case (`authoring/
fix-layered-config/readings.py`), none blind; the correct-but-slow ones are separated by the
limit alone. One reading written as wrong turned out equivalent - a memo keyed by path rather
than by definition, which this contract cannot distinguish because a path holds one definition
per view - and is kept as the correct variant `ok-path-memo`.

## Validation record

| gate | how run | result |
|---|---|---|
| reference vs frozen answers | `agree.py` | 85 of 85, byte-identical for the 61 pre-tie answers |
| model vs frozen answers | `agree.py` | 85 of 85 |
| reference vs model, random | `fuzz.py`, four generators | 11,900 plans, 0 disagreements |
| reference vs model, families | `famcheck.py` | every family, 0 disagreements |
| readings separated | `readings.py` | 40 of 40 by a named case; 3 timed-only |
| cheats caught where expected | `cheat_report.py` | see the recovery entry, updated below |
| oracle / nop | `host_trial.py` (host emulation) | updated below |
| preflight | `scripts/preflight.py` | updated below |
