"""Exact focus-trail grading for scopes, lifetimes and render transactions.

The 89 literal cases pin the focus contract, lifetime rules and buffered renders. Two sets of
300 deterministic histories test the old interactions and their nested combinations.
A further 150 histories reuse retired widget names.
Another 300 histories mix nested render transactions with those same operations.
Expected output is produced only by the sealed independent model. Every literal is
checked against that model so model drift cannot silently alter the grading contract.

The worker runs the four submitted policy files under the frozen runtime. The
remaining tests check runtime identity, report completeness and instrumentation. This
module is executed only by the trusted grader; no submitted code is imported here.
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
import transaction_gen

RUN_OUT = os.environ.get("RUN_OUT", "/work/run/out.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE = os.environ.get("PRISTINE_DIR", "/pristine")
HERE = pathlib.Path(__file__).resolve().parent
ARTIFACTS = frozenset(("ui/focus.py", "ui/keep.py", "ui/reach.py", "ui/mem.py"))

REACH = ("reach-inherits-hidden", "reach-inherits-shut", "reach-inherits-disabled-focused")
GROUPS = ("group-selected-is-the-stop", "group-none-selected", "group-selected-unreachable",
          "group-unselected-holds-focus", "pick-keeps-focus")
COMPOSITES = ("comp-is-one-stop", "comp-back-lands-on-memory", "comp-memory-from-request",
              "comp-memory-gone", "comp-arrows-do-not-wrap", "comp-empty-is-no-stop",
              "want-inside-composite", "comp-keys-leave-it",
              "comp-back-from-dropped-place")
SCREENS = ("push-lands-on-auto", "push-without-auto", "push-nothing-to-take",
           "pop-restores-the-widget", "pop-restores-lazily", "pop-target-still-unreachable",
           "pop-target-dropped", "pop-the-last-screen", "push-over-nothing")
ORDER = ("pop-out-of-order", "pop-out-of-order-target-gone", "pop-out-of-order-twice",
         "pop-out-of-order-with-held")
REQUESTS = ("want-held-for-a-screen-below", "want-held-beats-the-return",
            "want-held-latest-wins", "want-held-unreachable-at-return",
            "want-held-re-enabled-before-return", "want-held-before-the-push",
            "want-unreachable-is-ignored")
LOST = ("lost-starts-after-the-widget", "lost-widget-shown-again", "lost-container-dropped",
        "lost-container-dropped-then-parent", "lost-insert-at-the-point",
        "lost-point-does-not-move", "lost-point-at-the-end", "lost-moved-under-hidden",
        "lost-inside-composite")


def report():
    raw = pathlib.Path(RUN_OUT).read_bytes()
    if not raw.strip():
        pytest.fail("the run left no report")
    try:
        body = json.loads(raw)
    except ValueError as exc:
        pytest.fail("the report is not JSON: %s" % exc)
    if not isinstance(body, dict) or not isinstance(body.get("trails"), dict) \
            or not isinstance(body.get("faults"), dict):
        pytest.fail("the report is not shaped like one")
    return body


REP = report()
NONCE = os.environ.get("RUN_NONCE", "")
COUNT = int(os.environ.get("RUN_COUNT", "300"))
SCRIPTS = dict(runner.plan(NONCE, COUNT))
TRUTH = json.loads((HERE / "gt.json").read_text())


def expected(name):
    if name in cases.CASES:
        return tuple(TRUTH["cases"][name])
    return tuple(oracle.solve(SCRIPTS[name]))


def produced(name):
    body = REP["trails"].get(name)
    if not isinstance(body, dict) or not isinstance(body.get("tr"), list):
        return None
    return tuple(str(x) for x in body["tr"])


def explain(name):
    got = produced(name)
    if got is None:
        return "%s: no trail" % name
    want = expected(name)
    if got == want:
        return None
    lines = SCRIPTS[name].split("\n")
    evs = [ln for ln in lines if ln.strip() and not ln.startswith(("screen ", "w "))]
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "missing"
        b = want[i] if i < len(want) else "nothing"
        if a != b:
            ev = evs[i] if i < len(evs) else "?"
            return "%s: after event %d (%s) focus is %s, expected %s" % (name, i + 1, ev, a, b)
    return "%s: differs" % name


def sweep(names):
    bad = [x for x in (explain(n) for n in names) if x]
    if bad:
        pytest.fail("%d of %d scripts wrong\n%s" % (len(bad), len(names), "\n".join(bad[:8])))


# ------------------------------------------------------------------ the run itself

def test_the_run_reported_every_script():
    assert REP.get("nonce") == NONCE, "the report does not carry this run's nonce"
    assert not REP["faults"], "the toolkit raised on %d scripts: %s" % (
        len(REP["faults"]), sorted(REP["faults"])[:4])
    missing = [n for n in SCRIPTS if n not in REP["trails"]]
    assert not missing, "no trail for %d scripts: %s" % (len(missing), missing[:6])


# ------------------------------------------------------------------ the rules

def test_reachability_is_inherited():
    """A widget under a hidden, disabled or shut container cannot take focus."""
    sweep(REACH)


def test_groups_have_one_stop():
    """The selected member is the stop when it can take focus, else the first that can;
    an unselected member can still hold focus by request."""
    sweep(GROUPS)


def test_composites_are_one_stop_with_a_memory():
    """Entering a composite from either direction lands on the remembered descendant;
    the memory learns from every landing; arrows move inside without wrapping."""
    sweep(COMPOSITES)


def test_screens_land_and_return():
    """A push lands on the first auto widget that can take focus; a pop returns to where
    focus was, resolved against the tree as it is at the pop."""
    sweep(SCREENS)


def test_screens_popped_out_of_order():
    """A return through a screen that has already gone lands where that screen would
    have returned to."""
    sweep(ORDER)


def test_requests_for_screens_below_are_held():
    """The latest request for a screen not on top is honoured when it next is, against
    the tree as it is then, and it outranks the return record."""
    sweep(REQUESTS)


def test_lost_focus_starts_from_the_place():
    """Focus lost to a hide, a drop, a disable or a move starts the next key from the
    widget's place, and the place of a dropped widget does not move."""
    sweep(LOST)


