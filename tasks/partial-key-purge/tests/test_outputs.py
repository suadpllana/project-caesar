"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies five files under `/app/db/`: `match.py`, `drop.py`, `clear.py`, `hold.py`
and `audit.py`. Everything else in the tree - the driver `run_db.py`, the reader `parse.py`, the
store `rows.py`, the printer `say.py` - is the verifier's own pristine copy, so only those five
can change what a script prints. Each graded script runs in a fresh interpreter.

Graded, and settled the same way by two implementations written apart:

  1  a reference is inert for a row whose referencing columns are all null, and under `simple`
     also for a row with any of them null; under `full` a row with some but not all of them null
     is broken; otherwise the row matches every row of the key's table whose key columns equal
     its non-null referencing columns, pairwise in order, and a row can match itself
  2  a row loses a reference when it matched at least one row through it before the statement
     and every row it matched is removed; matching reads the values from before the statement
  3  the removed set is the rows the statement names and every row that loses a cascade
     reference, and nothing else: the smallest such set, so rows that match only one another
     keep each other and a row that matches itself keeps itself
  4  a row that is not removed and loses a setnull reference has that reference's listed
     columns, or all of its columns when none are listed, set to null; clearing never changes
     the removed set, and such a row counts as cleared even when the columns already held null
  5  the statement is refused when any row, removed or not, loses a restrict reference
  6  it is also refused when, after the removal and the clearing, a remaining row is broken, or
     matches no remaining row through a reference that is not inert for it (both rows with
     their values after clearing), or holds a null in a column of a key
  7  a refusal names the failing key or reference declared first in the script, and the
     smallest id of a row that fails it, and changes nothing
  8  `ok <removed> <cleared>`, `refused <name> <id>`, a dump line per row in id order, and an
     audit line per row, tables in declaration order and ids ascending, each giving what a
     lone delete of that row would remove and clear and whether it would be refused, counts
     included when it would be; the audit changes nothing
  9  the whole graded set, one fresh interpreter per script, inside the worker's wall clock

Implementation choice, and not graded: how match sets are indexed, how the removed set is
grown, how the audit is computed (the reference builds an ownership tree top down with binary
lifting and counts unions of chains by inclusion and exclusion; the model runs iterative
dominators over reverse postorder with an Euler tour; a variant replays small stores), and any
internal naming. Not a free choice, and not asserted here either: the audit cannot replay a
delete per row on the deep stores, which the wall clock on the worker decides rather than any
assertion in this file.

Hand scripts are checked against `gt.json`, frozen before this file was written. Nonce scripts
are generated before the worker starts, answered by the sealed model, and regenerated here from
the same nonce to confirm the answers belong to them. The model must also reproduce `gt.json`
exactly, so a drifted model cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

SEAL = os.environ.get("PKP_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

TESTS = pathlib.Path(os.environ.get("PKP_TESTS", "/tests"))
WORK = pathlib.Path(os.environ.get("PKP_WORK", "/work"))
LOGS = pathlib.Path(os.environ.get("PKP_LOGS", "/logs/verifier"))
OUT = WORK / "run" / "worker_out.jsonl"
GT = pathlib.Path(SEAL) / "gt.json"
ANSWERS = pathlib.Path(SEAL) / "expected.json"
CASES = cases.ORDER


def _sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _case(name):
    return cases.CASES[name]


def _load():
    """Every byte here came from a process that ran agent code. Parse it defensively."""
    try:
        raw = [json.loads(line) for line in OUT.read_text(encoding="utf-8").splitlines()
               if line.strip()]
    except Exception as exc:
        pytest.fail("worker produced no readable output: %s" % exc)
    by = {}
    for item in raw:
        if not isinstance(item, dict):
            pytest.fail("worker output entry is not an object")
        kind, name = item.get("kind"), item.get("name")
        if not isinstance(kind, str) or not isinstance(name, str):
            pytest.fail("worker output entry has no kind or name")
        by[(kind, name)] = item
    return by


def _lines(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the store raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of lines")
    return got


def _first_difference(got, want):
    for i, (a, b) in enumerate(zip(got, want)):
        if a != b:
            return "line %d: got %r, want %r" % (i + 1, a, b)
    return "got %d lines, want %d" % (len(got), len(want))


@pytest.fixture(scope="module")
def produced():
    return _load()


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def answers():
    return json.loads(ANSWERS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def nonce():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side has to agree with itself before it judges anything ---------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(truth) == CASES
    for name in CASES:
        assert model.expect(_case(name)) == truth[name], name


def test_answers_belong_to_this_nonce(answers, nonce):
    """The answers were written before the worker ran; regenerate the scripts and compare."""
    seed, per = nonce
    wanted = gen.programs(seed, per)
    assert sorted(answers) == sorted(name for _f, name, _t in wanted)
    for fam, name, text in wanted:
        assert answers[name]["fam"] == fam
        assert answers[name]["sig"] == _sig(text), name


# --- the enumerated scripts: one per graded decision, plus both sides of each fence ---

@pytest.mark.parametrize("name", CASES)
def test_hand_case(produced, truth, name):
    item = produced.get(("hand", name))
    assert item is not None, "no result for hand script %s" % name
    assert item.get("sig") == _sig(_case(name)), "hand script was altered: %s" % name
    got = _lines(item)
    assert got == truth[name], _first_difference(got, truth[name])


# --- scripts generated from a seed drawn after the agent's container was gone ----------

def test_every_nonce_script_matches(produced, answers):
    assert len(answers) >= 300, "nonce population too small: %d" % len(answers)
    bad = []
    for name, ans in sorted(answers.items()):
        item = produced.get(("nonce", name))
        if item is None:
            bad.append((name, "missing"))
            continue
        if item.get("sig") != ans["sig"]:
            bad.append((name, "script altered"))
            continue
        got = item.get("got")
        if got is None:
            bad.append((name, "raised: %s" % (item.get("err"),)))
        elif got != ans["want"]:
            bad.append((name, _first_difference(got, ans["want"])))
    assert not bad, "%d of %d nonce scripts wrong, first: %s" % (len(bad), len(answers), bad[:3])


def test_every_family_is_represented(answers):
    fams = {ans["fam"] for ans in answers.values()}
    assert fams == {f for f, _small in gen.FAMILIES}
    assert sum(1 for ans in answers.values() if ans["fam"] == "deep") == gen.DEEP
