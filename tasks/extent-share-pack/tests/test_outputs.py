"""Grading. Runs as root, and executes nothing the agent wrote.

FROZEN CONTRACT
---------------
Six files come from the submission and are laid over the verifier's own copy of the tree:
`/app/st/ext.py` (the extent record and what an extent costs), `/app/st/pt.py` (a pointer put on
or taken off a slot), `/app/st/pk.py` (rewriting an extent down to the blocks still pointed at),
`/app/st/step.py` (the settle that follows every op), `/app/st/tot.py` (the size questions) and
`/app/st/own.py` (the drop question). Nothing else in the tree can change what a program prints.

The ten decisions graded here, each settled the same way by two implementations written apart:

  1  an extent takes its whole size while any of its blocks is pointed at
  2  a volume is charged for an extent once, however many of its slots are on it
  3  blocks are counted as blocks: two slots on one block are one block occupied
  4  a volume is on an extent while any of its slots points into it
  5  an extent is given up when no slot anywhere points into it, whichever op emptied it
  6  it is rewritten when slots of exactly one volume point into it and twice its occupied
     blocks is under its size
  7  the rewrite keeps the surviving blocks in order, moves every pointer, and prints one line
  8  the settle runs after every op, the ops that drop a volume or copy pointers away included
  9  `use` totals the extents a volume is on, `tot` the extents the store holds
 10  `own` is how much smaller the store would be after dropping that volume, which carries the
     rewrite the drop leaves behind in whichever volume survives

Free, and not graded: how the extent table is held, whether occupancy is a list or a dict, how
the pointers into an extent are found, how the per-volume totals are kept, and any naming. Not
free, and not asserted here either: neither a total nor the pointers into an extent may be found
by walking the store, which the clock on the submitted half decides rather than any line below.

The enumerated programs are checked against `seal/gt.json`, frozen before this file existed. The
rest are generated here, after the agent's container is gone, and checked against the sealed
model, which has to reproduce the frozen answers first or nothing is graded at all.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = pathlib.Path(os.environ.get("ESP_SEAL", "/tests/seal"))
sys.path.insert(0, str(SEAL))

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("ESP_WORK", "/work"))
LOGS = pathlib.Path(os.environ.get("ESP_LOGS", "/logs/verifier"))


def fingerprint(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


class Record:
    """What the unprivileged half wrote. Every field of it is hostile until proved otherwise."""

    def __init__(self):
        try:
            raw = json.loads((WORK / "worker_out.json").read_text(encoding="utf-8"))
        except Exception as exc:
            pytest.fail("no readable record from the submitted half: %s" % exc)
        if not isinstance(raw, list):
            pytest.fail("the record is not a list")
        self.by = {}
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                pytest.fail("the record holds an entry with no name")
            self.by[item["name"]] = item

    def trace(self, name, lines):
        item = self.by.get(name)
        if item is None:
            pytest.fail("no result for %s" % name)
        if item.get("sig") != fingerprint(lines):
            pytest.fail("the program %s was altered before it ran" % name)
        got = item.get("got")
        if got is None:
            pytest.fail("%s raised or produced nothing: %s" % (name, item.get("err")))
        if not isinstance(got, list) or not all(isinstance(one, str) for one in got):
            pytest.fail("%s did not come back as lines" % name)
        return got

    def compare(self, name, lines, want):
        return None if self.trace(name, lines) == want else name


@pytest.fixture(scope="module")
def record():
    return Record()


@pytest.fixture(scope="module")
def frozen():
    return json.loads((SEAL / "gt.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawn():
    return ((LOGS / "nonce").read_text(encoding="utf-8").strip(),
            int((LOGS / "per").read_text(encoding="utf-8").strip()))


# --- before anything is judged, the sealed side has to agree with itself ---------------------

def test_frozen_truth_matches_the_model(frozen):
    assert sorted(frozen) == sorted(cases.ORDER)
    drift = [name for name in cases.ORDER if model.expect(cases.ops(name)) != frozen[name]]
    assert not drift, "the model no longer reproduces the frozen answers: %s" % drift[:3]


# --- one program per graded decision, and the must-still-work twin of each fence -------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(record, frozen, name):
    assert record.trace(name, cases.ops(name)) == frozen[name]


# --- programs drawn from a seed taken after the agent's container was torn down --------------

def test_every_nonce_program_matches(record, drawn):
    seed, per = drawn
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "the drawn population is too small: %d" % len(wanted)
    wrong = [record.compare(name, lines, model.expect(lines)) for _fam, name, lines in wanted]
    wrong = [name for name in wrong if name]
    assert not wrong, "%d of %d drawn programs came back wrong, first: %s" % (
        len(wrong), len(wanted), wrong[:4])


def test_every_family_is_represented(record, drawn):
    seed, per = drawn
    seen = {fam for fam, _name, _lines in gen.programs(seed, per)}
    assert seen == {fam for fam, _big in gen.FAMILIES}
