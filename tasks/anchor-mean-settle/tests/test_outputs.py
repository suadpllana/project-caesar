"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six modules under `/app/pan/`: `grid.py` holds the row order and the
figures a prefix height is read from, `gues.py` says how tall a row nobody has measured is
assumed to be, `seat.py` holds the anchor and decides where a scroll position lands,
`step.py` is a render pass, `edit.py` is every change to the list, and `ask.py` answers the
three questions. Everything else in the tree is the verifier's own pristine copy, so only
those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  the assumed height of an unmeasured row is the floor mean of the measured rows'
     heights over the rows still in the list, and 24 only while none is measured
  2  that assumption reaches every unmeasured row, so measuring any row moves the total and
     every offset, ahead of the anchor as well as behind it
  3  a pass measures the lowest unmeasured row the view touches, re-seats, and asks again -
     `seen` counts the rows it measured, not the rows the view held when it started
  4  the anchor is the first row the view touches, taken before the pass measures anything
  5  the anchor's distance from the view's top edge is held for the whole pass, so a clamp
     loses the residue instead of absorbing it
  6  a re-seat is clamped to the scroll range, which the total height decides
  7  `roll` clamps and then takes the anchor from where it landed
  8  every edit re-seats against the anchor being held
  9  deleting the anchor falls to the row that took its index, or to the new last row, and
     keeps the held distance; deleting the last row leaves no anchor and no scroll
 10  a move keeps the row's measurement and its anchor role
 11  `set` gives up that row's measurement, and with it a sample from the mean
 12  `span` gives up every measurement, so the assumption falls back to 24
 13  `face` names the first row the view touches and its edge relative to the view's, which
     is zero or negative, and `face none` when there are no rows
 14  `tall` counts the unmeasured rows at the assumed height

Implementation choice, and not graded: how the row order is held, whether a prefix is read
from blocks over the list or from the aggregates of a position tree, whether a width change
sweeps every row or bumps a generation, where the measured height is stored, and any
internal naming. Not a free choice, and not asserted here either: no prefix height, scroll
range or view membership may be found by walking the row list, which the execution limit on
the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce
programs are generated here, after the agent has finished, and checked against the sealed
model. The model must also reproduce `gt.json` exactly, so a drifted model cannot quietly
redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("AMS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("AMS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("AMS_LOGS", "/logs/verifier"))


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
        pytest.fail("the panel raised or produced nothing: %s" % (item.get("err"),))
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
    assert len(wanted) >= 400, "nonce population too small: %d" % len(wanted)
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
