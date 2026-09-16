# Task state

Working memory for this task. The assistant updates it after every stage. Assume the next
session starts with no memory of this one - anything not written here is lost.

## Current stage

`Stage 2 - Verifier contract` (contract frozen below; environment work follows)

## Assistant's assigned role

Data platform engineer on the evaluation path of a derived-field service: the part that decides
which derived fields have to be worked out again when a source value is published, and what a
preview of an unpublished value is allowed to reuse and to leave behind.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task
- Task shape chosen: not applicable (no repository vendored)
- Contributor's relationship to it: not applicable
- License, and why vendoring it is permitted: not applicable
- Pinned commit vendored into environment/app_src/: not applicable
- Load-bearing couplings found during research: not applicable
- Identifier degradation done? yes, authored directly in the legacy register (`fld/`, `keep`,
  `look`, `make`, `feed`, `hold`, `need`, `pub`, `over`) - no upstream names exist, so no
  conversion table is needed and nothing in the tree carries provenance
- Proper-noun sweep done? nothing to sweep: every name in the tree was authored here
- Upstream-diff check: not applicable

## Task summary

`/app` is the evaluation path of a derived-field service. A field is either a source whose value
is published, or a derived field defined by one small form over other fields. A program is a text
file of ops: definitions, publications, questions, and preview blocks that ask what publishing a
value would produce without publishing it. The service evaluates a field's body only when it
cannot show that the value it already has still stands, and it writes one line every time a body
is evaluated - that log is the cost record and the graded artifact. The shipped service is wrong
in six places at once. The agent fixes six files under `/app/fld` so that every program's trace
matches, and so that the two stated scale programs get through inside the stated limit.

## Why it is hard

The rules are all in the brief. What is not in the brief is which of the structures they seem to
ask for survive all of them at once. The evaluation rule turns the work list inside out (walk down
from what was asked, not out from what changed), the branching forms make the record of what a
field read a thing that changes under the field's own feet, and the preview has to be cheap,
invisible to the kept results, and still be there to stand on when the previewed value is
published. Every form is a pure function of what it reads, so a plan that evaluates too much
prints exactly the right values: the wrongness lives only in the run lines.

- Expert time estimate: 9 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the retrievable design for keeping derived values fresh pushes outward from what changed to its dependents, but this service is graded on a demand that walks the other way, down from the field asked, and stops at the first recorded read whose value moved; the agent then has to find that a preview cannot be a saved copy of the kept results, because its work has to be installable when the value is later published, which is a second structure rather than a fix to the first.
- Tactics making that true (docs/DIFFICULTY.md - prong A poison / prong B withholding / prong C late failure): A1 the outward-propagation prior is specifically wrong and is graded; A2 the rules never name caching, invalidation or provenance; B2 seven rules interact, each changing what another means; C1 both sides of every fence graded; C2 values stay right under the wrong plan so the agent's own oracle confirms nothing; C3 two exactly-correct families measured infeasible at the stated scale; C4 exact all-or-nothing traces over a seed drawn after the container is gone.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): first plan is a value plus a stale flag per field, a reverse index from each field to its readers, dirty-marking outward from a publication with early cutoff on unchanged values, and a preview served by copying the kept results and restoring them; it is wrong three ways - it evaluates fields nothing asked for, it checks declared arguments instead of the reads the last evaluation took so a flipped branch is checked against the arm it abandoned, and the saved copy is both unaffordable at scale and leaves nothing for the publication of the previewed value to stand on.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 2 (range 1-4)
- Difficulty record score (tools/difficultycheck.py on authoring/trial-keep-adopt/difficulty.toml,
  before Stage 2): attempt 1 on 2026-09-16 scored 100/100, in band, one warning that the resource
  gate was not yet measured; the gate was then measured before any environment code was written
  (numbers below) and the record's `measured` flag set.
- Difficulty score anchor (50 at first complete submission, approved by contributor): 50 (anchor). Rubric shape: every prong carries something; weakest row is B1 (the tree is compact by design, like focus-return-point - difficulty is interaction, not distribution). No rows at 0. Strongest are C2 (values stay correct under the wrong plan; only run lines move) and A1/A2 (the demand-walk-down contradicts the outward-propagation convention and is never named).
- Score history (date, score, what moved, and any pipeline re-anchor): 2026-09-16 100/100 at
  design time.
- Leak audit (docs/DIFFICULTY.md): the shipped service keeps a publication stamp per field, which
  is one of the six defects and cannot express what the correct check needs, and nothing in the
  tree derives one from the other; the op language has publish, ask, preview and end only, so no
  query reports whether a field is fresh, what it last read, or how many times it ran; the trace
  writer is frozen, so the run lines cannot be reshaped; no reverse edge from a field to its
  readers is stored anywhere, so nothing can be read off the definition table that says which
  fields a publication reaches; the shipped example programs exercise the language and the one
  wrong line the brief names, and none of them flips a branch guard, ends a preview and asks
  again, or publishes a previewed value; the sealed model, the frozen answers and the pristine
  tree exist only in the verifier image, in a directory locked to root before any submitted code
  runs.
