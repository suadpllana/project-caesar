"""Verifier for the delta view retraction task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather
than only in STATE.md because this is the file the run audit and the quality review read.

What the run produced is in /work/out.json, written by /tests/runner.py, which is the only
process that executed anything the agent wrote. Nothing in this file imports, execs or
subprocesses agent code: it reads that JSON as hostile input and grades it against
/tests/gt.json, which is root-only and was never visible to the run.

Nothing in the run's report is taken on trust. Every number in it was produced inside the
process that executed the agent's file, so a report on its own is a claim and not evidence.
What makes it evidence is the work journal view/core.py records - one entry per value
folded, per group reread from the row store, and per publication - which is checked three
ways before any of it is believed: the counters must equal what the journal contains, the
published values must be what the journal's work actually produces when it is folded back
through a sealed accumulator here, and every record in it must be one the scenario made
possible. A submission that writes its answers instead of computing them has to forge a
journal that survives all three, and a journal that survives all three is the work.

Four independent axes are checked and all of them must hold.

  1. VALUES. The final view map and every emitted (seq, group, kind, value) record, exact.
     Ground truth is re-proved here by oracle.py, a sealed implementation that shares no
     code with the engine tree: it keeps the full surviving multiset for every group and
     folds each aggregate over all of it, with no cap, no accumulator and no incremental
     repair. That is the definition the bounded accumulator is an optimisation of, so a
     submission whose accumulator drifted cannot match it.

  2. WORK. folds and scans, counted inside view/core.py, which is NOT an editable
     artifact, so they measure real work whatever the submitted implementation looks
     like. A fold is one value actually folded into an accumulator; a scan is one group
     actually re-read from the row store.

     Both are graded as a BUDGET rather than as an equality, and the budget is what the
     cheapest correct maintenance this environment allows actually spends. That direction
     is deliberate and it is the run-audit lesson applied honestly: two correct
     implementations of an optimisation do not have to agree on how far they took it, and
     an earlier version of this file graded equality against a reference that a submitted
     solution beat on six of the twelve scenarios while publishing every value correctly.
     Grading a ceiling cannot fail a better answer, and it cannot be bought from below,
     because axis 3 ties both counters to a journal that has to reproduce the published
     values and to the interpreter's own tally of the work.

     This is the axis that fails a submission that is merely safe. Rebuilding every
     order-sensitive cell on every retraction - the answer the literature gives - returns
     every value correctly and is over the budget on nine of the twelve scenarios. So is
     the reading that rebuilds whenever the accumulator has lost anything, which is
     correct, is the natural place to stop, and is over the budget on six.

  3. EVIDENCE. The work journal. folds and scans are required to equal the number of fold
     and scan records it holds, so a counter cannot be assigned; the journal replayed
     through the sealed accumulator in oracle.py must reproduce the published view and
     every published value, so a view cannot be pasted in; and every record must match
     what the scenario allows - a reread of a group folds exactly the rows the row store
     held at that delta, an incremental fold matches an edit that delta produced and is
     charged once, and no work may be charged to a group the delta never touched.

     The executed tree is attested too: the engine outside the declared artifact must be
     byte-identical to the pristine copy after the run, so the counted code is the code
     that shipped.

  4. LIFECYCLE. The emit log in order and the driver's own trace: which deltas arrived
     behind the watermark, when the watermark advanced, and which cells were emitted at
     each advance. The driver is not editable, so this pins that the submission did not
     move the emit schedule to make its numbers work.

DELIBERATELY NOT GRADED, because grading them would measure an implementation choice
rather than work (the run-audit lesson: a graded quantity two correct implementations
disagree on is a trap, not a test):

  - Any count of reads or writes against the row store. A submission may legitimately
    batch, cache or reorder its own reads; only folds and scans measure the work the task
    is about.
  - The order in which a submission visits the (group, kind) cells affected by one delta.
    Only the emit log, which the non-editable driver produces, is order-sensitive.
  - Whether a cell that ends up empty is rebuilt or folded to empty. Both reach the same
    accumulator and the same fold count.

Per-scenario notes on which reading of the rule each case is aimed at live in scen.py and
are quoted in the failure messages below.
"""

