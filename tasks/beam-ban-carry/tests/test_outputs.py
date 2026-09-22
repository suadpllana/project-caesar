"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/bm/`: `sc.py` is the scoring table, `rep.py`
holds a beam's sequence and the spans it and the kept set refuse, `keep.py` is the kept set,
`pick.py` ranks and selects, `walk.py` drives a request and `halt.py` decides when the search
ends. Everything else in the tree is the verifier's own pristine copy, so only those six can
change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a continuation exists only where the table has a row for the beam's last token and that
     token, and the stop token is never one of them
  2  a beam closes when it has emitted at least S tokens and the table has a stop row for its
     last token; the stop row's score counts toward the hypothesis and its length does not
  3  closing leaves the beam standing, and closing is settled for every beam in slot order
     before any candidate of that step is refused or ranked
  4  a hypothesis is ordered by its score less the penalty times its length, ties to the
     shorter and then to the earlier; the kept set holds at most H and gives up its worst
  5  a member of the kept set lends its spans, and a candidate whose span a member holds is
     refused
  6  a member that leaves takes its bans with it, and a span another member still holds stays
     refused
  7  a candidate is refused when its span already occurs in its own sequence, prompt included
  8  candidates rank by score descending, ties to the smaller parent slot then the smaller
     token, and are taken down that order keeping one per final token, at most W of them
  9  the search halts `dry` with nothing taken, `cap` at the ceiling, and `bound` when the kept
     set is full and no beam's reach can pass its worst member
 10  the printed form: `ask`, then `shut` and `gone` as they happen, then `halt`, then the kept
     set as `hyp` lines best first, and nothing else

Implementation choice, and not graded: how a beam's spans are held, whether its sequence is a
tuple or a link to its parent, how the kept set is ordered internally, and any internal naming.
Not a free choice, and not asserted here either: a beam's spans and a member's spans cannot be
rebuilt from tokens whenever they are wanted, which the execution limit on the worker decides
rather than any assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Nonce programs
are generated here, after the agent has finished, and checked against the sealed model. The
model must also reproduce `gt.json` exactly, so a drifted model cannot quietly redefine
correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("BBC_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("BBC_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("BBC_LOGS", "/logs/verifier"))


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
        pytest.fail("the stage raised or produced nothing: %s" % (item.get("err"),))
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


# --- the enumerated programs: one per wrong reading, plus the ordinary side of each fence

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(produced, truth, name):
    assert name in produced, "no result for hand case %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.prog(name)), "hand program was altered: %s" % name
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
    assert fams == {f for f, _big in gen.FAMILIES}
