"""Grading. Root, and it never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies `/app/cyc/keep.py`, exposing `cycle(h)` and returning three collections:
the names of weak references this collection clears, the ids whose finalizer joins the queue,
and the ids released. Everything else in the tree is the verifier's own pristine copy, so only
that one file can change what a program prints.

Graded, and settled the same way by two implementations written apart:
  1  what the open frames reach, a pair's value joining once its key is reached, iterated
  2  that iteration cascading - a value pulled in can be the next pair's key
  3  the queue settled against what the frames reach, before any keeping for finalizers
  4  what a queued finalizer keeps: its object and that object's closure, pairs included
  5  weak clearing tested against the frames alone, never against what is merely kept
  6  clearing staying put once done
  7  a finalizer queued at most once for an object, across every cycle
  8  release: everything neither reached nor kept, and nothing else

Implementation choice, never graded: how each fixed point is walked (the reference goes
depth-first from a stack, the model breadth-first from a deque), what the collector returns as
its container type, the order within each returned collection (the runtime sorts), and any
internal naming or structure. Not a free choice, and not graded here either: the pair table has
to be indexed rather than rescanned, which the execution limit decides rather than any assertion
in this file.

The record is compared exactly, line for line. Hand cases are checked against `gt.json`, frozen
before the verifier was written; nonce programs are generated here, after the agent has
finished, and checked against the sealed model. `gt.json` and the model must also agree with
each other on every hand case, so a drifted model cannot quietly redefine correct.
"""
import json
import os
import pathlib

import pytest

import cases
import gen
import model

WORK = pathlib.Path(os.environ.get("RPS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(os.environ.get("RPS_TESTS", "/tests")) / "gt.json"
LOGS = pathlib.Path(os.environ.get("RPS_LOGS", "/logs/verifier"))
NONCE = LOGS / "nonce"
PER = LOGS / "per"


def _load():
    """Everything here came from agent-influenced code. Parse it defensively."""
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


@pytest.fixture(scope="module")
def produced():
    return _load()


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


def _record(item):
    got = item.get("got")
    if got is None:
        pytest.fail("collector raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("record is not a list of lines")
    return got


# --- the sealed side must agree with itself before it judges anything ----------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == truth[name], name


# --- hand cases: one per graded decision, plus the must-still-work side ---------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item["lines"] == cases.CASES[name], "hand program was altered: %s" % name
    assert _record(item) == truth[name]


# --- nonce programs, generated after the agent finished ------------------------------

def _nonce():
    return NONCE.read_text(encoding="utf-8").strip(), int(PER.read_text(encoding="utf-8").strip())


def test_every_nonce_program_matches(produced):
    seed, per = _nonce()
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item["lines"] != list(lines):
            bad.append((name, "program altered"))
            continue
        got, want = item.get("got"), model.expect(gen.ops(lines))
        if got != want:
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_families_all_present(produced):
    seed, per = _nonce()
    fams = {fam for fam, _, _ in gen.programs(seed, per)}
    assert fams == {f for f, _ in gen.FAMILIES}