import hashlib
import json
import os

import pytest

import oracle
import scen

OUT_PATH = os.environ.get("RUN_OUT", "/work/run/out.json")
HERE = os.path.dirname(os.path.abspath(__file__))
GT_PATH = os.path.join(HERE, "gt.json")
CONF_PATH = os.path.join(HERE, "view.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE_DIR = os.environ.get("PRISTINE_DIR", "/pristine")
ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "/app")
ARTIFACTS = ("view/route.py",)
NONCE = os.environ.get("RUN_NONCE", "")
# Set by test.sh. The verifier image is Python 3.12, where the tally comes from
# sys.monitoring; the weaker profile hook exists for the authoring host only, and
# is not something a run gets to fall back to here.
STRICT_MON = os.environ.get("REQUIRE_MONITORING") == "1"

NAMES = [s["name"] for s in scen.SCENARIOS]
AIM = {s["name"]: s["aim"] for s in scen.SCENARIOS}


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


GT = load_json(GT_PATH)
RUN = load_json(OUT_PATH)
BASE = load_json(CONF_PATH)


def report(name):
    """The run's report for one scenario, or None if the run produced nothing usable.

    Everything here came from agent code, so every access is defensive: wrong types,
    missing keys and junk values must produce a clean failure, never an exception that
    escapes the test and skips the verdict.
    """
    if not isinstance(RUN, dict):
        return None
    reps = RUN.get("reports")
    if not isinstance(reps, dict):
        return None
    rep = reps.get(name)
    if not isinstance(rep, dict):
        return None
    return rep


def expected(name):
    return GT["scenarios"][name]


def cfg_for(name):
    cfg = json.loads(json.dumps(BASE))
    for k, v in (scen.by_name(name).get("cfg") or {}).items():
        cfg[k] = v
    return cfg


def as_rows(x):
    """Coerce a run-supplied list-of-lists into a comparable form, or None."""
    if not isinstance(x, list):
        return None
    out = []
    for r in x:
        if not isinstance(r, list):
            return None
        out.append(list(r))
    return out


def test_ground_truth_present():
    assert isinstance(GT, dict) and GT.get("scenarios"), "ground truth missing"
    assert isinstance(BASE, dict) and BASE.get("view"), "view config missing"
    assert set(GT["scenarios"]) == set(NAMES), "ground truth does not cover the scenario set"


def test_run_completed():
    """Every scenario has to run. A crash is a failure, not a skipped case."""
    assert isinstance(RUN, dict), "no usable run output at %s" % OUT_PATH
    if NONCE:
        assert RUN.get("nonce") == NONCE, (
            "the graded output was not written by this run's runner")
    errs = RUN.get("errors") or {}
    assert not errs, "the engine raised in: %s" % ", ".join(sorted(errs))
    reps = RUN.get("reports")
    assert isinstance(reps, dict), "run output carries no reports"
    assert set(reps) == set(NAMES), (
        "not every scenario reported: missing %s" % sorted(set(NAMES) - set(reps)))


@pytest.mark.parametrize("name", NAMES)
def test_ground_truth_is_independently_reproducible(name):
    """Axis 1, first half: the recorded ground truth still matches the sealed definition.

    This runs oracle.py - which shares no code with the engine tree - over the scenario
    and requires it to reproduce the stored view and emit log exactly. It grades nothing
    the agent did; it proves the numbers the other tests grade against are the aggregate
    over the full surviving multiset, and not an artifact of how the reference happened
    to be written.
    """
    exp = expected(name)
    t = oracle.Truth(cfg_for(name))
    t.run(scen.by_name(name)["ops"])
    assert t.view() == exp["view"], (
        "stored ground truth for %s disagrees with the sealed oracle" % name)
    assert [list(x) for x in t.log] == [list(x) for x in exp["log"]], (
        "stored emit log for %s disagrees with the sealed oracle" % name)


