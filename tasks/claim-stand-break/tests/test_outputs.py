"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/tx/`: `rows.py` is the committed rows and their
versions, `hold.py` is what an open transaction holds, `view.py` answers a read, `cover.py`
says what a claim covers and whether it still stands, `watch.py` drives the checks and holds
the death index, and `path.py` is the op loop and the commit path. Everything else in the tree
is the verifier's own pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a read is answered from the rows as they stood when the transaction opened, under its own
     changes that were made before the read and have not been taken back
  2  a scan returns the first n rows from lo to hi in key order, its own new keys included and
     its own deleted keys left out
  3  every get, span, put and del is a claim, numbered from 0 in op order, counting the ops a
     rollback later takes back
  4  a read claim stands while answering it again, against the rows committed now, gives what
     it gave - by value, so a rewrite with the value already held leaves it standing
  5  what a claim is drawn from: a point read its key, a scan that filled its row limit the
     keys up to its last row, a scan that came back short its whole range
  6  a change claim stands while it has not been taken back and no transaction that committed
     after this one opened has written its key - by version, whatever value it wrote
  7  claims are judged when they are made, after every commit that goes through, and after
     every rollback
  8  the lowest index of the claims that stopped standing at that moment is reported once, and
     a claim that stopped standing never stands again
  9  a commit applies the last standing change of each key and is reported before the deaths it
     causes, which come out lowest transaction number first; a dead or dropped transaction
     applies nothing

Implementation choice, and not graded: whether claims are indexed by key or walked, whether the
cover of a read is found by a binary search or by running back along a list, whether the key
order of the rows is kept sorted or worked out when a scan needs it, and any internal naming.
Not a free choice, and not asserted here either: a scan must not be answered again from the
rows to decide whether it still stands, which the execution limit on the worker decides rather
than any assertion in this file.

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

SEAL = os.environ.get("CSB_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("CSB_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("CSB_LOGS", "/logs/verifier"))


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
        pytest.fail("the engine raised or produced nothing: %s" % (item.get("err"),))
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