- Expert path, described step by step: run the shipped service on the small program the brief
  names and reproduce the wrong line; read the frozen definition table and trace writer to learn
  that a run line is the only observable; work out from the evaluation rule that the check is a
  walk down the reads the last evaluation took, in that order, stopping at the first difference;
  move the per-field record from a publication stamp to the ordered list of fields read with the
  value each returned, and make an evaluation replace that list outright; make the two branching
  forms read only the arm they take; restructure the preview as a layer laid over the kept results
  holding only the fields that ran inside the block; keep that layer past the end of the block and
  install it when the previewed value is published, discarding it when a different value is
  published to that field; settle each field once per publication and once per layer; time the two
  stated scale programs against the stated limit.
- Originality check: searched 2026-09-16 for demand-driven incremental recomputation with early
  cutoff and for retained hypothetical evaluation adopted on commit. The first returns the Adapton
  papers, a compiler query system's red-green chapter and several incremental-computation
  libraries - they describe validation and early cutoff at node granularity against revision
  stamps, which is the base half of this contract and is deliberately deviated from (the check
  here is against the values the last evaluation read, in read order, and the read list is
  replaced rather than merged). The second returns nothing that plans a preview whose work is kept
  past the block and installed when the value is published. No public write-up of this rule set
  exists; recorded as a residual risk that the base half is retrievable, which is why it is the
  half the worked example gives away.

## Instruction contract (docs/INSTRUCTION-CONTRACT.md, read before anything else)

- Instruction trace (authoring/trial-keep-adopt/trace.md; rows walked, none left unstated, tracecheck result): trace.md walks all 4 test functions, 22 enumerated cases, 6 artifacts, the 60 s clock and every model rule; every row cites a sentence; tools/tracecheck.py is clean.
- Identifiability (readings enumerated, which survived the published evidence, what separated them): 19 readings built as working services; 16 wrong ones are each separated by a named enumerated case (readingcheck.py); reads-set was proven equivalent to the reference and promoted to a correct variant; pre-copy and no-memo survive on values and are separated only by the stated 60 s limit.
- Shortcut strategies scored (nop, constant, positional, replayed example; score and cases matched): nop 0 (shipped engine wrong in six places, caught across every family); constant 0 (run lines are the graded output); replayed worked example 0 (every graded program differs from tiny.txt); always-evaluate-never-check is the no-memo shape, correct on values but killed by the deep limit.
- Independent implementation behind every tolerance and limit (path, measured headroom): the 60 s clock is validated by two naive families written apart from the reference (authoring/trial-keep-adopt/readings/pre-copy at 88-95 s on wide alone, no-memo over 240 s on one deep program) against the reference at ~3 s for the whole set; exact-trace equality is validated by the sealed model plus two correct variants.
- Undecided decisions from the cold-reader pass (author-run or fresh session; sentence or example added for each): author-run cold-reader pass over every graded output; sentences added for run-line ordering, the same-value no-op, pin-demands-first, and the layer's fate on each publication kind; tiny.txt gives the run-order convention freely.

## Verifier contract - FROZEN after Stage 2

Once agreed, this does not change without the contributor's explicit approval.

- Artifacts the agent produces: `/app/fld/keep.py`, `/app/fld/look.py`, `/app/fld/make.py`,
  `/app/fld/feed.py`, `/app/fld/hold.py`, `/app/fld/need.py`. Nothing else is taken; the verifier
  lays those six over its own pristine copy of the tree.
- What is checked: the exact trace a program produces, line for line, over enumerated hand
  programs frozen in `gt.json` and programs generated inside the verifier from a seed drawn after
  the agent's container is gone. The whole graded set must complete inside the worker's wall
  clock, which is the execution limit stated in the brief.
- Tolerances: none. Exact string equality on every line, all or nothing.
- Ground truth, and where it lives: `tests/seal/gt.json` for the hand programs, frozen before the
  grading file was written, and `tests/seal/model.py` for the generated ones; both in a directory
  locked to root before any submitted code runs. The grader asserts the model still reproduces
  `gt.json` exactly before it grades anything.

### The graded semantics, in full

A field is a source (`raw`, its value published, 0 until first published) or derived by one form:
`add a b` reads a then b and is their sum; `cap a k` reads a and is the smaller of it and k;
`pick g a b` reads g and then reads a when g is not zero and b when it is, and is what that arm
returned; `gate g a` reads g and, only when g is not zero, reads a, and is that or 0.

1. A demanded field that has no kept result is evaluated. A source is never evaluated and never
   prints a line.
2. A field with a kept result is checked: the fields its last evaluation read are demanded again,
   in the order it read them, and compared with the value each returned then.
3. The check stops at the first read whose value differs; the remaining recorded reads are not
   demanded at all, and the field is evaluated.
4. A check in which every recorded read returns the value it returned before keeps the value and
   prints nothing.
5. An evaluation records the fields it read, in order, with repeats, and that record replaces the
   previous one outright.
