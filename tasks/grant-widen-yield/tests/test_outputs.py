"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/lk/`: `mode.py` is the lattice, `hold.py` the
table of what each transaction holds, `give.py` what happens to a holder that must give way,
`keep.py` the claims and the sweep over them, `wide.py` the widen rule and `step.py` the take
and the line procedure. Everything else in the tree is the verifier's own pristine copy, so
only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  the compatibility table over IS, IX, S, SIX and X, and the supremum of any two of them
  2  the cover a mode requires above it - IS for the two read modes, IX for the three that
     write - and that a transaction's mode at a store or a block is the supremum of the mode
     it asked for there and the covers its own live grants below currently require
  3  a take is settled level by level from the store inward with no look-ahead: a younger
     conflicting holder gives way there and then, an older one refuses the take outright, and
     what was already given up stays given up while nothing asked for is granted
  4  giving way takes the node and every grant the holder has below it, deepest first, and
     then the levels above it fall to what is left
  5  only a node the program asked for leaves a claim, at that asked mode
  6  a claim is due when it is made and again when the service moves anything at the level
     that last refused it; a sweep takes the claims due when it starts, oldest transaction
     first and then outermost resource, and tries each once
  7  the widen rule counts grants only, fires at the supremum of the children and the asked
     mode, forces nobody to give way, runs deepest level first in transaction order until a
     round changes nothing, and runs after the sweep
  8  a release takes the subtree and the claims under it, deepest first, and then narrows
  9  the printed vocabulary and its order, and the closing report

Implementation choice, and not graded: how the hold table is indexed, whether the cover is a
pair of counters or a multiset, whether claims are one record or two indexes, whether
compatibility is decided by counting holders or by walking them, and any internal naming. Not
a free choice, and not asserted here either: neither the cover, nor the set of claims a sweep
looks at, nor the pairs the widen rule tests can be found by scanning everything that could in
principle be relevant, which the execution limit on the worker decides rather than any
assertion in this file.

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

SEAL = os.environ.get("GWY_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("GWY_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("GWY_LOGS", "/logs/verifier"))


def _sig(rows):
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


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
    return gen.programs(seed, per)


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
    bad = []
    for _fam, name, rows in nonce:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _sig(rows):
            bad.append((name, "program altered"))
            continue
        if item.get("got") != model.expect(rows):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (
        len(bad), len(nonce), bad[:4])


def test_the_nonce_population_is_large_enough(nonce):
    assert len(nonce) >= 300, "nonce population too small: %d" % len(nonce)


def test_every_family_is_represented(nonce):
    fams = {fam for fam, _n, _l in nonce}
    assert fams == {f for f, _big in gen.FAMILIES}
