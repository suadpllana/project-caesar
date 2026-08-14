"""Verifier for the segment merge horizon task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather
than only in STATE.md because this is the file the run audit and the quality review read.

What the run produced is in the work file written by /tests/runner.py, which is the only
process that executed anything the agent wrote. Nothing in this file imports, execs or
subprocesses agent code: it reads that JSON as hostile input and grades it against
/tests/gt.json, which is root-only and was never visible to the run.

Nothing in the run's report is taken on trust. Every number in it was produced inside the
process that executed the agent's file, so a report on its own is a claim and not evidence.
What makes it evidence is the work journal merge/core.py records - one entry per record
pulled out of a job, per point read of the rest of the store, and per record written to the
output - which is checked four ways before any of it is believed: the counters must equal
what the journal contains, replaying the journal's writes must reproduce the store the run
says it produced, every written record must be one the declared reads determine, and the
segment layer's own log of what it materialised must be the same list in the same order.
A submission that writes its answers instead of computing them has to forge a journal that
survives all four, and a journal that survives all four is the work.

Four independent axes are checked and all of them must hold.

  1. VALUES. Every read the store can answer - each key at each read point, after every job
     and again at the end - exact. Ground truth is re-proved here by oracle.Truth, which
     shares no code with the engine tree: it keeps every record ever written and answers a
     read by walking that history, so it never merges anything. A merge is an optimisation
     over that definition, which means a submission that discarded a record it needed, or
     kept an adjust without the base it stands on, cannot match it.

  2. WORK. reads, writes and probes, counted inside merge/core.py, which is NOT an editable
     artifact, so they measure real work whatever the submitted plan looks like. A read is
     one record actually pulled out of the merged input, a write is one record actually
     placed in the output segment, and a probe is one point read against the segments the
     job does not own.

     All three are graded as a BUDGET rather than as an equality, and the budget is what the
     cheapest correct merge this environment allows actually spends. That direction is
     deliberate and it is the run-audit lesson applied honestly: a verifier that fails a
     better answer than the reference is the failure mode, and a ceiling cannot do that. It
     cannot be bought from below either, because axis 3 ties every counter to a journal that
     has to reproduce the published reads and to the interpreter's own tally.

     This is the axis that fails a submission that is merely safe. Draining each key instead
     of stopping where the answers stop is correct on every value and over the read budget
     on eight of the fourteen scenarios. Keeping one record per read point instead of one
     per distinct outcome is correct and over the write budget. So is never dropping the
     lowest record because the rest of the store was not asked.

  3. EVIDENCE. The work journal, four ways, plus the attestation that the counting code is
     the code that shipped. See the module docstring above and the tests themselves.

  4. LIFECYCLE. The driver's own trace: which segments each job merged, at which read
     points, and where the flushes fell. The driver is not editable, so this pins that a
     submission did not move the job schedule to make its numbers work.

DELIBERATELY NOT GRADED, because grading them would measure an implementation choice rather
than work (the run-audit lesson: a graded quantity two correct implementations disagree on
is a trap, not a test):

  - The shape of the output segment - how many records it holds, in what order, and at which
    sequences. Two correct plans encode the same answers differently, and only the reads
    those encodings produce are the task.
  - The order in which a plan visits the keys of one job, or interleaves its point reads
    with its writes. Only the totals and the driver's own trace are order sensitive.
  - Whether a plan closes an open outcome with a difference or with an absolute record it
    got from a point read. Both are correct, both cost one record, and oracle.justify
    accepts either.
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
CONF_PATH = os.path.join(HERE, "store.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE_DIR = os.environ.get("PRISTINE_DIR", "/pristine")
ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "/app")
ARTIFACTS = ("merge/plan.py",)
NONCE = os.environ.get("RUN_NONCE", "")
# Set by test.sh. The verifier image is Python 3.12, where the tally comes from
# sys.monitoring; the weaker profile hook exists for the authoring host only and is not
# something a run gets to fall back to here.
STRICT_MON = os.environ.get("REQUIRE_MONITORING") == "1"

NAMES = [s["name"] for s in scen.SCENARIOS]
AIM = {s["name"]: s["aim"] for s in scen.SCENARIOS}
COUNTERS = ("reads", "writes", "probes")


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

    Everything here came from agent code, so every access is defensive: wrong types, missing
    keys and junk values must produce a clean failure, never an exception that escapes the
    test and skips the verdict.
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
    """Coerce a run-supplied list of lists into a comparable form, or None."""
    if not isinstance(x, list):
        return None
    out = []
    for r in x:
        if not isinstance(r, list):
            return None
        out.append(list(r))
    return out


def as_maps(x):
    """The same for a list of read maps, one per job."""
    if not isinstance(x, list):
        return None
    out = []
    for m in x:
        rows = as_rows(m)
        if rows is None:
            return None
        out.append(rows)
    return out


def _first_diff(got, want):
    for i in range(max(len(got), len(want))):
        a = got[i] if i < len(got) else "<missing>"
        b = want[i] if i < len(want) else "<extra>"
        if a != b:
            return "at index %d: got %r, expected %r" % (i, a, b)
    return "none"


def test_ground_truth_present():
    assert isinstance(GT, dict) and GT.get("scenarios"), "ground truth missing"
    assert isinstance(BASE, dict) and BASE.get("tier"), "store config missing"
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

    This runs oracle.Truth - which shares no code with the engine tree - over the scenario
    and requires it to reproduce the stored reads exactly. It grades nothing the agent did;
    it proves the numbers the other tests grade against are what the whole history says,
    and not an artifact of how the reference happened to be written.
    """
    exp = expected(name)
    t = oracle.Truth(cfg_for(name))
    t.run(scen.by_name(name)["ops"])
    assert t.map() == exp["view"], (
        "stored ground truth for %s disagrees with the sealed definition" % name)
    assert [[list(x) for x in m] for m in t.snaps] == exp["snaps"], (
        "stored per job reads for %s disagree with the sealed definition" % name)


