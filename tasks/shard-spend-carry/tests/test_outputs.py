"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/opt/`: `cell.py` holds the per-slot state of one
parameter, `lay.py` decides what the map holds and in what order, `cut.py` cuts the map into
shards, `walk.py` spends each rank's budget, `tick.py` takes gradients and drives the step, and
`keep.py` writes and restores checkpoints. Everything else in the tree is the verifier's own
pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  the map holds the live parameters, and it is laid again only at a step, and only when a
     parameter was declared, frozen or thawed or the world size was set since it was last laid
  2  a parameter already in the map keeps its place; ones newly live go on the end, in the
     order they became live
  3  a parameter that leaves the map loses its moments, and keeps its values and what is pending
  4  the shard is ceil(total/ws) slots, the last one is short, and one past the world size or
     past the end of the map is empty
  5  a rank walks the slots it holds in increasing flat position with a running total from zero
  6  a slot with nothing pending costs nothing and is passed over untouched
  7  any other slot costs the size of its pending gradient and is applied while the total stays
     within the budget
  8  the first slot a rank cannot afford stops it, and that slot and everything behind it in its
     shard keep what is pending
  9  applying a slot adds its pending gradient to its moment, takes the moment off its value,
     and clears what was pending
 10  a gradient reaches every slot of its parameter whether or not the parameter is in the map
 11  a checkpoint is the value and moment of every slot of the map in flat order, and a restore
     puts each pair back into the slot that flat position held at the save
 12  a restore leaves what is pending, the live set, the world size and the budget alone

Implementation choice, and not graded: how per-slot state is held, how the parameters carrying
pending work are indexed, whether the map keeps offsets or recomputes them, how a checkpoint
records the layout it was written against, and any internal naming. Not a free choice, and not
asserted here either: neither a rank's first payable slot nor the map's offsets may be found by
walking the map, which the execution limit on the worker decides rather than any assertion in
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

SEAL = os.environ.get("SSC_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("SSC_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("SSC_LOGS", "/logs/verifier"))


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
    assert fams == {f for f, _big in gen.FAMILIES}