@pytest.mark.parametrize("name", NAMES)
def test_view_values(name):
    """Axis 1: the maintained view must equal the aggregate over the surviving multiset."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    got = rep.get("view")
    assert isinstance(got, dict), "%s: view is not an object" % name
    assert got == exp["view"], (
        "%s: view is wrong.\n  aim: %s\n  expected %s\n  got      %s"
        % (name, AIM[name], json.dumps(exp["view"], sort_keys=True),
           json.dumps(got, sort_keys=True)))


@pytest.mark.parametrize("name", NAMES)
def test_emitted_values(name):
    """Axis 1: every value published at a watermark advance, in order.

    The final view can be right while intermediate emits were wrong, which is exactly
    what a submission that repairs lazily and settles at the end looks like.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    got = as_rows(rep.get("log"))
    assert got is not None, "%s: emit log is not a list of records" % name
    assert got == [list(x) for x in exp["log"]], (
        "%s: emitted values differ from ground truth.\n  aim: %s\n  first difference: %s"
        % (name, AIM[name], _first_diff(got, [list(x) for x in exp["log"]])))


@pytest.mark.parametrize("name", NAMES)
def test_work_counters(name):
    """Axis 2: the work has to come in under the budget.

    folds and scans are incremented in view/core.py, outside the editable set. Correct
    values with counters over the budget is the signature of a submission that plays safe
    and rebuilds when it did not have to.

    This is a ceiling and not an equality, deliberately. The budget is what the cheapest
    correct maintenance this environment allows actually spends, so a submission can only
    get under it by doing less real work than that while still publishing every value
    exactly - which is a better answer than the reference, not a worse one, and the run
    audit exists to stop a verifier failing those. Nothing can buy its way under the
    ceiling by declaring less than it did: the evidence axis ties both counters to a work
    journal that has to reproduce the published values, and to the interpreter's own
    tally.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    for field in ("folds", "scans"):
        got = rep.get(field)
        assert isinstance(got, int) and not isinstance(got, bool), (
            "%s: %s is not an integer" % (name, field))
        assert got >= 0, "%s: %s is negative" % (name, field)
        assert got <= exp[field], (
            "%s: %s is %d, and the budget is %d (the shipped tree spends %d here).\n"
            "  aim: %s"
            % (name, field, got, exp[field], exp["shipped_%s" % field], AIM[name]))


def journal(name):
    """The run's work journal for one scenario, or None. Hostile input, like the rest."""
    rep = report(name)
    if rep is None:
        return None
    j = rep.get("jrn")
    if not isinstance(j, list):
        return None
    return j


@pytest.mark.parametrize("name", NAMES)
def test_work_journal_accounts_for_the_counters(name):
    """Axis 3: the counters are read off the journal, never taken from the report.

    folds and scans are assignable attributes on an object the submitted file holds a
    reference to, so a number on its own proves nothing. Requiring them to equal what the
    journal contains means a submission that wants a counter has to produce the records
    that justify it, and those records are checked by the two tests below.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    bad = oracle.shape(j)
    assert bad is None, "%s: %s" % (name, bad)
    tally = {"f": 0, "s": 0, "e": 0}
    for e in j:
        tally[e[0]] += 1
    assert rep.get("folds") == tally["f"], (
        "%s: reports %r folds, journal records %d" % (name, rep.get("folds"), tally["f"]))
    assert rep.get("scans") == tally["s"], (
        "%s: reports %r scans, journal records %d" % (name, rep.get("scans"), tally["s"]))
    assert rep.get("emits") == tally["e"], (
        "%s: reports %r emits, journal records %d" % (name, rep.get("emits"), tally["e"]))


@pytest.mark.parametrize("name", NAMES)
def test_work_journal_produces_the_published_values(name):
    """Axis 3: the published values have to be what the recorded work computes.

    The journal is folded back through oracle.Bag, a second implementation of the bounded
    accumulator that shares no code with store/agg.py. What comes out has to be the view
    the submission published and the values it published on the way, which ties every
    number in the report to work the engine actually did.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    assert oracle.shape(j) is None, "%s: malformed work journal" % name
    view, emitted, bad = oracle.replay(j)
    assert bad is None, "%s: %s" % (name, bad)
    assert view == rep.get("view"), (
        "%s: the published view is not what the recorded work produces.\n"
        "  published %s\n  recorded  %s"
        % (name, json.dumps(rep.get("view"), sort_keys=True), json.dumps(view, sort_keys=True)))
    assert emitted == as_rows(rep.get("log")), (
        "%s: the published values are not what the recorded work produces.\n"
        "  first difference: %s"
        % (name, _first_diff(emitted, as_rows(rep.get("log")) or [])))


