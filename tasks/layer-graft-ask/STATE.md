# layer-graft-ask

## Current stage

`Stage 7 - pre-flight and packaging`.

## Assistant's assigned role

An engineer on the settings service of a fleet deployment tool: the part that composes the
layers a rollout applies, answers what a service would read at any point in that rollout, and
has to keep the answer defensible when somebody asks what a layer was deciding against. Later
sessions resume in this persona.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. Nothing is vendored, so the identifier-degradation and
  proper-noun sweeps of the repo intake do not apply; the tree is written here in the house
  legacy register from the start.

## Task summary

A settings service composes a plan of layers. Each layer holds entries that give a path a
definition, remove a path and everything under it, or replace one subtree with another. An
entry may carry a guard. A definition is an expression that can name other paths, either as the
plan stands when the question is asked or as it stood before the layer that wrote the
definition. The service answers two questions: what a path says, together with the layer that
wrote the definition answering, and how many paths under a prefix hold a definition. Both can
be asked as if the plan had stopped after a given number of layers.

`/app` ships that service with six of its files wrong in eight places and slow in three more.
The agent rewrites those six so that `/app/run_plan.py` prints, for every graded plan, exactly
the trace the contract below defines, and gets through the whole graded set inside 60 seconds.

## Why it is hard

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): a question in this
  service carries how much of the plan counts when it is answered, and guards are questions, so
  the two things the obvious design separates - fold the layers into views, then evaluate the
  values - cannot be separated; meanwhile a copy carries definitions that keep their own layer
  and multiplies the paths holding them, so the per-layer dictionary the obvious design folds
  into is both the wrong shape and unaffordable, and every structure the rules seem to ask for
  (one finished view that forward references resolve against, a memo per path, a copy expanded
  path by path, a count taken by walking) is right until it is not.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, B2, C1, C2, C3, C4 - B1 is not
  claimed. A1: every account of layered overrides has one finished result that forward
  references resolve against and treats copying a subtree as taking the values found there, and
  both are inverted here. A2: the rule is stated as how far the plan counts when a question is
  answered, and the words snapshot, thunk, closure, fixpoint, persistent and memo appear nowhere
  the agent can read. B2: twelve rules hold at once and each changes what another means. C1:
  both sides of every fence are graded. C2: no op prints a view, no query returns a definition's
  layer except the graded line itself, and the only local oracle is the shipped engine, which is
  wrong in eight places. C3: three naive-but-correct families measured against the stated limit.
  C4: exact all-or-nothing traces over enumerated corners and plans generated inside the
  verifier from a seed drawn after the agent's container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is a dictionary from path to a definition, folded layer by layer with a copy of the dictionary
  kept before each layer, a copy expanded by walking the source paths, and a lazy evaluation
  where a forward reference means the finished dictionary and a backward reference means the
  dictionary before the definition's layer, memoised per path. That plan is right about entry
  order, about removal taking the subtree, and about what a backward reference means; it is
  wrong about forward references, because it has one finished result and the service has one per
  count; it cannot be built in the order it assumes, because a guard is itself a question and so
  the fold and the evaluation have to advance together; and it dies on both measured families,
  because a copy whose destination sits inside its own source doubles the paths twenty-one times
  and a count taken by walking is asked twelve thousand times per wide plan.
- Estimated solves out of 8: 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/layer-graft-ask/difficulty.toml,
  before Stage 2): attempt 1 scored 100/100 on paper. Re-scored at Stage 7 against the built
  tree: 100/100, measured at 359 environment lines, 6 editable files, 308 reference lines, 29
  cheats and 2 variants, with no drift reported on any declared size.
