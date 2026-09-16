"""The trusted grader.

Runs as root, after the worker has finished and its survivors have been reaped.
It never imports anything the agent wrote: it reads the worker's report as
hostile data, rebuilds the expected traces itself from the frozen answers and
the sealed model, and compares them exactly. Every section below states which
behaviour it checks.
"""

import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, "/tests")
sys.path.insert(0, "/tests/seal")

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

RUN_OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE = os.environ.get("PRISTINE_DIR", "/pristine")
GT = "/tests/gt.json"

EDITABLE = ("sked/zt.py", "sked/due.py", "sked/gate.py", "sked/lane.py")


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


@pytest.fixture(scope="session")
def report():
    """The worker's output, treated as hostile: any shape but the expected one
    is a failed run, never an exception that skips the verdict."""
    if not os.path.isfile(RUN_OUT) or os.path.getsize(RUN_OUT) == 0:
        pytest.fail("the worker produced no report")
    try:
        with open(RUN_OUT) as fh:
            data = json.load(fh)
    except Exception as exc:
        pytest.fail("the worker's report is not readable JSON: %r" % (exc,))
    if not isinstance(data, dict):
        pytest.fail("the worker's report is not an object")
    for key in ("nonce", "per", "cases", "gen", "fault", "made", "lines"):
        if key not in data:
            pytest.fail("the worker's report has no %r" % key)
    if not isinstance(data["cases"], dict) or not isinstance(data["gen"], dict):
        pytest.fail("the worker's report has no trace tables")
    return data


@pytest.fixture(scope="session")
def frozen_answers():
    with open(GT) as fh:
        return json.load(fh)


def rows(data, bucket, name):
    got = data[bucket].get(name)
    if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
        pytest.fail("%s: the planner did not return a trace" % name)
    return got


def report_diff(name, got, want):
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "<missing>"
        b = want[i] if i < len(want) else "<extra>"
        if a != b:
            return ("%s: line %d is %r, expected %r (%d lines against %d)"
                    % (name, i + 1, a, b, len(got), len(want)))
    return "%s: traces differ" % name


# -- the files the run is allowed to have changed ---------------------------

def test_only_the_planner_modules_differ():
    """Everything outside the four declared paths is served from the pristine
    tree, so the parser, the record types, the trace writer, the validator and
    the entry point cannot have been rewritten."""
    for root, _, files in os.walk(PRISTINE):
        for f in files:
            if not f.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(root, f), PRISTINE)
            live = os.path.join(APP_DIR, rel)
            assert os.path.isfile(live), "missing from the run tree: %s" % rel
            if rel.replace(os.sep, "/") in EDITABLE:
                continue
            assert digest(live) == digest(os.path.join(root, f)), \
                "%s is not the shipped file" % rel


# -- the run itself ---------------------------------------------------------

def test_worker_ran_every_plan(report):
    """A planner that raised on a plan produced no trace for it; the first such
    fault is reported rather than hidden behind a comparison failure."""
    assert isinstance(report["fault"], dict)
    if report["fault"]:
        first = sorted(report["fault"])[0]
        pytest.fail("the planner raised on %s - %s" % (first, report["fault"][first]))


def test_nonce_echo(report):
    """The traces belong to this run's population, not to an earlier one."""
    assert report["nonce"] == os.environ["RUN_NONCE"]
    assert report["per"] == int(os.environ.get("RUN_COUNT", "50"))


def test_every_line_came_from_a_record(report):
    """Attestation: the frozen record type made at least as many records as
    there are printed lines, so a planner that returns ready-made strings or
    replays a stored answer is visible even when the strings would have
    matched."""
    if os.environ.get("REQUIRE_MONITORING") != "1":
        pytest.skip("monitoring not requested")
    assert isinstance(report["made"], int) and isinstance(report["lines"], int)
    assert report["lines"] > 0, "the planner printed nothing at all"
    assert report["made"] >= report["lines"], (
        "%d printed lines came from %d records" % (report["lines"], report["made"]))


# -- the enumerated corners, against the frozen answers ---------------------

@pytest.mark.parametrize("name", [n for n, _ in cases.PLANS])
def test_enumerated_plan(report, frozen_answers, name):
    """One plan per rule of the contract. The name says which decision it pins,
    so a failure names the rule."""
    want = frozen_answers[name]
    got = rows(report, "cases", name)
    assert got == want, report_diff(name, got, want)


def test_frozen_answers_still_match_the_model(frozen_answers):
    """The sealed model must reproduce every frozen answer before a run can
    pass, so a drifted model cannot quietly redefine correct."""
    for name, text in cases.PLANS:
        assert model.trace(text) == frozen_answers[name], \
            "%s: the sealed model no longer reproduces the frozen answer" % name


# -- the generated families, against the sealed model -----------------------

def test_generated_families(report):
    """Plans this run generated from its own nonce, answered by the model. Each
    family is shaped around one mechanism; all of them must match."""
    nonce = os.environ["RUN_NONCE"]
    per = int(os.environ.get("RUN_COUNT", "50"))
    bad = []
    seen = 0
    for name, text in gen.plans(nonce, per):
        want = model.trace(text)
        got = rows(report, "gen", name)
        seen += 1
        if got != want:
            bad.append(report_diff(name, got, want))
            if len(bad) >= 3:
                break
    assert seen == len(gen.FAMILIES) * per
    assert not bad, "\n".join(bad)
