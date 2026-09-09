"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/link/`: `walk.py` brings a unit up, `view.py` says
which publications a caller may read, `pick.py` answers a name, `site.py` decides what a call
does, `want.py` says whether a live unit has to stay, and `drop.py` releases a hold and sweeps.
Everything else in the tree is the verifier's own pristine copy, so only those six can change
what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  the order units come up in: what a unit names first, in declaration order, whether it is a
     dependency or an ordering edge, one that is already up or part way up skipped
  2  publication and startup interleaved per unit, so a startup call sees the order as far as it
     has been built and no further
  3  a unit coming up has settled nothing, whatever the record it is handed carries from a
     previous life
  4  `act` publishes into no scope, `open` publishes one activation into a single fresh scope,
     and a call reaches a publication only when it is public or sits in the caller's own scope
  5  `act` on a unit that is up in a scope makes that publication public where it stands - same
     publication, same place in the order, visible to everyone from then on
  6  which publisher answers a name: the first in publication order that the caller can see, a
     fallback publication counting exactly like any other
  7  a call that finds no publisher settles nothing, so a later call can still settle, against a
     unit that came up or became visible in between
  8  a settled use is never resolved again
  9  a settled use that reaches a publication which has gone answers dead, and a unit of the same
     name coming back does not repair it
 10  a live unit stays while it holds a hold of its own or any live unit names it as a
     dependency; an ordering edge keeps nothing
 11  the sweep after a release: the last unwanted unit in publication order, applied before the
     next is chosen, repeated until nothing unwanted is left
 12  a call from a unit that is not up is not an event
 13  bringing up a unit that is already up adds a hold and leaves its publication where it is

Implementation choice, and not graded: how the dependency walk is carried (the reference
recurses, the model runs an explicit stack), how a publication is told apart from the one before
it, what the resolution buckets and the retention ledger are made of, and any internal naming.
Not a free choice, and not asserted here either: neither the answer to a name nor the next
candidate for retirement can be found by scanning, which the execution limit on the worker
decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs
are generated here, after the agent has finished, and checked against the sealed model. The
model must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("PSO_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("PSO_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("PSO_LOGS", "/logs/verifier"))


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
        pytest.fail("the host raised or produced nothing: %s" % (item.get("err"),))
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
    assert fams == {f for f, _small in gen.FAMILIES}
