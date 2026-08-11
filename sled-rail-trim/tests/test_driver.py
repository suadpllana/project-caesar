"""Grades the apply path.

Nothing here links, imports or executes the agent's code. It is compiled into a
separate binary that runs as an unprivileged user and asks for bus transactions
on a pipe; the part, the fault rules, the sessions and the ceiling all live on
this side of that pipe, inside a root-only /tests.
"""

import os
import sys

import pytest

import cases
import fingerprints
import harness
import plan
import sessions

SEED = int(os.environ["CHECK_SEED"])
APP_DIR = os.environ.get("CHECK_APP", "/app")
PRISTINE = os.environ.get("CHECK_PRISTINE", "/tests/pristine")
BINARY = os.environ["CHECK_RUNNER"]
USER = os.environ.get("CHECK_USER", "")

# The graded run. Several sessions rather than one, so the count is not at the
# mercy of a single seed's shape.
LONG_RAILS = 20
LONG_BATCHES = 10
LONG_SESSIONS = 8


def _fingerprints_or_fail():
    problems = fingerprints.check(APP_DIR, PRISTINE)
    if problems:
        pytest.fail("fingerprint check failed:\n  " + "\n  ".join(problems))


@pytest.fixture(scope="session")
def short_runs():
    _fingerprints_or_fail()
    out = {}
    for case in cases.all_cases(SEED):
        cost = plan.reference_cost(case["rails"], case["start"], case["session"])
        spent, fault, ok, note = harness.drive(
            BINARY, case["rails"], case["start"], case["session"], cost, USER)
        out[case["id"]] = {
            "batches": len(case["session"]), "ok": ok, "fault": fault,
            "note": note, "spent": spent,
        }
    harness.assert_agent_code_absent(sys.modules, APP_DIR)
    return out


@pytest.fixture(scope="session")
def long_run():
    _fingerprints_or_fail()
    spent_total = 0
    reference_total = 0
    faults = []
    misses = 0
    batches = 0
    for n in range(LONG_SESSIONS):
        start, session = sessions.build(SEED + n * 7919, LONG_RAILS, LONG_BATCHES)
        cost = plan.reference_cost(LONG_RAILS, start, session)
        spent, fault, ok, note = harness.drive(
            BINARY, LONG_RAILS, start, session, cost, USER)
        reference_total += cost
        spent_total += spent
        batches += len(session)
        misses += len(session) - ok
        if fault:
            faults.append(f"session {n}: {fault}")
        if note:
            faults.append(f"session {n}: {note}")
    harness.assert_agent_code_absent(sys.modules, APP_DIR)
    return {
        "spent": spent_total,
        "reference": reference_total,
        "ceiling": plan.ceiling_from(reference_total),
        "faults": faults,
        "misses": misses,
        "batches": batches,
    }


def _check(runs, case_id):
    assert case_id in runs, f"{case_id} never ran"
    got = runs[case_id]
    assert not got["fault"], f"{case_id}: the part faulted with {got['fault']}"
    assert not got["note"], f"{case_id}: {got['note']}"
    assert got["ok"] == got["batches"], (
        f"{case_id}: the part was left wrong after "
        f"{got['batches'] - got['ok']} of {got['batches']} batches")


@pytest.mark.parametrize("case_id", cases.REQUIRED_IDS)
def test_named_case(short_runs, case_id):
    _check(short_runs, case_id)


def test_generated_cases(short_runs):
    generated = [k for k in short_runs if k.startswith("generated-")]
    assert generated, "no generated cases ran"
    bad = []
    for case_id in sorted(generated):
        got = short_runs[case_id]
        if got["fault"] or got["note"] or got["ok"] != got["batches"]:
            bad.append((case_id, got["fault"] or got["note"] or "wrong end state"))
    assert not bad, f"{len(bad)} generated cases disagree: {bad[:6]}"


def test_every_named_case_present(short_runs):
    """Deleting or renaming a case must not make the run pass."""
    missing = [i for i in cases.REQUIRED_IDS if i not in short_runs]
    assert not missing, f"cases missing from the run: {missing}"


def test_the_named_cases_are_all_here():
    """The count is written down here rather than counted from cases.py.

    REQUIRED_IDS is derived from named_cases(), so on its own it would shrink
    quietly if a case were ever dropped. This is the independent assertion.
    """
    assert len(cases.REQUIRED_IDS) == 45, (
        f"cases.py offers {len(cases.REQUIRED_IDS)} named cases, not 45")
    assert len(set(cases.REQUIRED_IDS)) == 45, "two named cases share an id"


def test_long_run_reaches_every_batch(long_run):
    assert not long_run["faults"], f"the part faulted: {long_run['faults'][:4]}"
    assert long_run["misses"] == 0, (
        f"the part was left wrong after {long_run['misses']} of "
        f"{long_run['batches']} batches")


def test_long_run_inside_the_ceiling(long_run):
    assert long_run["spent"] <= long_run["ceiling"], (
        f"the apply path spent {long_run['spent']} transactions against a "
        f"ceiling of {long_run['ceiling']} "
        f"({plan.REFERENCE_MULTIPLE:.2f}x the {long_run['reference']} a "
        "reference apply path spends on the same sessions)")
