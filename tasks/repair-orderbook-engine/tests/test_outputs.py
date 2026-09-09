"""Verifier for the slice trip fill task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather
than only in STATE.md because this is the file the run audit and the quality review read.

What the run produced is in /work/run/out.json, written by /tests/runner.py, the only
process that executed anything the agent wrote. Nothing in this file imports, execs or
subprocesses agent code. It reads that JSON as hostile input and grades it against
/tests/oracle.py, a sealed second implementation of the same rules that shares no code
with the tree, and against /tests/gt.json, which is root-only and was never visible to
the run.

WHAT IS GRADED, on every session, exactly, with no partial credit:

  THE EVENT STREAM. The ordered list of rows the engine emitted: every fill with its
  aggressor, its resting order, its price and its size; every order pulled and why; every
  re-disclosure and the size it showed; every order that joined the book; every order
  parked off it and every one that fired; and, at the end, the resting book in queue
  order and the orders still parked. That last block is the final state rather than a
  separate axis, and it is what stops a submission from getting the fills right by
  leaving the book wrong.

  Every one of those rows is written by mkt/ev.py, which is not an editable artifact, so
  the stream records what the engine actually did rather than what a submission says it
  did.

SESSION SETS, with nonce-generated inputs preventing a reusable answer key:

  The enumerated set in cases.py is sixty-seven sessions, named for the
  reading each exists to fail and including the must-still-work side of every fence. It
  is fixed, it is in the bundle, and its expected results are in gt.json.

  The differential set is three hundred sessions built by gen.py from RUN_NONCE, which
  test.sh makes from /dev/urandom inside the verifier container at trial time. Those
  sessions did not exist when the submission was written and their expected events are
  produced here by the sealed model after the run, so there is nothing to hardcode and no
  table to paste. The generated sessions combine the same rules in different orders;
  named cases separately ensure each specified interaction has a fixed regression.

  The deep set is four large sessions from the same nonce, in two shapes, because there
  are two ways to be right about the rules and unaffordable. Two combine thousands of
  parked orders with many fills against deeply sliced liquidity. The other two combine
  thousands of mostly unreachable resting orders with repeated all-or-nothing arrivals.
  The instruction states the worker deadline and provides a sample of each shape. The
  wrapper enforces that deadline; this file does not compare measured durations against
  a reference runtime or require a particular data structure.

  Fill-boundary execution adds 120 generated small sessions and one large book session.
  They exercise descendant execution and nested whole-order rollback, and what a failed
  whole fired: kept out of the parked set, announced after the cancellation line and run
  again in arrival order, at any depth and after each enclosing failure. One of the six
  small families, spark, aims order-pace whole orders at parked orders in the same way. The small
  generator creates at most sixteen trip-bearing messages in a session; the large
  family has at most one waiting at once, inside the specified limit of twenty-four.

  gt.json is therefore a tripwire rather than the answer: the model is required to
  reproduce it for the enumerated set, so a drift in oracle.py fails loudly instead of
  quietly regrading the task.

  Each session and its expected event stream are deterministic given the run nonce.
  The model uses a scanned flat book with explicit queue priority, an undo trail for
  all-or-nothing admission, and price buckets for parked orders. A separate message
  arrival stamp orders activations; order IDs and changing book priority cannot replace
  it. No event comparison depends on wall clock time or on the network.

INTEGRITY, because the verifier executes agent code:

  - The executed tree outside the five declared artifacts must be byte-identical to the
    pristine copy after the run.
  - Every sealed engine function is fingerprinted as it actually existed in the running
    interpreter, at import and again when each session finished, against digests derived
    here by compiling the pristine sources - nothing is executed to do it. That catches a
    submission that leaves the files alone and rebinds a driver function instead.
  - Event rows are appended by a closure the runner owns, which refuses any caller that
    is not Emit.row itself, so a submission cannot write its own stream.
  - The interpreter's tally of entries into the committed sink must equal the row count,
    and the instrumentation must still have been registered and armed when each session
    ended. On 3.12 that tally comes from sys.monitoring, on older interpreters from the
    profile hook, and the grader will insist on the former when REQUIRE_MONITORING is set.
  - The report must carry the run nonce, so a report planted before the run cannot pass.

DELIBERATELY NOT GRADED, because grading them would measure an implementation choice
rather than behaviour (the run-audit lesson: a graded quantity that two correct
implementations disagree on is a trap, not a test):

  - How a submission holds the parked orders, the book, or the queue, as long as the
    events it produces are the ones the rules require.
  - Exact decision-call totals. The named entry points walk, avail, blocks, admit and
    check must each be exercised somewhere in the population, as the instruction
    requires, but no fixed call count or per-session call pattern is prescribed.
  - Wall clock, as a number. The scale bound is the timeout on the run, not a measured
    duration compared here.

  Correctness is the complete ordered output, not agreement with the reference's
  internal algorithm. Failed admission must undo every visible effect except a firing,
  successful admission must execute the full walk, and simultaneous fill consequences
  must follow the serialization order stated in the instruction.
"""

