"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/kv/`: `pool.py` is the pool of pages and the
take-back, `keep.py` is the reuse index and the walk, `live.py` is residency, `fill.py` is
the filling of a prompt, `turn.py` is the step, and `put.py` writes a token and completes a
page. Everything else in the tree is the verifier's own pristine copy, so only those six can
change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a fill holds every page of its prompt, reused or written, until the prompt is complete,
     and then lets go of everything outside residency
  2  residency is the pages of the first `A` tokens together with the pages of the last `S`,
     recomputed as the request grows
  3  a walk from the start of a prompt reuses pages until one of them is gone, and stops
     there whatever still sits below it
  4  a page whose last holder lets go is reusable when a walk can still reach it and goes
     back to the pool at once when it cannot
  5  a take-back takes the page released longest ago and takes with it every page below it:
     those nobody holds go back to the pool, those somebody holds go out of reach for good
  6  a page comes from the lowest free page, failing that a take-back, failing that a
     preemption, and a fill asks for one page at a time
  7  a preemption takes the request that became resident most recently, or the one that
     asked when none is resident, discards its progress and ends the step
  8  a page completing onto tokens that already sit below the same page is handed back and
     the one already there is taken instead
  9  a step decodes one token for each resident request in residency order and then fills
     waiting prompts in arrival order, inside the budget, stopping at the first prompt that
     cannot reach a page boundary; what a walk reuses costs no budget
 10  a request that finishes, is cancelled or is preempted lets go of everything it holds,
     in the order of the tokens those pages carry

Implementation choice, and not graded: how the pool, the index and residency are held,
whether the reusable order is an ordered mapping or a heap of stamps, whether the strand of
a take-back is walked depth or breadth first, where the tokens of a page live, and any
internal naming. Not a free choice, and not asserted here either: neither residency, nor the
oldest release, nor the strand can be recomputed by sweeping everything each time, which the
execution limit on the worker decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce
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

SEAL = os.environ.get("PWR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("PWR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("PWR_LOGS", "/logs/verifier"))


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
    assert len(wanted) >= 390, "nonce population too small: %d" % len(wanted)
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
