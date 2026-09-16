"""Unprivileged worker: run the submitted planner and report what it printed.

This process is the only one that imports anything the agent wrote. It runs as
an unprivileged uid, in its own session, under a hard wall clock, with the
answers (gt.json and tests/seal/) unreadable to it. It computes no verdict: it
writes traces into a descriptor root opened for it and exits. Everything that
decides the reward happens later, in a process this one cannot reach.

    python runner.py fd:<n>
    python runner.py <path>
"""

import json
import os
import sys


def target(spec):
    if spec.startswith("fd:"):
        return os.fdopen(int(spec[3:]), "w")
    return open(spec, "w", newline="\n")


def main():
    out = target(sys.argv[1])
    app = os.environ.get("APPDIR", "/work/app")
    nonce = os.environ["RUN_NONCE"]
    per = int(os.environ.get("RUN_COUNT", "50"))
    sys.path.insert(0, app)
    sys.path.insert(0, "/tests")

    import cases
    import gen
    from sked import emit, lane, read, rec

    # Attestation: every printed line must come from a record the frozen type
    # made, so a planner that hands back ready-made strings is visible here.
    made = [0]
    born = rec.Ev.__init__

    def counted(self, *a, **kw):
        made[0] += 1
        return born(self, *a, **kw)

    rec.Ev.__init__ = counted

    report = {"nonce": nonce, "per": per, "cases": {}, "gen": {}, "fault": {}}
    work = [("cases", list(cases.PLANS)), ("gen", gen.plans(nonce, per))]
    total = 0
    for bucket, plans in work:
        for name, text in plans:
            try:
                got = emit.lines(lane.run(read.parse(text)))
                if not isinstance(got, list) or not all(isinstance(x, str) for x in got):
                    raise TypeError("trace is not a list of strings")
            except Exception as exc:
                report["fault"][name] = "%s: %s" % (type(exc).__name__, exc)
                got = []
            report[bucket][name] = got
            total += len(got)
    report["made"] = made[0]
    report["lines"] = total
    json.dump(report, out)
    out.flush()
    out.close()


main()
