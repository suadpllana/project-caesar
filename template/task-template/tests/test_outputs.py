"""Verifier assertions.

Copied to /tests/test_outputs.py and run by /tests/test.sh in the verifier container.

This file encodes the verifier contract agreed in Stage 2. Once that contract is frozen,
it does not change to make a run pass. If the reference solution fails these tests, the
solution or the environment is wrong — not the test. Loosening a tolerance or deleting an
assertion to reach a passing score is reward hacking.

Rules:
  - Read only the paths declared in `artifacts` in task.toml. They appear at their
    original absolute paths (the agent's /app/output.json is read as /app/output.json);
    a declared path the agent never created simply does not exist here — treat that as
    a failing case, not an error to work around.
  - Assert on substance, not on incidentals: check that the work was actually done, not
    that a file exists or that a string appears somewhere.
  - Assume an adversarial agent. Ask of every assertion: what is the laziest output that
    would pass this? If that output does not represent real work, the assertion is too weak.
  - Give each test a failure message a human can act on.
"""

# TODO: replace with the assertions from your frozen verifier contract.


def test_outputs():
    """Verify the agent's output represents genuinely completed work."""
    raise AssertionError("TODO: verifier not implemented")
