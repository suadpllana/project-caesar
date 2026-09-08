# Task state

Working memory for this task. Updated after every stage; assume the next session starts with no
memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging`. The two-container gates cannot be run in this session:
Docker's daemon starts, but the egress policy denies Docker Hub's blob CDN
(`production.cloudfront.docker.com`, 403 on CONNECT), so no base image can be pulled and no
image can be built. Everything else has been run - see the validation table, and read the
`host trial` rows as host emulation rather than container evidence.

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
they publish (some as fallbacks) and the startup calls they make; then the program brings units
up, calls names and releases holds. `/app/run_host.py` prints one event per line: `up`, `down`,
`run`, `miss`, `dead`. The frozen half of the tree is the record table, the declaration store,
the publication order, the hold ledger and the event writer; the five files under `/app/link`
decide the activation walk, which publisher answers a name, what a call does, whether a live
unit has to stay, and what a released hold takes down. All five ship wrong. The graded artifact
is those five files; the verifier overlays them onto its own copy of the tree and compares the
trace of every program, line for line.

## Why it is hard

- Expert time estimate: 8 hours.
- Why a frontier agent cannot one-shot the plan (the strategic answer): the rules are all
  stated, but two of them cannot be implemented from the brief alone. Instance identity has no
  representation in the shipped tree - `reg/tab.py` keeps one record per name for the whole run
  and hands the same object back after a retirement, so the natural store (the record, or the
  record plus its `live` flag) silently revives a use that must stay dead, and the repair is a
  data-model change the agent has to invent. And the resolution rule, implemented literally as
  the sentence reads, is a scan of the publication order per call, which is exactly correct and
  measured at 220 s against a stated 60 s limit. Neither failure is visible until late: the
  first needs a retire-and-return ordering, the second needs the wide family.
- Tactics making that true: A1, A2, A3, B2, C1, C2, C3, C4.
  A1 - the priors are coherent and specifically wrong: a fallback publication is what a
  registry usually consults last, a re-registration is usually what wins, and initialisation
  usually runs after the whole closure is in place. All three are inverted here and stated.
  A2 - nothing is named: no interposition, no lazy binding, no scope, no generation counter.
  A3 - sticky settlement and instance identity have no single known technique that gives both;
  the record is the wrong key for one and the only key available for the other.
  B2 - thirteen decisions that consume each other: the walk decides the order, the order decides
  the answer, the answer decides what a retirement breaks, and the retention rule decides which
  retirement happens at all. There is no per-decision feedback, because all five shipped modules
  are wrong at once.
  C1 - both fences: `fall-first`, `casc-order`, `same-name`, `pre-no-keep` fail a conservative
  reading; `fall-late`, `miss-open`, `dep-holds`, `hold-two`, `not-live`, `rel-early` fail an
  eager one.
  C2 - the shipped host is wrong in four of five modules, so running it confirms nothing, and
  no standard library implements this contract.
  C3 - a measured boundary: the reference settles the whole graded set in 1.7 s, the same
  contract implemented by scanning the order per call takes 659 s, against a stated 60 s limit.
  The two are semantically identical - `readings.py` measures 0 differences over 360 programs -
  and so are the cached scan and the rebuild-on-every-change index, which are also cut off.
  C4 - all-or-nothing over 27 enumerated programs and 364 nonce programs generated inside the
  verifier from a seed drawn after the agent's container is gone.
- Assistant's attack on the plan: my first plan was to model units as records, recurse through
  declared dependencies, append each unit to a publication order, resolve a name by scanning
  that order and caching the answer on the unit, and retire on a hold that reaches zero. That
  plan is right in shape and wrong in three places that matter. It caches the record, so a name
  that comes back revives a settled use; it scans, so it dies on the execution limit; and it
  runs startup calls after the closure is published, which changes what a startup call inside a
  dependency cycle can see. I would have found the third by reading the brief again, the first
  only by building the retire-and-return case, and the second only by timing.
- Estimated solves out of 8: 3 (honest range 2 to 5).
- Difficulty score anchor: not yet submitted.
- Score history: none yet.
- Leak audit (docs/DIFFICULTY.md), run as a procedure:
  - Can a shipped file reproduce a graded answer by a join, a sort or a field comparison? No.
    The tree ships four programs and no expected trace for any of them. The answer is a
    sequence of events produced by running a program; nothing in the tree stores one.
  - Is there a stored derived quantity? No. `Rec` holds what the program declared - `needs`,
    `pubs`, `boots` - plus `live` and `uses`, which the editable code maintains itself, and the
    hold ledger is a count per name in `reg/hold.py`. There is no publication serial, no
    generation counter, no resolution cache and no dependent list in the shipped tree: the
    instance mark the contract needs does not exist until the agent invents it, which is the
    point.
  - Unused affordances? None. Every function in `reg/` and `ops.py` is called on the live path;
    `link/` exposes exactly the five entry points `ops.py` dispatches to.
  - Manifests? None. Units are declared by the program being run, not by a config file.
  - Self-labelling data? None. Programs are ops over `u0`-style names; nothing in them says
    which decision they exercise.
  - Any artifact that is a function of the correct trajectory? No. `gt.json` is sealed in the
    verifier image and never enters the agent's tree.
  - Free join keys or callable difficulty? The shipped host is callable and wrong, which is the
    opposite: running it produces a plausible trace that disagrees with the contract in four
    places.
  - Per-axis confirmation before commit? No. One trace per program, all-or-nothing.
- Expert path, described step by step: read `ops.py` to learn the op set and which of the five
  entry points each op reaches; read `reg/tab.py` and notice that records are keyed by name and
  never removed, so `uses` and any state on a record outlive a retirement; write the activation
  walk with publication and startup interleaved per unit and the in-progress set that makes a
  cycle terminate; give each publication a mark of its own and store it beside the target in a
  settled use, because that is the only thing that separates a unit from the unit of the same
  name that replaced it; implement resolution as first-in-order over live publishers with
  fallbacks counted the same, then replace the scan with per-name publisher lists kept in
  publication order, which is correct because the order only ever grows at the back; implement
  retention as a hold of its own or a live unit that needs it as a dependency, reading the second
  half of a `needs` entry to tell a dependency from an ordering edge, and the sweep as
  repeat-until-stable taking the last unwanted unit; time `progs/wide.txt`, multiply by four, and
  check it against the limit.
- Originality check: searched on 2026-09-08 for the composite (plugin/extension host,
  publication order, first publisher wins, fallback on equal footing, sticky settlement,
  retire-and-return identity, hold-based retirement). Nothing describes this rule set. What is
  retrievable is the neighbouring real machinery - dynamic-linker symbol interposition, .NET
  load contexts, plugin registries - and the closest public fact is that a first-in-search-order
  definition wins whether or not it is weak, which is one of the eleven decisions here. The
  others (startup against the partly built order, settlement that survives everything except
  the publication it named, retention by live declared dependent, reverse-order sweep applied
  one at a time) are not stated together anywhere found, and the graded object is this host's
  exact trace.

## Verifier contract - FROZEN

- Artifacts the agent produces: `/app/link/walk.py`, `/app/link/pick.py`, `/app/link/site.py`,
  `/app/link/want.py`, `/app/link/drop.py`. Nothing else is read from the agent.
- What is checked: the verifier overlays those five files onto its own pristine copy of the
  tree, runs every graded program through `ops.ex`, and compares the printed event list line
  for line. 27 enumerated programs are checked against `tests/seal/gt.json`; 364 programs
  generated from a nonce drawn at verification time are checked against `tests/seal/model.py`.
  The model must reproduce `gt.json` exactly before anything else is graded. Every program must
  match.
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
- Prong C tactics used: C1 (both fences enumerated), C2 (no oracle - four of five shipped
  modules are wrong and no library implements the contract), C3 (measured execution limit),
  C4 (nonce-generated population plus enumerated corners, all-or-nothing).
- Route-around guard: only the five files are declared artifacts, so the rest of the runtime -
  the op dispatch, the record table, the program reader - cannot be reshaped by the agent.

## Stage 7 re-attack (D7)

Read cold, the brief hands over the rules and nothing else. The first plan it supports is:
records for units, a recursive dependency walk appending to `h.seq`, resolution by scanning
`h.seq` and caching the answer on the unit, hold counts, and a sweep on release. That plan is
right in shape. It is wrong in three places, and the brief cannot be blamed for any of them,
because each is a consequence the reader has to work out rather than a rule the reader has to
read:

- caching the record revives a settled use as soon as a name goes down and comes back, and the
  tree gives no other handle on the publication, so the fix is a mark the solver has to invent;
- the scan is 580 s against the stated 60 s, and so is rebuilding the index on every change;
- the sweep has to take the last unwanted unit and ask again after each retirement, which is
  visible only when two units become unwanted at once.

Are the load-bearing facts still distributed? The record-reuse fact is still readable only in
`reg/tab.py`, and `tools/onelinecheck.py` confirms mechanically that neither what a call does
nor what a release takes down has an exact rule of two terms over the fields the tree exposes.
Has the instruction come to telegraph the method? It states the limit and the input scale, as a
measured C3 must, and never the index; it states that a returning unit is not the one that
left, and never how to represent that.

The self-probe proper - a cold solve by an author who has not seen the model - was not run, and
is recorded as not run. The order here was brief, then reference, then environment, so by the
time an environment existed both discoveries were already in hand; a self-probe reported as
passed by a contaminated author is worse than none. The reading separations, the layer report
and the no-short-rule result stand in its place.

Estimated solves out of 8 after the re-attack: 3 (honest range 2 to 5), unchanged.

## Decisions and their reasons

- The instance mark is deliberately absent from the shipped tree. Shipping a generation counter
  that nothing reads would be a dead field, and `deadfieldcheck` exists because a dead field is
  read as a hint. The contract states that a name coming back is not the unit that left; how to
  represent that is the agent's to invent.
- All five modules ship wrong. `want.py` was going to ship correct, on the retained four-of-five
  shape, until the ordering edge went in: a correct `want.py` states the hard/soft distinction in
  one legible line, which is the whole of that decision handed over. It ships wrong in both
  directions instead - counting soft edges, and counting units that are no longer up.
- The environment was rebuilt once, on measurement rather than taste. At 162 lines of Python it
  sat below every retained bundle (229 to 544) and matched the shape the quality review has
  failed twice on. The repair was structure the rules actually use - a declaration store, a
  publication order, a hold ledger keyed by name and an event writer, all frozen - plus one more
  graded rule, the ordering edge, which is a real thing extension hosts have and which splits
  bringing a unit up from keeping it up. 234 lines now, and one more fence in both directions.
- `tests/pristine/` has to be re-synced whenever the shipped tree changes. It was not, once, and
  the oracle failed with an import error inside the worker rather than a wrong trace.
  `authoring/publish-settle-order/sync_pristine.py --check` is the guard.
- The wide example ships at the size of the graded ones, and the brief says how many there are,
  so timing it is a measurement rather than an extrapolation across a superlinear cost.
- Events are printed in occurrence order, not sorted, because the order is what several of the
  decisions are about.
- `tests/seal/` holds the model and the frozen answers and is `chmod 700` before the worker
  starts. Without that, code inside the verifier can `import model` and answer every program
  without implementing anything - the worker puts `/tests` on `sys.path` for `cases` and `gen`.
  `cheat-probe-answer-key` and `cheat-probe-hijack-driver` are the proof, and both report the
  denial rather than only a zero. `tools/forgecheck.py` and `tools/hintcheck.py` were taught to
  look in `tests/seal/` first so the kit and the bundle do not disagree about where truth lives.
- `environment/Dockerfile` still reads 0.88 similar to two retained bundles. It is seven lines of
  `FROM python:3.12-slim`, `WORKDIR /app`, `COPY app_src/`; there is no honest way to write it
  differently. `tests/test.sh` and `tests/Dockerfile` were rewritten after `simcheck` flagged
  them at 0.958 and 0.907, and now flag nothing.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Reference vs sealed model | pass | 24 hand cases, 304 nonce programs, 0 disagreements |
| Wrong readings separated | pass | 25 readings; 22 caught by a named hand case, 3 by the limit |
| `tools/readingcheck.py` | pass | no blind reading over 2400 generated programs |
| Execution boundary measured | pass | reference 1.7 s, scan-per-call 659 s, cached scan and rebuild-per-change also cut off, limit 60 s |
| `tools/onelinecheck.py` | pass | no short rule for `call_outcome` or `retire_now` |
| `tools/imagecheck.py` | pass | the image would hold 15 files; the reference runs all four shipped programs inside it |
| `tools/catcheck.py` | pass | Software vocabulary present in the environment, not only in the prose |
| `tools/deadfieldcheck.py` | pass | clean |
| `tools/extraneouscheck.py` | pass | clean |
| `tools/solvecheck.py` | pass | clean |
| `tools/hintcheck.py` | pass | no refutation, emphasis or stale figure |
| `tools/structcheck.py`, `tools/textcheck.py` | pass | no findings against `focus-return-point` |
| `tools/simcheck.py` | pass with note | only `environment/Dockerfile`, seven lines of boilerplate |
| `tools/forgecheck.py` | pass | `cheat-forge-from-truth` passes all 27 enumerated programs and is caught by the nonce population alone |
| `cheat_report.py` | pass | 36 of 36 cheats caught by the layer named for them |
| host trial oracle = 1 | pass | emulated two-stage run, real `tests/test.sh`, 30 tests passed |
| host trial nop = 0 | pass | the shipped host is both wrong and over the limit |
| host trial cheats = 0 | pass | 38/38 trials behaved as required |
| Isolation probes | pass | uid 1002, `PermissionError` on the seal, the reward channel and the grader's seed |
| `package.py` + `tools/zipcheck.py` | pass | 95 entries, no findings |
| Correct variants = 1 | pass | `ok-flat`, `ok-memo`, `ok-stack` |
| `preflight.py` | pass | no errors |
| Docker oracle/nop | BLOCKED | image pull denied by the egress policy in this session |
| `harbor check` rubric | not run | harbor is not installed in this environment |

## Open questions and next steps

Two-container gates on a machine with a reachable registry, and the platform's own probes. The
residual risk to flag to a reviewer is the one the host emulation cannot close: it runs the real
`tests/test.sh`, including the privilege drop and the locked reward channel, but it does not
build either image, so a packaging fault of the class `imagecheck.py` models would show up only
there. `imagecheck.py` is clean, which is the closest local substitute.