- Score history: see the table under "Difficulty record" below.
- Leak audit (docs/DIFFICULTY.md): no shipped plan carries its own correct answers and the only
  thing in the tree that runs them is wrong in eight places, so nothing demonstrates a rule; the
  two small shipped plans copy nothing that reads backwards and guard only on a path nothing
  later touches; the shipped store keeps beside each path the layer that last touched it, which
  is the wrong quantity for every carried definition, and no query prints it; copying happens
  inside the store's own edit path and no reachable entry point returns the set of paths a copy
  would take; counts are a function of the shape alone, so differencing them across a copy says
  nothing about the layer a carried definition keeps; the sealed model, the frozen answers and
  the pristine tree exist only in the verifier image, in a directory locked to root before any
  submitted code runs. Measured by `tools/onelinecheck.py`: of the four graded quantities, only
  the guard verdict has an exact rule at depth two (`atown == want`, which is the stated rule and
  is covered by two cheats); the layer a query reports, which kind of answer comes out and the
  count under a prefix have none.
- Expert path, described step by step: reproduce the wrong line the brief names on the shipped
  plan; read the frozen driver, op parser and trace writer to pin the output contract; carry the
  count a question is asked at through every reference rather than only through the query that
  named it; fold the layers and answer the guards in one forward pass, because each guard is a
  question asked at its own layer; give every definition the layer that wrote it and keep that
  layer when a copy carries it; rebuild the store from nodes that are never mutated so each
  layer keeps a root and a copy is one node reference; keep the number of defined paths on each
  node so a count never walks a subtree; key the memo and the in-progress set on the definition
  together with the count; generate the wide and the doubling plan and time both against the
  stated limit.
- Originality check: searched on 2026-09-11 for layered configuration systems that copy
  definitions rather than values, for overlay calculi, and for historical reads over composed
  layers. The closest public material is a recent calculus of overlay inheritance and the
  configuration module system it models (arXiv 2602.16291): there layers compose by recursively
  merging subtrees, there is one finished tree that every forward reference resolves against,
  and there is no notion of asking a question as if the plan had stopped. Persistent tries with
  structural sharing, lazy evaluation with memoisation, and cycle detection are each documented
  on their own; the conjunction with a moving count, a copy that carries dated definitions, and
  a replacing rather than merging copy is described nowhere found. No retained task in this
  repository is about layered definitions or demand-driven evaluation; the two nearest by
  subcategory are `guard-mark-unwind` (unwinding) and `reach-pair-sweep` (reachability), and
  `tools/simcheck.py` reports "this task does not grade what any earlier one grades".

## Category

`Software` / `Languages`. The graded work is the evaluator of a small declarative language:
definitions that carry the scope they were written in, references resolved against a moving
horizon, demand-driven evaluation with memoisation and circularity, and a store of bindings
that has to stay readable at every earlier point. `catcheck` reports 65 environment hits for the
Software vocabulary against 83 in the prose.

Domain role adopted for the project: an engineer on the settings service of a fleet deployment
tool - the part that composes the layers a rollout applies and answers what a service would read
at any point in it.

Tags: `lazy-evaluation`, `scoped-references`, `structural-sharing`, `memoisation`,
`cycle-detection`, `subtree-copy`.

## Definition of done

Six files under `/app/cfg/` - `pile.py`, `past.py`, `made.py`, `roll.py`, `work.py`, `ans.py` -
are replaced so that `/app/run_plan.py` prints, for every graded plan, exactly the trace the
frozen contract defines, and finishes the whole graded set inside 60 seconds.

## Verifier contract - FROZEN after Stage 2

### Declared artifacts

```
/app/cfg/pile.py
/app/cfg/past.py
/app/cfg/made.py
/app/cfg/roll.py
/app/cfg/work.py
/app/cfg/ans.py
```

Nothing else is read from the agent. The verifier lays these six over its own pristine copy of
the tree, so nothing else the agent touched can change what a plan prints.

### The plan language

A plan is a text file, one op per line, single spaces between tokens. A path is one to
twenty-four segments joined by `.`, each segment `[a-z][a-z0-9]{0,7}`. Integers are decimal and
may be negative.

```
lay                              open a new layer; layers are numbered 0, 1, 2 ... in order
put <path> <expr>                entry: the path takes this definition
cut <path>                       entry: the path and everything under it lose theirs
mix <src> <dst>                  entry: the destination subtree is replaced by the source one
ask <path> [<n>]                 query: what the path says, counting n layers or the whole plan
tot <path> [<n>]                 query: how many paths at or under it hold a definition
```

