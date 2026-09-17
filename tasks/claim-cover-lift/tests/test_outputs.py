"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/hb/`: `hold.py` records what each job holds,
`fit.py` decides what conflicts and what a job already covers, `line.py` keeps the waiting
requests, `lift.py` turns a slot request into a request for the box, `knot.py` finds jobs that
have come to wait for each other, and `gate.py` drives take, drop and end. Everything else in
the tree is the verifier's own pristine copy, so only those six can change what a program
prints.

Graded, and settled the same way by two implementations written apart:

  1  a claim on a box and a claim on any of its slots conflict when at least one is w
  2  two claims on sibling slots never conflict, and two readers never conflict
  3  a request is granted at once, ahead of the line, when the asking job already holds a
     covering claim on that node or on its box; a claim on a slot covers nothing above it
  4  a hold is a list of acquires: a drop removes the most recent one and what is left decides
  5  a request that is blocked waits, and a request behind an older conflicting one waits too
  6  grants are ordered by one sequence taken across the whole store, not per node
  7  a slot request by a job already holding four or more slots of that box, and no covering
     claim on it, becomes a request for the box, in w when the request or any of them is w
  8  a lifted request that cannot be granted waits, keeping the slot claims until it is
  9  a granted lifted request frees those claims in slot order and then grants its trigger
 10  a job lies on a cycle of the waits-for relation through granted claims and through older
     waiting requests alike; the job on any cycle with the fewest acquires is stopped, ties to
     the largest job number
 11  a job ignores every line naming it while its own request waits, after it has ended, and
     after it has been stopped
 12  end frees every acquire in node order, then says done
 13  show lists the jobs holding a node in job order with their acquires as sorted letters

Implementation choice, and not graded: how holdings are indexed, whether the waiting requests
are one list or one per box, how the cycle is found, and any internal naming. Not a free choice,
and not asserted here either: neither the jobs of a family, nor which requests are grantable,
nor whether a job lies on a cycle can be found by walking the whole store, which the execution
limit on the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs
are generated here, after the agent has finished, and checked against the sealed model. The
model must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("CCL_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("CCL_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("CCL_LOGS", "/logs/verifier"))


def fingerprint(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def read_record():
    """Every byte here came from a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("worker produced no readable output: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("worker output is not a list")
    by = {}
    for item in raw:
        if not isinstance(item, dict):
            pytest.fail("worker output entry is not an object")
        name = item.get("name")
        if not isinstance(name, str):
            pytest.fail("worker output entry has no name")
        by[name] = item
    return by


def trace_of(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the service raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of lines")
    return got


@pytest.fixture(scope="module")
def record():
    return read_record()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def exam():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side has to agree with itself before it judges anything ---------------

def test_the_model_still_makes_the_frozen_answers(frozen):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == frozen[name], name


# --- the enumerated programs: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_program(record, frozen, name):
    assert name in record, "the service was never run on %s" % name
    item = record[name]
    assert item.get("sig") == fingerprint(cases.ops(name)), "hand program was altered: %s" % name
    assert trace_of(item) == frozen[name]


# --- programs generated from a seed drawn after the agent's container was gone ---------

def test_generated_program(record, exam):
    seed, per = exam
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for _fam, name, body in wanted:
        item = record.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != fingerprint(body):
            bad.append((name, "program altered"))
            continue
        if item.get("got") != model.expect(body):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_was_run(record, exam):
    seed, per = exam
    fams = {fam for fam, _n, _b in gen.programs(seed, per)}
    assert fams == {name for name, _big in gen.FAMILIES}
