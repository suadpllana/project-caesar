"""The graded decisions, as rows of numbers a solver could read at that moment.

`tools/onelinecheck.py` searches these for the shortest exact rule over the
fields the environment already exposes. A graded decision that a two-term
comparison reproduces is an answer a frontier model writes cold, whatever the
prose around it says, and that is an easiness rejection waiting to be measured
rather than argued about.

Three decisions, and the features are deliberately generous: everything a
submission can read off the state without doing the reasoning, including the
version numbers, which are exactly what the tempting wrong rule compares.

  gate-up      should this parcel go up against this shown map now
  cover-one    is this one line of a writer's picture covered
  entry-move   does this entry of a parcel move the shown map

The one that has to come back without a short rule is `gate-up`. If any of them
were reproducible at depth two, the fabric would be a lookup rather than a
question.
"""

import os
import shutil
import sys
import tempfile

import lab

PROBE = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from base import drv, tape, wire
from bay import cov, desc, stand

OUT = {"gate-up": [], "cover-one": [], "entry-move": []}
REAL_RIPE = stand.ripe
REAL_COVER = cov.covers


def _hi(st, ids):
    return max(ids) if ids else -1


def watched_ripe(st, p, view):
    got = REAL_RIPE(st, p, view)
    ent = p
    held = [len(wire.held(st, w)) for w in st.bag]
    row = {
        "entries": len(ent),
        "known": sum(1 for s in ent if s in view),
        "unknown": sum(1 for s in ent if s not in view),
        "topent": _hi(st, list(ent.values())),
        "topview": _hi(st, list(view.values())),
        "shown": len(view),
        "picture": max([len(st.vers[v].deps) for v in ent.values()] or [0]),
        "bag": max(held or [0]),
        "vers": len(st.vers),
        "parcels": len(st.parc),
        "step": st.step,
        "higher": sum(1 for s in ent if ent[s] > view.get(s, -1)),
        "lower": sum(1 for s in ent if s in view and ent[s] < view[s]),
    }
    OUT["gate-up"].append([row, bool(got)])
    return got


def watched_cover(st, deps, view, ent):
    got = REAL_COVER(st, deps, view, ent)
    for s in deps:
        v = deps[s]
        OUT["cover-one"].append([{
            "want": v,
            "haveview": view.get(s, -1),
            "haveent": ent.get(s, -1),
            "inview": 1 if s in view else 0,
            "inent": 1 if s in ent else 0,
            "gap": view.get(s, -1) - v,
            "parents": len(st.vers[v].base),
            "vers": len(st.vers),
        }, bool(got)])
    return got


stand.ripe = watched_ripe
cov.covers = watched_cover

for text in json.load(open(sys.argv[2])):
    drv.run(text, lambda row: None)

json.dump(OUT, open(sys.argv[3], "w"))
'''


def samples():
    feeds = lab.named()
    feeds.update(lab.made("decisions", 90))
    hold = tempfile.mkdtemp(prefix="pcg-dec-")
    try:
        where = lab.tree(os.path.join(hold, "ref"), lab.reference())
        import json
        import subprocess
        src = os.path.join(hold, "probe.py")
        inp = os.path.join(hold, "in.json")
        outp = os.path.join(hold, "out.json")
        with open(src, "w") as fh:
            fh.write(PROBE)
        with open(inp, "w") as fh:
            json.dump([feeds[n] for n in sorted(feeds)], fh)
        run = subprocess.run([sys.executable, src, where, inp, outp],
                             capture_output=True, text=True, timeout=900)
        if run.returncode != 0:
            raise RuntimeError(run.stderr[-600:])
        with open(outp) as fh:
            got = json.load(fh)
    finally:
        shutil.rmtree(hold, ignore_errors=True)
    out = {}
    for key in got:
        rows = got[key][:4000]
        out[key] = [(r[0], r[1]) for r in rows]
    move = []
    for row, label in out["gate-up"]:
        move.append(({"higher": row["higher"], "lower": row["lower"],
                      "unknown": row["unknown"], "entries": row["entries"],
                      "topent": row["topent"], "topview": row["topview"]}, label))
    out["entry-move"] = move
    return out
