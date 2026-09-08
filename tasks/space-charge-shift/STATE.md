# Task state

Working memory for `space-charge-shift`. Updated after every stage. Assume the next session
starts with no memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`

## Assistant's assigned role

Storage-platform engineer. I work on the metadata and accounting layer of a shared object
store: the part that decides which team's budget a file counts against, keeps per-team totals
correct while folders are reorganised under it, and refuses the write that would put a team
over. The retained bundles in this repository are the evidence for this role: their environments
are runtimes whose policy layer decides observable behaviour, and the graded work is settling
what that policy must do when two of its rules pull against each other.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The first prompt named no repository, so there is no
  vendoring, no license question and no upstream diff to survive.
- Task shape chosen: authored-on-top does not apply; the environment is written here.

## Task summary

`/app` is the metadata layer of a shared asset store. Top-level spaces hold folders; folders
hold named entries; an entry is either a folder or a link to an asset. One asset can be linked
under many names, in many spaces. Every asset is charged, in full, to exactly one space: the one
holding its **oldest** surviving link. Each space has a byte limit, and an operation is refused
when it would leave a space over its limit with more bytes than it had before. A script drives
the store and every operation prints one line; `use` prints each space's total. The accounting
layer under `/app/bil` is wrong in four ways and the agent rebuilds it.

The charge is a moving target: removing an asset's oldest link hands the charge to its
next-oldest one, which may be in another space; moving a folder relocates the charge without
creating or destroying any link, because link ages do not change when a link travels; a
recursive delete removes many links at once and every asset's next owner has to be settled
against what survives the whole delete rather than one removal at a time. Checkpoints roll the
store back with the original ages restored, while the age counter itself never rewinds. The
limits make all of this observable: a wrong charge shows up as an operation refused that should
have gone through, or accepted that should not have.

## Why it is hard

Not one rule, and not the number of rules: it is that the natural implementation of each rule
is wrong in a way that only shows when it meets one of the others. Charging at link time is
right until a folder moves; taking the head of a per-asset link list is right until a rollback
restores links newest-first; settling the next owner per removed link is right until two links
of one asset sit in the same deleted folder; refusing whenever a space is over its limit is
right until an operation lowers an already-over space. And a straight recomputation of the
totals from the tree - the implementation that avoids every one of those traps - does not fit
the execution limit at the stated scale, so the fallback that would be reliably correct is not
available.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the plan has
  to settle four separate "when is this decided" questions whose answers point in opposite
  directions - the owning link is fixed at link creation but the space it charges is re-derived
  from where that link now sits; a batch's per-asset outcome is decided against the batch's final
  state, not against each removal in turn; the limit test is decided on the produced state and
  on the direction of change, not on the delta; and the derived totals must survive a rollback
  that restores link ages the accounting cannot re-issue. A first plan settles some of them the
  same way for all four, which is coherent, passes ordinary scripts, and is wrong on the cases
  where two of the rules meet. The execution limit removes the one plan that dodges the whole
  question, recomputing every total from the tree, so the agent cannot buy correctness with work.
- Tactics making that true (docs/DIFFICULTY.md): A1, A3, B2, C1, C2, C3, C4. A1: the retrievable convention is the opposite
  one (documented hard-link quota accounting charges the file to its owner or promotes the newest
  remaining link when the primary goes; here the oldest surviving link owns it and the charge
  follows that link between spaces); A3 the limit gate and the execution limit together admit no
  single known technique - recomputation is correct and too slow, incremental maintenance is fast
  and is where every ownership rule bites; B2 twelve rules that interact, with no per-rule
  feedback because the only observable is the printed line; C1 both sides fenced - refusals that
  must happen and refusals that must not; C2 the obvious oracle is denied, since the store itself
  is the only thing that prints an answer and it prints the agent's own reading back; C3 a
  measured scaling boundary at a stated input scale where recomputation is exact and infeasible;
  C4 exact all-or-nothing grading over enumerated corners plus nonce-generated scripts.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan is
  to keep, per asset, its links sorted by age, take the minimum as owner, cache the owning space
  on the asset, keep one total per space, and for each operation apply the structural effects one
  at a time while adjusting the totals, then check whether any space ends over its limit. Four
  things in that plan are wrong. The cached owning space is stale the moment a folder moves,
  which creates and destroys no link at all. Applying effects one at a time makes a recursive
  delete settle each asset's next owner against links the same delete is about to remove. The
  limit test as stated refuses an operation that lowers an already-over space, which the
  instruction requires to succeed. And walking the moved subtree to re-charge its assets, which
  is the obvious repair for the first defect, is what the wide family is built to make
  infeasible. I would find the first defect quickly, the second only after building a case where
  one asset has two links in one folder tree, and the fourth only after the timing run.
- Estimated solves out of 8: 3 (range 2-4; design target 1, and the Stage 7 re-attack below
  is where the number moved)
- Difficulty score anchor: 50 at first complete submission
- Score history: 2026-09-08 anchor 50, rubric shape recorded at Stage 7
- Leak audit (docs/DIFFICULTY.md), run 2026-09-08 and again after the verifier was resealed:
  the agent tree holds no comment, docstring, README or `.md` file (grep clean), no proper noun,
  and nothing that names or derives an owning space or a space's total. The shipped `bil` is a
  working implementation that is wrong in four places, not a stub and not an oracle: it prints
  its own reading back. `runs/mixed.txt` and `runs/wide.txt` are inputs; no expected output ships
  anywhere in the tree. Every helper in the tree is reached through real behaviour (checked by
  hand against preflight's affordance warnings, which fire on module-qualified calls and are
  noise here as they are on the retained bundles: 20 against 12 for reach-pair-sweep and 15 for
  focus-return-point). `tools/onelinecheck.py` finds no rule of two terms or fewer over the
  fields the environment exposes for any of the three graded quantities. The one real leak found
  was on the verifier side, not in the environment: agent code executing inside the verifier
  could read `/tests/gt.json` and `/tests/model.py`. Script generation moved to a root stage and
  those files are now root-only while the worker runs, which a container probe confirms.
- Cold self-attack (2026-09-08, and honestly qualified): a genuine cold solve was not available
  to me, because I designed the mechanism before the environment existed, so what follows is
  recorded as what it is. Reading only the brief and the tree, the plan I write is: index the
  links of each content by age; owner is the smallest age; keep per-space totals; on a folder
  move, walk the moved subtree and re-charge what it owns; decide an operation by simulating its
  records one at a time and refusing when a space ends over. That plan passes `mixed.txt` and
  most of what I would write by hand. It fails three of the thirty enumerated cases and dies on
  the clock, which is the intended shape. What stands in for the self-probe: the ten wrong
  readings are each separated by an enumerated case (`tools/readingcheck.py`), no graded quantity
  is reproduced by a short rule (`tools/onelinecheck.py`), and the four alternative correct
  implementations all score 1.
- Expert path, described step by step: (1) run the shipped scripts and read `ops.py` to see that
  the runtime hands the accounting layer an effect list per operation and applies nothing until
  the layer approves it; (2) notice that a folder move is one effect naming a folder, not a list
  of links, and conclude that the owning space cannot be stored on the asset; (3) settle
  ownership as "oldest link, current ancestry" and hold per-folder aggregates of the size owned
  beneath each folder so a folder move is a walk up the ancestors rather than down the subtree;
  (4) settle the batch rule by computing, for each asset touched by an operation, its owner in
  the state the operation would produce, and turning that into per-space deltas; (5) implement
  the limit test on the produced totals and the direction of change; (6) run the wide script and
  the timing; (7) work the rollback: the effect list an undo replays carries the original ages,
  so the owner index has to be keyed by age rather than by arrival, and the aggregates have to be
  driven by the same path as the forward direction.
- Originality check: searched 2026-09-08 for hard-link quota accounting, oldest-link ownership,
  subtree usage aggregation with rollback. What exists: filesystem quota documentation (xfs, ext4
  project quotas, GFS2), an NSS guide describing hard links where the file is charged to its
  owner and the newest remaining link becomes primary when the primary goes, a 1996-2001 kernel
  thread proposing tree quotas, and a glusterfs issue about quota accounting being wrong with
  hard links. None of these charges the oldest link, moves the charge when a folder moves, or
  settles a batch against its produced state. No write-up plans this task.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-08, before any environment code. A later change to what "correct" means needs
the contributor's approval; refinements made while building are recorded here as amendments.

### Artifacts the agent produces

    /app/bil/own.py   the per-asset link index and which link owns the asset
    /app/bil/agg.py   the aggregate that answers a space's usage
    /app/bil/gate.py  the limit decision for a whole operation
    /app/bil/edit.py  the accounting update once an operation is applied

Nothing else is read. Everything else in `/app` is the verifier's own pristine copy, so only
those four files can change what a script prints.

### The system, stated exactly

Spaces are named top-level folders, each with a byte limit. A folder holds named entries; an
entry is a folder or a link to an asset. An asset has an id and a size, and exists while it has
a link or an open claim. Every link carries an age: consecutive integers from 1, issued when the
link is created, never reissued, unchanged when the link or any folder above it moves.

An asset with at least one link is charged, whole, to the space holding its oldest link. An
asset with no links is charged nowhere. A space's usage is the total size of the assets charged
to it.

An operation is refused when the state it would produce has a space over its limit whose usage
is higher than before the operation. Structure is checked first and the limit last. A refused
operation changes nothing and issues no age.

Operations, one printed line each, `<i> <op> ok` or `<i> <op> no <reason>`:

    mkdir <path>              path name
    add <path> <id> <size>    path name id over
    link <path> <id>          path name id over
    unlink <path>             path over
    rmdir <path>              path over
    move <path> <path>        path name loop over
    write <id> <size>         id over
    claim <id>                id held
    free <id>                 id held
    limit <space> <n>         path
    snap <name>               name
    undo <name>               snap
    use                       prints `<i> use <space>=<bytes>` for every space, name order

`undo <name>` restores folders, links with their original ages, assets, sizes and limits to the
state at that checkpoint, and discards that checkpoint and every later one. Two things it does
not do: it never rewinds the age counter, so a link created afterwards is newer than every
restored link; and it does not touch claims, so an asset created after the checkpoint survives
the rollback with no links when a claim is open on it, and is destroyed otherwise.

### Graded decisions

  1  the oldest link owns the asset, not the newest and not the first the accounting saw
  2  the charged space is where that link sits now, re-derived after a folder moves
  3  removing the owning link hands the charge to the oldest surviving link, wherever it is
  4  a batch settles every asset against the links that survive the whole batch
  5  a link that is not the oldest changes no charge when it is created, moved or removed
  6  an asset with no links is charged nowhere, claim or no claim
  7  a size change moves with the charge, to the owning space only
  8  the limit refuses only a space that ends over and higher than it started
  9  structure is refused before the limit is considered, and a refusal changes nothing
 10  a rollback restores ages, so ownership after it follows the restored ages
 11  ages issued after a rollback are newer than everything restored
 12  claims are not rolled back, and decide whether a post-checkpoint asset survives one

### Implementation choices the verifier must accept

How the accounting is indexed and aggregated, the container types, the order of any internal
iteration, where the state is kept on the store object, and internal naming. The one thing that
is not free, and is decided by the execution limit rather than by an assertion: the totals
cannot be recomputed from the tree at the stated scale.

### Evidence

Hand-written scripts, one per graded decision plus the must-still-work side of each fence,
compared against `tests/gt.json`, frozen before the verifier was written. Nonce scripts
generated inside the verifier after the agent has finished, compared against an independent
model that shares no code with the environment. The model must reproduce every hand case before
any grading counts. Exact line-for-line comparison, all-or-nothing.

### Independence, stated precisely

Closed to both sides, and therefore evidence of nothing: both maintain a per-folder aggregate of
the bytes owned beneath it, because the execution limit forbids recomputation. Different: the
reference decides an operation by computing per-space deltas from the effect list before it
touches the store, where the model applies the effect to its own store, measures the totals and
inverts it when the limit refuses; the reference keeps ownership in a per-asset structure keyed
by age, where the model keeps a per-asset map from age to folder and re-minimises on change; the
reference follows the runtime's inverse-effect journal through a rollback, where the model holds
whole-store snapshots and restores one.

### Isolation

The verifier executes agent code, so `docs/VERIFIER-ISOLATION.md` applies in full: unprivileged
worker, root-owned locked reward channel defaulted to 0, trusted grader that imports nothing the
agent wrote, checked exit statuses, survivor reaping, pristine overlay of only the four declared
files, and the mandatory reward-tamper cheats.

## Stage 7 re-attack, 2026-09-08

Read cold, with the built tree in front of me, the plan I would write now is: index each
content's links by age and take the smallest as owner; hold a per-folder aggregate of the bytes
owned beneath it so a space's usage is the aggregate at its root and a folder move is two
ancestor walks; decide an operation by working out where every touched content's oldest link
would be in the state it produces; refuse a space that ends over its limit and higher. That is
the reference. So the honest reading is that the plan is now formable in one shot by someone who
has already built it, which is exactly what the re-attack is supposed to expose, and it moved the
estimate from 2 to 3.

What still stands between that plan and a passing submission: nine of the twelve graded decisions
have to be right at once, with no per-rule feedback anywhere, because nothing in the tree prints
a correct answer and the graded population is generated after the run. The three the shipped tree
gets wrong are the ones a first pass reproduces - a link index in arrival order, a content change
that settles only the content joined, a limit test without the direction clause - and each shows
up only in a shape ordinary testing does not build. The execution limit removes the
implementation that would dodge all of it.

One fairness repair came out of this pass. The brief said `wide.txt` was "a third of the size" of
the graded scripts, which invites a linear extrapolation; the cost of a subtree walk grows with
moves times subtree, so the real factor is about nine. The brief now states both sizes in full
and asks the agent to build a script at the graded size and time that instead. The shipped
`wide.txt` was also regenerated so its ratio of contents to assets matches the graded family
rather than the earlier one.

## Contract amendments after the Stage 2 freeze

All made while building, before the first oracle run, and all recorded here rather than folded
away.

1. Content sharing was added to the model of the store. An asset now carries a content tag whose
   size is declared, several assets can carry the same content, and a content is charged once, to
   the space holding the oldest link across every asset that carries it. The first design charged
   per asset, and with per-asset charging the whole task was four local fixes in four files.
   Sharing is what forces the accounting to be keyed by something other than what the runtime
   hands it, and it makes `write` a movement of one asset's links between two contents.
2. `("sz", asset, old, new)` records became `("ct", asset, old, new)`: an asset's size changes by
   taking on other content.
3. The accounting hook fires once per journal record, immediately after that record is applied,
   in both directions. The first design called it once per operation with the store still in its
   pre-state, which cannot work: a rollback that restores a deleted folder has to put the folder
   back before the links inside it can be charged. The gate still sees the whole operation
   against the pre-state store, and that asymmetry is deliberate and readable in `ops.py`.
4. "Ages issued after a rollback are newer than everything restored" was dropped as a graded
   decision. It is unobservable: every link with an age above the checkpoint's counter is removed
   by the rollback, so a counter that rewound would produce the same order. What replaced it is
   observable and is graded: an id an asset has held is never available again (`roll-drop`).
5. `no tag` was added for content a script never declared.
6. The two scripts that ship under `/app/runs` are graded, from the verifier's pristine copy of
   them. The brief promises to grade "the scripts in the tree", and until this was added that
   sentence was not true. A refusal "issues no age" came out of the brief in the same pass: ages
   are only ever observed through their order, so a consumed age is unobservable and the sentence
   had no test behind it.
7. The verifier was resealed after the cheat suite found the hole described in the leak audit.
   Script generation moved from the worker into a root-only stage that writes them to `/feed`,
   and `model.py`, `gt.json`, `cases.py`, `gen.py`, `prep.py` and `test_outputs.py` are mode 600
   before the privilege drop.

## Measurements

| What | Result |
|---|---|
| reference against the sealed model | 30 hand cases and over 1200 generated scripts across five seeds, no disagreement |
| reference, whole graded set, inside the verifier container | 1.65 s against a 60 s budget |
| recompute-a-space-from-the-index variant | 18.5 to 19.8 s for one wide script, about 115 s for the six |
| walk-the-moved-subtree variant | 23.5 to 25.7 s for one wide script, about 141 s for the six |
| shipped tree against the hand cases | 9 of 30 wrong, before the clock is considered |
| wrong readings separated by an enumerated case | 10 of 10 (`tools/readingcheck.py`) |
| alternative correct implementations scoring 1 | 4 of 4 |
| shortest exact rule over exposed fields, any graded quantity | none at depth <= 2 |

## Decisions and their reasons

- Slug `space-charge-shift`: the mechanism is a charge that shifts between spaces without a link
  being created or destroyed. It does not name the oldest-link rule.
- Category Software / Systems: the graded work is storage accounting, atomic application of a
  batched effect, and incremental aggregation. The story is a store, and the skill is systems
  software.
- The environment is compact by design (one runtime, four editable policy files). It does not
  claim B1: the difficulty is the semantic conjunction, as in `focus-return-point`.

## Quality self-review (docs/QUALITY-REVIEW.md), 2026-09-08

Walked criterion by criterion against the finished bundle.

- Instruction against verifier, both directions. Each of the twelve graded decisions in
  `tests/test_outputs.py` has a sentence in `instruction.md`, and each rule in the brief has a
  hand case behind it. Two findings came out of this pass and both were fixed: the brief promised
  to grade "the scripts in the tree" and the graded set did not contain them, and "a refused
  operation issues no age" was a promise nothing could test, because ages are only ever observed
  through their order.
- Output paths. The four artifacts are named with absolute paths in the brief and in
  `task.toml`; the printed line format is given by example.
- Prose. `tools/textcheck.py` against `focus-return-point` reports the candidate at least as
  irregular as the reference on every axis; `tools/structcheck.py` and `tools/hintcheck.py` are
  clean. Read aloud, no run of same-shaped sentences survives.
- Verifier rigour. The tests read what the store printed while running the submitted layer, not
  a report it wrote about itself. `test_outputs.py`, `worker.py`, `prep.py`, `reap.py` and
  `model.py` each open with what they are for and what they refuse to trust. Grading is
  deterministic: the nonce fixes the population, and the only clock in it is the execution
  budget, which the reference clears by a factor of 36.
- Environment hygiene. `environment/Dockerfile` copies `app_src/` and nothing else; the verifier
  installs its own pins (`pytest==9.1.1`, `pytest-json-ctrf==0.5.2`) and no apt package is
  pinned - none is installed at all, since the base image already carries `setpriv` and
  `setsid`. Every path the brief names exists in the tree, spelled the same way.
- Solution quality. `solution/solve.sh` copies four source files into place and runs the store;
  it computes nothing by hand and reads nothing the agent could not.
- Anti-cheating. Nothing in the agent tree carries an expected output. The answer-key probe,
  built from `gt.json` itself, scores 0.
- Metadata. Software / Systems with five specific tags; the difficulty field names the four
  places the first plan is wrong and says the environment is small and terse by design.

One accepted residual: `environment/Dockerfile` and `tests/Dockerfile` are close to the retained
bundles' by `tools/simcheck.py`, because they are five and nine lines of platform boilerplate.
`simcheck` reports the conceptual axis clean - this task grades nothing an earlier one grades.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py space-charge-shift --build` |
| No answer leaked into agent image | pass | grep sweep plus `tools/imagecheck.py`, clean |
| oracle = 1 | pass | two-container run, 33 tests passed, reward 1 |
| nop = 0 | pass | shipped tree is both wrong and over the budget |
| Cheats all score 0 | pass | 19 of 19 in the container |
| `preflight.py` | pass | no errors |
| `harbor check` rubric | not run | harbor is not installed here; the docker two-image runner stands in |

