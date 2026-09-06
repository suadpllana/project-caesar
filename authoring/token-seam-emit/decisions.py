"""The graded decisions as integer features, for `tools/onelinecheck.py`.

The question this answers is not "is the task hard" but "is the answer short". If the
release point can be reproduced by one or two comparisons between quantities the agent can
already read off the state at that moment, then a frontier model writes the answer cold and
every rule in the brief is decoration.

So the features here are only what the runner actually hands the release module: the step
index, the floor, how much text exists, how much has already gone out, and the shape of the
request's stop set. Quantities that are the answer in disguise - where the earliest
occurrence starts, how long the live partial is - are deliberately absent, because those are
what a solver has to derive. Putting them in would measure nothing except that the answer
equals the answer.

Two decisions are reported per step, because they fail differently: how far the release
point moved, and whether the request ended.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "token-seam-emit"))

PROBE = r'''
import json, os, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import cases, gen
from strm import rel, fin, req
from strm.st import St
from tok import decode, vocab

rows = []


def walk(spec):
    floor, cap, stops, ids = spec
    s = St(floor, stops)
    ps = decode.Pcs()
    run = ids[:cap]
    for j, tid in enumerate(run):
        s.add(ps.step(tid))
        last = j + 1 == len(run)
        before = s.r
        i, d, r = rel.point(s)
        if not d:
            i, d, r = fin.end(s, tid, last, i)
        feats = [
            s.n,                                  # step index
            s.fl,                                 # the floor
            len(s.t),                             # bytes of text so far
            before,                               # bytes already released
            len(s.t) - before,                    # bytes standing unreleased
            len(s.ss),                            # how many stop strings
            max([len(x) for x in s.ss] + [0]),    # longest stop string
            min([len(x) for x in s.ss] + [0]),    # shortest stop string
            1 if tid in vocab.SP else 0,          # was this piece text-free
            1 if tid == vocab.EOS else 0,         # was this the end-of-stream piece
            1 if last else 0,                     # is this the cap
        ]
        rows.append({"f": feats, "released": i - before, "ended": 1 if d else 0})
        s.r = i
        if d:
            return


for nm, spec in cases.CASES:
    walk(spec)
for nm, spec in gen.make("decisions", %d):
    walk(spec)
print(json.dumps(rows))
'''


def _rows(count=120):
    work = tempfile.mkdtemp(prefix="tse-dec-")
    try:
        tree = os.path.join(work, "tree")
        shutil.copytree(os.path.join(TASK, "environment", "app_src"), tree)
        for f in sorted(os.listdir(os.path.join(TASK, "solution"))):
            if f.endswith(".py"):
                shutil.copy(os.path.join(TASK, "solution", f), os.path.join(tree, "strm", f))
        src = PROBE % (tree, os.path.join(TASK, "tests"), count)
        r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("decisions probe failed:\n%s" % r.stderr)
        import json
        return json.loads(r.stdout)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def samples():
    """`(features, label)` for each graded decision the reference makes.

    Two labelled questions share one feature set: how many bytes the step released, and
    whether the step ended the request.
    """
    data = _rows()
    out = {
        "released": [(row["f"], row["released"]) for row in data],
        "ended": [(row["f"], row["ended"]) for row in data],
    }
    return out


if __name__ == "__main__":
    got = samples()
    for name in sorted(got):
        labels = sorted({lab for _, lab in got[name]})
        print("%-9s %5d decisions, %d distinct labels"
              % (name, len(got[name]), len(labels)))
