"""Trusted exact grading; this process never imports the submitted service.

The original twelve behavior groups remain checked by the retained hand plans. The added
map groups check definition relocation, pre-entry predecessor views, source selection after
clearing, chronological composition, aliases and distinct installation identity, later fresh
puts, guards, nested historical reads, and gone/loop evaluation order. Cases and frozen
answers document both sides of each fence. The independent model must reproduce every
frozen answer before it is used for generated plans.

Only the six declared modules are copied into the worker's pristine interpreter. Plan and
output signatures, complete population coverage, exact trace equality, worker success and
trusted grader success all contribute to the binary reward. The worker's record is untrusted.
Implementation structures are not inspected. The 60-second submitted batch checks that both
ordinary and mapped logical subtrees remain affordable at the disclosed scale.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("LGA_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("LGA_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("LGA_LOGS", "/logs/verifier"))


def _sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _trace(item, name):
    if item.get("code") != 0:
        pytest.fail("the driver did not return 0 on %s: %r" % (name, item.get("code")))
    got = item.get("got")
    if got is None:
        pytest.fail("the service raised or produced nothing on %s: %s" % (name, item.get("err")))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record for %s is not a list of lines" % name)
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
    scale = int((LOGS / "scale").read_text(encoding="utf-8").strip())
    return seed, per, scale


# --- the sealed side has to agree with itself before it judges anything ---------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.PLANS)
    for name in sorted(cases.PLANS):
        assert model.trace(cases.PLANS[name]) == truth[name], name


# --- the enumerated plans: one per graded decision, plus both sides of each fence ------

@pytest.mark.parametrize("name", sorted(cases.PLANS))
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.PLANS[name]), "hand plan was altered: %s" % name
    assert _trace(item, name) == truth[name]


# --- plans generated from a seed drawn after the agent's container was gone ------------

def test_every_nonce_plan_matches(produced, nonce):
    seed, per, scale = nonce
    wanted = gen.programs(seed, per, scale=scale)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for name, text in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _sig(text):
            bad.append((name, "plan altered"))
            continue
        if item.get("code") != 0 or item.get("got") != model.trace(text):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce plans wrong, first: %s" % (len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per, scale = nonce
    names = {n.rsplit("-", 1)[0] for n, _t in gen.programs(seed, per, scale=scale)}
    assert names == {f for f, _fn in gen.FAMS} | {f for f, _fn in gen.SCALE}