6. `run <name>` is printed when a field's evaluation finishes, so the fields it read appear above
   it. `ask <name>` prints `val <name> <value>`. Nothing else is printed.
7. Publishing to a source the value it already carries changes nothing at all.
8. Inside a preview block the previewed source reads as the previewed value. A field whose check
   passes under that value keeps its kept result and is not evaluated.
9. A field evaluated inside a preview block leaves the kept results untouched; its result belongs
   to the preview.
10. At the end of the block the preview's results are retained. Publishing that same value to that
    same source installs them as kept results; publishing a different value to that source
    discards them; publishing to any other source leaves them standing; opening another preview
    block discards them.
11. An installed result is checked like any other, so a read that moved while the preview stood
    makes the field evaluate again.
12. The whole graded set completes inside 60 seconds.

### Prong C tactics this contract uses, and the route-around guard

- C1: every rule above is graded from both sides - an enumerated program fails an implementation
  that evaluates too much and another fails one that evaluates too little.
- C2: every form is a pure function of what it reads, so evaluating too much prints the right
  values; the only observable that moves is the run lines, and no query exposes a kept result.
- C3: two exactly-correct families are measured infeasible at the stated scale (below).
- C4: exact traces, all-or-nothing, enumerated corners plus a generated population drawn from a
  seed the submission never saw.
- Route-around guard: six files under `/app/fld` are the only artifacts. The driver, the op
  language, the definition table and the trace writer are the verifier's own pristine copy, so the
  log format, the program language and the field table cannot be reshaped.

## Decisions and their reasons

- The preview is retained past the block and installed on publication of the previewed value,
  rather than discarded at the block's end. This is the second discovery the design rests on: it
  makes the obvious isolation (save the kept results, restore them at the end) both unaffordable
  and structurally unable to do what the rule asks.
- A publication to another source leaves a standing preview alone. That is what makes the late
  case - preview, unrelated publication that moves a read, then publication of the previewed value
  - a program in which the installed results have to be checked rather than trusted.
- Values are integers and every form is pure, deliberately: it is what denies the obvious oracle.
- The worked example in the brief demonstrates the cutoff rule, which is the one half of the
  contract public material already covers. It was searched for rather than chosen, against the
  requirement that it decide as few of the other readings as possible.

## Measured resource gate (run before the design depended on it, 2026-09-16)

Prototype at `/tmp/.../proto.py`, three readings of the same semantics, identical traces:

| shape | correct | naive family | naive |
|---|---|---|---|
| ladder of 22 diamonds, 2 rounds | 0.00 s | a field settled every time it is reached, never once per publication | 15.32 s |
| 20000 chains (60000 fields), 20000 previews | 0.31 s | preview by saving the kept results and putting them back | 32.87 s |

The ladder shipped is 30 diamonds deep, where the naive family is 2^8 times worse again. Both
families print byte-identical traces to the correct one on everything they finish, so the limit is
the only thing that separates them.

## Validation status

Docker Hub's blob CDN is denied by this environment's egress policy, so `harbor`/`docker build`
cannot pull a base image. The two-stage trial was run instead by `authoring/host_trial.py`, which
runs `tests/test.sh` verbatim as root (privilege drop to uid 1002, session and wall clock,
root-owned reward channel, reap, reward last). Container evidence is still owed on the platform.

| Check | Status | Notes |
|---|---|---|
| Agent image builds (imagecheck) | pass | tools/imagecheck.py assembles the image tree and runs the four shipped programs; no missing COPY |
| No answer leaked into agent image | pass | seal/model.py and gt.json live only under tests/; catcheck and manual inspection clean |
| oracle = 1 (host_trial) | pass | 25 graded tests pass; reward 1 |
| nop = 0 (host_trial) | pass | shipped engine fails every family; reward 0 |
| Cheats all score 0 (host_trial --all) | pass | 30/30 trials behaved: oracle 1, nop 0, all 28 cheats 0 |
| Correct variants = 1 (host_trial --variants) | pass | dedup and iter both score 1 |
| cheat_report (which case catches each) | pass | 16 semantic cheats each caught by a named enumerated case; both slow cheats over 60 s; forgery reproduces 20/22 enumerated, fails all 40 nonce |
| readingcheck (readings separated) | pass | 16 wrong readings separated by named cases; reads-set equivalent (a variant) |
| onelinecheck (no short rule) | pass | no graded decision reproduced at depth <= 2 |
| differential (reference vs sealed model) | pass | 0 disagreements over 3600 shaped programs |
| tracecheck (every graded assertion traced) | pass | clean |
| preflight.py | pass | 0 errors (benign warnings: frozen-module public functions, boilerplate) |
| difficultycheck (Stage 1 and Stage 7) | pass | 100/100 in band; measured tree 240 env, 213 ref, 6 editable |
| harbor oracle/nop on the platform | not run | Docker Hub CDN blocked here; owed on the platform |
| harbor check rubric | not run | needs an API key; not available here |

## Open questions and next steps

Build the environment, the reference, the sealed model and the generator; then the instruction,
the cheats and the gates.
