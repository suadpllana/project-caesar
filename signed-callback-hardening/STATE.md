# Task state

Working memory for this task. Assume the next session starts with no memory of this one.

## Current stage

`Stage 7 - Pre-flight and packaging` (bundle complete; gates run, see Validation status)

## Assistant's assigned role

"You are a senior application security engineer; you have spent years on request
authentication for partner and payment integrations - HMAC callback schemes, canonical request
formats, webhook receivers and the middleware in front of them."

Assigned implicitly by the contributor's choice of category (Security) and label (AppSec)
rather than in their own words. **Open item for the contributor: confirm or restate this role,
and confirm or replace `relevant_experience` in `task.toml`, which is currently a draft written
for review, not text the contributor supplied.**

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task. The application tree under `environment/app_src/` is
  authored for this task, not vendored, so the repo-based rules in `docs/ABLATION.md` and the
  upstream-diff concerns do not apply.

## Task summary

A service receives signed partner callbacks through a relay it does not control. The agent gets
the whole service: the partner client library that signs (`sdk/signer.py`), the WSGI entry point,
the routing and ingest handlers, a hand-rolled JSON parser, a key store with per-key states, and
three configuration profiles. One file is editable, `svc/auth/verify.py`, and it currently
accepts requests nobody signed. The agent must make an accepted request provably one the named
key holder signed - partner attribution, routing target and the document the handler acts on -
without narrowing what real partners and the relay already send.

## Why it is hard

The environment holds four independent weaknesses in the shipped verifier. Three of them are
textbook and a frontier agent fixes them from its prior: no floor on which headers the signature
covers, no key-state check against the live profile, no clock-skew window and no replay cache.
The fourth is the wall. `x-body-sha256` is verified against a digest taken over `json.loads`
output, which keeps the **last** occurrence of a repeated object key; the ingest handler reads
the same bytes through `svc/core/jsonx.py`, whose object parser keeps the **first**. A repeated
key placed at the front of the document leaves the signed digest byte-identical and changes what
the handler acts on.

- Expert time estimate: 7 hours
- Why a frontier agent cannot one-shot the plan: the correct plan requires knowing that the
  component that authenticates the payload and the component that consumes it disagree about how
  to read it. That fact exists nowhere in the instruction and in no single file - it is the
  difference between `svc/handlers/ingest.py` + `svc/core/jsonx.py` and `svc/auth/verify.py`,
  three files in two directories. The default plan for "harden an HMAC callback verifier" is
  complete, confident, and leaves the service forgeable.
- Tactics making that true (`docs/DIFFICULTY.md`):
  - **Prong A (poison the default plan)**: the memorized fix list for signature verification is
    exactly the set of weaknesses that are *not* decisive here. A2 applies too - the concept is
    described operationally ("the document the handler ends up working with") and never named.
  - **Prong B (withhold the correct plan)**: the load-bearing facts are distributed.
    `sdk/signer.py` defines what legitimate traffic looks like; `svc/handlers/ingest.py` names
    the parser the handler uses; `svc/core/jsonx.py` holds the first-wins behavior;
    `svc/core/canon.py` holds the canonical form the digest is taken over;
    `svc/core/cfg.py` plus `svc/conf/profiles/standard.toml` decide the key-state policy and the
    skew, with two decoy profiles present and only one live. The agent-facing tree ships with no
    comments, docstrings or documentation.
  - **Prong C (make the wrong plan fatal, and late)**: two instinctive repairs pass every
    forgery test and fail all legitimate traffic. Digesting the raw body bytes looks like the
    obvious fix and breaks every partner, because the client library serializes with
    `json.dumps` default separators while the digest is over the compact sorted form. Requiring
    that every present header be covered blocks the coverage forgeries and rejects every real
    request, because the relay adds unsigned headers. Both only surface against traffic the
    agent has to construct itself.
  - **The guard (block the route-around)**: only `/app/svc/auth/verify.py` is collected. The
    verifier composes it with a pristine copy of everything else, so the signer, the parser, the
    handler and the interface cannot be changed to suit a different plan.
- Assistant's attack on the plan: my first plan was "enforce a mandatory covered-header set,
  check key state against the profile, add a skew window, add a per-key nonce cache, use
  `compare_digest`, and digest the raw body". Four of those six are right. The fifth (raw body)
  breaks all legitimate traffic and would be caught in minutes by running the SDK. The sixth
  item is missing entirely: nothing in my first plan binds the digest to the parse the handler
  performs, and my own tests - built from SDK-generated bodies, which never repeat a key - would
  have passed. That is the definition of a plan that is wrong somewhere that matters.
