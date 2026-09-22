"""Grading. Runs as root, and never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies the six files under `/app/lm/`: `held.py` keeps the lock records,
`wait.py` the waiting requests, `grant.py` decides what a request waits for, `esc.py` trades
a pile of row locks for a table lock, `dead.py` finds a wait cycle and its victim, and
`settle.py` drives an op and settles the manager afterwards. Everything else in the tree is
the verifier's own pristine copy, so only those six can change what a script prints.

Graded, and settled the same way by two implementations written apart:

  1  two locks conflict when their targets overlap - the same target, or a table and a row of
     it - they belong to different transactions, and they are not both shared
  2  a request is granted only when no record held by another transaction conflicts with it
     and it is not behind any earlier waiting request it conflicts with
  3  it is not behind such a waiter when that waiter's transaction waits, directly or through
     other waits, on the requester
  4  after every op the manager settles: the earliest grantable waiting request is granted,
     again and again; when none is, a hard cycle costs its victim; until nothing changes
  5  a request already covered by the transaction's own records is granted at once and adds
     no record; an upgrade is evaluated like any request and raises the record in place
  6  a granted table lock releases the row records it covers
  7  after a row grant, K or more row records on the table make the transaction try for the
     table lock, exclusive if any of them is exclusive
  8  the try is evaluated behind every waiting request, taken at once or abandoned, never queued
  9  the victim is the transaction on a hard cycle holding the fewest records, ties to the
     most recent request
 10  end and dead lines carry the number of records released, a table record counting one
 11  drop releases the record on exactly that target, if any, and prints nothing

Implementation choice, and not graded: how records and waiting requests are indexed, whether
the wait relation is walked lazily or rebuilt, how cycles are found, and any internal naming.

Hand scripts are checked against `gt.json`, frozen before this file was written. Nonce
scripts are generated here, after the agent has finished, and checked against the sealed
model. The model must also reproduce `gt.json` exactly, so a drifted model cannot quietly
redefine correct.

Three sections below: the sealed side agreeing with itself, the hand scripts, and the nonce
population. Every byte of the worker's record came from a process that ran agent code and is
parsed as hostile input; a missing, malformed or altered record is a failure, never a pass.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("LBE_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("LBE_WORK", "/work"))
LOGS = pathlib.Path(os.environ.get("LBE_LOGS", "/logs/verifier"))


def fingerprint(lines):
    """The script as the worker was handed it, so an altered script is caught by its hash."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


class Record:
    """The worker's output, read once and looked up by script name."""

    def __init__(self):
        try:
            raw = json.loads((WORK / "worker_out.json").read_text(encoding="utf-8"))
        except Exception as exc:
            pytest.fail("no readable worker record: %s" % exc)
        if not isinstance(raw, list):
            pytest.fail("the worker record is not a list")
        self.items = {}
        for entry in raw:
            if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
                pytest.fail("a worker record entry has no name")
            self.items[entry["name"]] = entry

    def trace(self, name, lines):
        """The trace the submission printed for this script, or a failure that says why not."""
        entry = self.items.get(name)
        if entry is None:
            pytest.fail("no result for script %s" % name)
        if entry.get("sig") != fingerprint(lines):
            pytest.fail("the script was altered before it ran: %s" % name)
        got = entry.get("got")
        if got is None:
            pytest.fail("the manager raised or printed nothing on %s: %s" % (name, entry.get("err")))
        if not isinstance(got, list) or not all(isinstance(line, str) for line in got):
            pytest.fail("the trace of %s is not a list of lines" % name)
        return got


@pytest.fixture(scope="module")
def record():
    return Record()


@pytest.fixture(scope="module")
def frozen():
    return json.loads((pathlib.Path(SEAL) / "gt.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def population():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return gen.programs(seed, per)


# --- the sealed side agrees with itself before it judges anything ---------------------

def test_frozen_truth_matches_the_model(frozen):
    """gt.json was frozen from the model. If the two have drifted apart, nothing is graded."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the hand scripts: one per graded decision, plus both sides of each fence ---------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(record, frozen, name):
    lines = cases.prog(name)
    assert record.trace(name, lines) == frozen[name], name


# --- the nonce population, generated from a seed drawn after the agent was gone ---------

def test_every_nonce_script_matches(record, population):
    assert len(population) >= 300, "nonce population too small: %d" % len(population)
    wrong = []
    for _family, name, lines in population:
        entry = record.items.get(name)
        if entry is None:
            wrong.append((name, "missing"))
        elif entry.get("sig") != fingerprint(lines):
            wrong.append((name, "script altered"))
        elif entry.get("got") != model.expect(lines):
            wrong.append((name, "trace differs"))
    assert not wrong, "%d of %d nonce scripts wrong, first: %s" % (
        len(wrong), len(population), wrong[:4])


def test_every_family_is_represented(population):
    """The set the run was graded on holds every family the generator declares."""
    assert {family for family, _n, _l in population} == {f for f, _big in gen.FAMILIES}