@pytest.mark.parametrize("name", NAMES)
def test_reads_after_every_job(name):
    """Axis 1: what the store answers after each merge, key by key and read point by read
    point.

    The final state can be right while an intermediate one was wrong - a job that discarded
    a record a pinned read point needed is invisible later if a subsequent write covers the
    key again. Checking after every job is what makes that fatal.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    got = as_maps(rep.get("snaps"))
    assert got is not None, "%s: the per job reads are not a list of read maps" % name
    assert got == exp["snaps"], (
        "%s: the store answers differently after a merge than it did before it.\n"
        "  aim: %s\n  first job that differs: %s"
        % (name, AIM[name], _first_diff(got, exp["snaps"])))


@pytest.mark.parametrize("name", NAMES)
def test_final_reads(name):
    """Axis 1: every read the store can answer once the stream is over."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    got = as_rows(rep.get("view"))
    assert got is not None, "%s: the final read map is not a list of records" % name
    assert got == exp["view"], (
        "%s: the store no longer answers what the record history says.\n"
        "  aim: %s\n  first difference: %s"
        % (name, AIM[name], _first_diff(got, exp["view"])))


@pytest.mark.parametrize("name", NAMES)
def test_work_counters(name):
    """Axis 2: the work has to come in under the budget.

    reads, writes and probes are incremented in merge/core.py, outside the editable set.
    Correct values with counters over the budget is the signature of a plan that plays safe:
    it drains every key rather than stopping where the answers stop, or it keeps a record
    per read point rather than a record per distinct outcome.

    This is a ceiling and not an equality, deliberately. The budget is what the cheapest
    correct merge this environment allows actually spends, so a submission can only get
    under it by doing less real work than that while still answering every read exactly -
    which is a better answer than the reference, not a worse one, and the run audit exists
    to stop a verifier failing those. Nothing can buy its way under the ceiling by declaring
    less than it did: the evidence axis ties every counter to a journal that has to
    reproduce the published reads, and to the interpreter's own tally.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    for field in COUNTERS:
        got = rep.get(field)
        assert isinstance(got, int) and not isinstance(got, bool), (
            "%s: %s is not an integer" % (name, field))
        assert got >= 0, "%s: %s is negative" % (name, field)
        assert got <= exp[field], (
            "%s: %s is %d, and the budget is %d (the shipped plan spends %d here).\n"
            "  aim: %s"
            % (name, field, got, exp[field], exp["shipped_" + field], AIM[name]))


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

    reads, writes and probes are assignable attributes on an object the submitted file holds
    a reference to, so a number on its own proves nothing. Requiring each to equal what the
    journal contains means a submission that wants a counter has to produce the records that
    justify it, and those records are checked by the tests below.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    bad = oracle.shape(j)
    assert bad is None, "%s: %s" % (name, bad)
    tally = {"r": 0, "w": 0, "p": 0}
    for e in j:
        tally[e[0]] += 1
    for field, tag in zip(COUNTERS, ("r", "w", "p")):
        assert rep.get(field) == tally[tag], (
            "%s: reports %r %s, journal records %d"
            % (name, rep.get(field), field, tally[tag]))


@pytest.mark.parametrize("name", NAMES)
def test_work_journal_produces_the_published_reads(name):
    """Axis 3: the reads the run published have to be what its recorded writes produce.

    oracle.check replays the scenario, and at every job replaces the merged segments with
    exactly the records the journal says the run wrote. What the store then answers has to
    be what the submission reported answering, which ties the view to work rather than to a
    string it chose to return.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    assert oracle.shape(j) is None, "%s: malformed work journal" % name
    view, snaps, bad = oracle.check(j, scen.by_name(name)["ops"], cfg_for(name))
    assert bad is None, "%s: %s\n  aim: %s" % (name, bad, AIM[name])
    assert view == as_rows(rep.get("view")), (
        "%s: the published reads are not what the recorded writes produce.\n"
        "  first difference: %s" % (name, _first_diff(view, as_rows(rep.get("view")) or [])))
    assert snaps == as_maps(rep.get("snaps")), (
        "%s: the published per job reads are not what the recorded writes produce"
        % name)


