"""Verifier for the panel settle order task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather
than only in STATE.md because this is the file the run audit and the quality review read.

What the run produced is in the report written by /tests/runner.py, the only process that
executed anything the submission wrote. Nothing in this file imports, execs or subprocesses
agent code. It reads that report as hostile input and grades it against /tests/oracle.py, a
second implementation of the same specification that shares no code with the tree, and
against /tests/gt.json, which is root-only and was never visible to the run.

WHAT IS GRADED, on every panel, exactly, with no partial credit:

  1. THE LEDGER. The ordered rows the panel produced: every feed that moved when a round's
     writes landed, every gauge that was committed and the value it took, and every latch
     that tripped and the value it reported. Every one of those rows is emitted by
     pnl/loop.py, which is not an editable artifact, so the ledger records what the engine
     actually did rather than what a submission says it did.

  2. THE FINAL VALUES. What every entry in the panel was left holding. Stated honestly this
     is a cross-check rather than an independent axis: a submission that produced the right
     ledger has already produced these. What it buys is legibility, because a submission
     that settles the panel to the right numbers by the wrong route fails on the ledger and
     the two together say which of the two happened.

TWO PANEL SETS, and the second is why an answer key is worth nothing:

  The enumerated set in cases.py is twenty panels, one per rule, including the must-work
  side of every fence. It is fixed, it is in the bundle, and its expected results are in
  gt.json.

  The generated set is three hundred panels built by gen.py from PSO_NONCE, which test.sh
  makes from /dev/urandom inside this container at trial time. Those panels did not exist
  when the submission was written and their expected ledgers are produced here by the
  sealed model after the run, so there is nothing to hardcode, no table to paste and no
  report to forge: a submission has to actually implement the rules to produce the right
  rows for a panel it has never seen.

  gt.json is therefore a tripwire rather than the answer: the model is required to
  reproduce it for the enumerated set, so a drift in oracle.py fails loudly instead of
  quietly regrading the task.

  On determinism, since a seeded set invites the question: the engine and the model are
  both deterministic functions of a panel, so a correct submission passes every run with
  certainty and there is no flake to trade against. What the nonce randomises is only which
  panels a WRONG submission is caught by. Nothing here depends on wall clock time, on the
  network, or on any ordering that is not itself under test.

  A panel the model cannot settle inside its caps, or one that would need a gauge to run
  twice in a round, is not graded at all. See oracle.check.

INTEGRITY, because the verifier executes agent code:

  - The executed tree outside the four declared artifacts must be byte-identical to the
    pristine copy after the run.
  - Every sealed engine function is hashed as it actually existed in the running
    interpreter, at import and again after each panel, against digests derived here by
    COMPILING the pristine sources - nothing is executed to do it. That catches a
    submission that leaves the files alone and rebinds a function instead.
  - Ledger rows are appended by a closure the runner owns, which refuses any caller that is
    not the loop's emitter, so a submission cannot write its own ledger.
  - The interpreter's own count of entries into that emitter must equal the number of rows
    reported, and the instrumentation must still have been registered and armed at the end.
  - The report must carry the run nonce, so a report planted before the run cannot pass.

DELIBERATELY NOT GRADED, because grading them would measure an implementation choice rather
than behaviour (the run-audit lesson: a graded quantity two correct implementations disagree
on is a trap, not a test):

  - How many times a submission evaluates a gauge before committing it. A gauge reached too
    early is evaluated and thrown away, and whether an implementation reaches it once or
    three times before it settles changes nothing observable. No count of evaluations is
    compared.
  - Whether a submission updates a gauge's wiring on a run it then discards, or only on the
    run it commits. Measured over 500 panels: no observable difference. It ships as a
    variant and must score 1.
  - Which data structures a submission keeps, whether it caches distances between rounds,
    and what it calls anything.
"""

import hashlib
import json
import os
import types

import pytest

import cases
import gen
import oracle
import runner

REPORT = os.environ.get("PSO_REPORT", "/rep/out.json")
TREE = os.environ.get("PSO_TREE", "/work/app")
PRISTINE = os.environ.get("PSO_PRISTINE", "/pristine")
HERE = os.path.dirname(os.path.abspath(__file__))

ARTIFACTS = ("pnl/ord.py", "pnl/wire.py", "pnl/trip.py", "pnl/same.py")