- Estimated solves out of 8: **1 to 2** after the 2026-08-12 rebuild (was 3, and the probe measured it well above that). Three independent findings are now required, none of
  them visible from the file under edit, and the measured partial solutions all score 0. The
  contributor asked for at most 1 solve in a 3-attempt probe after the task was solved 2 of 3;
  note the kit's arithmetic (`docs/DIFFICULTY.md`): a true rate near 1 in 8 carries roughly a
  1-in-3 chance of scoring zero across 8 attempts and being rejected as unverifiable. The
  reference solution is a natural expert path and every fact is in the tree, so the design is
  solvable, but this is the deliberate trade the contributor asked for.
- Originality check: the underlying bug classes are individually documented (signature coverage
  gaps, JSON parser differentials, "sign what you parse"). No public write-up plans *this*
  composition in *this* codebase, which does not exist outside the bundle. Searched for
  write-ups combining HMAC callback verification with duplicate-key JSON parser differentials;
  what exists describes the bug class, not a task or a solution. Retrieval helps an agent name
  the class only after it has already noticed the disagreement, which is the hard step.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: `/app/svc/auth/verify.py`, and nothing else. The verifier image
  bakes a pristine copy of the application tree at `/app`; the harness drops the agent's file on
  top of it.
- What is checked: every case is driven through the real WSGI application at
  `/app/svc/wsgi.py`. Acceptance means HTTP 200 plus exactly one ingest ledger entry whose
  partner, target and document match what was signed. Rejection means HTTP 401 from verification
  plus no ledger entry at all.
  - 200 randomized legitimate requests from the partner client library, plus a relay-header case.
  - Five uncovered-field forgeries (`x-partner`, `x-target`, `x-body-sha256`, `x-ts`,
    `x-nonce`), 25 randomized cases each.
  - Repeated-key document rewrites at the top level and inside a nested object, plus appended
    members.
  - Byte-identical redelivery rejected; the same nonce from two different keys accepted.
  - Timestamps on both sides of the configured window, in and out.
  - Every key state the live profile excludes, and every state it allows.
  - Plain tampering: flipped signature, missing signature, unknown key id, a signature from
    another key, a rewritten cover list, a body from another request, an empty body.
- Tolerances: none. All cases are exact; the grade is all-or-nothing across 18 tests.
- Ground truth, and where it lives: there is no stored expected answer. The verifier derives its
  expectations from the service's own configuration (`accepted_key_states`, `max_skew_sec`) and
  key store, and grades observed behavior. The hardened reference implementation exists only in
  `solution/solve.sh`.

## Decisions and their reasons

- **One editable file, everything else composed from a pristine copy.** Without this the agent
  could delete `jsonx.py`, change the signer, or alter the handler, all of which convert the
  task back into an execution exercise. It also makes the artifact list a single path.
- **No reference implementation in `tests/`.** The verifier grades behavior, so any correct fix
  passes: binding the digest to `jsonx.parse`, or rejecting bodies whose two parses disagree,
  or requiring a canonical body, all work. This avoids grading against one author's spelling of
  the fix.
- **The vulnerable file already uses `hmac.compare_digest`.** Leaving the timing-safe comparison
  done removes the cheapest textbook win and pushes the agent toward the real weaknesses.
- **Three configuration profiles, one live.** `standard.toml` is what `cfg.py` loads by default;
  `permissive.toml` and `lab.toml` are realistic alternates that punish reading the wrong file.
  This is config indirection, not a trap: nothing in the tree makes a false statement.
- **Timestamp freshness uses real wall-clock time.** The tests build stamps relative to now and
  only assert on relative age, which is the behavior under test, so there is no flakiness.
- **Identifier naming is ordinary production naming.** This is an authored environment, not a
  vendored repository, so no identifier degradation was applied; the difficulty comes from the
  couplings, not from decoding names.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | `environment/Dockerfile`, ubuntu:24.04 plus python3 from apt; no pip, no network at runtime. |
