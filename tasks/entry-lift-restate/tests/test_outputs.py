"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the seven files under `/app/cf/`: `book.py` holds the journal and which
changes stand, `sect.py` the board and the climb that reads a name in a section, `step.py`
what one entry does, `gate.py` the `if` condition, `wake.py` the sleeping entries, `walk.py`
the pass and the settle, and `tell.py` what is printed. Everything else in the tree is the
verifier's own pristine copy, so only those seven can change what a program prints, and a new
file put beside them is never collected at all.

Graded, and settled the same way by two implementations written apart:

  1  a read takes the value in the slot; a masked slot ends the climb with nothing found; an
     empty one sends the climb to the section this one links to; a section reached twice ends it
  2  `add` reads its name through that climb and writes into the section the walk is carrying
  3  `add` does nothing at all when the read finds nothing
  4  `clr` empties a slot so the climb goes on where `cut` masks it so the climb stops
  5  every entry acts in the section the walk carries when it reaches it, starting at 0 in
     every pass
  6  an entry whose `if` condition is not met does nothing at all, section and link entries
     included
  7  every settle starts from a clean board with every `once` entry asleep again
  8  between passes the lowest-numbered sleeping entry whose condition is met wakes, one per pass
  9  that condition is read in the section the finished pass gave its position, over the board
     that pass left
 10  a woken entry is applied on the passes after without being tested again
 11  a lifted change takes no part in any pass, moves nothing, and can never wake
 12  what `get` and `all` print, the three counts and the order of the detail lines

Implementation choice, and not graded: how the board is held, whether the writes of a slot are
one list or several, whether an entry's lookups are remembered by key or by name, and any
internal naming. Not a free choice, and not asserted here either: a resolver cannot answer
every question by walking the whole journal again, which the execution limit on the worker
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

SEAL = os.environ.get("ELR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("ELR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("ELR_LOGS", "/logs/verifier"))


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
        pytest.fail("the resolver raised or produced nothing: %s" % (item.get("err"),))
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


# --- the enumerated programs: one per graded decision, plus both sides of each fence ---

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
    assert fams == set(gen.FAMILIES)
