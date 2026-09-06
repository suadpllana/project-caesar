# Frontier Bench workspace

Follow `AGENTS.md` as the operating manual. The retained task inventory is in `README.md`.
Before designing or hardening another task, read `docs/DIFFICULTY.md`,
`docs/QUALITY-REVIEW.md`, and `docs/PASSING-TASK-RESEARCH.md`.

Historical task transcripts and retired project notes were deliberately removed. Do not restore
them as examples; only the projects listed in `README.md` belong in this checkout.

## Lessons, measured (2026-09-06, `token-seam-emit`)

Four defects found by local gates before submission, each with the number that found it:

- **An ablation that measures unreachable variants measures nothing.** The first
  core-versus-periphery run ablated `sm.py`, which ships correct, and reported the character
  seam as the dominant failure at 47.8% of requests against the core's 15.2%. No agent
  produces that variant. Rebuilt as reachable whole-solver readings
  (`authoring/<slug>/readings.py`); the core reading now fails 50.5% and every reading is
  separated *and* named by an enumerated case. Frequency is not the point either: with 300
  nonce requests and all-or-nothing grading, any reading moving 1% of requests scores 0.
- **A cheat sweep that never installs the cheat reports 18 clean zeroes.** `trial.py`
  treated a whole app tree as a flat module directory, found only `run_stream.py`, and
  graded every cheat as the shipped tree. Caught only because `cheat_report.py` asserts
  *which* test catches each attestation probe. Assert the layer, never just the reward.
- **A probe that attacks at import time attacks nothing.** `cheat-kill-monitor` freed the
  monitoring tool id on import, before the runner arms it, and scored 1. Attestation probes
  must interfere during the run.
- **Fingerprints must not `repr()` nested code objects.** A `repr` of a code object carries
  its filename and address, so any function containing a generator expression hashed
  differently every run and failed the reference. Recurse into nested code instead.

- **Authoring scratch inside the task folder ships.** `package.py` zipped `.trial/` and
  `.cheats/` from an authoring run still in flight: 455 entries instead of 70, and
  `zipcheck` caught it only because the stray files were newer than the zip. Every
  authoring script now writes to `tempfile.mkdtemp` outside the bundle. Related: `zipcheck`
  rejects CRLF in `.py` and `.json`, not only in `.sh`, and Git normalising on commit hides
  it because the working copy is what gets zipped.

Two findings the models caught in the reference itself: an occurrence cache that froze the
first index it found missed a longer stop completing later but starting earlier, and a
backward character scan disagreed with a forward one on a malformed lead byte. Both were
invisible to 1200 random requests until a stop pool containing the shape was added.

## Lessons, measured (2026-09-06, `pack-bind-retire`)

Six defects found by local gates before submission, each with the number or symptom that
found it:

- **An attack the setup makes impossible is not a cheat.** `cheat-rewrite-frozen` appended to
  a frozen module of the executed tree and scored **1**: that tree is root-owned and
  read-only to the uid the run drops to, so the write never happens and the reference simply
  ran. Shipping it would have implied an evidence layer that never fires. Replaced with
  `cheat-patch-frozen-file`, which solves the task in `hst/ev.py` and scores 0 because only
  declared artifacts reach the run - a probe that would score 1 if the boundary leaked.
- **`docker run -v <relative path>` mounts an empty named volume, silently.** A debugging call
  with a relative cheat path produced `laid 0 of 5 declared artifacts` and a clean zero for
  every probe. This is the 2026-09-06 "a cheat sweep that never installs the cheat" finding in
  a new shape, and the thing that caught it was `place.py` printing how many artifacts it
  laid. Every overlay step should print its own count.
- **Three checkers looked only inside the bundle for authoring material the doctrine forbids
  shipping.** `readingcheck.py` reported "nothing to check", and all four correct variants
  scored **0** through `docker_trial.py --variants` and `--dir`, because both resolve
  `tasks/<slug>/authoring/` and the doctrine puts that material at `authoring/<slug>/`. Both
  patched to prefer the repo-level copy, the way `onelinecheck.py` already did. A gate that
  reports success while looking at nothing is worse than no gate.
- **A probe that reports only its reward proves nothing.** Half the special probes were caught
  by a layer they were not aimed at, and only asserting the *trace* found it:
  `cheat-malformed-report` overwrote the report before the runner wrote it, which is a no-op;
  `cheat-reward-daemon` left no message because the reap killed it mid-sleep, so `reap.py` now
  reports how many it signalled rather than only how many survived; `cheat-plant-and-crash`
  failed at fixture setup, which pytest prints as `ERROR` and a `FAILED`-only parser misses
  entirely, reporting "no test failed" on a probe that worked perfectly.
- **The verifier image installed `util-linux` it already had.** `setsid`, `setpriv`, `timeout`
  and `useradd` are all in `python:3.12-slim`. Dropping the apt layer removed a build-time
  network dependency that fails in a sandbox with no plain-HTTP egress, and took
  `tests/Dockerfile` from 0.754 against `token-seam-emit` to clean on `simcheck`.
- **`preflight.py` cannot see module-qualified calls.** Its unused-public-function check uses a
  `(?<![\w.])name\s*\(` lookbehind, so `ld.ld(...)` is invisible and every module of a
  package-structured environment earns a warning: 8 here, 10 on `token-seam-emit`. Left
  as-is because both retained bundles trip it and the warning names the exception, but a
  gate everyone learns to ignore is how a real finding gets missed.

One finding about the design rather than the tooling. The agent tree is **198 lines across 10
files, the smallest of the seven retained tasks** (alias-settle-report 229, token-seam-emit
250, guard-mark-unwind 544), so Prong B1 is not operating: a frontier agent holds all of it at
once. That is deliberate here - the 2026-09-06 review demanded that every load-bearing rule be
stated outright, so the tree hides nothing by design - but it means the whole difficulty rests
on B2 and C1. Padding a tree with scenery is the scale anti-pattern and would have been worse.
If this comes back solved too often the repair is a semantic addition that multiplies
interactions, not more files.

And one about the review itself: **when a reviewer says the spec withholds a load-bearing
rule, they are agreeing with this file, not arguing with it.** Both sentences this task had
listed as withheld were requirements the verifier grades, not method, and two defensible
readings of each produced different ledgers. Stating them cost nothing measurable - every
reading they closed is still a wrong answer an agent can reach, and `readings.py` measures
each one moving 12 to 92 per cent of scripts.
