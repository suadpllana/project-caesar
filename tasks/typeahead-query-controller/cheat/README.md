# Cheating attempts considered

Each of these was tried against the verifier while building the task. None
is executed by the pipeline; they are recorded so the defences are explicit.

## 0. Execute code via the build config (vite.config.ts RCE)

The strongest attack: Vite evaluates `vite.config.ts` as code when the dev
server starts. If the verifier served the agent's own config, an agent could
inject a plugin that runs arbitrary code inside the verifier and forges
`reward.txt`. See `cheat/vite_config_rce.ts`.

**Rejected by three independent layers**, any one sufficient:

1. `test.sh` never serves the agent's `vite.config.ts`, `tsconfig.json` or
   `package.json` -- it overlays the pristine copies baked into the verifier
   image and deletes any config-shaped files dropped into `src/`. The agent's
   config is never evaluated.
2. The dev server runs as the unprivileged `verifier` user (`setpriv`), and
   `/logs/verifier` is root-owned mode 0700. Code that does execute cannot
   read, write or replace the reward file (EACCES).
3. `run_conformance.js` hashes `vite.config.ts`, `tsconfig.json` and
   `package.json` against pristine copies before any scenario runs; a mismatch
   fails `test_protected_files_unmodified` with zero scenarios executed.

Additionally, all agent-derived processes are killed and the reward is
re-asserted to `0` before grading, so a self-daemonizing plugin cannot win a
late race against the verdict.

## 1. Rewrite the transport so races cannot happen

The most direct exploit: edit `src/transport.ts` so `settleIgnoringAbort`
behaves like `settle`, or so aborted requests never resolve. Every ordering
scenario then passes with the original buggy controller.

**Rejected by:** the driver hashes `src/types.ts`, `src/transport.ts` and
`src/main.ts` against pristine copies baked into the verifier image before
any scenario runs, and `test_protected_files_unmodified` fails the whole run
on a mismatch. The pristine copies live in the verifier image, which the
agent never sees and cannot write to.

## 2. Fake the harness

Replace `src/main.ts` so `window.__harness.controller` is a stub that
returns whatever state the scenarios want, ignoring the real controller.

**Rejected by:** same integrity check -- `main.ts` is protected.

## 3. Neutralise the scenarios

Delete scenarios, rename their ids, or make `run_conformance.js` report
`pass: true`.

**Rejected by:** the tests are baked into the verifier image with
`COPY . /tests/` and are not reachable from the environment container at all.
`REQUIRED_IDS` in `test_conformance.py` is asserted independently, so a
report that omits or renames a scenario fails `test_all_scenarios_ran`.

## 4. Write the reward file directly

Have the agent create `/logs/verifier/reward.txt` containing `1`.

**Rejected by:** the verifier runs in a separate container after the
environment is torn down, and `test.sh` unconditionally overwrites the file
with `0` before grading. Only a clean pytest exit rewrites it to `1`.

## 5. Suppress everything

Notice that several scenarios check that bad states are never emitted, and
"solve" them by making the controller emit nothing at all, or never leave
`loading`.

**Rejected by:** `r4b`, `r5`, `r7b` and `r8` require positive outcomes --
the authoritative result must arrive, a cached query must be served with the
right items, a real transport failure must surface as `status: "error"`, and
a typing burst must settle on the final query. A controller that stays silent
fails all four. `r7_emit_snapshot` additionally requires that all four
subscribers are notified exactly once.

## 6. Hardcode the fixtures

Detect the specific query strings used by the tests (`"ca"`, `"car"`,
`"carbon"`, …) and return canned results.

**Partially open, and deliberately so.** The scenarios use several disjoint
query families and assert on transport call counts and provisional flags as
well as payloads, so a lookup table has to reproduce the caching and
continuity *behaviour* rather than just the strings -- at which point it is
doing the real work in a fragile way. `see cheat/hardcode_attempt.ts` for how
far this gets: it fails `r8` because the burst asserts the payload came from
the transport for the final query.