| No answer leaked into agent image | pass | The image contains only `environment/app_src/`; the hardened implementation exists only in `solution/solve.sh`. Verified by listing the built image tree and grepping it for the fix. |
| `harbor run -a oracle` = 1 | pass | Run locally with docker. |
| `harbor run -a nop` = 0 | pass | The unmodified vulnerable file fails 10 of the 18 tests. |
| Cheats all score 0 | pass | Seven attempts, see `cheat/README.md`; the decisive one for difficulty is `cheat-textbook-hardening.sh`, and `cheat-kill-the-test-runner.sh` / `cheat-forge-the-reward.sh` are the platform probe's findings kept as regression cases. |
| Verifier execution isolation | pass | Probed directly in the built verifier image: as uid 65534, writing `/logs/verifier/reward.txt`, listing `/logs/verifier`, reading `/tests/test_outputs.py`, writing `/tests/test.sh` and writing the `/app` tree are all denied. |
| `preflight.py` | pass | No errors, no warnings. |
| `harbor check` rubric | not run | No model API key available in the authoring environment. Walked `docs/QUALITY-REVIEW.md` by hand instead, criterion by criterion. |

Local validation note: the machine used for authoring sits behind a TLS-intercepting egress
proxy, so the local runs used a copy of the bundle with the proxy CA added to `tests/Dockerfile`
before the `pip install` line. Nothing else differed, and the shipped bundle carries no CA
material.

## Platform verdicts and what fixed them

| Date | Gate | Verdict | Fix |
|---|---|---|---|
| 2026-08-11 | Anti-cheat robustness (blocking) | The collected artifact is code the verifier imports into a root pytest process, so a `verify.py` whose module body calls `os._exit(0)` made pytest exit 0 with zero tests executed, and `test.sh` wrote reward 1 from the exit code alone. | Execution and grading were separated. `tests/worker.py` is now the only process that imports the application, launched by the harness through `setpriv --reuid 65534 --regid 65534 --clear-groups --no-new-privs`; `tests/harness.py` imports only modules the agent cannot supply. The reward comes from `tests/grade.py`, which validates the CTRF report against the pinned id list in `tests/expected_tests.txt`. Kept as `cheat/cheat-kill-the-test-runner.sh`. |
| 2026-08-12 | Easiness probe (blocking) | Solved 2 of 3 by Opus 5. The probe trajectory shows the solver identifying the parser differential in its first analysis pass, before writing any code. | Two causes, both fixed. (1) The shipped `verify.py` displayed the bug: `json.loads` sat in the 33-line file under edit while the handler two directories away called `jsonx.parse`, a one-glance inconsistency. The verifier now ships textbook-complete, the duplicate-key policy is a parameter of one shared parser (`jsonx.parse(..., keep=...)`), and the consuming call lives in a config-selected pipeline stage. (2) The instruction enumerated exactly the fields that had to be covered, which handed over the coverage fix; it now states the property once, generally. Two further independent gaps were added in the consumers (the overlay stage's `x-doc-*` merge, and the key-to-partner entitlement in the key store), so finding the parse disagreement alone is no longer sufficient - measured: `cheat/cheat-parser-differential-only.sh`, which reproduces the probe's winning answer, now scores 0. |
| 2026-08-11 | Verifier execution isolation (blocking) | No privilege drop, `/logs/verifier` never restricted before agent code ran, reward derived from pytest's exit status; a daemonized child overwriting `reward.txt` was equally available. | `test.sh` now makes `/logs/verifier` root-owned mode 700 and `/tests` mode 700 before anything runs, copies the worker to `/run/worker.py` as the only file the unprivileged user needs, runs `pkill -u 65534` after the suite, and writes `reward.txt` only after grading. `tests/Dockerfile` tightens ownership at build time. Kept as `cheat/cheat-forge-the-reward.sh`. |

Note on D2: neither change touched the verifier contract. The 18 tests, their assertions and
what counts as correct for the agent are identical; only the isolation around executing the
deliverable and the derivation of the reward changed, and both moved in the strict direction.

## Open questions and next steps

1. `instruction.md` was drafted by the assistant from the task design rather than dictated by
   the contributor, because the contributor asked for a complete bundle. Before submission the
   contributor should read it end to end, reword it in their own voice, and confirm every claim
   about the environment. This is the one part of the bundle that must be theirs (D1).
2. Same for `relevant_experience` and `author_name` in `task.toml`.
3. `harbor check -m <model>` should be run once an API key is available.
