"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/cfg/`: `pile.py` is the store, `past.py` is the
plan's history and the stop a question is answered at, `made.py` is what a definition is and
what a copy hands on, `roll.py` applies one layer, `work.py` evaluates a definition, and
`ans.py` answers the two queries. Everything else in the tree - the driver, the plan parser
and the trace writer - is the verifier's own pristine copy, so only those six can change what
a plan prints.

Graded, and settled the same way by two implementations written apart:

  1  a layer's entries apply in the order written, a later one replacing an earlier one
  2  a guard is answered against the plan before its whole layer, not against the earlier
     entries of that layer
  3  a guard is answered as if the plan had stopped at its own layer
  4  a query naming a layer is answered as if the plan had stopped there, values included
  5  a removal takes the path named and everything under it
  6  a copy clears the destination before it carries anything, and fixes its source paths
     before it writes any of them
  7  a copy carries definitions and not the values they had, so a carried path goes on
     following the same expression
  8  a carried definition keeps the layer that wrote it, for its backward references and for
     the layer a query reports
  9  a value that requires itself at the same stop is circular, and a definition naming its
     own path backwards is not
 10  absent and circular are distinct answers, and the left side of an expression decides
     which one comes out
 11  a count reports only the paths holding a definition at or under the prefix
 12  a conditional tests whether the path holds a definition, evaluates only the side it
     chooses, and is answered at the stop of the question

Implementation choice, and not graded: how the store is held, whether a copy grafts a node or
is recorded as a redirect, what the memo is keyed on, whether a guard is answered as its entry
comes up or in a pass over the layer, and any internal naming. Not a free choice, and not
asserted here either: neither the number of defined paths under a prefix nor the answer to a
repeated question may be recomputed from scratch, which the execution limit on the worker
decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce plans are
generated here, after the agent's container is gone, and checked against the sealed model. The
model must also reproduce `gt.json` exactly, so a model that had drifted cannot quietly
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
