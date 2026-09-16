"""The graded decisions, as rows of features the agent can read off the plan.

tools/onelinecheck.py searches for the shortest exact rule over these. A task is at risk
when every graded quantity has one at depth two or less, because that is an answer a
frontier model writes without running anything. The features here are deliberately the raw
fields of the plan - priority, mode, duration, step, window, cap, how many jobs, whether
the zone moves, whether the pool's zone is the job's - because those are what the agent
actually sees; a feature like "is this instant inside the window" would be a derived truth
the task is about and would measure nothing.

Three quantities are scored, one per event the trace can carry:

  outcome   what became of an occurrence: 0 started, 1 skipped, 2 dropped
  wait      how long a started occurrence waited, in minutes, or -1 if it never started
  due_gap   how far the job's next occurrence is from this one, or -1 if it has none

    python3 tools/onelinecheck.py fix-dst-scheduler
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "fix-dst-scheduler")
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402


def features(job, k, jobs, nshift):
    return {
        "prio": job.prio,
        "follow": 1 if job.mode == "follow" else 0,
        "dur": job.dur,
        "step": job.step,
        "opn": job.opn,
        "shut": job.shut,
        "span": job.shut - job.opn,
        "cap": job.pool.cap,
        "njobs": len(jobs),
        "nshift": nshift,
        "zmoves": 1 if len(job.zone.starts) > 1 else 0,
        "pzsame": 1 if job.pool.zone is job.zone else 0,
        "k": k,
    }


def trace_one(text):
    """Run the sealed model with the occurrence bookkeeping exposed."""
    jobs, horizon = model.read(text)
    nom = {}
    got = {}

    born = model.Run.__init__

    def watched(self, job, k, n, dead):
        nom[(job.jid, k)] = n
        return born(self, job, k, n, dead)

    noted = model.Sim.note

    def recorded(self, kind, job, k, t):
        if kind == "skip":
            nom.setdefault((job.jid, k), t)
        if kind in ("start", "skip", "drop"):
            got[(job.jid, k)] = (kind, t)
        return noted(self, kind, job, k, t)

    model.Run.__init__ = watched
    model.Sim.note = recorded
    try:
        model.Sim(jobs, horizon).go()
    finally:
        model.Run.__init__ = born
        model.Sim.note = noted
    return jobs, nom, got


OUTCOME = {"start": 0, "skip": 1, "drop": 2}


def samples():
    plans = list(cases.PLANS) + gen.plans("decisions", 12)
    rows = {"outcome": [], "wait": [], "due_gap": []}
    for _name, text in plans:
        jobs, nom, got = trace_one(text)
        nshift = sum(len(j.zone.starts) - 1 for j in jobs)
        by = {j.jid: j for j in jobs}
        for (jid, k), (kind, t) in got.items():
            job = by[jid]
            row = features(job, k, jobs, nshift)
            rows["outcome"].append((row, OUTCOME[kind]))
            rows["wait"].append((dict(row), t - nom[(jid, k)] if kind == "start" else -1))
            nxt = nom.get((jid, k + 1))
            rows["due_gap"].append((dict(row), nxt - nom[(jid, k)] if nxt is not None else -1))
    return rows
