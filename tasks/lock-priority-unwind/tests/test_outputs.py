"""Verifier for the lock priority unwind task.

THE VERIFIER CONTRACT, frozen before the environment was finished. It lives here rather than
only in STATE.md because this is the file the run audit and the quality review read.

What the run produced is in the work file written by /tests/runner.py, the only process that
executed anything the agent wrote. Nothing in this file imports, execs or subprocesses agent
code: it reads that JSON as hostile input and grades it against /tests/gt.json and against
oracle.py, both of which are root-only and were never visible to the run.

WHAT IS GRADED, and all of it must hold.

  1. THE SCHEDULE. Which task held the processor at every tick, and which task finished when.
     Produced by rt/core.py, which is not editable, so it is a consequence of the priorities
     the submitted policy set rather than something the policy can write down.

  2. THE PRIORITY TABLE. What every task was worth at every tick. This is a state and not a
     call sequence, which matters: two correct policies may set the same value by different
     routes and at different moments within a tick, and grading the route would grade an
     implementation choice. The engine keeps priority changes in a separate list that is
     reported for the solver's benefit and is deliberately NOT compared here, for exactly
     that reason.

     The state itself has no freedom in it. A task is worth its own priority, or the highest
     priority among the tasks blocked - directly or through a chain - on mutexes it holds,
     whichever is greater. Raising a task higher than that is as wrong as leaving it too low,
     and three scenarios exist to fail a policy that plays safe by raising too much.

  3. THE LIFECYCLE LOG. Acquisitions, blocks, releases, abandoned waits, sleeps and
     completions, in order, all of them produced by the non-editable scheduler.

  4. THE DRAWN SCENARIOS. Everything above, again, on task sets built at verification time
     from a seed the run is given but cannot predict. Ground truth for these is computed here
     by the sealed model, right then. This is the anti-cheat design of this task and it
     replaces a work journal entirely: there is no table of answers to memorise, because the
     questions did not exist when the submission was written.

Ground truth for the fixed scenarios is re-proved on every run by oracle.Model, which shares
no code with the engine and solves the priority assignment as a fixed point over the whole
task set instead of patching it incrementally. A policy that patches the wrong task, stops at
the first link of a chain, or leaves a boost standing after the waiter that caused it gave up,
cannot agree with it.

DELIBERATELY NOT GRADED, because grading them would measure a choice rather than behaviour:

  - The sequence of priority changes, as above. Only the resulting table per tick.
  - How the policy is structured, which of the four hooks it does its work in, or whether it
    recomputes incrementally or from scratch. Three alternative correct policies in the
    authoring directory take different routes and all produce identical schedules.
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
CONF_PATH = os.path.join(HERE, "sched.json")
APP_DIR = os.environ.get("APP_DIR", "/work/app")
PRISTINE_DIR = os.environ.get("PRISTINE_DIR", "/pristine")
ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR", "/app")
ARTIFACTS = ("rt/prio.py",)
NONCE = os.environ.get("RUN_NONCE", "")

FIXED = [s["name"] for s in scen.SCENARIOS]
AIM = {s["name"]: s["aim"] for s in scen.SCENARIOS}
FIELDS = ("trace", "prio", "ev", "done", "ids", "ticks")


def read(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


GT = read(GT_PATH)
RUN = read(OUT_PATH)
BASE = read(CONF_PATH)


def drawn():
    """The scenarios this run was actually given, rebuilt from the seed it reported."""
    if not isinstance(RUN, dict):
        return []
    seed = RUN.get("seed")
    n = RUN.get("drawn")
    if not isinstance(seed, str) or not seed or not isinstance(n, int) or n <= 0 or n > 200:
        return []
    return scen.batch(scen.seed_from(seed), n)


DRAWN = drawn()
DRAWN_NAMES = [s["name"] for s in DRAWN]


def got(name):
    """One scenario's report, or None. Everything here came back from agent code."""
    if not isinstance(RUN, dict):
        return None
    runs = RUN.get("runs")
    if not isinstance(runs, dict):
        return None
    rep = runs.get(name)
    return rep if isinstance(rep, dict) else None


def cfg_for(sc):
    c = json.loads(json.dumps(BASE))
    for k, v in (sc.get("cfg") or {}).items():
        c[k] = v
    return c


def rows(x):
    if not isinstance(x, list):
        return None
    out = []
    for r in x:
        if not isinstance(r, list):
            return None
        out.append(list(r))
    return out


def first_gap(a, b):
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else "<missing>"
        y = b[i] if i < len(b) else "<extra>"
        if x != y:
            return "at index %d: got %r, expected %r" % (i, x, y)
    return "none"


def compare(name, rep, want, aim):
    """One report against one expected schedule, on every graded field."""
    assert rep is not None, "%s: no report" % name
    for f in FIELDS:
        nested = f in ("trace", "prio", "ev", "done")
        mine = rows(rep.get(f)) if nested else rep.get(f)
        theirs = want[f]
        if not nested:
            assert mine == theirs, (
                "%s: the run lasted %r ticks and should have lasted %d.\n  aim: %s"
                % (name, mine, theirs, aim))
            continue
        assert mine is not None, "%s: %s is not a list of records" % (name, f)
        assert mine == theirs, (
            "%s: %s differs.\n  aim: %s\n  %s"
            % (name, {"trace": "the schedule", "prio": "what tasks were worth",
                      "ev": "the lifecycle log", "done": "the completion ticks",
                      "ids": "the task set"}.get(f, f),
               aim, first_gap(mine, theirs)))


