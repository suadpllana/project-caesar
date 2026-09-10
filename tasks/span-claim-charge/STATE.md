# Task state

Working memory for `afterquery/span-claim-charge`. Updated after every stage.

## Current stage

`Stage 7 - Pre-flight and packaging` (Stages 1 to 6 complete; see Validation status)

## Assistant's assigned role

Storage-engine engineer working on the allocation and space-accounting half of a
copy-on-write block store: the free map, the spans handed out by it, the per-item coverage
that points into them, and the numbers a volume is charged when several volumes stand on
the same span.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The store is authored here; nothing is vendored.
- Task shape chosen: not applicable (no repository).

## Task summary

`/app` is a small copy-on-write block store driven by a text program: a device of blocks, a
free map over it, `line`s (named sets of items) and `item`s whose coverage points into
`span`s handed out by the allocator. Every command prints one line, so a program's whole
trace is the observable. Five modules under `/app/store/` ship wrong - the allocator, the
span table, the item write path, the line table and the charge side - and the task is to
make the store obey the stated rules on every program and get the graded set through a
60-second limit.

The rules that carry it: a block is rewritten where it stands only when no second claim
covers it; a span goes back to the free map only when no claim covers any part of it;
allocation is best fit with ties to the lowest address and a split across runs, largest
first, when nothing fits; a write releases before it allocates, so it can land on the
blocks it just freed, and the room check is made against the free total that release will
produce; referenced space is the whole length of every span a line stands on counted once,
exclusive space is the part of that no other line stands on; a stamp puts a second line on
every span the origin held; freed-by-dropping a set of lines is the spans whose whole
standing set is inside it.

## Why it is hard

- Expert time estimate: 10 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the two questions
  the rules ask about the same claims want different structures - the write path asks
  whether a *block* carries a second claim, the charge side asks which *lines* stand on a
  span - and a single reference count per span, which is what the first plan reaches for,
  answers neither. The second finding then reorders the write path itself: because the
  fresh blocks are taken only after that write has released the spans it emptied, a write
  can land on the ground it just freed, the run shape at that instant decides how many
  spans it becomes, and the room check has to be made against the free total the release
  will produce. Nothing in the tree confirms any of this one rule at a time, and two
  execution limits forbid answering either question by walking the claims.
- Tactics making that true: A1, A3, B2, C1, C2, C3, C4. A1: the prior for a copy-on-write
  store is that every write allocates; here it rewrites in place wherever no second claim
  covers the block. A3: charges want the line set on a span, the write path wants claim
  multiplicity under a block, and the limit forbids recomputing either - no one structure
  serves all three. B2: best fit with a split across runs, release only when no claim
  survives, coalescing, in-place rewrite, charge per line set, stamp duplication and the
  room check all have to hold at once and each decides the addresses the next command
  sees. C1: always copying fails the ordinary programs, never copying fails the shared
  ones - the trace carries both the blocks kept and the blocks taken. C2: five modules
  ship wrong at once and no expected output ships, so a self-consistent wrong reading
  prints a plausible trace. C3: three exactly-correct naive methods measured at 90.8 s,
  112.3 s and 149.5 s against a 60 s limit the reference clears in 11.2 s. C4: one line
  per command, compared byte for byte, and a wrong release rule moves every later address
  so the tail of a program diverges whole.
- Assistant's attack on the plan: my first plan was one reference count per span, a claim
  list per item, allocate-then-splice on a write, and charges summed from the spans a line
  touches. It is wrong in four places that only show up together: the count cannot tell a
  span carrying two claims of one item from a span carrying one claim of each of two
  lines, and the two cases differ in *both* answers and in opposite directions; the
  allocation has to happen after the release or a full-device rewrite fails for no reason;
  the room check on the arrival total refuses writes that must succeed; and summing the
  charges per query is exactly correct and eight times over the limit. I could see where to
  start and could not have committed to the structures without running the programs.
- Estimated solves out of 8: 2 (designed at the hard edge; the realized rate drifts up)
- Difficulty record score (tools/difficultycheck.py): 100/100 on the first attempt,
  2026-09-10, `authoring/span-claim-charge/difficulty.toml`. There was no earlier attempt:
  the design was scored before any code and reached the band as written. Re-measured
  against the built tree at Stage 7 on the same date: 100/100, with 630 environment lines,
  5 editable files, 605 reference lines, 44 cheats and 2 variants; the record's planned
  sizes were updated to the measured ones.
