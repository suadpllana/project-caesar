"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/tab/`: `live.py` holds the bucket and answers the
two queries, `lay.py` is the append, `wipe.py` is the cut, `mark.py` says what a created slab
carries, `take.py` says which slabs a fold re-packs, and `push.py` drives a proposal.
Everything else in the tree is the verifier's own pristine copy, so only those six can change
what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a put makes every key of its range live in one new slab, taking any of them that were
     already live away from the slab that held them
  2  `add` counts the keys of the put's range that were not live
  3  a cut reports the keys it actually removed, not the width of its range
  4  a slab left holding nothing is gone, whichever part emptied it
  5  a fold looks only at the slabs all of whose keys lie inside its range
  6  which of those it re-packs is decided key by key against the proposal's base
  7  one of them holding a key from each side of the base undoes the attempt and forces a
     second one at the head
  8  the undone attempt leaves nothing behind, slab numbering included
  9  only one second attempt is ever made, and its base is the head
 10  a fold with fewer than two slabs in reach does nothing at all
 11  a re-packed key keeps the number it already carried
 12  a proposal that creates no slab and removes no key takes no number

Implementation choice, and not graded: how a bucket is held, whether an attempt is undone by a
journal or by rebuilding what it touched, whether adjacent runs of one slab are merged, where
the number a key carries is stored, and any internal naming. Not a free choice, and not
asserted here either: neither the slabs meeting a range, nor the live key count, nor whether a
slab lies wholly inside a range can be found by walking the bucket, which the execution limit
on the worker decides rather than any assertion in this file.

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

SEAL = os.environ.get("SFS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("SFS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("SFS_LOGS", "/logs/verifier"))


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
