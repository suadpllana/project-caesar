# span-claim-charge

## Current stage

`Easiness recovery` (RAISE-DIFFICULTY.md), re-entered at Stage 2. The bundle as it was probed
is the one the contributor uploaded on 2026-09-10; it shipped without a STATE.md, so this file
was written from the bundle, the three probe trajectories and the recovery work below.

## Assistant's assigned role

An engineer on the allocation and accounting half of a copy-on-write block store: the part that
hands out extents from a free map, lets several volumes and their snapshots stand on the same
extent, decides whether a write can be taken in place, and answers what a volume - or a volume
together with everything snapshotted from it - is using and would give back. Later sessions
resume in this persona.

## Task summary

`/app` is a small store: lines (volumes) hold items (files) whose coverage is a list of claims
on spans (extents) handed out by an allocator. Programs are command files; `run_store.py` prints
one line per command. The agent replaces the five modules under `/app/store/` so that every
graded program prints exactly the sealed model's trace inside the stated execution limit.

## Why it is hard

- Expert time estimate: 12 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the shipped store is a
  coherent design - one reference count per span, charges added up by walking claims, a family
  charge added up over the members of a stamp tree, allocate-then-splice - and every one of
  those structures is the natural first idea and is wrong. The rules ask two different
  questions of the same claims (may this block be rewritten where it stands; which lines stand
  on this span), so a count per span answers neither and the span record has to be redesigned
  rather than fixed; the family questions, asked thousands of times against thousands of spans
  under a tree that loses lines and hands their stamps up to the origin, cannot be answered by
  walking, so the standing set of a span has to be carried against the tree and kept current
  through every claim event and every drop - a second redesign of the same record.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C3, C4, and the guard.
  A1: the retrievable model of a copy-on-write store is a reference count per extent and
  per-volume totals added up from it; both are the shipped design and both are wrong. A2: the
  words snapshot tree, lowest common ancestor, hierarchy, subtree sum and reference count never
  appear; the family is described as a line together with everything stamped from it. A3:
  exact charges on every command, a family question answered in constant time, and a drop that
  moves spans between families have no single retrievable structure that gives all three. B2:
  twenty graded decisions in five modules that each change what another means (listed under
  Stage 2). C1: both sides of every fence are enumerated. C2: the shipped store is wrong in nine
  places at once, the eight shipped programs contain no drop of a stamped line, no share across
  families and no family question after a drop, and the graded programs are generated after
  the agent's container is gone. C3: four naive-but-correct families measured against the
  stated limit. C4: exact traces, all-or-nothing, enumerated corners plus nonce programs in
  eleven families. Guard: five editable files declared as the only artifacts; the driver, the
  op set and the trace writer are the verifier's pristine copy.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): my first plan
  is the shipped one. A count of claims per span decides the in-place test and exclusivity,
  claims per item spliced on a write, an allocation taken and then laid, charges walked when
  asked, and a family answered by walking the stamp records and adding its members up. It is
  wrong about the in-place test (a second claim of the same item is not a second line, and a
  count cannot tell them apart), wrong about the order of a write on a full device, wrong about
  the charges of a family (neither number is a sum over members), wrong about what a drop does
  to the stamps hanging off the dropped line, and it dies on all four measured families. I
  would not commit to the two-index span record, nor to carrying the tree against every span,
  before running the wide and tree programs and reading their timings.
- Estimated solves out of 8: 2 (range 1-4)
- Difficulty record score: see the table under "Difficulty record" below.
- Leak audit (docs/DIFFICULTY.md): the shipped Span carries a start, a length and one count -
  nothing per line and nothing per block, so the two-index record is designed, not fixed; the
  shipped stamp record is a name-keyed parent map, which is the primitive the family rule
  needs, wrong about drops and about a reused name, and it derives nothing; the shipped
  programs exercise the op language and contain none of the family corners; the example in the
  brief is one line and one write; no per-span standing set, no deepest common line, no
  per-family total and no answer key ships; the model, the frozen answers and the pristine tree
  exist only in the verifier image, in a directory locked to root before any agent code runs.