ORDER = ("order-diamond", "order-scrambled", "tie-declaration")
FLIP = ("flip-deeper", "flip-shallower", "flip-far", "chained-flip", "two-flips")
WAKE = ("drop-wake", "take-wake", "no-move-no-run", "unread-feed", "quiet-panel")
LATCH = ("latch-settles", "latch-no-move", "latch-once", "latch-order", "build-quiet")
BACK = ("write-back-round", "write-back-cascade")


def load():
    try:
        with open(REPORT) as fh:
            body = fh.read()
    except OSError as exc:
        pytest.fail("the run left no report: %s" % exc)
    if not body.strip():
        pytest.fail("the run produced an empty report")
    try:
        rep = json.loads(body)
    except ValueError as exc:
        pytest.fail("the run's report is not JSON: %s" % exc)
    if not isinstance(rep, dict):
        pytest.fail("the run's report is not an object")
    for key in ("nonce", "runs"):
        if key not in rep:
            pytest.fail("the run's report has no %s" % key)
    if not isinstance(rep["runs"], dict):
        pytest.fail("the run's report is malformed")
    return rep


REP = load()
PANELS = dict([(n, cases.PANELS[n]) for n in sorted(cases.PANELS)]
              + gen.build(os.environ.get("PSO_NONCE", ""),
                          int(os.environ.get("PSO_COUNT", "300"))))
WANT = {}


def want(name):
    if name not in WANT:
        WANT[name] = oracle.check(PANELS[name])
    return WANT[name]


def mine(name):
    """One panel's result out of the report, treated as hostile."""
    body = REP["runs"].get(name)
    if not isinstance(body, dict):
        return None, "no result for %s" % name
    if body.get("err"):
        return None, "%s: the engine raised %s" % (name, body["err"])
    try:
        log = tuple(tuple(r) for r in body["log"])
        dump = tuple((str(a), int(b)) for a, b in body["dump"])
    except (KeyError, TypeError, ValueError) as exc:
        return None, "unreadable result for %s: %s" % (name, exc)
    return (log, dump), None


def show(row):
    return " ".join(str(x) for x in row)


def wrong(name):
    """None when this panel is exactly right, else a short readable reason."""
    good = want(name)
    if good is None:
        return None
    got, why = mine(name)
    if got is None:
        return why
    log = tuple(tuple(r) for r in good["log"])
    if got[0] != log:
        for i in range(max(len(got[0]), len(log))):
            a = got[0][i] if i < len(got[0]) else None
            b = log[i] if i < len(log) else None
            if a != b:
                return ("%s: ledger row %d is %s, expected %s"
                        % (name, i, show(a) if a else "missing",
                           show(b) if b else "nothing"))
    if got[1] != tuple(good["dump"]):
        return "%s: final values are %r, expected %r" % (name, got[1], good["dump"])
    return None


def sweep(names):
    bad = [w for w in (wrong(n) for n in names) if w]
    if bad:
        pytest.fail("%d of %d panels wrong\n%s"
                    % (len(bad), len(names), "\n".join(bad[:6])))


def generated():
    return sorted(n for n in PANELS if n not in cases.PANELS)


# ------------------------------------------------------------------ the run happened

def test_the_run_completed():
    """Every planned panel reported, nothing crashed the runner, and the report is this
    run's rather than one prepared earlier."""
    assert REP["nonce"] == os.environ.get("PSO_NONCE", ""), \
        "the report does not carry this run's nonce"
    assert not REP.get("fault"), "the run crashed: %s" % REP.get("fault")
    missing = [n for n in PANELS if n not in REP["runs"]]
    assert not missing, "no result for %d panels: %s" % (len(missing), missing[:6])


# ------------------------------------------------------------------ the rules, one by one

def test_settle_order():
    """Gauges are reached in order of how far they sit from the feeds, and among gauges
    equally far in the order the panel declares them - never in the order they were woken
    and never in declaration order alone."""
    sweep(ORDER)


def test_distance_follows_the_wiring():
    """A conditional that changes which entry it reads changes how far out it stands, so a
    distance is a property of the run rather than of the panel."""
    sweep(FLIP)


def test_what_wakes_a_gauge():
    """A gauge runs when something it reads moves, and only then: an entry it has stopped
    reading no longer wakes it, and an entry it has started reading does."""
    sweep(WAKE)


