"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the five files under `/app/jl/` that the brief names: `table.py` (the lock
table and what the service does with a request), `tally.py` (the running totals, the digest
rule and a lost span's slack), `span.py` (the fillings of one lost span), `seek.py` (the whole
journal; the frozen driver calls its `mend(journal)`) and `walk.py` (what every account agrees
on in one span). Everything else is the verifier's own pristine copy, so only those five can
change what `/app/mend.py` prints for a journal.

Graded, and settled the same way by two implementations written apart (the reference, a
layered forward pass pruned by a backward one; the sealed model, a memoized completion test):

  1  acq takes a free lock at depth 1 (grant), deepens one the session holds (again), or
     queues behind another holder (wait); rel is the holder's, lowers depth, and at zero
     hands the lock to the first waiter at depth 1 (pass) or frees it (free), else keeps it
  2  a waiting session sends nothing; a heartbeat needs a held lock and changes nothing
  3  totals start at zero on an empty table; a pass is a grant
  4  a digest is written right after any entry that brings grants to a multiple of the
     period, and nowhere else; it carries the holder fingerprint
  5  an audit carries every total and the whole-table fingerprint; one taken during a lost
     span may sit anywhere among the lost entries, in the order listed
  6  an account fills every lost span so that the whole journal replays: evidence after a
     span, and later spans, constrain it as much as evidence inside it
  7  a span prints the entries every account agrees on from its start, then the candidates
     at the first point accounts part, `-` where an account ends the span, in text order

Implementation choice, not graded: how tables and totals are represented, whether the
journal is settled forward-then-backward or by memoized search, and any internal naming. Not
a free choice either, and not asserted here: every account cannot be enumerated at the busy
family's size, which the worker's wall clock decides rather than any assertion in this file.

Hand journals are checked against `seal/gt.json`, frozen from the sealed model when the hand
set was built.
Generated journals are drawn inside the verifier after the agent has finished and checked
against the sealed model, which must also reproduce `gt.json` exactly, so a drifted model
cannot quietly redefine correct.
"""
import hashlib
import json
import os
import pathlib
import random
import sys

import pytest

SEAL = os.environ.get("JGM_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

PRISTINE = pathlib.Path(os.environ.get("JGM_TESTS", "/tests")) / "pristine"
WORK = pathlib.Path(os.environ.get("JGM_WORK", "/work"))
OUT = WORK / "worker_out.json"
LOGS = pathlib.Path(os.environ.get("JGM_LOGS", "/logs/verifier"))
GT = pathlib.Path(SEAL) / "gt.json"


def _sig(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _lines(item):
    got = item.get("got")
    if got is None:
        pytest.fail("the tool raised or produced nothing: %s" % (item.get("err"),))
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the record is not a list of lines")
    return got


@pytest.fixture(scope="module")
def produced():
    return _load()


@pytest.fixture(scope="module")
def graded():
    """The root-only set prep.py wrote before any submitted code ran."""
    return json.loads((LOGS / "set.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


# --- the sealed side has to agree with itself before it judges anything ---------------------

def test_frozen_answers_match_the_model(truth):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.text(name)) == truth[name], name


def test_model_fingerprints_match_the_frozen_code():
    """The model computes fingerprints itself; they must be the frozen /app/jl/fp.py's."""
    sys.path.insert(0, str(PRISTINE))
    try:
        from jl import fp
    finally:
        sys.path.pop(0)
    rng = random.Random(7)
    for _ in range(200):
        n = rng.randint(1, 4)
        hs = tuple(rng.choice([None, 0, 1, 2, 3, 4]) for _ in range(n))
        ds = tuple(0 if h is None else rng.randint(1, 3) for h in hs)
        qs = tuple(() if h is None else tuple(rng.sample(range(5), rng.randint(0, 2)))
                   for h in hs)
        rows = tuple(zip(hs, ds, qs))
        assert fp.holders(rows) == model.holders_mark((hs, ds, qs))
        assert fp.whole(rows) == model.whole_mark((hs, ds, qs))


def test_the_set_is_whole(graded, truth):
    """The set the grader holds is the one prep.py built: every hand journal, and the right
    number from every family."""
    names = [g["name"] for g in graded]
    assert len(names) == len(set(names))
    hand = [g for g in graded if g["fam"] == "hand"]
    assert [g["name"] for g in hand] == list(cases.ORDER)
    for g in hand:
        assert g["want"] == truth[g["name"]], g["name"]
    fams = {}
    for g in graded:
        fams[g["fam"]] = fams.get(g["fam"], 0) + 1
    assert set(fams) == {"hand"} | set(gen.FAMILIES)
    assert fams["busy"] == gen.BUSY_COUNT
    assert sum(v for k, v in fams.items() if k != "hand") >= 300


# --- the hand journals: one per graded decision, plus the ordinary side of each fence --------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_journal(produced, truth, name):
    assert name in produced, "no result for hand journal %s" % name
    item = produced[name]
    assert item.get("sig") == _sig(cases.text(name)), "hand journal was altered: %s" % name
    assert _lines(item) == truth[name]


# --- journals generated from a seed drawn after the agent's container was gone ---------------

def test_every_generated_journal_matches(produced, graded):
    bad = []
    wanted = [g for g in graded if g["fam"] != "hand"]
    for g in wanted:
        item = produced.get(g["name"])
        if item is None:
            bad.append((g["name"], "missing"))
            continue
        if item.get("sig") != g["sig"]:
            bad.append((g["name"], "journal altered"))
            continue
        if item.get("got") != g["want"]:
            bad.append((g["name"], "printout differs"))
    assert not bad, "%d of %d generated journals wrong, first: %s" % (
        len(bad), len(wanted), bad[:4])
