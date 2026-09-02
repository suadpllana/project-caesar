"""The grader.

THE CONTRACT, frozen before the environment was written and not touched since.

Two things are graded, exactly, with no partial credit and no tolerance:

  the sheet   what became of every obligation - paid, given up on, or still open when the
              last round ended - and the tick it happened on.
  the rows    the ordered record the book kept: which obligation moved, which the house
              gave up on, and what every party was holding when each round closed.

Both are produced inside house/bk.py, which is not an editable artifact, so they record
what the book was actually made to do rather than what a submission says it did. The sheet
is a cross-check on the rows rather than a second axis, and the two can only disagree if a
submission reached past the book's own methods.

DELIBERATELY NOT GRADED, because grading them would measure an arrangement of the code
rather than a behaviour: how many times a round asks for a plan, how many turns its loop
takes, what it keeps between turns, and which data structures it holds. Five alternative
correct implementations live in the authoring directory and all five are required to score
1 - among them the drain written as a shrinking set, the drain written as a repeated
recomputation, the round with the giving-up done before the moving, and the reach written
with a different iterator.

WHERE THE EXPECTED ANSWERS COME FROM. tests/oracle.py is a second reading of the round
rules written from the specification rather than from the tree: plain tuples in lists
instead of a Book of objects, a shrinking set of chosen obligations instead of a depth per
party. The enumerated streams are also pinned in tests/gt.json, and the oracle has to
reproduce that file before anything else is graded, so a drift in either is caught rather
than absorbed. The other three hundred streams are built in this container from a nonce
made out of /dev/urandom after the submission was sealed.
"""
import hashlib
import json
import os
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, "/tests")

import gen
import oracle
import scen

REPORT = Path(os.environ.get("QDR_REPORT", "/rep/out.json"))
PRIST = Path("/pristine")
WORK = Path(os.environ.get("QDR_WORK", "/work/app"))
GT = Path("/tests/gt.json")
NONCE = Path("/tests/nonce")

EDITABLE = {"house/drn.py", "house/gvp.py", "house/rnd.py", "house/due.py"}

SEALED = {
    "bk.Book.move": ("house/bk.py", "Book.move"),
    "bk.Book.drop": ("house/bk.py", "Book.drop"),
    "bk.Book.shut": ("house/bk.py", "Book.shut"),
    "bk.Book.book": ("house/bk.py", "Book.book"),
    "bk.Book.top": ("house/bk.py", "Book.top"),
    "ev.read": ("house/ev.py", "read"),
    "ev.feed": ("house/ev.py", "feed"),
}


def _shape(code, out):
    out.append(code.co_name)
    out.append(str(code.co_argcount))
    out.append(code.co_code.hex())
    out.extend(code.co_names)
    out.extend(code.co_varnames)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            _shape(c, out)
        else:
            out.append(repr(c))


def _find(code, want):
    if getattr(code, "co_qualname", code.co_name) == want:
        return code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            got = _find(c, want)
            if got is not None:
                return got
    return None


def _pristine_marks():
    out = {}
    for name, (rel, qual) in SEALED.items():
        src = (PRIST / rel).read_text()
        top = compile(src, str(PRIST / rel), "exec")
        code = _find(top, qual)
        assert code is not None, "no %s in the pristine %s" % (qual, rel)
        acc = []
        _shape(code, acc)
        out[name] = hashlib.sha256("\x1f".join(acc).encode()).hexdigest()[:32]
    return out


@pytest.fixture(scope="session")
def report():
    assert REPORT.exists(), "the run produced no report at all"
    raw = REPORT.read_text()
    assert raw.strip(), "the run produced an empty report"
    return json.loads(raw)


@pytest.fixture(scope="session")
def wanted():
    want = {}
    for name, text in scen.STREAMS:
        want[name] = oracle.play(text)
    return want


def _norm(d):
    return {
        "rows": [list(r) for r in d["rows"]],
        "sheet": {k: list(v) for k, v in d["sheet"].items()},
    }


def _from_oracle(text):
    r = oracle.play(text)
    return {
        "rows": [list(x) for x in r["log"]],
        "sheet": {k: [v[0], v[1]] for k, v in r["sheet"].items()},
    }


