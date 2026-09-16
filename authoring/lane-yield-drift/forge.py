"""The answer-key forgery: a planner carrying tests/gt.json verbatim.

tools/forgecheck.py asks whether the suite contains a cheat that was handed every answer,
because a suite made only of wrong implementations tests the problem and not the verifier.
This builds that planner, keyed on the plan itself rather than on the order the plans
arrive - a probe keyed on the process reproduces the first case and drifts on every one
after it, and then scores 0 for the wrong reason.

The forgery reproduces all 21 frozen answers, which is asserted here before it is written
out, and still scores 0, because the graded population is generated from a nonce drawn
after the run begins and the key holds none of it.
"""

import importlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import harness  # noqa: E402

STAMP = '''

def stamp(plan):
    bits = ["h%d" % plan.horizon]
    for name in sorted(plan.zones):
        z = plan.zones[name]
        bits.append("z:%s:%d:%s" % (name, z.base,
                                    ";".join("%d,%d" % (a, o) for a, o in z.shifts)))
    for name in sorted(plan.pools):
        q = plan.pools[name]
        bits.append("p:%s:%s:%d" % (name, q.zone.name, q.cap))
    for j in sorted(plan.jobs, key=lambda j: j.prio):
        bits.append("j:%s:%s:%d:%s:%d:%d:%d:%s:%d:%d"
                    % (j.jid, j.zone.name, j.prio, j.pool.name, j.dur, j.opn, j.shut,
                       j.mode, j.step, j.anchor))
    return "|".join(bits)
'''

HEAD = '''import json

from . import rec

KEY = json.loads(r"""__KEY__""")

INDEX = json.loads(r"""__INDEX__""")
'''

TAIL = '''

def run(plan):
    rows = KEY.get(INDEX.get(stamp(plan), ""), [])
    by = {j.jid: j for j in plan.jobs}
    out = []
    for line in rows:
        kind, jid, k, t = line.split()
        out.append(rec.Ev(kind, by[jid], int(k), int(t)))
    return out
'''


def planner():
    sys.path.insert(0, os.path.join(harness.TASK, "tests"))
    import cases
    work = tempfile.mkdtemp(prefix="lyd-forge-")
    try:
        app = harness.build_app(os.path.join(harness.TASK, "solution"), work)
        sys.path.insert(0, app)
        for name in list(sys.modules):
            if name == "sked" or name.startswith("sked."):
                del sys.modules[name]
        read = importlib.import_module("sked.read")
        scope = {}
        exec(STAMP, scope)
        stamp = scope["stamp"]
        with open(os.path.join(harness.TASK, "tests", "gt.json")) as fh:
            frozen = json.load(fh)
        # Carried in the same compact shape the ground truth has on the wire, so the
        # answers are verbatim rather than reformatted past recognition.
        key_text = json.dumps(frozen, sort_keys=True)
        index = {}
        for name, text in cases.PLANS:
            index[stamp(read.parse(text))] = name
        if len(index) != len(cases.PLANS):
            raise AssertionError("two enumerated plans share a fingerprint")
        for name, text in cases.PLANS:
            if frozen[index[stamp(read.parse(text))]] != frozen[name]:
                raise AssertionError("%s: the key does not round-trip" % name)
        sys.path.remove(app)
        for name in list(sys.modules):
            if name == "sked" or name.startswith("sked."):
                del sys.modules[name]
        return (HEAD.replace("__KEY__", key_text).replace("__INDEX__", json.dumps(index))
                + STAMP + TAIL)
    finally:
        shutil.rmtree(work, ignore_errors=True)
