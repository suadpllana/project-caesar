"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/pane/`: `geom.py` indexes the flow and turns an
offset into an item, `band.py` decides the pinned group and how tall its band comes out,
`win.py` decides which items a pass renders and measures, `hold.py` chooses the item a frame
holds and carries it across an edit, `move.py` applies the event's own movement and reads the
foot flag, and `frame.py` drives the settle loop and reports the line. Everything else in the
tree is the verifier's own pristine copy, so only those six can change what a document prints.

Graded, and settled the same way by two implementations written apart:

  1  a header is as tall as it declares and a row is its group's estimate until the row has
     been measured, after which it is its real height, permanently
  2  the pinned group is the last one whose header top has reached the offset, and the band is
     the smaller of its header height and the distance from the offset to the next header
  3  the held item is the one lying across the anchor line - the offset plus the band - and
     the last item when the line falls on the total; the gap is its top less the line
  4  an item is visible when it starts before the bottom edge and ends after the top edge, and
     the window adds the overscan on both sides and is clipped to the flow
  5  the event's movement is applied and clamped first, and the foot flag is read from what it
     left behind
  6  the hold is taken before the edit and carried through it: a removed hold becomes the first
     surviving item after it, or the last surviving item before it when none follows, with the
     gap moved by the difference of the two tops as they stood before the edit
  7  a settle pass lays the band and window out from the offset it starts with, measures what
     the window has not measured, then puts the offset at the foot when the flag is set and
     otherwise at the held item's top less the gap less that pass's band, clamped
  8  the frame is settled when a pass measured nothing and left the offset alone, and stops at
     the pass cap however unsettled it is
  9  the line carries the settled offset, the last pass's pinned group, band and window, the
     hold as it stood after the edit, the rows this frame measured and the passes it ran

Implementation choice, and not graded: how the flow is indexed, whether group sums are held in
a tree, an array or a chunked list, whether the hold is carried as an index or a key, and any
internal naming. Not a free choice, and not asserted here either: the geometry cannot be walked
from the start of the flow, which the execution limit on the worker decides rather than any
assertion in this file.

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

SEAL = os.environ.get("RAP_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("RAP_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("RAP_LOGS", "/logs/verifier"))


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
        pytest.fail("the pane raised or produced nothing: %s" % (item.get("err"),))
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