def test_nested_scopes():
    """Scope traversal, local group representatives, branch memory and deferred returns."""
    sweep(sorted(n for n in cases.CASES if n.startswith("nested-")))


def test_widget_instances_survive_name_reuse():
    """Saved state stays with the retired instance; a new request addresses the replacement."""
    sweep(sorted(n for n in cases.CASES if n.startswith("instance-")))


def test_generated_scripts():
    """All fixed-seed generated families must pass in full."""
    sweep(sorted(n for n in SCRIPTS if n not in cases.CASES))


def test_render_transactions_preserve_order_and_identity():
    """Commits evaluate bound intents on the final tree; aborts restore original instances."""
    sweep(sorted(n for n in cases.CASES if n.startswith("tx-")))


def test_transaction_inputs_obey_the_documented_contract():
    """This input-only parser checks nesting, rollback, allocation and tree legality."""
    for name, text in SCRIPTS.items():
        if not name.startswith(("tx-", "transaction-")):
            continue
        state = transaction_gen.InputState()
        for raw in text.splitlines():
            if raw.strip():
                state.apply(raw)
        assert not state.frames, name


def test_each_group_has_at_most_one_selected_member():
    """Every graded script respects the instruction's singular selected-member state."""
    for name, text in SCRIPTS.items():
        sim = oracle.BufferedSim()
        created = 0
        for raw in text.splitlines():
            toks = raw.split()
            if not toks:
                continue
            sim.feed(toks)
            created += toks[0] in ("w", "add")
            assert created <= 40 and len(sim.screens) <= 5, name
            selected = {}
            for wid in sim.par:
                group = sim.grp[wid]
                if sim.live(wid) and group is not None and "sel" in sim.fl[wid]:
                    key = (sim.home[wid], group)
                    selected.setdefault(key, []).append(wid)
            duplicates = {key: members for key, members in selected.items()
                          if len(members) > 1}
            assert not duplicates, "%s contains multiple selected group members: %s" % (
                name, duplicates)
        assert not sim.frames, name


# ------------------------------------------------------------------ the model

def test_the_sealed_model_still_reproduces_the_truth():
    assert sorted(TRUTH["cases"]) == sorted(cases.CASES), \
        "gt.json and cases.py describe different sets"
    for name in sorted(cases.CASES):
        assert oracle.solve(cases.CASES[name]) == list(TRUTH["cases"][name]), \
            "oracle.py has drifted on %s" % name


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
    assert checked >= 6, "only %d frozen files were compared" % checked


def _inner(code, name):
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
            node = _inner(node, part)
        out["%s#%s" % (rel, qual)] = runner.digest(node)
    return runner.stamp(out)


def test_frozen_functions_were_the_shipped_ones():
    if not os.path.isdir(PRISTINE):
        pytest.skip("no pristine tree")
    want = compiled_baseline()
    bad = [n for n in sorted(REP["trails"])
           if REP["trails"][n].get("fp") != want or REP["trails"][n].get("fp2") != want]
    assert not bad, "frozen functions were replaced during %d scripts: %s" % (len(bad), bad[:4])


def test_instrumentation_was_intact():
    """Every trail row came out of Ui.step, and the interpreter's instrumentation was
    still armed when each script ended. How often the policy itself was entered is not
    graded: a correct policy may re-enter its own entry point however it likes."""
    need = os.environ.get("REQUIRE_MONITORING") == "1"
    bad = []
    for n in sorted(REP["trails"]):
        r = REP["trails"][n]
        mon = r.get("mon") or {}
        rows = len(r.get("tr") or [])
        if not r.get("arm"):
            bad.append("%s: instrumentation was disturbed" % n)
        elif need and r.get("how") != "monitoring":
            bad.append("%s: instrumentation fell back to %s" % (n, r.get("how")))
        elif mon.get("step") != rows:
            bad.append("%s: %d rows but Ui.step ran %s times" % (n, rows, mon.get("step")))
    assert not bad, "\n".join(bad[:6])