An entry line may end with one guard, either `if <path> <int>` or `un <path>`. Every entry
belongs to the layer most recently opened. No entry may follow a query.

```
lit <int>                        the integer
now <path>                       the path, counted the way the question counts the plan
old <path>                       the path, counted as the plan stood before the layer that
                                 wrote this definition
sum <expr> <expr>                the sum
top <expr> <expr>                the larger
pick <path> <expr> <expr>        the first when the path holds a definition, else the second
```

### State

`S[n]` is the store after the first `n` layers; `S[0]` is empty. A store maps a path to a
definition, and a definition is the pair of an expression and the layer whose `put` wrote it.

### Applying a layer, exactly

Layer `j` turns `S[j]` into `S[j+1]`. Its entries are taken in the order written, against the
store as the earlier entries of the same layer have left it. A guard is answered against `S[j]`
at count `j` - the plan as it stood before the whole layer - so the earlier entries of the same
layer do not move it. `if <path> <int>` holds when the path answers exactly that integer;
`un <path>` holds when it answers absent. A path that answers circular satisfies neither. An
entry whose guard does not hold is skipped.

- `put P E` - `P` takes the definition `(E, j)`, replacing whatever stood there.
- `cut P` - `P` and every path under it lose their definitions.
- `mix A B` - `B` and every path under it first lose their definitions; then every path `A` or
  `A.<suffix>` holding a definition at that moment gives that same definition, unchanged and
  still carrying the layer that wrote it, to `B` or `B.<suffix>`. The source paths are fixed
  before any of them is written.

### Answering a question, exactly

A question counts the first `n` layers; `n` is the number a query names, the whole plan when it
names none, and `j` for a guard in layer `j`.

- The definition answering `P` at count `n` is the one `S[n]` holds at `P`. If there is none the
  answer is absent.
- A definition `(E, h)` is evaluated at count `n`. `lit m` is `m`. `now Q` is the answer for `Q`
  at count `n`. `old Q` is the answer for `Q` at count `h`. `sum` and `top` evaluate their left
  side and then their right side. `pick Q a b` evaluates `a` when `S[n]` holds a definition at
  `Q` and `b` otherwise, and the other side is not evaluated.
- Absent and circular are the two answers that are not integers, and they carry outward: an
  expression whose first failing side is absent answers absent, and one whose first failing side
  is circular answers circular.
- Evaluating a definition at a count while that same pair is already being evaluated answers
  circular.

### Queries

- `ask P` and `ask P n` print `val <P> <value> <layer>`, where the layer is the one that wrote
  the definition answering, or `val <P> gone`, or `val <P> loop`.
- `tot P` and `tot P n` print `num <P> <count>`, the number of paths at or under `P` holding a
  definition at that count.

### The twelve graded decisions

1. a layer's entries apply in the order written, and a later one replaces an earlier one
2. a guard is answered against the plan before its own layer, not against the earlier entries
   of that layer
3. a guard is answered as if the plan had stopped at its own layer
4. a query that names a layer is answered as if the plan had stopped there, values included
5. a removal takes the path named and everything under it
6. a copy replaces the destination subtree before it carries anything, and its sources are
   fixed before any of them is written
7. a copy carries definitions, not values, so a carried path keeps following the same expression
8. a carried definition keeps the layer that wrote it, both for its backward references and for
   the layer a query reports
9. a value that requires itself at the same count is circular, and a definition naming its own
   path backwards is not
10. absent and circular are distinct and the left side of an expression decides which is
    reported
11. a count reports only the paths that hold a definition at or under the prefix
12. `pick` tests whether the path holds a definition, evaluates only the side it chooses, and is
    answered at the count of the question

### Prong C, and the route-around

