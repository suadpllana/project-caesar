"""The grader. Runs as root, after the sandboxed run has finished and been reaped.

THE VERIFIER CONTRACT, frozen before any environment code was written. It lives here
rather than only in a working note because this is the file the run audit and the quality
review read.

WHAT IS GRADED, all or nothing:

  the determination record for every register, which is one row per company in
  incorporation order carrying the company, whether the programme's list holds it, how
  many of its seats the list took, how many seats it has, and who took each seat.

Two register sets are driven. Twenty-three are enumerated, one per rule, and their
expected records ship in gt.json AND are re-proved here by oracle.py before they are
believed. The rest are built inside this container from a nonce made out of /dev/urandom
after the agent has finished, so they did not exist when the submission was written and
their expected records are produced by oracle.py after the run. That is what replaces a
work counter: what is compared is the whole determination rather than a summary of it, so
there is no number to assign and no table to paste.

WHAT IS DELIBERATELY NOT GRADED, because two correct implementations differ on it: how
many times a submission consults the register, what it caches between companies, the order
it sweeps in, and the name it gives to a hand of several holders. Five alternative correct
implementations live in the authoring directory and all five must score 1, among them one
that names the combined hand so that it sorts after every party id rather than before.
Registers are generated tie free for that reason: a seat taken on a tied average would be
settled by the name of a hand, and the name is the submission's business.

WHAT ELSE IS ATTESTED, since the run executes agent code in a shared interpreter: the tree
outside the four declared artifacts is byte-identical to the pristine copy after the run;
the frozen entry points are fingerprinted as they actually stood in the running
interpreter, against digests derived here by compiling the pristine sources; the
interpreter's own tally of entries into the seat allocation and the register reader has to
be consistent with the register set and the instrumentation still armed at the end; and
the report has to carry the run nonce.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

import cases
import gen
import mark
import oracle

REPORT = Path(os.environ.get("SRS_REPORT", "/tests/out/report.json"))
NONCE = Path(os.environ.get("SRS_NONCEFILE", "/tests/out/nonce"))
PRISTINE = Path(os.environ.get("SRS_PRISTINE", "/pristine"))
WORK = Path(os.environ.get("SRS_WORK", "/work/app"))
GT = Path("/tests/gt.json")

ARTIFACTS = ("pol/screen.py", "pol/voice.py", "pol/tally.py", "pol/note.py")
FROZEN = ("reg/poll.py", "reg/book.py", "reg/site.py", "reg/run.py", "reg/lex.py")


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def report():
    assert REPORT.is_file(), "the run produced no report at %s" % REPORT
    body = REPORT.read_text(encoding="utf-8")
    assert body.strip(), "the run produced an empty report"
    try:
        return json.loads(body)
    except ValueError as exc:
        pytest.fail("the report is not JSON: %s" % exc)


@pytest.fixture(scope="session")
def wanted(report):
    """Every register the run should have driven, with the record it should have made."""
    out = []
    truth = _load(GT)["cases"]
    for name, text in cases.CASES:
        assert name in truth, "no ground truth for enumerated register %s" % name
        out.append((name, text, truth[name]))
    for name, text in gen.batch(report["nonce"], int(report["count"])):
        out.append((name, text, None))
    return out


def test_report_carries_the_run_nonce(report):
    assert NONCE.is_file(), "no nonce was written for this run"
    assert report["nonce"] == NONCE.read_text(encoding="utf-8").strip()
    assert len(report["nonce"]) >= 16


def test_every_register_was_driven(report, wanted):
    assert report["names"] == [n for n, _, _ in wanted], \
        "the run drove a different set of registers from the one this trial asked for"


def test_no_register_raised(report):
    hurt = sorted(k for k, v in report["rows"].items() if isinstance(v, dict))
    assert not hurt, "the rebuilt screen raised on %d register(s): %s" % (
        len(hurt), ", ".join("%s (%s)" % (k, report["rows"][k]["raised"]) for k in hurt[:4]))


def test_ground_truth_reproduces_from_the_sealed_model(wanted):
    """gt.json is believed only where a second implementation reaches the same record."""
    for name, text, stored in wanted:
        if stored is None:
            continue
        assert oracle.determine(text) == stored, \
            "gt.json disagrees with the sealed model on %s" % name


def test_enumerated_registers(report, wanted):
    bad = []
    for name, text, stored in wanted:
        if stored is None:
            continue
        got = report["rows"].get(name)
        if got != stored:
            bad.append((name, stored, got))
    assert not bad, _spell(bad)


def test_generated_registers(report, wanted):
    bad = []
    for name, text, stored in wanted:
        if stored is not None:
            continue
        want = oracle.determine(text)
        got = report["rows"].get(name)
        if got != want:
            bad.append((name, want, got))
    assert not bad, "%d of the generated registers came back wrong. %s" % (
        len(bad), _spell(bad[:3]))


def test_the_executed_tree_was_the_one_we_shipped(report):
    # Counted first. A comparison against a directory that is not there passes every file
    # it never looked at, which is a gate that manufactures evidence rather than one that
    # fails quietly.
    shipped = [p for p in PRISTINE.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    assert len(shipped) >= 12, "the pristine copy is missing at %s" % PRISTINE
    moved = []
    for path in sorted(shipped):
        rel = path.relative_to(PRISTINE).as_posix()
        if rel in ARTIFACTS:
            continue
        mine = WORK / rel
        if not mine.is_file():
            moved.append("%s is gone" % rel)
        elif _sha(mine) != _sha(path):
            moved.append("%s was rewritten" % rel)
    assert not moved, "the run changed files it does not declare: %s" % ", ".join(moved)


def test_the_frozen_entry_points_were_the_ones_we_shipped(report):
    assert report["marks"]["import"], "the run recorded no fingerprints"
    want = mark.compiled({p.replace("/", ".")[:-3]: (PRISTINE / p).read_text(encoding="utf-8")
                          for p in FROZEN})
    for when in ("import", "end"):
        for label, digest in sorted(report["marks"][when].items()):
            assert label in want, "unknown entry point %s" % label
            assert digest == want[label], \
                "%s was not the shipped function at %s of the run" % (label, when)


def test_the_interpreter_saw_the_work_happen(report, wanted):
    tally = report["tally"]
    assert report["armed"], "the instrumentation was not still armed when the run ended"
    assert tally["load"] == len(wanted), \
        "the register reader ran %d times for %d registers" % (tally["load"], len(wanted))
    seats = 0
    for _, text, _ in wanted:
        seats += sum(1 for line in text.splitlines() if line.startswith("co "))
    assert tally["elect"] >= seats, \
        "the seat allocation ran %d times for %d companies" % (tally["elect"], seats)
    assert tally["stakes"] >= 1


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _spell(bad):
    out = []
    for name, want, got in bad:
        if not isinstance(got, list):
            out.append("%s: nothing usable came back (%r)" % (name, got))
            continue
        lines = ["%s:" % name]
        for i, row in enumerate(want):
            mine = got[i] if i < len(got) else None
            if mine != row:
                lines.append("    company %s wanted %r, got %r"
                             % (row[0], row[1:], mine[1:] if isinstance(mine, list) else mine))
        out.append("\n".join(lines))
    return "\n".join(out)
