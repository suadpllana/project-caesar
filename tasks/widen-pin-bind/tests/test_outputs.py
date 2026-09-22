"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/res/`: `kind.py` measures the rise between two
kinds, `pick.py` collects the candidates of a call and puts the settled kind into an entry's
slots, `pin.py` settles an open entry, `cost.py` prices a slot and a result, `best.py` chooses
between the survivors and `walk.py` drives the binding. Everything else in the tree is the
verifier's own pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a kind rises to another over the shortest chain of declared edges, and to itself in none
  2  the candidates of a call are the entries of its name taking as many slots as it has
     arguments
  3  a call in a slot is bound asking for that slot's kind, and an open slot of an entry that
     is not pinned is bound asking for nothing
  4  an open entry settles at the single least kind every open slot rises to, and is dropped
     when there is no such kind or it does not rise to the entry's bound
  5  a slot costs the steps from the kind its argument stands at to the kind the slot asks
     for, and the last cost is the steps from the result to the kind the call was asked for
  6  the winner is no worse at every cost than each other survivor and better at one; with
     none such the call is ambiguous, and with no survivor it has no binding
  7  the pins of trials that were abandoned or beaten are dropped, and the winner's are kept
     in the order they were made, its own last
  8  a pinned entry is not settled again, and its open slots ask for the kind it holds
  9  the bind lines run outermost first and left to right, and the tally adds every cost of
     every call that was kept

Implementation choice, and not graded: whether the pins are threaded as a map or kept in one
table under an undo log, how the survivors are reduced, whether the rise distances are
searched for or closed over once, and any internal naming. Not a free choice, and not asserted
here either: what a call produces cannot be found again by trying it under every candidate of
the call above it, which the execution limit on the worker decides rather than any assertion in
this file.

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

SEAL = os.environ.get("WPB_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("WPB_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("WPB_LOGS", "/logs/verifier"))


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
        pytest.fail("the binder raised or produced nothing: %s" % (item.get("err"),))
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
