"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies six files under `/app/led/`: `ver.py` holds the number standing at each key
and writes a close in, `take.py` what a transaction has taken and whether that has moved,
`hold.py` what it holds at a key while it runs, `work.py` the work list and the marks,
`step.py` one op of a program, and `close.py` the close. Everything else in the tree is the
verifier's own pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a transaction takes the number standing at a key the first time one of its ops names that
     key; `cpy` and `raw` name two keys and `bmp` names its whole range
  2  an op whose key has moved since it was taken takes it again before the op runs
  3  the number held at a key is what the transaction's work makes of the numbers it has
     taken, so taking a key again moves every number derived from it, wherever it sits
  4  `add` shifts the number held just before it, `cpy` takes the number held at the other key
     just before it, and `raw` takes the number the transaction took at the other key
  5  a read prints the number held and fixes it: the work gets an entry setting that key
  6  `mk` marks; `un` throws away the work from the last standing mark through the end, and
     the whole work when no mark stands
  7  a condition is recorded while the transaction runs and tested only when it closes, at its
     own position in the work, `chk` for equal and `lim` for n or more
  8  the close takes every moved key again before the conditions are tested; a condition that
     fails throws away the work from the last standing mark through itself and the testing
     carries on, and one that fails with no mark standing writes nothing
  9  the close writes the keys the surviving work sets, at the number held at the end of it,
     in ascending key order, and a read's entry is not a write

Implementation choice, and not graded: whether a value is carried as a form over its basis or
re-derived from the work, whether a mark saves state or the work is walked again, how the work
list is held, and any internal naming. Not a free choice, and not asserted here either:
neither the re-take nor the cut may re-derive the whole work, which the execution limit on the
worker decides rather than any assertion in this file.

Hand programs are checked against `gt.json`, frozen before this file was written. Nonce
programs are generated here, after the agent has finished, and checked against the sealed
model. The model must also reproduce `gt.json` exactly, so a drifted model cannot quietly
redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("PDR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("PDR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("PDR_LOGS", "/logs/verifier"))


def stamp(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def records():
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


def lines_of(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the engine raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of lines")
    return got


@pytest.fixture(scope="module")
def kept():
    return records()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawn():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side has to agree with itself before it judges anything ---------------

def test_frozen_answers_match_the_model(frozen):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the enumerated programs: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_program(kept, frozen, name):
    assert name in kept, "no result for hand case %s" % name
    item = kept[name]
    assert item.get("sig") == stamp(cases.prog(name)), "hand program was altered: %s" % name
    assert lines_of(item) == frozen[name]


# --- programs generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_program_matches(kept, drawn):
    seed, per = drawn
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for _fam, name, lines in wanted:
        item = kept.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != stamp(lines):
            bad.append((name, "program altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(kept, drawn):
    seed, per = drawn
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