import ast
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
ARTIFACTS = ("eng/take.py", "eng/shown.py", "eng/hand.py", "eng/hold.py", "eng/trip.py")

DISCLOSE = ("show-interleaves", "show-alone-refills", "show-goes-to-the-back",
            "show-on-a-resting-remainder", "show-larger-than-the-order")
HAND = ("hand-pulled-at-the-front", "hand-takes-the-hidden-part",
        "hand-pull-does-not-step", "other-hand-steps")
BAND = ("band-steps-with-the-fills", "band-stops-the-walk", "band-does-not-look-past",
        "band-off-a-stale-mark", "limit-stops-the-walk")
WHOLE = ("whole-leaves-nothing-behind", "whole-fills-exactly",
         "whole-discounts-the-same-hand", "whole-discounts-past-the-band",
         "whole-counts-the-step", "whole-counts-the-hidden-part",
         "whole-never-rests", "whole-market-order")
TRIP = ("trip-lands-on-the-fill", "trip-cascades", "trip-order-is-arrival",
        "trip-arrival-with-unordered-ids", "trip-before-disclosure",
        "trip-waits-for-a-fill", "trip-pulled-before-it-fires", "trip-sell-side")
ORDINARY = ("plain-cross", "plain-rests-both-sides", "part-cancels-the-remainder",
            "market-cancels-the-remainder", "pull-an-unknown-id",
            "pull-a-partly-filled-rest")
FIRED = ("whole-keeps-what-it-fired", "whole-fires-nothing-without-a-fill",
         "whole-fired-batch-is-arrival-order", "whole-fired-waits-its-turn")
FIRED_FILL = ("fill-parent-failure-keeps-child-fired", "fill-nested-failure-fires-again",
              "fill-fired-batch-precedes-waiting-siblings",
              "fill-fired-whole-stays-fired-under-parent-failure",
              "fill-refired-order-fires-more", "fill-failure-with-nothing-fired",
              "fill-refired-order-starts-over", "fill-successful-child-firings-run-again")
FILL = tuple(n for n in cases.SESS if n.startswith("fill-") and n not in FIRED_FILL) + (
    "order-selector-preserves-deferred-execution",)


def load():
    """Read the run's report, treating everything about it as hostile.

    A run that died, was killed on the clock, or wrote something unreadable must come out
    as a named failing test rather than as an error while this module is being imported,
    so the reward is 0 for a reason the report says out loud.
    """
    try:
        with open(RUN_OUT) as fh:
            body = fh.read()
    except OSError as exc:
        return {"broken": "the run left no report: %s" % exc}
    if not body.strip():
        return {"broken": "the run produced no report - it did not finish"}
    try:
        rep = json.loads(body)
    except ValueError as exc:
        return {"broken": "the run's report is not JSON: %s" % exc}
    if not isinstance(rep, dict):
        return {"broken": "the run's report is not an object"}
    for key in ("nonce", "small", "deep", "reports", "errors"):
        if key not in rep:
            return {"broken": "the run's report has no %s" % key}
    if not isinstance(rep["reports"], dict) or not isinstance(rep["errors"], dict):
        return {"broken": "the run's report is malformed"}
    return rep


def alive():
    if REP.get("broken"):
        pytest.fail(REP["broken"])


REP = load()
PLAN = dict(runner.plan(os.environ.get("RUN_NONCE", ""),
                        int(os.environ.get("RUN_SMALL", "300")),
                        int(os.environ.get("RUN_DEEP", "4"))))
WANT = {}


def model(name):
    if name not in WANT:
        WANT[name] = tuple(tuple(r) for r in oracle.solve(PLAN[name]))
    return WANT[name]


