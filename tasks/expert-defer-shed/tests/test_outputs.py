"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the seven files under `/app/lay/`: `gate.py` ranks the experts and says how
many of them a token wants, `cap.py` sizes the buffers and the bank budget, `buf.py` holds the
buffers, `back.py` carries what a token has been refused and the queue between microbatches,
`put.py` drives the step, `trim.py` is the end-of-step bank shed and `tally.py` reports.
Everything else in the tree is the verifier's own pristine copy, so only those seven can
change what a step file prints.

Graded, and settled the same way by two implementations written apart:

  1  experts rank by gate score descending, ties to the smaller index, and a token wants the
     shortest prefix of that ranking reaching the threshold - all of it when it falls short
  2  buffers are sized from the first microbatch's wanted slots, the bank budget from the
     buffer size, both rounded up
  3  a token takes the experts of its want list in rank order at the lowest free slot, and
     stops at the first it cannot enter
  4  a full expert gives up its weakest occupant that has not been displaced this step, if the
     arrival's score there is strictly higher, and the arrival takes that exact slot
  5  a token that loses a rank loses every placement it holds at a later one
  6  only a token that loses or never gets rank zero is queued, in the order the losses
     happened, and a loss in the last microbatch is held and prints nothing
  7  an expert that refused a token is struck out of its ranking for the rest of the step
  8  banks shed in index order once the step is over, weakest placement first, each removal
     carrying the token's later ranks with it wherever they sit
  9  the residual is read off the want list as it finally stands, and the balance number pairs
     final demand with kept placements

Implementation choice, and not graded: how a buffer's free slots and its order over
displaceable occupants are held, whether a token's placements are one list of pairs or two
parallel lists, whether the ranking is stored or recomputed, and any internal naming. Not a
free choice, and not asserted here either: neither the weakest occupant, nor the lowest free
slot, nor the weakest placement of a bank can be found by scanning, which the execution limit
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

SEAL = os.environ.get("EDS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("EDS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("EDS_LOGS", "/logs/verifier"))


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
