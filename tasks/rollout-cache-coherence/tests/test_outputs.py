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

  2. The work.  computed / reused / preempt, and the position count taken inside the
     backend, must equal the ground truth exactly.  This is the side that fails an engine
     which is merely safe: dropping the cache on every push, keying blocks on the adapter,
     treating a copy-out-and-back offload as destructive, or clearing the half-built prefix
     of a request that has emitted nothing when the push could not have moved what that
     prefix holds - all produce correct tokens and the wrong amount of work.

     Deliberately NOT graded, in two places:

     How many index entries were retired, and when.  Retiring a stale entry as soon as its
     fingerprint is superseded and leaving it for the least-recently-used sweep are both
     correct and cost the same key/value work.

     The work counters of any scenario that runs the pool dry.  Once requests are being
     thrown off the pool, the totals depend on which of several equally old blocks the
     sweep picks, and two faithful implementations of the same policy disagree there - an
     ordered-dict least-recently-used index and a tick-counter one produce different
     preemption counts on identical semantics.  Grading that made a correct solution
     reverse-engineer a hidden constant, so scenarios that preempt are graded on tokens
     and rewinds alone, neither of which eviction order can move.  ORDER_FREE below is
     derived from the ground truth rather than hand listed, so a scenario that starts
     preempting drops out of counter grading by itself.

     Eviction on its own is not that regime and is graded.  A pool under pressure but
     never exhausted forces the same evictions in the same order whatever the index is
     built on, which is what lets the spill-* scenarios measure the second holder at all;
     authoring/variant_check.py is the evidence, with two different least-recently-used
     containers agreeing exactly on those three scenarios.

  3. The lifecycle.  The set of rewound samples must be exactly right - no sample left
     straddling a push, none rewound that did not need it - and the engine's own
     start / finish / preempt trace must match in order.

     Not graded here either: how many times a request is admitted.  A rewound sample goes
     back to the queue and is picked up again, and whether that second pickup counts as a
     fresh admission is bookkeeping, not work.  A submission that clears the started flag
     when it rewinds - which the instruction's "submitted fresh" invites - raises a second
     admission event for the same request, having recomputed exactly as much as one that
     does not.  Repeated admissions of the same request are therefore collapsed on both
     sides before the order is compared, so what is checked is the order requests were
     first admitted, finished and preempted in.  The recompute those rewinds cost is
     already measured by computed / reused / pos, and the rewinds themselves by the
     restart events below.

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

COUNTERS = ("computed", "reused", "restart", "preempt", "pos")

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
    "prefill-relevant": "a push upstream of a key/value projection lands on one request "
                        "that has emitted tokens and one that is part way through its "
                        "prompt: the first is rewound, the second loses the prefix it "
                        "built and rebuilds it",
    "prefill-neutral": "the same two requests under a push that cannot move a key or "
                       "value: the one emitting tokens is rewound, the one part way "
                       "through its prompt keeps every position it has computed",
    "prefill-adapter": "a push into one adapter takes down only that adapter's half-built "
                       "prefix, then a base push that moves nothing a block depends on "
                       "must leave the rebuilt one alone",
    "spill-neutral": "a prompt whose blocks were evicted and kept, then a push that "
                     "cannot move a key or value: what the engine still holds is still "
                     "good and must be served rather than rebuilt",
    "spill-relevant": "the same shape under a push upstream of a key/value projection: "
                      "the block a later request asks for is a different block, and the "
                      "work has to be done again",
    "spill-discard": "both offload levels across a prompt whose blocks were evicted and "
                     "kept: a cycle that never touched what the engine still holds must "
                     "not cost a recompute",
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


def order_free(name):
    """True when the counters cannot depend on which block a sweep happened to pick.

    Preemption is the hazard the run audit found: once the pool is dry enough that
    requests are thrown off it, which of several equally old blocks goes first decides how
    much is recomputed, and two faithful implementations of one policy disagree.  A
    scenario that evicts without ever preempting is not in that regime - the pool is under
    pressure but never exhausted, every eviction is forced by the same allocation in the
    same order, and the totals are fixed by the policy rather than by the container the
    index is built on.  authoring/variant_check.py holds the evidence: an ordered-dict
    index and a tick-counter index produce identical computed / reused / pos on the
    scenarios kept here, and diverge on the ones dropped.
    """
    return expected(name)["preempt"] == 0


ORDER_FREE = [n for n in NAMES if GT and order_free(n)]


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
    assert rep is not None, "no report for %s (%s)" % (name, AIM.get(name, name))
    got = rep.get("out")
    assert isinstance(got, dict), "report for %s has no output map" % name
    want = expected(name)["out"]
    assert set(got) == set(want), "%s: wrong request set" % name
    for rid in sorted(want):
        assert list(got[rid]) == list(want[rid]), (
            "%s: request %s produced %r, expected %r (%s)"
            % (name, rid, got[rid], want[rid], AIM.get(name, name)))


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


@pytest.mark.parametrize("name", ORDER_FREE)
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
    for field in ("computed", "reused", "pos", "preempt"):
        assert rep.get(field) == want[field], (
            "%s: %s was %r, expected %r (%s)"
            % (name, field, rep.get(field), want[field], AIM.get(name, name)))


@pytest.mark.parametrize("name", NAMES)
def test_counters_agree_with_each_other(name):
    """Two counters for the same quantity, incremented in two different modules.

    computed is bumped in the engine facade, pos inside the backend's forward pass, and
    both live outside the files the agent may edit. An honest run cannot separate them.
    A report whose numbers were written rather than earned generally can.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    assert rep.get("computed") == rep.get("pos"), (
        "%s: engine counted %r computed positions, the backend counted %r forward passes"
        % (name, rep.get("computed"), rep.get("pos")))
    assert isinstance(rep.get("reused"), int) and rep["reused"] >= 0, (
        "%s: reused is not a count" % name)


@pytest.mark.parametrize("name", NAMES)
def test_rewinds(name):
    """The set of rewound samples, not just how many."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    want = expected(name)
    assert rep.get("restart") == want["restart"], (
        "%s: %r samples rewound, expected %r (%s)"
        % (name, rep.get("restart"), want["restart"], AIM.get(name, name)))
    got_ev = [e for e in (rep.get("trace") or []) if str(e).startswith("restart:")]
    want_ev = [e for e in want["trace"] if e.startswith("restart:")]
    assert sorted(got_ev) == sorted(want_ev), (
        "%s: rewound %r, expected %r" % (name, sorted(got_ev), sorted(want_ev)))


def lifecycle(events):
    """The engine's own start / finish / preempt events, with repeat admissions dropped.

    A request that was rewound or preempted goes back on the queue and is picked up again.
    Whether the engine treats that pickup as a fresh admission is an implementation choice
    that costs no key/value work, so only the first admission of each request is kept.
    Completions and preemptions are left alone: those the engine raises itself.
    """
    keep = ("start:", "finish:", "preempt:")
    seen = set()
    out = []
    for ev in events:
        ev = str(ev)
        if not ev.startswith(keep):
            continue
        if ev.startswith("start:"):
            if ev in seen:
                continue
            seen.add(ev)
        out.append(ev)
    return out


@pytest.mark.parametrize("name", ORDER_FREE)
def test_engine_trace(name):
    """Admission, completion and preemption order, as recorded by the engine itself."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    got = lifecycle(rep.get("trace") or [])
    want = lifecycle(expected(name)["trace"])
    assert got == want, "%s: engine trace diverged\n got %r\nwant %r" % (name, got, want)
