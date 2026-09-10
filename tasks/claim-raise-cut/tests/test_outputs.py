"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five modules under `/app/hold/`: `mark.py` says which marks stand
together and what the join of two of them is, `item.py` holds an item's claims and requests and
decides what a sweep grants, `wait.py` says who each blocked request is waiting for, `cyc.py`
finds the rings and picks the transaction to cut, and `txn.py` drives a program. Everything else
in the tree is the verifier's own pristine copy, so only those five can change what a program
prints.

Graded, and settled the same way by two implementations written apart:

  1  the mark a request is tested in: the join of what the asking transaction already holds on
     that item and what it asked for, which is the least mark excluding everything both exclude
  2  a request stands when its mark stands beside every claim held by every *other* transaction,
     the asking transaction's own claims taken out of the test
  3  a sweep walks the raises first, in the order their claimants came to hold the item, granting
     each that stands and passing over each that does not
  4  a raise that was passed over pins the item: no first-time claim is granted while one is
     outstanding, whatever it asked for
  5  the first-time claims are then walked in request order and the walk stops at the first that
     does not stand
  6  a grant appends the asked mark to the claim stack, and the effective mark is the join of
     that stack; a drop takes the last mark off and the effective mark is the join of the rest
  7  who a blocked request waits for: every transaction whose claims and request, taken out of
     the service, would leave the sweep granting it
  8  while that relation has a ring, the transaction on a ring holding claims on the fewest items
     is cut, ties going to the later request and then to the larger number
  9  a cut takes the victim's request and claims out, then sweeps the items it held in the order
     it came to hold them and the item it was waiting on last; its later steps do nothing
 10  a transaction whose request is granted joins the back of one line; the line runs after the
     step that filled it, from the front, one transaction at a time, each running its own backlog
     until it blocks, ends or runs out, never interrupted, and whatever it grants joins the back
     of the same line behind everything granted before it
 11  a transaction that ends releases its claims and its items are swept in that same order
 12  the trace: one line per grant, block, drop, cut and end, in the order they happen

Implementation choice, and not graded: how the join is computed or cached, how an item indexes
its holders, whether the relation is derived or simulated, which cycle algorithm finds the rings,
and any internal naming. Not a free choice, and not asserted here either: neither the relation nor
the sweep may be recomputed from scratch across the whole service on every step, which the
execution limit on the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs are
generated here, after the agent has finished, and checked against the sealed model. The model must
also reproduce `gt.json` exactly, so a model that had drifted cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("CRC_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("CRC_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("CRC_LOGS", "/logs/verifier"))


def _sig(steps):
    return hashlib.sha256("\n".join(" ".join(s) for s in steps).encode("utf-8")).hexdigest()


def _load():
    """Every byte here came from a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("worker produced no readable output: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("worker output is not a list")
    by = {}
    for one in raw:
        if not isinstance(one, dict):
            pytest.fail("worker output entry is not an object")
        name = one.get("name")
        if not isinstance(name, str):
            pytest.fail("worker output entry has no name")
        by[name] = one
    return by


def _trace(one):
    got = one.get("got")
    if got is None:
        pytest.fail("the service raised or produced nothing: %s" % (one.get("err"),))
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
    heavy = int((LOGS / "heavy").read_text(encoding="utf-8").strip())
    return seed, per, heavy


# --- the sealed side has to agree with itself before it judges anything ----------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    hand = cases.programs()
    assert sorted(truth) == sorted(name for name, _steps in hand)
    for name, steps in hand:
        assert model.trace(steps) == truth[name], name


# --- the enumerated programs: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", [n for n, _s in cases.programs()])
def test_hand_case(produced, truth, name):
    steps = dict(cases.programs())[name]
    assert name in produced, "no result for hand case %s" % name
    one = produced[name]
    assert one.get("sig") == _sig(steps), "hand program was altered: %s" % name
    assert _trace(one) == truth[name]


# --- programs generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_program_matches(produced, nonce):
    seed, per, heavy = nonce
    wanted = gen.programs(seed, per, heavy)
    assert len(wanted) >= 380, "nonce population too small: %d" % len(wanted)
    bad = []
    for name, steps in wanted:
        one = produced.get(name)
        if one is None:
            bad.append((name, "missing"))
            continue
        if one.get("sig") != _sig(steps):
            bad.append((name, "program altered"))
            continue
        if one.get("got") != model.trace(steps):
            bad.append((name, "trace differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per, heavy = nonce
    fams = {name.rsplit("-", 1)[0] for name, _s in gen.programs(seed, per, heavy)}
    assert fams == set(gen.FAMILIES) | set(gen.HEAVY)