@pytest.mark.parametrize("name", NAMES)
def test_every_written_record_was_earned(name):
    """Axis 3: a plan may only write records its declared reads determine.

    This is the check that makes the read counter mean something. A submission is free to
    reach the right answer without pulling records for it - by reading the segments behind
    the cursor, or by knowing the scenario - but the records it writes are then unexplained:
    oracle.justify works out, from the records that job declared it pulled for that key,
    exactly which records are derivable, and a write outside that set is rejected. It also
    checks the other direction, that a declared read really is the next record the merged
    input hands out, so a journal cannot be padded either.

    oracle.check performs it as part of the replay; this test states it separately so a
    failure names the right thing.
    """
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    assert oracle.shape(j) is None, "%s: malformed work journal" % name
    _, _, bad = oracle.check(j, scen.by_name(name)["ops"], cfg_for(name))
    assert bad is None, "%s: %s\n  aim: %s" % (name, bad, AIM[name])


@pytest.mark.parametrize("name", NAMES)
def test_the_segments_handed_out_what_the_job_paid_for(name):
    """Axis 3: the segment layer's own log against the work the core charged for.

    seg/table.py records every record it materialises, at the point it materialises it, and
    merge/core.py records what it charged for. Requiring the two to be the same list in the
    same order is what stops a plan from doing its real work beside the counted path: a
    submission can pull a whole key group through a reference it captured at import time and
    report a cost that never saw it, and the values and the counters both come out right,
    because nothing in the counted path is wrong - it is merely no longer the path that did
    the work.

    Every correct plan satisfies this by construction: records reach it through the cursor,
    and the cursor charges for what it hands over.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    j = journal(name)
    assert j is not None, "%s: no work journal in the report" % name
    assert oracle.shape(j) is None, "%s: malformed work journal" % name
    bad = oracle.reconcile(j, rep.get("deep"), scen.by_name(name)["ops"], cfg_for(name))
    assert bad is None, "%s: %s\n  aim: %s" % (name, bad, AIM[name])


@pytest.mark.parametrize("name", NAMES)
def test_the_interpreter_agrees_about_how_much_work_happened(name):
    """Axis 3: the work counted by the interpreter, which no submitted file can edit.

    Every other number here is a record the engine keeps, and those can be reached from the
    file the agent writes. This one is a tally of entries into Core.take, Core.emit and
    Core.probe taken through sys.monitoring by the runner, kept in a closure rather than in
    the tree, and it sees a call however it was reached. It has to agree with the counters
    and with the budget, which is what makes the counters a measurement of cost rather than
    a declaration of it.
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
    for field, op in zip(COUNTERS, ("take", "emit", "probe")):
        assert tally.get(op) == rep.get(field), (
            "%s: %s was entered %r times and %r %s were charged for.\n"
            "  Work done outside the counted path is still work done.\n  aim: %s"
            % (name, op, tally.get(op), rep.get(field), field, AIM[name]))
        assert tally.get(op) <= exp[field], (
            "%s: the interpreter counted %r entries into %s, over a budget of %d"
            % (name, tally.get(op), op, exp[field]))


@pytest.mark.parametrize("name", NAMES)
def test_engine_functions_were_not_replaced(name):
    """Axis 3: the counting code that ran is the counting code that shipped.

    Hashing the tree catches a submission that rewrites merge/core.py on disk. This catches
    the one that leaves the file alone and rebinds the function, which is the cheaper attack
    on every counter and on the driver's report. The run fingerprints the engine twice, once
    at import and once when the scenario is over, and the grader compiles the pristine
    sources to work out what those fingerprints have to be.
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

    The counters live in merge/core.py and the job schedule in merge/drv.py, neither of which
    is a declared artifact. That guarantee is only worth something if the tree the run
    executed still matches the pristine copy afterwards, so it is checked rather than
    assumed: every file outside the declared set must be byte identical, and the declared
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
    shipped = os.path.join(PRISTINE_DIR, "conf", "store.json")
    if not os.path.isfile(shipped):
        pytest.skip("no pristine config to compare")
    assert load_json(shipped) == BASE, "the sealed store config is not the shipped one"


@pytest.mark.parametrize("name", NAMES)
def test_lifecycle_trace(name):
    """Axis 4: the driver's own record of the run, in order.

    Which segments each job merged, at which read points, where the flushes fell and how
    many jobs ran. None of it is the plan's to decide, so a difference here means the
    submission changed the schedule rather than the decision.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    exp = expected(name)
    got = as_rows(rep.get("trace"))
    assert got is not None, "%s: trace is not a list of records" % name
    assert got == exp["trace"], (
        "%s: the job schedule differs.\n  aim: %s\n  first difference: %s"
        % (name, AIM[name], _first_diff(got, exp["trace"])))
    assert rep.get("jobs") == exp["jobs"], (
        "%s: ran %r jobs, expected %d" % (name, rep.get("jobs"), exp["jobs"]))