@pytest.mark.parametrize("name", NAMES)
def test_work_journal_is_possible(name):
    """Axis 3: every record has to be work the scenario allowed.

    A reread of a group folds exactly the rows the row store held at that delta; an
    incremental fold matches one of the edits that delta produced and is charged once; no
    work is charged to a group the delta never touched or to an aggregate the source does
    not feed. The scenario model doing the deciding is in oracle.py and is root-only.
    """
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    assert oracle.shape(j) is None, "%s: malformed work journal" % name
    bad = oracle.audit(j, scen.by_name(name)["ops"], cfg_for(name))
    assert bad is None, "%s: %s\n  aim: %s" % (name, bad, AIM[name])


@pytest.mark.parametrize("name", NAMES)
def test_all_work_went_through_the_counted_path(name):
    """Axis 3: the accumulator's own record of its folds must be the work that was charged.

    store/agg.py logs every fold at the point it happens, so that log is the total amount
    of aggregate work the submission did by any route. The core's journal is the work it
    declared. Requiring the two to be the same list, in order, is what stops an engine
    from repairing cells behind the core's back: a submission can fold a whole group back
    together for free and report an incremental cost, and the published values and the
    counters both come out right, because nothing in the counted path is wrong - it is
    merely no longer the path that did the work.

    Every correct implementation satisfies this by construction: a cell's accumulator is
    reached through the core's two operations, and both of them charge for what they fold.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    assert oracle.shape(j) is None, "%s: malformed work journal" % name
    bad = oracle.reconcile(j, rep.get("deep"))
    assert bad is None, "%s: %s\n  aim: %s" % (name, bad, AIM[name])


@pytest.mark.parametrize("name", NAMES)
def test_the_interpreter_agrees_about_how_much_work_happened(name):
    """Axis 3: the work counted by the interpreter, which no submitted file can edit.

    Every other number here is a record the engine keeps, and those can be reached from
    the file the agent writes. This one is a tally of entries into agg.fold, Core.apply
    and Core.rebuild taken through sys.monitoring by the runner, kept in a closure rather
    than in the tree, and it sees a call however it was reached. It has to agree with the
    counters and with the ground truth, which is what makes the counters a measurement of
    cost rather than a declaration of it.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    tally = rep.get("mon")
    assert isinstance(tally, dict), "%s: the run recorded no independent tally" % name
    assert rep.get("mon_intact") is True, (
        "%s: the run interfered with the verifier's instrumentation" % name)
    if STRICT_MON:
        assert rep.get("mon_how") == "monitoring", (
            "%s: the work was tallied by %r, not by the interpreter"
            % (name, rep.get("mon_how")))
    exp = expected(name)
    # Against the submission's own counters, exactly: that is what stops work happening
    # off the counted path. Against the budget, as a ceiling, for the reason set out in
    # test_work_counters.
    assert tally.get("fold") == rep.get("folds"), (
        "%s: the accumulator was entered %r times and %r folds were charged for.\n"
        "  Work done outside the counted path is still work done.\n  aim: %s"
        % (name, tally.get("fold"), rep.get("folds"), AIM[name]))
    assert tally.get("rebuild") == rep.get("scans"), (
        "%s: the group was reread %r times and %r scans were charged for.\n  aim: %s"
        % (name, tally.get("rebuild"), rep.get("scans"), AIM[name]))
    assert tally.get("fold") <= exp["folds"] and tally.get("rebuild") <= exp["scans"], (
        "%s: the interpreter counted %r folds and %r rereads, over a budget of %d and %d"
        % (name, tally.get("fold"), tally.get("rebuild"), exp["folds"], exp["scans"]))


