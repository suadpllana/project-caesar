"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/feed/`: `mix.py` says which source a slot belongs
to and what retiring does to the pattern, `deck.py` is one source's own stream, `draw.py` fills
slots, `spot.py` is the feeder's state at a slot, `deal.py` cuts a step into micro-batches and
`keep.py` writes a checkpoint record and reads one back. Everything else in the tree - the
driver, the plan parser, the hand-over order and the printed line format - is the verifier's own
pristine copy, so only those six can change what a plan prints.

Graded, and settled the same way by two implementations written apart:

  1  a sample whose token length is over the cap is passed over, does not fill the slot, and
     the same source is asked again
  2  a cursor that runs off the end of an epoch continues at the start of the next one under
     that epoch's hand-over order, and the samples over the cap that trail an epoch are passed
     over only when the source is next asked
  3  a source retires the moment it delivers the last sample its allowance covers; an allowance
     of zero never retires
  4  a retired source's entries leave the pattern, the survivors keep their order, and the next
     slot begins a stretch whose offsets are counted from it
  5  slot offset o of a step goes to rank o % world, and each rank's slots fill its accumulation
     micro-batches in order
  6  a record names the base, the steps the trainer completed, the steps the feeder produced,
     and every source's state at the feeder's position
  7  the state a record names is the one the feeder is in before the slot it names is filled,
     and a retired source prints as gone
  8  a load begins at the slot after the last step the trainer completed, under the geometry
     that run was using
  9  a load carries the base of the run it came from, so a chained load composes

Implementation choice, and not graded: whether the timeline is grown lazily or built eagerly,
how a stretch is found in it, whether a source's position inside an epoch is precomputed or
counted for, how a step is cut into micro-batches, what a record holds beyond the four fields
the line format reads, and any internal naming. Not a free choice, and not asserted here
either: nothing may be reached by walking the stream, which the execution limit on the worker
decides rather than any assertion in this file.

Hand plans are checked against `gt.json`, frozen before this file was written. Nonce plans are
generated here, after the agent has finished, and checked against the sealed model. The model
must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("MRR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("MRR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("MRR_LOGS", "/logs/verifier"))


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
        pytest.fail("the feeder raised or produced nothing: %s" % (item.get("err"),))
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


# --- the enumerated plans: one per graded decision, plus both sides of each fence ------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.ops(name)), "hand plan was altered: %s" % name
    assert _trace(item) == truth[name]


# --- plans generated from a seed drawn after the agent's container was gone ------------

def test_every_nonce_plan_matches(produced, nonce):
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
            bad.append((name, "plan altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce plans wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
