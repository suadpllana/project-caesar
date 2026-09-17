"""Cross-check the three implementations on the generated population, with timings.

    python3 -u cross.py [per]          brute (small only), model, reference laid over the tree

Prints one line per family: how many programs, how long each side took, and any disagreement.
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(HERE))

import brute  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402
from fuzz import lay  # noqa: E402

RUN = """
import json, sys, time, traceback
sys.path.insert(0, %r)
import ops
from led import store
out = []
for lines in json.load(open(%r)):
    st = store.Led()
    t = time.time()
    try:
        for line in lines:
            ops.ex(st, tuple(line.split()))
        out.append([st.out, time.time() - t])
    except Exception:
        out.append([["ERR " + traceback.format_exc(limit=3).strip().splitlines()[-1]],
                    time.time() - t])
json.dump(out, open(%r, "w"))
"""


def under(tree, progs):
    room = Path(tempfile.mkdtemp())
    src, dst = room / "in.json", room / "out.json"
    src.write_text(json.dumps(progs), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-c", RUN % (str(tree), str(src), str(dst))],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-3000:])
    return json.loads(dst.read_text(encoding="utf-8"))


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    which = Path(sys.argv[2]) if len(sys.argv) > 2 else TASK / "solution"
    tree = lay(which)
    work = gen.programs("cross-seed", per)
    bad = 0
    for fam, big in gen.FAMILIES:
        mine = [(name, lines) for f, name, lines in work if f == fam]
        progs = [lines for _n, lines in mine]
        t0 = time.time()
        got = under(tree, progs)
        t1 = time.time()
        want = [model.expect(lines) for lines in progs]
        t2 = time.time()
        slow = ""
        if not big:
            t3 = time.time()
            for lines, w in zip(progs, want):
                if brute.expect(lines) != w:
                    print("  BRUTE DIFFERS", fam)
                    bad += 1
            slow = " brute %.1fs" % (time.time() - t3)
        worst = max(g[1] for g in got) if got else 0.0
        for (name, lines), g, w in zip(mine, got, want):
            if g[0] != w:
                bad += 1
                if bad <= 3:
                    print("=== %s" % name)
                    print("\n".join(lines[:40]))
                    print("want:", w[:12])
                    print("got :", g[0][:12])
        print("%-8s n=%-4d ref %.1fs (worst %.2fs)  model %.1fs%s"
              % (fam, len(progs), t1 - t0, worst, t2 - t1, slow))
    print("disagreements: %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
