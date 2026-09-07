"""Exact grading of the printed grid, all-or-nothing.

The 45 enumerated scripts pin one stated rule each: what a block occupies and what refuses
it, the loop rule, how a cell is read, and how the shape-preserving functions carry holes
and refusals. Five seeded families of generated sheets test the same rules in combination.
Expected output comes only from the sealed independent model; every enumerated script is
checked against that model too, so model drift cannot quietly move the grading contract.

The worker ran the four submitted policy files under the frozen runtime. The remaining
tests check runtime identity, report completeness and instrumentation. This module is
executed only by the trusted grader; no submitted code is imported here.
"""

import hashlib
import json
import os
import pathlib
import types

import pytest

import cases
import oracle
import runner

RUN_OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE = os.environ.get("PRISTINE_DIR", "/pristine")
HERE = pathlib.Path(__file__).resolve().parent
ARTIFACTS = frozenset(("sheet/val.py", "sheet/see.py", "sheet/lay.py", "sheet/memo.py"))

PLACED = ("owner-shows-its-first-value", "block-refused-by-content",
          "refused-owner-covers-nothing", "overlap-earliest-wins",
          "later-block-fills-a-refused-gap", "owner-cell-is-not-in-the-way",
          "clearing-frees-a-block", "content-put-under-a-block",
          "cover-reaches-through-a-range", "two-columns-of-blocks")
EDGES = ("block-past-the-last-row", "block-past-the-last-column", "row-width-limit",
         "count-must-be-at-least-one", "count-past-the-sheet")
LOOPS = ("read-into-own-quadrant", "read-same-row-to-the-right", "read-up-and-right-is-fine",
         "read-down-and-left-is-fine", "loop-marks-the-whole-chain",
         "loop-does-not-stop-at-a-sum", "loop-in-a-count-argument",
         "owner-order-decides-a-loop", "loop-swallows-what-it-passed-through")
READS = ("empty-is-zero-in-arithmetic", "count-ignores-empty", "sum-steps-over-a-refusal",
         "count-includes-a-refusal", "max-with-nothing-numeric", "left-error-wins",
         "block-in-arithmetic", "range-in-arithmetic", "a-range-cell-shows-a-refusal",
         "len-counts-cells-not-values")
SHAPES = ("at-on-an-empty-cell", "at-past-the-end", "grow-keeps-a-hole",
          "grow-keeps-a-refusal", "grow-keeps-the-shape", "keep-takes-the-first-cells",
          "keep-past-the-end", "rep-of-an-error-is-a-block-of-errors", "row-runs-across",
          "count-comes-from-a-cell", "count-from-a-refused-cell")


def report():
    """Read the worker's report defensively. Everything here came through a process that
    ran agent code, so a bad shape is a graded failure rather than an exception: an
    import-time abort would leave no named test behind for the run audit to read."""
    blank = {"error": None, "nonce": None, "grids": {}, "faults": {}}
    try:
        raw = pathlib.Path(RUN_OUT).read_bytes()
    except OSError as exc:
        return dict(blank, error="the report could not be read: %s" % exc)
    if not raw.strip():
        return dict(blank, error="the run left no report")
    try:
        body = json.loads(raw)
    except ValueError as exc:
        return dict(blank, error="the report is not JSON: %s" % exc)
    if not isinstance(body, dict) or not isinstance(body.get("grids"), dict) \
            or not isinstance(body.get("faults"), dict):
        return dict(blank, error="the report is not shaped like one")
    body.setdefault("error", None)
    return body


REP = report()
NONCE = os.environ.get("RUN_NONCE", "")
COUNT = int(os.environ.get("RUN_COUNT", "120"))
SCRIPTS = dict(runner.plan(NONCE, COUNT))
TRUTH = json.loads((HERE / "gt.json").read_text())


def expected(name):
    if name in cases.CASES:
        return tuple(TRUTH["cases"][name])
    return tuple(oracle.solve(SCRIPTS[name]))


def produced(name):
    body = REP["grids"].get(name)
    if not isinstance(body, dict) or not isinstance(body.get("gr"), list):
        return None
    return tuple(str(x) for x in body["gr"])


def explain(name):
    got = produced(name)
    if got is None:
        return "%s: no printout" % name
    want = expected(name)
    if got == want:
        return None
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "<missing line>"
        b = want[i] if i < len(want) else "<no such line>"
        if a != b:
            return "%s: line %d is\n      %s\n   expected\n      %s" % (name, i + 1, a, b)
    return "%s: differs" % name


def sweep(names):
    bad = [x for x in (explain(n) for n in names) if x]
    if bad:
        pytest.fail("%d of %d scripts wrong\n%s" % (len(bad), len(names), "\n".join(bad[:6])))


# ------------------------------------------------------------------ the run itself

def test_the_run_reported_every_script():
    assert not REP.get("error"), REP.get("error")
    assert REP.get("nonce") == NONCE, "the report does not carry this run's nonce"
    assert not REP["faults"], "the engine raised on %d scripts: %s" % (
        len(REP["faults"]), sorted(REP["faults"])[:4])
    missing = [n for n in SCRIPTS if n not in REP["grids"]]
    assert not missing, "no printout for %d scripts: %s" % (len(missing), missing[:6])


# ------------------------------------------------------------------ the rules

