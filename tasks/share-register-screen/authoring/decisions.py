"""The graded decisions, as rows of integers a solver can read at the moment it decides.

tools/onelinecheck.py searches these for the shortest exact rule. A task where every graded
decision falls to a rule of two terms over fields the environment already exposes is an
answer a frontier model writes cold, before running anything, which is what an easiness
rejection looks like.

The features are deliberately generous. `apart` is the number of seats the list's holders
take standing under their own names, which is one call to the shipped seat allocation away
and is exactly the answer a solver reaches first. If the graded decision were reproducible
from it the task would be worth nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402


PROBE = r'''
import json, sys
sys.path.insert(0, %r)
from reg import book, poll, site
from pol import screen, voice, tally
out = []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        bk = book.load(fh.read())
    st = site.Site(bk)
    on = screen.sweep(st)
    for cid in st.cos():
        rows = [(st.voter(h), w) for h, w in st.stakes(cid)]
        mine = sorted({v for v, _ in rows if v in on})
        myvotes = sum(w for v, w in rows if v in on)
        allvotes = sum(w for _, w in rows)
        alone = poll.elect({v: sum(w for v2, w in rows if v2 == v)
                            for v, _ in rows}, st.seats(cid))
        apart = sum(1 for k in alone if k in on)
        got = tally.held(poll.elect(voice.hands(st, cid, on), st.seats(cid)), on)
        out.append({
            "seats": st.seats(cid),
            "hands": len({v for v, _ in rows}),
            "mine": len(mine),
            "myvotes": myvotes // 10,
            "allvotes": allvotes // 10,
            "apart": apart,
            "listed": 1 if cid in on else 0,
            "took": got,
        })
sys.stdout.write(json.dumps(out))
'''


def _rows(count):
    tree = harness.stage(harness.REF)
    import json
    import subprocess
    import tempfile
    texts = [t for _, t in cases.CASES] + [t for _, t in gen.batch("decisions", count)]
    d = Path(tempfile.mkdtemp(prefix="dec-"))
    paths = []
    for i, t in enumerate(texts):
        p = d / ("r%04d.txt" % i)
        p.write_text(t, encoding="utf-8", newline="\n")
        paths.append(str(p))
    proc = subprocess.run([sys.executable, "-c", PROBE % str(tree)] + paths,
                          capture_output=True, text=True, cwd=str(tree))
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return json.loads(proc.stdout)


def samples():
    rows = _rows(240)
    feats = [{k: v for k, v in r.items() if k not in ("listed", "took")} for r in rows]
    return {
        "on-the-list": [(f, bool(r["listed"])) for f, r in zip(feats, rows)],
        "seats-the-list-took": [(f, r["took"]) for f, r in zip(feats, rows)],
    }


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print(name, len(rows), rows[0])
