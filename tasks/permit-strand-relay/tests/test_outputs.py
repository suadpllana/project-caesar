"""The grader. Runs as root, after the sandboxed run has been reaped, and never
imports or executes anything the agent wrote.

THE CONTRACT, frozen before the environment was written.

What is graded, per stream: the ordered rows the machine emitted - `grant` and
`pull` with the level and the absolute ceiling, `over` and `late` with the feed
and the row count, `drop` with the rows a teardown discarded - and the rows
still parked on every live feed at the end. All of it, all or nothing.

Why that is real work and not an implementation choice. A ceiling is a formula
over the level's drained total, and a ceiling is published exactly when the
raise clears the threshold or when withholding it would leave a producer unable
to send its smallest batch while rows are free. Both halves are total, so the
log is a deterministic function of the stream: emissions at a tick change only
what a producer has learned LAG ticks later, so by induction on the tick nothing
in the log is left to taste. Five alternative correct implementations, each
building one of the quantities a different way, and one sealed model sharing no
code with the machine, all reach the same rows on the enumerated set and on
hundreds of generated streams. Order within a tick is not graded because it is
not the policy's to choose - the machine sorts what the policy hands it before
anything is appended.

What is NOT graded: how the policy stores what it has published, what it names
anything, when it computes what. None of it reaches the rows.

Where the answers come from. The enumerated half is in gt.json, written only
after the reference and the sealed model agreed on every one of them and on
four hundred generated streams. The generated half does not exist until test.sh
draws a nonce from /dev/urandom, after the agent has stopped, and is recomputed
here by the sealed model rather than looked up.

Why the numbers are earned rather than reported. The rows come back from the
process that ran the submission, so four things are required of them beyond
being right: every row was appended through the machine's own emitting methods
and not by the policy; the interpreter's own count of entries into the frozen
functions is at or above what the streams require; every frozen function still
carries the bytecode compiled from the pristine sources, checked against a
baseline this grader compiles itself from files the run cannot write; and the
executed tree is byte for byte the shipped tree outside the four declared
policy files.
"""

import hashlib
import json
import os
import types

import pytest

import cases
import gen
import oracle

REPORT = "/work/report.json"
CELL = "/work/app"
SHIPPED = "/pristine"
EDITABLE = ("pol/adm.py", "pol/rtn.py", "pol/tear.py", "pol/emit.py")

SEALED = (
    ("lnk/book.py", "Book.__init__"),
    ("lnk/book.py", "Book.arm"),
    ("lnk/book.py", "Book.charge"),
    ("lnk/book.py", "Book.bill"),
    ("lnk/book.py", "Book.stow"),
    ("lnk/book.py", "Book.draw"),
    ("lnk/book.py", "Book.close"),
    ("lnk/book.py", "Book.held"),
    ("lnk/book.py", "Book.open"),
    ("lnk/mach.py", "Mach.run"),
    ("lnk/mach.py", "Mach.arrive"),
    ("lnk/mach.py", "Mach.take"),
    ("lnk/mach.py", "Mach.shut"),
    ("lnk/mach.py", "Mach.reopen"),
    ("lnk/mach.py", "Mach.publish"),
    ("lnk/rd.py", "parse"),
)


def mark(code):
    pot = hashlib.sha256()
    pot.update(code.co_code)
    pot.update(repr(code.co_names).encode("utf-8"))
    pot.update(repr(code.co_varnames).encode("utf-8"))
    for lump in code.co_consts:
        if isinstance(lump, types.CodeType):
            pot.update(mark(lump).encode("utf-8"))
        else:
            pot.update(repr(lump).encode("utf-8"))
    return pot.hexdigest()


def fold(table):
    pot = hashlib.sha256()
    for key in sorted(table):
        pot.update((key + "=" + table[key] + "\n").encode("utf-8"))
    return pot.hexdigest()


def dig(code, dotted):
    head, _, rest = dotted.partition(".")
    for lump in code.co_consts:
        if isinstance(lump, types.CodeType) and lump.co_name == head:
            return dig(lump, rest) if rest else lump
    raise KeyError(dotted)


def baseline():
    """Fingerprints derived by compiling the pristine sources. Nothing runs."""
    table = {}
    seen = 0
    for rel, dotted in SEALED:
        path = os.path.join(SHIPPED, rel)
        with open(path, "rb") as fh:
            body = fh.read()
        shell = compile(body, rel, "exec")
        table[rel + "::" + dotted] = mark(dig(shell, dotted))
        seen += 1
    assert seen == len(SEALED), "compiled %d of %d sealed names" % (seen, len(SEALED))
    return table


