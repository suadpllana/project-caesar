"""Grading. Root, and it never executes agent code.

FROZEN CONTRACT
---------------
The agent supplies five files under `/app/mrg/`: `live.py` decides which nodes the record
keeps, `spot.py` decides the folder and the name of each one and repairs the result,
`name.py` settles contested names, `book.py` settles contents, makes the node a two-sided
write leaves behind, hands out numbers and builds the record, and `step.py` turns the record
into the operations each side carries out. Everything else in the tree is the verifier's own
pristine copy, so only those five can change what a scenario prints.

Graded, and settled the same way by two implementations written apart:
  1  which nodes the record keeps: removal against change on the other side, removal against
     quiet, and the pull that holds a folder open for the nodes the record put in it
  2  the folder and the name settled separately, each contested part going to the server
  3  the walk up to the nearest folder that survived, for anything left without one
  4  the loop break when two folders end up inside each other
  5  what each node holds, and the second node a two-sided write leaves behind
  6  the numbers new nodes get, which decide who keeps a contested name and in what order
     the rest are marked
  7  contested names: case-blind, who keeps the name, and where the mark goes
  8  the operations each side is given, in the order they can be carried out, including the
     push-aside when a wanted name is occupied
  9  the record carried into the next round, visible only through what the next round does

Implementation choice, never graded: how the tree is represented, whether survival is a fixed
point or an upward walk, how loops are found, the order files are read in, and any internal
naming. The reference and the model differ in all of those.

The trace is compared exactly, line for line. Enumerated scenarios are checked against
`gt.json`, frozen before the verifier was written; generated scenarios are built from the run
nonce after the agent has finished, and checked against the sealed model. `gt.json` and the
model must also agree on every enumerated scenario, so a drifted model cannot quietly redefine
correct.
"""
import json
import os
import pathlib

import pytest

import cases
import gen
import model
import seal

HERE = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
OUT = pathlib.Path(os.environ.get("RUN_OUT", "/work/run/out.json"))
PLAN = pathlib.Path(os.environ.get("PLAN", "/work/run/plan.json"))
GT = HERE / "gt.json"
PRISTINE = os.environ.get("PRISTINE_DIR", "/pristine")
NONCE = pathlib.Path(os.environ.get("NONCE_FILE", "/logs/verifier/nonce"))


def _report():
    """Everything here came from agent-influenced code. Parse it defensively."""
    try:
        raw = json.loads(OUT.read_text(encoding="utf-8"))
    except Exception as exc:
        pytest.fail("the run produced no readable report: %s" % exc)
    if not isinstance(raw, dict):
        pytest.fail("the run's report is not an object")
    traces = raw.get("traces")
    if not isinstance(traces, dict):
        pytest.fail("the run's report carries no traces")
    return raw, traces


@pytest.fixture(scope="module")
def report():
    return _report()


@pytest.fixture(scope="module")
def truth():
    return json.loads(GT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def wanted():
    nonce = NONCE.read_text(encoding="utf-8").strip()
    count = int(os.environ.get("RUN_COUNT", "60"))
    return nonce, count, gen.batch(nonce, count)


def rows(traces, name):
    item = traces.get(name)
    if not isinstance(item, dict):
        pytest.fail("no result for scenario %s" % name)
    got = item.get("tr")
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("the trace of %s is not a list of lines" % name)
    return got


# --- the sealed side must agree with itself before it judges anything -------------------

def test_frozen_truth_matches_the_model(truth):
    """gt.json was frozen from the model; if they have drifted apart, grade nothing."""
    assert sorted(truth) == sorted(cases.ORDER)
    for name in cases.ORDER:
        assert model.replay(cases.CASES[name]) == truth[name], name


# --- the report has to be this run's, from an engine that is still the shipped one -------

def test_report_is_this_run(report, wanted):
    raw, traces = report
    nonce, count, batch = wanted
    assert raw.get("nonce") == nonce, "the report does not carry this run's nonce"
    assert not raw.get("faults"), "the engine raised: %s" % list(raw.get("faults", {}))[:4]
    assert raw.get("count") == len(cases.ORDER) + len(batch)


def test_frozen_files_were_not_rewritten(report):
    """Only the five policy files may differ from the pristine tree."""
    want = seal.from_source(PRISTINE)
    _, traces = report
    for name, item in traces.items():
        assert item.get("fp") == want, "the engine was not the shipped one for %s" % name
        assert item.get("fp2") == want, "a frozen function changed while %s ran" % name


def test_the_driver_actually_ran(report):
    """The trace has to come from the driver, once per scenario, with the meter armed.

    The applier is entered at least once for every line of the scenario and once for every
    operation the trace reports, so a trace richer than the work behind it is a failure.
    """
    _, traces = report
    if os.environ.get("REQUIRE_MONITORING", "1") != "1":
        pytest.skip("monitoring not required")
    planned = dict((item["name"], item["text"])
                   for item in json.loads(PLAN.read_text(encoding="utf-8")))
    for name, item in traces.items():
        assert item.get("arm") is True, "the instrumentation was disarmed during %s" % name
        mon = item.get("mon") or {}
        assert mon.get("go") == 1, "the driver ran %r times for %s" % (mon.get("go"), name)
        given = sum(1 for line in planned.get(name, "").split("\n") if line[:2] in ("L ", "R "))
        emitted = sum(1 for line in rows(traces, name)
                      if len(line.split(" ")) > 1 and line.split(" ")[1] in ("L", "R"))
        assert mon.get("do", 0) >= given + emitted, (
            "%s reported %d operations behind %d visits to the applier"
            % (name, given + emitted, mon.get("do", 0)))


def test_the_run_saw_the_scenarios_it_was_given(report, wanted):
    """The plan root wrote is the plan the grader regenerates."""
    nonce, count, batch = wanted
    planned = json.loads(PLAN.read_text(encoding="utf-8"))
    by = dict((item["name"], item["text"]) for item in planned)
    for name in cases.ORDER:
        assert by.get(name) == cases.CASES[name], "enumerated scenario altered: %s" % name
    for name, text in batch:
        assert by.get(name) == text, "generated scenario altered: %s" % name
    assert len(by) == len(cases.ORDER) + len(batch)


# --- enumerated scenarios: one per graded decision, plus the quiet side ------------------

@pytest.mark.parametrize("name", cases.ORDER)
def test_enumerated_scenario(report, truth, name):
    _, traces = report
    assert rows(traces, name) == truth[name]


# --- generated scenarios, built from the nonce after the agent finished ------------------

def test_every_generated_scenario_matches(report, wanted):
    _, traces = report
    nonce, count, batch = wanted
    assert len(batch) >= 200, "generated population too small: %d" % len(batch)
    bad = []
    for name, text in batch:
        got = rows(traces, name)
        if got != model.replay(text):
            bad.append(name)
    assert not bad, "%d of %d generated scenarios wrong, first: %s" % (
        len(bad), len(batch), bad[:4])


def test_every_family_is_present(wanted):
    nonce, count, batch = wanted
    fams = set(name.split("-")[0] for name, _ in batch)
    assert fams == set(fam for fam, _ in gen.FAMILIES)
