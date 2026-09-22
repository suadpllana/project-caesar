"""Stage two: grading. Runs as root, and never executes a line the agent wrote.

FROZEN CONTRACT
---------------
Six files come from the agent, all under `/app/lg/`. `store.py` is the log and the index into
it; `pin.py` is the marks and the feeds, and what each key's held points and trailing point
are; `fold.py` turns a run of entries into a value; `span.py` cuts a key into spans and says
what collapsing one of them leaves behind; `pare.py` is the budgeted collapse loop; `tell.py`
renders a read and the end-of-program report. The rest of the tree is the verifier's own
pristine copy, so nothing else can change what a program prints.

What is graded, settled the same way by two implementations written apart:

  1  a value is folded from the entries the log still holds at or below the point, an `add`
     onto an absent key making it present at that amount
  2  a key's held points are the head, every live mark, and every live feed whose range covers
     it, counted once per point
  3  a key's trailing point is the lowest position among the feeds covering it, and the head
     when none does
  4  an entry above its key's trailing point is never removed and never rewritten
  5  the held points at or below the trailing point cut the rest of the key into spans
  6  collapsing a span keeps no entry when the key's value is the same at its top and its floor
  7  otherwise it keeps one, at the sequence number of the last entry the log still holds there
  8  and that entry becomes `set` carrying the value at the top, or `del` when the key is
     absent there
  9  a pare collapses the pair standing to remove the most first, ties to the lower span top
     and then the smaller key, and stops as soon as the log holds at most the budget
 10  an acknowledgement moves a feed only to a point above its own and not above the head

Left to the implementation, and not asserted anywhere below: how the log and its per-key index
are held, whether the span table is cached, rebuilt or carried between commands, whether the
next collapse is found with a heap, a sort or a bucket, and every internal name. Not free, and
also not asserted here: the span table cannot be rebuilt for every key on every pare, and the
pair table cannot be re-formed after every single collapse. The execution limit on stage one
decides that, not a line in this file.

The enumerated programs are checked against `gt.json`, frozen before this file existed. The
generated ones are built here, after the agent has finished, and checked against the sealed
model - which has to reproduce `gt.json` first, so a model that had drifted cannot quietly
redefine what correct means.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("FLP_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("FLP_WORK", "/work"))
FROM_STAGE_ONE = WORK / "worker_out.json"
FROZEN = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("FLP_LOGS", "/logs/verifier"))


def fingerprint(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def collected():
    """Every byte below came out of a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(FROM_STAGE_ONE.read_text(encoding="utf-8"))
    except Exception as why:
        pytest.fail("stage one left no readable record: %s" % why)
    if not isinstance(raw, list):
        pytest.fail("the record is not a list")
    named = {}
    for item in raw:
        if not isinstance(item, dict):
            pytest.fail("a record entry is not an object")
        name = item.get("name")
        if not isinstance(name, str):
            pytest.fail("a record entry carries no name")
        named[name] = item
    return named


def printed(item):
    lines = item.get("got")
    if lines is None:
        pytest.fail("the service raised or printed nothing: %s" % (item.get("err"),))
    if not isinstance(lines, list) or not all(isinstance(one, str) for one in lines):
        pytest.fail("the record is not a list of lines")
    return lines


@pytest.fixture(scope="module")
def record():
    return collected()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(FROZEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawn():
    seed = (LOGS / "nonce").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- before anything is judged, the sealed side has to agree with itself --------------

def test_the_model_still_reproduces_the_frozen_answers(frozen):
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the enumerated programs: one per graded decision, and both sides of each fence ----

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_program(record, frozen, name):
    assert name in record, "no result for %s" % name
    item = record[name]
    assert item.get("sig") == fingerprint(cases.prog(name)), "program altered: %s" % name
    assert printed(item) == frozen[name]


# --- and the programs built from a seed drawn after the agent's container was gone -----

def test_every_generated_program(record, drawn):
    seed, per = drawn
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 300, "the generated population is too small: %d" % len(wanted)
    wrong = []
    for _fam, name, lines in wanted:
        item = record.get(name)
        if item is None:
            wrong.append((name, "missing"))
        elif item.get("sig") != fingerprint(lines):
            wrong.append((name, "program altered"))
        elif item.get("got") != model.expect(lines):
            wrong.append((name, "trace differs"))
    assert not wrong, "%d of %d generated programs wrong, first: %s" % (
        len(wrong), len(wanted), wrong[:4])


def test_every_family_was_generated(record, drawn):
    seed, per = drawn
    seen = {fam for fam, _name, _lines in gen.programs(seed, per)}
    assert seen == {fam for fam, _big in gen.FAMILIES}
