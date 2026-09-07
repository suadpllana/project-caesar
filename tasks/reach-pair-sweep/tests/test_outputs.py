"""Grading. Root, and it never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five files under `/app/col/`: `plan.py` chooses the roots for a
collection, `scan.py` walks reachability and folds in the pair table, `keep.py` settles the
finalizer queue and what it keeps alive, `age.py` decides ageing and promotion, and `wipe.py`
clears weak references and names what is released. Everything else in the tree is the verifier's
own pristine copy, so only those five can change what a program prints.

Graded, and settled the same way by two implementations written apart:
  1  the roots of a full collection, and of a minor one, where the remembered set is a hint
     whose recorded field has to be read again rather than trusted
  2  what the walk reaches, with a pair's value joining once its key is reached, iterated, and
     an old key ready from the start of a minor collection
  3  that a minor collection traces and releases only the nursery
  4  the finalizer queue settled against the walk, before any keeping is granted
  5  what a queued finalizer keeps: its object and that object's closure, pairs included
  6  weak clearing tested against the walk alone, never against what is merely kept, and never
     against old space on a minor collection
  7  clearing staying put once done, and a finalizer queued at most once for an object
  8  ageing: a survivor ages, an object kept only for a finalizer does not, a pinned object
     still ages but stays put, and promotion records its existing nursery-valued fields
  9  release: everything in scope that the walk did not reach and no finalizer is keeping
 10  a number is not an object: `new` reuses the number of an object that has been released, and
     nothing the runtime recorded about the earlier occupant answers for the later one - not
     whether its finalizer has run, and not a pair row written about it as a key

Implementation choice, never graded: how each fixed point is walked (the reference goes
depth-first from a stack, the model breadth-first from a deque), the container types returned,
the order within each returned collection (the runtime sorts), and any internal naming. Not a
free choice, and not graded by any assertion here: what a minor collection is allowed to cost.
The pair table has to be indexed rather than rescanned, a minor collection's passes have to be
over the nursery rather than the whole heap, and the remembered set has to be pruned of entries
that no longer name a nursery object. The execution limit decides all three, on the `wide` and
`sweep` families, and every one of them leaves the answers unchanged - which is why none of them
can be an assertion.

The record is compared exactly, line for line. Hand cases are checked against `gt.json`, frozen
before the verifier was written; nonce programs are generated here, after the agent has
finished, and checked against the sealed model. `gt.json` and the model must also agree with
each other on every hand case, so a drifted model cannot quietly redefine correct.
"""
import hashlib
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


def _digest(lines):
    """Must match `worker.py`'s digest exactly: it is how a program is identified here."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


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
    assert len(cases.ORDER) == 32
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == truth[name], name


# --- hand cases: one per graded decision, plus the must-still-work side ---------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("prog") == _digest(cases.CASES[name]), (
        "hand program was altered: %s" % name)
    assert _record(item) == truth[name]


# --- nonce programs, generated after the agent finished ------------------------------

def _nonce():
    return NONCE.read_text(encoding="utf-8").strip(), int(PER.read_text(encoding="utf-8").strip())


def test_every_nonce_program_matches(produced):
    seed, per = _nonce()
    wanted = gen.programs(seed, per)
    assert len(wanted) == 378, "nonce population changed: %d" % len(wanted)
    bad = []
    for fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("prog") != _digest(lines):
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
