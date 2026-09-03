"""The graded decision, as rows of integers a solver can read at that moment, plus the label.

The decision the server makes after every token is how many bytes of the response it may now put
on the wire. The features below are what the shipped tree already hands it: the length of the raw
stream, what the stream renders to if nothing more arrives, where the first opener still waiting
for a closer sits, how long the stops are, and whether one of them already matches. If a rule over
those reproduces the label, the answer is short enough to write cold.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stage

SNIP = """
import json, sys
sys.path.insert(0, %r)
import cases, gen
from srv import look, bite, hold, wire
rows = []
jobs = list(cases.jobs()) + gen.jobs('decisions', 120)
for name, job in jobs:
    stops = job['stops']
    wide = max(len(s) for s in stops)
    cur, at, raw = 's0', 0, b''
    st = wire.St(stops)
    for _ in range(400):
        if at >= len(job['scripts'][cur]):
            break
        raw += job['scripts'][cur][at]
        at += 1
        st.raw = raw
        st.ended = False
        vis, inert = look.read(raw)
        text, tin, hit = bite.chop(vis, inert, stops)
        openat = -1
        i = 0
        while i < len(raw):
            ja, jq = raw.find(b'<~', i), raw.find(b'<#', i)
            opts = [(j, o, c) for j, o, c in ((ja, b'<~', b'~>'), (jq, b'<#', b'#>')) if j >= 0]
            if not opts:
                break
            j, o, c = min(opts)
            k = raw.find(c, j + 2)
            if k < 0:
                openat = j
                break
            i = k + len(c)
        sent, fin = hold.ready(st)
        rows.append({
            'f': [len(raw), len(vis), len(text), int(hit), wide, openat,
                  int(raw.endswith(b'<')), sum(inert), len(stops)],
            'label': len(sent),
            'fin': int(fin),
        })
print(json.dumps(rows))
"""


def samples():
    """Two graded questions: how many bytes go out now, and whether the response is over."""
    app = stage.reference()
    rows = json.loads(stage.drive_in(app, SNIP % stage.TESTS))
    return {
        "release-length": [(r["f"], r["label"]) for r in rows],
        "declared-over": [(r["f"], r["fin"]) for r in rows],
    }


NAMES = ["rawlen", "vislen", "choplen", "hit", "widest", "openat", "trail", "inert", "nstops"]

if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%-16s %d samples, %d features" % (name, len(rows), len(rows[0][0])))
