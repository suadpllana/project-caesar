"""Stage two: grading. Runs as root, and executes nothing that was submitted.

FROZEN CONTRACT
---------------
The agent supplies the five files under `/app/pg/`: `fit.py` says what a page costs and when
it is over capacity or under the floor, `bound.py` derives the string that divides two pages
and puts it right when it has moved, `cut.py` decides where an over-capacity page is cut and
what is promoted, `join.py` joins an under-floor page, removes a page that holds nothing and
folds the root, and `step.py` orders the work inside one operation. Everything else under
`/app` is this verifier's own copy, so nothing but those five can change what a program
prints.

Graded, and settled the same way by two implementations written apart from each other:

  1  a page costs eight bytes, two more for every child it points at, the common prefix of
     its entries once, and two bytes and the remaining characters for each entry
  2  over capacity is strictly greater than the declared capacity; under the floor is
     strictly less than the declared floor, and the root is never joined
  3  the string between two pages is the shortest one greater than the greatest key to its
     left and not greater than the least key to its right
  4  that string is what it is at all times, so one is derived again whenever either of the
     two keys behind it moves, and a line is printed only when the value changes
  5  inside one operation the strings are put right before any page is measured
  6  an over-capacity page is cut at the position where the larger of the two pages, plus
     what the promoted string adds to the page above, is smallest; ties to the lower position
  7  each page from the leaf to the root is visited once, so a page that is still over
     capacity after being cut is left alone
  8  an under-floor page takes its right neighbour under the same page above when the joined
     page is within capacity, otherwise its left neighbour on the same test, otherwise it
     stays; an internal join brings the string that divided the pair down into the survivor
  9  a page that holds nothing leaves the tree, the left of the two strings beside it goes
     when it has a left neighbour, and only the last removal of a run puts a string right
 10  while the root is an internal page with one child, that child becomes the root

Implementation choice, and not graded: how a page's size is arrived at, whether entry lengths
are carried or summed on demand, whether the walk upward is a loop or recursion, how the page
holding a string is located, and any internal naming. Not a free choice and not asserted here
either: neither the common prefix of a page nor the page holding a string that has moved can
be found by sweeping the tree, which the execution limit on stage one decides rather than any
assertion in this file.

The enumerated programs are checked against `gt.json`, frozen before this file was written.
The generated programs are built here, from a seed drawn after the agent's container was
gone, and checked against the sealed model. The model has to reproduce `gt.json` as well, so
a model that has drifted cannot quietly redefine what correct means.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("PBC_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

YARD = pathlib.Path(os.environ.get("PBC_YARD", "/work"))
KEEP = pathlib.Path(os.environ.get("PBC_KEEP", "/logs/verifier"))
ROWS = YARD / "traces.json"
GT = pathlib.Path(SEAL) / "gt.json"


def _stamp(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _rows():
    """Every byte here came out of a process that ran submitted code. Parse it defensively."""
    try:
        raw = json.loads(ROWS.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("stage one left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the record is not a list")
    by = {}
    for row in raw:
        if not isinstance(row, dict):
            pytest.fail("a record entry is not an object")
        name = row.get("name")
        if not isinstance(name, str):
            pytest.fail("a record entry carries no name")
        by[name] = row
    return by


def _trace(row, name):
    got = row.get("got")
    if got is None:
        pytest.fail("%s: the layer raised or produced nothing: %s" % (name, row.get("err")))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("%s: the record is not a list of lines" % name)
    return got


@pytest.fixture(scope="module")
def produced():
    return _rows()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def draw():
    seed = int((KEEP / "seed").read_text(encoding="utf-8").strip(), 16)
    each = int((KEEP / "each").read_text(encoding="utf-8").strip())
    return seed, each


# --- the sealed side has to agree with itself before it judges anything ----------------

def test_the_model_still_reproduces_the_frozen_answers(frozen):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        body = "\n".join(cases.prog(name)) + "\n"
        assert model.trace(body) == frozen[name], name


# --- the enumerated programs: one per graded decision, and both sides of each fence ----

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_program(produced, frozen, name):
    assert name in produced, "no result for %s" % name
    row = produced[name]
    body = "\n".join(cases.prog(name)) + "\n"
    assert row.get("stamp") == _stamp(body), "%s: the program was altered" % name
    assert _trace(row, name) == frozen[name]


# --- programs built from a seed drawn after the agent's container was gone -------------

def test_every_generated_program(produced, draw):
    seed, each = draw
    wanted = gen.population(seed, each)
    assert len(wanted) >= 100, "generated population too small: %d" % len(wanted)
    wrong = []
    for name, body in wanted:
        row = produced.get(name)
        if row is None:
            wrong.append((name, "missing"))
            continue
        if row.get("stamp") != _stamp(body):
            wrong.append((name, "program altered"))
            continue
        if row.get("got") != model.trace(body):
            wrong.append((name, "trace differs"))
    assert not wrong, "%d of %d generated programs wrong, first: %s" % (
        len(wrong), len(wanted), wrong[:4])


def test_every_family_is_represented(produced, draw):
    seed, each = draw
    names = {name for name, _body in gen.population(seed, each)}
    for row in gen.FAMILIES:
        assert any(n.startswith(row[0] + "-") for n in names), row[0]
    for row in gen.SCALE:
        assert row[0] in names, row[0]
