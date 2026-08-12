"""Verifier for the checkpoint resume drift task.

What the run produced is in /work/out.json, written by /tests/runner.py, which is the only
process that executed anything the agent wrote.  Nothing in this file imports, execs or
subprocesses agent code: it reads that JSON as hostile input and grades it against
/tests/gt.json, which is root-only and was never visible to the run.

Three independent things are checked, and all of them must hold:

  1. The state the run ends on.  The parameter vector, the shadow average and the step
     counter must equal the ground truth, and the ground truth is re-proved here by the
     sealed generator in oracle.py, which shares no code with the tree and implements the
     lifecycle from scratch.  On top of that, test_resume_matches_a_run_that_never_died
     re-proves the property the whole task is about: the same op list with the down time
     compacted out - the rolled-back interval deleted, the amendments that landed in it
     kept - ends on the same parameters.  A resume that reseeded the per-row stream,
     restarted the epoch, or dropped the item the packer was holding cannot match a run
     that never checkpointed at all.

  2. The work.  reads is counted inside data/store.py, pos inside train/model.py and upd
     inside train/opt.py, none of which the agent may edit, so these measure real work
     whatever the submitted implementation looks like.  Reconstructing state by replaying
     the stream produces the right parameters and the wrong number of reads.

     Deliberately NOT graded: how many slots the checkpoint used and in what order, which
     holders it names, how the vector is framed.  Any encoding the bounded channel accepts
     is as good as any other, and grading one would make a correct solution guess at a
     layout the task never asked for.  draws is not graded either: a solution that puts
     the held item back by rewinding the cursor and letting the sampler hand it out again
     asks the sampler one more time for the same sample, which is bookkeeping rather than
     work.  loads and saves are not graded because the driver counts them and no
     implementation can move them.

  3. The trace.  The per-microbatch and per-update record the loop writes itself, in
     order, which pins where every window opened and closed and what the schedule handed
     it - including across an amendment taken while the trainer was down.

Per-scenario notes on which reading of the rule each case is aimed at are in scen.py and
are quoted in the failure messages.
"""

import json
import os

import pytest

import oracle
import scen

OUT_PATH = os.environ.get("RUN_OUT", "/work/out.json")
GT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gt.json")
CONF_PATH = os.environ.get("CONF_JSON", "/tests/train.json")

NAMES = [s["name"] for s in scen.SCENARIOS]
AIM = {s["name"]: s["aim"] for s in scen.SCENARIOS}

STATE = ("p", "ema", "step")
WORK = ("reads", "pos", "upd")


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


def cfg_for(name):
    """The configuration a scenario starts from: the shipped one plus its overrides."""
    cfg = json.loads(json.dumps(BASE))
    for k, v in (scen.by_name(name).get("over") or {}).items():
        if k == "sched":
            for a, b in v.items():
                cfg["sched"][a] = b
        else:
            cfg[k] = v
    return cfg


def test_ground_truth_present():
    assert isinstance(GT, dict) and GT.get("scenarios"), "ground truth missing"
    assert isinstance(BASE, dict) and BASE.get("sched"), "trainer config missing"
    assert set(GT["scenarios"]) == set(NAMES), "ground truth does not cover the scenario set"


def test_run_completed():
    """The trainer has to survive every scenario.

    A crash counts as a failure, and the commonest crash here is a checkpoint the channel
    refuses: the payload is a bounded vector of integers, and a submission that tries to
    carry the sample order or the token table exceeds it.
    """
    assert isinstance(RUN, dict), "no usable run output at %s" % OUT_PATH
    errs = RUN.get("errors") or {}
    assert not errs, "trainer raised in: %s" % ", ".join(sorted(errs))
    assert set((RUN.get("reports") or {})) == set(NAMES), "not every scenario reported"


