"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five files under `/app/keep/`: `live.py` tracks what a volume holds and for
how long, `cover.py` says which pegs a closed hold leaves behind, `edge.py` says what shedding a peg
changes, `gone.py` says what a trim gives back, and `sole.py` answers a tally. Everything else in
the tree is the verifier's own pristine copy, so only those five can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a peg keeps what its volume held at the moment it was made, and that never changes afterwards:
     a block written later is not kept by it, and a block overwritten afterwards still is
  2  a volume keeps a block while any of its slots holds it, several slots may hold one block, and
     the hold ends only when the last of them lets go
  3  a block may be taken back into a volume it had left, and pegs made while it was away keep
     nothing of it, so a volume's hold on a block is a series of stretches rather than one
  4  a fork holds everything the peg holds, and pegs of the fork keep those blocks too, whichever
     volume wrote them
  5  writing in a volume after a fork changes that volume alone
  6  shedding a peg ends its keeping and nothing else, including when a volume was forked from it
  7  a block nothing keeps is given back at the next trim, not at the moment it stopped being kept
  8  the reclaim list is in the order blocks stopped being kept, blocks of one op in allocation
     order, and a block already given back is never printed again
  9  a tally counts the blocks its peg keeps and nothing else keeps: another peg keeping the block,
     or a volume still holding it, takes it out of the count

Implementation choice, and not graded: how the hold on a block is carried, what is written down when
a hold closes and what is worked out later, whether the pegs that keep a block are counted or
recognised from their ends, how the pegs of a volume are indexed, what a shed walks, and any
internal naming. Not a free choice, and not asserted here either: no arrangement that recomputes
what is kept at each trim, tally or shed gets through the three large families inside the execution
limit, which the wall clock on the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen from a definitional settling of the contract before
this file was written. Nonce programs are generated here, after the agent has finished, and checked
against the sealed model. The model must also reproduce `gt.json` exactly, so a drifted model cannot
quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("PHT_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("PHT_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("PHT_LOGS", "/logs/verifier"))


def _sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _load():
    """Every byte here came from a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
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
        pytest.fail("the accounting raised or produced nothing: %s" % (item.get("err"),))
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
    """gt.json was frozen from a definitional settling. If the model has drifted, grade nothing."""
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