## Handover

What was run here, and what it returned.

- `python3 scripts/preflight.py tasks/space-charge-shift` - no errors, 18 warnings, all of them
  the affordance heuristic firing on module-qualified calls (12 and 15 on the retained bundles).
- `python3 tools/docker_trial.py space-charge-shift --all` in real two-container runs - oracle 1,
  nop 0, and 19 of 19 cheats 0.
- The same runner on each alternative correct implementation - 4 of 4 scored 1.
- `authoring/space-charge-shift/fuzz.py`, `check_cases.py`, `variant_check.py`, `cheat_report.py`,
  `timing.py`, `sync.py`, `build_gt.py` - all clean, with the numbers in the table above.
- `tools/`: hintcheck, structcheck, catcheck, deadfieldcheck, solvecheck, extraneouscheck,
  imagecheck, readingcheck, onelinecheck, forgecheck and zipcheck report nothing. `textcheck`
  against `focus-return-point` reports the brief at least as irregular as the reference on every
  axis. `simcheck` flags only the two Dockerfiles, which are platform boilerplate, and reports
  the conceptual axis clean.
- `harbor check` was not run: harbor is not installed in this container. The two-image runner in
  `tools/docker_trial.py` stands in for `harbor run`, and it is the same two containers with the
  same artifact upload.

Residual risk, stated plainly.

- The difficulty band is stochastic and nothing here can predict it. The honest estimate is 3 of
  8, with the design aimed lower.
- The execution limit is measured on this machine. A platform an order of magnitude slower would
  narrow the reference's 36x headroom, though not enough to reach it.
- The two Dockerfiles are near-identical to the retained bundles' by `simcheck`. They are five
  and nine lines of required boilerplate.

## Open questions and next steps

- Nothing is blocked. If the easiness probe rejects this task, `RAISE-DIFFICULTY.md` applies and
  the first place to look is the wide family: the shipped `bil` is already both wrong and too
  slow, so a winning trajectory would have to have found all four readings and the aggregate.
