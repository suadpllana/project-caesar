"""Grading. Root, and it never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies six files under `/app/train/`: `pick.py` tracks how much of each
open document a step consumed and names the ones that settled in it, `fold.py`
evaluates one settled document's objective and gradient, `norm.py` averages the
settled documents and clips, `turn.py` decides whether a step is taken and moves
the parameters, momentum, average and schedule, `again.py` decides which settled
documents are requeued, and `keep.py` says what a checkpoint carries. Everything
else in the tree is the verifier's own pristine copy, so only those six can change
what a run prints.

Graded, and settled the same way by two implementations written apart:
  1  which documents settle in a step - the ones whose last token it consumed -
     and in the order their last tokens stand in the stream, masked documents
     consumed but never settling
  2  the objective of a settled document, evaluated once, over all of its tokens,
     at the parameters in force for the settling step, whatever the parameters
     were when its earlier tokens were consumed
  3  the divisor: the documents that settled, never the micro-batches the step was
     split into nor the tokens it consumed, which is what makes the trace
     independent of the accumulation and worker layout
  4  the reported gradient length, taken before clipping, and the clip applied to
     the step's own gradient rather than to the accumulated momentum
  5  a step that settles nothing is held: nothing moves and it does not count
  6  the learning rate and the average's decay, keyed to steps taken, the rate read
     before the count advances and the decay after the update
  7  the requeue decision, per document, on that document's own loss, with the
     allowance counted along the chain of requeues rather than by name
  8  the requeued occurrence joining the tail of the pending stream, so what the
     next steps settle depends on this decision
  9  what a checkpoint carries: parameters, momentum, average, steps taken, the
     consumption of every open document and every pending allowance - and not the
     batch layout, which is configuration

Implementation choice, never graded: how the open documents are stored, whether the
objective is computed with or without the customary shift by the largest score,
the container types the policy returns, and any internal naming. The record is
compared exactly, line for line, on every script.

Hand cases are checked against `gt.json`, frozen before this file was written;
nonce scripts are generated here, after the agent has finished, and checked
against the sealed model. `gt.json` and the model must also agree with each other
on every hand case, so a drifted model cannot quietly redefine correct.
"""
import json
import os
import pathlib
import stat

import pytest

import cases
import gen
import model

HERE = pathlib.Path(__file__).resolve().parent
WORK = pathlib.Path(os.environ.get("SCS_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = HERE / "gt.json"
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


def _record(item):
    got = item.get("got")
    if got is None:
        pytest.fail("trainer raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("record is not a list of lines")
    return got


# --- the sealed side must agree with itself before it judges anything ----------

def test_sealed_side_is_out_of_the_sandbox():
    """In the image, nothing but root may read the model, the generator or the answers.

    The submitted trainer runs inside the worker under the sandbox uid, and that
    process has `/tests` on its import path. If this directory were readable it
    could import the model, compute the expected trace and hand it back. Skipped
    when the tests are being driven from somewhere other than the image, where
    there is no second uid for the mode bits to mean anything.
    """
    if str(HERE) != "/tests/seal":
        pytest.skip("not running from the verifier image")
    mode = stat.S_IMODE(HERE.stat().st_mode)
    assert not mode & (stat.S_IRWXG | stat.S_IRWXO), oct(mode)
    for name in ("model.py", "gen.py", "cases.py", "gt.json"):
        m = stat.S_IMODE((HERE / name).stat().st_mode)
        assert not m & (stat.S_IRWXG | stat.S_IRWXO), (name, oct(m))


def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.ops(name)) == truth[name], name


# --- hand cases: one per graded decision, plus the must-still-work side --------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item["lines"] == cases.ops(name), "hand script was altered: %s" % name
    assert _record(item) == truth[name]


# --- nonce scripts, generated after the agent finished -------------------------

def _nonce():
    return NONCE.read_text(encoding="utf-8").strip(), int(PER.read_text(encoding="utf-8").strip())


def test_every_nonce_script_matches(produced):
    seed, per = _nonce()
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "nonce population too small: %d" % len(wanted)
    bad = []
    for fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item["lines"] != list(lines):
            bad.append((name, "script altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "record differs"))
    assert not bad, "%d of %d nonce scripts wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_families_all_present(produced):
    """Every shaped family has to be in the population that was actually graded."""
    seed, per = _nonce()
    fams = set(fam for fam, _, _ in gen.programs(seed, per))
    assert fams == set(f for f, _ in gen.FAMILIES)
