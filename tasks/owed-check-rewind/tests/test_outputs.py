"""Stage two: grading. Runs as root and never executes the agent's code.

FROZEN CONTRACT
---------------
The agent supplies six files under /app/tx: heap.py, act.py, chk.py, owe.py, sp.py and
sess.py. Stage one laid them over the verifier's own pristine copy of the tree - the driver
run_tx.py, the parser prog.py, the catalog cat.py and the line writer say.py are ours - and
recorded what every graded program printed, one line per statement.

Graded, and settled identically by the sealed model and by two correct executors written apart:

   1  an insert of a present key raises `key` at once; an update or delete of a missing key
      does nothing
   2  notnull is violated by null; min N by a value below N and never by null
   3  a foreign key is violated by a child whose column is not null and names no parent row;
      a parent key is left behind when no parent row has it and some child still holds it
   4  a write (insert, update, setnull) checks the row at once against each immediate check
      of its table, in declaration order
   5  a delete walks the keys referring to its table in declaration order, whatever their
      modes, and for each the rows holding the key at that moment in key order: cascade
      depth-first, setnull writes null, restrict raises at once, noaction does nothing
   6  at the end of a statement each immediate foreign key, in declaration order, looks at the
      rows it wrote and the parent keys it deleted, in first-touch order; the first violation
      raises
   7  a statement that raises leaves nothing behind and aborts the transaction
   8  at the end of a statement each deferred constraint judges the rows and keys the statement
      touched: violated and not owed gains an entry, not violated and owed loses it; nothing
      else changes an entry
   9  the ledger is ordered by declaration and then by when each entry was made
  10  set immediate and commit walk the entries they cover in ledger order; the first still
      violated raises and nothing changes (a commit also rolls back); otherwise all go
  11  modes start as declared each transaction; set changes deferrable ones only; naming one
      that is not deferrable is an error
  12  rollback to S restores rows, the ledger with every entry's place, and the modes as they
      stood when the latest S was made; release S drops S and every later savepoint
  13  an unknown savepoint is an error; errors and raises abort; an aborted transaction ignores
      everything but rollback, rollback to and commit, and commit there rolls back
  14  an ok line lists the entries the statement removed, in the order they stood, then the
      entries it added, in ledger order; an entry there before and after is in neither
  15  the whole graded set runs inside the wall clock on stage one

Implementation choice, and not graded: how rows, the key index, the ledger and the undo state
are held, whether a savepoint is a journal position or a level of before-images, and every
internal name. Not free either, and not asserted here: an executor that copies its rows or its
ledger at a savepoint, or scans a table for the rows holding a key, cannot finish the scale
programs inside the clock, which test.sh enforces rather than this file.

Enumerated programs are compared with seal/gt.json, frozen before this file was written.
Generated programs are drawn from a seed chosen after the agent finished and compared with the
sealed model, which must itself still reproduce gt.json before anything is judged.
"""
import hashlib
import json
import os
from pathlib import Path

import pytest

import cases
import gen

SEAL = Path(os.environ.get("OCR_SEAL", "/tests/seal"))
SCRATCH = Path(os.environ.get("OCR_SCRATCH", "/scratch"))
VERDICT = Path(os.environ.get("OCR_VERDICT", "/logs/verifier"))

import sys  # noqa: E402
sys.path.insert(0, str(SEAL))
import model  # noqa: E402


def _digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _record():
    """Everything in this file came out of a process that ran agent code."""
    try:
        raw = json.loads((SCRATCH / "record.json").read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("stage one left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the record is not a list")
    by = {}
    for entry in raw:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            pytest.fail("a record entry is malformed")
        by[entry["name"]] = entry
    return by


def _same(entry, want):
    """Does one recorded printout equal the lines a correct executor prints?"""
    if "error" in entry:
        return False
    n, dig = entry.get("n"), entry.get("digest")
    if not isinstance(n, int) or not isinstance(dig, str):
        return False
    if n != len(want) or dig != _digest(want):
        return False
    lines = entry.get("lines")
    return lines is None or lines == want


def _first_difference(entry, want):
    if "error" in entry:
        return "raised: %s" % entry["error"]
    lines = entry.get("lines")
    if not isinstance(lines, list):
        return "printout differs (%s lines, %s expected)" % (entry.get("n"), len(want))
    for i, (a, b) in enumerate(zip(lines, want)):
        if a != b:
            return "statement %d printed %r, expected %r" % (i + 1, a, b)
    return "printed %d lines, expected %d" % (len(lines), len(want))


@pytest.fixture(scope="module")
def record():
    return _record()


@pytest.fixture(scope="module")
def truth():
    return json.loads((SEAL / "gt.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def population():
    seed = (VERDICT / "seed").read_text(encoding="utf-8").strip()
    each = int((VERDICT / "each").read_text(encoding="utf-8").strip())
    return gen.programs(seed, each)


# --- the sealed side must agree with itself before it judges anything ----------------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if the two have drifted apart, nothing is graded."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == truth[name], name


# --- the enumerated programs: one per graded decision and both sides of each fence ---------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_case(record, truth, name):
    assert name in record, "no printout for hand case %s" % name
    entry = record[name]
    assert entry.get("prog") == _digest(cases.prog(name)), "hand case %s was altered" % name
    assert _same(entry, truth[name]), "%s: %s" % (name, _first_difference(entry, truth[name]))


# --- programs generated from a seed drawn after the agent was gone --------------------------

def test_every_generated_program_matches(record, population):
    assert len(population) >= 300, "population too small: %d" % len(population)
    wrong = []
    for _fam, name, lines in population:
        entry = record.get(name)
        if entry is None:
            wrong.append((name, "missing"))
            continue
        if entry.get("prog") != _digest(lines):
            wrong.append((name, "program altered"))
            continue
        want = model.expect(lines)
        if not _same(entry, want):
            wrong.append((name, _first_difference(entry, want)))
    assert not wrong, "%d of %d generated programs wrong; first: %s" % (
        len(wrong), len(population), wrong[:3])


def test_every_family_is_represented(population):
    assert {fam for fam, _n, _l in population} == {f for f, _big in gen.FAMILIES}
