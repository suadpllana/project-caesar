# Task state

Working memory for `token-seam-emit`. Assume the next session starts with no memory of this
one â€” anything not written here is lost.

## Current stage

`Stage 2 â€” Verifier contract` â€” FROZEN 2026-09-06. Environment work follows.

## Assistant's assigned role

TODO: the contributor has not yet supplied the role sentence or `relevant_experience`.
Both are theirs to write and must not be invented. Needed before packaging.

## Source repository

- Repo URL: none â€” idea-based task.
- Task shape: authored from scratch.

## Task summary

The tree under `/app` is the output side of an inference server: recorded token ids are
replayed through a byte-level piece vocabulary and the stream releases bytes to a client as
decoding proceeds. The machine may never release a byte it would have to take back, and may
never withhold one it was safe to release. The agent supplies the release policy.

The graded artifact is the release point at every step: which bytes left the server at each
decode step, and the finish record.

## Why it is hard

A frontier agent's first plan is a pending byte buffer plus a matcher over the live stop set,
releasing the longest prefix that is character-complete and carries no live stop prefix. That
plan is coherent, matches every published incremental detokenizer, and is wrong here because
stop matching runs over the request's whole accumulated text and the floor decides only
whether a found occurrence *terminates*. An occurrence that completed while suppressed is
found at the first check after the floor lifts, so below the floor the release point is not a
bounded suffix â€” it is pinned at the earliest position that could still start an occurrence,
and in the worst case nothing may be released at all until the floor lifts.

