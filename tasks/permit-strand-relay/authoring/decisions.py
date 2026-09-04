"""The graded decisions the reference makes, as rows of primitive features.

tools/onelinecheck.py reads this and looks for the shortest exact rule over the
features, which is the easiness probe asked mechanically: a decision a two-term
comparison reproduces is one a frontier model writes cold whatever the brief
says.

The features are what the book actually exposes at the moment the decision is
made - the rows offered, what the feed and the link have sent and drained, what
ceiling stands at each level, how long since anything was accepted, how long
since the feed was torn down. Nothing derived is included: what the producer has
been told is not a field anywhere, and putting it in would be measuring a rule
the environment does not hand over.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases
import gen
import harness

ROUNDS = 150

PROBE = r'''
import json, sys
sys.path.insert(0, %r)
from lnk.book import LINK, WINF, WINL
from lnk.mach import Mach
from lnk.rd import parse
from pol import adm, emit

CALLS = []
_verdict = adm.verdict
_plan = emit.plan


def verdict(st, bk, when, fd, rows):
    call = _verdict(st, bk, when, fd, rows)
    CALLS.append(["adm", {
        "rows": rows,
        "fsnt": bk.snt.get(fd, 0),
        "ftkn": bk.tkn.get(fd, 0),
        "fheld": bk.held(fd),
        "fpub": bk.pub.get(fd, 0),
        "lsnt": bk.lsnt,
        "ltkn": bk.ltkn,
        "lpub": bk.pub.get(LINK, 0),
        "since": (when - bk.shut[fd]) if bk.shut.get(fd) is not None else -1,
        "quiet": when - bk.last.get(fd, when),
    }, call])
    return call


def plan(st, bk, when):
    out = _plan(st, bk, when)
    fired = dict((row[0], row[2]) for row in out)
    for level in [LINK] + bk.open():
        seat = bk.pub.get(level)
        if seat is None:
            continue
        wide = WINL if level == LINK else WINF
        spent = bk.lsnt if level == LINK else bk.snt.get(level, 0)
        took = bk.ltkn if level == LINK else bk.tkn.get(level, 0)
        CALLS.append(["emit", {
            "seat": seat,
            "spent": spent,
            "took": took,
            "wide": wide,
            "held": 0 if level == LINK else bk.held(level),
            "quiet": 0 if level == LINK else when - bk.last.get(level, when),
        }, 1 if level in fired else 0])
    return out


adm.verdict = verdict
emit.plan = plan
for plan_blob in json.load(open(%r)):
    Mach(parse(json.dumps(plan_blob)), lambda row: None).run()
print(json.dumps(CALLS))
'''


def collect():
    import json
    import subprocess
    import tempfile
    tree = harness.tempo(os.path.join(ROOT, "solution"))
    try:
        streams = [cases.SETS[k] for k in sorted(cases.SETS)]
        streams += gen.batch(777, ROUNDS)
        tmp = tempfile.mkdtemp(prefix="dec-")
        jobs = os.path.join(tmp, "jobs.json")
        with open(jobs, "w", newline="\n") as fh:
            json.dump(streams, fh)
        script = os.path.join(tmp, "probe.py")
        with open(script, "w", newline="\n") as fh:
            fh.write(PROBE % (tree, jobs))
        got = subprocess.run([sys.executable, script], capture_output=True,
                             text=True, timeout=600)
        if got.returncode != 0:
            raise SystemExit(got.stderr[-1200:])
        return json.loads(got.stdout)
    finally:
        harness.clear(tree)


def samples():
    out = {"adm": [], "emit": []}
    for tag, feats, label in collect():
        out[tag].append((feats, label))
    return {"admit": out["adm"], "publish": out["emit"]}
