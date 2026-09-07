"""Exact grading of the recalculation reports.

The 32 enumerated sheets pin one stated rule each; their expected reports are hand-derived
and live in gt.json, and the sealed model has to reproduce every one of them before any
generated answer counts. Five families of deterministic scripts then cover the rules in
combination, and three large sheets cover them at a scale where deciding what to bring up
to date by looking at the whole sheet does not finish.

The worker runs the four submitted policy files under the frozen runtime. The remaining
tests check that the runtime that ran was the shipped one, that the report came out of the
frozen driver, and that the scripts themselves obey the input contract the brief states.
This module is executed only by the trusted grader; no submitted code is imported here.
"""

import hashlib
import json
import os
import pathlib
import types

import pytest

import cases
import gen
import oracle
import runner

RUN_OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE = os.environ.get("PRISTINE_DIR", "/pristine")
HERE = pathlib.Path(__file__).resolve().parent
ARTIFACTS = frozenset(("sheet/dep.py", "sheet/lay.py", "sheet/upd.py", "sheet/flow.py"))

VALUES = ("value-moves-reader-follows", "value-restated-nothing-moves",
          "recompute-that-lands-where-it-was", "empty-member-of-a-span",
          "count-ignores-the-empties", "a-chain-stops-where-nothing-moved",
          "two-ways-round-to-the-same-cell")
BRANCHES = ("branch-not-taken-is-not-read", "branch-flips-and-the-reads-move")
LAYOUT = ("a-block-occupies-what-is-under-it", "an-empty-block-shows-nothing",
          "a-block-that-runs-off-the-sheet", "a-block-may-not-cover-its-own-input")
OCCUPANCY = ("content-planted-in-the-way", "the-blocker-goes-away-again",
             "a-blocker-holding-the-very-same-value", "the-value-dips-and-comes-back",
             "a-reader-that-sits-above-the-block", "the-lower-formula-is-in-the-way",
             "two-things-in-the-way", "a-blocker-outside-the-block")
RELEASE = ("a-shorter-block-lets-go", "the-formula-stops-being-a-block",
           "the-formula-is-cleared-away", "a-literal-lands-on-the-formula",
           "a-cell-it-let-go-of-was-taken", "clearing-a-cell-a-block-covers")
EDITS = ("the-same-formula-written-again", "a-different-formula-over-the-same-cells")
ELEMENTS = ("the-head-holds-still-while-the-tail-moves",
            "the-head-moves-while-the-tail-holds-still")
ERRORS = ("the-error-travels",)


def report():
    raw = pathlib.Path(RUN_OUT).read_bytes()
    if not raw.strip():
        pytest.fail("the run left no report")
    try:
        body = json.loads(raw)
    except ValueError as exc:
        pytest.fail("the report is not JSON: %s" % exc)
    if not isinstance(body, dict) or not isinstance(body.get("runs"), dict) \
            or not isinstance(body.get("faults"), dict):
        pytest.fail("the report is not shaped like one")
    return body


REP = report()
NONCE = os.environ.get("RUN_NONCE", "")
COUNT = int(os.environ.get("RUN_COUNT", "60"))
SCRIPTS = dict(runner.plan(NONCE, COUNT))
TRUTH = json.loads((HERE / "gt.json").read_text())


def expected(name):
    if name in cases.CASES:
        return [str(x) for x in TRUTH["cases"][name]]
    return oracle.solve(SCRIPTS[name])


def produced(name):
    body = REP["runs"].get(name)
    if not isinstance(body, dict) or not isinstance(body.get("rp"), list):
        return None
    return [str(x) for x in body["rp"]]


def edits_of(name):
    out = []
    live = False
    for raw in SCRIPTS[name].split("\n"):
        s = raw.strip()
        if not s:
            continue
        if s.split(None, 1)[0] == "go":
            live = True
        elif live:
            out.append(s)
    return out


