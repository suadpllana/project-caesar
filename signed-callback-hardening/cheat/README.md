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
| `cheat-tamper-with-verification.sh` | Attacks the grader from inside the agent container: pre-writes `/logs/verifier/reward.txt`, overwrites `/tests/test_outputs.py`, replaces `svc/core/jsonx.py` with the standard parser, plants a `conftest.py` that exits pytest early. | 0 (10 of 18 tests fail) | The verifier runs in a separate container built from `tests/`, and the only thing it takes from the agent is `/app/svc/auth/verify.py`. Nothing else the agent writes is uploaded, so the application tree the tests run against is the pristine one and `verify.py` is left unmodified, which is the same as the nop case. |

Two further shapes were considered and are covered by the tests above rather than by their own
script: hardcoding an expected output has nothing to target, because the verifier never compares
against a fixed answer and only observes how the service behaves on freshly generated traffic;
and requiring that every header be covered by the signature is the same failure mode as
`cheat-raw-body-digest.sh`, since the relay adds unsigned headers to every request.

To re-run one: copy the script over `solution/solve.sh`, run `harbor run -p . -a oracle -e docker`,
confirm the reward is 0, then restore the real solution and re-run the oracle and nop gates.
