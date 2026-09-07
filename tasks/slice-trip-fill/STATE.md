# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 6 - Anti-cheat` complete; `Stage 7 - Pre-flight and packaging` in progress.
Contributor confirmed candidate, category (Software / Algorithms), expert role and the
8 hour / 14400 s budget on 2026-09-07. The instruction still needs their review before
submission (D1): the draft in instruction.md is the assistant's, written from the fact
sheet, and has not been read back yet.

## Assistant's assigned role

Assigned by the contributor 2026-09-07, verbatim: "You are a senior
exchange-infrastructure engineer; you have spent years inside single-threaded matching
engines, order-book data structures, and the rulebook corner cases that only show up in
production replays."

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. No repository has entered the conversation, so the
  authored-on-top versus ablation choice is not owed yet; it is owed the moment one does.
- Task shape chosen (authored-on-top / ablation per docs/ABLATION.md): not applicable while
  there is no repository. If the contributor supplies one, the two-shape choice is owed before
  any candidate is proposed against it.
- Contributor's relationship to it: n/a
- License, and why vendoring it is permitted: n/a
- Pinned commit vendored into environment/app_src/ (.git stripped): n/a
- Load-bearing couplings found during research (file paths): n/a
- Identifier degradation done? n/a (the tree is authored here, so names are chosen in the
  legacy register from the start rather than degraded from an upstream)
- Proper-noun sweep done? n/a for provenance; the tree still carries no venue, vendor or
  product names by construction
- Upstream-diff check: n/a

## Task summary

`/app` is a single-instrument matching engine. A session file is a list of order messages;
`/app/run_book.py` replays one and prints an event line per fill, cancel, disclosure and
activation, then the resting book. The engine was rewritten and has been wrong since. The
agent repairs the matching decisions - the walk over the opposite side, disclosure of
partially shown orders, same-participant handling, all-or-nothing admission, the price band,
and activation of resting armed orders - so that the printed event stream matches exactly.

## Why it is hard