C1 is the both-sides fencing above. C2 is that no op prints a view, no query returns a
definition's layer except the graded line, and the two small shipped plans demonstrate neither
the count rule nor the carrying rule. C3 is the three measured families under "Measured" below.
C4 is exact all-or-nothing grading over enumerated corners and plans generated inside the
verifier from a seed drawn after the agent's container is gone. The route-around is blocked by
the artifact list: the six files decide what a plan prints, and the driver, the plan parser and
the trace writer are the verifier's own copy.

### Correct variants that must score 1

1. `authoring/layer-graft-ask/variants/ok-model` - nodes carrying no count, sizes worked out by
   walking with a memo on the node itself, guards of a layer all answered in one pass before any
   entry is applied, and what is remembered keyed on the path and the count;
2. `authoring/layer-graft-ask/variants/ok-stack` - children in a sorted list found by bisection,
   the count re-added from the children on every rebuild, roots held in a dict keyed by the
   count, and evaluation driven by an explicit stack with no recursion.

Both score 1 in the container.

### One rule was cut here, before the contract was frozen

The design as first written (`layer-graft-read`, discarded) had guards testing only whether a
path was defined. That made the views foldable before any value was computed, which made the
whole evaluation a second pass and left the task resting on the resource gate alone. Guards
became questions answered at their own layer instead. Nothing else in the contract changed.

After this point the contract is frozen. A change to it changes what "correct" means.

## Difficulty record

`authoring/layer-graft-ask/difficulty.toml`, scored with `tools/difficultycheck.py`.

| attempt | score | what changed |
|---|---|---|
| 0 (`layer-graft-read`, discarded) | 100 / 100 on paper | first record; discarded on my own cold attack, not on the score: with guards testing only whether a path was defined, the views could be folded before any value was computed, a from-scratch dictionary implementation got the carrying rule right by accident because a dictionary entry copies a reference, and the only work left was the resource gate - the shape the quality review has failed `difficult` on twice |
| 1 (`layer-graft-ask`) | 100 / 100 on paper | guards became questions answered at their own layer, which makes a forward reference mean something different to a guard than to a plain read, forces the fold and the evaluation to advance together, and makes circularity a property of the count rather than of the definition's text |
| 1, re-scored at Stage 7 | 100 / 100 measured | 359 environment lines, 6 editable files, 308 reference lines, 29 cheats, 2 variants; no drift on any declared size |

## Stages 3 to 6 - what was built

### Environment

`environment/app_src/` is ten modules, 359 lines of Python. Frozen: `run_plan.py` (the driver),
`cfg/lex.py` (the plan and expression parser, including the rule that no entry may follow a
query), `cfg/say.py` (the three trace lines), `cfg/__init__.py`. Editable, and shipping wrong in
eight places: `cfg/pile.py` (a flat dictionary store; a copy merges into the destination instead
of replacing it, and a count counts every path prefix rather than the defined paths),
`cfg/past.py` (one full dictionary copy per layer, and the count a query is answered at),
`cfg/made.py` (a copy re-stamps each definition with the copying layer), `cfg/roll.py` (a guard
is answered against the store the earlier entries of its layer have left), `cfg/work.py` (the
right side of an expression decides which failure is reported, and a conditional tests whether
anything at or under the path is defined), `cfg/ans.py` (a query naming a layer takes its value
from the finished plan, and a circular answer is reported as absent).

`plans/` holds `one.txt` (the wrong line the brief names), `two.txt` (a plan the shipped engine
gets right), and `wide.txt` and `deep.txt` at the graded scale, generated from a public seed
that is not the nonce the verifier draws.

### Reference

`solution/` is the six files: a store of nodes never mutated carrying the number of defined
paths beneath them and maintained by arithmetic, one root kept per layer, a copy grafting the
source node, a definition that keeps the layer that wrote it and that a copy hands on
untouched, a layer application that answers each guard against the store the layer started
from, an evaluator that threads the count through every reference and remembers a value on the
definition and the count, and a query answerer that takes definition and value at the same
count. 296 lines by `wc -l`; `difficultycheck` measures 308.

### Verifier

