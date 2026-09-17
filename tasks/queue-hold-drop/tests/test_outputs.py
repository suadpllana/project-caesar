"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/pend/`: `line.py` is the queue and what a change
names, `fold.py` is what an answer does, `hold.py` decides which changes go out, `view.py` is the
laid-over view and the two questions, `lay.py` is what one change does to a set of records, and
`reach.py` answers which records lie under one. Everything else in the tree is the verifier's own
pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  the view is the confirmed records with the queue laid over them in the order it was made
  2  a change naming a record the view does not hold does nothing at all
  3  `add` adds to what the field holds at that moment, and a field nothing has set holds zero
  4  a removal takes the records under it in the view as it stands when it is laid over
  5  a move whose new parent is the record itself or lies under it does nothing
  6  a change goes out only when every record it names carries an id, bar the one a creation
     makes, and one that stays behind holds every later change naming a record it is about
  7  a creation and a move name their parent as well; the other three name only their record
  8  an answer lands on the oldest change that has gone out and is still queued, or on nothing
  9  acceptance puts the change into the confirmed records, hands a creation the next id in the
     order answers arrive, and prints the identity the record has afterwards
 10  refusal takes the change and, spreading forward, every later change naming a record a taken
     change is about, and prints how many went
 11  a removal of a record the server has never confirmed takes that record's creation off the
     queue instead of joining it, and spreads the same way
 12  records are listed in the order they entered the view, the confirmed ones first, with their
     fields in name order

Implementation choice, and not graded: how the queue, the confirmed records and the view are
held, whether the view is carried forward or rebuilt, how the holding and take-away sets are
represented, where the identity of a record is kept, and any internal naming. Not a free choice,
and not asserted here either: neither the view nor the records under one may be derived once per
question, which the execution limit on the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs are
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

SEAL = os.environ.get("QHD_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("QHD_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("QHD_LOGS", "/logs/verifier"))


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


# --- the sealed side has to agree with itself before it judges anything ------------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == truth[name], name


# --- the enumerated programs: one per graded decision, plus both sides of each fence -----

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.ops(name)), "hand program was altered: %s" % name
    assert _trace(item) == truth[name]


# --- programs generated from a seed drawn after the agent's container was gone ------------

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