- Difficulty score anchor: not yet submitted; no pipeline anchor.
- Score history: 2026-09-10 100 (pre-code record); 2026-09-10 100 (built tree measured).
- Leak audit: no span stores a count of the lines or claims standing on it - a span is a
  start and a length, and every sharing answer is derived from the claim table the agent
  builds. No frozen module answers a question the task grades: `base/text.py` formats,
  `base/feed.py` parses, `base/box.py` builds the store and `ops.py` dispatches, and none
  of them touches a span. The shipped allocator has no `total()` entry point, because an
  unused one is a hint at the room check that the task turns on; `deadfieldcheck` and
  `preflight` are both clean on unused affordances. The trace fields `new`, `keep` and
  `rel` report what the shipped store did, which is wrong, so they confirm a reading only
  once the reading is right. No expected output ships for any program in `/app/progs`, and
  the graded programs are generated inside the verifier from a seed drawn after the
  agent's container is gone. Nothing in the tree is a function of the correct trajectory.
  Considered and kept: a span carries a claim count per line (`Span.by`). It is a primitive
  the shipped store already maintains, the rule it serves is stated outright in the brief,
  and what the task turns on is what a solver builds beside it - the claim ranges the write
  path needs, the running totals the limit needs, and the write ordering. The derivations
  themselves - referenced, exclusive, freed-by-dropping, and the in-place answer - are
  computed nowhere in the shipped tree.
  `tools/onelinecheck.py` measured the shape of the answer over 4290 recorded decisions:
  three of the five graded quantities - the in-place test, how many spans a write becomes,
  and whether a write is refused - have no exact rule at depth two over the features the
  agent can read at that moment; the two that do (`claims_left == 0` for release and
  `claims_on_span == own_claims_here` for exclusivity) are the two the brief states
  outright and both have a cheat.
- Expert path, described step by step: run the shipped programs and read `new`, `keep` and
  `rel` against the stated rules; separate the two sharing questions - multiplicity under a
  block, and the set of lines on a span; give each span its claim list and a count per
  line and derive both answers from those; rebuild the write path as boundaries, then drop
  and release, then allocate, then splice; lay the allocated pieces over the fresh
  stretches in item order, splitting a stretch across two pieces; index the free map by run
  length as well as by start so best fit and coalescing are both cheap; carry referenced
  and exclusive as running totals moved on the zero-to-one and one-to-two transitions;
  check the room against the free total the write's own releases will produce.
- Originality check: searched 2026-09-10 for public write-ups of extent-level shared and
  exclusive space accounting and of copy-on-write allocator exercises. What exists is
  filesystem quota-group documentation defining referenced and exclusive space for volumes
  that share extents, and general articles on why deleting most of a file frees nothing.
  Neither states an allocation policy, an in-place rewrite test, the order in which a write
  releases and then allocates, or how one allocation is laid across several stretches of an
  item. No exercise, kata or repository implementing this contract was found. The store,
  its command language and its rules are authored here. `simcheck` reports that this task
  grades nothing an earlier one grades; its only similarity hits are the two Dockerfiles
  and the verifier harness, all of which sit below the retained bundles' own similarity to
  each other.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-10. Changing any of it changes what "correct" means and needs approval.

- Artifacts the agent produces: `/app/store/dev.py`, `/app/store/hold.py`,
  `/app/store/item.py`, `/app/store/line.py`, `/app/store/tally.py`. Nothing else is read
  from the agent's container.
- What is checked: the verifier lays those five files over its own pristine copy of the
  tree and runs every graded program through `base.feed.run`, comparing the trace line for
  line. 48 enumerated programs are checked against `gt.json`, frozen before the grading
  file was written; 366 generated programs are checked against the sealed model, from a
  seed drawn after the agent's container is gone. Every program must match exactly.
- Tolerances: none. Exact string equality on every line of every trace, all or nothing.
- Ground truth, and where it lives: `tests/seal/gt.json` and `tests/seal/model.py`, in a
  directory owned by root with mode 700, unreadable by the uid that runs the submitted
  store. The grader asserts that the model still reproduces `gt.json` before it grades.
- Graded decisions (13): best-fit allocation with ties to the lowest address; the split
  across runs, largest first, when no run fits, and the refusal when the total does not;
  the room check made against the free total the release will produce; the in-place
  rewrite test per block; a span released only when no claim covers any part of it;
  coalescing on release; release before allocation inside one write; one allocation laid
  over the fresh stretches in item order; referenced space as whole spans counted once per
  line; exclusive space by standing line set; a stamp putting a second line on every span;
  freed-by-dropping as the spans whose standing set is inside the named set; and a refused
  command leaving the store unchanged.
- Prong C tactics in the contract: C1 (both sides of the in-place fence, both sides of the
  release fence, both sides of the room check), C2 (no expected output ships and five
  modules are wrong at once), C3 (a 60-second wall clock on the whole graded set, with the
  input scale stated in the brief), C4 (byte-exact traces over enumerated corners and a
  seeded population the submission cannot have seen).
