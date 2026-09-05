"""The grader for focus-return-point. Runs as root after the run has been reaped, and
never imports, execs or subprocesses anything the agent wrote.

THE VERIFIER CONTRACT, frozen before the environment was finished, and kept here because
this is the file the run audit and the quality review read.

WHAT IS GRADED. One thing, on every script, exactly, all or nothing: the trail - which
widget holds focus after each event, or `none`. The trail is written by ui/core.py, which
is not an editable artifact, from the focus the core holds after the policy has answered,
so it records what the toolkit did rather than what a submission says it did.

TWO SCRIPT SETS. The enumerated set in cases.py is 45 scripts, one per rule, each named
for the reading it exists to fail, and its expected trails are in gt.json - which were
derived by hand from the rules before either implementation existed (authoring/handcheck.py
carries those literals and build_gt.py refuses to write a ground truth that differs). The
generated set is 300 scripts built by gen.py from a nonce made in test.sh from /dev/urandom
after the agent has finished; their expected trails are produced here by oracle.py, a
second implementation written from the rules that shares no code with the tree or the
reference. Those scripts did not exist when the submission was written, so there is no
table to paste and no report to forge.

gt.json is therefore a tripwire rather than the answer: the model is required to reproduce
it on the enumerated set, so a drift in oracle.py fails loudly instead of silently
regrading the task.

NOT GRADED, because two correct implementations may differ on it: how the policy stores
its records, how many times it consults the tree, which representation it uses for a
point, whether it resolves a chain iteratively or recursively, and what it does on events
the rules say change nothing. Four alternative correct implementations in
authoring/variants are required to score 1.

INTEGRITY, because the verifier executes agent code:
  - the executed tree outside the four declared artifacts is byte-identical to the
    pristine copy, and the comparison counts the files it checked before it believes
    itself;
  - every frozen function is digested as it existed in the running interpreter, at import
    and after each script, against digests compiled here from the pristine sources;
  - trail rows are appended by a closure the runner owns which refuses any caller other
    than Ui.step, and the interpreter's own count of entries into Ui.step must equal the
    number of rows and still have been armed when each script ended;
  - the report carries the run nonce.
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
ARTIFACTS = frozenset(("ui/focus.py", "ui/keep.py", "ui/reach.py", "ui/mem.py"))

REACH = ("reach-inherits-hidden", "reach-inherits-shut", "reach-inherits-disabled-focused")
GROUPS = ("group-selected-is-the-stop", "group-none-selected", "group-selected-unreachable",
          "group-unselected-holds-focus", "pick-keeps-focus")
COMPOSITES = ("comp-is-one-stop", "comp-back-lands-on-memory", "comp-memory-from-request",
              "comp-memory-gone", "comp-arrows-do-not-wrap", "comp-empty-is-no-stop",
              "want-inside-composite", "comp-keys-leave-it")
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


def test_generated_scripts():
    """Three hundred scripts neither the author nor the submission has seen."""
    sweep(sorted(n for n in SCRIPTS if n not in cases.CASES))


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
