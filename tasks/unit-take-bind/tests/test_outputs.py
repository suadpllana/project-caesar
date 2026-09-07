"""Grading. Root, and it never executes submitted code.

FROZEN CONTRACT
---------------
The submission supplies four files under `/app/res/`: `step.py` costs a candidate and says which
units a pull's source name can denote, `show.py` says which names each kind of pull can reach
from a unit, `pick.py` settles a set of lowest-ranked candidates, and `turn.py` drives the
settlement. Everything else in the tree is this verifier's own pristine copy, so only those four
can change what a program prints.

Graded, and settled the same way by two implementations written apart - the reference sweeps one
rank at a time, `model.py` pushes candidates onto a heap and pops a whole rank at once:

  1  a unit's own declarations sit at rank 0, and nothing pulled can undercut them
  2  `als` sits at rank 0 too, and binds only when its target is a declared unit - a unit named
     nowhere but as a pull source or an alias target is not one
  3  a pulled candidate costs one more than the larger of two ranks: the source reading's, and
     the rank the name already holds in the source unit
  4  a source name has one reading per unit it can denote - the program unit of that name at
     rank 0, and any unit the name is bound to in the pulling unit, at that binding's rank -
     and both readings contribute candidates
  5  a wide pull reaches the names that are neither hidden nor shut in the source
  6  a narrow pull reaches the names that are not hidden, shut ones included
  7  only the lowest-ranked candidates decide; a higher-ranked one from another origin is not
     a second opinion
  8  lowest-ranked candidates agreeing on one origin bind the name; two origins clash
  9  a clash is terminal: it binds nothing and neither kind of pull carries it onward
 10  a binding is decided once, from facts of lower rank only, so no declaration order and no
     visiting order can move it

Implementation choice, never graded: how the settlement is driven (sweep, heap, work list), the
container types the four functions return, the order within them, and any internal naming. The
interfaces the pristine tree calls - `step.cost`, `step.srcs`, `show.out_all`, `show.out_one`,
`pick.settle`, `turn.run` - are the contract; everything inside them is free.

The record is compared exactly, line for line. Enumerated programs are checked against
`gt.json`, frozen by `authoring/unit-take-bind/build_gt.py` before this file was written;
generated programs are built here from a nonce drawn after the submission has finished and
settled by the sealed model. The model must reproduce `gt.json` exactly before anything is
graded, so a drifted model cannot quietly redefine correct.
"""
import json
import os
import pathlib

import pytest

import cases
import gen
import model

WORK = pathlib.Path(os.environ.get("UTB_WORK", "/work"))
OUT = WORK / "worker_out.json"
TESTS = pathlib.Path(os.environ.get("UTB_TESTS", "/tests"))
GT = TESTS / "gt.json"
LOGS = pathlib.Path(os.environ.get("UTB_LOGS", "/logs/verifier"))


def _load():
    """Everything here came from submitted code. Parse it defensively."""
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


@pytest.fixture(scope="module")
def produced():
    return _load()


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


def _record(item):
    got = item.get("got")
    if got is None:
        pytest.fail("binder raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("record is not a list of lines")
    return got


def _nonce():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side must agree with itself before it judges anything ---------------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == truth[name], name


# --- enumerated programs: one per graded decision, plus the must-still-work side -----------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for enumerated program %s" % name
    item = produced[name]
    assert item["lines"] == cases.CASES[name], "program was altered: %s" % name
    assert _record(item) == truth[name]


# --- generated programs, built after the submission finished --------------------------------

def test_every_generated_program_matches(produced):
    seed, per = _nonce()
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "generated population too small: %d" % len(wanted)
    bad = []
    for fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item["lines"] != list(lines):
            bad.append((name, "program altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d generated programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_families_all_present(produced):
    seed, per = _nonce()
    fams = {fam for fam, _, _ in gen.programs(seed, per)}
    assert fams == {f for f, _ in gen.FAMILIES}


def test_no_extra_records(produced):
    """A submission may not add programs of its own to the record."""
    seed, per = _nonce()
    known = set(cases.ORDER) | {name for _, name, _ in gen.programs(seed, per)}
    assert set(produced) <= known, "unexpected records: %s" % sorted(set(produced) - known)[:4]