def got(name):
    """Read one session's result out of the report, treating it as hostile."""
    body = (REP.get("reports") or {}).get(name)
    if not isinstance(body, dict):
        return None, "no report for %s" % name
    try:
        return tuple(tuple(r) for r in body["ev"]), None
    except (KeyError, TypeError, ValueError) as exc:
        return None, "unreadable report for %s: %s" % (name, exc)


def show(row):
    return " ".join(str(x) for x in row) if row else "nothing"


def diff(name):
    """None when this session is exactly right, else a short readable reason."""
    mine, why = got(name)
    if mine is None:
        return why
    want = model(name)
    if mine == want:
        return None
    for i in range(max(len(mine), len(want))):
        a = mine[i] if i < len(mine) else None
        b = want[i] if i < len(want) else None
        if a != b:
            return "%s: event %d is %s, expected %s" % (name, i, show(a), show(b))
    return "%s: event stream differs" % name


def sweep(names):
    alive()
    bad = [d for d in (diff(n) for n in names) if d]
    if bad:
        pytest.fail("%d of %d sessions wrong\n%s"
                    % (len(bad), len(names), "\n".join(bad[:6])))


def smalls():
    return [n for n in PLAN if n not in cases.SESS and not n.startswith("deep-")]


def deeps():
    return sorted(n for n in PLAN if n.startswith("deep-"))


# ---------------------------------------------------------------- the run happened

def test_the_run_completed():
    """Every planned session reported, nothing raised, and the report is this run's."""
    alive()
    assert REP["nonce"] == os.environ.get("RUN_NONCE", ""), \
        "the report does not carry this run's nonce"
    assert not REP["errors"], \
        "the run raised on %d sessions: %s" % (
            len(REP["errors"]), sorted(REP["errors"])[:4])
    missing = [n for n in PLAN if n not in REP["reports"]]
    assert not missing, "no result for %d sessions: %s" % (len(missing), missing[:6])


# ---------------------------------------------------------------- the rules, one by one

def test_disclosure():
    """How much of a partly shown order may be taken now, what it shows next, and where
    it stands in its queue afterwards."""
    sweep(DISCLOSE)


def test_same_participant():
    """A resting order belonging to the incoming order's own participant goes, whole,
    without a fill - and the walk carries on from what is left."""
    sweep(HAND)


def test_the_band():
    """Where the walk is allowed to trade, measured against the price the last fill
    made, and where it stops rather than reaching past."""
    sweep(BAND)


def test_all_or_nothing():
    """An order that must fill entirely either does, or leaves the book exactly as it
    found it."""
    sweep(WHOLE)


def test_activation():
    """When the parked orders are asked, which of them fire, in what order they are
    taken, and when their own walks happen."""
    sweep(TRIP)


def test_what_a_failed_whole_fired():
    """A whole that came up short after a fill that fired keeps the firing: announced
    after its cancellation line, run in arrival order from the end of the waiting queue -
    and a failed whole that made no fill fired nothing."""
    sweep(FIRED)


def test_ordinary_sessions():
    """The must-still-work side: plain crossing, resting, cancelling a remainder, and
    pulling."""
    sweep(ORDINARY)


def test_generated_sessions():
    """Three hundred sessions neither the author nor the submission has seen, graded
    against the sealed model. This is the axis that cannot be answered from a table."""
    sweep(smalls())


def test_deep_sessions():
    """The same rules at a scale where the shape of the engine starts to matter."""
    sweep(deeps())


def test_fill_boundary_interactions():
    """Execution, output ordering and nested rollback hold at each fill boundary."""
    sweep(FILL)


def test_fill_what_a_failed_whole_fired():
    """Under fill pace the kept firings run at once, before anything that was waiting on
    the failed order, from full size, whether they fired inside a child that committed or
    one that failed, and again after each enclosing failure."""
    sweep(FIRED_FILL)


def test_fill_generated_sessions():
    """Nonce-generated combinations include whole children, later pulls and both sides."""
    sweep(sorted(n for n in PLAN if n.startswith("fill-random-")))


def test_fill_deep_sessions():
    """Nested commit and restore leave a large untouched book correctly represented."""
    sweep(sorted(n for n in PLAN if n.startswith("fill-deepbook-")))


# ---------------------------------------------------------------- the model itself

def test_ground_truth_matches_the_model():
    """Tripwire: the sealed model still produces the events recorded at build time."""
    with open(os.path.join(HERE, "gt.json")) as fh:
        gt = json.load(fh)
    assert sorted(gt["cases"]) == sorted(cases.SESS), \
        "gt.json and cases.py describe different session sets"
    for name in sorted(cases.SESS):
        want = model(name)
        rows = tuple(tuple(r) for r in gt["cases"][name])
        assert rows == want, "oracle.py has drifted on %s" % name


