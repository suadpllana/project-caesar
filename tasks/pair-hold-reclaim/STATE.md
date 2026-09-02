# Task state

Working memory for this task. Reconstructed on 2026-09-02 from task.toml, the tree and the
pipeline's rejection notice, because the task was authored outside this repo and arrived as a
zip - STATE.md never ships in a bundle, so there was none to recover. Nothing here is
archaeology from git; where a fact was not recoverable it says so.

## Current stage

`Stage 8 - resubmission`. Submitted 2026-09-02 and rejected by the **bundle structure check**
before any of the nine gates ran. One blocking error, ARTIFACT-PARENT-NOT-CREATED, plus the
informational cheat-dir warning that every bundle here gets. Fixed; see Decisions below.

## Assistant's assigned role

Runtime and storage-engine engineer, per task.toml `relevant_experience`: someone who has
debugged conditional-retention lifetime bugs in a production cache.

## Source repository (repo-based tasks only)

- Repo URL: none - idea-based task, seeded by a conditional-retention cache bug described in
  task.toml `relevant_experience`. Nothing is vendored.

## Task summary

The tree is a working object store whose reclamation pass is written as a pipeline of phases -
mark once, empty the watches marking condemned, run the cleanups it found, let go of the rest.
The agent rewrites the pass across four declared artifacts under /app/core so that a completed
pass leaves nothing in the store out of reach, and nothing in reach gone. Graded on the ordered
ledger and the final store, over 31 enumerated streams and 300 generated inside the verifier
from a nonce made after the agent has finished.

## Why it is hard

Reach is a least fixed point, not a traversal, and a pass has to settle rather than run. The two
are linked through the choosing rule: a cleanup may not run while anything else with a cleanup
still pending can reach its cell, and the natural implementation asks that of the pending cells
alone - right for every one-key entry, wrong for a two-key entry with one key held from outside
the group being torn down.

- Expert time estimate: 8 hours
- Why a frontier agent cannot one-shot the plan (the strategic answer - required): the phased collector it reconstructs from its prior is correct on most streams, and both discoveries the task is built on break that shape rather than extending it, so the first correct-looking implementation is wrong on chained streams with no crash to point at it.
- Tactics making that true: prong A, since the textbook tracing-collector answer is specifically wrong here, and prong C, since every wrong reading still prints a plausible ledger and fails only in the verifier.
- Assistant's attack on the plan (its first plan, and where that plan is wrong): the first plan sweeps both entry tables once and closes over the links again, then recomputes a single time after the cleanups have run; it is wrong the first time one cleanup drops the last name holding a cell whose own cleanup is still pending.
- Estimated solves out of 8 (design for 1, the hard edge; the realized rate drifts up): 1 of 8.
- Difficulty score anchor: not recorded - authored outside this repo, and the bundle has never
  reached a probe.
- Score history: 2026-09-02 submitted, rejected at the bundle structure check. No gate score yet.
- Leak audit (docs/DIFFICULTY.md): per task.toml, the environment ships no expected output, no
  comments and no self-describing identifiers, and the graded streams are generated from a nonce
  made after the agent finishes. Not independently re-audited this session.
- Expert path, described step by step: task.toml `solution_explanation` carries it - reach as a
  least fixed point, the pass as rounds, the choosing seeded with the held cells, and the two
  kinds of watch emptied at different points.
- Originality check: not recorded. `tools/simcheck.py` has not been run against this bundle; it
  grades a reconstructed state and a ledger rather than work counters against a budget, which is
  the axis the similarity screen rejected `segment-merge-horizon` on.

## Verifier contract - FROZEN after Stage 2

- Artifacts the agent produces: /app/core/rch.py, /app/core/cln.py, /app/core/pss.py,
  /app/core/obs.py. The fourth needs no change, which is deliberate.
- What is checked: the ordered ledger and the store each stream leaves behind, exactly, no
  partial credit. Both come out of core/st.py, which is not editable.
- Tolerances: none. Integer and exact.
- Ground truth, and where it lives: tests/gt.json for the enumerated set, chmod 600; the
  generated set is graded by tests/oracle.py after the run.
- Deliberately not graded: mark count, round count, caching between rounds, data structures.

## Decisions and their reasons

**2026-09-02, the structural rejection.** `tests/Dockerfile` created /app/core on a
line-continuation of the `useradd` instruction:

    RUN useradd --uid 1002 --create-home sandbox \
     && mkdir -p /app/core /work /rep /logs/verifier

The directory was genuinely created, and `scripts/preflight.py` reported the bundle clean,
because its check searches the whole file for `mkdir ... /app/core`. The pipeline's structural
check does not join continuations, so it saw no RUN line creating the parent and refused the
bundle. Fixed by giving it a standalone `RUN mkdir -p /app/core`, which is what all ten archives
in this repo that have reached a pipeline gate do. Behaviour-preserving: `mkdir -p` is
idempotent and the ordering against `chmod 700 /rep` is unchanged. Do not fold it back into
another instruction to save a layer.

`tools/zipcheck.py` now fails this, validated in both directions - it fires on the archive the
pipeline rejected, naming that error, and is clean on all ten other archives including
`typeahead-query-controller`, whose `/app/src` artifact has its parent created by prefix.

**2026-09-02, the variant count.** task.toml claims six alternative correct implementations
twice and enumerates six by name, and only five directories shipped: `ok-collect` carried two
independent readings at once, the release list collected before it is applied (pss.py) and the
emptying walked over a materialised list instead of the live mapping (obs.py). Neither was ever
tested on its own, so either could have been masking the other. Split into `ok-collect` (pss.py
only) and `ok-live` (obs.py only); both score 1 independently through the real trial, and the
claim in task.toml is now literally true. Nothing the pipeline grades moved - the reference, the
ground truth, the cheats, the instruction and every line of task.toml are byte-identical.

## Validation status

| Check | Status | Notes |
|---|---|---|
| Agent image builds | pass | 2026-09-02, real docker build |
| Verifier image builds | pass | 2026-09-02, after the mkdir split |
| `/app/core` present in verifier image | pass | 2026-09-02, checked in the built image |
| oracle = 1 | pass | 2026-09-02, real two-image trial |
| nop = 0 | pass | 2026-09-02, real two-image trial |
| Cheats all score 0 | pass | 2026-09-02, all 27 through the real two-image trial (29/29 with oracle and nop) |
| Variants all score 1 | pass | 2026-09-02, 6/6 after ok-collect was split |
| `preflight.py` | pass | errors clean; 23 advisory warnings, all the documented false-positive class |
| `zipcheck.py` | pass | 2026-09-02, on the rebuilt archive |
| `harbor check` rubric | not run | harbor is not installed here |
| difficulty / easiness probes | not run | never reached a gate |

## Open questions and next steps

- The bundle has never been through `tools/simcheck.py`, `forgecheck.py`, `onelinecheck.py`,
  `deadfieldcheck.py` or `readingcheck.py`. It ships `authoring/decisions.py` and
  `authoring/readings.py`, so the last three can run. Worth doing before the probes, not before
  this resubmission - the rejection was packaging, and the content is unchanged.
- The 23 preflight warnings are all the unused-public-function class documented in CLAUDE.md
  (methods reached through an instance). Read, not obeyed.
