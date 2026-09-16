"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/fld/`: `keep.py` holds the kept results, the preview
layer and the pin table, `look.py` decides whether a kept result still stands, `make.py` evaluates
a body and records what it read, `need.py` is the demand, `feed.py` publishes a value to a source,
and `hold.py` opens and closes a preview block. Everything else in the tree is the verifier's own
pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a demanded derived field with no kept result is evaluated; a source is never evaluated
  2  a kept result is checked by demanding the fields its last evaluation read, in that order
  3  the check stops at the first read whose value differs, and the rest are never demanded
  4  a check in which every read returns what it returned before keeps the value and prints
     nothing
  5  an evaluation records the reads it took, in order and with repeats, replacing the last record
  6  a branching form reads the guard and only the arm it takes
  7  `run` is written when an evaluation finishes; `ask` writes `val`; nothing else is written
  8  publishing to a source the value it already carries changes nothing at all
  9  inside a preview block the previewed source reads as the previewed value, results computed
     there belong to the layer, and the kept results are untouched
 10  the layer outlives the block: the same value published to that source installs it, a
     different value discards it, another block discards it, and any other source leaves it
 11  an installed result is checked like any other
 12  a pinned field stands at the value it was pinned at, is never evaluated until it is freed,
     and pinning demands the field first

Implementation choice, and not graded: how the kept results are held, whether the layer is a
second dict or a copy-on-write map, whether a repeated read is recorded twice or once, where the
pin table lives, and any internal naming. Not a free choice, and not asserted here either: neither
the layer nor the settling of a field within one question may cost the size of the whole graph,
which the execution limit on the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs are
generated here, after the agent has finished, and checked against the sealed model. The model must
also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("TKA_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("TKA_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("TKA_LOGS", "/logs/verifier"))


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
    assert len(wanted) >= 350, "nonce population too small: %d" % len(wanted)
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
