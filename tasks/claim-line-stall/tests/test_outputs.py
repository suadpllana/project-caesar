"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/hold/`: `book.py` holds the scope and mode
arithmetic and what every job holds, `line.py` the order of the waiting line and the refusal
test, `lift.py` when an ask is raised to its whole unit, `knot.py` which jobs can never
proceed and which one is cancelled, `turn.py` what the service does after an op, and `act.py`
the four ops. Everything else in the tree is the verifier's own pristine copy, so only those
six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  an ask the job's own claims already cover, in a mode at least as strong, is granted and
     changes nothing at all
  2  an ask is refused by a claim of another job whose scope overlaps it when either is a write
  3  an ask is refused by an ask of another job that conflicts with it and stands ahead of it
  4  asks whose job holds an overlapping claim stand ahead of asks whose job does not, and
     filing order breaks ties inside each group
  5  where an ask stands is read off what its job holds at that moment, not recorded when it
     was filed
  6  four cell claims already held in one unit make the next ask in that unit an ask for the
     whole unit, in the strongest mode involved
  7  a raised ask keeps the job's cell claims until it is granted
  8  a granted claim removes every claim the job holds on a scope it strictly covers
  9  after an op that releases a claim or discards an ask, the line is settled once, in order
 10  a job is forgotten once it holds nothing and waits for nothing, and starts again under a
     new number
 11  a job is held up by whoever refuses its ask, held claim or ask standing ahead alike, and a
     group held up only by one another can never proceed
 12  of the jobs on such a group, the one holding fewest claims is cancelled, ties going to the
     one that started most recently
 13  a take by a job that already has an ask waiting is ignored
 14  `end` discards the job's waiting ask as well as releasing its claims
 15  every event carries the counts the brief states, and a `show` lists the claims
     overlapping its unit in the order the jobs started, the unit ahead of its cells
 16  nothing else is printed

Implementation choice, and not graded: how claims are indexed, whether the line is one
sequence or one per unit, how the order is derived, which search finds a group of jobs held up
only by one another, and any internal naming. Not a free choice, and not asserted here either:
neither the claims conflicting with an ask, nor where an ask stands, nor which jobs can never
proceed may be found by walking the whole book or the whole line, which the execution limit on
the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs
are generated here, after the agent has finished, and checked against the sealed model. The
model must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine
correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("CLS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("CLS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("CLS_LOGS", "/logs/verifier"))


def _sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _load():
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


def _trace(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the service raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of lines")
    return got


@pytest.fixture(scope="module")
def produced():
    return _load()


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nonce():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side has to agree with itself before it judges anything ---------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == truth[name], name


# --- the enumerated programs: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.ops(name)), "hand program was altered: %s" % name
    assert _trace(item) == truth[name]


# --- programs generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_program_matches(produced, nonce):
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 200, "nonce population too small: %d" % len(wanted)
    bad = []
    for _fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _sig(lines):
            bad.append((name, "program altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
