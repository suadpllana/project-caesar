"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/mix/`: `deck.py` owns the manifest - who is in the
blend, what each weighs, and the counters that go back to zero when any of that changes;
`pick.py` says which source a draw goes to; `walk.py` moves one source's cursor and decides when
its cap is finished; `lay.py` says which draws of a step reach which rank and slot; `keep.py` is
the checkpoint; `turn.py` runs steps and answers a feed. Everything else in the tree is the
verifier's own pristine copy, so only those six can change what a script prints.

Graded, and settled the same way by two implementations written apart:

  1  a draw goes to the live source with the smallest counter over weight, the earlier declared
     source taking a tie
  2  every live source's counter goes back to 0 whenever the blend changes - a declaration, a
     reweighing whatever weight it names, or a departure - and a draw moves only the counter of
     the source it went to
  3  a draw takes the sample under the source's cursor in its current epoch's permutation and
     moves the cursor on, a cursor reaching the source's size starting the next epoch at 0
  4  a source with a cap leaves the blend instead of starting the epoch its cap numbers, at the
     draw that takes its last permitted sample and before any further draw
  5  `done` is printed at that moment, carrying the source, the step holding that draw, and the
     position of that draw inside the step
  6  draw i of a step goes to rank (i // micro) % ranks, slot i // (micro * ranks) and position
     i % micro, and the order the draws are taken in does not depend on any of the three
  7  a stop puts back the step, and the epoch, cursor and counter of every source the checkpoint
     holds; who is live and what they weigh is the manifest's and is not put back
  8  the counters a stop puts back stand only when the live sources and their weights are the
     ones the checkpoint was written under, and are all 0 when they are not
  9  a feed reports the step the run is about to take, changes nothing, and prints no `done`
     line for a departure inside that step
 10  a source declared since the checkpoint was written keeps its own epoch and cursor across a
     stop

Implementation choice, and not graded: how the manifest and the counters are held, whether a
step's draws are settled with a heap or by arithmetic, how a feed puts back what it touched,
whether permutations are cached, and any internal naming. Not a free choice, and not asserted
here either: neither the counters at an arbitrary draw nor the draw a capped source finishes on
can be reached by taking the draws one at a time, which the execution limit on the worker
decides rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce scripts are
generated here, after the agent has finished, and checked against the sealed model. The model
must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("BRR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("BRR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("BRR_LOGS", "/logs/verifier"))


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
        pytest.fail("the feed raised or produced nothing: %s" % (item.get("err"),))
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


# --- the enumerated scripts: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.ops(name)), "hand script was altered: %s" % name
    assert _trace(item) == truth[name]


# --- scripts generated from a seed drawn after the agent's container was gone ---------

def test_every_nonce_script_matches(produced, nonce):
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
            bad.append((name, "script altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce scripts wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
