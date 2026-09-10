# Task state — aside-fit-sweep

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 — Pre-flight and packaging`

## Assistant's assigned role

A systems engineer who has written and debugged heap allocators: arena geometry, free-space
indexing, deferred coalescing, in-place resize, and the class of bug where a wrong placement
rule shows up ten thousand operations later as a different address and nowhere else.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task.
- Task shape: not applicable; nothing is vendored, every line is authored here.

## Task summary

`/app` is a heap allocator under test. A program is a text file of operations - declare the
arena geometry, then `get`, `put`, `fit` and `sweep` - and the host prints one line per event:
`at <id> <addr> <size>` when a range is placed, `no <id>` when a request cannot be served, and
`same <id> <size>` when a resize is answered in place. A free prints nothing. The shipped
allocator is wrong, and the five modules under `/app/pool/` are the agent's to rewrite.

The allocator's rules are ordinary except where they are not. A freed range of 256 bytes or
less is set aside whole rather than returned to the free map: while it is aside it joins no
neighbour, no allocation may be placed in it, and no range may grow into it, but a request of
exactly its size takes the one set aside most recently. When more than 32 are aside, the one
set aside earliest goes back to the free map and joins its neighbours there. A request the
aside list and the free map cannot serve returns everything aside to the map and tries once
more, and the list stays empty whether or not the retry succeeds. Placement is the leftmost
address whose next `n` bytes are free and lie inside one part, and if what would be left over
after it inside that part is under 16 bytes, the allocation takes those bytes too.

## Why it is hard

- Expert time estimate: 10 hours.

- Why a frontier agent cannot one-shot the plan (the strategic answer): every rule is stated,
  so the first plan is easy to form and semantically right. What the brief does not say is
  which structures survive all the rules at once. One collection has to carry two orders over
  the same entries with removals from the middle; the free map is neither the free bytes nor
  the complement of the live allocations; the size a range is set aside under is the size it
  was carved at, not the size that was asked for; and the placement question is not "the
  leftmost free range that is large enough" but "the leftmost address whose next n bytes are
  free and lie inside one part", which is a different query and rules out the index the first
  replan reaches for. A free prints nothing at all, so the only feedback on any of it is an
  address several thousand operations later.

- Tactics making that true (docs/DIFFICULTY.md): A1, A2, A3 (prong A), B2 (prong B), C1, C2,
  C3, C4 (prong C), plus the route-around guard. Each is justified in this task's terms in
  `authoring/aside-fit-sweep/difficulty.toml`.

  - A1: an allocator joins a freed range with its neighbours, grows a range into the free
    bytes that follow it, and frees the old range before placing the new one. All three are
    stated the other way here.
  - A2: nothing is named - no deferred coalescing, no quick list, no run index.
  - A3: reuse by exact size wants an index by size, eviction by age wants a queue, and reuse
    from the middle of that queue wants identity per entry. No single container gives all three.
  - B2: the free of a small range is an allocation event, a joining event, a growth event and
    an eviction event at once, and four modules have to agree about it.
  - C1: both fences on every axis (see the enumerated cases).
  - C2: a brute-force model written from the brief is correct for free and says nothing about
    the structures that must replace the scan.
  - C3: five measured boundaries, fast paths following from the one-part invariant.
  - C4: all-or-nothing over enumerated and nonce programs.

- Assistant's attack on the plan: my first plan is a dict from address to range, one
  address-ordered list of free ranges scanned from the left, a dict from size to a list of the
  ranges set aside, a counter for how many are aside, coalescing with both neighbours on every
  return, and a resize that frees then allocates. That plan is semantically correct in outline
  and wrong in five places I would not have found by reading: the aside list needs one queue
  with entry identity, the joining has to skip aside neighbours, the resize has to place before
  it frees, the size a range is set aside under is its carved size, and the scan cannot answer
  the fit inside the stated limit while the obvious replacement - a tree keyed by the largest
  free range - answers the wrong address at a part boundary. So: I can see where to start, and
  I could not commit to the full plan without exploring.

- Estimated solves out of 8: 3 (designed at 1 to 2; raised to 3 at Stage 7 after re-reading
  the finished brief cold, because every rule in it is stated and an expert who gets the aside
  list and the index right has no other obstacle).

- Difficulty record score: 100/100 on the first attempt, in the 95-100 band
  (`python tools/difficultycheck.py aside-fit-sweep`, 2026-09-10). One warning stands:
  `gate.measured` is false until the naive and expert timings are actually run at Stage 4.

- Leak audit: Six candidates, each closed, recorded in the difficulty record. The tree
  ships programs and no expected trace for any of them; no run index, per-part maximum, aside
  age, join candidate or aside count ships; the record stores the range a live id was carved
  (a primitive the free path needs) and never the size that was requested, so the difference
  the sliver rule creates has to be derived; the sealed model and the frozen answers live in
  `tests/seal/`, `chmod 700` before any agent code runs.

- Expert path: the ten steps in `authoring/aside-fit-sweep/difficulty.toml` under
  `plan.expert_path`.

- Originality check: Searched 2026-09-10 for the mechanism and for the slug. The parts are
  public - glibc fastbin and tcache write-ups describe deferred consolidation, allocator
  surveys describe segregated and first fit, CS107-style heap allocator assignments describe
  first-fit with coalescing and in-place realloc - and none of them describes an age-bounded
  aside list with two orders over it, placement by leftmost address inside a part, the sliver
  rule, or the flush-and-retry that persists on failure. No public page plans this task, and
  the graded object is this host's exact trace.

## Verifier contract — FROZEN 2026-09-10

- **Artifacts the agent produces.** Exactly the five files it may change:
  `/app/pool/find.py`, `/app/pool/cut.py`, `/app/pool/side.py`, `/app/pool/back.py`,
  `/app/pool/edge.py`. The verifier reads nothing else from the agent.

- **What is checked.** The verifier lays those five files over its own pristine copy of the
  tree and runs every graded program through the result inside an unprivileged worker. For
  each program the produced trace is compared line for line with the truth. All or nothing:
  every enumerated program and every nonce program must match exactly.

  Graded decisions:

  1. a request is rounded up to a multiple of 8, and one that rounds to 0 or exceeds the part
     size is refused
  2. placement is the leftmost address whose rounded bytes are all free and lie inside one part
  3. the sliver rule: leftover free bytes after the allocation, up to the end of that part,
     join the allocation when they number fewer than 16
  4. a freed range of 256 bytes or less is set aside whole - not returned to the free map, not
     joined, not available to placement or to growth
  5. a request of exactly the size of a range that is aside takes the one set aside most
     recently, before the free map is consulted
  6. more than 32 aside returns the one set aside earliest to the free map, joined with its
     free neighbours there and not with any neighbour that is aside
  7. a request neither the aside list nor the free map can serve returns everything aside to
     the map and searches once more; the list stays empty whether or not that succeeds
  8. `sweep` returns everything aside to the map
  9. a resize down releases the tail through the ordinary free path, and changes nothing when
     the tail would be under 16 bytes
  10. a resize up takes the following bytes only when they are in the free map and in the same
      part, and the sliver rule then applies at the new end
  11. a resize that cannot be answered in place places the new range before it frees the old
      one, and leaves the range alone when the placement fails
  12. `get` on a live id, `put` on an id that is not live, and `fit` on an id that is not live
      are not events

- **Tolerances.** None. Exact string equality of the whole trace.

- **Ground truth.** Enumerated programs: `tests/seal/gt.json`, frozen from the sealed model
  before the grading file was written; the grader asserts the model still reproduces it.
  Nonce programs: the sealed model `tests/seal/model.py`, written independently of the
  reference, over programs generated inside the verifier from a seed drawn after the agent's
  container is gone. `tests/seal/` is `chmod 700` before the privilege drop.

- **Execution limit.** The worker runs under a wall clock that is also the task's stated
  execution limit, so a correct allocator that cannot get through the set in time scores
  exactly as a wrong one does. The limit and the input scale are both stated in the brief.

- **Prong C tactics in the contract.** C1 both sides of every fence, in enumerated cases named
  for each; C2 no oracle ships and the shipped host is wrong; C3 the execution limit with the
  two large families; C4 all-or-nothing over enumerated corners and nonce programs.

- **Route-around guard.** Only the five `/app/pool/` files are declared artifacts, and the
  verifier overlays them onto its own pristine tree, so the op dispatch, the program reader,
  the id table, the geometry and the event printer cannot be reshaped and the trace format
  cannot be changed.

## Decisions and their reasons

- No granule map ships. An earlier draft put a flat per-granule state array in the frozen tree;
  a C-level substring search over it would have answered the fit fast enough to blunt the
  execution limit, and it would also have handed the agent the free/aside distinction as a
  ready-made field. The pool modules own every representation of arena state instead.
- The shipped allocator is a complete working engine with the naive structure - an
  address-ordered list of free ranges, scanned from the left - so it is a worked example of
  the plan that has to be replaced, not a stub. All five modules ship wrong.

## Validation status

Container evidence is from `tools/docker_trial.py`, which builds both images and runs
`tests/test.sh` for real. Two local accommodations were needed and neither changes the shipped
bundle: this sandbox's egress denies Docker Hub's blob CDN, so the base image was pulled from
`mirror.gcr.io/library/python:3.12-slim` and tagged `python:3.12-slim` locally; and it denies
`deb.debian.org`, so the verifier image was built with `DOCKER_TRIAL_NO_APT=1`, which comments out
the apt layer. That layer installs `procps` and `util-linux`; `setpriv`, `setsid`, `timeout` and
`install` are all already in the base image and `ps` is never called, so the isolation the trial
exercised is the isolation the shipped image will have. The platform builds with ordinary network
access and needs neither accommodation.

| Check | Status | Notes |
|---|---|---|
| Difficulty record in band | pass | 100/100 with the built tree measured: 304 environment lines, 5 editable files, 350 reference lines |
| Packaged and checked | pass | `package.py` built a 100-entry zip; `zipcheck.py` clean; no STATE.md, bytecode or authoring material in it |
| Reference vs sealed model | pass | 406 nonce programs, 0 differing; 30 enumerated frozen in gt.json and re-derived by the model at grade time |
| Both images build | pass | `docker_trial.py --build` |
| No answer leaked into agent image | pass | `imagecheck.py` assembles what the image would hold (19 files) and runs the shipped programs; no trace, index or answer ships |
| `docker_trial.py oracle` = 1 | pass | 33 tests passed, reward 1; re-run against the final image after the last edit |
| `docker_trial.py nop` = 0 | pass | 1 passed, 32 errors, reward 0; re-run against the final image |
| Cheats all score 0 | pass | 43 cheats. `docker_trial.py --all` returned 41/41 for the first 39 plus oracle and nop; the four added afterwards - sweep-drop, put-dead, fit-dead, part-strict - were run separately and each scored 0 |
| Correct variants score 1 | pass | ok-flat, ok-mask and ok-token each scored 1 in the two-image trial, and agree with the reference on every program on the host |
| Every cheat caught by a named layer | pass | `cheat_report.py`: 43 cheats, 0 caught by nothing. Every enumerated case is now the case named for at least one reading |
| Every wrong reading separated | pass | `readingcheck.py`: 28 semantic readings separated by their enumerated case; the 3 slow ones report `equivalent`, which is correct - they are separated by the execution limit and belong in neither the variants nor the case set |
| No graded decision has a short rule | pass | `onelinecheck.py` over `decisions.py`: no exact rule at depth <= 2 on any of the four quantities |
| `preflight.py` | pass | no errors; 19 warnings, all the module-qualified-call false positive that every retained bundle also reports |
| `solvecheck` `deadfieldcheck` `catcheck` `hintcheck` `structcheck` `extraneouscheck` `forgecheck` | pass | clean |
| `textcheck` against a passed brief | pass | no findings; burstiness 0.80 against a retained band of 0.79 to 1.11 |
| `simcheck` | known risk | the two Dockerfiles are near-identical to earlier bundles' (rule-constrained boilerplate; the retained tasks report the same against each other). `test.sh` and `reap.py` were rewritten after being flagged as literal copies and are now clear |
| `harbor check` rubric | not run | needs a provider API key, which this session does not have |

### Measured numbers behind the claims

- Execution limit 60 s for the whole graded set of 436 programs. The reference settles it in
  3.3 s; the sealed model takes 7.3 s.
- One `wide` program: reference 0.6 s. Correct and too slow: free ranges scanned from the left
  72.0 s, every part looked at in turn 29.3 s, every part's maximum re-derived on every change
  105.1 s. All three produce exactly the reference's traces.
- One `churn` program: reference 0.4 s; the scanning free map 27.2 s.
- The three correct variants on one `wide` program: ok-flat 7.5 s, ok-mask 1.3 s, ok-token 0.6 s.
- The forgery carrying the 30 frozen answers passes all 30 and fails all 80 nonce programs
  it could not have seen. In the container it reports `1 failed, 32 passed`: every enumerated
  case and the frozen-truth check pass, and only the nonce comparison rejects it.

## Stage 7 re-attack, 2026-09-10

Read the finished `instruction.md` cold, with the built tree in front of me, and asked the two
questions the manual asks.

**Is the first plan still wrong?** Yes, in two places, and neither is visible from the brief.
The plan the brief invites is a dict from id to range, one address-ordered list of free ranges
scanned from the left, a dict from size to a list for the aside list with something alongside it
for age, and the four rules applied where they are stated. Of the twelve graded decisions that
plan gets ten right. It gets the aside list wrong, because the natural shape - one list per size
plus a queue of addresses with lazy deletion - cannot tell one setting-aside from the next, and a
range set aside, taken and set aside again is then given back at the wrong turn (measured: that
reading moves 9 per cent of the population and fails `aside-again`). And it dies on the limit: the
scan takes 72 seconds on one wide program against 60 for the whole set of 436, and the index that
replaces it is not the one a first replan reaches for, because a tree keyed by the largest free
range answers the wrong address wherever a free run straddles a part boundary.

**Are the load-bearing facts still distributed?** They are stated rather than distributed, which
is what this task claims: B2, not B1. The tree is 304 lines of agent-facing Python across eleven
files, five of them editable, and the conjunction rather than the size is the difficulty. Nothing
flattened during the build: the difficulty record measures the built tree at 100/100 with the
environment, the reference and the editable count all inside the retained band.

**Did the instruction come to telegraph the method?** One clause did and was cut: an earlier draft
said the placement address "is not the same address as the start of the lowest free run that is
large enough", which names the structure that fails instead of stating the rule. The rule and the
worked example say it without naming it.

**Estimated solves, updated:** 3. Raised from 2 because the brief is complete and an expert who
gets the aside list and the index right has no other obstacle; still inside the design target.

## Cold self-attack: not run, and why

The order of work here was environment, then reference, then sealed model, then brief. By the time
the brief existed both discoveries were already in hand, so a solve by this author would have
measured memory rather than difficulty, and a self-probe reported as passed by a contaminated
author is worse than no self-probe. It is recorded as not run.

What stands in its place, all of it measured rather than asserted:

- every one of the 24 semantic wrong readings is separated by the enumerated case written for it
  (`tools/readingcheck.py`, and `authoring/aside-fit-sweep/cheat_report.py` names the case for
  each of the 39 cheats);
- the three readings that are exactly correct and too slow are separated by the limit alone, with
  the seconds recorded;
- no graded quantity is reproduced by a rule at depth two over the state the agent can read
  (`tools/onelinecheck.py` over `authoring/aside-fit-sweep/decisions.py`);
- nothing in the tree is an oracle: no expected trace ships, and the forgery that carries the
  frozen answers passes all 30 enumerated programs and fails all 80 nonce programs it could not
  have seen.

## Known risks to flag to a reviewer

- One enumerated program was extended after the first cheat sweep: `dead-put` gained a second
  request so that giving a range back twice for the same id is visible in its trace, which is what
  the `put-dead` reading needed. The extension is additive - the old expected trace is a prefix of
  the new one and no other frozen answer moved - and `build_gt.py` refused it until it was forced,
  which is the check working.
- The two Dockerfiles are close to those of earlier tasks in this repository (`tools/simcheck.py`
  reports 0.98 and 1.00 against `publish-settle-order`). They are seven and sixteen lines of
  rule-constrained boilerplate - the same base image, the same pins, the same artifact-parent
  mkdirs - and the retained tasks report the same similarity against each other. `test.sh` and
  `reap.py` were rewritten after simcheck flagged them as literal copies, and are now clear.
- The difficulty band is a stochastic gate. Nothing here can promise 1 to 7 of 8; the local
  evidence says the first plan is wrong in two places and that both are measured, and the probe
  decides.

## Open questions and next steps

Nothing is open in the bundle. What remains is external: the platform's own gates, and above all
the eight-attempt difficulty probe, which is the only thing that can decide whether the estimate
of three solves is right. If it comes back at 8, `RAISE-DIFFICULTY.md` applies and the repair is
semantic, not more cases: the first place to look is the aside list, because its two orders are
the part of the design a careful agent is most likely to get right on the first read.
