# Task state

Working memory for this task. Updated after every stage; assume the next session starts with no
memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`, after the easiness recovery recorded below (probe 2 of 3
on 2026-09-09). The two-container gates cannot be run in this session: Docker's daemon starts,
but the egress policy denies Docker Hub's blob CDN (`production.cloudfront.docker.com`, 403 on
CONNECT), so no base image can be pulled and no image can be built. Everything else has been
run - see the validation table, and read the `host trial` rows as host emulation rather than
container evidence. The recovery's exit gate is the platform's own easiness probe, which has
not yet been run against this build; the recovery is therefore **pending** at gate 1 of section
6 of `RAISE-DIFFICULTY.md`, and this bundle is the candidate for it.

## Assistant's assigned role

Not supplied in the contributor's words - the first prompt carried no seed idea, so the task was
selected here. Working persona: platform engineer on an extension host, the kind that loads
units of code at run time, decides which of them answers a published name, and has to keep the
answer stable while units come and go.

## Source repository

- Repo URL: none - idea-based task.
- Task shape: not repo-based, so neither authored-on-top nor ablation applies.

## Task summary

`/app` is an extension host. A program is a text file of ops: units are declared with what they
need (a dependency, which keeps its target up, or an ordering edge, which does not), the names
they publish (some as fallbacks), the startup calls they make, and whether a call may bring
them up (`auto`); then the program brings units up, calls names and releases holds.
`/app/run_host.py` prints one event per line: `up`, `down`, `run`, `miss`, `dead`. The frozen
half of the tree is the record table, the declaration store (including the list of `auto`
marks in the order made), the publication order (a linked list that can be spliced into), the
hold ledger and the event writer; the six files under `/app/link` decide the activation walk,
which publications a caller reads, which publisher answers a name, what a call does, whether a
live unit has to stay, and what a released hold takes down. `act` brings a unit up for
everyone; `open` brings a whole activation up into a scope only its own members can read, and
`act` on a unit that is up in a scope makes it public where it stands. A call that finds
nothing it can see brings up the first `auto` unit that could answer it, as if the caller had
named it as a dependency: published directly ahead of the caller, into the caller's read scope,
with no hold, kept up by the caller. All six ship wrong. The graded artifact is those six files;
the verifier overlays them onto its own copy of the tree and compares the trace of every
program, line for line.

## Why it is hard

- Expert time estimate: 12 hours.
- Why a frontier agent cannot one-shot the plan (the strategic answer): every rule is stated,
  and the structures each rule seems to ask for - a serial minted at publication, per-name
  buckets per scope sorted by it, a heap keyed by it, one scope attribute per unit, a ledger fed
  by publication and retirement, an in-progress set local to one activation - are the standard
  ones, and the easiness probe showed three agents choosing them on sight. One rule invalidates
  all six at once: a unit brought up by a call is published directly *ahead* of its caller, as a
  dependency would be, into the caller's read scope, held by nothing, kept by the caller. The
  brute-force model of that rule is trivial (a list with `insert`), so an agent's own oracle
  confirms nothing about the fast structures; and the fast structures fail on programs an agent
  does not write unprompted - a competitor opened privately before the load and promoted after
  it, sixty loads in front of one caller, a load from a promoted unit, a load from inside a
  startup call of a unit part way up.
- Tactics making that true: A1, A2, A3, B2, C1, C2, C3, C4.
  A1 - the prior for a lazy load is coherent and specifically wrong twice: it appends, and it
  holds. The prior for a promoted unit is that it reads what its publication reads. All stated
  the other way.
  A2 - nothing is named: no lazy binding, no generation, no label, no order maintenance, no
  index. The brief says where a unit is published and what keeps it up.
  A3 - insertion ahead of a live unit, first-in-order resolution across two buckets, and
  last-first retirement, all at scale, have no single structure that gives all three; and the
  key that admits insertion must also be the identity that separates two lives of one record.
  B2 - one event, the load, is an order event, a scope event, a retention event and a
  resolution event at once, and the four modules that own those have to agree on it. There is
  no per-decision feedback: all six shipped modules are wrong, the shipped load is wrong in four
  ways at once.
  C1 - both fences on every new axis: `auto-bound` against `auto-plain`, `auto-scope` against
  `auto-scope-mates`, `auto-dead` against `auto-late-mark`, `cycle-stays` against `casc-order`,
  `promote-reads-home` against `scope-no-republish`.
  C2 - no oracle: a spec-derived brute-force model is right for free and transfers nothing.
  C3 - six measured boundaries, each with a fast path that follows from an invariant (the order
  is spliced into only directly ahead of a live unit; each bucket is a subsequence of one order;
  retention changes only at publication, load and retirement). Quiet numbers, one program each
  against a 60 s limit for all 456: comparing by position 43 s, one list per name filtered 46 s,
  rebuilding the index per load 202 s, scanning the order 281 s; retention by scan 132 s,
  candidates by rescanning 77 s. Reference: 5.2 s for the whole set.
  C4 - all-or-nothing over 56 enumerated programs and 456 nonce programs in twelve families,
  generated inside the verifier from a seed drawn after the agent's container is gone.
- Assistant's attack on the plan: my first plan, read cold, is the one the three probe agents
  wrote - buckets per scope and name ordered by a serial, a heap by serial, a ledger fed by two
  events - plus "on a miss, bring the auto unit up with the ordinary activation and resolve
  again". That plan is wrong in six places that the brief states and I would not have
  connected: the serial orders nothing once the load lands ahead of the caller; a float midpoint
  survives everything but the fan family; promotion needs two scope attributes because the load
  goes into the *read* scope; the ledger needs a third writer and the caller's record needs to
  remember what it bound; the in-progress set has to be shared or a boot inside the load
  re-enters its own unit; and the answer after the load is a re-resolution, not the unit. I
  would have found the first by thinking about `auto-order`, the second never without the fan
  family, and the others one at a time from hand cases I would have had to invent.
- Estimated solves out of 8 after the easiness repair: 2 (honest range 1 to 4). Measured before
  it: 2 of 3, which reads as 5 to 7.
- Difficulty score anchor: not yet submitted.
- Score history: easiness probe 2026-09-09, 2 of 3 solved, on commit `654a50c`.
- Leak audit (docs/DIFFICULTY.md), run as a procedure:
  - Can a shipped file reproduce a graded answer by a join, a sort or a field comparison? No.
    The tree ships eight programs and no expected trace for any of them. The answer is a
    sequence of events produced by running a program; nothing in the tree stores one.
  - Is there a stored derived quantity? No. `Rec` holds what the program declared - `needs`,
    `pubs`, `boots`, `auto` - plus `live`, `uses` and the order links, which the frozen order
    module maintains; `Host.autos` is the list of marks in the order made, which is what the
    program said and nothing derived from running it. There is no publication key, no
    generation counter, no resolution cache, no dependent list and no binding list in the
    shipped tree: every one of them is the agent's to invent.
  - Unused affordances? `reg/order.py` has `put`, which the shipped `walk.py` uses (wrongly:
    for the loaded unit and not its closure). Every other function in `reg/` and `ops.py` is on
    the live path; `link/` exposes exactly the entry points `ops.py` and the shipped modules
    call.
  - Manifests? None. Self-labelling data? None. Any artifact that is a function of the correct
    trajectory? No - `gt.json` is sealed in the verifier image and never enters the agent's
    tree. Free join keys or callable difficulty? The shipped host is callable and wrong, which
    is the opposite. Per-axis confirmation before commit? No - one trace per program,
    all-or-nothing.
- Expert path, described step by step: read `ops.py` to learn the op set and which of the entry
  points each op reaches; read `reg/tab.py` and `reg/order.py` and notice that records are
  reused across lives and that the order is a linked list with an insertion primitive; write
  the activation walk with publication and startup interleaved per unit and the in-progress set
  on the host; mint a key per publication that is both its identity and its place, and make the
  key admit insertion directly ahead of a live unit (a tuple with a suffix, or an exact
  fraction between neighbours); keep two attributes per unit, what its publication is and what
  it reads; keep buckets per scope and name sorted by key and answer the earlier of the two
  heads; on a miss, bring the first `auto` unit in mark order that is neither up nor part way up
  up ahead of the caller into the caller's read scope, record the binding on the caller's
  record, and resolve again; keep the ledger fed by publication, binding and retirement and the
  cascade queue keyed by the same key; time `progs/wide.txt` and `progs/tear.txt`, multiply by
  three, and check it against the limit.
- Originality check: searched again on 2026-09-09 for the composite (extension host, lazy
  activation on first use, the lazily loaded unit taking a dependency's place in the
  resolution order rather than the time it was loaded, kept up by its caller, published into
  the caller's scope). The neighbouring real machinery is retrievable - OSGi lazy activation,
  where wiring is fixed at resolve time and activation happens on first class load; VS Code
  activation events; dynamic-linker lazy binding - and the principle that resolution order is
  not activation-time order is exactly what those systems have. No public description states
  this rule set, and the graded object is this host's exact trace.

## Verifier contract - FROZEN

- Artifacts the agent produces: `/app/link/walk.py`, `/app/link/view.py`, `/app/link/pick.py`,
  `/app/link/site.py`, `/app/link/want.py`, `/app/link/drop.py`. Nothing else is read from the
  agent.
- What is checked: the verifier overlays those six files onto its own pristine copy of the
  tree, runs every graded program through `ops.ex`, and compares the printed event list line
  for line. 56 enumerated programs are checked against `tests/seal/gt.json`; 456 programs
  generated from a nonce drawn at verification time (twelve families, 45 small programs each,
  three of each large size - `PER=45` in `tests/test.sh`, which every count in the prose is
  derived from) are checked against `tests/seal/model.py`. The model must reproduce `gt.json`
  exactly before anything else is graded. Every program must match.
- The rules are the sixteen numbered decisions in the docstring of `tests/test_outputs.py`.
  Decisions 14 to 16 (the load), the read-scope clause of decision 5, the mutual-dependency
  clause of decision 10 and the no-self-naming guarantee of decision 1 were added on
  2026-09-09. Every one of the 36 answers frozen before that date came out byte-identical
  afterwards, which `build_gt.py` checks on every run. One corner changed meaning: a unit made
  public by `act` used to read public publications only in the sealed model and now goes on
  reading its own scope. No frozen program and no generated program exercised it, so no answer
  moved; it is recorded here as a contract change all the same.
- Tolerances: none. Exact string equality on an ordered list of lines.
- Execution limit: the worker that runs the submitted host has a 60 second wall clock, stated
  in the instruction. Exceeding it is scored 0.
- Ground truth: `tests/seal/gt.json`, built by `authoring/publish-settle-order/build_gt.py` from
  the sealed model and checked against the reference; baked into the verifier image only, in a
  directory `chmod 700` before any agent code runs.
- Isolation: the worker runs as uid 1002 in its own session under `timeout`, `/logs/verifier`
  is root-owned and `chmod 700` before any agent code runs, the reward defaults to 0 and is
  written last by the privileged stage, survivors are reaped by uid, and the grader never
  executes agent code.
- Prong C tactics used: C1 (both fences enumerated on every axis), C2 (no oracle - all six
  shipped modules are wrong and a brute-force model transfers nothing), C3 (six measured
  boundaries against the execution limit), C4 (nonce-generated population plus enumerated
  corners, all-or-nothing).
- Route-around guard: only the six files are declared artifacts, so the rest of the runtime -
  the op dispatch, the record table, the declaration store, the order, the program reader -
  cannot be reshaped by the agent.

## Stage 7 re-attack (D7)

Read cold, the brief hands over the rules and nothing else. The first plan it supports is the
one three probe agents wrote before the load existed, plus the obvious extension: on a miss,
bring the `auto` unit up with the ordinary activation and resolve again. That plan is right in
shape and wrong in six places, and the brief cannot be blamed for any of them, because each is a
consequence the reader has to work out rather than a rule the reader has to read:

- a serial orders nothing once a publication can land ahead of the caller, so every structure
  keyed by it - buckets, heap, promotion insert - has to be rekeyed by something that admits
  insertion and still identifies a life of a record;
- a float midpoint is that something for fifty loads in front of one caller and not for sixty;
- the load goes into the caller's *read* scope, which a promoted unit still has, so one scope
  attribute is one too few;
- the caller keeps what it loaded, so the ledger has a third writer and the caller's record has
  to remember what to give back when it goes down - not when it next comes up;
- a startup call inside the load can miss on a name the unit part way up publishes, so the
  in-progress set has to be one set on the host;
- the answer after the load is whatever is first in the order now, which is the loaded unit's
  own dependency when that publishes the name.

Are the load-bearing facts still distributed? The record-reuse fact is readable only in
`reg/tab.py`, the insertion primitive only in `reg/order.py`, and `tools/onelinecheck.py`
confirms mechanically that none of the three graded quantities has an exact rule of two terms
over the fields the tree exposes. Has the instruction come to telegraph the method? It states
the limit and the input scale, as a measured C3 must, and never the index or the key; it states
where a loaded unit is published and what keeps it up, and never how to represent either.

The self-probe proper was not run, and is recorded as not run: by the time this environment
existed the design was in hand, and a self-probe reported as passed by a contaminated author is
worse than none. The probe trajectories, the reading separations, the layer report and the
no-short-rule result stand in its place.

Estimated solves out of 8 after the re-attack: 2 (honest range 1 to 4).

## Decisions and their reasons

- The publication key is deliberately absent from the shipped tree. Shipping a serial, a label
  or a generation counter that nothing reads would be a dead field, and `deadfieldcheck` exists
  because a dead field is read as a hint. The contract states that a returning unit is not the
  one that left and that a loaded unit stands ahead of its caller; how to represent either is
  the agent's to invent.
- The frozen order became a linked list with `put(h, r, before)` on the easiness recovery,
  because a dict cannot express insertion and a list makes retirement linear in the order. The
  frozen half stays correct and cheap; what it does not offer is a comparable position, and
  `pos` is a walk. The shipped `walk.py` uses `put` wrongly (for the loaded unit, not its
  closure), so the primitive is on the live path and is not an unused affordance.
- `Host.autos` is a declaration store, not a derived quantity: the list of marks in the order
  the program made them, which is what the rule refers to. Without it the agent would have to
  reconstruct mark order from a dict it has no hook into, which is busywork rather than
  difficulty.
- A promoted unit goes on reading its own scope. The alternative (reads public only) was what
  the sealed model did before 2026-09-09 and what no program exercised; the probe's trial 2
  took the other reading and flagged it. A scope is where a unit came up, `act` acts on its
  publication, and the load rule needs the read scope to be a property of the unit. Recorded as
  a contract change above.
- All six modules ship wrong, and the shipped load is wrong in four ways at once (appends the
  closure, holds, answers with itself, searches in declaration order), so running the host
  confirms nothing about the load.
- `PER=45` in `test.sh`, and every count in the brief and the metadata is derived from
  `gen.programs` at that value. It was 60 before the recovery while the prose said 45; the
  prose was right and the harness was not.
- `fan-deep` is the one enumerated program that is mechanical rather than hand-readable: sixty
  loads in front of one caller, because a float-midpoint key is exact for the first fifty-odd
  insertions at one spot and wrong after that. It is kept in the enumerated set so the layer
  report can name it rather than leaving the float reading to the nonce population alone.
- Six readings are semantically identical to the reference on purpose and are separated by the
  execution limit alone; `readings.py` and `readingcheck` both report them as equivalent, and
  `cheat_report.py` requires the worker to be cut off for each of them. They are measured on a
  quiet machine; measured under three parallel jobs the same numbers came out 1.5 to 3 times
  larger and were nearly shipped.
- `tests/pristine/` has to be re-synced whenever the shipped tree changes.
  `authoring/publish-settle-order/sync_pristine.py --check` is the guard.
- The wide and tear examples ship at the size of the graded ones, and the brief says how many
  there are, so timing them is a measurement rather than an extrapolation across a superlinear
  cost. `lazy.txt` ships as a readable example of a load; no expected trace ships for any
  program.
- Events are printed in occurrence order, not sorted, because the order is what several of the
  decisions are about, and a load's events come before the call's own.
- `tests/seal/` holds the model and the frozen answers and is `chmod 700` before the worker
  starts. `cheat-probe-answer-key` and `cheat-probe-hijack-driver` are the proof, and both
  report the denial rather than only a zero. `tools/forgecheck.py` and `tools/hintcheck.py`
  look in `tests/seal/` first so the kit and the bundle agree about where truth lives.
- `environment/Dockerfile` and `tests/Dockerfile` read as near-copies of two retained bundles
  in `simcheck`; they are seven and a dozen lines of `FROM`, `RUN mkdir`, `COPY`, and there is
  no honest way to write them differently. `simcheck` finds nothing conceptual.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model | pass | 56 hand cases, 456 nonce programs on two seeds plus the scaled large families, 0 disagreements |
| Frozen answers held through the contract change | pass | `build_gt.py`: 36 of 36 pre-recovery answers byte-identical, 20 new |
| Wrong readings separated | pass | 54 readings; 48 caught by a named hand case, 6 by the limit alone; `busy-per-load` needed its edit fixed before it was a reading at all |
| `tools/readingcheck.py` | pass | 48 separated, 6 equivalent (the timed-only six), no blind reading |
| Execution boundaries measured (quiet machine) | pass | reference 5.2 s for the set; one wide: positions 43 s, filtered list 46 s, rebuild per load 202 s, scan 281 s; one tear: retention scan 132 s, rescanning sweep 77 s; limit 60 s |
| `tools/onelinecheck.py` | pass | no short rule for any of the three graded quantities |
| `tools/imagecheck.py` | pass | 24 files in the image; the reference runs the shipped programs inside it |
| `tools/catcheck.py` | pass | Software vocabulary present in the environment, not only in the prose |
| `tools/deadfieldcheck.py` | pass | clean |
| `tools/extraneouscheck.py` | pass | clean |
| `tools/solvecheck.py` | pass | clean |
| `tools/hintcheck.py` | pass | no refutation, emphasis or stale figure |
| `tools/structcheck.py`, `tools/textcheck.py` | pass | no findings against `focus-return-point`; the cadence finding was repaired by opening backtick-led sentences with a word |
| `tools/simcheck.py` | pass with note | the two Dockerfiles against retained bundles; nothing conceptual |
| `tools/forgecheck.py` | pass | `cheat-forge-from-truth` carries every frozen answer and is caught by the nonce population alone |
| `tools/leakcheck.py` | run | one shared rule sentence in trial 1, nothing in trials 2 and 3, against the brief before the recovery |
| `cheat_report.py` | pass | 65 of 65 cheats caught by the layer named for them (see the final run recorded below) |
| host trial oracle = 1 | pass | emulated two-stage run, real `tests/test.sh`, 59 tests passed |
| host trial nop = 0 | pass | the shipped host is both wrong and over the limits |
| host trial cheats = 0 | pass | 65 of 65 cheats scored 0 in the emulated trial |
| Correct variants = 1 | pass | `ok-flat`, `ok-stack`, `ok-count`, each 59 tests passed in the emulated trial |
| Isolation probes | pass | uid 1002, `PermissionError` on the seal, the reward channel and the grader's seed |
| `package.py` + `tools/zipcheck.py` | pass | see the packaging line at the end of this file |
| `preflight.py` | pass | no errors; the warnings are the standing unused-function notes on entry points `ops.py` calls |
| Docker oracle/nop | BLOCKED | image pull denied by the egress policy in this session |
| `harbor check` rubric | not run | harbor is not installed in this environment |
| Easiness probe (exit gate) | PENDING | the platform's probe has not run against this build |

## Easiness recovery - 2026-09-09

### 1. The failure, captured before editing

Gate 5, the agentic quality review (model `claude-fable-5-1`), failed the blocking `difficult`
criterion. Every other criterion passed, including `agentic`, `anti cheat robustness`,
`binary reward`, `category and tags`, `ctrf reporting`, `deterministic reproducible` and
`difficulty explanation quality`; so did the AI check, the similarity screen and reference
verification, which means the platform built both images and confirmed oracle 1 and nop 0 on its
own infrastructure. The verdict, verbatim:

> Every semantic rule is spelled out in the instruction, the editable code is roughly 100 lines
> of Python across five files, and each fix is a few lines. The two "inventions" the author
> highlights (a per-instance mark to defeat record reuse, and a per-name list kept in publication
> order) are standard techniques (ABA/generation tagging, a dict of lists). It is easy to misread
> a rule, and the randomized hidden programs punish any misreading, but a careful undergraduate
> with the spec in hand could complete this in a day or two; it does not require years of domain
> expertise.

No trajectory exists: this is a rubric verdict rather than the eight-attempt probe, so there is
no winning agent plan to read. The reviewer's own account of the winning route stands in its
place, and it is specific enough to act on. Estimated solves before the change: 3 of 8, which
was too generous - the honest reading of the verdict is 6 to 8.

### 2. Classification of the winning route

Two rows of the table in `RAISE-DIFFICULTY.md` apply, and the third does not.

- **The default plan was correct.** Named directly: generation tagging and a dict of lists. Both
  of my load-bearing "inventions" are retrieved, not derived. Required direction: add a specified
  interaction that makes that coherent prior wrong.
- **The graded work is too small.** A hundred lines across five files, each fix a few lines. This
  is not a row in the table but it is half the verdict, and it is measurable: the reference is
  179 lines including docstrings against 87 to 412 across the retained set, and no single
  decision needs more than a handful of lines.
- **Not "the instruction delivered the plan" in the sense the table means.** Every rule is stated
  because the doctrine forbids secrecy, and `docs/DIFFICULTY.md` is explicit that nothing is
  hidden in a passing task. The repair is therefore not to hide a rule. It is to make stating the
  rules insufficient: the correct implementation has to rest on a consequence of the rules that
  no rule states, and that consequence has to be worth deriving.

### 3. The semantic replan - candidates, attacked

**Candidate A: private activation scopes.** `open` brings a unit up visible only to the units
that same activation brought up. Resolution stops being a property of the order alone and becomes
a property of the order and the caller. Attacked: a scope tag plus a set-membership test is
another standard technique, and on its own it would earn the same verdict. It survives only
because of what it does to the fast path - see the selection below.

**Candidate B: hot replacement in place.** `swap` puts a fresh publication at the retiring
unit's position rather than at the back. Attacked: it breaks the append-only invariant I
advertised, which is the point, but a dict of lists with an in-place write is if anything easier
than an append. Rejected as the main change.

**Candidate C: an order-preserving cascade over live-dependent counts.** The retention rule is
unchanged - a unit stays while it holds a hold or a live unit needs it as a dependency - but the
teardown becomes the expensive operation, and the specified event order forbids the obvious
worklist. Attacked: this is the strongest of the three, because the fast path is not a technique
but a theorem about which candidates a retirement can expose, and the theorem is false in exactly
the case the task already generates (a dependency that retired and came back sits *after* its
dependent in the order, so a cascade can expose a candidate later in the order than the unit that
exposed it). An agent that derives the natural monotone version passes every small case and dies
on the retire-and-return family.

**Selected: A and C together, with the wide family exercising both.** They interact rather than
stack: the resolution structure and the retention counts are maintained by the same publication
and retirement events, and both need a stable ordering key that survives splicing, which is the
same key the identity rule needs. The per-name list the reviewer called a dict of lists is no
longer sufficient, because the answer for a caller is the earlier of two heads - the public list
and the caller's own scope - and that follows from a subsequence property of the order that has
to be noticed rather than looked up.

Tactics: A1 (the prior - a global resolution table, and a worklist teardown - is coherent and
specifically wrong), A3 (visibility-filtered resolution and an order-preserving cascade have no
single technique that gives both), B2 (six modules whose structures are updated by the same
events), C1 (both fences on scope and on cascade order), C2 (four of six shipped modules wrong,
no oracle), C3 (two measured boundaries, both with derivable fast paths), C4 (all-or-nothing over
enumerated and nonce programs).

### 4. What was rebuilt

Stage 2 first: the contract gained scopes and kept every existing rule unchanged in meaning, so
the thirty-six enumerated answers frozen before the change had to come out byte-identical
afterwards. They did - that regression is the evidence that the addition is additive rather than
a redefinition, and it is checked every time `build_gt.py` runs.

- `environment/app_src`: `open` added to the op set, `reg/order.py` gained the position accessor
  the shipped sweep uses, and `link/view.py` joined the editable set. Six editable modules now,
  all shipping wrong.
- `solution/`: rewritten around the two structures - buckets per scope and name, and a retention
  ledger feeding a serial-ordered candidate queue. 312 lines against 179.
- `tests/seal/model.py`: rewritten independently on the same contract, addressing everything by
  publication id, with the candidate list kept by bisect rather than by heap.
- `tests/gen.py`: two new small families (`scope`, `deep`), a second scale family (`tear`), and
  private publishers threaded through `wide` so a visibility filter over one global list is the
  wrong shape at scale as well as the wrong shape in principle.
- `tests/cases.py`: nine new enumerated programs, one per new decision plus both fences on
  visibility and the cascade-exposes-a-later-unit case.
- `cheat/`: thirty-two readings, ten probes and the forgery, regenerated from the reference.

### 5. The old winning implementation, kept as a cheat

The rubric named the implementation it expected: generation tagging and a dict of lists. Both
are now cheats. `cheat-global-list-filtered` is exactly that dict of lists, one entry per name in
publication order, filtered by visibility at lookup - semantically perfect, and 47 seconds on a
single wide program against a 60 second limit for the whole set. `cheat-scan-the-order` is the
same answer without the dict, at 126 seconds. Generation tagging survives as part of the
reference, because the contract requires it; what it no longer buys is the resolution, which now
needs the two-subsequence argument and buckets per scope and name.

### 6. Measurement of the repair

`tools/onelinecheck.py` is the sharpest single number: before the change one of the three graded
quantities (`run_target`) had the exact rule `= first_publisher_pos`, which is the reviewer's
"dict of lists" written as a one-liner. After it, none of the three has an exact rule at depth
two over the fields the environment exposes.

## Easiness recovery - 2026-09-09 (probe 2 of 3)

### 1. The failure, captured before editing

The easiness probe ran three trials against the bundle at commit `654a50c` and two of them
solved it. The trajectories are `probes/publish-settle-order/2026-09-09-easiness-1.txt`,
`-2.txt` and `-3.txt`, each with the brief removed from the top so `tools/leakcheck.py` is not
circular; commentary is in `probes/publish-settle-order/notes.md`. The files carry no
verdicts, so which trial failed, and on what, cannot be read from them and is not claimed.

Each agent's route, in its own words condensed:

- **Trial 1.** First plan: read the six editable files and the frozen tree, run `tiny.txt`,
  list every shipped defect against the sentence of the brief it breaks (fallback ranking,
  `view.can` returning true, startup calls after the closure, `uses` surviving a retirement,
  `pre` and dead units counted for retention, the sweep taking the first unwanted unit).
  Decisive discovery: none needed - one profile of `wide.txt` ("that scan was why wide.txt
  took 58 seconds") and the index by name and scope was its first idea. Final method: six
  files in one pass, publication generations on settled uses, buckets per name and scope, a
  heap for the sweep. Judgement call flagged: a self-dependency does not keep a unit up.
- **Trial 2.** First plan: the same list, from reading the code ("fallback demoted in pick,
  missing scopes in view, delayed boots and unreset uses in walk, dead units and pre-links
  counted in want, drop selecting the wrong item while being quadratic"), then all six files
  rewritten before any experiment. Decisive discovery: none - it wrote a brute-force model of
  the brief and fuzzed 1,900 programs against it, so every rule was confirmed against its own
  reading of the rules. Final method: per-symbol-per-scope index, publication generation, live
  hard-dependent count, max-heap on publication position. Judgement call flagged: a unit made
  public by `act` keeps reading its own scope.
- **Trial 3.** The same plan again, an explicit stack for the walk, a live dependent count and
  a heap ordered from the back. Judgement call flagged: two units that name each other as
  dependencies stay up after every hold is gone.

Earliest point at which each had enough to commit to the winning plan: the end of the first
read of the tree, before any program was run. The plan came from the instruction's rule list
and the shape of the tree - six modules, one per paragraph - not from an example, a helper, a
public source or a verifier loophole; `leakcheck` finds one shared rule sentence in trial 1 and
nothing in trials 2 and 3.

Tactics on record before this probe: A1, A2, A3, B2, C1, C2, C3, C4. The ones that failed in
practice: B2, because every rule was implementable on its own and the structures each rule
wants are the standard ones, so the conjunction was a checklist; C2, because a brief that
states every rule is a complete specification of a brute-force oracle, and trial 2 wrote one;
and C3, because the fast structures the boundaries demanded were each agent's first idea.

Estimated solves out of 8 before this repair: 6 (honest range 5 to 7), from 2 of 3 measured.

### 2. Classification of the winning route

Three rows of the table in `RAISE-DIFFICULTY.md` apply.

- **The default plan was correct.** All three named the state model on sight: an integer
  serial as both identity and order key (`solution/walk.py`, the `h.tick` line), per-name
  buckets per scope ordered by that serial (`solution/pick.py`), a heap keyed by it
  (`solution/drop.py`), one scope attribute per unit (`solution/view.py`), a ledger fed by
  publication and retirement only (`solution/want.py`), and an in-progress set local to one
  activation (`solution/walk.py`, the `busy` argument). Required direction: a specified
  interaction that makes that coherent prior wrong.
- **The instruction delivered the decomposition.** The brief's paragraphs map one to one onto
  the six modules, and each shipped module is wrong in exactly the way its paragraph
  describes, so reading the two side by side is the plan. The doctrine forbids hiding a rule,
  so the direction is not to withhold one: it is to add behaviour whose stated rules are
  simple and whose consequences break the structures above.
- **The agent confirmed each step independently.** Trial 2's brute-force model, written from
  the brief, is an oracle for the brief. That cannot be denied, and should not be; what can
  be denied is that the brute-force structure transfers to the fast one. A rule that a list
  with `insert` gets right for free and that no integer-keyed structure survives is the shape
  that does it.

Not applicable: no route-around was found (the traces were produced by satisfying the
invariants), the naive method was not fast enough (both scale boundaries were real and both
agents rebuilt around them), and the verifier accepted no false solution.

### 3. The semantic replan - candidates, attacked

**Candidate A: lazy binding with a dependency's place in the order.** A unit marked `auto`
may be brought up by a call that finds nothing it can see. It is brought up exactly as an
activation would bring it up, into the caller's own scope, with three differences that all
follow from one sentence - it is treated as if the caller had named it as a dependency: it is
published directly ahead of the caller in the publication order rather than at the back, it
takes no hold, and the caller keeps it up as a dependency would, until the caller goes down.
The call is then answered by the ordinary rule, which may name a dependency of the unit that
was brought up rather than the unit itself. Attacked: the brute-force model gets every part
of this for free (`list.insert` before the caller, one more dependent in a count), which is
the point - nothing in a spec-derived oracle warns that the fast structures are dead. The
integer serial can no longer order anything: a bucket sorted by it answers the wrong head, a
heap keyed by it retires the wrong unit first, and promotion inserts at the wrong place. A
float midpoint key is right until roughly fifty insertions land in front of one caller and
then silently wrong. The single scope attribute cannot express a unit that is public and still
reads its scope, which the binding rule needs because the load goes into the caller's *read*
scope. The ledger has to be fed by a resolution event and emptied by a retirement, not by the
two events it was built on. The in-progress set has to be shared across activations that nest
through startup calls. Expert path: an order key that admits insertion (labels with a suffix,
or exact fractions), two attributes per unit, bindings stored on the publication and released
when it retires, one in-progress set on the host, and resolution run again after the load.
**Selected.**

**Candidate B: teardown calls.** A unit declares calls to make as it goes down, run during a
cascade before its publication goes, able to bring a unit up in the middle of a sweep.
Attacked: nested operations inside deferred effects is the right kind of boundary, but a
heap-based sweep absorbs a push during its pop loop without noticing, and every consequence is
one more local rule. Rejected as the main change; it adds rules without invalidating a
structure.

**Candidate C: retention by settled use.** Every settled use keeps its publication up.
Attacked: it changes the answer of `stick-dead`, `dead-stays` and eleven other frozen
programs, so it redefines correct rather than extending it, and it collapses identity into
retention - a use could never go dead. Rejected.

**Candidate D: replacement in place.** Rejected on the previous recovery for the same reason
it fails here: an in-place write into a list is easier than an append.

Why A is enough on its own: it is one rule with a one-line justification that a real host has
(a dependency bound late is still a dependency, and resolution should not depend on whether it
was bound early or late), and it invalidates six structures at once while leaving the naive
model trivially right. Tactics: A1 (the prior for a lazy load - append it, hold it - is
coherent and wrong twice), A2 (the brief never says binding, generation, label or order
maintenance), A3 (insertion in front of a live unit, first-in-order resolution and last-first
retirement at scale have no single structure that gives all three), B2 (one event - the load -
is an order event, a scope event, a retention event and a resolution event, and the four
modules that own those have to agree on it), C1 (`auto-bound` against `auto-plain`,
`auto-scope` against `auto-scope-mates`, `auto-dead` against `auto-late-mark`), C2 (the shipped
load is wrong in four ways, and a brute-force model confirms nothing about the fast path), C3
(positions against keys at the wide scale, measured below; float keys fail only in the fan
family), C4 (two new nonce families and `auto` threaded through two existing ones).

Three readings the trials flagged are stated outright now rather than left to a judgement
call: a unit made public by `act` keeps reading the scope it came up in; two units that name
each other as dependencies keep each other up whatever holds are given back; no unit names
itself. The second and third were already what the sealed model did. The first was not - the
model read a promoted unit as reading public publications only - and the corner was exercised
by no hand case and no generated program, which is how it survived. It is changed to the
reading trial 2 took, because a scope is where a unit was brought up and `act` acts on its
publication, and that change is recorded as a contract change on a corner that had no answer
frozen anywhere.

### 4. What was rebuilt

Stage 2 first: the contract gained the load (decisions 14 to 16), the read-scope clause, the
mutual-dependency clause and the no-self-naming guarantee, and kept every existing rule
unchanged in meaning, so the thirty-six enumerated answers frozen before the change had to come
out byte-identical afterwards. They did; `build_gt.py` now reads the old file before it writes
the new one and refuses a change that is not additive.

- `environment/app_src`: `auto` added to the op set and the declaration store (`Rec.auto`,
  `Host.autos`); `reg/order.py` rewritten as a linked list with `put(h, r, before)`; the shipped
  `walk.py` and `site.py` given a coherent wrong load. `progs/lazy.txt` added; `wide.txt` and
  `tear.txt` regenerated at the scaled sizes (52 thousand units, 26 thousand calls, 5 thousand
  loads; 24 thousand units). 314 lines of Python.
- `solution/`: rewritten around tuple order keys that admit insertion, two scope attributes,
  one in-progress set on the host, bindings kept on the caller's record and given back in
  `want.parted`, and a second resolution after the load.
- `tests/seal/model.py`: rewritten on the same contract with exact fractions for keys, a sorted
  list of live keys for the predecessor lookup, sorted bucket lists, an explicit stack, and a
  bisect-kept candidate queue.
- `tests/gen.py`: two new small families (`lazy`, `fan`), `auto` threaded through `again` and
  `scope`, late declaration blocks in `lazy`, and `wide` reshaped so that every caller brings a
  unit up ahead of itself and gives its hold back, with the public providers coming up a quarter
  of the way through the callers so that every call compares two heads.
- `tests/cases.py`: twenty new enumerated programs, one per new decision plus both fences on
  each new axis, and `fan-deep`.
- `cheat/`: fifty-four readings, ten probes and the forgery, regenerated from the reference.
- `authoring/`: three correct variants rewritten (fractions and sorted lists in one module; an
  explicit stack with fraction keys and dictionary buckets; tuple keys with a set ledger and a
  bisect queue), `decisions.py` taught the linked order and the read scope, `readings.py` given
  an alarm guard so a reading that corrupts the order is reported rather than waited on.

### 5. The old winning implementation, kept as a cheat

Every structure the three trials chose is now a named cheat, each caught by the enumerated case
named for it: `int-keys` (a serial as the order key; `auto-order`), `float-keys` (midpoints;
`fan-deep`), `bucket-append` (append-only buckets; `auto-promote-order`), `auto-holds` and
`auto-at-back` (the ordinary activation used for the load; `auto-plain`, `auto-order`),
`promote-drops-home` (one scope attribute; `promote-reads-home`), `no-tie` and
`ties-outlive-caller` (a ledger with two writers; `auto-bound`, `auto-next-life`),
`busy-per-load` (an in-progress set per activation; `auto-busy`), `auto-answer-self`
(`auto-first-in-order`), `pos-compare` and `rebuild-on-load` (correct and cut off by the
limit). The three judgement calls the trials flagged are stated in the brief, and `cycle-gc` and
`promote-drops-home` are the readings that take them the other way.

### 6. Measurement of the repair

- Reference 1, nop 0, all 65 cheats 0, three correct variants 1, in the emulated two-stage
  trial with the real `tests/test.sh`.
- The probe-winning structures fail a specific hand case each (section 5) and, for the ones the
  population is shaped for, the sealed suite as well: `int-keys` and `auto-at-back` move 9.7% of
  600 generated small programs, `float-keys` 10%, `bucket-append` 2.8%, `busy-per-load` 0.5%.
- `tools/onelinecheck.py`: no exact rule at depth two for any of the three graded quantities.
- Timings on a quiet machine, one program each against a 60 s limit for all 456: positions
  43 s, filtered list 46 s, rebuild per load 202 s, scan 281 s; retention scan 132 s,
  rescanning sweep 77 s; reference 5.2 s for the set. Under three parallel jobs the same
  readings had measured 63, 76, 149, over 200, 125 and 79 seconds, and the position boundary
  had not bitten in one `cheat_report.py` run at the previous scale; both large families were
  scaled up before the numbers were written.
- Cold self-attack, honestly: I can see where to start - the walk, the key, the two scope
  attributes - and I cannot commit to the full plan without working the `auto-order`,
  `auto-busy` and `fan-deep` shapes by hand, and my first plan would have been wrong at the key.
- Estimated solves out of 8 after this repair: 2 (honest range 1 to 4).

The external easiness probe has not been run against this build. The recovery is pending at
the exit gate.

## Rejections and what fixed them

| Date | Gate | Verdict | Fix |
|---|---|---|---|
| 2026-09-09 | Easiness probe | 2 of 3 trials solved on commit `654a50c` | Trajectory analysis and the load rule (this file, "Easiness recovery - 2026-09-09 (probe 2 of 3)"); the old winning structures are cheats; recovery pending the next probe. |
| 2026-09-09 | Bundle structure | `ARTIFACT-PARENT-NOT-CREATED - TESTS/DOCKERFILE`: "tests/Dockerfile never creates /app/link" | The directory was created, by `RUN useradd ... && mkdir -p /app/link /work /logs/verifier`. The platform reads whole instructions and wants the mkdir to be the instruction, so each parent now has its own `RUN mkdir -p` line, as the retained bundles have. `scripts/preflight.py` was matching `mkdir` anywhere in the file and passed the rejected shape; it now requires the instruction to begin with `RUN mkdir` or `WORKDIR`, was confirmed to fire on the exact Dockerfile that was rejected, and is clean on all ten bundles. The `CHEAT-DIR-PRESENT` warning in the same report is informational and expected. |

## Open questions and next steps

The platform's easiness probe against this build is the exit gate, and it is the one thing this
session cannot run. Two-container gates on a machine with a reachable registry are the other.
The residual risk to flag to a reviewer is the one the host emulation cannot close: it runs the
real `tests/test.sh`, including the privilege drop and the locked reward channel, but it does
not build either image, so a packaging fault of the class `imagecheck.py` models would show up
only there. `imagecheck.py` is clean, which is the closest local substitute. The timing margins
were measured on this machine; a platform machine half as fast still cuts every timed reading
off (the smallest single-program number is 43 s against a limit for the whole set) and still
runs the reference in a fraction of the limit.