def explain(name):
    got = produced(name)
    if got is None:
        return "%s: no report" % name
    want = expected(name)
    if got == want:
        return None
    lines = edits_of(name)
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "missing"
        b = want[i] if i < len(want) else "nothing"
        if a != b:
            edit = lines[i // 2] if i // 2 < len(lines) else "?"
            return "%s: after edit %d (%s) the engine reported\n      %s\n   expected\n      %s" \
                % (name, i // 2 + 1, edit, a, b)
    return "%s: differs" % name


def sweep(names):
    bad = [x for x in (explain(n) for n in names) if x]
    if bad:
        pytest.fail("%d of %d scripts wrong\n%s" % (len(bad), len(names), "\n".join(bad[:6])))


# ------------------------------------------------------------------ the run itself

def test_the_run_reported_every_script():
    assert REP.get("nonce") == NONCE, "the report does not carry this run's nonce"
    assert not REP["faults"], "the engine raised on %d scripts: %s" % (
        len(REP["faults"]), sorted(REP["faults"])[:4])
    missing = [n for n in SCRIPTS if n not in REP["runs"]]
    assert not missing, "no report for %d scripts: %s" % (len(missing), missing[:6])


# ------------------------------------------------------------------ the rules

def test_a_cell_follows_the_values_it_read():
    """A reader is recomputed when a value it read moves, and left alone when the value
    it read is restated or recomputed to what it already was."""
    sweep(VALUES)


def test_only_the_branch_that_was_taken_counts():
    """The arm a conditional did not evaluate is not a dependency, and the reads move
    when the test flips."""
    sweep(BRANCHES)


def test_a_block_finds_room_or_says_so():
    """Length, the edge of the sheet, an empty result and a block that would land on its
    own input."""
    sweep(LAYOUT)


def test_occupancy_is_a_dependency_of_its_own():
    """Content planted in a block's way blocks it and clearing that content brings it
    back, whether or not the displayed value moves; content outside the block is not the
    block's business."""
    sweep(OCCUPANCY)


def test_a_block_gives_cells_up_cleanly():
    """A shorter block, a formula that stops being a block, a cleared formula and a
    literal written over one all release the right cells and leave own content alone."""
    sweep(RELEASE)


def test_writing_a_formula_recomputes_that_cell():
    """A cell whose content is replaced has no read record to trust, even when the new
    formula reads the same cells to the same values."""
    sweep(EDITS)


def test_elements_of_a_block_move_one_at_a_time():
    """A reader of one occupied cell follows that cell, not the block."""
    sweep(ELEMENTS)


def test_an_error_travels_and_clears():
    sweep(ERRORS)


def test_generated_families():
    """All five deterministic families must pass in full."""
    sweep(sorted(n for n in SCRIPTS if n.startswith("sheet-v1-")))


def test_large_sheets():
    """Three sheets of roughly twelve thousand formulas, loaded cell by cell."""
    sweep(sorted(n for n in SCRIPTS if n.startswith("wide-")))


# ------------------------------------------------------------------ the inputs

def cycle_free(own):
    """No formula may end up needing its own value.

    Edges run from a cell to the cells that supply what it reads: the cell itself when it
    carries a formula, and every block-valued formula above it in its column, since the
    next block may reach further than the last one. A block-valued formula supplying a
    cell it reads itself is not a cycle - that is exactly the case the layout rule turns
    into a block that does not fit - so self edges are dropped.
    """
    edge = {}
    for ad, e in own.items():
        if e[0] != "f":
            continue
        out = set()
        for t in e[2]:
            if t in own and own[t][0] == "f":
                out.add(t)
            for r in range(1, t[0]):
                other = own.get((r, t[1]))
                if other is not None and other[0] == "f" and other[1] == "v":
                    out.add((r, t[1]))
        out.discard(ad)
        edge[ad] = out
    seen = {}
    for start in edge:
        stack = [(start, iter(edge.get(start, ())))]
        if seen.get(start) == 2:
            continue
        seen[start] = 1
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                seen[node] = 2
                stack.pop()
                continue
            if seen.get(nxt) == 1:
                return False
            if seen.get(nxt) != 2:
                seen[nxt] = 1
                stack.append((nxt, iter(edge.get(nxt, ()))))
    return True


def walk_script(text):
    """Replay a script's content changes and yield the own-content map after each."""
    own = {}
    nr = 0
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            continue
        t = s.split(None, 2)
        if t[0] == "size":
            nr = int(t[1])
            continue
        if t[0] == "go":
            continue
        ad = oracle.pa(t[1])
        assert 1 <= ad[0] <= nr, "%s is outside the sheet" % t[1]
        if t[0] == "clr":
            own.pop(ad, None)
        else:
            body = t[2].strip()
            if body.startswith("="):
                kind, _, refs = oracle.build(body[1:])
                for r in refs:
                    assert 1 <= r[0] <= nr, "%s reads outside the sheet" % s
                own[ad] = ("f", kind, refs)
            else:
                own[ad] = ("n", int(body))
        yield own


def test_every_graded_script_obeys_the_input_contract():
    """Addresses stay inside the sheet, block-valued calls are whole formulas, and no
    formula ever ends up needing its own value. The large sheets are checked in their
    final state only; walking their eighteen thousand load lines cell by cell would cost
    more than the grading."""
    for name in sorted(SCRIPTS):
        big = name.startswith("wide-")
        state = None
        for own in walk_script(SCRIPTS[name]):
            state = own
            if not big:
                assert cycle_free(own), "%s builds a sheet that needs its own value" % name
        assert state is not None, name
        assert cycle_free(state), "%s ends needing its own value" % name


# ------------------------------------------------------------------ the model

def test_the_sealed_model_still_reproduces_the_hand_derivations():
    assert sorted(TRUTH["cases"]) == sorted(cases.CASES), \
        "gt.json and cases.py describe different sets"
    for name in sorted(cases.CASES):
        assert oracle.solve(cases.CASES[name]) == [str(x) for x in TRUTH["cases"][name]], \
            "oracle.py has drifted on %s" % name


def test_the_families_are_the_ones_that_were_measured():
    assert gen.SHAPES == ("plain", "block", "coin", "self", "mix")
    assert len([n for n in SCRIPTS if n.startswith("sheet-v1-")]) == COUNT * len(gen.SHAPES)
    assert len([n for n in SCRIPTS if n.startswith("wide-")]) == runner.WIDE


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
    assert checked >= 5, "only %d frozen files were compared" % checked


def inner(code, name):
    for k in code.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == name:
            return k
    raise KeyError(name)


def compiled_baseline():
    out = {}
    for rel, qual in runner.FROZEN:
        src = pathlib.Path(PRISTINE, rel).read_text()
        node = compile(src, rel, "exec")
        for part in qual.split("."):
            node = inner(node, part)
        out["%s#%s" % (rel, qual)] = runner.digest(node)
    return runner.stamp(out)


def test_frozen_functions_were_the_shipped_ones():
    if not os.path.isdir(PRISTINE):
        pytest.skip("no pristine tree")
    want = compiled_baseline()
    bad = [n for n in sorted(REP["runs"])
           if REP["runs"][n].get("fp") != want or REP["runs"][n].get("fp2") != want]
    assert not bad, "frozen functions were replaced during %d scripts: %s" % (len(bad), bad[:4])


def test_the_report_came_out_of_the_driver():
    """Every report line was appended by the frozen driver, the instrumentation was still
    armed at the end of each script, the driver ran once per script, the per-edit step ran
    once per edit line, and at least as many recomputations happened as were reported."""
    need = os.environ.get("REQUIRE_MONITORING") == "1"
    bad = []
    for n in sorted(REP["runs"]):
        r = REP["runs"][n]
        mon = r.get("mon") or {}
        rows = r.get("rp") or []
        lines = [s for s in (x.strip() for x in SCRIPTS[n].split("\n"))
                 if s and s.split(None, 1)[0] not in ("size", "go")]
        claimed = set()
        for row in rows:
            parts = str(row).split()
            if parts and parts[0] == "rc":
                claimed.update(p for p in parts[2:] if p != "-")
        if not r.get("arm"):
            bad.append("%s: instrumentation was disturbed" % n)
        elif need and r.get("how") != "monitoring":
            bad.append("%s: instrumentation fell back to %s" % (n, r.get("how")))
        elif mon.get("drive") != 1:
            bad.append("%s: the driver ran %s times" % (n, mon.get("drive")))
        elif mon.get("step") != len(lines):
            bad.append("%s: %d edit lines but the step ran %s times"
                       % (n, len(lines), mon.get("step")))
        elif mon.get("calc", 0) < len(claimed):
            bad.append("%s: %d cells reported as recomputed but only %s recomputations ran"
                       % (n, len(claimed), mon.get("calc")))
    assert not bad, "\n".join(bad[:6])
