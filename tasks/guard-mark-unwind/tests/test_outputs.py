"""Verifier for the guard mark unwind task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather
than only in STATE.md because this is the file the run audit and the quality review read.

What the run produced is in /work/run/out.json, written by /tests/runner.py, the only
process that executed anything the agent wrote. Nothing in this file imports, execs or
subprocesses agent code. It reads that JSON as hostile input and grades it against
/tests/oracle.py, a sealed second implementation of the same specification that shares no
code with the tree, and against /tests/gt.json, which is root-only and was never visible
to the run.

WHAT IS GRADED, on every program, exactly, with no partial credit:

  1. THE TRACE. The ordered list of events the runtime emitted: which fiber ran, which
     token it produced, which guard opened and closed and how, which guard was marked and
     why, which mark was delivered to which fiber, which cleanup block began, which band
     opened and closed and with what, which fiber ended carrying what. Every one of those
     rows is emitted by kern/loop.py, which is not an editable artifact, so the trace
     records what the runtime actually did rather than what a submission says it did.

  2. THE TOKENS. Every fiber's own list of emitted tokens, in order. Stated honestly this
     is a cross-check rather than an independent axis: the trace already carries a row per
     token, so the two cannot disagree unless a submission has written one of them without
     the other - the token lists are read off the fiber objects while the trace is read off
     the emitter. What it buys is legibility. The mistake this task turns on, attributing a
     mark to the innermost marked guard instead of the outermost, shows up as one extra
     token in an otherwise perfect run, and a token diff says that in one line where a row
     index does not. Measured: across 427 programs no cheat in the suite differs on tokens
     while agreeing on the trace, which is what "cross-check" means and why it is described
     that way here rather than counted as a second axis.

TWO PROGRAM SETS, and the second is the reason an answer key is worth nothing:

  The enumerated set in cases.py is twenty-seven programs, one per rule, including the
  must-still-work side of each fence. It is fixed, it is in the bundle, and its expected
  results are in gt.json.

  The differential set is three hundred programs built by gen.py from RUN_NONCE, which
  test.sh makes from /dev/urandom inside the verifier container at trial time. Those
  programs did not exist when the submission was written and their expected traces are
  produced here by the sealed model after the run, so there is nothing to hardcode, no
  table to paste, and no report to forge: a submission has to actually implement the rules
  to produce the right events for a program it has never seen. This is what replaces the
  usual counter-and-budget accounting, and it is strictly stronger, because the thing being
  checked is the whole behaviour rather than a summary of it.

  gt.json is therefore a tripwire rather than the answer: the model is required to
  reproduce it for the enumerated set, so a drift in oracle.py fails loudly instead of
  quietly regrading the task.

  On determinism, since a seeded set invites the question: both the runtime and the model
  are deterministic functions of a program, so a correct submission passes every run with
  certainty - there is no flake to trade against. What the nonce randomises is only which
  programs a WRONG submission is caught by, and the reference has been checked against the
  model on 3027 programs across many seeds with no disagreement. Nothing here depends on
  wall clock time, on the network, or on any ordering that is not itself under test.

INTEGRITY, because the verifier executes agent code:

  - The executed tree outside the four declared artifacts must be byte-identical to the
    pristine copy after the run.
  - Every sealed runtime function is fingerprinted as it actually existed in the running
    interpreter, at import and again when each program finished, against digests derived
    here by compiling the pristine sources - nothing is executed to do it. That catches a
    submission that leaves the files alone and rebinds a function instead.
  - Trace rows are appended by a closure the runner owns, which refuses any caller that is
    not Loop.ev itself, so a submission cannot write its own trace.
  - The interpreter's own tally of entries into Loop.ev must equal the number of trace
    rows, and the instrumentation must still have been registered and armed when each
    program ended. On 3.12 that tally comes from sys.monitoring, on older interpreters
    from the profile hook, and the grader will insist on the former when
    REQUIRE_MONITORING is set - test.sh does not set it, and the reason is written there.
  - The report must carry the run nonce, so a report planted before the run cannot pass.

DELIBERATELY NOT GRADED, because grading them would measure an implementation choice
rather than behaviour (the run-audit lesson: a graded quantity that two correct
implementations disagree on is a trap, not a test):

  - How many times a submission asks a question. Consulting the chain once per checkpoint
    or five times changes nothing observable, and no count of policy calls is compared.
  - Which data structures a submission keeps, or whether it caches the window between
    checkpoints, as long as the answers it gives are the ones the rules require.
  - Anything about wall clock time or memory. The virtual clock in the trace is the
    runtime's own and is not a measure of the submission's cost.

  Six alternative correct implementations live in authoring/variants and all six must
  score 1: the window taken as an outward slice, the same thing by index arithmetic, the
  two halves of the resting rule tested in the opposite order, the band's ordering kept
  by insertion rather than sorted at the close, the ordering built by grouping, and one
  that clears a mark as its guard takes the cut - which is provably unobservable, because
  the guard has already left every chain by then, and was proved so on 6026 programs
  against the sealed model before it was moved out of the cheat suite.
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

RUN_OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE = os.environ.get("PRISTINE_DIR", "/pristine")
HERE = os.path.dirname(os.path.abspath(__file__))

# The declared artifacts: the only files a submission may replace. Everything else in the
# tree is compared byte for byte against the pristine copy after the run.
ARTIFACTS = ("kern/pick.py", "kern/stop.py", "kern/knot.py", "kern/wake.py")

DELIVERY = ("outer-wins", "outer-wins-deep", "shield-owns-mark", "shield-hides-outer",
            "shield-drop", "unmarked-guard-passes-it")
CLOCK = ("no-mark-no-cut", "mark-twice", "zero-wait", "deadline-at-entry",
         "deadline-wakes-sleeper", "deadline-elsewhere", "cross-fiber-mark",
         "spawn-inherits-band")
CLEANUP = ("cleanup-outside", "cleanup-under-outer-mark", "cleanup-shielded",
           "cleanup-raises")
BANDS = ("band-holds", "band-restamp", "band-snag", "band-own-mark",
         "stale-stamp")
REPORT = ("bundle-order", "outer-outranks-bundle", "nested-band",
          "shielded-child-survives", "err-passes-guards")


def load():
    with open(RUN_OUT) as fh:
        body = fh.read()
    if not body.strip():
        pytest.fail("the run produced no report")
    try:
        rep = json.loads(body)
    except ValueError as exc:
        pytest.fail("the run's report is not JSON: %s" % exc)
    if not isinstance(rep, dict):
        pytest.fail("the run's report is not an object")
    for key in ("nonce", "count", "reports", "errors"):
        if key not in rep:
            pytest.fail("the run's report has no %s" % key)
    if not isinstance(rep["reports"], dict) or not isinstance(rep["errors"], dict):
        pytest.fail("the run's report is malformed")
    return rep


REP = load()
PLAN = dict(runner.plan(os.environ.get("RUN_NONCE", ""),
                        int(os.environ.get("RUN_COUNT", "300"))))
WANT = {}


def model(name):
    if name not in WANT:
        WANT[name] = norm(oracle.solve(PLAN[name]))
    return WANT[name]


def norm(res):
    return ([tuple(r) for r in res["tr"]],
            tuple((int(a), str(b), tuple(c)) for a, b, c in res["tk"]))


def got(name):
    """Read one program's result out of the report, treating it as hostile."""
    body = REP["reports"].get(name)
    if not isinstance(body, dict):
        return None, "no report for %s" % name
    try:
        tr = [tuple(r) for r in body["tr"]]
        tk = tuple((int(a), str(b), tuple(c)) for a, b, c in body["tk"])
    except (KeyError, TypeError, ValueError) as exc:
        return None, "unreadable report for %s: %s" % (name, exc)
    return (tr, tk), None


