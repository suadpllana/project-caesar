"""Verifier for the rollout cache coherence task.

What the run produced is in /work/out.json, written by /tests/runner.py, which is the
only process that executed anything the agent wrote.  Nothing in this file imports,
execs or subprocesses agent code: it reads that JSON as hostile input and grades it
against /tests/gt.json, which is root-only and was never visible to the run.

Three independent things are checked, and all of them must hold:

  1. The tokens.  Every request's stream must equal the ground truth, and the ground
     truth is itself re-proved here by the sealed generator in oracle.py, which shares
     no code with the tree and recomputes each stream from scratch under one parameter
     snapshot.  A stream that mixed two policies, or that was assembled from key/value
     projections computed under earlier parameters, cannot match.

  2. The work.  computed / reused / preempt / evict, and the position count taken inside
     the backend, must equal the ground truth exactly.  This is the side that fails an
     engine which is merely safe: dropping the cache on every push, keying blocks on the
     adapter, or treating a copy-out-and-back offload as destructive all produce correct
     tokens and the wrong amount of work.

  3. The lifecycle.  The set of rewound samples must be exactly right - no sample left
     straddling a push, none rewound that did not need it - and the engine's own
     start / finish / preempt trace must match in order.

Per-scenario notes on which mistake each case is aimed at are on the assertions below.
"""

import json
import os

import pytest

import oracle
import scen

OUT_PATH = os.environ.get("RUN_OUT", "/work/out.json")
GT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gt.json")
CONF_PATH = os.environ.get("CONF_JSON", "/tests/engine.json")

COUNTERS = ("computed", "reused", "restart", "preempt", "evict", "pos")

NAMES = [s["name"] for s in scen.SCENARIOS]

# What each scenario is aimed at. Kept next to the data so a failure report says which
# reading of the rule broke, not just which numbers moved.
AIM = {
    "group": "plain prefix sharing inside one rollout group, no pushes involved",
    "neutral-base": "a push that cannot move any key or value: samples in flight are "
                    "still from the old policy and must be rewound, but every cached "
                    "block stays valid",
    "relevant-base": "a push upstream of a key/value projection: blocks and samples "
                     "both go",
    "tied-push": "a push addressed at a module that shares storage with an earlier "
                 "layer, so the harmless-looking target is not harmless",
    "adapter-share": "adapters whose deltas sit downstream of the last key/value write "
                     "must share one prompt's blocks with the base policy",
    "adapter-push": "a push into one adapter must not disturb the blocks or the samples "
                    "of the base policy or of another adapter",
    "adapter-neutral-push": "a push into an adapter that cannot move keys or values: "
                            "rewind its sample, keep its blocks",
    "replayed-push": "a push that lands the values already loaded invalidates nothing "
                     "and rewinds nothing",
    "offload-cycle": "a copy-out-and-back offload preserves the cache; a discarding one "
                     "does not, and neither may change a single token",
    "pressure": "eviction and preemption interleaved with a push",
    "mixed": "everything at once, over a long op list",
}


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


GT = load_json(GT_PATH)
RUN = load_json(OUT_PATH)
CONF = load_json(CONF_PATH)


def report(name):
    """The run's report for one scenario, or None if the run did not produce a usable one."""
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
    return GT["scenarios"][name]["report"]


def test_ground_truth_present():
    assert isinstance(GT, dict) and GT.get("scenarios"), "ground truth missing"
    assert isinstance(CONF, dict) and CONF.get("seeds"), "engine config missing"
    assert set(GT["scenarios"]) == set(NAMES), "ground truth does not cover the scenario set"


def test_run_completed():
    """The engine has to survive every scenario; a crash or a hang is a failed run."""
    assert isinstance(RUN, dict), "no usable run output at %s" % OUT_PATH
    errs = RUN.get("errors") or {}
    assert not errs, "engine raised in: %s" % ", ".join(sorted(errs))
    assert set((RUN.get("reports") or {})) == set(NAMES), "not every scenario reported"


@pytest.mark.parametrize("name", NAMES)
def test_tokens(name):
    """Every sample must be token-identical to the ground truth stream."""
    rep = report(name)
    assert rep is not None, "no report for %s (%s)" % (name, AIM[name])
    got = rep.get("out")
    assert isinstance(got, dict), "report for %s has no output map" % name
    want = expected(name)["out"]
    assert set(got) == set(want), "%s: wrong request set" % name
    for rid in sorted(want):
        assert list(got[rid]) == list(want[rid]), (
            "%s: request %s produced %r, expected %r (%s)"
            % (name, rid, got[rid], want[rid], AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_ground_truth_streams_are_single_policy(name):
    """Re-prove the expected streams without the engine.

    For each request the sealed generator reproduces the expected tokens from scratch,
    with no cache and no scheduler, under one of the parameter snapshots the scenario
    passes through. This is what makes the token check above meaningful: the target is
    a real single-policy sample, not whatever the reference implementation happened to
    emit.
    """
    sc = scen.by_name(name)
    snaps = oracle.snapshots(CONF["seeds"], CONF["adapters"], sc["ops"])
    want = expected(name)["out"]
    recorded = GT["scenarios"][name]["snap"]
    for op in sc["ops"]:
        if op["op"] != "add":
            continue
        rid = op["rid"]
        idx = recorded[rid][0]
        seeds, ad = snaps[idx]
        deltas = ad.get(op.get("adapter"), {}) if op.get("adapter") else {}
        fresh = oracle.generate(seeds, deltas, rid, op["prompt"], op["max_new"])
        assert fresh == list(want[rid]), (
            "%s: ground truth for %s is not a fresh single-policy sample" % (name, rid))


@pytest.mark.parametrize("name", NAMES)
def test_work_done(name):
    """Exact accounting.

    computed and reused are incremented in the engine facade, pos inside the backend -
    all outside the files the agent may edit - so these numbers measure real key/value
    work whatever the submitted implementation looks like. An engine that keeps stale
    blocks computes too little; one that drops blocks it did not have to computes too
    much. Both are failures.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    want = expected(name)
    for field in ("computed", "reused", "pos", "preempt", "evict"):
        assert rep.get(field) == want[field], (
            "%s: %s was %r, expected %r (%s)"
            % (name, field, rep.get(field), want[field], AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_rewinds(name):
    """The set of rewound samples, not just how many."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    want = expected(name)
    assert rep.get("restart") == want["restart"], (
        "%s: %r samples rewound, expected %r (%s)"
        % (name, rep.get("restart"), want["restart"], AIM[name]))
    got_ev = [e for e in (rep.get("trace") or []) if str(e).startswith("restart:")]
    want_ev = [e for e in want["trace"] if e.startswith("restart:")]
    assert sorted(got_ev) == sorted(want_ev), (
        "%s: rewound %r, expected %r" % (name, sorted(got_ev), sorted(want_ev)))


@pytest.mark.parametrize("name", NAMES)
def test_engine_trace(name):
    """Admission, completion and preemption order, as recorded by the engine itself."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    keep = ("start:", "finish:", "preempt:")
    got = [e for e in (rep.get("trace") or []) if str(e).startswith(keep)]
    want = [e for e in expected(name)["trace"] if e.startswith(keep)]
    assert got == want, "%s: engine trace diverged\n got %r\nwant %r" % (name, got, want)
