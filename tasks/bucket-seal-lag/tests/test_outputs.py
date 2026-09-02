"""Verifier for the bucket seal lag task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here
rather than only in STATE.md because this is the file the run audit and the
quality review read.

What the run produced is in /work/run/out.json, written by /tests/runner.py, the
only process that executed anything the agent wrote. Nothing in this file
imports, execs or subprocesses agent code. It reads that JSON as hostile input
and grades it against /tests/oracle.py, a sealed second implementation of the
same specification that shares no code with the tree, and against /tests/gt.json,
which is root-only and was never visible to the run.

WHAT IS GRADED, on every plan, exactly, with no partial credit:

  1. THE TRACE. The ordered list of events the machine emitted: what each source
     released, announced and when it shut, which item a lift dropped past its
     floor, which bucket opened, what joined it, which bucket was sealed and with
     which members, what arrived for a bucket already sealed, what each sink took,
     what went past the horizon, and the tick the run ended on. Every one of those
     rows is emitted by flow/mach.py, which is not an editable artifact, so the
     trace records what the machine actually did rather than what a submission
     says it did.

  2. THE SINK LISTS. Each sink's own list of the stamps it took, in order. Stated
     honestly this is a cross-check rather than an independent axis: the trace
     already carries a row per sink receipt, so the two cannot disagree unless a
     submission has produced one without the other - the sink lists are collected
     from the rows as the machine runs while the trace is read off the emitter.
     What it buys is legibility. A bucket sealed one tick early loses whatever
     arrives for it afterwards, and a sink list that is short by one stamp says
     that in one line where a row index does not.

TWO PLAN SETS, and the second is the reason an answer key is worth nothing:

  The enumerated set in cases.py is thirty-one plans, one per rule, including the
  must-still-work side of each fence. It is fixed, it is in the bundle, and its
  expected results are in gt.json.

  The differential set is three hundred plans built by gen.py from RUN_NONCE,
  which test.sh makes from /dev/urandom inside the verifier container at trial
  time. Those plans did not exist when the submission was written and their
  expected traces are produced by the sealed model after the run, so there is no
  number to assign, no journal to pad and no table to paste. The cheat suite makes
  the point directly: one cheat carries gt.json's own bytes, is right on every
  enumerated plan, and scores 0.

WHAT IS NOT GRADED, because grading it would measure an implementation choice
rather than a behaviour: how many times a submission consults the graph, what it
caches between ticks, which data structures it keeps, and whether it asks the
question one node at a time or for the whole graph at once. Both readings ship as
correct variants and both are required to score 1. The interpreter's own counts
of entries into the four decision functions are recorded and only ever compared as
floors, for the same reason.

FOUR ATTESTATIONS, because the verifier executes agent code:

  The executed tree outside the declared artifacts must be byte-identical to the
  pristine copy after the run.

  Every sealed machine function must be, as it actually existed in the running
  interpreter at import and again when each plan ended, what the pristine sources
  compile to. Nothing is executed to derive that: the sources are compiled and the
  code objects fingerprinted.

  The interpreter's count of entries into the emitter must equal the number of
  trace rows, and the instrumentation must still have been armed at the end.

  The report must carry the run nonce, so a report planted before the run cannot
  pass.
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

ARTIFACTS = ("flow/emit.py", "flow/route.py", "flow/due.py", "flow/pick.py")

ACCOUNT = ("near-source", "two-hop", "three-hop", "shut-releases",
           "plain-pipe", "all-drained")
LIFTS = ("lift-on-route", "lift-holds", "lift-holds-stale", "two-routes",
         "lift-below-all", "two-sources")
GATHERS = ("gather-onward", "gather-sealed-skip", "arrival-not-emission",
           "inbox-counts", "inbox-onward", "inbox-holds-downstream",
           "inbox-sealed-skip", "gathers-apart")
LOOPS = ("own-bucket-holds-next", "bucket-high-edge", "loop-lap",
         "below-comes-back")
EDGES = ("edge-exact", "box-direct", "two-seals-one-tick", "horizon-cut")
SHIPPED = ("direct", "relay", "redrive")


def load():
    try:
        with open(RUN_OUT) as fh:
            blob = json.load(fh)
    except Exception as exc:
        pytest.fail("the run produced no readable report: %r" % (exc,))
    if not isinstance(blob, dict):
        pytest.fail("the run's report is not an object")
    for key in ("nonce", "reports", "errors"):
        if key not in blob:
            pytest.fail("the run's report has no %r" % key)
    if not isinstance(blob["reports"], dict) or not isinstance(blob["errors"], dict):
        pytest.fail("the run's report is malformed")
    return blob


REP = load()
NONCE = os.environ.get("RUN_NONCE", "")
COUNT = int(os.environ.get("RUN_COUNT", "300"))
PLAN = dict(runner.plan(NONCE, COUNT))
WANT = {}


def model(name):
    if name not in WANT:
        WANT[name] = oracle.play(PLAN[name])
    return WANT[name]


def norm(res):
    return {"tr": [list(r) for r in res["tr"]],
            "sk": dict((k, list(v)) for k, v in res["sk"].items())}


def got(name):
    if name not in PLAN:
        pytest.fail("plan %s is not in the set the grader built" % name)
    r = REP["reports"].get(name)
    if r is None:
        pytest.fail("the run produced no report for %s: %s"
                    % (name, str(REP["errors"].get(name, "missing"))[-500:]))
    for key in ("tr", "sk", "fp", "fp2", "mon", "arm"):
        if key not in r:
            pytest.fail("the report for %s has no %r" % (name, key))
    if not r["arm"]:
        pytest.fail("the instrumentation was not armed at the end of %s" % name)
    if r["fp"] != r["fp2"]:
        pytest.fail("a sealed machine function changed while %s ran" % name)
    if r["mon"].get("ev") != len(r["tr"]):
        pytest.fail("%s reported %d trace rows and the interpreter counted %d "
                    "entries into the emitter"
                    % (name, len(r["tr"]), r["mon"].get("ev")))
    return norm(r)


def show(row):
    return json.dumps(row, separators=(", ", ": "))


def diff(name):
    mine, theirs = got(name), norm(model(name))
    if mine == theirs:
        return None
    for i, (a, b) in enumerate(zip(mine["tr"], theirs["tr"])):
        if a != b:
            return ("%s: trace row %d is %s and should be %s"
                    % (name, i, show(a), show(b)))
    if len(mine["tr"]) != len(theirs["tr"]):
        short, long_ = sorted((mine["tr"], theirs["tr"]), key=len)
        return ("%s: the trace has %d rows and should have %d; the first one "
                "missing is %s" % (name, len(mine["tr"]), len(theirs["tr"]),
                                   show(long_[len(short)])))
    for k in sorted(set(list(mine["sk"]) + list(theirs["sk"]))):
        if mine["sk"].get(k) != theirs["sk"].get(k):
            return ("%s: sink %s took %s and should have taken %s"
                    % (name, k, mine["sk"].get(k), theirs["sk"].get(k)))
    return "%s: differs" % name


def sweep(names):
    bad = [d for d in (diff(n) for n in names) if d]
    if bad:
        pytest.fail("%d of %d plans wrong. %s"
                    % (len(bad), len(names), "  |  ".join(bad[:4])))


def randoms():
    return ["z%04d" % i for i in range(COUNT)]


def test_the_run_completed():
    if REP.get("nonce") != NONCE:
        pytest.fail("the report carries nonce %r and this run made %r"
                    % (REP.get("nonce"), NONCE))
    missing = [n for n in PLAN if n not in REP["reports"]]
    if missing:
        first = missing[0]
        pytest.fail("%d of %d plans produced no report; %s failed with %s"
                    % (len(missing), len(PLAN), first,
                       str(REP["errors"].get(first, "no reason recorded"))[-500:]))


def test_the_bound_is_taken_over_the_whole_machine():
    sweep(ACCOUNT)


def test_lifts_on_a_route():
    sweep(LIFTS)


def test_gathers_on_a_route():
    sweep(GATHERS)


def test_routes_that_lead_back():
    sweep(LOOPS)


def test_the_edges_of_a_bucket():
    sweep(EDGES)


def test_the_plans_that_ship_in_the_tree():
    sweep(SHIPPED)


def test_generated_plans():
    sweep(randoms())


def test_ground_truth_matches_the_model():
    with open(os.path.join(HERE, "gt.json")) as fh:
        truth = json.load(fh)
    if sorted(truth) != sorted(cases.PLANS):
        pytest.fail("the ground truth covers %d plans and the case set has %d"
                    % (len(truth), len(cases.PLANS)))
    for name in sorted(truth):
        want = norm(oracle.play(cases.PLANS[name]))
        have = {"tr": [list(r) for r in truth[name]["tr"]],
                "sk": dict((k, list(v)) for k, v in truth[name]["sk"].items())}
        if want != have:
            pytest.fail("the ground truth for %s is not what the model produces"
                        % name)


def walk(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f.endswith(".pyc"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            with open(p, "rb") as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def test_the_executed_tree_was_the_one_we_shipped():
    want = walk(PRISTINE)
    if not want:
        pytest.fail("the pristine tree is missing from %s" % PRISTINE)
    have = walk(APP_DIR)
    checked = 0
    bad = []
    for rel in sorted(want):
        if rel in ARTIFACTS:
            continue
        checked += 1
        if have.get(rel) != want[rel]:
            bad.append(rel)
    if checked < len(want) - len(ARTIFACTS):
        pytest.fail("only %d files were compared" % checked)
    extra = sorted(set(have) - set(want))
    if bad or extra:
        pytest.fail("the executed tree was not the shipped one: changed %s added %s"
                    % (bad[:6], extra[:6]))


def find(code, name):
    for k in code.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == name:
                return k
            deep = find(k, name)
            if deep is not None:
                return deep
    return None


def baseline():
    out = {}
    for rel, qual in runner.SEALED:
        with open(os.path.join(PRISTINE, rel)) as fh:
            top = compile(fh.read(), rel, "exec")
        code = top
        for part in qual.split("."):
            code = find(code, part)
            if code is None:
                pytest.fail("no %s in the pristine %s" % (qual, rel))
        out["%s:%s" % (rel, qual)] = runner.fingerprint(code)
    return runner.seal(out)


def test_the_machine_functions_were_the_ones_we_shipped():
    want = baseline()
    bad = [n for n in sorted(PLAN)
           if REP["reports"].get(n, {}).get("fp") != want]
    if bad:
        pytest.fail("%d plans ran against a machine function that is not the "
                    "shipped one; first %s" % (len(bad), bad[0]))


def test_the_decisions_were_reached_through_the_machine():
    thin = []
    for name in sorted(PLAN):
        r = REP["reports"].get(name, {})
        mon = r.get("mon", {})
        rows = r.get("tr", [])
        opens = sum(1 for row in rows if row and row[0] == "op")
        if mon.get("ripe", 0) < opens:
            thin.append(name)
        if mon.get("order", 0) < 1:
            thin.append(name)
    if thin:
        pytest.fail("%d plans reached a seal without the machine asking for it; "
                    "first %s" % (len(thin), thin[0]))