- Route-around guard: only the five modules are taken. The program reader, the trace
  formatter, the store record and the command table are the verifier's own copies, so the
  output format and the command semantics cannot be reshaped, and a submission that
  rewrites them changes nothing (`cheat-probe-rewrite-frozen`).

## Decisions and their reasons

- The map command prints coverage as maximal stretches. Without that, the printed claim
  boundaries would depend on where an implementation happened to split, and the verifier
  would be grading an implementation choice rather than the contract. Both correct variants
  cut claims in different places and print the same picture.
- Spans never split or shrink. A partially claimed span stays whole, which is what makes
  "overwriting the middle frees nothing" true and keeps the free map a function of span
  lifetimes rather than of byte ranges.
- The write path releases before it allocates. Both orders are implementable; this one is
  stated in the brief because it is the one that makes a full-device rewrite possible, and
  it is what forces the room check to be made against the post-release total.
- The device size is the first line of every program, so the generated families can pick a
  scale without a separate command.
- `line.py` ships with a `drop` that releases nothing and `tally.py` ships recomputing the
  charges by walking the spans: the shipped tree is therefore both wrong and, on the wide
  family, too slow, which is the shape the task is about.
- `tests/Dockerfile` installs no apt packages. `setpriv`, `setsid`, `runuser`, `install`
  and `useradd` are already in `python:3.12-slim`, and `reap.py` reads `/proc` directly
  rather than shelling out to `pkill`, so the verifier image needs nothing from a distro
  mirror at build time.
- Three enumerated cases were added at Stage 6, all additive. `alloc-fit` came from
  `tools/readingcheck.py` reporting first fit blind to the set: `alloc-best` gives every free
  run the same length, where first fit and best fit agree. `chart-empty` and `vac-short` came
  from the instruction-to-test sweep - the brief promises that nothing follows the size when
  an item is empty, and that a defragment is refused when the release would not free enough,
  and neither had a case. `build_gt.py` reports 48 frozen, 3 added, 0 moved across the three.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `tools/docker_trial.py --build` |
| Verifier image builds | pass | same |
| No answer leaked into agent image | pass | `imagecheck` clean; `tests/` and `solution/` are never copied into `environment/Dockerfile` |
| oracle scores 1 | pass | 51 tests passed in 9.8 s, reward=1 |
| nop scores 0 | pass | 1 passed, 50 errors, reward=0 |
| Cheats all score 0 | pass | 46/46 trials behaved as required through the two-container runner: oracle 1, nop 0, 44 cheats 0 |
| | | the three exactly-correct-and-slow readings are caught by the wall clock (the worker never finishes); the forgery is caught on content alone - 50 passed, 1 failed, the one being the generated population |
| Correct variants score 1 | pass | both score 1 through the two-container runner (51 tests passed each); on the host they settle the graded set in 8.9 s and 8.8 s |
| | | `ok-blocks` is the sealed model re-split into the five-module shape - per-block items, a free map indexed by run length; `ok-sized` keeps the claim shape and differs in the free-map index, the in-place algorithm and how exclusivity is tracked |
| `preflight.py` | pass | no errors, no warnings |
| `difficultycheck` | 100/100 | in band, measured against the built tree |
| `readingcheck` | pass | all 29 wrong readings separated by an enumerated case |
| `onelinecheck` | pass | 3 of 5 graded quantities have no rule at depth two |
| `deadfieldcheck` / `extraneouscheck` / `catcheck` / `hintcheck` / `solvecheck` / `forgecheck` / `imagecheck` | pass | clean |
| `textcheck` against a passed instruction | pass | no findings; burstiness 0.876 against 0.877 |
| `simcheck` | pass | grades nothing an earlier task grades |
| Reference against model | pass | 48 hand cases and 366 generated programs agree; 3600 further random programs agree |
| Resource gate measured | pass | reference 11.2 s; naive readings 90.8 s, 112.3 s, 149.5 s; variants 8.9 s and 8.8 s; limit 60 s |
| `harbor check` rubric | not run | harbor is not installed in this environment and no model API key is configured |

## Isolation, as measured inside the verifier container

Two probes leave a note in `/work/probe.log`, which
`authoring/span-claim-charge/probe_evidence.py` prints. Both scored 0, and this is what they
saw, which is the part that matters:

- `cheat-probe-privilege`: `uid=1002 euid=1002`, and `PermissionError` on
  `/logs/verifier/reward.txt`, `/tests/test_outputs.py`, `/tests/seal/gt.json` and
  `/tests/pristine/ops.py`. The submitted store runs unprivileged and can reach neither the
  reward, nor the grader, nor the answers, nor the verifier's own copy of the tree.
