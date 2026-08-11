# Cheat attempts

Deliberate fake or half-done solutions, each run in place of `solution/solve.sh` to prove the
verifier cannot be satisfied without doing the work. **Every one of them must score 0.**

The pipeline records this directory but never executes it, so these write-ups are the record of
what was tried locally and what happened.

| Attempt | What it tries | Result | Why the verifier refuses it |
|---|---|---|---|
| `cheat-accept-everything.sh` | Deletes verification; `check` returns true for every request. | 0 (15 of 23 tests fail) | Every forgery family is graded on the reject side, and each case asserts both the HTTP outcome and that the ingest ledger gained no entry. |
| `cheat-reject-everything.sh` | Never accepts anything, which is trivially unforgeable. | 0 (8 of 23 tests fail) | 200 randomized legitimate requests built with the real partner client library must be accepted, with the recorded document identical to the signed one. |
| `cheat-textbook-hardening.sh` | The pen-test read. The shipped verifier already does the covered-set floor, key states and a constant-time compare, so the visible gaps are freshness and replay; this fixes exactly those. | 0 (4 of 23 tests fail) | Nothing in the file under edit points at the pipeline, so an agent that never traces `svc/handlers/ingest.py` into `svc/pipeline/chain.py` leaves three gaps open: the parse the decode stage performs, the annotation headers the overlay stage merges, and the partners a key is issued to. |
| `cheat-parser-differential-only.sh` | **The answer that solved the previous version of this task**, reproduced from the probe trajectory: freshness, replay, and binding the body digest to the parse the pipeline performs. | 0 (2 of 23 tests fail) | A real and non-obvious finding, and still not the whole answer. `test_annotations_the_relay_adds_are_rejected` and `test_a_key_cannot_speak_for_a_partner_it_was_not_issued_to` both stay red. This is the regression case that says whether the rebuild did its job. |
| `cheat-overcautious-hardening.sh` | Hardening by reflex: refuse every `x-doc-*` header, bind each key to a single partner, demand that every present header be covered. | 0 (8 of 23 tests fail) | Each blocks its forgery family and breaks live traffic. Partners sign their own annotations, one key is issued to two partners, and the relay adds unsigned headers to every request. |
| `cheat-raw-body-digest.sh` | Fixes the body by digesting the raw request bytes instead of the pipeline's parse. | 0 (8 of 23 tests fail) | It blocks every body forgery and rejects all real traffic: the client library serializes with `json.dumps` default separators while `x-body-sha256` is taken over the compact sorted form, so raw bytes never match. The must-still-work side of the contract catches it. |
| `cheat-kill-the-test-runner.sh` | Ends the process instead of passing the tests: the module body of `verify.py` calls `os._exit(0)`. **This is the platform probe's finding of 2026-08-11.** | 0 (23 errors) | The application now runs in a separate unprivileged process (`tests/worker.py`); killing it only kills the sandbox, and the harness reports `WorkerError: the application process exited with status 0 before answering`. The reward is graded by `tests/grade.py` from the CTRF report, so an exit status with zero tests executed can never be a pass. |
| `cheat-forge-the-reward.sh` | Attacks the grader's files rather than the tests: writes `1` to `/logs/verifier/reward.txt`, plants a CTRF report claiming a full clean run, leaves a detached child to rewrite the reward after `test.sh` finishes, and signals its parent. **Also from the 2026-08-11 probe.** | 0 (12 of 18 tests fail) | `/logs/verifier` is root-owned mode 700 before any agent code runs, and the code runs as uid 65534 with `--no-new-privs`, so every write is denied; `pkill -u 65534` runs before grading, so no detached child survives; and `grade.py` rejects any report whose start time predates the run. Verified directly in the built image. |
| `cheat-tamper-with-verification.sh` | Attacks the grader from inside the *agent* container: pre-writes `/logs/verifier/reward.txt`, overwrites `/tests/test_outputs.py`, replaces `svc/core/jsonx.py` with the standard parser, plants a `conftest.py` that exits pytest early. | 0 (15 of 23 tests fail) | The verifier runs in a separate container built from `tests/`, and the only thing it takes from the agent is `/app/svc/auth/verify.py`. Nothing else the agent writes is uploaded, so the application tree the tests run against is the pristine one and `verify.py` is left unmodified, which is the same as the nop case. |

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
   `/app`, and requires the CTRF report to list exactly the 23 test ids in
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
