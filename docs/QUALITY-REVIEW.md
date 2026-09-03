# Passing the quality review

Gate 5 of the validation pipeline is an **agentic quality review**: a frontier model
(`claude-opus-4-8` in observed runs) reads the entire bundle — instruction, environment, verifier,
solution, metadata — against the benchmark's implementation rubric. Some criteria are **blocking**
(they reject the task outright); others are advisory and surfaced to the human reviewer.

Preflight cannot catch most of this: the criteria need reading comprehension, not pattern matching.
So the assistant must review the bundle itself, as the reviewer would, **before packaging**.

## How to run the self-review

Read the bundle end to end with fresh eyes and answer each criterion below explicitly — not "looks
fine", but which file and line satisfies it. Anything you cannot answer is a finding: fix it, or
tell the contributor plainly that it is a known risk.

`harbor check <dir> -m <model>` runs a version of this automatically and is worth running when an
API key is available. It is not a substitute for the pass below: its built-in rubric is smaller
than the platform's, and one of its criteria still describes the old same-container test layout.

## Criteria

**Instruction ↔ verifier agreement** (the reviewer checks this in both directions)

- Every behavior the tests check is described in the instruction. An assertion the instruction
  never mentions is an unfair task.
- Every behavior the instruction promises is actually checked by a test. An untested requirement is
  a hole an agent can skip through.
- Every output file the tests read is named explicitly, with its absolute path, in the instruction.
- If the agent must produce structured data, the exact schema is specified — in the instruction or
  in a file the instruction points to.

**Instruction prose** (a reading check — no script can make this call)

- No runs of successive same-structured sentences (same opener, same rhythm, parallel clause
  after parallel clause). These read as machine-written whatever their true authorship. Where a
  run exists, the fix is the contributor rewording in their own voice — not you rewriting.
- Each requirement stated once; no restatements in different words.
- The register is the contributor's throughout — no drift into assistant-flavored phrasing in
  passages that were heavily edited.

**Verifier rigor**

- The tests demand evidence of real execution, not exit codes or state the agent could write
  directly.
- Test code is structured and commented so a reader can see which behavior each section checks.
- Tests are deterministic: no dependence on wall-clock time, network availability, or ordering that
  is not itself under test.

**Environment hygiene**

- Neither `tests/` nor `solution/` is copied into the agent image.
- Test dependencies are installed by `tests/test.sh` (or baked into `tests/Dockerfile`), not into
  the agent's environment.
- Every Python package is pinned with `==`; no apt package is pinned.
- No dangling references: paths, filenames and variables in the instruction exist in the
  environment and are spelled identically. The reviewer looks closely at names, where typos hide.

**Solution quality**

- `solution/solve.sh` *computes* the answer through the steps a real expert would take. Writing the
  final answer directly with `echo`/`cat` fails. Using `echo`/`cat` to write a program that is then
  executed is fine.
- The solution does not exploit anything the agent could not legitimately use.

**Anti-cheating**

- The answer cannot be found by reading the environment: no leftover data files, caches, git
  history, or comments that reveal it.
- Tolerances are tight enough that a trivial or degenerate output fails.
- If the environment clones a repository, the agent cannot reach a commit that contains the answer.

**Metadata quality** — cheap to get wrong, and blocking

- `category` is one of the seven, and `subcategory` is a label from *that category's* row.
- `tags` name the **specific** techniques, concepts, tools and libraries of this task. Restating
  the category or subcategory is a blocking failure. Three to five specific tags is a good target.
- `difficulty_explanation` names the concrete step a frontier agent gets wrong — not "this task is
  complex".
- If the environment uses deliberate legacy-register naming (degraded identifiers) or a stripped
  documentation style, `difficulty_explanation` says so as a design choice. The rubric's typo
  criterion reads variable names closely, and terse names without a stated rationale can be
  misread as sloppiness by the reviewing model.
- `solution_explanation` describes the actual method, and why an expert would work that way.
- `verification_explanation` explains why passing the tests means the work was genuinely done.
- `relevant_experience` is real and specific to this domain.
- `expert_time_estimate_hours` is honest and consistent with the task's difficulty claim.

## Observed platform verdicts

Record every real rejection here, with what fixed it, so the same failure cannot recur. Where a
rule can be mechanically checked, it also goes into `scripts/preflight.py`.

