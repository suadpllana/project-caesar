"""Stage two of grading: read stage one's record and decide. Runs as root, runs no agent code.

FROZEN CONTRACT
---------------
The agent hands over six files under `/app/dur/`. `tab.py` indexes the recorded log,
`edge.py` owns where replay stops and what the log has left over, `pair.py` binds an answer
to a command, `pend.py` holds the commands whose result has not been taken, `sigq.py`
delivers signals and `ver.py` settles version markers. Everything else under `/app` is the
verifier's own copy, so nothing but those six can change what a run file prints, and a file
left beside them is never collected.

Graded, and settled the same way by two implementations written apart:

  1  a command matches the recorded command at its own position among the recorded commands
     OF ITS KIND; other kinds do not shift that position
  2  a recorded command naming something else ends the run where it happens
  3  the first command whose kind has no recorded position left opens the live side, once
     for the whole run, and nothing after it looks at the log for a position
  4  a replayed command's answer is the recorded answer at its position among the answers of
     its KIND AND NAME together
  5  live answers come from the run file's own list, in the order the live commands were
     issued, and count as arriving after every recorded answer
  6  `join` takes the outstanding command issued earliest, `race` the one answered earliest
  7  a command whose answer is not recorded stops the run and names it
  8  signals are taken per tag in recorded order, on either side of the boundary, and a
     signal nobody waited for is not a failure
  9  a marker with no recorded choice is zero while replaying and the body's own value once
     live
 10  a body that reaches its end while the log still holds a command it never issued fails,
     naming the earliest of them; a body that stopped short does not
 11  a body past the step ceiling ends over

Implementation choice, and not graded: how the log is indexed, whether the outstanding set
is a list or a pair of structures, whether the answer positions are held on the records or
looked up, and any internal naming. Not a free choice either, and not asserted here: none of
the three lookups may be a walk over the log, which the execution limit on stage one decides
rather than any assertion in this file.

The hand programs are checked against `gt.json`, frozen before this file was written. The
generated population is built here from a seed drawn after the agent's container is gone and
checked against the sealed model, which must still reproduce `gt.json` exactly, so a model
that had drifted could not quietly redefine what correct means.
"""
import hashlib
import json
import os
import pathlib
import sys

import pytest

import cases
import gen

SEAL = os.environ.get("RMD_SEAL", "/tests/seal")
sys.path.insert(0, SEAL)

import model  # noqa: E402

WORK = pathlib.Path(os.environ.get("RMD_WORK", "/work"))
RECORD = WORK / "stage_one.json"
FROZEN = pathlib.Path(SEAL) / "gt.json"
LOGS = pathlib.Path(os.environ.get("RMD_LOGS", "/logs/verifier"))


def _stamp(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _record():
    """Every byte here came out of a process that ran agent code. Parse it defensively."""
    try:
        raw = json.loads(RECORD.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("stage one left no readable record: %s" % exc)
    if not isinstance(raw, list):
        pytest.fail("the record is not a list")
    rows = {}
    for item in raw:
        if not isinstance(item, dict):
            pytest.fail("a record entry is not an object")
        name = item.get("name")
        if not isinstance(name, str):
            pytest.fail("a record entry carries no name")
        rows[name] = item
    return rows


def _printed(item):
    got = item.get("printed")
    if got is None:
        pytest.fail("the engine raised or printed nothing: %s" % (item.get("blew"),))
    if not isinstance(got, list) or not all(isinstance(row, str) for row in got):
        pytest.fail("the record is not a list of printed lines")
    return got


@pytest.fixture(scope="module")
def produced():
    return _record()


@pytest.fixture(scope="module")
def frozen():
    return json.loads(FROZEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drawn():
    seed = (LOGS / "seed").read_text(encoding="utf-8").strip()
    per = int((LOGS / "per").read_text(encoding="utf-8").strip())
    return seed, per


# --- the sealed side has to agree with itself before it judges anything ------------------

def test_the_model_still_reproduces_the_frozen_answers(frozen):
    """gt.json was frozen from the model. If they have drifted apart, grade nothing."""
    assert sorted(frozen) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.expect(cases.prog(name)) == frozen[name], name


# --- the enumerated programs: one per graded decision, and both sides of each fence -------

@pytest.mark.parametrize("name", cases.ORDER)
def test_hand_program(produced, frozen, name):
    assert name in produced, "no result for hand program %s" % name
    item = produced[name]
    assert item.get("stamp") == _stamp(cases.prog(name)), "hand program altered: %s" % name
    assert _printed(item) == frozen[name]


# --- programs built from a seed drawn after the agent's container was gone ----------------

def test_every_generated_program_matches(produced, drawn):
    seed, per = drawn
    wanted = gen.programs(seed, per)
    assert len(wanted) >= 400, "generated population too small: %d" % len(wanted)
    wrong = []
    for _fam, name, lines in wanted:
        item = produced.get(name)
        if item is None:
            wrong.append((name, "missing"))
            continue
        if item.get("stamp") != _stamp(lines):
            wrong.append((name, "run file altered"))
            continue
        if item.get("printed") != model.expect(lines):
            wrong.append((name, "trace differs"))
    assert not wrong, "%d of %d generated programs wrong, first: %s" % (
        len(wrong), len(wanted), wrong[:4])


def test_every_family_is_represented(produced, drawn):
    seed, per = drawn
    seen = {fam for fam, _n, _l in gen.programs(seed, per)}
    assert seen == {fam for fam, _big in gen.FAMILIES}