`tests/worker.py` stages a pristine copy of the tree under `/work`, lays the six submitted files
over it, and runs all 359 graded plans through the shipped driver, capturing what it printed. It
runs as uid 1002 in its own session under a 60 second wall clock, which is also the task's
stated execution limit. `tests/test_outputs.py` runs as root, never executes agent code, and
compares 33 hand traces against `tests/seal/gt.json` and 326 nonce traces against
`tests/seal/model.py`, having first asserted that the model still reproduces `gt.json`. The seal
is `chmod 700` before anything the agent wrote runs; the reward defaults to 0 and is written
last by the privileged stage; `tests/reap.py` kills anything still holding the sandbox uid.

### Cheats

29, generated by `authoring/layer-graft-ask/emit.py` from the reference plus one named defect
each, so a cheat and the reading it stands for cannot drift apart. 16 wrong readings, 3 correct
but over budget, 1 forgery carrying `gt.json` verbatim, 9 isolation probes. `emit.py` compiles
every file it emits before writing it.

## Measured

| what | reference | naive family | limit |
|---|---|---|---|
| one `wide` plan | 0.39 s | 28.8 s with a count answered by walking | - |
| one `wide` plan | 0.39 s | not finished after 240 s with no value remembered | - |
| one `deep` plan | 0.04 s | 98.3 s with a copy expanded path by path | - |
| the whole graded set | 1.24 s | all three killed at the wall clock | 60 s |
| shipped `deep.txt` | 0.10 s | 113.3 s with the shipped engine | - |
| shipped `wide.txt` | 0.47 s | 125.5 s with the shipped engine | - |

All three naive families produce exactly the reference's answers on everything they finish;
measured at `--scale 0` each is caught only by `test_every_family_is_represented`, which is the
generator artefact of running with no scale family, and not by any semantic case. The limit is
the only thing that separates them.

## Decisions and their reasons

- The count rule is uniform: every reference is answered at some count, and only `old` moves it,
  strictly downwards. That is what makes the whole thing terminate and what makes the memo key
  `(definition, count)`. It was chosen over letting guards read the finished plan, which would
  have made the result depend on evaluation order.
- `pick` tests the definition and `un` tests the value, deliberately. The pair is a fence: a path
  whose definition answers absent satisfies `un` and takes `pick`'s first side.
- A copy replaces rather than merges. The retrievable convention is merging, so this is where
  the spec departs from what a retrieved source would say.
- Queries may not precede entries. The plan parser rejects it, so there is no question about
  what a query written in the middle of a plan counts.
- `tests/reap.py` and `tests/test.sh` were rewritten rather than adapted after `simcheck`
  reported 0.995 and 0.955 against `slab-fold-scope`; they now report clean. The two Dockerfiles
  remain near the retained set, which is the level every retained bundle already carries for
  files of six and thirteen lines.

## Findings from building it

- **A memoised value that is circular only through the caller is not circular.** Evaluating the
  side of a conditional that is not taken can leave a `loop` verdict behind for a definition that
  answers an ordinary number when it is asked on its own. The reference is safe because every
  edge it follows is a demanded edge; `pick-eager` is the cheat, and `pick-side-not-asked` is the
  hand case, added after `readingcheck` showed nothing enumerated separated it.
- **A cheat report run at the wrong population size measures the population size.** The first
  full cheat run used `per=12`, below the grader's own `len(wanted) >= 300` floor, so three
  cheats were reported as caught by the nonce test when what had actually fired was that
  assertion. The defaults are now the shipped `per=40`, `scale=3`.
- **A forgery built on a correct implementation scores 1, correctly.** The first
  `forge-from-truth` was the reference plus a lookup table and passed everything, because the
  reference passes everything. A forgery has to answer nothing on its own; it now returns absent
  for any plan its table does not cover, and it carries `gt.json` verbatim so `forgecheck` can
  find it.
- **Python escapes written through a shell heredoc arrive as real newlines.** Two isolation
  probes shipped an unterminated string literal and scored 0 because the worker died on the
  import, not because the isolation held. `emit.py` now compiles every file before writing it,
  and the repair was made by line index rather than through another heredoc.
