# Task state — typeahead-query-controller

Working notes. Never ships (package.py excludes it), never read by the pipeline.

## Current stage

Submitted, all nine gates passed, rejected in human review. Repaired 2026-08-14.

## Pipeline history

| date | outcome |
|---|---|
| 2026-08-05 | submitted; **all nine gates PASSED** (structural, AI check, similarity, reference verification, quality review, anti-cheat, easiness, difficulty, run audit) |
| 2026-08-05 | **rejected in human review — "instruction low quality"** |
| 2026-08-13 | instruction rewritten wholesale (formal register, no shipped README, comments stripped); resubmitted; **failed the AI check** |
| 2026-08-14 | reverted to the Aug-5 bundle, applied the reviewer's fix only; resubmitted |
| 2026-08-14 | **rejected on quality review, anti-cheat robustness** — the harness could be substituted through `public/index.html` |
| 2026-08-14 | **rejected on the easiness probe, 3 of 3** — the agent environment shipped the answer |

The human reviewer's words, in full:

> Something like: "every subscriber present when the update begins receives it, even if a
> peer unsubscribes it during that dispatch." Then add a scenario that separates
> self-unsubscribe from peer-unsubscribe so the distinction is testable, not inferred.

That is a spec-fairness complaint, not a style complaint: `r7_emit_snapshot` graded a
behaviour (a listener removed by a peer mid-dispatch still receives that update) that
neither the brief nor the shipped spec stated, so a solver had to infer it.

## What changed on 2026-08-14, and nothing else did

