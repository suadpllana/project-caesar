"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/lst/`: `seq.py` is the table's order and the
view a scroll walks, `scr.py` holds the scroll records - the mark, the limits and the
delivery memory - `owe.py` is the ledger and the weight the service is holding, `pg.py`
serves one page, `edt.py` applies the edits, and `rep.py` writes the closing report.
Everything else in the tree is the verifier's own pristine copy, so only those six can
change what a list file prints.

Graded, and settled the same way by two implementations written apart:

  1  a place is the key and then the id, and a scroll sees the rows carrying its tag at the
     moment it looks
  2  a page drains the scroll's ledger strictly from the front while the entry there fits
  3  a page that has handed out nothing takes the row it would otherwise leave behind
     whatever it weighs, and the page's weight is spent to nothing by doing so
  4  the scan takes the view from strictly after the mark, passing by rows this scroll
     already has, handing out rows that fit, and stepping over rows that do not
  5  the scan stops on the row limit, on the weight left, on the weight it has stepped over
     in this page, on the end of the view, or on the hold - and only the hold leaves the
     mark short of the row that stopped it
  6  the mark is the place of the last row the scan looked at, and draining never moves it
  7  a row is owed when it carries the scroll's tag, sits at or before the mark, and has not
     been handed out; the ledger holds those rows in the order they came to be owed, and a
     row owed a second time enters at the end
  8  the service holds at most cfg weight owed across every scroll at once, and that hold
     governs what a scan may step over, never what an edit may bring to be owed
  9  the delivery memory is permanent, per scroll, and by row id
 10  the closing report gives, per scroll, rows handed out, rows owed now and rows of the
     view not handed out, then the weight owed across every scroll

Implementation choice, and not graded: how the view is ordered internally, whether the
ledger is a dict, a list with stamps or a linked list, whether the weight held is one total
or a sum over per-scroll totals, whether the delivery memory is a set or a map, and any
internal naming. Not a free choice, and not asserted here either: the view cannot be
re-derived on every page and the scan cannot resume from the front of the table, which the
execution limit on the worker decides rather than any assertion in this file.

Hand list files are checked against `gt.json`, frozen before this file was written. Nonce
list files are generated here, after the agent has finished, and checked against the sealed
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

SEAL = pathlib.Path(os.environ.get("PPO_SEAL", "/tests/seal"))
sys.path.insert(0, str(SEAL))

import model  # noqa: E402

RECORD = pathlib.Path(os.environ.get("PPO_WORK", "/work")) / "worker_out.json"
LOGS = pathlib.Path(os.environ.get("PPO_LOGS", "/logs/verifier"))


def fingerprint(lines):
    """What the worker was asked to run, so a rewritten list file is not graded."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


class Record(object):
    """The worker's output. Every byte of it came from a process that ran agent code.

    Nothing here trusts a type, a key or a shape: a missing file, a top-level object
    instead of a list, an entry that is a string, a trace that is a dict - each of those is
    a submission that did not produce a record, which is a failure and never a pass.
    """

    def __init__(self, path):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            pytest.fail("the worker left no readable record: %s" % exc)
        if not isinstance(raw, list):
            pytest.fail("the worker's record is not a list of entries")
        self.by_name = {}
        for entry in raw:
            if not isinstance(entry, dict):
                pytest.fail("a record entry is not an object")
            label = entry.get("name")
            if not isinstance(label, str):
                pytest.fail("a record entry carries no name")
            self.by_name[label] = entry

    def ran(self, label, lines):
        """The entry for one list file, with the program it was actually given checked."""
        entry = self.by_name.get(label)
        if entry is None:
            pytest.fail("no record for %s" % label)
        if entry.get("sig") != fingerprint(lines):
            pytest.fail("the list file %s was altered before it was run" % label)
        return entry

    @staticmethod
    def printed(entry):
        out = entry.get("got")
        if out is None:
            pytest.fail("the service raised or printed nothing: %s" % (entry.get("err"),))
        if not isinstance(out, list) or not all(isinstance(line, str) for line in out):
            pytest.fail("the recorded trace is not a list of lines")
        return out


@pytest.fixture(scope="module")
def record():
    return Record(RECORD)


@pytest.fixture(scope="module")
def frozen():
    return json.loads((SEAL / "gt.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def population():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return gen.programs(seed, per)


# --- before judging anything, the sealed side has to agree with itself -----------------

def test_the_model_still_reproduces_the_frozen_answers(frozen):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the enumerated list files: one per graded decision, and both sides of each fence ---

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_list_file(record, frozen, name):
    lines = cases.prog(name)
    assert Record.printed(record.ran(name, lines)) == frozen[name]


# --- list files generated from a seed drawn after the agent's container was gone --------

def test_every_generated_list_file(record, population):
    """All-or-nothing: one differing line anywhere in four hundred traces is a failure."""
    assert len(population) >= 300, "generated population too small: %d" % len(population)
    wrong = []
    for _family, name, lines in population:
        entry = record.by_name.get(name)
        if entry is None:
            wrong.append((name, "no record"))
        elif entry.get("sig") != fingerprint(lines):
            wrong.append((name, "list file altered"))
        elif entry.get("got") != model.expect(lines):
            wrong.append((name, "trace differs"))
    assert not wrong, "%d of %d generated list files wrong, first: %s" % (
        len(wrong), len(population), wrong[:4])


def test_the_population_covers_every_family(population):
    """A shrunken generator is a shrunken exam; the families are named, not counted."""
    assert {family for family, _n, _l in population} == set(gen.SMALL) | {"wide", "deep"}
