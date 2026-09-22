"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six reader modules under `/app/sr/`: `look.py`, `know.py`,
`watch.py`, `unit.py`, `line.py` and `voice.py`. Everything else in the tree - the page model,
the script parser, the log writer, the runner and the sample pages - is the verifier's own
pristine copy, so only those six can change what a page prints, and a file put beside them is
never collected.

Graded, and settled the same way by two implementations written apart (the sealed model in
seal/model.py and the reference) and by a third that recomputes the page on every tick:

   1  a node is exposed when attached and nothing at or above it carries `hidden` (any value)
      or `aria-hidden="true"`; `aria-hidden="false"` never undoes an ancestor
   2  a node's region is the nearest element at or above it carrying aria-live, `off`
      included; a region voices while exposed and polite or assertive
   3  belief is kept per (region, text node) with the anchor the node had when it was written,
      and moves only when an utterance finishes, by absorption, or at load
   4  a difference is the current value against what the reader will believe once the playing
      utterance finishes, by presence and text: addition, removal, text change; a move inside
      a region is none
   5  a difference that cannot be voiced, or whose kind the region element's own aria-relevant
      does not name, is absorbed and released from the playing utterance
   6  a difference is held while aria-busy="true" is on its path from the node's parent - for a
      removal, from its anchor when that is still exposed in the region - up to the region
   7  a difference keeps the age of the tick that first saw it; a cut hands carried ones back
      at the age they had
   8  a free reader takes the oldest unheld difference, assertive before polite, ties to the
      lower text node id then region id
   9  the unit is the first element from the start up to the region whose aria-atomic is true
      or false - true is a unit, false or none is not; a unit reads its exposed text now and
      carries every unheld difference whose unit it is; an empty unit is believed at once
  10  an utterance of w words started at t finishes at t + w; an unheld assertive difference
      cuts a playing polite utterance and nothing cuts an assertive one
  11  each tick applies its ops, then finishes, observes, cuts and selects, and prints
      `<t> polite|assertive <text>` per start and `<t> cut` per cut

Implementation choice, and not graded: how belief, the carried layer, the waiting line and the
holds are stored, whether exposure and regions are cached or walked, and any internal naming.
Not a free choice, and not asserted here either: neither a recompute of the whole page on every
tick nor a rescan of every waiting difference at every selection finishes the wide and held
families, which the execution limit on the worker decides rather than any assertion in this
file.

Hand pages are checked against `gt.json`, frozen from the model only once the model, the
reference and the recompute-everything reader printed the same log for every one of them. Nonce
pages are generated here, after the agent has finished, and checked against the sealed model. The
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

SEAL = os.environ.get("HCR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("HCR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("HCR_LOGS", "/logs/verifier"))


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


def _log(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the reader raised or produced nothing: %s" % (item.get("err"),))
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


# --- the enumerated pages: one per graded decision, plus both sides of each fence -------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand page %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.prog(name)), "hand page was altered: %s" % name
    assert _log(item) == truth[name]


# --- pages generated from a seed drawn after the agent's container was gone ------------

def test_every_nonce_program_matches(produced, nonce):
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 270, "nonce population too small: %d" % len(wanted)
    bad = []
    for _fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _sig(lines):
            bad.append((name, "page altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "log differs"))
    assert not bad, "%d of %d nonce pages wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