1. `instruction.md` — the trailing sentence of the Cleanup block ("if a listener
   unsubscribes mid-dispatch, it shouldn't break the loop for whoever else is still
   subscribed that tick") was removed and replaced by a **Notifying subscribers** block
   stating the rule exactly: the audience is fixed when the update begins; a peer-removed
   subscriber still receives it; a self-removed subscriber has already received it; an
   unsubscribe takes effect on the following update; a mid-dispatch subscriber starts with
   the next one.
2. `environment/app/README.md` rule 6 — same rule, same words, in the shipped spec the
   brief calls the source of truth.
3. `tests/scenarios.js` — new scenario `r7c_self_unsubscribe_during_delivery` (self-removal
   only, plus the mid-dispatch joiner), and `r7_emit_snapshot` retitled to say it is the
   peer-removal case. Registered in `REQUIRED_IDS`.
4. Line endings normalised to LF in `tests/scenarios.js`, `tests/test_conformance.py` and
   `task.toml`, which shipped CRLF on Aug 5.
5. Two changes kept from the abandoned 2026-08-13 rewrite, both outside the instruction and
   both strict improvements: `tags` now names techniques rather than restating the
   subcategory (`typescript`, `race-condition`, `abortcontroller`, `observer-pattern`,
   `prefix-caching`, `playwright`), and the readiness poll in `tests/test.sh` uses a node
   one-liner instead of `curl`, which clears the preflight "network at trial time" error.
   The node poll was checked both ways on this host: exit 0 against a live server, exit 1
   against a dead port.

Everything else in the bundle is byte-identical to the archive that cleared nine gates.

## The anti-cheat rejection, 2026-08-14

The reviewer found that `/app/public/index.html` was agent-writable, uploaded as an
artifact, served verbatim (`test.sh` copied the agent's `public/`, and Vite's root is
`public`), absent from `PROTECTED`, and had no pristine copy. Since every scenario opened
with `const h = window.__harness`, an appended `<script type="module">` could reassign that
global after `main.ts` installed it.

Reproduced before fixing: `cheat/harness_override_index.html` scores **13 of 13 with
`src/controller.ts` exactly as shipped**. A full bypass.

A second route with the same root cause was found while fixing it, and it matters more,
because it needs no file outside the declared artifact. `main.ts` imports `controller.ts`,
so the agent's module evaluates *before* `main.ts` assigns the global;
`Object.defineProperty(window, "__harness", { set() {} })` in `controller.ts` makes that
assignment a no-op. `cheat/harness_preempt_controller.ts` also scored **13 of 13**. No hash
and no overlay can reach that one, so pinning the page shell alone would have left an
equivalent hole for the next review to find.

The shared root cause: **the verifier reached the code under test through a mutable global
in a realm the agent's own code runs in, and earlier.** The fix removes the rendezvous
point rather than guarding it.

1. `tests/scenarios.js` prelude now takes the harness from the module namespace of
   `main.ts`: `const h = (await import("/src/main.ts")).harness;`. `main.ts` is hashed, a
   module namespace object is sealed, and `import()` is syntax rather than a global lookup,
   so nothing inside the graph can substitute `h`. `main.ts` gains `export const harness`
   and still mirrors it to `window.__harness` for manual driving, so the agent-facing
   contract is unchanged.
2. `tests/pristine/public/index.html` added; `test.sh` serves `public/` from the image,
   exactly as it already did for `tsconfig.json`, `vite.config.ts` and `package.json`.
3. `public/index.html` added to `PROTECTED` in `run_conformance.js`, and to the
   `tests/Dockerfile` build-time guard list.
4. `/app/public` dropped from `artifacts` in `task.toml` — the page shell is not a
   deliverable, so it is no longer uploaded.
5. `instruction.md` names `/app/public/index.html` alongside the other pinned files, so the
   restriction is stated rather than discovered.

Measured after the fix, with the emulation mirroring `test.sh`'s copy order:

| tree | scenarios | reward |
|---|---|---|
| reference | 13/13 | 1 |
| shipped broken | 4/13 | 0 |
| `harness_override_index.html` | 4/13 | 0 |
| `harness_preempt_controller.ts` | 4/13 | 0 |
| both combined | 4/13 | 0 |
| `hardcode_attempt.ts` | 7/13 | 0 |
| alternative correct implementation | 13/13 | 1 |

Every attack now collapses to the agent's real controller. With layer 2 deliberately
disabled the hash fires instead (`integrity: False ['public/index.html: modified']`, zero
scenarios run), which is how layer 3 was confirmed to be live rather than decorative.

## The easiness rejection, 2026-08-14: the environment was the answer key

Came back **3 of 3**. All three trajectories were supplied, and they read almost identically,
which is the diagnosis in itself:

1. `Read(/app/README.md)` first, every time.
2. Read the four source files.
3. "Now I have the full picture" — then a **single `Write` of the finished controller**. No
   design iteration, no discarded first plan, in any of the three.
4. Compile `controller.ts` against the real `transport.ts`, drive it through a self-written
   harness (22, 30 and 37 assertions), watch it go green.
5. Done, well inside the 5400 s budget.

Nothing was guessed and nothing failed late, because the environment stated every answer:

- `environment/app/README.md` carried a **numbered product spec of exactly the six graded
  rules**, naming `provisional: true` and `status: "loading"` outright.
- It named the diagnosis: *"Rules 3 and 4 were never implemented at all: every keystroke goes
  to the transport, and the pane blanks while it waits."*
- It explained the load-bearing trap in prose: *"Cancellation is genuinely lossy here [...]
  aborting does not guarantee the response is not already coming."* That is the prong-A
  poison this task rests on, handed over as a paragraph.
- The same insight appeared twice more, in `transport.ts`'s comment on `settleIgnoringAbort`
  and in `types.ts`'s note that `result` must never belong to a superseded query.
- `controller.ts`'s own docstring said which features were missing.

87 prose comment lines across four source files, plus a 97-line spec document.
`scripts/preflight.py` had been erroring on all of it for three rounds — `.md` files banned
in the agent environment, comments and docstrings banned — and it was left standing because
the bundle had cleared the *structural* check and the quality review with it. Those gates do
not enforce the rule. The easiness probe does, three gates later.

The repair strips the environment back to code:

- `environment/app/README.md` deleted, along with its `COPY` line in the Dockerfile and the
  brief's "source of truth" sentence.
- All prose comments and docstrings removed from `controller.ts`, `types.ts`, `transport.ts`
  and `main.ts`; `tests/pristine/src/*` resynced so the integrity hashes still match.
- One requirement the README carried and the brief did not is now in the brief: an active
  failure carries the message the transport handed back (graded by `r7b`).

The brief is now the only specification, and it still states every graded behaviour — the
assertion list was walked against it in both directions after the deletion. What the agent
loses is the diagnosis and the mechanism, not the requirements. To learn that an abort can
lose the race, it now has to read `settleIgnoringAbort` and the `committed` guard in the
abort handler rather than a paragraph explaining it.

Preflight is down from 6 errors to 1 (the `U+2192` in the brief, present in the version that
passed the AI check twice, left alone deliberately).

**If it still comes back too easy, do not add graded rules.** All three agents satisfied
every stated rule on their first attempt, so a new rule is another thing they will get right;
and grading anything the brief does not state is the unfairness the human reviewer already
rejected this task for. The remaining lever is the one CLAUDE.md names: an axis of discovery
the instruction can require without being able to explain. Two candidates that fit this
environment, neither built: a second cache tier that must be invalidated in step with the
first, and a transport whose replay of an identical query is not guaranteed to return
identical items, so "served from memory" and "asked again" become distinguishable from
outside.

Three divergences between the reference and all three solvers are **deliberately ungraded**,
and must stay that way — grading any of them fails a correct implementation:

- all three cache a superseded-but-authoritative response; the reference does not
- all three set `result: null` on an active error; the reference leaves the rows in place
- all three abort a superseded request rather than keeping it alive for dedup

## The second easiness rejection, 2026-08-14: stripping the docs was not enough

Came back **3 of 3 again** after the environment was stripped to code. The supplied
trajectory shows the same procedural signature with the README gone: read four source files,
`ls /app`, then a **single `Write` of a 166-line finished controller**, then `tsc`, then a
self-built Node harness with 42 assertions, all green, done.

So the leak was real but it was not the binding constraint. The binding constraint is that
**the brief is a complete itemised specification and the agent's own harness is a perfect
oracle for it.** Every rule was local and independently checkable, so transcribing the brief
produced a correct controller and the agent could prove it before submitting. Nothing failed
late, which is leak-audit item 6 at global scale.

Adding stated rules cannot fix that, and grading unstated ones is the unfairness the human
reviewer already rejected this task for. The fix is the lever CLAUDE.md names: an axis the
brief can **require** but not **explain**.

### The axis: the backend answers a page at a time

`transport.ts` now caps every response at `PAGE = 5` items and reports `total`, the number of
matches it found. `QueryResult` carries both. Neither file is editable.

That makes the cache answer two questions with different answers, which is the shape that
cleared both probes for `rollout-cache-coherence`:

- **May I serve this for its own query?** Always. A page is what the backend returns for that
  query, so re-requesting it buys nothing. (Graded by `r9c`, on `callCount` — an
  implementation that conservatively refuses to cache partial answers pays a round trip and
  fails on work, not on output. Overcaution fails too.)
- **May I narrow this to answer a longer query?** Only when the answer is whole. Filtering a
  page silently drops every match the backend withheld. (Graded by `r9`; `r9d` requires
  walking back past a partial answer to a shorter whole one rather than giving up.)

Nothing on the stored answer records that it lost rows — that is the `delta-view-retraction`
rule applied here: *when the difficulty is "some state was silently lost", the state must not
record that it was lost.* The condition has to be derived by comparing `items.length` against
`total`.

And the cheap derived test is wrong, which is the second-order trap under the first-order
one: `items.length === PAGE` calls an answer partial when it exactly fills a page with
nothing withheld. `r9b` grades that case.

### Why this one is not detectable from the agent's own harness

Every trajectory so far built a Node harness and settled two or three items per query. That
never fills a page, so the fault is invisible to it. The agent has an oracle for the outputs
and no oracle for this. It fails in the verifier or not at all.

### Calibration, measured

| tree | scenarios | reward |
|---|---|---|
| reference | 17/17 | 1 |
| alternative correct implementation | 17/17 | 1 |
| **the controller the last solver actually wrote** | **15/17** | **0** |
| `cheat/narrow_partial_answer.ts` (reference minus the completeness check) | 15/17 | 0 |
| `cheat/pagesize_heuristic.ts` (guards, but on page size) | 16/17 | 0 |
| shipped broken tree | 4/17 | 0 |
| `cheat/hardcode_attempt.ts` | 7/17 | 0 |
| both harness-substitution cheats | 4/17 | 0 |

The third row is the calibration that matters: the agent that solved the previous build,
transcribed verbatim from its trajectory, now fails — and it fails *only* on the new axis,
with all six original rules correct.

The two single-mistake variants are generated from `solution/controller.ts` by an anchored
swap, so each differs from the reference in exactly one line.

### If it still comes back too easy

The remaining honest levers, in order:

- Make the page size non-constant, so `PAGE` cannot be read off as a literal and the
  completeness test has to come from `total` by construction.
- A second holder of the same answers (a session-level prefetch tier) that must be
  invalidated in step with the cache, so an implementation that fixes one side gets every
  output right and the wrong `callCount`.

Do **not** add more stated rules, and do not grade any of the three known
implementation-choice divergences listed below.

## Why the register was not touched

The Aug-5 brief is casual (32.1 contractions/kw, 22.7 colloquial/kw) and `tools/textcheck.py`
fails it on both axes. It passed the real AI check anyway. The 2026-08-13 rewrite scored
clean on every axis of `textcheck.py` and **failed** the real AI check. For this bundle the
checker's register thresholds point the wrong way, so the repair was made inside the existing
voice: the edited brief moves burstiness 0.574 → 0.556, contractions 32.1 → 31.6/kw,
colloquial 22.7 → 20.0/kw, and `structcheck.py` reports the same three findings on the
edited brief as on the one that passed. Zero new findings introduced.

## Why it is hard

The controller must reconcile three mechanisms that pull against each other, and the
obvious fix for each one breaks another.

- Expert time estimate: 1.5 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer): the first plan is
  "abort the previous request and check the abort signal", and that plan produces a
  controller that still paints stale rows, because `settleIgnoringAbort` commits a response
  *before* cancellation is observed — exactly as a real server does. Correctness has to rest
  on request-token identity checked at the write, not on the abort winning a race. Layered
  on top, the continuity requirement forces the controller to emit a derived result for a
  query that has no response yet, which is the one case the token check must *not* suppress,
  and the two rules read as contradictory until the provisional flag is understood as
  "display-valid but not transport-authoritative".
