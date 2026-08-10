# Cheat attempts

Deliberate fake or half-done solutions, each run in place of `solution/solve.sh` to prove the
verifier cannot be satisfied without doing the work. **Every one of them must score 0.**

The pipeline records this directory but never executes it, so these write-ups are the record of
what was tried locally and what happened.

| Attempt | What it tries | Result | Why the verifier refuses it |
|---|---|---|---|
| `cheat-accept-everything.sh` | Deletes verification; `check` returns true for every request. | 0 (12 of 18 tests fail) | Every forgery family is graded on the reject side, and each case asserts both the HTTP outcome and that the ingest ledger gained no entry. |
| `cheat-reject-everything.sh` | Never accepts anything, which is trivially unforgeable. | 0 (6 of 18 tests fail) | 200 randomized legitimate requests built with the real partner client library must be accepted, with the recorded document identical to the signed one. |
| `cheat-textbook-hardening.sh` | The plan a strong agent writes without reading the ingest handler: coverage floor, key-state policy, clock skew, per-key nonce cache, constant-time compare. Everything except binding the digest to the parse the handler performs. | 0 (2 of 18 tests fail) | `test_document_cannot_be_reshaped_under_a_valid_signature` and its nested variant place a repeated key at the front of the document. `json.loads` keeps the last occurrence, so the digest is unchanged, while `svc/core/jsonx.py` keeps the first, so the handler acts on different data. This is the attempt that decides whether the task has teeth. |
| `cheat-raw-body-digest.sh` | Fixes the body by digesting the raw request bytes instead of the handler's parse. | 0 (6 of 18 tests fail) | It blocks every body forgery and rejects all real traffic: the client library serializes with `json.dumps` default separators while `x-body-sha256` is taken over the compact sorted form, so raw bytes never match. The must-still-work side of the contract catches it. |
| `cheat-kill-the-test-runner.sh` | Ends the process instead of passing the tests: the module body of `verify.py` calls `os._exit(0)`. **This is the platform probe's finding of 2026-08-11.** | 0 (18 errors) | The application now runs in a separate unprivileged process (`tests/worker.py`); killing it only kills the sandbox, and the harness reports `WorkerError: the application process exited with status 0 before answering`. The reward is graded by `tests/grade.py` from the CTRF report, so an exit status with zero tests executed can never be a pass. |
| `cheat-forge-the-reward.sh` | Attacks the grader's files rather than the tests: writes `1` to `/logs/verifier/reward.txt`, plants a CTRF report claiming 18 clean passes, leaves a detached child to rewrite the reward after `test.sh` finishes, and signals its parent. **Also from the 2026-08-11 probe.** | 0 (12 of 18 tests fail) | `/logs/verifier` is root-owned mode 700 before any agent code runs, and the code runs as uid 65534 with `--no-new-privs`, so every write is denied; `pkill -u 65534` runs before grading, so no detached child survives; and `grade.py` rejects any report whose start time predates the run. Verified directly in the built image. |
| `cheat-tamper-with-verification.sh` | Attacks the grader from inside the *agent* container: pre-writes `/logs/verifier/reward.txt`, overwrites `/tests/test_outputs.py`, replaces `svc/core/jsonx.py` with the standard parser, plants a `conftest.py` that exits pytest early. | 0 (10 of 18 tests fail) | The verifier runs in a separate container built from `tests/`, and the only thing it takes from the agent is `/app/svc/auth/verify.py`. Nothing else the agent writes is uploaded, so the application tree the tests run against is the pristine one and `verify.py` is left unmodified, which is the same as the nop case. |

The last two rows are the anti-cheat probe's blocking findings against the first submission,
kept here as permanent regression cases. The defect was real: the verifier used to import the
agent's `verify.py` into the pytest process and derive the reward from pytest's exit status, so
`os._exit(0)` in the module body produced exit 0 with no tests executed and scored 1. Three
things changed, and none of them touched what the task asks the agent to do:

1. **The grading process no longer executes agent code.** `tests/harness.py` imports only
   modules the agent cannot supply (`sdk.signer`, `svc.auth.keys`, `svc.core.cfg`, none of
   which import the verifier) and drives the application through `tests/worker.py`, a separate
   process launched with `setpriv --reuid 65534 --regid 65534 --clear-groups --no-new-privs`.
   The worker's file descriptor 1 is moved aside before the application is imported, so output
   printed by agent code cannot be passed off as a protocol reply.
2. **The grader's files are out of reach.** `/logs/verifier` is root-owned mode 700 and
   `/tests` is mode 700 before anything runs; the worker script is copied to `/run/worker.py`,
   the only file the unprivileged user needs. `test.sh` kills anything left running as that
   user before grading.
3. **The reward comes from evidence.** `tests/grade.py` runs as root, imports nothing from
   `/app`, and requires the CTRF report to list exactly the 18 test ids in
   `tests/expected_tests.txt`, all passed, with zero failed, skipped, pending or other, and a
   start timestamp after `test.sh` began. `test_environment_is_the_one_the_verifier_expects`
   additionally asserts that the grading process never imported the application and that the
   worker is not running as root.

Two further shapes were considered and are covered by the tests above rather than by their own
script: hardcoding an expected output has nothing to target, because the verifier never compares
against a fixed answer and only observes how the service behaves on freshly generated traffic;
and requiring that every header be covered by the signature is the same failure mode as
`cheat-raw-body-digest.sh`, since the relay adds unsigned headers to every request.

To re-run one: copy the script over `solution/solve.sh`, run `harbor run -p . -a oracle -e docker`,
confirm the reward is 0, then restore the real solution and re-run the oracle and nop gates.
