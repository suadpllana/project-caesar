"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/bind/`: `hold.py` keeps parts and holds claim
keys, `want.py` is the name table and the wanted set, `pull.py` decides which member a bundle
gives up, `place.py` places the names nothing gives, `prune.py` is reachability and the image,
and `wire.py` drives the input list and answers the queries. Everything else in the tree is
the verifier's own pristine copy, so only those six can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a part whose claim key is already held is dropped, and neither its gives nor its uses enter
  2  a part of a unit named on the input list takes a held key back from a part that came out
     of a bundle, and the displaced part's gives and uses leave before the new one enters
  3  a key held by a unit off the input list never changes hands, and a member never takes one
  4  a name is wanted while a kept part uses it strongly or a loaded unit spares it and no kept
     part gives it strongly; a weak give settles nothing and a weak use wants nothing
  5  a bundle gives up its first member in member order that strongly gives a wanted name, and
     is scanned again from the first member after every take
  6  a group of bundles is scanned again from its first bundle while a pass takes anything, and
     the input list itself is walked once
  7  a take is never unsaid, and a member already loaded is passed over rather than taken
  8  the strong gives of a name stand in arrival order, the first binds, a second reports and
     changes nothing, and the next one binds silently when the first leaves
  9  a name with no strong give stands on the first weak one
 10  a name nothing gives and something spares is placed at the largest size spared, against
     the first unit in load order that spared it at that size
 11  the prune keeps what the roots and the held parts reach through strong uses, and a name
     whose part it drops binds to nothing
 12  the image is the surviving parts and the placed names they reach, by count and by bytes

Implementation choice, and not graded: how the kept parts are held, whether the wanted set is
carried or read off the parts, whether a bundle is indexed by name or walked, how a displaced
part is found, and any internal naming. Not a free choice, and not asserted here either:
neither the member a bundle gives up next, nor the wanted set, nor reachability can be found by
walking everything each time, which the execution limit on the worker decides rather than any
assertion in this file.

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

SEAL = os.environ.get("BCP_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("BCP_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("BCP_LOGS", "/logs/verifier"))


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


# --- programs generated here, from a seed drawn after the agent's container was gone ---

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