def show(row):
    return " ".join(str(x) for x in row)


def diff(name):
    """None when this program is exactly right, else a short human-readable reason."""
    mine, why = got(name)
    if mine is None:
        return why
    want = model(name)
    if mine[0] != want[0]:
        for i in range(max(len(mine[0]), len(want[0]))):
            a = mine[0][i] if i < len(mine[0]) else None
            b = want[0][i] if i < len(want[0]) else None
            if a != b:
                return ("%s: trace row %d is %s, expected %s"
                        % (name, i, show(a) if a else "missing",
                           show(b) if b else "nothing"))
    if mine[1] != want[1]:
        return ("%s: tokens are %s, expected %s"
                % (name, [list(c) for _, _, c in mine[1]],
                   [list(c) for _, _, c in want[1]]))
    return None


def sweep(names):
    bad = [d for d in (diff(n) for n in names) if d]
    if bad:
        pytest.fail("%d of %d programs wrong\n%s"
                    % (len(bad), len(names), "\n".join(bad[:6])))


def randoms():
    return sorted(n for n in PLAN if n not in cases.PROGS)


# ---------------------------------------------------------------- the run happened

def test_the_run_completed():
    """Every planned program reported, nothing raised, and the report is this run's."""
    assert REP["nonce"] == os.environ.get("RUN_NONCE", ""), \
        "the report does not carry this run's nonce"
    assert not REP["errors"], \
        "the run raised on %d programs: %s" % (
            len(REP["errors"]), sorted(REP["errors"])[:4])
    missing = [n for n in PLAN if n not in REP["reports"]]
    assert not missing, "no result for %d programs: %s" % (len(missing), missing[:6])


