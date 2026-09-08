"""Grading. Root, and it never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies four files under `/app/bil/`: `own.py` indexes the links an asset and a
content carry, `agg.py` answers a space's usage, `gate.py` decides whether an operation fits
the limits, and `edit.py` updates the accounting once one is applied. Everything else in the
tree is the verifier's own pristine copy, so only those four can change what a script prints.

Graded, and settled the same way by two implementations written apart:
  1  the oldest link owns a content, and owns it whole
  2  the charged space is the one that link sits in now, re-read after a folder moves
  3  the charge moves to the oldest link left when the owning link goes
  4  a content is charged once, however many assets carry it and however many links they hold
  5  changing an asset's content re-settles both the content it left and the one it joined
  6  an operation is settled against the state it produces, not against the states it passes
  7  a space is refused only when it ends over its limit and higher than it started
  8  structure is refused before the limit is looked at, and a refusal changes nothing
  9  a content nothing links is charged nowhere, claim or no claim
 10  a rollback restores links with their ages, so ownership after it follows those ages
 11  claims are not rolled back, and decide whether a later asset survives one
 12  an id an asset has held is never available again

Implementation choice, never graded: how the links are indexed, how the aggregate is shaped,
which container types are used, the order of any internal iteration, where the state is kept on
the store object, and internal naming. Not a free choice, and not graded by any assertion here
either: a space's usage cannot be recomputed from the tree at the scale the wide family
reaches, which the execution limit decides rather than this file.

The record is compared exactly, line for line. Hand cases are checked against `gt.json`, frozen
before the verifier was written; nonce scripts are generated here, after the agent has
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

WORK = pathlib.Path(os.environ.get("SCS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(os.environ.get("SCS_TESTS", "/tests")) / "gt.json"
LOGS = pathlib.Path(os.environ.get("SCS_LOGS", "/logs/verifier"))
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


def _sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _usable(item, lines):
    """The worker's own account of one script, or a reason it cannot be graded."""
    got = item.get("got")
    if got is None:
        return None, "the store raised or produced nothing: %s" % (item.get("err"),)
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        return None, "record is not a list of lines"
    if item.get("sig") != _sig(list(lines)):
        return None, "the script that ran is not the script we asked for"
    return got, None


def _record(item, lines):
    got, why = _usable(item, lines)
    if why is not None:
        pytest.fail(why)
    return got


# --- the sealed side must agree with itself before it judges anything ----------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.run(cases.ops(name)) == truth[name], name


# --- hand cases: one per graded decision, plus the must-still-work side ---------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    assert _record(produced[name], cases.CASES[name]) == truth[name]


# --- the scripts that ship in the agent's tree ----------------------------------------

@pytest.mark.parametrize("name", cases.SHIPPED)
def test_shipped_script(produced, name):
    """The brief says the scripts in the tree are graded, so they are, against the model."""
    lines = cases.shipped(name)
    item = produced.get("runs-" + name)
    assert item is not None, "no result for the shipped script %s" % name
    assert _record(item, lines) == model.run([tuple(ln.split()) for ln in lines])


# --- nonce scripts, generated after the agent finished --------------------------------

def _nonce():
    return NONCE.read_text(encoding="utf-8").strip(), int(PER.read_text(encoding="utf-8").strip())


def test_every_nonce_script_matches(produced):
    seed, per = _nonce()
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 200, "nonce population too small: %d" % len(wanted)
    bad = []
    for fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        got, why = _usable(item, lines)
        if why is not None:
            bad.append((name, why))
            continue
        if got != model.run(gen.ops(lines)):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce scripts wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_families_all_present(produced):
    seed, per = _nonce()
    fams = set(fam for fam, _, _ in gen.programs(seed, per))
    assert fams == set(nm for nm, _ in gen.FAMILIES) | {"wide"}