@pytest.fixture(scope="session")
def report():
    assert os.path.exists(REPORT), "the run produced no report at " + REPORT
    with open(REPORT) as fh:
        body = fh.read()
    assert body.strip(), "the run produced an empty report"
    blob = json.loads(body)
    assert isinstance(blob, dict), "the report is not an object"
    assert int(blob.get("nonce", -1)) == int(os.environ["RUN_NONCE"]), \
        "the report does not carry this run's nonce"
    return blob


@pytest.fixture(scope="session")
def wanted():
    with open("/tests/gt.json") as fh:
        truth = json.load(fh)
    nonce = int(os.environ["RUN_NONCE"])
    wide = int(os.environ.get("RUN_WIDE", "300"))
    for plan in gen.batch(nonce, wide):
        rows, park = oracle.settle(plan)
        truth[plan["name"]] = {
            "ev": rows,
            "park": dict((str(k), v) for k, v in park.items()),
        }
    return truth


def test_the_instrumentation_was_armed(report):
    assert report.get("mode") == "monitoring", \
        "the interpreter's own counter did not run in monitoring mode"
    assert report.get("armed") is True, \
        "the interpreter's own counter was not still armed at the end"


def test_no_row_was_offered_by_the_policy(report):
    assert report.get("forced") is False, \
        "a row was appended by something other than the machine"


def test_the_frozen_machine_was_the_one_we_shipped(report):
    want = fold(baseline())
    assert report.get("open") == want, \
        "a frozen function was already not the shipped one when the tree imported"
    assert report.get("shut") == want, \
        "a frozen function was not the shipped one when the last stream finished"


def test_the_executed_tree_was_the_one_we_shipped():
    looked = 0
    for here, _, leaves in os.walk(SHIPPED):
        for leaf in sorted(leaves):
            full = os.path.join(here, leaf)
            rel = os.path.relpath(full, SHIPPED).replace(os.sep, "/")
            if rel in EDITABLE:
                continue
            mirror = os.path.join(CELL, rel)
            assert os.path.exists(mirror), "the run removed " + rel
            with open(full, "rb") as a, open(mirror, "rb") as b:
                assert a.read() == b.read(), "the run rewrote " + rel
            looked += 1
    assert looked >= 7, "only %d files were compared against the shipped tree" % looked


def test_the_frozen_calls_were_actually_made(report):
    ticks = 0
    lands = 0
    for name in sorted(cases.SETS):
        plan = cases.SETS[name]
        ticks += int(plan["ticks"])
        lands += sum(1 for row in plan["ev"] if row[1] == "a")
    for plan in gen.batch(int(os.environ["RUN_NONCE"]),
                          int(os.environ.get("RUN_WIDE", "300"))):
        ticks += int(plan["ticks"])
        lands += sum(1 for row in plan["ev"] if row[1] == "a")
    hits = report.get("hits") or {}
    assert hits.get("publish", 0) >= ticks, \
        "the machine published on %d ticks, not the %d the streams have" \
        % (hits.get("publish", 0), ticks)
    assert hits.get("arrive", 0) >= lands, \
        "the machine handled %d arrivals, not the %d the streams have" \
        % (hits.get("arrive", 0), lands)


def test_every_stream_ran(report, wanted):
    runs = report.get("runs") or {}
    missing = sorted(set(wanted) - set(runs))
    assert not missing, "no rows for %d stream(s), first %s" \
        % (len(missing), missing[:4])
    broke = sorted(k for k in runs if "error" in runs[k])
    assert not broke, "the policy raised on %d stream(s): %s" \
        % (len(broke), runs[broke[0]]["error"][-300:] if broke else "")


@pytest.mark.parametrize("name", sorted(cases.SETS))
def test_enumerated(report, wanted, name):
    got = (report.get("runs") or {}).get(name)
    assert got is not None, "no rows for " + name
    want = wanted[name]
    assert got.get("park") == want["park"], \
        "%s: parked rows %s, expected %s" % (name, got.get("park"), want["park"])
    mine = [list(r) for r in got.get("ev", [])]
    theirs = [list(r) for r in want["ev"]]
    if mine != theirs:
        for i, (a, b) in enumerate(zip(mine, theirs)):
            if a != b:
                pytest.fail("%s: row %d is %s, expected %s" % (name, i, a, b))
        pytest.fail("%s: emitted %d rows, expected %d"
                    % (name, len(mine), len(theirs)))


def test_generated_streams(report, wanted):
    runs = report.get("runs") or {}
    bad = []
    for name in sorted(wanted):
        if name in cases.SETS:
            continue
        got = runs.get(name) or {}
        want = wanted[name]
        if [list(r) for r in got.get("ev", [])] != [list(r) for r in want["ev"]] \
                or got.get("park") != want["park"]:
            bad.append(name)
    assert not bad, "%d generated stream(s) wrong, first %s" % (len(bad), bad[:5])