- Expert path, described step by step: (1) run the shipped store on `tiny.txt` and reproduce
  the wrong free total the brief names; (2) read the frozen driver and the five store modules
  and notice that one count per span cannot say who stands on it; (3) give the span record the
  claims on it and a count per line, and derive the in-place test and both charges from those
  as running totals; (4) reorder the write path so the replaced claims go first and the room is
  judged against the total that release produces, and spread one allocation over the fresh
  stretches in item order; (5) index the free runs by length beside the address order; (6)
  record the stamp tree on line records that survive a name being reused, and hand stamps up
  to the origin on a drop; (7) answer the family questions by walking, time the tree family,
  and replace the walk with per-span summaries kept against the tree - the deepest line every
  standing line descends from, and a count per ancestor; (8) re-time everything against the
  limit.
- Originality check: searched for the shape (copy-on-write extent accounting, snapshot
  exclusive/referenced space, qgroup-style hierarchical accounting). The public material
  defines referenced and exclusive space and describes settling them at commit by walking back
  references; nothing public specifies a per-block in-place test that counts claims of the
  same item, a release-before-take room check, a largest-run fallback laid across stretches, or
  a family charge kept current under drops that re-parent stamps. No retained task in this
  repository is about extents, sharing or hierarchical accounting.

## Easiness recovery - 2026-09-10

### 1. The failure, captured before editing

The easiness probe ran three trials against the uploaded bundle and two of them solved it. The
transcripts are `probes/span-claim-charge/2026-09-10-easiness-1.txt`, `-2.txt` and `-3.txt`,
each with the brief removed from the top so `tools/leakcheck.py` compares the solver's words
with the brief rather than the brief with itself; commentary is in
`probes/span-claim-charge/notes.md`. The files carry no verdicts. Which trial failed can still
be read from the traces they printed: trial 1 printed `g a,b rel=10` on `pair.txt` and
`g a,b rel=10` on `weave.txt`, where the reference prints 12 and 16, and trials 2 and 3 printed
the reference's numbers on every shipped program. Trial 1 read "the spans whose whole standing
set lies inside that set" as the spans every named line stands on - a reading slip on one
rule, not a planning failure.

Each agent's route, condensed from its own words:

- **Trial 1 (failed).** First plan: read the five store modules, the frozen driver and the
  shipped programs in two tool calls, list the defects against the brief (first-fit-only
  allocation, forward-only merge, span-level rather than block-level claim check, wrong
  take/release order, per-claim charging, drop reporting zero), rewrite all five files in one
  heredoc. Decisive discovery: none; one `sed` to fix a `spare` counter it had zeroed. Final
  method: the reference's shape, with `g` over a set computed as the spans all named lines
  stand on. Eight tool calls.
- **Trial 2 (solved).** First plan: the same list from the same read, in one thinking block:
  "take-before-release in writes, a whole-span bare test, right-only free-map coalescing, drop
  reporting 0, and charges recomputed via scanning". Rewrote the five files before running any
  program, timed `wide.txt` and `churn.txt` once, then wrote a brute-force recount of the
  charges and a live-plus-free-equals-device invariant and checked them after the big runs.
  Final method: two indexes per span (the shipped `on` and `by`), running totals, `g` summed
  from a table keyed by each span's standing set, best fit by bisection. Seven tool calls.
