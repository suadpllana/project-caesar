"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five modules under `/app/store/`: `dev.py` hands out blocks and
takes them back, `hold.py` keeps the spans and the claims standing on them, `item.py` runs
the write path, `line.py` keeps the lines, the stamp tree and what a stamp and a drop do to
them, and `tally.py` answers what a line, and a line with everything stamped from it, is
charged. Everything else in the tree is the verifier's
own pristine copy, so only those five can change what a program prints.

Graded, and settled the same way by two implementations written apart:

  1  a request is met from the smallest free run that fits, the lowest of those on a tie
  2  a request no run fits takes the largest run whole, the lowest on a tie, and goes on
     with the rest; a request the free total cannot meet is refused and changes nothing
  3  a block is rewritten where it stands exactly when no claim but the one covering it
     stands on that block of its span - a second claim of the same item counts
  4  a span goes back to the free map only when no claim covers any part of it, and it goes
     back whole, merging with a free run on either side
  5  inside one write the replaced claims go first, so the spans they empty are back in the
     free map before the allocation runs and can be handed to that same write
  6  the room a write needs is checked against the free total its own release will produce
  7  one allocation is laid over the fresh stretches in item order, so a stretch can
     straddle two pieces and a piece can serve two stretches
  8  referenced space is the whole length of every span a line stands on, counted once
     however many claims it holds there
  9  exclusive space is the part of that no other line stands on
 10  a stamp puts a second line on every span the origin stands on, so the origin has no
     exclusive space left the moment it is stamped
 11  freed by dropping a set of lines is the spans whose whole standing set is inside it
 12  a share moves coverage without allocating, and a copy still standing keeps its span
 13  a refused command leaves the store exactly as it was
 14  a family's referenced space counts a span once however many members stand on it
 15  a family's exclusive space is the spans whose whole standing set lies inside the
     family - neither the sum of the members' exclusive space nor the origin's alone
 16  a stamp leaves the origin's family charge where it was while the origin's own
     exclusive space collapses
 17  a dropped line's stamps count as stamped from the line it came from
 18  a dropped line that came from none leaves its stamps standing alone
 19  a line outside the family standing on a span takes it out of the family's exclusive
     space and changes no member's referenced space
 20  a name made again after a drop is a new line standing alone

Implementation choice, and not graded: how the free runs are indexed, how an item's
coverage is stored (the reference keeps claims and splices them, the model keeps one entry
per block), where a claim is split, how the charges and the family summaries are carried
(the reference keeps a count per ancestor on each span, the model sorts the standing lines'
stamp paths), and any internal naming. Not a free choice, and not asserted here either:
neither the charges, nor the family questions, nor the best fit, nor the in-place test may
be answered by walking, which the execution limit on the worker decides rather than any
assertion in this file.

Hand cases are checked against `gt.json`, frozen before this file was written. Generated
programs are built here, after the agent has finished, and checked against the sealed
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

SEAL = os.environ.get("SCC_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("SCC_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("SCC_LOGS", "/logs/verifier"))


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
        pytest.fail("the store raised or produced nothing: %s" % (item.get("err"),))
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

def test_every_generated_program_matches(produced, nonce):
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "generated population too small: %d" % len(wanted)
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
    assert not bad, "%d of %d generated programs wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(produced, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _small in gen.FAMILIES}