def test_a_block_occupies_and_is_refused():
    """An owner shows its block's first value; a block is refused by content or by a block
    already in the way; a refused owner covers nothing and a later one may take the room."""
    sweep(PLACED)


def test_a_block_stays_inside_the_sheet():
    """A rectangle that leaves the last row or column is refused, and a count outside the
    sheet's own bounds is a bad argument rather than a refusal."""
    sweep(EDGES)


def test_the_loop_rule():
    """A read into a cell's own down-right quadrant re-enters that cell; the re-entered cell
    and every cell asked on its behalf report a loop, and a loop is never stepped over."""
    sweep(LOOPS)


def test_reading_a_cell():
    """Empty reads as zero in arithmetic but is not counted; refusals are stepped over by
    the summing functions and counted by the counting one; the left error wins."""
    sweep(READS)


def test_the_shape_preserving_functions():
    """Picking, keeping and growing carry holes and refusals through unchanged, and keep
    the shape they were given."""
    sweep(SHAPES)


def test_every_enumerated_script_is_graded():
    """No enumerated case may sit outside the groups above."""
    grouped = set(PLACED) | set(EDGES) | set(LOOPS) | set(READS) | set(SHAPES)
    assert grouped == set(cases.CASES), \
        "ungrouped: %s" % sorted(set(cases.CASES) ^ grouped)


def test_generated_sheets():
    """All five fixed-seed families must pass in full."""
    sweep(sorted(n for n in SCRIPTS if n not in cases.CASES))


# ------------------------------------------------------------------ the model

def test_the_sealed_model_still_reproduces_the_truth():
    assert sorted(TRUTH["cases"]) == sorted(cases.CASES), \
        "gt.json and cases.py describe different sets"
    for name in sorted(cases.CASES):
        assert oracle.solve(cases.CASES[name]) == list(TRUTH["cases"][name]), \
            "oracle.py has drifted on %s" % name


def test_the_scripts_stay_inside_the_stated_bounds():
    """Input-only check: every graded script addresses cells inside the sheet and uses only
    the two commands the instruction describes."""
    for name, text in SCRIPTS.items():
        steps = 0
        for raw in text.split("\n"):
            toks = raw.split()
            if not toks:
                continue
            steps += 1
            assert toks[0] in ("put", "clr"), "%s: %s" % (name, toks[0])
            assert oracle.where(toks[1]) is not None, "%s: %s" % (name, toks[1])
            if toks[0] == "put":
                oracle.parse(" ".join(toks[2:]))
        assert 1 <= steps <= 60, "%s has %d commands" % (name, steps)


# ------------------------------------------------------------------ integrity

def hashes(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in files:
            if fn.endswith(".pyc"):
                continue
            p = os.path.join(base, fn)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, root).replace(os.sep, "/")] = \
                    hashlib.sha256(fh.read()).hexdigest()
    return out


def test_the_executed_tree_is_the_shipped_tree():
    if not os.path.isdir(APP_DIR) or not os.path.isdir(PRISTINE):
        pytest.skip("no work tree to compare")
    live, base = hashes(APP_DIR), hashes(PRISTINE)
    checked = 0
    for rel in sorted(set(live) | set(base)):
        if rel in ARTIFACTS:
            continue
        assert rel in base, "%s is not part of the shipped tree" % rel
        assert rel in live, "%s is missing from the executed tree" % rel
        assert live[rel] == base[rel], "%s was modified" % rel
        checked += 1
    assert checked >= 7, "only %d frozen files were compared" % checked


def _inner(code, name):
    for k in code.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == name:
            return k
    raise KeyError(name)


def compiled_baseline():
    """The seal the run should have reported, derived from the untouched sources by
    compiling them. Nothing here is executed."""
    marks = []
    for rel, qual in runner.FROZEN:
        node = compile(pathlib.Path(PRISTINE, rel).read_text(), rel, "exec")
        for part in qual.split("."):
            node = _inner(node, part)
        marks.append("%s#%s=%s" % (rel, qual, runner.digest(node)))
    return hashlib.sha256("\n".join(sorted(marks)).encode()).hexdigest()


def test_frozen_functions_were_the_shipped_ones():
    if not os.path.isdir(PRISTINE):
        pytest.skip("no pristine tree")
    want = compiled_baseline()
    bad = [n for n in sorted(REP["grids"])
           if REP["grids"][n].get("sealed") != want
           or REP["grids"][n].get("resealed") != want]
    assert not bad, "frozen functions were replaced during %d scripts: %s" % (len(bad), bad[:4])


def test_instrumentation_was_intact():
    """Every printed line came out of Run.step, and the interpreter's instrumentation was
    still armed when each script ended."""
    need = os.environ.get("REQUIRE_MONITORING") == "1"
    bad = []
    for n in sorted(REP["grids"]):
        r = REP["grids"][n]
        lines = len(r.get("gr") or [])
        if not r.get("armed"):
            bad.append("%s: the counter was disturbed during the run" % n)
        elif need and r.get("how") != "monitoring":
            bad.append("%s: counting fell back to %s" % (n, r.get("how")))
        elif r.get("steps") != lines:
            bad.append("%s: %d lines printed but the driver ran %s times"
                       % (n, lines, r.get("steps")))
    assert not bad, "\n".join(bad[:6])