@pytest.mark.parametrize("name", NAMES)
def test_ground_truth_is_reproduced_by_the_sealed_trainer(name):
    """Re-prove every graded field without the tree.

    oracle.py is a second implementation of the same arithmetic and the same lifecycle,
    written from scratch. If it disagrees with the recorded ground truth, the ground truth
    is what is wrong, and no submission should be graded against it.
    """
    want = expected(name)
    fresh = oracle.run(cfg_for(name), scen.by_name(name)["ops"])
    for field in STATE + WORK + ("trace",):
        assert fresh[field] == want[field], (
            "%s: ground truth for %s does not match the sealed trainer" % (name, field))


@pytest.mark.parametrize("name", NAMES)
def test_resume_matches_a_run_that_never_died(name):
    """The property the task is defined by, checked against a run with no checkpoint.

    The op list is compacted: the interval the load rolled back is deleted and the
    amendments that landed in it are kept, since the configuration lives with whoever
    relaunches the trainer rather than in the checkpoint. Running that list straight
    through never saves and never loads. It has to end where the ground truth ends.
    """
    cfg = cfg_for(name)
    ops = scen.by_name(name)["ops"]
    comp = oracle.run(cfg, oracle.compact(ops))
    want = expected(name)
    for field in STATE:
        assert comp[field] == want[field], (
            "%s: the ground truth's %s is not what an uninterrupted run reaches (%s)"
            % (name, field, AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_state(name):
    """Where the run ended: parameters, shadow average, step counter."""
    rep = report(name)
    assert rep is not None, "no report for %s (%s)" % (name, AIM[name])
    want = expected(name)
    for field in STATE:
        assert rep.get(field) == want[field], (
            "%s: %s was %r, expected %r (%s)"
            % (name, field, rep.get(field), want[field], AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_work_done(name):
    """Exact accounting of the work the run actually cost.

    reads is bumped in data/store.py, pos in train/model.py, upd in train/opt.py, all
    outside the files the agent may edit. A resume that rebuilds its position by replaying
    the stream reaches the right parameters and reads the store far more times than the
    run it is continuing ever did.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    want = expected(name)
    for field in WORK:
        assert rep.get(field) == want[field], (
            "%s: %s was %r, expected %r (%s)"
            % (name, field, rep.get(field), want[field], AIM[name]))


@pytest.mark.parametrize("name", NAMES)
def test_trace(name):
    """The loop's own record of every microbatch and every update, in order."""
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    got = [str(e) for e in (rep.get("trace") or [])]
    want = list(expected(name)["trace"])
    assert got == want, (
        "%s: trace diverged at entry %d (%s)\n got %r\nwant %r"
        % (name, next((i for i, (a, b) in enumerate(zip(got, want)) if a != b), len(want)),
           AIM[name], got[:60], want[:60]))


@pytest.mark.parametrize("name", NAMES)
def test_counters_agree_with_each_other(name):
    """Three counters for overlapping quantities, incremented in three modules.

    pos is bumped inside the model's backward pass; the loop writes the same token count
    into its own trace; the sampler counts draws and the store counts reads, and the store
    is read once per placement, which is at least once per draw. An honest run cannot
    separate them. A report whose numbers were written rather than earned generally can.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    rows = [str(e) for e in (rep.get("trace") or []) if str(e).startswith("m:")]
    tok = 0
    for e in rows:
        parts = e.split(":")
        assert len(parts) == 4 and parts[3].lstrip("-").isdigit(), (
            "%s: malformed microbatch entry %r" % (name, e))
        tok += int(parts[3])
    assert rep.get("pos") == tok, (
        "%s: the model counted %r positions, the loop's trace accounts for %r"
        % (name, rep.get("pos"), tok))
    draws, reads = rep.get("draws"), rep.get("reads")
    assert isinstance(draws, int) and isinstance(reads, int), "%s: counters are not counts" % name
    assert 0 < draws <= reads, (
        "%s: %r draws against %r reads; every sample placed is read at least once"
        % (name, draws, reads))
