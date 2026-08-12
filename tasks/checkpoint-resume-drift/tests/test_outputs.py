"""Verifier for the checkpoint resume drift task.

What the run produced is in /work/out.json, written by /tests/runner.py, which supervises
the trainer without ever executing any of it: every scenario's trainer is a child process,
unprivileged and in its own session, and the counters and the trace in that file are the
supervisor's own record of what its service was asked to do.  Nothing in this file
imports, execs or subprocesses agent code: it reads that JSON as hostile input and grades
it against /tests/gt.json, which is root-only and was never visible to the run.

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

  2. The work.  reads, pos and upd are counted by the supervisor's service, in the
     process that spawned the trainer rather than in the trainer, so they are what the
     service was asked for and not what the trainer said about itself.  The corpus comes
     from that service too, generated from a seed the trainer never sees and which is not
     the seed shipped in the tree, so a sample's tokens cannot be produced without asking
     for them and every ask is charged.  Reconstructing state by replaying the stream
     produces the right parameters and the wrong number of reads.

     Deliberately NOT graded: how many slots the checkpoint used and in what order, which
     holders it names, how the vector is framed.  Any encoding the bounded channel accepts
     is as good as any other, and grading one would make a correct solution guess at a
     layout the task never asked for.  draws is not graded either: a solution that puts
     the held item back by rewinding the cursor and letting the sampler hand it out again
     asks the sampler one more time for the same sample, which is bookkeeping rather than
     work.  loads and saves are not graded because the driver counts them and no
     implementation can move them.

  3. The trace.  Written by the supervisor from the requests it served, in order, which
     pins where every window opened and closed and what the schedule handed it - including
     across an amendment taken while the trainer was down.  A microbatch entry is only
     written when the row count and token count the loop announces match the gradients the
     service actually computed for it.

  4. The lifecycle.  Every kill destroyed a process and every load started another one, so
     the checkpoint vector is the only thing that crossed.

Per-scenario notes on which reading of the rule each case is aimed at are in scen.py and
are quoted in the failure messages.
"""

import json
import os
import stat

import pytest

import oracle
import scen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.environ.get("RUN_OUT", "/work/out.json")
GT_PATH = os.path.join(HERE, "gt.json")
CONF_PATH = os.environ.get("CONF_JSON", "/tests/train.json")
CORPUS_PATH = os.environ.get("CORPUS", os.path.join(HERE, "corpus.json"))

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
DSEED = (load_json(CORPUS_PATH) or {}).get("dseed")


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
    assert isinstance(DSEED, int), "the graded corpus is missing"
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
    fresh = oracle.run(cfg_for(name), scen.by_name(name)["ops"], DSEED)
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
    comp = oracle.run(cfg, oracle.compact(ops), DSEED)
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

    Every one of these is a tally the supervisor kept while serving the trainer: a read is
    a sample the service handed over, a position is a position the gradient kernel was
    given, an update is an optimiser step it applied. None of them is reported by the
    trainer, so none of them can be reset, suppressed or written. A resume that rebuilds
    its position by replaying the stream reaches the right parameters and asks the service
    for the corpus far more times than the run it is continuing ever did, and it has no
    way to get those samples without asking.
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
    """Counters for overlapping quantities, all of them the service's own tallies.

    pos is the positions the gradient kernel was handed; the microbatch entries account
    for the same tokens, because the supervisor refuses to write one that does not match
    the work it just did; upd is the number of optimiser steps it applied and there is one
    update entry per step; a sample is drawn at most as often as the corpus is read. An
    honest run cannot separate them, and a run that did the work somewhere the service
    cannot see it comes out short on every one of them at once.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    trace = [str(e) for e in (rep.get("trace") or [])]
    tok = 0
    for e in [x for x in trace if x.startswith("m:")]:
        parts = e.split(":")
        assert len(parts) == 4 and parts[3].lstrip("-").isdigit(), (
            "%s: malformed microbatch entry %r" % (name, e))
        tok += int(parts[3])
    assert rep.get("pos") == tok, (
        "%s: the service computed gradients over %r positions, the microbatch record "
        "accounts for %r" % (name, rep.get("pos"), tok))
    assert rep.get("upd") == len([x for x in trace if x.startswith("u:")]), (
        "%s: %r optimiser steps against %d update entries"
        % (name, rep.get("upd"), len([x for x in trace if x.startswith("u:")])))
    draws, reads = rep.get("draws"), rep.get("reads")
    assert isinstance(draws, int) and isinstance(reads, int), "%s: counters are not counts" % name
    assert 0 < draws <= reads, (
        "%s: %r draws against %r reads; every sample placed is read at least once"
        % (name, draws, reads))


@pytest.mark.parametrize("name", NAMES)
def test_every_load_started_a_new_process(name):
    """The kill is a kill.

    The trainer for each scenario runs in a child process the supervisor spawns. A kill
    signals that process group and reaps it, and the load that follows starts another one
    from nothing, so the only thing that reaches the resumed trainer is the vector the
    checkpoint channel accepted. This checks the supervisor's own record of that: one
    process to begin with, one more for every load, and no process id reused - which is
    what makes a module global, a cached corpus or an open file useless as a way to carry
    state across the interruption the task is about.
    """
    rep = report(name)
    assert rep is not None, "no report for %s" % name
    lives = rep.get("lives")
    loads = len([op for op in scen.by_name(name)["ops"] if op.get("op") == "load"])
    assert isinstance(lives, list) and all(isinstance(x, int) for x in lives), (
        "%s: the supervisor did not record which processes ran the trainer" % name)
    assert len(lives) == loads + 1, (
        "%s: %d trainer processes for %d loads (%s)" % (name, len(lives), loads, AIM[name]))
    assert len(set(lives)) == len(lives), "%s: a trainer process was reused" % name


def _writable_by_the_trainer():
    """Every path the trainer's uid could have written, outside the kernel filesystems.

    A checkpoint that fits in the channel is the point of the task, so a submission that
    parks its state somewhere else and posts a handle through the channel has answered a
    different question. Process death takes care of memory. This takes care of disk: the
    verifier closes every path the trainer's uid can write before the run, and the run is
    only graded if that actually held.
    """
    uid = 1002
    bad = []
    for root in ("/app", "/bin", "/etc", "/home", "/lib", "/logs", "/media", "/mnt",
                 "/opt", "/pristine", "/root", "/run", "/sbin", "/srv", "/tests", "/tmp",
                 "/usr", "/var", "/work", "/dev/shm"):
        if not os.path.isdir(root):
            continue
        for base, dirs, files in os.walk(root, onerror=lambda e: None):
            for name in [""] + dirs + files:
                path = os.path.join(base, name) if name else base
                try:
                    st = os.lstat(path)
                except OSError:
                    continue
                if stat.S_ISLNK(st.st_mode):
                    continue
                mode = st.st_mode
                if (mode & 0o002
                        or (st.st_uid == uid and mode & 0o200)
                        or (st.st_gid == uid and mode & 0o020)):
                    bad.append(path)
                    if len(bad) > 20:
                        return bad
    return bad


def test_the_trainer_had_nowhere_to_write():
    """The kill has to be the only thing that survives, and disk is the other way round it.

    This is a property of the verifier rather than of the submission, so it is checked
    directly instead of assumed: after the run, no file and no directory on the image is
    writable by the uid every trainer process ran as.
    """
    bad = _writable_by_the_trainer()
    assert not bad, "the trainer's uid could write: %s" % ", ".join(sorted(bad)[:20])