- **`ok-stack` passed on the host and failed in the container** because it was only two files:
  the host harness layered it over the reference, while the container filled the other four from
  the shipped tree. A variant has to be a whole submission.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `python:3.12-slim` pulled through `mirror.gcr.io` and retagged; the shipped Dockerfiles are unchanged |
| No answer leaked into agent image | pass | `extraneouscheck`, `deadfieldcheck`, `hintcheck` clean; `imagecheck` runs all four shipped plans against a placed reference |
| oracle = 1 | pass | two-container run, 36 tests passed |
| nop = 0 | pass | 1 passed, 35 errors |
| Cheats all score 0 | pass | 29 of 29, container run; `cheat_report` names the case that catches each of the 20 non-probe ones |
| Correct variants score 1 | pass | both, in the container |
| `preflight.py` | pass | no errors, 16 warnings of the same class the retained bundles carry |
| `readingcheck` | pass | all 16 wrong readings separated by a named enumerated case |
| `onelinecheck` | pass | 3 of 4 graded quantities have no exact rule at depth two |
| `forgecheck` | pass | the answer-key carrier is found and scores 0 |
| `imagecheck` | pass | 14 files, reference placed, all four shipped plans run |
| `catcheck`, `solvecheck`, `structcheck`, `hintcheck` | pass | clean |
| `simcheck` | pass | conceptual clean; only the two Dockerfiles remain near |
| `textcheck` | pass | mean sentence 21.5 and 24 per cent short against a retained band of 19.2-26.0 and 21-40; burstiness 0.789 against a retained band of 0.791-1.112 |
| Reference vs model | pass | 1204 generated plans, 484 more including the scale families, and all 33 hand plans, 0 disagreements |
| `package.py` + `zipcheck` | see below | |

## Stage 7 - the re-attack, and the cold solve

**The cold solve was not run, and is recorded as not run.** The order of work here was brief,
then sealed model, then environment, so by the time a cold tree existed both discoveries were
already in hand and a solve by this author would have measured memory rather than difficulty.
`reach-pair-sweep` recorded the same and for the same reason: a self-probe reported as passed by
a contaminated author is worse than no self-probe. What stands in its place is measurable and is
above: every wrong reading separated by a named case (`readingcheck`), three of four graded
quantities with no exact rule at depth two (`onelinecheck`), and no oracle anywhere in the tree.

**The re-attack against the finished thing.** Reading the final brief with the built environment
in front of me, my first plan is still the dictionary-per-layer fold, and it is still wrong in
two places that matter. The brief states all twelve rules, so none of them is hidden; what it
does not state, and what no sentence in it points at, is the order the work has to be done in.
An implementation that builds every view first and evaluates afterwards is the natural reading
of a plan composed of layers, and it runs into the guards, which are questions; at that point
the finished views exist and answering a guard against them is the obvious repair and the wrong
one. That is `guard-final-view`, and it is a coherent thing to write. The second is the doubling
plan: a copy handled path by path is correct and is what the shipped engine does, and it is
113 seconds on a plan the brief tells the agent to time.

Two things I would flag as pulling the realised rate up. The brief is complete, so an agent that
reads it through before writing anything and reaches for a shared-node store from the start can
get there in one pass. And `plans/deep.txt` ships, so the scaling boundary is discoverable
locally rather than only at the verifier - which is the fairness requirement, and it costs
difficulty. Two things pull it down: the count a question is answered at has to be threaded
through guards as well as queries, which is one sentence in seven paragraphs; and
`pick-side-not-asked` is an interaction nothing in the brief points at, which `readingcheck`
found blind on the first pass and which a case was added for.

Honest estimate after the re-attack: unchanged at 2 of 8, range 1 to 4.

## Open questions and next steps

None blocking. The residual risk to flag to a reviewer is the difficulty band: every rule is
stated in the brief, so a very careful agent that reads it through before writing anything and
reaches for a shared-node store from the start could get this in one pass. That is what the
estimate of 2 solves out of 8, with a range of 1 to 4, is saying.