- Expert time estimate: 8 hours (contributor's number, 2026-09-06).
- Agent timeout: 14400 s (contributor's number, 2026-09-06).
- Why a frontier agent cannot one-shot the plan: the bounded-window hold-back is not merely
  imprecise here, it is unsound, and the correction is not a patch â€” safety stops being a
  predicate of the current step and becomes one over the whole remaining life of the request.

## Tactics, attack and estimate

Tactics making that true, from docs/DIFFICULTY.md: A1, A2, A3, B2, C1, C3, C4. A1 - the bounded-suffix hold-back every published incremental detokenizer uses is specifically wrong here. A2 - the floor is described by what it suppresses and never named as a rule about retention. A3 - the exhaustive rescan is correct and infeasible while the cheap incremental form is unsound until the pinning rule is derived. B2 - eight decisions interacting through one release point, with no per-decision feedback anywhere in the tree. C1 - fenced both ways, so over-holding fails as hard as over-releasing. C3 - a measured semantic scaling boundary with the limit and the scale stated in the brief. C4 - exact and all-or-nothing over 300 nonce-generated requests plus a wide family.

My own attack on the plan (D1): my first plan is a pending byte buffer, a matcher over the stop
set, and the longest prefix that is character-complete and carries no live stop prefix. It
is wrong in two places that matter. It holds a bounded suffix below the floor, where the
hold-back is unbounded because a completed occurrence pins it; and its matcher remembers the
first occurrence it finds, where the earliest start can still move backwards when a longer
stop completes later. I can see where to start and my first plan would be wrong somewhere
that matters.

Estimated solves out of 8: 2 of 8. Designed at 1 of 8, adjusted up because every rule is stated and
the shipped tree fails visibly on two named requests, which gives a competent agent a
concrete place to start.

## The frozen verifier contract

Frozen 2026-09-06 from section 9 of the accepted proposal. The contributor answered
category, timeout and scale gate, and did not amend the contract.

### Graded artifact

One record per decode step per request, plus one finish record. Every step emits a record
even when nothing is released, so there is no representational choice and ties are impossible
by construction.

    <req> em <step> <hex>          bytes released at this step, hex, empty when none
    <req> fi <step> <reason>       reason is exactly one of: stop, eos, length

### Real work (two correct implementations agree by construction)

- The release point at every step, byte-exact.
- The finish step and the finish reason.
- The dropped tail on a stop finish.

### Implementation choice (never graded)

- Matcher construction (KMP, automaton, or rescan), buffer representation, internal ids,
  how the pristine tree's frozen helpers are called, module-private names.

### Grading shape

- Exact, all-or-nothing, over enumerated cases plus 300 nonce-generated requests built
  inside the verifier after the agent finishes.
- Fenced both ways: releasing early fails, and holding what was safe to release fails.
- A ceiling, not a published target: the wide family is graded by completion inside the
  stated execution limit, and the limit and the input scale are stated in the brief.

### Evidence, not report

- The runner owns the record gate; it refuses any caller that is not its own emitter.
- Source-side journal; `sys.monitoring` tally in a closure (tool id 3, callbacks bound once,
  never as bound-method attributes, tolerant teardown setting `armed = False`).
- Function fingerprints checked against a baseline compiled from pristine sources.
- Pristine tree hashed after the run, with the file count asserted before any comparison.
- Reward locked first and default 0, privilege drop, `setsid --wait`, `reap.py` walking
  `/proc`, root-only `gt.json` / `oracle.py` / `test_outputs.py`.

## The machine, precisely

Text the client has been sent is `T` â€” the concatenation of the decoded bytes of every
non-special piece so far, with one leading space dropped from the request's output.

At each step the release point `R` is the largest index that can never be affected by a
future termination, backed off to the last complete character boundary at or before it:

- `P1` = the earliest index `i` where a complete occurrence of a stop string starts.
- `P2` = the earliest index `i` where `T[i:]` is a proper prefix of a stop string.
- `R = min(P1, P2, len(T))`, then backed off to a character boundary.

Matching *terminates* the request only at steps at or after the floor. Below the floor a
found occurrence does not terminate, but it still pins `P1`, so retention below the floor is
unbounded. At the step the floor lifts, either the earliest occurrence truncates the request
at its start (reason `stop`, tail dropped) or the whole retained backlog becomes releasable
at once.

End of stream: an EOS piece below the floor contributes no text and the stream continues; at
or above the floor it finishes with reason `eos`. Reaching the cap finishes with reason
`length`. Matching still runs at that final step, so a stop occurrence there wins and the
reason is `stop`. A trailing incomplete character at the very end is dropped.

## The eight graded decisions

Core, all three regimes of the one release rule:

1. Retention below the floor is pinned at the earliest possible occurrence start.
2. The release burst at the step the floor lifts with no occurrence present.
3. Truncation at the earliest occurrence start when the floor lifts onto one.

Periphery:

4. The character-boundary backoff, byte-fallback pieces included.
5. The bounded suffix hold-back against stops when the floor is already lifted.
6. Special pieces contribute nothing to `T`, so an occurrence may span one.
7. The single leading space dropped once per request, which shifts match positions.
8. End of stream: suppressed EOS, flush, cap, trailing incomplete character, three reasons.

## Required intake answers

1. First plan: pending buffer, matcher over live stops, longest safe prefix.
2. What makes it wrong: matching is over accumulated text and the floor gates termination,
   not detection, so the bounded-suffix hold-back is unsound below the floor.
3. Second discovery forcing a replan: a complete occurrence below the floor pins the release
   point permanently, so safety is a property of the request's whole remaining life.
4. What could reveal either: any shipped helper that computes a boundary, any exposed pair of
   counts whose difference is the pinned position, any expected output. None ships. Audited
   as a procedure at Stage 3.
5. Ordinary case preventing overconservatism: a floor with no stop must release immediately;
   a stop with no floor uses the bounded rule.
6. Adversarial case failing late: an occurrence completing two tokens below the floor in a
   long request, where every earlier step looked correct.
7. Resource gate: MEASURED 2026-09-06 and kept. Scanning the accumulated text from the
   start at every step is semantically correct and quadratic; the fast path is an
   incremental matcher plus a character boundary that only ever moves forward. Curve on one
   request, reference against the shipped naive scanners: 2000 tokens 0.06 s / 0.34 s,
   4000 0.05 / 1.18, 8000 0.06 / 4.48, 16000 0.09 / 18.21 - the reference is flat, the
   naive path quadruples per doubling. At full scale, four wide requests: reference 0.65 s,
   naive 366.98 s, 565x, both emitting the same 150615 rows, so the naive path is correct
   and only infeasible. The graded set carries 8 wide requests; the stated run limit is
   600 s, which the reference clears by about two orders of magnitude and the naive path
   misses by roughly a factor of 1.2.
8. Wrong-plan cheat kept: hold against live stops only. Hand case separating it: a request
   with a floor of 6 whose stop completes at step 3.
9. Independent correct variant: an automaton matcher against a rescan matcher.
10. Why an expert still solves it: the symptom is visible in the shipped tree on two named
    requests, the floor semantics is readable from the request lifecycle, and each regime is
    testable against the runner once the rule is derived.

## Core-versus-periphery measurement (run 2026-09-06)

The first instrument was wrong and its verdict was discarded. It ablated `sm.py`, which
ships correct, and concluded the character seam dominated at 47.8% of requests against the
core's 15.2%. No agent produces that variant, so the number measured nothing. Frequency is
also not what decides the probe: with 300 nonce requests and all-or-nothing grading, any
reading that moves even 1% of requests scores zero with certainty.

The instrument that replaced it is `authoring/token-seam-emit/readings.py`, which builds
each wrong reading as a complete, reachable set of the four editable modules. Measured over
400 generated requests:

| reading | core | requests failed |
|---|---|---|
| `fixed-window` | - | 80.5% |
| `cut-after-stop` | - | 57.5% |
| `flush-on-stop` | - | 57.5% |
| `blind-below-floor` | yes | 47.0% |
| `floor-ignored` | yes | 29.0% |
| `no-pin` | yes | 29.0% |
| `eos-below-floor` | yes | 8.2% |
| `raw-flush` | - | 1.5% |

Every reading is separated. The distinction that matters is not the share but which
readings survive a careful reading of the brief: the periphery readings are each decided by
a sentence the brief must carry, and the core readings are the ones a solver still holds
after reading it, because they are consequences rather than statements. That split is what
the coverage walk and the WITHHELD list have to preserve.

## Brief budget (committed)

5,200â€“6,300 characters, no headings, no bullets, no labelled buckets. Measured basis:
`guard-mark-unwind` is 6,261 characters carrying 8 decisions, `alias-settle-report` is 5,286;
both cleared the AI-text screen. `focus-return-point` at 9,931 is not licence. If the eight
decisions will not fit that shape, a decision gets cut rather than the brief grown.

## Editable artifacts

Four declared, three ship wrong, one ships correct, and the brief says one may already be
right. This follows `guard-mark-unwind`, which passed with a four-file list and a three-file
`solution/`. Noted tension: the prompt's Stage B says every editable artifact must need to
change, while its Stage 9 asks for a candidate set wider than what changes. The retained
passing bundle resolves it the way this task does.

## Gates run (2026-09-06)

| gate | result |
|---|---|
| three-way agreement (reference / naive model / fast model) | 1539 requests, 0 disagreements |
| build_gt | 39 enumerated requests, 259 rows, model agreed on all |
| host trial, reference | reward 1, 11 tests, 347 requests in 4.1 s |
| host trial, shipped tree (nop) | reward 0 |
| readings | 8 readings, all separated, all named by an enumerated case; hardest core reading fails 50.5% |
| cheat_report | 18 cheats, all 0, every attestation probe caught by its own layer |
| forgecheck | forge carrying gt.json verbatim scores 0 |
| onelinecheck | no graded decision reproduced by a rule at depth <= 2 |
| catcheck | ML: environment 10, prose 17 |
| simcheck | no shipped file close to another bundle; grades what no earlier task grades |
| solvecheck, deadfieldcheck, extraneouscheck, hintcheck, structcheck | clean |
| textcheck | 4 cadence findings open - the contributor's voice pass |
| preflight | 1 error: relevant_experience empty (contributor's) |
| docker_trial --all / --variants | NOT RUN - no Docker on this host |

## The self-probe, honestly

It was not run, and it could not have been run validly. The procedure asks the author to
solve the task cold from `environment/app_src` and `instruction.md` alone; the author here
wrote the reference, the floor semantics and the case set, so a cold solve would measure
recall rather than difficulty. Reporting a green self-probe from that position would be
worth nothing.

The substitute evidence is stronger on the question that matters and weaker on one other.
Stronger: `readings.py` builds each plausible first plan as a complete reachable solver and
grades it through the real verifier, which answers "does the natural plan pass" directly -
it does not, failing 50.5% of requests. `onelinecheck` answers "is the answer short" over
the exposed state - it is not, at depth <= 2. Weaker: neither answers "could a solver
confirm each rule with its own harness", which only a cold agent can measure. The leak
audit is the partial answer - the tree ships no expected output, no comments, no docs, no
unused public function and no unread field - but an external probe is still the only real
instrument, and this bundle has not had one.

## Open items

- Contributor's role sentence and `relevant_experience` â€” needed before packaging.
- Contributor's laziest-cheat list â€” needed at Stage 6.
- Docker is not installed on this host. `docker_trial.py --all` and `--variants` cannot run
  here; the host emulation covers everything except image build, artifact upload, privilege
  drop and the reaper. That gap gets stated plainly in the handover.
