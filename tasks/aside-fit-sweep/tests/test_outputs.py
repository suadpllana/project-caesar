"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five files under `/app/pool/`: `find.py` is the free map and the
placement search, `cut.py` serves a request, `side.py` holds the ranges that have been set
aside, `back.py` gives a range back, and `edge.py` resizes one. Everything else in the tree is
the verifier's own pristine copy, so only those five can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a request is rounded up to a multiple of eight; one that rounds to nothing, or that
     exceeds the size of a part, is refused
  2  a range is placed at the leftmost address whose rounded bytes are all in the free map and
     lie inside one part - which is not the same address as the leftmost free range that is
     large enough
  3  free bytes standing after the allocation, up to the end of that part, join the allocation
     when they number fewer than sixteen
  4  a freed range of 256 bytes or less is set aside whole: out of the map, joined to no
     neighbour, invisible to placement and to growth
  5  a request of exactly the size of a range that is aside takes the one set aside most
     recently, and looks there before it looks at the map
  6  more than thirty-two aside returns the one set aside earliest to the map, where it joins
     the ranges it touches; a range set aside, taken and set aside again is as young as its
     second setting aside
  7  a request that neither the aside list nor the map can serve returns everything aside to
     the map and searches once more, and the list stays empty whether or not that succeeds
  8  `sweep` returns everything aside to the map
  9  a resize down releases the tail through the ordinary free path, and changes nothing at all
     when that tail would be under sixteen bytes
 10  a resize up takes the bytes that follow only when they are in the map and only while the
     whole range stays inside one part, and the sliver rule then applies at the new end
 11  a resize that cannot be answered in place places the new range before it frees the old
     one, and leaves the range exactly where it is when that placement fails
 12  `get` on an id that is live, `put` on an id that is not, and `fit` on an id that is not
     are not events

Implementation choice, and not graded: how the free map is represented (the reference keeps
runs clipped to parts and a segment tree over the parts, the model one integer of bits per part
and a maximum per group), how the aside list carries its two orders, whether joining is a step
at all, and any internal naming. Not a free choice, and not asserted here either: neither the
placement nor the join may be answered by walking the arena, which the execution limit on the
worker decides rather than any assertion in this file.

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

SEAL = os.environ.get("AFS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("AFS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("AFS_LOGS", "/logs/verifier"))


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
        pytest.fail("the allocator raised or produced nothing: %s" % (item.get("err"),))
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
    assert fams == {f for f, _small in gen.FAMILIES}