def test_the_report_belongs_to_this_run(report):
    assert report["nonce"] == NONCE.read_text().strip(), "the report carries a different nonce"
    assert report["clean"], "at least one stream ended in a fault"
    assert report["count"] == int(os.environ.get("QDR_COUNT", "300"))


def test_the_second_reading_reproduces_the_ground_truth(wanted):
    gt = json.loads(GT.read_text())
    assert len(gt) == len(scen.STREAMS) > 0
    seen = 0
    for name, text in scen.STREAMS:
        got = _from_oracle(text)
        assert got == gt[name], "the sealed model and gt.json disagree on %s" % name
        seen += 1
    assert seen == len(scen.STREAMS)


def test_every_enumerated_stream_matches(report):
    gt = json.loads(GT.read_text())
    seen = 0
    for name, _text in scen.STREAMS:
        assert name in report["runs"], "no result for %s" % name
        assert _norm(report["runs"][name]) == gt[name], "the book disagrees on %s" % name
        seen += 1
    assert seen == len(scen.STREAMS) > 0


def test_every_generated_stream_matches(report):
    made = gen.batch(report["nonce"], report["count"])
    assert len(made) == report["count"] > 0
    seen = 0
    for name, text in made:
        assert name in report["runs"], "no result for %s" % name
        assert _norm(report["runs"][name]) == _from_oracle(text), "the book disagrees on %s" % name
        seen += 1
    assert seen == report["count"]


def test_no_party_was_left_holding_less_than_nothing(report):
    seen = 0
    for name, run in sorted(report["runs"].items()):
        for kind, a, b in run.get("rows", []):
            if kind == "hold":
                assert b >= 0, "%s left %s holding %d" % (name, a, b)
                seen += 1
    assert seen > 0


def test_the_rows_and_the_sheet_tell_the_same_story(report):
    seen = 0
    for name, run in sorted(report["runs"].items()):
        told = {}
        for kind, a, b in run.get("rows", []):
            if kind in ("paid", "gone"):
                assert a not in told, "%s recorded %s twice" % (name, a)
                told[a] = [kind, b]
        for i, v in sorted(run.get("sheet", {}).items()):
            if v[0] == "open":
                assert i not in told, "%s calls %s open after recording it" % (name, i)
            else:
                assert told.get(i) == v, "%s: the sheet and the rows disagree on %s" % (name, i)
            seen += 1
    assert seen > 0


def test_the_recording_methods_were_the_ones_we_shipped(report):
    want = _pristine_marks()
    assert len(want) == len(SEALED) > 0
    assert report["marks"] == want, "a sealed function was not the one compiled from the tree"
    assert report["drift"] == [], "a sealed function changed during the run: %s" % report["drift"]


def test_the_interpreter_saw_the_work_happen(report):
    assert report["strict"], "the run was not asked to instrument itself"
    assert report["armed"], "the instrumentation was not still armed when the last stream ended"
    assert report["rows"] > 0
    seen = 0
    for name, run in sorted(report["runs"].items()):
        rows = run.get("rows", [])
        gave = sum(1 for k, _a, _b in rows if k == "gone")
        held = [a for k, a, _b in rows if k == "hold"]
        who = len(set(held))
        assert who > 0, "%s closed no round at all" % name
        assert len(held) % who == 0, "%s did not close every round for every member" % name
        floor = gave + len(held) // who
        assert run.get("saw", 0) >= floor, (
            "%s: the interpreter saw %d entries into the book against a floor of %d"
            % (name, run.get("saw", 0), floor))
        seen += 1
    assert seen == len(report["runs"]) > 0


def test_the_executed_tree_was_the_one_we_shipped():
    seen = 0
    for p in sorted(PRIST.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(PRIST).as_posix()
        live = WORK / rel
        assert live.exists(), "%s is missing from the tree that ran" % rel
        if rel in EDITABLE:
            continue
        assert live.read_bytes() == p.read_bytes(), "%s was not the file we shipped" % rel
        seen += 1
    assert seen >= 5, "compared %d files, which is not the tree" % seen
