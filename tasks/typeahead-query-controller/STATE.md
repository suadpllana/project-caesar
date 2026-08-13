# Task state

Working memory for `typeahead-query-controller`. Written retroactively on 2026-08-13, after
the bundle had already been through the pipeline once, so the early-stage sections record
what the bundle shows rather than a live authoring session.

## Current stage

`Post-rejection repair`. The bundle cleared all nine automated gates on 2026-08-05 and was
then **rejected by human review** for instruction quality. The repair is described under
"Human review rejection" below.

## Assistant's assigned role

Senior frontend engineer. Production UI in React, Vue and plain TypeScript; the working
material is component state that has to stay correct while data is still arriving, and
Playwright/Cypress coverage for async UI behaviour.

## Source repository (repo-based tasks only)

None - idea-based task. The simulator is written from scratch: a controller, a
driver-settled test transport, and a browser harness. Nothing is vendored, so there is no
public diff and no public fix.

## Task summary

A type-ahead search panel fires a request per keystroke and paints whatever arrives last, so
a slow reply for `c` can overwrite the reply for `car`. The agent rewrites
`/app/src/controller.ts` so that display always matches the current query, superseded
requests are silent, repeated queries are coalesced and cached, and the pane keeps showing
filtered rows from the nearest known prefix instead of blanking. Twelve conformance
scenarios drive the agent's real module graph in Chromium through a transport that settles
only when the driver says so.

## Why it is hard

The textbook fix - a monotonic request token, drop replies whose token is stale - is the
first thing written and it is necessary but not sufficient. Three requirements pull against
it:

- Cancellation is genuinely lossy. `settleIgnoringAbort` commits a reply before the abort is
  observed, so any implementation that leans on abort rather than on identity checked at
  write time corrupts the panel, intermittently, only inside the lost-race window.
- The continuity invariant pulls directly against the token check. Identity wants to suppress
  every write that is not the newest authoritative response; continuity requires emitting a
  displayable result for a query that has no response at all. Reconciling them means
  separating "authoritative" from "displayable" in the state model, which is a design change
  rather than a patch.
- Serving a revisited query from cache must also invalidate the in-flight token, or a late
  reply overwrites the cached answer on backspace.

- Expert time estimate: 4 hours
- Why a frontier agent cannot one-shot the plan: the first plan is "add a request token and
  ignore stale responses, plus an AbortController". That plan gets the ordering scenarios
  right and still fails the continuity and cache-invalidation scenarios, because it has no
  notion of a state that is displayable without being authoritative.
- Tactics making that true: A1 poisons the default plan; B1 withholds it; C1 makes the wrong
  plan fail late.
  - Prong A1: the retrieved answer for "stale search response overwrites newer" is the
    token/abort fix, which is precisely the insufficient one here. `cheat/hardcode_attempt.ts`
    records an attempt that fakes outcomes instead, and scores 0.
  - Prong B1: the instruction states the required behaviour (rows stay up, marked
    provisional) without naming prefix derivation, cache keying or the token mechanism.
  - Prong C1: the lossy-cancellation window and the late-overwrite-on-backspace path both
    fail only in specific interleavings the agent must construct deliberately via
    `window.__harness`; neither shows up in casual manual testing.
- Assistant's attack on the plan: the first plan is "monotonic token on each search, drop settled replies whose token is stale, abort the previous request, swallow AbortError", and it is wrong in two places that only surface late.
  That plan is right about ordering and wrong in
  two places that only surface later. It has no state that is displayable-but-not-
  authoritative, so the moment a refinement is outstanding it must either blank the pane or
  paint a stale payload - both fail. And serving a revisited query from the cache without
  bumping the token leaves the outstanding reply live, so backspacing to a settled query
  gets overwritten a tick later by the response it was supposed to supersede.
- Estimated solves out of 8: 2. Measured while designing: the shipped code fails 7 of 12
  scenarios, and a strong "obvious" fix carrying request tokens, AbortError suppression,
  in-flight coalescing and a dispose latch still fails 2 of 12.
- Leak audit: the environment carried a `README.md` product spec and prose docstrings in all
  four `src` files. **Both were removed on 2026-08-13** (see below); the spec now lives in
  `instruction.md` where it belongs, and the sources carry no explanatory comments.
- Expert path: reproduce out-of-order arrival through the harness; add a monotonic token
  checked at write time rather than relying on abort; add a query-keyed cache written only
  from authoritative responses; derive the provisional view from the longest cached prefix
  of the current query; bump the token when serving from cache; latch `dispose` before
  aborting; iterate a snapshot of the subscriber set in `emit`.
- Originality check: the stale-response race is well known; the task's difficulty is in the
  interaction with continuity and caching, which is not a documented recipe.

## Verifier contract - FROZEN

- Artifacts the agent produces: `/app/src`, `/app/public`, `/app/tsconfig.json`,
  `/app/vite.config.ts`, `/app/package.json`. Only `src/controller.ts` needs to change.
- What is checked: 13 conformance scenarios, all-or-nothing, asserted on the full emission
  history rather than final state, so a stale payload that appears for one frame and is
  later corrected still fails. Scenario ids are asserted independently in
  `tests/test_conformance.py::REQUIRED_IDS`, so deleting or renaming a scenario fails.
