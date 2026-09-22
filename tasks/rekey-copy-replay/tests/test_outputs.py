"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/reb/`: `walk.py` takes a chunk and moves the
cursor, `mark.py` records what journal position each chunk range was read at, `sift.py`
decides each journal entry, `place.py` puts a row on its new key and takes it off again,
`wait.py` holds the rows set aside for a key, and `tally.py` closes the books. Everything
else in the tree is the verifier's own pristine copy, so only those six can change what a
program prints.

Graded, and settled the same way by two implementations written apart:

  1  a chunk takes the smallest CHUNK source keys standing above the cursor as the source
     stands at that moment, and the cursor lands on the largest key taken
  2  a chunk that takes nothing leaves the cursor where it is and records no range
  3  a chunk that took something records the range it covered against the journal length
     standing at that moment
  4  an entry whose source key is above the cursor is dropped as ahead and never revisited
  5  an entry at or below the cursor whose position is at most the mark of the range covering
     its key is dropped as seen
  6  every other entry is applied, and every entry considered is consumed
  7  a row's new key is its first two fields, and a row whose first two fields are unchanged
     is updated where it stands
  8  a row that changes its new key leaves the key the rebuild holds for it
  9  a free new key is taken and a held one sets the arriving row aside
 10  a freed new key goes to the smallest source key set aside for it, and a row that was only
     set aside frees nothing when it leaves
 11  a delete reaches the row the rebuild holds, and a delete of a row it does not know is a
     miss
 12  the walk offers the keys it took in ascending order, by the same rules as a replay
 13  the closing line counts the rows holding a key, the rows set aside, and totals the third
     field over the rows holding a key only

Implementation choice, and not graded: how the source keys still to be walked are held, how
the chunk ranges are searched, whether the rows set aside are a heap with lazy removal or a
sorted list, whether the journal is read through a pointer or a slice, and any internal
naming. Not a free choice, and not asserted here either: neither the next chunk, nor the mark
covering a key, nor the smallest row set aside for a key may be found by scanning, which the
execution limit on the worker decides rather than any assertion in this file.

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

SEAL = os.environ.get("RCR_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("RCR_WORK", "/work"))
OUT = WORK / "worker_out.json"
GT = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("RCR_LOGS", "/logs/verifier"))


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
        pytest.fail("the rebuild raised or produced nothing: %s" % (item.get("err"),))
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


@pytest.fixture(scope="module")
def wanted(nonce):
    """The graded population, built once. Two of the eleven families are large, so
    regenerating them per test would cost more than running them."""
    seed, per = nonce
    return gen.programs(seed, per)


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

def test_every_nonce_program_matches(produced, wanted):
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


def test_the_graded_set_is_the_size_the_brief_states(wanted):
    """The brief quotes these counts, so a generator change cannot quietly contradict it."""
    assert len(cases.ORDER) == 34, "hand programs: %d" % len(cases.ORDER)
    assert len(wanted) == 330, "generated programs: %d" % len(wanted)
    big = [name for fam, name, _lines in wanted if fam in ("wide", "deep")]
    assert len(big) == 6, "large programs: %d" % len(big)


def test_generated_programs_respect_the_stated_bounds(wanted):
    """The brief bounds the source key, the fields, the chunk size and n. The graded
    population has to stay inside them, or the brief describes a different task."""
    for _fam, name, lines in wanted:
        head = lines[0].split()
        assert head[0] == "cfg", name
        assert 1 <= int(head[1]) <= 5, name
        for raw in lines[1:]:
            part = raw.split()
            if part[0] == "set":
                assert 1 <= int(part[1]) < 100000, name
                assert all(0 <= int(x) < 100 for x in part[2:5]), name
            elif part[0] == "del":
                assert 1 <= int(part[1]) < 100000, name
            elif part[0] == "play":
                assert int(part[1]) >= 0, name


def test_every_family_is_represented(wanted):
    fams = {fam for fam, _n, _l in wanted}
    assert fams == {f for f, _big in gen.FAMILIES}
