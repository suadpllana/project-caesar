"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/keep/`: `hit.py` finds the rows that point at a
set of keys, `reach.py` works out which rows a change touches and how deep each one sits,
`meld.py` settles what one row ends up taking, `halt.py` holds the three checks that stop a
change, `lay.py` orders the effects and applies them, and `undo.py` walks a change back.
Everything else in the tree is the verifier's own pristine copy, so only those six can change
what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a link takes the rows whose column holds the key of a row the change carries; an empty
     column is not one of them
  2  every match, every restrict and every merge reads the store as it stood when the change
     began, so nothing a change does can hide a row from a link that comes after it
  3  a row's group is the greatest number of links on any chain reaching it, not the first
  4  a row taken out ignores every effect on its columns, and where two links act on one
     column of a row, or both take it out, the one declared first decides
  5  groups go deepest first when the change takes a row out and shallowest first when it
     re-keys one; inside a group it is table, then the key the row had when the change began,
     then column, and every line names that same key
  6  a follow onto a row's key column re-keys that row and the change carries on from it; onto
     any other column it stops there
  7  a restrict link is read off the whole reach before anything is applied, so the row that
     stops the change may be one the change would itself have taken out
  8  a deferred link is read off the store the change leaves, and only a key its parent table
     held when the change began and does not hold now can bring it down
  9  a change that stops applies nothing, or is walked back to exactly what it found, columns
     and keys alike
  10 a key already held by another row stops a re-key before anything is applied
  11 a change naming a key that is not there says so and does nothing

Implementation choice, and not graded: how the rows that point at a set of keys are found,
whether the reach walks the tables in order or relaxes a worklist, how the effects on a row
are held, and whether a change is walked back from a log or from remembered slots. Not a free
choice, and not asserted here either: neither the matching nor the deferred check may be a
walk of the table, which the execution limit on the worker decides rather than any assertion
in this file.

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

SEAL = os.environ.get("LCR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("LCR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("LCR_LOGS", "/logs/verifier"))


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
        pytest.fail("the keeper raised or produced nothing: %s" % (item.get("err"),))
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