- **Trial 3 (solved).** The same list ("per-block sole-claim check, allocation policy,
  release-before-take ordering, charge semantics using span vs claim lengths, drop not
  releasing, quadratic charge cost"), all five files rewritten in two heredocs, the small
  programs checked by hand against the brief, the refusal paths exercised once. Nine tool
  calls.

Earliest point at which each had enough to commit to the winning plan: the end of the first
read of the tree, before any program ran. The plan came from two places. The tree: the shipped
`store/hold.py` already carried `Span.on` (the claims) and `Span.by` (a count per line),
`store/tally.py` already carried `own` (spans per line) and the `gain`/`lose` hooks, and
`store/item.py` already carried `_cut`, `_pull`, `_lay`, `_holes` and `_sole` - the reference's
own skeleton, with about a hundred lines of diff between the shipped store and the reference
(`hold.bare` stubbed to a span-level test, `_victims`/`doomed` absent, `take` first-fit, `give`
forward-only, `charge` recounting, `drop` returning 0). Every agent kept the structure and
repaired the functions. The brief: it narrates the write path in order ("the claims over those
fresh stretches are dropped before anything is taken ... So a write can land on the ground it
just freed. The room it needs is judged against the free total that release produces") and
refutes the count-per-span reading in as many words ("a span two lines reach is exclusive to
neither of them while a span one line reaches through four claims of its own is exclusive to
that one"). `tools/leakcheck.py` finds the solvers quoting exactly those sentences back: trial
1 reuses "so a write can land on the ground it just freed", "is judged against the free total"
and "whole standing set lies inside"; trial 2 reuses "is judged against the free total that
release produces" and "a free run on either side"; trial 3 nothing above the floor. Not from an
example, a public source, generated experiments or a verifier loophole.

Tactics on record before this probe, from the uploaded `task.toml`: A1 (the reference-count
prior), A3, B2, C1, C2, C3, C4. The ones that failed in practice: A1, because the shipped tree
did not embody the prior it claimed to poison - it embodied the correct two-index model, so
the prior never had to be fought; B2, because every rule was implementable on its own against
the shipped skeleton, and the eight shipped programs plus the brief gave per-rule feedback
(trial 3 checked each small program by hand; trial 2 built an oracle from the brief); C3,
because the fast structures the boundaries demanded - a `(length, start)` list for best fit,
running totals for the charges - were each agent's first idea, as they were on
`publish-settle-order`.

Estimated solves out of 8 before this repair: 6 (honest range 5-7), from 2 of 3 measured.

### 2. Classification of the winning route

Four rows of the table in `RAISE-DIFFICULTY.md` apply.

- **The environment delivered the plan.** `environment/app_src/store/hold.py` lines 5-30 of
  the uploaded bundle (`Span.on`, `Span.by`, `add` and `rip` maintaining both), `tally.py`
  (`own`, `gain`, `lose`), `item.py` (`_sole`, `_holes`, `_lay` handling straddles the shipped
  allocator can never produce). The data model the task exists to make the agent design was
  shipped; only its functions were wrong. Required direction: remove the derived structure while
  keeping every necessary fact observable - ship a working store built on the coherent wrong
  model instead.
- **The instruction delivered the decomposition.** Paragraph four narrates the write path in
  the order the reference executes it; paragraph six refutes the count reading. Both were
  quoted back. Required direction: state behaviour without narrating the method or naming the
  wrong reading. The doctrine forbids hiding a rule, so the order of release and allocation
  stays stated - as an observable ("a write is refused only when the free total after its own
  release is short") rather than as a procedure - and the refutation goes.
- **The default plan was correct.** All three named the state model on sight, and the two
  solvers' final structures are the reference's. Required direction: a specified interaction
  that makes that coherent prior wrong - one that the two-index record and running totals do
  not survive.
- **The agent confirmed each step independently.** Eight shipped programs plus a
  fully-specified brief let each rule be checked alone; trial 2 wrote a brute-force model.
  The doctrine says the brute-force oracle cannot be denied; what can be denied is that its
  structure transfers to the fast one. Required direction: a rule the brute force gets for
  free that no per-line running total survives.

Not applicable: no route-around (the traces were produced by satisfying the invariants); the
naive method was not fast enough (both scale boundaries were real); the verifier accepted no
false solution (trial 1 failed on a genuine misreading).

### 3. The semantic replan - candidates, attacked

**Candidate A: the family charge.** A new question, `u <line>`, asks the two charge questions
of a line together with every line stamped from it, and from those in turn: referenced is the
spans any of them stands on, exclusive is the spans nothing outside that set stands on. One
tree rule goes with it: when a line is dropped, the lines stamped from it count as stamped
from the line it came from, and stand alone when it came from none. Attacked: the brute-force
model gets it for free (walk the stamp records, apply `g` to the set, union the members'
spans), which is the point. At scale - a `tree` family with thousands of items, forty lines in a
stamp tree and fifteen thousand family questions interleaved with writes and drops - the walk
is a hundred seconds per program, and a running total per line cannot answer a question about
a set, so the running-total design the solvers built is dead. The fast path is a derivation
about the tree, not a lookup: a span belongs to a family's exclusive exactly when the deepest
line all its standing lines descend from lies inside the family, and a span counts toward a
family's referenced space exactly when some standing line lies inside it, so each span carries
the deepest common line and a count per ancestor, and a drop hands the totals of the dropped
line up to its origin instead of recomputing anything. A `c` and a `u` move in opposite
directions on a stamp (the origin's exclusive collapses, its family's exclusive does not move),
which is the fence a conservative solution fails. Every one of the 48 frozen answers stays
byte-identical because none of them names `u` and no existing rule changes meaning.
**Selected.**

**Candidate B: a reserve honoured against exclusive space.** `r <line> <n>` promises a line n
blocks of exclusive space; the room any request has is the free total less every other line's
shortfall, and a stamp is refused when the collapse of the origin's exclusive would leave the
shortfalls over the free total. Real (it is how one production store treats a snapshot of a
reserved dataset) and unnamed, but attacked: the running totals answer it directly, the room
check gains one sum over at most eight lines, and the post-release exclusivity of other lines
is a fifteen-line extension of the doomed-span derivation the reference already makes. A
patch, not a replan. Rejected as the main change; recorded here so it is not proposed again
without this attack.

**Candidate C: freed spans pinned until a batch closes.** Inside `[` ... `]` a span emptied
by any command is held back from the free map until the batch closes, so a write on a full
device cannot land on what it freed. Real, and it inverts a stated rule. Attacked: one mode flag
and one list; every agent writes it in ten lines. Rejected.

**Candidate D: hundreds of stamps of a large line, so that copying claims per stamp is the
scale boundary and the item table itself has to be copy-on-write.** Attacked: the fast path
(shared item objects with owner sets, or layered tables) has no clean exact route to per-line
exclusive space that I can describe step by step; the risk is zero solves, not one. Rejected.

**Candidate E: a span gives back the head and tail no claim covers.** Attacked: it changes the
answer of `trim-part` and every frozen program that leaves a span partly uncovered, so it
redefines correct rather than extending it. Rejected.

Alongside A, two repairs the classification demands regardless of the twist:

- **The shipped engine is rebuilt on the coherent wrong model.** One reference count per span
  (`Span.refs`), no per-line and no per-block index; the in-place test asks whether the span
  carries one claim; charges are added up on demand by walking the line's claims, referenced
  as the sum of claim widths, exclusive as the spans with one claim; freed-by-dropping a set as
  the sum of members' exclusive; the family charge as the members' charges added up, over a
  name-keyed parent map that a drop leaves dangling so the dropped line's stamps fall out of
  the family; first-fit allocation from a single run with a forward-only merge; the allocation
  taken before the replaced claims go and the room judged on arrival; a drop that gives nothing
  back; one piece laid per stretch. It runs every shipped program and prints wrong numbers on
  most of them. The agent designs the two-index record, the hooks from the span table into the
  charges, the length index over the free runs, the release-first write path and the tree
  summaries; none of them is present to be repaired.
- **The brief states behaviour, not procedure.** The narrated write path becomes the observable
  it produces; the refutation of the count reading goes; the `g` sentence stays because it is
  the rule (trial 1 misread it and lost, which is the rule working). Every count in the prose is
  re-derived from `gen.py` after the generator changes.

Tactics: A1 (the shipped reference-count store is the memorised design of a copy-on-write
allocator, and it is wrong four ways), A2 (family, stamp tree, common ancestor, subtree sum,
back reference: none named), A3 (exact charges on every command, a family answered without a
walk, and drops that move spans between families have no single structure), B2 (twenty graded
decisions across the five modules; the pairs are listed under Stage 2), C1 (`fam-leaf` and
`fam-stamp` against `fam-sum` and `fam-orphan`; `keep-sole` against `keep-shared`; `room-after`
against `room-short`), C2 (nine shipped defects, no shipped family corner, nonce programs), C3
(the walk over a family's spans, the charge recounted per query, the best fit by scan and the
in-place test from every item's claims, each measured), C4 (all-or-nothing exact traces).

Why A is enough on its own: it is one question with one tree rule, both with a one-line
justification any store with snapshots has (what does this volume and everything snapshotted
from it cost, and what would deleting the lot give back), and it invalidates the per-line
running total, the flat `by` dictionary and the name-keyed line table at once while leaving the
brute-force model trivially right.

## Stage 2 - the verifier contract (revised, additive)

Recorded below as it is frozen; the 48 answers frozen before this recovery must come out
byte-identical from the revised model, and `authoring/span-claim-charge/build_gt.py` checks
that on every run.

### Declared artifacts

```
/app/store/dev.py
/app/store/hold.py
/app/store/item.py
/app/store/line.py
/app/store/tally.py
```

### The op language

Unchanged from the uploaded bundle (`dev n p d w s t x v c g f m`, `#` comments, blank lines
skipped), plus one query:

```
u <line>          -> u <line> ref=X excl=Y     or  u <line> err=nosuch
```

### The family

A line made with `n` stands alone. `p <line> <new>` records that `<new>` is stamped from
`<line>`. A line's family is the line itself, every line stamped from it, and from those in
turn. When a line is dropped, the lines stamped from it count from then on as stamped from the
line it was itself stamped from; when it was stamped from none, each of them stands alone. A
line made again under a dropped name is a new line standing alone. `u <line>` reports the total
length of the spans any line of the family stands on, and the total length of the spans whose
whole standing set lies inside the family.

### The graded decisions

The thirteen from the uploaded bundle, unchanged in meaning:

 1  best fit, lowest on a tie
 2  largest run whole when nothing fits, lowest on a tie; refused and unchanged when the total
    is short
 3  a block is rewritten where it stands exactly when no claim but the one covering it stands
    on that block of its span - a second claim of the same item counts
 4  a span goes back only when no claim covers any part of it, whole, merging both sides
 5  inside one write the replaced claims go first, so their spans can serve the same write
 6  the room is checked against the free total the write's own release produces
 7  one allocation is laid over the fresh stretches in item order; stretches straddle pieces
 8  referenced space is the whole length of every span the line stands on, once
 9  exclusive space is the part of that no other line stands on
10  a stamp puts a second line on every span the origin stands on
11  freed by dropping a set is the spans whose whole standing set is inside it
12  a share moves coverage without allocating; a copy still standing keeps its span
13  a refused command leaves the store as it was

Added by this recovery:

14  a family's referenced space counts a span once however many members stand on it
15  a family's exclusive space is the spans whose whole standing set lies inside the family,
    which is neither the sum of the members' exclusive space nor the origin's alone
16  a stamp leaves the origin's family charge where it was while the origin's own exclusive
    space collapses
17  a dropped line's stamps count as stamped from the line it came from
18  a dropped line that came from none leaves its stamps standing alone
19  a line outside the family standing on a span removes it from the family's exclusive
    space and changes no member's referenced space
20  a name made again after a drop is a new line standing alone

### Interacting pairs (B2)

- 3 x 9: the same claims answer two questions and a count per span answers neither.
- 5 x 6: the doomed spans have to be found before anything moves, because the room is judged
  after a release that has not happened yet.
- 2 x 7: the run shape at the instant of allocation decides how many pieces a write becomes,
  and the pieces are laid across stretches rather than one to one.
- 10 x 16: the same stamp collapses `c` of the origin and leaves `u` of the origin unchanged.
- 17 x 15: spans standing on two stamps of a dropped line belong to the origin's family
  afterwards, so whatever a span carries about its standing set has to move rather than be
  recomputed.
- 19 x 14: a share into a foreign line removes a span from a family's exclusive space without
  moving any member's referenced space.
- 20 x 17: the tree has to be keyed on line identity, because a dropped name can come back as
  a line that stands alone.

### Prong C, and the route-around

C1: both sides of every fence are enumerated in `tests/cases.py`. C2: no shipped program
contains a family corner; the graded programs are generated after the container is gone. C3:
four families measured (`authoring/span-claim-charge/time_slow.py`). C4: exact all-or-nothing
traces. The route-around is blocked by the artifact list.

### Correct variants that must score 1

Planned: `authoring/span-claim-charge/variants/ok-cells` (one entry per block per item, free
map indexed by run length, family settled from sorted stamp paths - the sealed model's shape
in the five-module API) and `ok-marks` (claims kept, in-place test from per-block hit counts,
family settled by counts per ancestor).

## Difficulty record

`authoring/span-claim-charge/difficulty.toml`, scored with `tools/difficultycheck.py`.

| attempt | score | what changed |
|---|---|---|
| (uploaded bundle, as probed) | not scored before the probe; see `authoring/controls/span-claim-charge-as-probed.toml` | the design the probe solved 2 of 3 |
| 1 | see below | the recovery design |

## Gate results

(filled in as the stages complete)

## Stages 3 to 6 - what was built in the recovery

### Environment (Stage 3)

`environment/app_src/store/` is rebuilt on the coherent wrong model. `hold.py` gives a span a
start, a length and one reference count (`refs`) and decides the in-place test from that count;
`tally.py` adds the charges up on demand by walking the line's claims (referenced as claim
widths, exclusive as spans with one claim), freed-by-dropping a set as the members' exclusive
added up, and the family by walking a name-keyed parent map (`st.kin`) and adding the members'
charges up; `line.py` keeps that map and leaves it dangling on a drop, so the dropped line's
stamps fall out of the family it came from, and a name made again picks the old stamps back
up; `dev.py` is first-fit from a single run with a forward-only merge; `item.py` takes the
allocation before the replaced claims go, judges the room on arrival, and lays one piece over
the stretches. Nine shipped defects; every shipped program runs. The frozen driver gained the
`u` op (`ops.py`, `base/text.py`), `progs/kin.txt` shows the op on one stamp, `progs/tree.txt`
is a generated tree program and `progs/wide.txt` was regenerated with family questions in it.
`tests/pristine/` mirrors the tree (`sync_pristine.py --check`).

Measured: 623 lines of agent-facing Python (retained band 229 to 544; the excess is the frozen
driver and the eight shipped programs' loader, not the editable store, which is 379 lines).

Leak audit of the built tree, run as a procedure: a script that reads the shipped `Span`
finds `at`, `wide`, `refs` and nothing per line or per block; the shipped `kin` map is the
primitive the family rule needs and derives nothing (its two wrong behaviours are the shipped
defects, not clues); no shipped program drops a line that has stamps, shares across families or
asks `u` after a drop; `tools/deadfieldcheck.py` is clean, so no field is written and never
read. `tools/extraneouscheck.py` and `tools/imagecheck.py` are clean.

### Reference (Stage 4)

`solution/` is 716 lines including docstrings (605 before the recovery). `line.py` keeps line
records with `up` and `kids`; `hold.py` keeps `on`, `by`, `cover` and `lca` on each span;
`tally.py` carries `ref`, `excl`, `reach`, `lcat` and `deep` per line, fed from `gain` and
`lose`, and `retire` hands a dropped line's `lcat` and kids to its origin. Agreement with the
sealed model: 0 disagreements over the 59 hand programs and the whole 414-program population
(`agree.py final 45`), and again over the tree family at its final shape.

The tree family's shape was measured, not assumed, and the first two shapes did not bite
(`time_tree.py`, subprocess timings per program):

| stamps / writes / asks / items | reference | standing-set table | family walk |
|---|---|---|---|
| 240 / 40 / 100 / 400 | 2.7 s | 3.8 s | 22.4 s |
| 240 / 120 / 200 / 400 | 5.9 s | 11.4 s | 88.7 s |
| 240 / 200 / 250 / 400 | 8.9 s | 19.5 s | 150.7 s |
| 240 / 80 / 150 / 600 | 6.2 s | 7.8 s | 41.9 s |
| 240 / 40 / 150 / 900 | 5.3 s | 6.1 s | 41.8 s |
| 240 / 40 / 250 / 900 (shipped) | see the whole-set table below | | |

Two findings from the sweep. The walk scales with the questions and with the spans the asked
families stand on, so the questions were biased to the eight oldest lines and raised; the
table keyed by standing set scales with the number of distinct standing sets, which the tree's
branching bounds at about 1,300 whatever the write count, so it stays within a small factor of
the reference at every shape and cannot be killed without killing the reference. It is a
correct variant (`variants/ok-keys`), not a cheat, and the metadata says so.

### Model (Stage 2)

`tests/seal/model.py` settles the family from a different derivation than the reference: each
line carries a stamp path, the standing lines of a span sort in tree order, the deepest common
line is the longest common prefix of the first and last paths shortened past dropped lines,
and what a family stands on follows from the identity that the union of the root paths of a
sorted set of nodes is the sum of the paths minus the sum of the paths of neighbouring pairs'
common ancestors. `build_gt.py` froze 59 answers: 48 unchanged byte for byte, 11 added, 0
moved - the evidence that the change is additive.

### Instruction and metadata (Stage 5)

The brief states the write path as an observable (a span the replaced claims empty is free
before the fresh blocks are taken; the write is refused only when the total after that release
is short) rather than as a procedure, drops the refutation of the count-per-span reading, adds
the family paragraph and the `u` output, and re-derives every count from `gen.py`: 414 graded
programs (9 small families of 45 plus 3 of each large shape), `tree.txt` at 71,309 lines with
33,321 family questions. `tools/leakcheck.py` against the three trajectories now finds nothing
above the floor in any of them (before the rewrite: three phrases in trial 1, two in trial 2).
`hintcheck`, `structcheck` and `textcheck` against the `publish-settle-order` brief are clean.
Category moved from the retired `Software / Systems` to `Software / Algorithms`; the graded
work is allocation policy, interval bookkeeping and tree accounting.

### Cheats (Stage 6)

`authoring/span-claim-charge/emit.py` writes 52 cheats from the reference with asserted
substitutions: 36 wrong readings (the 29 from the uploaded bundle re-derived, plus
`gone-all-stand` - the reading trial 1 took - and six family readings: `fam-sum-excl`,
`fam-ref-sum`, `fam-self-only`, `fam-orphan`, `fam-lca-stale`, `fam-name-reuse`), four exactly
correct and over the limit (`slow-family`, `slow-charge`, `slow-fit`, `slow-sole`), the forgery
regenerated over 59 frozen answers and the shipped store, and the eleven isolation probes over
the shipped `tally.py`. `cheat_report.py` names the program that catches each reading and
times the slow families over the whole graded set; `readings.py` feeds `tools/readingcheck.py`.

## Stage 7 - the cold re-attack, on the finished task

Read the brief cold with the built tree in front of me, the way the probe agent will.

My first plan is the shipped store. I would keep the reference count per span and fix what the
brief names: the in-place test per block (I would try to read it off the count and find that
a second claim of the same item and a second line are the same count - the tiny program is
exactly that case, so the first fix would be to look at the claims themselves), the largest-run
fallback, the merge on both sides, the release before the allocation, the drop that gives its
blocks back. I would then run `wide.txt`, see the charges recounted per question take a
minute, and carry the two line numbers forward from the moments a line's count on a span
leaves or reaches zero - which means the span has to know its lines, so `by` gets designed
here, after the in-place test already forced `on`. That is two structures I did not plan for,
both forced by measurements rather than by reading.

The family is where I would not commit. Walking the tree for the members and applying the set
rule is the obvious implementation and it is right; `tree.txt` at 33,000 questions of families
standing on up to 200,000 spans is what tells me it is dead, and only after running it. From
there I see two routes and would not know which to take without trying: a table keyed by each
span's standing set (my `g` table, if I built one, extended with the family's mask), or
summaries kept against the tree. The first is what I would probably build, and it works; the
second is the reference. Either way the drop rule - stamps handed up to the origin, a reused
name standing alone - has to be right before either route answers correctly, and the drop is
where my first tree would be wrong: I would key it by name.

Estimated solves out of 8 after the recovery: 3 (range 2-4). Up from the 2 in the design
record because the table route is a second fast path that a solver who already partitions
spans by standing set for `g` extends in a few lines; down from the 6 measured before the
recovery because the shipped tree no longer carries the two-index record, the brief no longer
narrates the write path, and the family question has no running-total answer. This is inside
the band and short of the hard edge; the honest statement is that the task is harder than the
probed one by two findings (the span record, and the family fast path) and one rule with
consequences (the drop), not by an order of magnitude.

What did not survive the build, and is recorded rather than hidden: the standing-set table was
meant to die at scale and did not; it is a correct variant now. The gate against the walk
holds with the margins in the whole-set table below.
