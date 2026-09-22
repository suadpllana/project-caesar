"""Grading. Runs as root, after the worker, and never executes a line of submitted code.

FROZEN CONTRACT
---------------
The agent supplies three files under `/app/rs/`: `cmp.py`, `join.py` and `keep.py`. The rest
of the tree is the verifier's pristine copy, so only those three can change what a program
prints. `/app/run_ask.py` loads a program, calls `report(store)` in `rs/keep.py` and prints what
it returns; the printer sorts the rows and prints each once.

Graded, and settled the same way by the sealed model, the reference and a brute force over
every filling:

  1  one label is one value everywhere in a program
  2  a label's allowed values are those every column it sits in allows
  3  a filling gives every label an allowed value, and two labels may share one
  4  an atom matches a row on equal constants, one value per variable and `_` for anything,
     and an integer never equals a symbol
  5  `X != c` holds when the value bound to X is not c
  6  a query returns the union of what its rules derive
  7  the report holds each row of constants the query returns under every filling, once;
     a row carrying a label never appears
  8  queries print in the order of their first rule, rows sorted with integers first
  9  the whole graded set, with programs of about nineteen thousand rows and eight thousand
     labels, finishes inside the worker's wall clock, which test.sh enforces

Implementation choice, not graded: how labels are classified, join order, how conditions are
held, how a row's conditions are split and searched, and internal naming. Not free, and not
asserted here either: trying every filling, or checking a row's conditions without splitting
them into groups that share no label, cannot finish the wide and flag families in time.

Hand cases are compared with `gt.json`, frozen before this file was written. Programs generated
from a seed drawn after the agent finished are compared with the sealed model, and the model
must first reproduce `gt.json` exactly, so a model that had drifted cannot redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("BFS_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("BFS_WORK", "/work"))
LOGS = pathlib.Path(os.environ.get("BFS_LOGS", "/logs/verifier"))
RUNS = WORK / "runs.json"
GT = pathlib.Path(SEAL) / "gt.json"


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def read_runs():
    """The worker ran submitted code, so every byte of this file is hostile input."""
    try:
        raw = json.loads(RUNS.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("the worker left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the worker record is not a list")
    by = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            pytest.fail("a worker record entry is malformed")
        by[item["name"]] = item
    return by


def printed(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the program raised or printed nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of printed lines")
    return got


@pytest.fixture(scope="module")
def runs():
    return read_runs()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nonce():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side agrees with itself before it judges anything --------------------------

def test_model_reproduces_frozen_answers(frozen):
    """gt.json was frozen from the model. If the two have drifted, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- enumerated programs: one per graded decision, and both sides of each fence ------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(runs, frozen, name):
    assert name in runs, "no record for hand case %s" % name
    item = runs[name]
    assert item.get("sig") == digest(cases.prog(name)), "hand program altered: %s" % name
    assert printed(item) == frozen[name]


# --- programs generated from a seed drawn after the agent's container was gone -------------

def test_every_generated_program_matches(runs, nonce):
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "generated population too small: %d" % len(wanted)
    wrong = []
    for fam, name, lines in wanted:
        item = runs.get(name)
        if item is None:
            wrong.append((name, "missing"))
            continue
        if item.get("sig") != digest(lines):
            wrong.append((name, "program altered"))
            continue
        got = item.get("got")
        if got != model.expect(lines):
            wrong.append((name, "report differs" if got is not None else item.get("err")))
    assert not wrong, "%d of %d generated programs wrong, first: %s" % (
        len(wrong), len(wanted), wrong[:4])


def test_every_family_is_graded(runs, nonce):
    seed, per = nonce
    fams = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert fams == {f for f, _big in gen.FAMILIES}
    assert {runs[n]["fam"] for _f, n, _l in gen.programs(seed, per) if n in runs} == fams