# ---------------------------------------------------------------- integrity

def walk_tree(root):
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
    """Everything outside the five declared artifacts is the code that shipped."""
    if not os.path.isdir(APP_DIR) or not os.path.isdir(PRISTINE):
        pytest.skip("no work tree to compare")
    mine, base = walk_tree(APP_DIR), walk_tree(PRISTINE)
    for rel in sorted(set(mine) | set(base)):
        if rel in ARTIFACTS:
            continue
        assert rel in mine, "%s is missing from the executed tree" % rel
        assert rel in base, "%s is not part of the shipped tree" % rel
        assert mine[rel] == base[rel], "%s was modified" % rel


def function_interfaces(path):
    """Inspect source without importing it; annotations and helper additions are free."""
    with open(path) as source:
        module = ast.parse(source.read(), filename=path)
    interfaces = {}
    for node in module.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        args = node.args
        positional = args.posonlyargs + args.args
        default_start = len(positional) - len(args.defaults)
        signature = []
        for index, arg in enumerate(positional):
            kind = "positional-only" if index < len(args.posonlyargs) else "positional-or-keyword"
            signature.append((kind, arg.arg, index >= default_start))
        if args.vararg is not None:
            signature.append(("variadic-positional", args.vararg.arg, False))
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            signature.append(("keyword-only", arg.arg, default is not None))
        if args.kwarg is not None:
            signature.append(("variadic-keyword", args.kwarg.arg, False))
        interfaces[node.name] = tuple(signature)
    return interfaces


def test_declared_function_interfaces_preserved():
    """Every shipped synchronous function keeps its parameters and calling convention."""
    for rel in ARTIFACTS:
        expected = function_interfaces(os.path.join(PRISTINE, rel))
        actual = function_interfaces(os.path.join(APP_DIR, rel))
        for name, signature in expected.items():
            assert name in actual, "%s: function %s is missing" % (rel, name)
            assert actual[name] == signature, "%s: parameters of %s changed" % (rel, name)


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
            node = compile(fh.read(), rel, "exec")
        for part in qual.split("."):
            node = find(node, part)
        out["%s:%s" % (rel, qual)] = runner.fingerprint(node)
    return runner.seal(out)


def test_functions_untouched():
    """The engine functions that ran are the ones that shipped, not replacements."""
    alive()
    if not os.path.isdir(PRISTINE):
        pytest.skip("no pristine tree to compare")
    want = baseline()
    bad = [n for n in sorted(REP["reports"])
           if REP["reports"][n].get("fp") != want or REP["reports"][n].get("fp2") != want]
    assert not bad, "engine functions were replaced during %d sessions: %s" % (
        len(bad), bad[:4])


def test_instrumentation_intact():
    """Every event row came out of Emit.row, and the interpreter's own instrumentation
    was still registered and still armed when each session ended.

    The per-session check is the row count: the interpreter counted entries into the
    trusted committed sink, which only accepts calls from the frozen Emit.row code.
    Private Emit instances may buffer speculative output without committing it.
    A stream carrying rows the engine did not emit fails here before the model check.
    Whether a particular
    decision was consulted is only meaningful in aggregate, because plenty of sessions
    never reach one - no session with an empty book asks about disclosure - and a correct
    submission is not asked about what does not arise."""
    alive()
    need = os.environ.get("REQUIRE_MONITORING") == "1"
    bad = []
    asked = {"walk": 0, "avail": 0, "admit": 0, "check": 0, "blocks": 0}
    for n in sorted(REP["reports"]):
        r = REP["reports"][n]
        mon = r.get("mon") or {}
        for k in asked:
            asked[k] += mon.get(k) or 0
        if not r.get("arm"):
            bad.append("%s: instrumentation was disturbed" % n)
        elif need and r.get("how") != "monitoring":
            bad.append("%s: instrumentation fell back to %s" % (n, r.get("how")))
        elif mon.get("row") != len(r.get("ev") or []):
            bad.append("%s: %s event rows but %s came from the engine"
                       % (n, len(r.get("ev") or []), mon.get("row")))
    assert not bad, "\n".join(bad[:6])
    empty = [k for k, v in asked.items() if v == 0]
    assert not empty, "these decisions were never asked on any session: %s" % empty
