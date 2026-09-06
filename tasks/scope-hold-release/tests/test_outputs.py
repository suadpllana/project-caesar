"""Grader for scope-hold-release. Runs as root; never executes agent code.

VERIFIER CONTRACT (frozen before the environment was written).

Graded artifact: the container's teardown dump. One record per line, in the
order the run produced it, over 22 enumerated cases and 300 streams the
verifier generates from a nonce minted after the agent has finished.

  ("torn", name, scope, cause)   an instance torn down, the scope that owned
                                 it, and the top-level name whose resolution
                                 or invocation created it
  ("refused", name, scope)       a resolution the container declined

Real work, safe to grade -- two correct implementations agree by construction:
the set of instances created, the scope each is owned by, the order within a
scope, and which resolutions are refused. All follow from the stated rules.

Implementation choice, never graded: the data structure holding the ledger
and internal instance labels. Relative allocation order controls teardown.
Scope labels and the complete order of teardown and refusal records are graded.

Ground truth in tests/gt.json is re-proved here against tests/oracle.py, a
sealed model that shares no code with the reference.
"""

import hashlib
import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, "/tests")

import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402

OUT = "/work/run/out.json"
GT = "/tests/gt.json"
PRISTINE = pathlib.Path("/pristine")
SEALED = {
    "core": ("wire/core.py", ["build", "fire", "mint", "forget", "since", "mark", "kind"]),
    "reg": ("wire/reg.py", ["load", "reach", "cycles"]),
    "scope": ("wire/scope.py", ["open", "close", "top", "under", "holds", "upto", "tag"]),
}


def _codes(co, want, found):
    for c in co.co_consts:
        if hasattr(c, "co_code"):
            if c.co_name in want:
                found[c.co_name] = c
            _codes(c, want, found)


def _baseline(rel, names):
    src = (PRISTINE / rel).read_text()
    top = compile(src, rel, "exec")
    found = {}
    _codes(top, set(names), found)
    h = hashlib.sha256()
    for n in sorted(names):
        c = found.get(n)
        if c is None:
            h.update(b"?")
            continue
        h.update(c.co_code)
        h.update(repr(c.co_consts).encode())
    return h.hexdigest()


@pytest.fixture(scope="module")
def report():
    try:
        with open(OUT) as fh:
            r = json.load(fh)
    except Exception:
        return None
    return r if isinstance(r, dict) else None


@pytest.fixture(scope="module")
def truth():
    with open(GT) as fh:
        return json.load(fh)


def test_the_run_produced_a_report(report):
    assert os.environ.get("RUNNER_OK") == "1", "the submitted run did not finish cleanly"
    assert report is not None, "the run produced no dump"
    assert report.get("fault") is None, "the run faulted: %s" % report.get("fault")
    assert isinstance(report.get("runs"), dict) and report["runs"], "the dump is empty"


def test_the_sealed_modules_were_the_ones_we_shipped(report):
    assert report is not None
    seal = report.get("seal")
    assert isinstance(seal, dict), "the run reported no seal"
    for key, (rel, names) in sorted(SEALED.items()):
        assert seal.get(key) == _baseline(rel, names), "%s was not the shipped module" % rel


def test_the_executed_tree_was_the_one_we_shipped():
    work = pathlib.Path(os.environ.get("WORKAPP", "/work/app"))
    seen = 0
    for src in sorted(PRISTINE.rglob("*.py")):
        rel = src.relative_to(PRISTINE)
        if rel.parts[0] == "cases":
            continue
        seen += 1
        got = work / rel
        assert got.exists(), "%s vanished from the work tree" % rel
        if str(rel).replace("\\", "/") in ARTIFACTS:
            continue
        assert got.read_bytes() == src.read_bytes(), "%s was modified" % rel
    assert seen >= 8, "compared only %d files against the pristine tree" % seen


ARTIFACTS = {"wire/own.py", "wire/pin.py", "wire/hold.py", "wire/gate.py", "wire/tear.py",
             "wire/shut.py", "wire/plan.py"}


def test_the_named_ground_truth_matches_the_rules(truth):
    bad = []
    for nm, rows, ops in cases.FIXED:
        want = [[str(x) for x in rec] for rec in oracle.play(rows, ops)]
        if truth["fixed"].get(nm) != want:
            bad.append(nm)
    assert not bad, "sealed ground truth disagrees with the rule model: %s" % ", ".join(bad)


def test_the_named_cases_match_the_rules(report, truth):
    assert report is not None
    bad = []
    for nm, _rows, _ops in cases.FIXED:
        want = [list(x) for x in truth["fixed"][nm]]
        got = report["runs"].get(nm)
        if got != want:
            bad.append(nm)
    assert not bad, "these cases came back wrong: %s" % ", ".join(bad)


def test_the_generated_streams_match_the_rules(report):
    assert report is not None
    nonce = report.get("nonce")
    assert nonce == os.environ.get("SHR_NONCE", "0"), "the dump carries the wrong nonce"
    bad = 0
    first = None
    for i in range(300):
        rows, ops = gen.stream("%s-%d" % (nonce, i), i % 2 == 0)
        want = [[str(x) for x in t] for t in oracle.play(rows, ops)]
        got = report["runs"].get("g%04d" % i)
        if got != want:
            bad += 1
            if first is None:
                first = "g%04d" % i
    assert bad == 0, "%d of 300 generated streams came back wrong, first %s" % (bad, first)