| Date | Gate | Verdict | Fix |
|---|---|---|---|
| 2026-08-09 | Quality review (blocking) | `category=Science, subcategory=Math, tags=["Math"]` — "a single generic term that merely restates the subcategory" | Tags must be specific to the task, e.g. `["algebraic-geometry", "resultants", "exact-arithmetic", "real-root-isolation", "sympy"]`. Now a preflight error, plus template guidance. |
| 2026-08-09 | Structural / verification | `tests/Dockerfile never creates /app` — artifact upload failed with "Could not find the file /app in container" | Verifier image must `RUN mkdir -p` the parent of every declared artifact. Now a preflight error, plus `RUN mkdir -p /app` in the template. |
| 2026-08-10 | Structural (blocking) | `PYTEST-VERSION` in both Dockerfiles: "pytest is pinned to 8.3.5 — every Frontier Bench verifier uses the canonical pytest==9.1.1" | Wherever pytest is pinned, in any scanned file, it must be exactly `pytest==9.1.1` (and `pytest-json-ctrf==0.5.2`). Now a preflight error (warn for ctrf); template already canonical. |
| 2026-08-10 | Structural (warning) | `CHEAT-DIR-PRESENT`: cheat/ included — informational only; the pipeline never executes it | Expected and benign. Keep cheat write-ups accurate and self-contained; no action needed. |
| 2026-08-10 | Structural (blocking) | `VERIFIER-NETWORK-FETCH`: test.sh pipes curl into a shell — "never install over the network at trial time" | All fetches move to tests/Dockerfile, pinned and sealed at build time. Template rewritten; preflight errors on curl/wget/pip/apt/uv/npm/git-clone in test.sh. |
| 2026-08-10 | Structural (blocking) | `VERIFIER-TOOLING-AT-TRIAL-TIME`: test.sh installs pytest/ctrf at trial time — verifier must not depend on PyPI | Canonical pytest/ctrf now installed in tests/Dockerfile; test.sh only runs pytest. Same preflight check covers it. |
| 2026-08-10 | Structural (blocking) | `CODENAME-HIT`: bundle contains blocked internal term "afterquery" | Allowed only as the org prefix in task.toml `[task] name`; preflight now errors on the term anywhere else in the bundle. |
| 2026-08-11 | Quality review (fail) | `verifier execution isolation`: verifier ran agent code as root with `/logs/verifier` unlocked and reward written after tests — agent could background a process that rewrites reward.txt to 1 | New `docs/VERIFIER-ISOLATION.md` (privilege drop, lock reward channel first, default-deny reward, reap survivors) + mandatory reward-tamper cheats + preflight warns when the verifier executes agent code without these. |
| 2026-08-11 | Structural (blocking) | `CODENAME-HIT` again — but the hits were in `jobs/*/result.json`, harbor's own output left inside the task folder after running the gates. `task.toml` was never the problem | Root cause was two tools disagreeing: preflight skipped `jobs/` when scanning, package.py shipped it. Both now share one `shipped_files()` definition, harness dirs are detected by content (`result.json`) not just by name, preflight warns when they are present, package.py audits the built zip itself, and the documented gate commands use `-o ../jobs`. |
| 2026-08-11 | Quality review (fail) | `verifier execution isolation`: grading verdict written into the sandbox-writable work dir with its path exposed to agent code; grader's result loop outside try/except and its exit status unchecked, so a planted verdict + `os._exit` crash yielded reward 1 with no work | Same doc, rules 4-6: trusted verdict on a path agent code never learns and cannot write; fragile parsing inside the guard; every stage's exit status checked; `grader crash after plant` and `malformed worker output` are now mandatory cheats. |
| 2026-09-04 | Quality review (blocking) | `category and tags`: `alias-settle-report` declared `category=ML, subcategory=Evaluation` because its brief is set in an evaluation harness — "nothing about the work requires ML knowledge, and the 'evaluation harness' framing is narrative". The work is union-find reachability under disequality constraints. Tags were praised as specific and good | Category names the skill the graded work exercises, not the story's setting: now `Software / Algorithms`, the reviewer's own suggestion (their other suggestion, "Debugging", is not a label in the guideline table). Two lines of `task.toml`; the brief was left byte-identical because it had just cleared the AI and similarity screens. New `tools/catcheck.py` fires when a category's vocabulary is absent from `environment/` and present in the prose — measured 0 environment hits here against 25-49 for the three ML tasks that passed this criterion. |