@pytest.mark.parametrize("name", NAMES)
def test_engine_functions_were_not_replaced(name):
    """Axis 3: the counting code that ran is the counting code that shipped.

    Hashing the tree catches a submission that rewrites view/core.py on disk. This catches
    the one that leaves the file alone and rebinds the function, which is the cheaper
    attack on every counter and on the driver's report. The run fingerprints the engine
    twice, once at import and once when the scenario is over, and the grader compiles the
    pristine sources to work out what those fingerprints have to be.
    """
    if not os.path.isdir(PRISTINE_DIR):
        pytest.skip("no pristine tree to attest against")
    want = oracle.expected_fingerprints(PRISTINE_DIR)
    assert want, "no sealed functions could be compiled from the pristine tree"
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    for when in ("fp", "fp_end"):
        got = rep.get(when)
        assert isinstance(got, dict), "%s: the run recorded no engine fingerprints" % name
        wrong = sorted(k for k, v in want.items() if got.get(k) != v)
        assert not wrong, (
            "%s: these engine functions are not the ones that shipped (%s): %s"
            % (name, "at import" if when == "fp" else "after the run", ", ".join(wrong)))


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(base, f)
            out[os.path.relpath(full, root).replace(os.sep, "/")] = _digest(full)
    return out


def test_executed_tree_was_the_shipped_tree():
    """Axis 3: the code that did the counting is the code that shipped.

    The counters live in view/core.py and the edits are split in view/land.py, neither of
    which is a declared artifact. That guarantee is only worth anything if the tree the
    run executed still matches the pristine copy afterwards, so it is checked rather than
    assumed: every file outside the declared set must be byte-identical, and the declared
    file must be the one that was uploaded.
    """
    if not os.path.isdir(APP_DIR) or not os.path.isdir(PRISTINE_DIR):
        pytest.skip("no executed tree to attest")
    ran = _tree(APP_DIR)
    want = _tree(PRISTINE_DIR)
    for rel in ARTIFACTS:
        supplied = os.path.join(ARTIFACT_DIR, rel)
        if os.path.isfile(supplied):
            want[rel] = _digest(supplied)
    assert set(ran) == set(want), (
        "the executed tree gained or lost files: added %s, missing %s"
        % (sorted(set(ran) - set(want)), sorted(set(want) - set(ran))))
    moved = sorted(r for r in want if ran[r] != want[r])
    assert not moved, "the executed tree was modified during the run: %s" % moved


def test_sealed_config_matches_the_shipped_config():
    """The config the verifier grades against is the one the engine was handed."""
    shipped = os.path.join(PRISTINE_DIR, "conf", "view.json")
    if not os.path.isfile(shipped):
        pytest.skip("no pristine config to compare")
    assert load_json(shipped) == BASE, "the sealed view config is not the shipped one"


@pytest.mark.parametrize("name", NAMES)
def test_lifecycle_trace(name):
    """Axis 3: the driver's own record of watermarks, late deltas and emits, in order."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    got = as_rows(rep.get("trace"))
    assert got is not None, "%s: trace is not a list of records" % name
    assert got == [list(x) for x in exp["trace"]], (
        "%s: lifecycle trace differs.\n  aim: %s\n  first difference: %s"
        % (name, AIM[name], _first_diff(got, [list(x) for x in exp["trace"]])))
    assert rep.get("emits") == exp["emits"], (
        "%s: emitted %r records, expected %d" % (name, rep.get("emits"), exp["emits"]))
    assert rep.get("revised") == exp["revised"], (
        "%s: counted %r late deltas, expected %d" % (name, rep.get("revised"), exp["revised"]))


def _first_diff(got, want):
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "<missing>"
        b = want[i] if i < len(want) else "<extra>"
        if a != b:
            return "at index %d: got %r, expected %r" % (i, a, b)
    return "none"
