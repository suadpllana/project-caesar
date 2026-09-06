# Task state

Working memory for `pack-bind-retire`. Assume the next session starts with no memory of this
one - anything not written here is lost.

## Current stage

`Stage 7 - Pre-flight and packaging` - 2026-09-06. Contract frozen, environment, verifier,
reference, cheats and brief built and gated.

## Assistant's assigned role

Engineer who owns the extension loader in a long-running host - an editor, a DAW, or a
database with loadable extensions. Contributor confirmed the seed and the category on
2026-09-06 and directed that the remaining metadata follow the retained tasks.

## Source repository

- Repo URL: none - idea-based task.
- Task shape: authored from scratch.

## Task summary

The tree under `/app` is the loader of an extension host. Packs declare what they provide,
what they require, which other packs they need and which names they use as they load. A
script loads, uses and drops them. Every resident keeps its own view of what a name means,
a name a resident has used is recorded against that resident for good, and a dropped pack
stays resident while anything can still use it.

The graded artifact is the residency ledger: for every event, what each use resolved to and
which residents the host released.

## Why it is hard

- Why a frontier agent cannot one-shot the plan: the host has no name-to-provider map to
  repair. A name means different residents for different askers and for the same asker at
  different moments, so the shipped central structure has to be inverted rather than fixed;
  and the view that replaces it is half frozen and half live, so both natural
  implementations - snapshot the view at load, or rebuild it at every lookup - are wrong on
  opposite cases.
- Tactics making that true: A1, A2, B2, C1, C2, C4. A1 - the memorised loader keeps one
  global symbol table and a refcount, and both are specifically wrong here. A2 - scope
  chains, tracing reclamation and interposition are described operationally and never named.
  B2 - eleven stated rules whose interactions are the work, with no per-rule feedback
  anywhere in the tree. C1 - the fence runs both ways: releasing a resident early and
  keeping one that nothing can use both fail. C2 - no oracle, the host runs whatever rules
  it is given and every wrong reading prints a plausible ledger. C4 - all-or-nothing over
  enumerated cases plus scripts generated inside the verifier from a nonce made after the
  agent finished.
- Your own attack on the plan: my first plan is one global name-to-resident map updated on
  load and drop, a per-asker cache of what it resolved, and a refcount so a drop defers the
  release. It is coherent and it is wrong in three places - the map cannot be global, the
  needs half of a view is fixed to residents at load time while the open half is live, and
  retention is a closure from the standing residents over requires that have not been used
  yet rather than a count of records already made. I would not find the third until a script
  dropped a pack, loaded it again, and then reached the old resident through a record.
- Estimated solves out of 8: 2, designed at the hard edge of the band

## The frozen contract

### The machine

A pack file declares one pack: `pv <name>` a name it provides, `rq <name>` a name it
requires, `wk <name>` a name it requires weakly, `nd <pack>` a pack it needs, `st <name>` a
name it uses as it loads. A script file is a list of events: `ld <pack> open`,
`ld <pack> own`, `us <pack> <name> [<name> ...]`, `dp <pack>`.

A resident is one loading of a pack. Residents are numbered from 1 in creation order. The
standing resident of a pack is the one its most recent load created and no drop has ended.
The open list is an ordered list of residents; a resident joins it when it is loaded `open`
or promoted, and leaves it when it is dropped.

A resident's view is: itself, then the residents its needs stood at when it was created,
walked breadth-first from its declared needs in declaration order, then the open list as it
stands at the moment of the lookup, skipping residents already in the view. Resolving a name
takes the first resident in the view whose pack provides it.

A use by resident R of name N: `bad` if R's pack declares N neither `rq` nor `wk`; the
recorded answer if R already has one; otherwise resolve N in R's view and record the answer,
a resident or nothing, against R for good.

Loading a pack that already stands creates nothing; in `open` mode it appends the standing
resident to the open list if it is not already there. Otherwise the pack's needs are loaded
first, in declaration order, each need's own needs before it, then the resident is created
and appended to the open list if the mode is `open`, then its `st` names are used in
declaration order.

Dropping ends the standing resident and takes it out of the open list. After every event the
kept set is the least set containing every standing resident and closed under: if X is kept
and X requires N with `rq` and has no record for N and N resolves in X's view to r, then r is
kept. Everything else is released and is gone from every view.

### The ledger, one row a line

    <step> ld <pack> <n>...     residents created, in creation order, or `-`
    <step> us <pack> <name> <r> a resident number, or `none`, `bad`, `off`
    <step> dp <pack> <n>        the resident that stopped standing, or `bad`
    <step> rl <n>...            residents released, newest first, or `-`