The naive walk ("take the opposite side best price first, fill each resting order, then look
at the armed orders") is coherent and right on ordinary sessions. Four stated rules make it
wrong, and each one changes the shape of the walk rather than adding a case to it.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the walk mutates the
  queue it is walking - a partially shown order rejoins the back of its own level the moment
  its shown part empties, and a same-participant resting order is pulled out from under the
  walk - so the iteration cannot be over a snapshot of the level; and the all-or-nothing
  admission rule needs the outcome of that same walk without any of its effects, so the walk
  has to be runnable and then unwound. A plan formed before reading the tree is written
  against a static level list and cannot express either, and the failure only appears when a
  level holds more than one order or a rejected all-or-nothing order has already pulled a
  same-participant order. The activation rule then re-times everything: the armed orders are
  tested after every fill against the price that fill made, not after the incoming order
  finishes, while the band that bounds those fills is snapshotted once per incoming order and
  does not move as the walk trades.
- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3, B2, C1, C2, C3, C4. A1: the
  retrievable matching-engine plan - a price-time walk over a level list, fill each resting
  order, then scan the stops - is specifically wrong here. A2: the concepts are stated as
  venue behaviour and never named, so no page is one query away ("iceberg", "self-trade
  prevention", "fill-or-kill" and "limit-up/limit-down" appear nowhere). A3: the
  all-or-nothing rule and a walk that mutates what it is walking have no single technique
  that satisfies both. B2: six rules that must hold at once, and getting the disclosure rule
  right changes what the admission rule has to simulate. Not B1: the tree is 300 lines and
  fits in one attention window, so the facts are adjacent however many files they occupy -
  the same honest position `focus-return-point` took. C1: both sides fenced - never pulling a
  same-participant order and pulling too eagerly both fail; never activating and activating
  everything both fail; over-retaining a shown order and under-retaining it both fail. C2: no
  oracle - the rulebook is authored, so there is nothing to compare against and nothing to
  run and see. C3: a measured scale family where a per-fill scan of the parked orders is
  quadratic (0.22 s against 22.8 s on the shipped sample, and the graded sessions run about
  three times larger). C4: exact all-or-nothing event streams over 34 enumerated corners, 300
  nonce sessions and 4 deep ones.
- Assistant's attack on the plan (its first plan, and where it is wrong): my first plan is
  "levels as a dict price -> deque; walk the opposite side in price order; for each resting
  order fill min(remaining, resting.remaining); pop it when empty; after the incoming order
  is finished, scan the armed list for anything the new last price has tripped; for
  all-or-nothing, sum the opposite side's quantity up to the limit first and reject if it is
  short." That plan is wrong in four places and only one of them shows up on a small
  session: filling a shown order to its full remaining quantity instead of to its shown size
  and requeueing it; summing available quantity without accounting for the same-participant
  pulls and for a band that steps with the fills, which makes the admission decision wrong in
  both directions; scanning armed orders once per incoming order instead of once per fill,
  which loses a whole cascade; and holding the band against the price the walk started from.
  I would not have committed to a walk that is decided before it runs, and the version I
  would have written first passes both shipped sessions.
- Estimated solves out of 8: 3 (design target 1; the realized rate drifts up). Raised from 2 to 5 by the honest Stage 7 re-attack below, then back to 3 by the scale repair that followed it.
- Difficulty score anchor: 50 at first complete submission, pending contributor approval
- Score history: 2026-09-07 - task created, no external result yet
- Leak audit (docs/DIFFICULTY.md): run as scripts, 2026-09-07, per mechanism. (1) Nothing
  in the tree is a function of the correct trajectory: no expected output ships, the brief
  quotes only WRONG printouts, and no row count or digest of a correct run appears anywhere.
  (2) No stored derived quantity: an order record carries qty, shown size and remaining, all
  primitives the engine must maintain; nothing carries reachable quantity, a fill count, or a
  flag saying an order is partly shown. (3) No unused affordance: `Side.rear` was exactly
  that - a method only the correct rotation needed, called by nothing shipped - and it was
  deleted; the corrected preflight affordance check now reports the tree clean. (4) No
  manifest: `sess/` is three files found by listing a directory, and no config enumerates
  them. (5) No self-labelling data: a session carries orders, not annotations, and no field
  says an order is unusual. (6) No per-axis confirmation: the engine prints what its own
  rules produce, so a wrong reading prints a plausible session and the agent gets no signal
  until the sealed model sees it. Re-run after every change to the tree.
- Expert path, described step by step: see the `Expert path` section below
- Originality check: searched 2026-09-07. Matching-engine architecture (price-time priority,
  level maps, FIFO queues) is thoroughly documented and there are open implementations that
  list the same order-type vocabulary (`ArjunVachhani/order-matcher` among them), so the
  substrate is retrievable and is deliberately shipped in the tree rather than being the
  work. No page found describes a rulebook with this combination, and searches for the
  load-bearing interactions (a shown-size requeue mid-walk, an all-or-nothing check that has
  to simulate same-participant pulls, a band snapshotted per incoming order, activation
  tested per fill) returned only retail broker explainers of what a stop order is. An earlier
  candidate - a declarative resource planner whose central discovery was destroy/create node
  splitting with keep-alive propagation - was rejected on this test: HashiCorp's own
  `docs/destroying.md` plans it end to end.

## Verifier contract - FROZEN after Stage 2

Frozen 2026-09-07, before the environment was finished. This does not change without the
contributor's explicit approval, because changing it changes what "correct" means.

- Artifacts the agent produces: `/app/eng/take.py`, `/app/eng/shown.py`,
  `/app/eng/hand.py`, `/app/eng/hold.py`, `/app/eng/trip.py`. The verifier reads nothing
  else from the agent's environment. They are overlaid onto a pristine copy of the tree;
  one the agent never wrote simply is not there and the shipped file stands.
- What is checked: the ordered event stream the engine emits for each session, exactly,
  with no partial credit - every `trd`, `pul`, `shw`, `rst`, `arm` and `trp` row in order,
  followed by the closing `bk`/`am` block that is the final state. Three session sets: 34
  enumerated (fixed, in cases.py, expected results in gt.json), 300 generated from the run
  nonce, 4 deep ones from the same nonce. Plus integrity: the executed tree outside the
  five artifacts byte-identical to pristine; sealed function fingerprints at import and
  after each session; the event sink refusing any caller that is not `Emit.row`; the
  interpreter's tally of entries into `Emit.row` equal to the row count and still armed at
  the end; and the run nonce present in the report.
- Tolerances: none. Exact integer and string comparison throughout.
- Ground truth, and where it lives: `tests/oracle.py`, an independent implementation of the
  same rules, and `tests/gt.json` as a tripwire on it. Both root-only inside the verifier
  image; neither is reachable from the run.
- Route-around guard: the five artifacts are the only files the agent may hand over, the
  driver and the emitter are sealed, and the interfaces are frozen - a submission cannot
  restructure the task into one its default plan handles, and cannot write its own trace.
- The scale bound is the wall clock on the run (300 s kill), not a duration compared in the
  grader, so the margin runs in the safe direction: nothing correct fails for being slower
  than the reference, only for being the wrong shape.

## Expert path, step by step

1. Run the two shipped sessions, read the printout against the stated rules, and find the
   two visible defects: a resting order handing over more than it shows, and a walk that
   stops one level in.
2. Read `mkt/drv.py` and `mkt/bk.py` to establish what is sealed - the message loop, the
   rest/cancel decisions, the emitter, the book - and therefore that the whole of the work
   is the five files under `eng/`.
3. Fix disclosure: the fill is bounded by the shown size, and the re-disclosed order goes
   to the back of its own level. Notice this makes the level mutate under the walk, so the
   walk has to ask the book for its front on every pass rather than iterate a snapshot.
4. Fix the band: read the last trade price on every pass rather than once. Check the
   consequence on a session where a level is cleared by a same-participant pull rather than
   by a fill - the price does not move, so the walk stops at the next gap.
5. Fix admission: an order that cannot fill entirely must leave nothing behind. Either
   decide first with a read-only pass over the levels (carrying a shadow last price, adding
   up the other participants' resting size including the hidden part), or copy the state and
   walk the copy. Both pass; the first is what the reference does.
6. Fix activation: ask the parked orders after every fill rather than once per order, and
   take the ones that fire in arrival order.
7. Time `wide.txt`. Discover that step 6 made the shipped scan several hundred times more
   expensive, and order the parked orders by trip price so each is touched once.

## Decisions and their reasons

## Decisions and their reasons

- 2026-09-07. Candidate chosen after attacking three: (1) a declarative resource planner -
  killed by the search test, the whole plan including node splitting and keep-alive
  propagation is in the upstream tool's own docs; (2) a module-name resolver whose imports
  reach a fixpoint - dropped after honest attack, because with ambiguity as a lattice top the
  correct plan really is "iterate until nothing changes", which a frontier agent writes in one
  shot; (3) this one.
- 2026-09-07. Rejected a numerical-equivalence ML candidate (gradient accumulation that must
  reproduce a full-batch step under a memory cap). The agent can write the full-batch
  reference itself and check every sub-part against it, which is the per-axis-confirmation
  anti-pattern in `docs/DIFFICULTY.md`; a task an agent can hill-climb is an execution task.
- 2026-09-07. Category will be proposed as Software / Algorithms, not Operations / Finance.
  The graded work is priority-queue maintenance, walk order over a mutating structure, and an
  activation cascade; no part of it needs financial reasoning, and the guideline's own
  Operations row is about "quantitative finance and risk", not market infrastructure. This is
  the same correction the platform applied to `alias-settle-report` on 2026-09-04, in the same
  direction. Contributor confirms.
- 2026-09-07. Deliberately not reusing the work-counter budget idiom (`tools/simcheck.py`
  reports four earlier bundles already grade against one). Any resource gate here is a wall
  clock limit on a wide session, stated in the brief, and it will be measured before it is
  claimed.

## Stage 7 re-attack, and the repair it forced (2026-09-07)

Read the finished instruction cold and tried to one-shot it. The honest answer was worse
than the Stage 1 attack: every rule is stated plainly, and a careful agent that implements
exactly what is written gets almost all of them right first time. Working through them one
by one - the fill bounded by the shown size, the re-disclosure to the back, the band read
from the last fill, stop rather than skip, all-or-nothing atomicity, activation per fill in
arrival order - a literal implementation of each stated sentence is the correct one. The
only step that did not follow from the text was the cost of activation once its timing is
fixed. That is one discovery, not two, and the estimate moved from 2 solves to about 5:
`note-carry-forward`'s failure mode, where adding decisions does not add difficulty because
each stays visible and locally checkable.

The repair is the one `docs/DIFFICULTY.md` prescribes and `alias-settle-report` measured: a
real input family in which the natural correct method stops fitting. All-or-nothing
admission has three correct shapes - copy the state and walk the copy, walk and rewind, or
decide with a read-only pass - and the first is what a solver writes first. A book-heavy
session makes it cost the book on every such order:

| shape | shipped sample | one graded session |
|---|---|---|
| reference (decide, then walk) | 0.02 s on `sess/book.txt` | 0.05 s |
| walk and rewind | 0.02 s | 0.05 s |
| copy the state per order | 20.85 s | 192.23 s |

Two of those sessions sit in the graded set behind a 300 second kill, so the first shape is
correct and unaffordable while two other correct shapes pass with three orders of magnitude
of headroom. The same is true on the other axis, measured earlier: the parked-by-scan form
needs over 400 s for 300 small sessions plus one parked-heavy deep one, where the reference
needs 21 s for 300 plus four.

Both unaffordable forms are kept in `authoring/slice-trip-fill/slow/` rather than in
`cheat/`, with their measurements, because neither is wrong about the rules - a cheat is an
attempt to score without doing the work, and these do the work. `ok-copy-state` moved out of
the correct-variant set for the same reason; four correct variants remain and all four score
1.

The instruction now states both shapes and both sample sessions, so the boundary is visible
before it is hit rather than after.

## Self-probe

Not run, and deliberately. The order here was design, then model, then environment, so by
the time there was anything to solve cold I had written both implementations and every
wrong reading. A cold solve by this author would measure memory. What stands in its place:
thirteen whole-engine wrong readings, each separated by a named enumerated session and each
moving between 3.8 and 85 per cent of the generated population; the no-oracle property,
which is a fact about the bundle rather than a judgement; and the two measured scale
boundaries above. A self-probe reported as passed by a contaminated author is worse than no
self-probe.

## Validation status

Docker image pulls are blocked in this environment by the egress policy
(`production.cloudfront.docker.com` returns 403 to CONNECT), so no image could be built
here and no container-level gate could run. Everything below is either host emulation
(`authoring/slice-trip-fill/trial.py`, which reproduces what `tests/test.sh` does with the
tree and the grader but not the privilege drop, the root-owned reward channel or the
root-only ground truth) or a static analysis. The container gates are outstanding.

| Check | Status | Notes |
|---|---|---|
| Agent image builds | NOT RUN | docker pull blocked by egress policy; `tools/imagecheck.py` assembled the image contents statically, dropped the reference in and drove all four shipped sessions: clean |
| No answer leaked into agent image | pass | environment/Dockerfile copies only `app_src/`; leak audit run as scripts, above |
| `harbor run -a oracle` = 1 | NOT RUN | blocked with the above; host emulation scores 1 at the full graded scale (300 small + 4 deep) |
| `harbor run -a nop` = 0 | NOT RUN | blocked with the above; host emulation scores 0 |
| Cheats all score 0 | pass (host) | 25 cheats, each caught by a named assertion, `authoring/slice-trip-fill/cheat_report.py` |
| Packaged archive | pass | `scripts/package.py` then `tools/zipcheck.py`: 76 entries, 154 KB, no findings; no authoring or STATE material, no CRLF, `.sh` files 755 |
| Correct variants score 1 | pass (host) | 4 variants, all 1 |
| Reference at the full graded scale | pass (host) | 300 small + 4 deep (both shapes): 13 tests pass, reward 1, 23 s wall against a 300 s kill on the run |
| Reference vs sealed model | pass | final sweep 4000 small sessions across eight seeds plus six deep ones of both shapes, zero disagreements; several thousand more during the build |
| `preflight.py` | pass | no errors, no warnings |
| `harbor check` rubric | NOT RUN | needs a provider API key, which this session does not have |
| readingcheck | pass | 13 readings, all separated by a named enumerated session |
| onelinecheck | pass | 3 of 6 graded decisions have no exact rule at depth <= 2, including all-or-nothing admission |
| forgecheck | pass | an answer-key probe carrying the whole ground truth scores 0 |
| deadfieldcheck / extraneouscheck / catcheck / hintcheck / structcheck | pass | clean |
| simcheck | pass | no shipped file near another bundle's; grades what no earlier task grades |

## Quality self-review (docs/QUALITY-REVIEW.md, 2026-09-07)

Criterion by criterion, with the file that satisfies it.

Instruction <-> verifier agreement. Every rule the tests compare has a sentence:
disclosure and the queue (instruction para 6 -> `test_disclosure`, five enumerated
sessions), the same participant (para 7 -> `test_same_participant`, four), the band and
the limit (para 5 -> `test_the_band`, five), all-or-nothing (paras 8-9 ->
`test_all_or_nothing`, eight), activation and `pull` (para 10 -> `test_activation`, six),
the ordinary side (paras 8, 10 -> `test_ordinary_sessions`, six), the event and book
formats (para 11, compared on every session), the scale (para 12, enforced by the wall
clock). The reverse direction holds too: nothing in the tests is unstated, and the one
place it nearly was - whether a fired order can be parked again - was closed on re-reading
("each fires once and is not parked again"). The five files the verifier reads are named
with absolute paths in para 3. The output schema is in para 11.

Instruction prose. Measured with tools/textcheck.py against all six retained briefs, not
one: burstiness 0.79, short sentences 22%, paragraph sd 34.8 sit inside the range of the
briefs that cleared the screen (0.74-1.11, 21-40%, 31.0-103.5), next to
`focus-return-point` and `token-seam-emit`. tools/structcheck.py: clean. Reading it as
prose, one thing was wrong and is fixed: the activation paragraph used to say "every fill
looks at all of them", which prescribes the scan the scale bound then punishes. It now
states when a parked order may fire and leaves the method alone. STILL OWED: the
contributor has not read this draft. It is the assistant's wording from the fact sheet, and
D1 is not satisfied until they have been through it.

Verifier rigor. Rows come from `mkt/ev.py`, which is not editable, through a sink that
refuses any caller but `Emit.row`, with the interpreter's own tally of entries into it
compared against the row count (`test_instrumentation_intact`). Test code is grouped one
function per rule and each carries what it checks. Nothing depends on wall clock inside a
comparison, on the network, or on an ordering not itself under test.

Environment hygiene. `environment/Dockerfile` copies `app_src/` and nothing else - no
`tests/`, no `solution/`. Verifier dependencies are baked in `tests/Dockerfile`. Every pip
install is pinned; no apt package is. Names in the instruction all exist in the tree,
checked one by one.

Solution quality. `solution/solve.sh` copies four source files in and drives every shipped
session; it computes nothing by echo. It uses nothing the agent could not.

Anti-cheating. The answer is not in the tree (leak audit above, run as scripts). Comparison
is exact. 25 cheats score 0, each caught by a named assertion, including an answer-key
probe carrying the whole ground truth.

Metadata. `Software` / `Algorithms`, both from the guideline table; the graded work is
priority-queue maintenance, walk order over a mutating structure and an activation cascade,
and no part of it needs financial reasoning - the same correction the platform applied to
`alias-settle-report`. Five tags, all specific to this task, none restating the taxonomy.
`difficulty_explanation` names the four concrete corrections and both measured boundaries,
and states the terse-naming and no-comment style as a design choice. `solution_explanation`
describes the method and why an expert works that way. `verification_explanation` says what
passing proves. `relevant_experience` is specific. Eight hours, consistent with the claim.

Known risks to flag to a reviewer: the container gates have not run here (see Validation
status); the instruction has not been through the contributor; and `tests/test.sh` and
`tests/runner.py` sit at 0.62 and 0.61 mechanical similarity against `guard-mark-unwind`,
which is the shared isolation architecture rather than copied text - below the 0.75 that the
one measured similarity rejection sat at, and left alone deliberately rather than reworded
to move a number on security-critical plumbing.

## Open questions and next steps

Asked the contributor (2026-09-07, one batched message): candidate choice, category and
label with the guideline table shown, domain-expert role, whether there is a repository, and
the expert-time / agent-budget numbers. Building Stage 2 (verifier contract) meanwhile.
