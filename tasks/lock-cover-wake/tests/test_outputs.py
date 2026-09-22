"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the seven files under `/app/lk/`: `mode.py` is the mode table, `ent.py` is
one entry of the lock table, `txn.py` is what a transaction holds and waits for, `ask.py` is the
request path, `wake.py` is the pass over waiting heads, `lift.py` is subsumption and the raise,
and `tell.py` is the report. Everything else in the tree is the verifier's own pristine copy, so
only those seven can change what a script prints.

Graded, and settled the same way by two implementations written apart:

  1  a request for a mode the transaction already covers, on that resource or on the row's
     table, takes no lock, prints nothing and is counted
  2  a row request takes the intention on its table first, and the row request is made when
     that intention request is granted rather than when the command is read
  3  a request by a holder converts to the cover of the two modes and is tested against the
     modes the other transactions hold
  4  a new request may not pass a queued request, and a conversion may not pass a queued
     conversion
  5  a request that cannot be granted fells, in begin order, every conflicting holder whose
     standing the requester began before
  6  a holder's standing is the earliest begin among itself and the transactions waiting on the
     other entries it holds
  7  the queue holds conversions ahead of new requests, each class in request order
  8  after every change the waiting heads are gone over again, earliest-begun transaction first
  9  a table grant releases the rows of that table the new mode covers, and only those
  10 a row grant that leaves the transaction at the threshold raises its table lock once,
     without queueing and without felling, and abandons the raise silently
  11 a command naming a transaction that is waiting, felled or committed is passed over
  12 the report: state and locks in acquisition order per transaction in begin order, then the
     queues in resource order, then the covered count

Implementation choice, and not graded: how an entry holds its granted modes and its two queue
classes, whether a transaction's rows are indexed per table or found by walking what it holds,
how the frontier of waiting heads is kept, how a standing is aggregated, and any internal
naming. Not a free choice, and not asserted here either: none of the tally, the standing or the
frontier may be worked out by walking everything a transaction holds, which the execution limit
on the worker decides rather than any assertion in this file.

Hand scripts are checked against `gt.json`, frozen before this file was written. Nonce scripts
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

SEAL = os.environ.get("LCW_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("LCW_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("LCW_LOGS", "/logs/verifier"))


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
        pytest.fail("the lock table raised or produced nothing: %s" % (item.get("err"),))
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


# --- the enumerated scripts: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.prog(name)), "hand script was altered: %s" % name
    assert _trace(item) == truth[name]


# --- scripts generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_script_matches(produced, nonce):
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
            bad.append((name, "script altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce scripts wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