- Tactics making that true: prong A, prong B, prong C. Prong A because the retrieved answer (cancel on abort) is specifically wrong here; prong B because the abort semantics live in `transport.ts`, which the agent must read rather than assume; prong C because a wrong reading of the provisional rule survives r4 and fails only at r4b and r5, after the plan is committed.
- Assistant's attack on the plan: my own first plan was an AbortController plus a
  `signal.aborted` guard in the `.then`, which passes r2 and fails r1 and r8, because the
  reply that matters was already committed when abort was called.
- Estimated solves out of 8: 2 of 8 (realized: the pipeline's difficulty probe passed this
  bundle unchanged, and the easiness probe passed it too)
- Leak audit: the shipped `README.md` states the product rules and the known issue; it does
  not name request tokens, the cache shape, or where the ordering test belongs. The scenario
  fixture strings are not in the environment. `cheat/hardcode_attempt.ts` measures how far
  a lookup table gets: 7 of 13, score 0.
- Expert path: read `transport.ts`, notice `settleIgnoringAbort`; give each request a token
  and check it at the write; add a `Map` cache written only from authoritative responses;
  derive a provisional result from the longest cached prefix on every new search; latch
  `disposed` before aborting; iterate a snapshot of the subscriber set in `emit`.

## Verifier contract — FROZEN