def test_ground_truth_present():
    assert isinstance(GT, dict) and GT.get("scenarios"), "ground truth missing"
    assert isinstance(BASE, dict) and BASE.get("limit"), "scheduler settings missing"
    assert set(GT["scenarios"]) == set(FIXED), "ground truth does not cover the scenario set"


def test_run_completed():
    """Every scenario has to run. A crash is a failure, not a skipped case."""
    assert isinstance(RUN, dict), "no usable run output at %s" % OUT_PATH
    if NONCE:
        assert RUN.get("nonce") == NONCE, "the graded output was not written by this run"
    broke = RUN.get("broke") or {}
    assert not broke, "the scheduler raised in: %s" % ", ".join(sorted(broke))
    runs = RUN.get("runs")
    assert isinstance(runs, dict), "the run reported nothing"
    assert DRAWN, "the run did not report the seed it was given"
    missing = sorted(set(FIXED + DRAWN_NAMES) - set(runs))
    assert not missing, "not every scenario reported: missing %s" % missing


@pytest.mark.parametrize("name", FIXED)
def test_recorded_truth_still_holds(name):
    """The stored schedule still matches the sealed model.

    This grades nothing the agent did. It proves the schedules the other tests compare against
    are what the published semantics produce, and not an artifact of how the reference policy
    happened to be written.
    """
    sc = scen.by_name(name)
    want = oracle.expect(cfg_for(sc), sc)
    for f in FIELDS:
        assert want[f] == GT["scenarios"][name][f], (
            "stored ground truth for %s disagrees with the sealed model on %s" % (name, f))


@pytest.mark.parametrize("name", FIXED)
def test_written_scenarios(name):
    """The schedule, what every task was worth, the lifecycle log and the finish times."""
    compare(name, got(name), GT["scenarios"][name], AIM[name])


@pytest.mark.parametrize("case", DRAWN, ids=DRAWN_NAMES or ["none"])
def test_drawn_scenarios(case):
    """The same, on task sets that did not exist when the submission was written.

    The seed comes in at run time, so these cannot be answered from a table, and their expected
    schedules are computed here by the sealed model rather than read from a file. A policy that
    is right about the shapes somebody thought to write down and wrong in general fails here.
    """
    want = oracle.expect(cfg_for(case), case)
    compare(case["name"], got(case["name"]), want, case["aim"])


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def tree(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".pyc"):
                continue
            full = os.path.join(base, f)
            out[os.path.relpath(full, root).replace(os.sep, "/")] = sha(full)
    return out


@pytest.mark.parametrize("name", FIXED[:3])
def test_scheduler_was_not_replaced(name):
    """The scheduler that produced the schedule is the scheduler that shipped.

    Hashing the tree catches a policy that rewrites rt/core.py on disk. This catches the one
    that leaves the file alone and rebinds the function, which is the cheaper way to make the
    trace say whatever you want. The run fingerprints the scheduler twice, once as loaded and
    once when the scenario is over, and the grader works out what those have to be by compiling
    the pristine sources - nothing is executed to do it.
    """
    if not os.path.isdir(PRISTINE_DIR):
        pytest.skip("no pristine tree to attest against")
    want = oracle.expected_fingerprints(PRISTINE_DIR)
    assert want, "no sealed functions could be compiled from the pristine tree"
    rep = got(name)
    assert rep is not None, "%s: no report" % name
    for when in ("fp", "fp_end"):
        seen = rep.get(when)
        assert isinstance(seen, dict), "%s: the run recorded no fingerprints" % name
        wrong = sorted(k for k, v in want.items() if seen.get(k) != v)
        assert not wrong, (
            "%s: these scheduler functions are not the ones that shipped (%s): %s"
            % (name, "as loaded" if when == "fp" else "after the run", ", ".join(wrong)))


def test_executed_tree_was_the_shipped_tree():
    """Everything outside the one editable file is byte identical after the run."""
    if not os.path.isdir(APP_DIR) or not os.path.isdir(PRISTINE_DIR):
        pytest.skip("no executed tree to attest")
    ran = tree(APP_DIR)
    want = tree(PRISTINE_DIR)
    for rel in ARTIFACTS:
        supplied = os.path.join(ARTIFACT_DIR, rel)
        if os.path.isfile(supplied):
            want[rel] = sha(supplied)
    assert set(ran) == set(want), (
        "the executed tree gained or lost files: added %s, missing %s"
        % (sorted(set(ran) - set(want)), sorted(set(want) - set(ran))))
    moved = sorted(r for r in want if ran[r] != want[r])
    assert not moved, "the executed tree was modified during the run: %s" % moved


def test_settings_match_the_shipped_settings():
    """The settings the verifier grades against are the ones the scheduler was handed."""
    shipped = os.path.join(PRISTINE_DIR, "conf", "sched.json")
    if not os.path.isfile(shipped):
        pytest.skip("no pristine settings to compare")
    assert read(shipped) == BASE, "the sealed scheduler settings are not the shipped ones"