def test_latches():
    """A latch reports what its entry came to rest at, once per round, in declaration
    order, and nothing trips while the panel is coming up."""
    sweep(LATCH)


def test_write_backs():
    """What a latch writes lands as the next round, in the order the latches tripped, and
    the panel keeps settling until nothing more is written."""
    sweep(BACK)


def test_generated_panels():
    """Three hundred panels neither the author nor the submission has seen, graded against
    the sealed model. This is the axis that cannot be answered from a table."""
    names = generated()
    live = [n for n in names if want(n) is not None]
    assert len(live) > len(names) // 2, \
        "only %d of %d generated panels are well formed" % (len(live), len(names))
    sweep(live)


# ------------------------------------------------------------------ the model itself

def test_ground_truth_matches_the_model():
    """Tripwire: the sealed model still produces the results recorded at build time."""
    with open(os.path.join(HERE, "gt.json")) as fh:
        gt = json.load(fh)
    assert sorted(gt["panels"]) == sorted(cases.PANELS), \
        "gt.json and cases.py describe different panel sets"
    for name in sorted(cases.PANELS):
        good = want(name)
        assert good is not None, "%s is no longer a panel the model will grade" % name
        assert [list(r) for r in good["log"]] == gt["panels"][name]["log"], \
            "oracle.py has drifted on %s" % name
        assert [list(r) for r in good["dump"]] == gt["panels"][name]["dump"], \
            "oracle.py has drifted on %s" % name


# ------------------------------------------------------------------ integrity

def walk(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            if fn.endswith(".pyc"):
                continue
            p = os.path.join(base, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            with open(p, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def test_tree_untouched():
    """Everything outside the four declared artifacts is the code that shipped."""
    if not os.path.isdir(TREE) or not os.path.isdir(PRISTINE):
        pytest.skip("no executed tree to compare")
    got, base = walk(TREE), walk(PRISTINE)
    assert base, "the pristine copy is empty - the comparison would pass vacuously"
    checked = 0
    for rel in sorted(set(got) | set(base)):
        if rel in ARTIFACTS:
            continue
        assert rel in got, "%s is missing from the executed tree" % rel
        assert rel in base, "%s is not part of the shipped tree" % rel
        assert got[rel] == base[rel], "%s was modified" % rel
        checked += 1
    assert checked >= 6, "only %d files were compared" % checked


def inner(code, name):
    for k in code.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == name:
            return k
    raise KeyError(name)


def baseline():
    """Digests of the sealed functions, derived by COMPILING the pristine sources."""
    out = {}
    for mod, path in runner.SEALED:
        src = os.path.join(PRISTINE, "pnl", mod + ".py")
        with open(src) as fh:
            top = compile(fh.read(), src, "exec")
        node = top
        for part in path.split("."):
            node = inner(node, part)
        c = node
        flat = [repr(x) for x in c.co_consts if not hasattr(x, "co_code")]
        blob = b"|".join([c.co_code, repr(c.co_names).encode(),
                          repr(c.co_varnames).encode(), repr(sorted(flat)).encode()])
        out["%s.%s" % (mod, path)] = hashlib.sha256(blob).hexdigest()[:32]
    return out


def test_engine_functions_untouched():
    """The engine functions that ran are the ones that shipped, not replacements."""
    if not os.path.isdir(PRISTINE):
        pytest.skip("no pristine tree to compare")
    want_stamps = baseline()
    got = REP.get("stamps") or {}
    bad = [k for k in sorted(want_stamps) if got.get(k) != want_stamps[k]]
    assert not bad, "engine functions were replaced: %s" % bad[:5]
    assert not REP.get("drift"), "engine functions changed while the panels were running"


def test_ledger_came_from_the_engine():
    """Every row was emitted by the loop, and the instrumentation was still armed at the
    end. The interpreter counted the entries itself, from a closure in the runner."""
    assert REP.get("armed"), "the instrumentation was disturbed during the run"
    if os.environ.get("REQUIRE_MONITORING") == "1":
        assert REP.get("mode") == "monitoring", \
            "the instrumentation fell back to %s" % REP.get("mode")
    assert REP.get("said") == REP.get("rows"), \
        "%s rows were reported but the engine emitted %s" % (REP.get("rows"), REP.get("said"))
    assert (REP.get("rows") or 0) > 0, "no rows at all were emitted"
