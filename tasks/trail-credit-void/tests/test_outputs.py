"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the seven files under `/app/crd/`: `store.py` holds the records and undoes
what a span wrote, `pred.py` decides whether a goal's predicate holds, `obs.py` carries the
previous observation's values and tests the violations against them, `book.py` is the credit
book, `void.py` is what a firing takes away, `ep.py` drives an episode and `tally.py` reports.
Everything else in the tree is the verifier's own pristine copy, so only those seven can change
what a trail prints.

Graded, and settled the same way by two implementations written apart:

  1  an observation happens at the end of a step that ended ok, and at the start of an episode,
     where it credits nothing and fires nothing
  2  a goal is credited when its predicate holds and every prerequisite was credited at a
     strictly earlier observation of the same episode, goals taken in ascending id, once
  3  credit settles: it survives the predicate going false, and is never granted twice
  4  a violation is a change between two consecutive observations of the same episode - a value
     lost, gained, or fallen
  5  a firing shuts the goal it names until that goal is observed unsatisfied, and strips the
     credit of that goal and of every goal standing on it, directly or through others
  6  credit is applied first and violations fire after it, both in ascending id
  7  a step that ended err leaves the records as it found them and observes nothing
  8  the budget charges every action, including those of a step that ended err; the action that
     would cross it is not performed and its step is rolled back
  9  an episode closed by its budget has its records undone to where it opened and keeps its
     credit; one that ran to the end leaves its records for the next episode
  10 an episode reports the weights it holds, and the run counts the episodes holding all of
     theirs

Implementation choice, and not graded: how the records hold their undo information, whether
goal states live in an array or in sets, whether prerequisites are counted down or compared by
observation index, how the dependants of a goal are walked, and any internal naming. Not a free
choice, and not asserted here either: neither the records nor the rubric may be swept in whole
at each step or each observation, which the execution limit on the worker decides rather than
any assertion in this file.

Hand trails are checked against `gt.json`, frozen before this file was written. Nonce trails are
generated here, after the agent has finished, and checked against the sealed model. The model
must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("TCV_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("TCV_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("TCV_LOGS", "/logs/verifier"))


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
        pytest.fail("the grader raised or produced nothing: %s" % (item.get("err"),))
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
        assert model.expect(cases.prog(name)) == truth[name], name


# --- the enumerated trails: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.prog(name)), "hand trail was altered: %s" % name
    assert _trace(item) == truth[name]


# --- trails generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_trail_matches(produced, nonce):
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for _fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _sig(lines):
            bad.append((name, "trail altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce trails wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
