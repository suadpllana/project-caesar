"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five files under `/app/eng/`: `keep.py` is the workspace, `mark.py`
builds and tests the observations a run makes, `hold.py` is what the engine remembers about
each step, `step.py` runs one step, and `wake.py` decides when a step needs running.
Everything else in the tree is the verifier's own pristine copy, so only those five can
change what a program prints, and a sixth file put beside them is never collected.

Graded, and settled the same way by two implementations written apart:

  1  a record is the ordered list of the observations one run made - a read of a path, a
     look at a path, a pull of a step, and the output a successful run wrote
  2  the record is walked in that order and the walk stops at the first observation that no
     longer holds; walking a pull observation brings that step up to date, so the walk runs
     steps, and observations past the first failure are neither walked nor run
  3  a step whose verdict was taken while the workspace was as it now is needs no walk
  4  a step runs at most once per round; one that has already run and is found stale ends
     the request with `stuck`
  5  a pull observation holds while the step it names still emits the value recorded, however
     many times that step has run
  6  a look observes presence, never the bytes at that path
  7  a read of an absent path ends the run with `missing`, and the record kept ends with that
     absence; a run cut short by a loop or a stuck below it keeps nothing
  8  a step that died stays dead until an observation of its record stops holding; a pull of
     a dead step ends the puller with `via`, and a dead observation holds whatever the reason
  9  a read of a path some step emits observes bytes, and never brings that step up to date
 10  a successful run observes what it wrote to its own output path
 11  a cycle is the live pull stack, and the chain runs from where the repeated step first
     appears on it

Implementation choice, and not graded: how the record is held, whether the workspace counts
its changes or versions each path, whether the scheduler recurses or keeps its own stack,
whether per-step state is one object or several dicts, and any internal naming. Not a free
choice, and not asserted here either: a verdict cannot be re-derived from scratch every time
a step is pulled, which the execution limit on the worker decides rather than any assertion
in this file.

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

TESTS = os.environ.get("PCS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

SEAL = os.environ.get("PCS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("PCS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("PCS_LOGS", "/logs/verifier"))


def _sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
        pytest.fail("the engine raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the trace is not a list of lines")
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
        assert model.expect(cases.prog(name)) == truth[name], name


# --- the enumerated programs: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.prog(name)), "hand program was altered: %s" % name
    assert _trace(item) == truth[name]


# --- programs generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_program_matches(produced, nonce):
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for name, text in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _sig(text):
            bad.append((name, "program altered"))
            continue
        if item.get("got") != model.expect(text):
            bad.append((name, "trace differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {name.split(".")[0] for name, _text in gen.programs(seed, per)}
    assert fams == set(gen.FAMILIES) | {"deep"}
