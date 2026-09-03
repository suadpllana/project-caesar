"""Grading. Runs as root after the sandboxed run has ended, and executes nothing it wrote.

THE CONTRACT, kept here rather than only in a working note, because this is the file the run
audit and the quality review read.

What is graded, exactly and with no partial credit:

  the trace     every row the sealed driver appended, in order, for every job: which token
                the model produced, which bytes went to the client at that step, which call
                was dispatched and what it answered, which script the answer branched to,
                whether the response was declared over, and the whole client text at the end.
  nothing else  not how the submission stores its state, not how many times it looks at the
                raw stream, not what it caches between steps. Six alternative correct servers
                live in authoring/variants and all six have to score 1, which is what stops
                an implementation choice from being graded.

Where expected results come from. The thirty-five enumerated jobs are pinned in gt.json. The
three hundred generated ones are built inside this container from a nonce made out of
/dev/urandom after the agent finished, and their expected traces come from oracle.py, a second
implementation written from the specification rather than from the tree, sharing no code with
it. Those jobs did not exist when the submission was written, so there is nothing to fit and
nothing to paste: an answer key would cover the thirty-five and say nothing about the rest.

Why the trace and not a work counter. Release timing is the whole question, and a counter of
releases says nothing about whether a byte went out at the right step. The trace carries the
step, so holding a byte one step too long is as visible as sending it one step too early - and
both have to be, because a server that never sends anything until the model stops satisfies
every safety rule and is wrong.

Since the verifier runs agent code, four more things are attested. The executed tree outside
the four declared artifacts must be byte-identical to the pristine copy. Each sealed function
is fingerprinted as it existed in the running interpreter, at import and again at the end,
against digests derived here by compiling the pristine sources - which is the layer an
import-time rebind cannot get in front of, since it is inside the tree before the first
in-process fingerprint is taken. The interpreter's own tally of entries into the sealed driver
and the sealed tool has to match the work the trace claims. And the report carries the run
nonce, so a report written before the run cannot pass.
"""

import hashlib
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402

ARTIFACTS = ("srv/look.py", "srv/bite.py", "srv/hold.py", "srv/pick.py")
SEALED = ("drive", "answer", "load")


def _digest(code, out=None):
    if out is None:
        out = hashlib.sha256()
    out.update(code.co_code)
    out.update(repr(code.co_names).encode())
    out.update(repr(code.co_varnames).encode())
    out.update(repr(code.co_argcount).encode())
    for const in code.co_consts:
        if hasattr(const, "co_code"):
            _digest(const, out)
        else:
            out.update(repr(const).encode())
    return out


@pytest.fixture(scope="module")
def report():
    path = os.environ.get("RUN_OUT", "/work/run/out.json")
    raw = pathlib.Path(path).read_text()
    assert raw.strip(), "the run produced an empty report"
    data = json.loads(raw)
    assert isinstance(data, dict), "the report is not an object"
    return data


@pytest.fixture(scope="module")
def wanted(report):
    """Expected traces: gt.json for the enumerated jobs, the sealed model for the rest."""
    pinned = json.loads((HERE / "gt.json").read_text())
    out = dict(pinned)
    for name, job in gen.jobs(report.get("nonce", ""), int(report.get("count", 0))):
        out[name] = oracle.drive(job)
    return out


@pytest.fixture(scope="module")
def baseline():
    """Digests of the sealed functions, derived by compiling the pristine sources."""
    src = pathlib.Path(os.environ.get("PRISTINE_DIR", "/pristine")) / "srv" / "wire.py"
    module = compile(src.read_text(), "wire", "exec")
    found = {}
    for const in module.co_consts:
        if hasattr(const, "co_code") and const.co_name in SEALED:
            found[const.co_name] = _digest(const).hexdigest()
    assert sorted(found) == sorted(SEALED), "the pristine driver is missing a sealed function"
    return found


def test_the_report_answers_about_this_run(report):
    assert report.get("nonce") == os.environ.get("RUN_NONCE"), \
        "the report does not carry this run's nonce"
    assert int(report.get("count", -1)) == int(os.environ.get("RUN_COUNT", "300"))


def test_every_job_was_driven(report):
    want = len(cases.jobs()) + int(os.environ.get("RUN_COUNT", "300"))
    assert len(report.get("runs", {})) == want, "some jobs produced no trace at all"
    assert report.get("drives") == want, \
        "the interpreter counted %r entries into the driver, not %d" % (report.get("drives"), want)


def test_the_instrumentation_was_still_on_at_the_end(report):
    assert report.get("arm") is True, "the instrumentation was not armed when the run ended"


def test_no_job_faulted_or_took_a_release_back(report):
    bad = []
    for name, rows in sorted(report.get("runs", {}).items()):
        for row in rows:
            if row and row[0] in ("boom", "rw"):
                bad.append((name, row))
                break
    assert not bad, "jobs that faulted or tried to unsend: %r" % (bad[:6],)


def test_the_dispatches_in_the_trace_really_happened(report):
    said = 0
    for rows in report.get("runs", {}).values():
        said += sum(1 for row in rows if row and row[0] == "dp")
    assert report.get("answers") == said, \
        "the trace claims %d dispatches, the interpreter counted %r" % (said, report.get("answers"))


def test_the_sealed_driver_is_the_one_we_shipped(report, baseline):
    assert report.get("early") == baseline, "the driver was not the shipped one when imported"
    assert report.get("late") == baseline, "the driver was changed while the run was going"


def test_the_executed_tree_was_the_one_we_shipped():
    app = pathlib.Path(os.environ.get("APP_DIR", "/work/app"))
    pristine = pathlib.Path(os.environ.get("PRISTINE_DIR", "/pristine"))
    assert pristine.is_dir(), "the pristine copy is missing, so this compared nothing"
    looked = 0
    for src in sorted(pristine.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(pristine).as_posix()
        if rel in ARTIFACTS:
            continue
        looked += 1
        mine = app / rel
        assert mine.is_file(), "a file the run should not touch is gone: %s" % rel
        assert mine.read_bytes() == src.read_bytes(), "the run rewrote %s" % rel
    assert looked >= 8, "only %d files were compared, so this test proved nothing" % looked


@pytest.mark.parametrize("name", [n for n, _ in cases.jobs()])
def test_named_job(report, wanted, name):
    got = report.get("runs", {}).get(name)
    assert got is not None, "no trace for %s" % name
    assert got == wanted[name], _why(name, wanted[name], got)


def test_the_generated_jobs(report, wanted):
    wrong = []
    for name in sorted(wanted):
        if not name.startswith("g"):
            continue
        got = report.get("runs", {}).get(name)
        if got != wanted[name]:
            wrong.append(name)
    assert not wrong, "%d of the generated jobs came out wrong, first few: %r" % (
        len(wrong), wrong[:8])


def _why(name, want, got):
    for i, (a, b) in enumerate(zip(want, got)):
        if a != b:
            return "%s row %d: wanted %r, got %r" % (name, i, a, b)
    if len(want) != len(got):
        side = want[len(got):] if len(want) > len(got) else got[len(want):]
        return "%s: traces differ in length, extra %r" % (name, side[:3])
    return "%s: traces differ" % name