- Tolerances: none; every assertion is exact.
- Ground truth: there is no re-implementation to grade against. The verifier drives the
  agent's real module graph in Chromium. `src/types.ts`, `src/transport.ts`, `src/main.ts`,
  `vite.config.ts`, `tsconfig.json` and `package.json` are hashed against
  `tests/pristine/` before any scenario runs.

## Human review rejection, 2026-08-13

Rejected after passing all nine automated gates. Reviewer's note:

> instruction low quality. Something like: "every subscriber present when the update begins
> receives it, even if a peer unsubscribes it during that dispatch." Then add a scenario
> that separates self-unsubscribe from peer-unsubscribe so the distinction is testable, not
> inferred.

The reviewer was right, and the defect is the `turn-seam-alignment` failure mode in a new
place: **a graded rule with more than one correct reading, only one of which was graded.**

The old text said only that a subscriber unsubscribing during notification "must not stop
its peers from receiving that same update". `r7_emit_snapshot` has listener 0 unsubscribe
*listeners 1 and 2*, then requires that they are still called. But a solver who reads "must
not stop its peers" as "must not skip over anyone" writes

```ts
for (const fn of [...subscribers]) if (subscribers.has(fn)) fn(state);
```

which takes the snapshot, skips nobody it still considers subscribed, satisfies every stated
word - and fails `r7` with `hits=1,0,0,1`. Nothing in the instruction, the README or
`types.ts` (which said only "Returns an unsubscribe function") distinguished the two
readings, and no scenario exercised self-unsubscribe, so the distinction could not be
settled by experiment either.

Measured on 2026-08-13 against three `emit` implementations:

| emit implementation | r7 (peer-unsubscribe) | r7c (self-unsubscribe) |
|---|---|---|
| snapshot, no liveness re-check (reference) | pass | pass |
| snapshot **+ liveness re-check** | **fail** `1,0,0,1` | pass |
| live `Set` iteration (shipped bug) | fail | **fail** `late=2` |

The middle row is the reviewer's point exactly. The bottom row shows `r7c` is not dead
weight - it independently catches a listener added mid-dispatch being wrongly pulled into
the update already in flight.

Fixes applied:

- `instruction.md` now states the dispatch contract explicitly: the audience is fixed when
  the update begins, a peer unsubscribed mid-dispatch still receives it, a listener that
  unsubscribes itself still receives the update it is inside, removals take effect from the
  next dispatch, and a listener that subscribes mid-dispatch starts at the following update.
- New scenario `r7c_self_unsubscribe_during_delivery` isolates self-unsubscribe and the
  subscribe-during-dispatch mirror, added to `REQUIRED_IDS`. Scenario count 12 -> 13.

## Other repairs made in the same pass, 2026-08-13

`scripts/preflight.py` (kit v1.9.1) reported 9 errors against this bundle; it predates
those rules and was submitted without a local preflight run. All are now fixed:

- `environment/app/README.md` **deleted**. Documentation is banned outright in the agent
  environment, and this file was also a leak surface: it restated the whole product spec.
  Its only unique content - the `window.__harness` API and `settleIgnoringAbort` semantics -
  moved into `instruction.md`. `environment/Dockerfile` no longer copies it.
- Prose comments and docstrings stripped from all four `environment/app/src/*.ts` files.
  `tests/pristine/` resynced to match, since three of them are hash-checked. No identifier
  was renamed and no API surface changed; `tsc --noEmit` is clean.
- `instruction.md`: the two U+2192 arrows replaced with ASCII.
- `task.toml`: tag `frontend` restated the subcategory (a blocking quality-review criterion);
  tags are now six technique names.
- `tests/test.sh`: the localhost readiness poll used `curl`, which preflight treats as a
  trial-time network dependency. Replaced with a `node -e` http probe. Substantively this
  was a false positive - it polls the verifier's own dev server - but the node probe removes
  the dependency entirely.

Two warnings remain and are both expected for this task's shape: `tests/test_outputs.py not
found` (the grader is `tests/test_conformance.py`) and "could not confirm it writes both 1
and 0" (`test.sh` writes the reward through a `finish()` helper the checker cannot trace).

## Decisions and their reasons

- The dispatch contract is **stated and graded on one reading**, not widened to a range. This
  is the opposite call to `turn-seam-alignment`'s character-count window, and deliberately:
  there the honest answer really was a range of equally correct optimisations, whereas here
  the two readings are genuinely different observable behaviours and the contract has to pick
  one. The rule is cheap to state precisely, so the fix is to state it.
- `r7` was **kept as well as** `r7c`. `r7` alone under-specified; `r7c` alone would miss the
  peer case. Together each is separately diagnostic - see the table above.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | not run | docker unavailable in this session (`docker info` fails) |
| No answer leaked into agent image | improved, not re-verified | README and all docstrings removed; image not rebuilt |
| preflight.py | clean | 0 errors, 2 expected warnings |
| Reference passes r7 + r7c | **verified** | esbuild + node, outside the container |
| Discrimination of r7/r7c | **verified** | three emit variants, table above |
| Full 13-scenario run in container | **NOT RUN** | needs docker + Playwright image |
| Cheats score 0 | not re-run | unchanged by this pass |
| `tsc --noEmit` on environment | clean | only a `vite` module error from absent node_modules |

**The gap that matters for the next session:** the full conformance suite has not been run
in the real verifier image since these edits. The reference was verified against the new
scenario outside the container, and the pristine hashes were resynced by copy-and-diff, but
`test.sh` end to end (Vite build, Chromium, all 13 scenarios, cheats at 0) still needs a
docker host.