Every event emits its own row, a `us` row per hop of a chained use, and exactly one `rl` row
last.

### Real work - two correct implementations agree by construction

- every resident number, and therefore the creation order of needs
- what every use resolves to, including repeats of a recorded name
- the released set after every event, and its order
- the tokens `none`, `bad`, `off` and `-`

### Implementation choice - never graded

- how a view is stored or cached, how records are indexed, module-private names, whether the
  frozen helpers are called at all, how the kept set is computed

### Grading

Ledger only. Enumerated cases checked against a sealed ground truth and against an
independent model; 300 scripts generated inside the verifier from a nonce made after the
agent finished, checked against the model. No process checks: no journal, no call tally, no
fingerprints of editable code. Mechanistic isolation only - the executed tree outside the
declared artifacts must be byte-identical to the pristine copy, the reward is root-owned and
defaults to 0 before submitted code loads, the run drops privileges in its own session, and
its survivors are reaped.

### Declared artifacts

`/app/hst/vw.py`, `/app/hst/bd.py`, `/app/hst/rt.py`, `/app/hst/ld.py`, `/app/hst/od.py`.
Four ship wrong; `od.py` ships correct.

## Measured

- Reference against the sealed model: 818 scripts, 0 disagreements (`fuzz.py 800`).
- Ground truth: 18 scripts, 160 rows, written only because both implementations agreed.
- Determinism: 120 scripts and their ledgers byte-identical across 5 PYTHONHASHSEED values.
- Readings, share of 60 generated scripts each moves (`readings.py`): kept-by-count 92%,
  needs-made-wide 90%, self-not-in-view 92%, one-table-for-everyone 57%, record-is-a-cache
  52%, no-promotion 50%, weak-keeps-too 32%, needs-followed-live 27%, needs-walked-deep 27%,
  open-before-needs 25%, kept-among-kept 15%, kept-by-record 15%, oldest-released-first 38%,
  start-names-last 13%, dropped-stays-open 12%. Every reading is above the one-tenth floor.
- `readingcheck` 150 rounds: all 15 readings separated by a named enumerated script.
- `onelinecheck`: no exact rule at depth <= 2 for any of the three graded decisions
  (4306 use samples, 6123 release samples, 964 load samples).
- `tiecheck` 168 scripts: 0 mirror disagreements, 0 ledger tokens from anywhere but the
  script or the host's own counting.
- Real two-image trial: oracle 1, nop 0, 21 cheats 0, 4 correct variants 1.
- `cheat_report`: every probe caught by the layer it is aimed at, with the trace that proves
  it got there (`blocked /tests/gt.json`, `report path taken`, `reward refused`, the reap
  signalling a survivor).
- Runtime: the whole graded set, 318 scripts, runs in well under a second. The verifier's
  600 s wall clock is a hang guard, not a gate, and there is no resource axis in this task.

## The self-probe, and what it could and could not measure

I built this task, so I cannot play the solving agent cold and any claim that I did would be
worthless. What the probe can still answer is the fairness question the review raised, and
that was run mechanically instead:

- For each of the 15 wrong readings, the sentence of the brief that decides it was named.
  All 15 have one. The walk runs the other way too: every rule sentence has an enumerated
  script asserting it, named by `readingcheck`.
- Mode A: `hintcheck` clean - the brief refutes no candidate rule and says nowhere which part
  carries the difficulty.
- Mode B: `onelinecheck` clean - no graded decision is a short rule over exposed state.
- Mode C: there is no oracle to build. The agent tree ships 198 lines of Python, no comments,
  no docstrings, no `.md`, and no expected output anywhere; the only ledger it can produce is
  the one its own rules produce, and the three shipped scripts print the wrong tree's answer,
  which the brief says is wrong.
- Mode D: no counts, no round numbers, no existence claims and no end-to-end reproduction
  step anywhere in the brief.

## Residual risk, stated plainly

The agent tree is 198 lines across 10 files, the smallest of the seven retained tasks
(alias-settle-report 229, token-seam-emit 250, note-carry-forward 300, focus-return-point
418, delta-view-retraction 408, guard-mark-unwind 544). Prong B1 is therefore not operating:
a frontier agent holds this whole tree at once. That is deliberate here, because every fact
is stated in the brief by design after the review, so the tree is not where anything hides -
but it does mean the difficulty rests entirely on B2 and C1, on thirteen interacting
decisions with no per-rule feedback and a fence graded from both sides. Padding the tree with
scenery would have been worse than being small; if this comes back solved too often, the
repair is a semantic addition that multiplies interactions - a resident able to open a pack
into a list only it can see - and not more files.

## Remaining

Package, zipcheck, deliver.
