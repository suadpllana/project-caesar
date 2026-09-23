"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/scn/`: `hdr.py` holds what a page header proves and
the interpolation the order is chosen on, `dct.py` decides what a chunk's dictionary speaks for
and what it charges, `live.py` carries the file's memory and one query's live rows and counts,
`pick.py` is the loop that chooses the next pair, `step.py` applies one condition to one chunk
page by page, and `proj.py` is the report pass. Everything else in the tree is the verifier's own
pristine copy, so only those six can change what a segment file prints.

Graded, and settled the same way by two implementations written apart:

  1  a column is chunks and a chunk is pages. A row's value in a column is its update when it
     has one and what its page holds otherwise; a deleted row is never alive. A page's header,
     a read of it and its chunk's dictionary describe the page as written.
  2  a page header whose exactness flag is off stands for a pair pushed out by the granularity
     less one; the two sound tests are what that pair and the null count prove about every row
     the page holds, and they settle the live rows that still take their value from the page
  3  live rows carrying an update are tested on their own value; a page with no live row that
     it still supplies is neither read nor consulted for
  4  a chunk's dictionary speaks only for its `i` pages and only for comparisons: no entry
     matching drops, every entry matching keeps a page holding no null, anything else reads
  5  the file has one memory: a page read or a dictionary consulted by any query is known to
     every later query, and `dc` and `rd` print only the first time
  6  a read of a page settles the exact count of every condition of the query over that column
     on that page, over the page as written; a page read before a query starts counts exactly
     from its start; a chunk's count is the sum over its pages
  7  the pair worked next is the one expected to leave the fewest rows alive - the smaller of
     the chunk's live rows and the condition's count on it; ties go to the condition written
     earlier, then to the lower chunk number
  8  the report pass wants a page only for live rows that take their value from it, pages in
     order, and answers it by a page already read, by its header (every row null, one value and
     no null, or the wanted rows being every row of the page, with its sum), by a one-entry
     dictionary on an `i` page with no null (charged), and by a read otherwise; columns in the
     order the query names them
  9  every query starts with every row not deleted alive

Implementation choice, and not graded: how the surviving rows are held, whether a chunk's live
count or a condition's count on it is kept or worked out again, how remembered pages and exact
counts are stored, whether the row-to-chunk map is an array or a search, and how the next pair
is found. Not a free choice, and not asserted here either: finding it by rescanning every
pending pair after every step does not fit the execution limit on the worker on the wide
family, which the limit decides rather than any assertion in this file.

Hand-written segment files are checked against `gt.json`.
The rest are built after the agent has finished, from a seed it never saw, and checked against
the sealed model. The model must also reproduce `gt.json` exactly, so a model that had drifted
cannot quietly redefine what correct means.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("SCP_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("SCP_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("SCP_LOGS", "/logs/verifier"))


def _mark(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _record():
    """Every byte here came from a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("the worker left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the worker's record is not a list")
    by = {}
    for item in raw:
        if not isinstance(item, dict):
            pytest.fail("an entry in the worker's record is not an object")
        name = item.get("name")
        if not isinstance(name, str):
            pytest.fail("an entry in the worker's record has no name")
        by[name] = item
    return by


def _lines(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the scan raised or printed nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("what the scan printed is not a list of lines")
    return got


@pytest.fixture(scope="module")
def scanned():
    return _record()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawn():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side has to agree with itself before it judges anything ---------------

def test_the_model_still_reproduces_the_frozen_answers(frozen):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the enumerated files: one per graded decision, plus the must-still-work side ------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(scanned, frozen, name):
    assert name in scanned, "no result for hand case %s" % name
    item = scanned[name]
    assert item.get("sig") == _mark(cases.prog(name)), "hand segment was altered: %s" % name
    assert _lines(item) == frozen[name]


# --- segment files built from a seed drawn after the agent's container was gone --------

def test_every_drawn_segment_matches(scanned, drawn):
    seed, per = drawn
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "the drawn population is too small: %d" % len(wanted)
    bad = []
    for _fam, name, lines in wanted:
        item = scanned.get(name)
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != _mark(lines):
            bad.append((name, "segment altered"))
            continue
        if item.get("got") != model.expect(lines):
            bad.append((name, "printed something else"))
    assert not bad, "%d of %d drawn segment files wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])


def test_every_family_is_represented(scanned, drawn):
    seed, per = drawn
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