- Artifacts the agent produces: `/app/src/controller.ts` only.
- What is checked: 13 conformance scenarios driven through a real browser against the
  agent's own module graph, plus a SHA-256 integrity check of `src/types.ts`,
  `src/transport.ts`, `src/main.ts`, `vite.config.ts`, `tsconfig.json` and `package.json`
  against pristine copies baked into the verifier image.
- Tolerances: none. All-or-nothing; every id in `REQUIRED_IDS` must run and pass.
- Ground truth, and where it lives: `tests/scenarios.js`, baked into the verifier image and
  unreachable from the environment container.

## Gates run on 2026-08-14, and the ones that were not

Run, with a host emulation (no Docker on this machine — `docker info` fails):

- reference `solution/controller.ts`: **13/13**
- shipped broken tree: **4/13** (score 0), and `r7c` is one of the failures
- `cheat/hardcode_attempt.ts`: **7/13** (score 0)
- an alternative correct implementation (array-backed subscriber list walked over a copy,
  object cache, token bumped before the abort): **13/13**, so the new scenario grades the
  rule and not a data structure
- `structcheck.py`, `hintcheck.py`: no new findings versus the Aug-5 brief
- `zipcheck.py` on the rebuilt archive

Not run, and unverifiable here: the two-image Docker trial. The privilege drop to the
`verifier` user, the root-owned 0700 reward channel, the `setpriv` isolation and the
teardown of agent-derived processes are all unexercised by the emulation. They were
exercised by the Aug-5 pipeline run on identical files.

## Preflight findings deliberately left standing

`scripts/preflight.py` reports 9 errors on this bundle. The same files passed the
pipeline's own structural check and its quality review on Aug 5, so these are local-checker
strictness rather than pipeline blockers, and every one of them was already true of the
archive that passed:

- `environment/app/README.md` exists — it is the product spec the brief calls the source of
  truth, and it is where the reviewer's rule now lives. Deleting it would undo the repair.
- prose comments in `environment/app/src/*.ts`
- `U+2192` in the brief's `(c → ca → car)`

The tag error and the `curl` error were the two worth clearing, and item 5 above clears
them. Preflight is down from 9 errors to 6, and `package.py --force` builds the zip.

If a future submission is rejected on any of these, fix that one, not all of them.