# ---------------------------------------------------------------- the rules, one by one

def test_delivery_window_and_attribution():
    """Which mark reaches a fiber, and which guard takes the cut: the window a shield
    closes, outermost-first, and only ever a guard that is itself marked."""
    sweep(DELIVERY)


def test_marks_deadlines_and_inheritance():
    """Marks are sticky and local; deadlines land where they belong; children inherit
    the chain the band was opened with."""
    sweep(CLOCK)


def test_cleanup_blocks():
    """Cleanup runs outside its own guard, is abandoned by a cut, and the newer of two
    in-flight exceptions is the one that keeps travelling."""
    sweep(CLEANUP)


def test_band_close_and_unwinding():
    """A fiber cannot leave a band while a child is alive, is asked again when the last
    one ends, and marks the band's guard when it unwinds into it."""
    sweep(BANDS)


def test_band_reporting():
    """What leaves a band: an enclosing mark outranks the collected payloads, which are
    otherwise ordered by when each child ended."""
    sweep(REPORT)


def test_random_programs():
    """Three hundred programs neither the author nor the submission has seen, graded
    against the sealed model. This is the axis that cannot be answered from a table."""
    sweep(randoms())


# ---------------------------------------------------------------- the model itself

def test_ground_truth_matches_the_model():
    """Tripwire: the sealed model still produces the results recorded at build time."""
    with open(os.path.join(HERE, "gt.json")) as fh:
        gt = json.load(fh)
    assert sorted(gt["cases"]) == sorted(cases.PROGS), \
        "gt.json and cases.py describe different program sets"
    for name in sorted(cases.PROGS):
        want = model(name)
        rows = [tuple(r) for r in gt["cases"][name]["tr"]]
        toks = tuple((int(a), str(b), tuple(c)) for a, b, c in gt["cases"][name]["tk"])
        assert rows == want[0], "oracle.py has drifted on %s" % name
        assert toks == want[1], "oracle.py has drifted on %s" % name


# ---------------------------------------------------------------- integrity

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
    if not os.path.isdir(APP_DIR) or not os.path.isdir(PRISTINE):
        pytest.skip("no work tree to compare")
    mine, base = walk(APP_DIR), walk(PRISTINE)
    for rel in sorted(set(mine) | set(base)):
        if rel in ARTIFACTS:
            continue
        assert rel in mine, "%s is missing from the executed tree" % rel
        assert rel in base, "%s is not part of the shipped tree" % rel
        assert mine[rel] == base[rel], "%s was modified" % rel


def find(code, name):
    for k in code.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == name:
            return k
    raise KeyError(name)


def baseline():
    """Digests of the sealed functions, derived by COMPILING the pristine sources."""
    out = {}
    for rel, qual in runner.SEALED:
        with open(os.path.join(PRISTINE, rel)) as fh:
            top = compile(fh.read(), rel, "exec")
        node = top
        for part in qual.split("."):
            node = find(node, part)
        out["%s:%s" % (rel, qual)] = runner.fingerprint(node)
    return runner.seal(out)


def test_functions_untouched():
    """The runtime functions that ran are the ones that shipped, not replacements."""
    if not os.path.isdir(PRISTINE):
        pytest.skip("no pristine tree to compare")
    want = baseline()
    bad = [n for n in sorted(REP["reports"])
           if REP["reports"][n].get("fp") != want or REP["reports"][n].get("fp2") != want]
    assert not bad, "runtime functions were replaced during %d programs: %s" % (
        len(bad), bad[:4])


def test_instrumentation_intact():
    """Every trace row came out of Loop.ev, and the interpreter's own instrumentation was
    still registered and still armed when each program ended.

    The per-program check is the row count: the interpreter counted the entries into
    Loop.ev itself, from a closure in the runner, so a trace carrying rows the runtime did
    not emit fails here even before it fails against the model. Whether the decision
    functions were consulted is only meaningful in aggregate, since plenty of programs
    hold no checkpoint at all and a correct submission is never asked about them."""
    need = os.environ.get("REQUIRE_MONITORING") == "1"
    bad = []
    asked = 0
    for n in sorted(REP["reports"]):
        r = REP["reports"][n]
        mon = r.get("mon") or {}
        asked += mon.get("pick") or 0
        if not r.get("arm"):
            bad.append("%s: instrumentation was disturbed" % n)
        elif need and r.get("how") != "monitoring":
            bad.append("%s: instrumentation fell back to %s" % (n, r.get("how")))
        elif mon.get("ev") != len(r.get("tr") or []):
            bad.append("%s: %s trace rows but %s came from the runtime"
                       % (n, len(r.get("tr") or []), mon.get("ev")))
    assert not bad, "\n".join(bad[:6])
    assert asked > 0, "the delivery decision was never asked on any program"