- `cheat-probe-answer-key`: `PermissionError` on `/tests/seal/gt.json`,
  `/tests/seal/model.py`, `/logs/verifier/nonce` and `/logs/verifier/per`, and
  `ModuleNotFoundError` on `import model`. The seed and the family size the grader uses are
  out of reach, so a submission cannot shrink its own exam, and the answers cannot be read
  or imported.

Both runs also show `worker exit 124` and `reaped 0, still holding the sandbox uid: 0`: the
wall clock fired on a store that is too slow, and nothing outlived it.

## Stage 7 re-attack, and what is not proved

Read cold, the instruction states every rule and no method. It names the limit and the
input scale, which fairness requires, and says nothing about how to index the free map,
how to carry the charges, or where to split a claim - the three places the work actually
is. The first plan is still wrong: `onelinecheck` says the in-place test, the number of
spans a write becomes and the refusal are not reachable by a short rule over what the agent
can see, and `readingcheck` says every wrong reading of the stated rules is separated by
an enumerated case. The environment is 630 lines over 20 files, which does not exceed an
attention window, so B1 is not claimed and the difficulty rests on the interaction and on
the three measured limits. Estimated solves stays at 2.

The cold self-probe was not run, and is recorded as not run rather than as passed. The
order here was brief, then reference, then model, so by the time an environment existed
both discoveries were already in hand; a self-probe reported as passed by a contaminated
author is worse than no self-probe. Standing in its place: the reading separations above,
the depth-two measurement, the fact that no expected output ships for any program, and the
three naive-but-correct methods that are exactly right and over the limit.

Residual risk to flag to a reviewer: the brief is complete, as the house style requires, so
a careful agent gets every rule for free and the whole difficulty rests on the structures
and the limits. That is the same shape as the retained tasks, but it is the axis on which
this one would fail if it fails.

## Quality self-review, criterion by criterion (docs/QUALITY-REVIEW.md)

Instruction and verifier agree in both directions. Every graded decision has a sentence:
allocation and the two refusals in paragraph 4, the in-place test and the write ordering in
5, sharing in 6, the charges, the stamp and freed-by-dropping in 7, defragmenting in 8, the
output shapes in 9, the refusal codes in 10. Every sentence has a case: the sweep that
found `chart-empty` and `vac-short` was exactly this pass run the other way, and the claim
that comments and blank lines are skipped is now carried by `keep-sole`, whose program has
both. The five artifact paths are named in paragraph 3 and all exist; a script checked each
backticked path in the brief against the tree.

Prose. `tools/textcheck.py` against `publish-settle-order`, which passed the screen, reports
no findings on any axis; burstiness 0.876 against its 0.877, no stock phrases, no hedges, no
triads. No requirement is stated twice. No headings, no bullets, plain ASCII.

Verifier rigor. The tests never read a state the agent could write directly: the worker lays
the five submitted modules over the verifier's own tree and every trace comes from running
the programs. `tests/test_outputs.py` opens with the frozen contract, thirteen numbered
decisions, and says what is an implementation choice; the grader's fragile parsing sits
inside its own guard and every value that came from agent code is treated as hostile.
Generation is seeded, and the one wall-clock dependence is the execution limit, which is
itself a graded property and is stated in the brief.

Environment hygiene. `environment/Dockerfile` copies `app_src/` and nothing else - not
`tests/`, not `solution/`. The verifier's dependencies are pinned in `tests/Dockerfile`
(`pytest==9.1.1`, `pytest-json-ctrf==0.5.2`) and nothing is fetched at trial time. The agent
tree has no comment, no docstring and no `.md` file, checked with an AST pass.

Solution quality. `solution/solve.sh` copies the five reference modules into place and runs
two programs; it computes nothing by `echo`. It uses only what the agent could use.

Anti-cheating. No expected output ships for any program. The forgery cheat carries the
frozen answers for all forty-eight enumerated programs, passes every one, and fails on the
generated ones. Grading is exact string equality, so a degenerate output fails on the first
line. No repository is cloned.

Metadata. `category = "Software"` with `subcategory = "Systems"` from that row; five tags
naming the techniques and none restating the taxonomy; `difficulty_explanation` names the
step - a count per span answers neither of the two questions the rules ask - and says that
the terse identifiers are a deliberate register; `solution_explanation` describes the method
and the order it is forced into; `verification_explanation` says why passing means the work
was done; `relevant_experience` is specific to this kind of engine and claims no employer,
credential or duration; `expert_time_estimate_hours = 10` matches the difficulty claim.

## Open questions and next steps

Package and deliver.
