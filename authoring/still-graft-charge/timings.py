"""Measure what each correct-but-unaffordable structure costs, against the 60 second limit.

    python3 -u timings.py                 the whole graded set, per implementation
    python3 -u timings.py <fam> <cap>     one family under one implementation, bounded

Every number quoted in `task.toml`, `STATE.md` and the brief comes from here. Output is
flushed, because a timing harness whose output sits in a buffer looks exactly like a hang.
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
sys.path.insert(0, str(HERE))

import gen  # noqa: E402
from fuzz import lay  # noqa: E402

WHICH = {
    "reference": TASK / "solution",
    "slow-copy": HERE / "variants" / "slow-copy",
    "slow-scan": HERE / "variants" / "slow-scan",
    "slow-plain": HERE / "variants" / "slow-plain",
    "shipped": TASK / "environment" / "app_src" / "led",
}

RUN = """
import json, sys, time, traceback
sys.path.insert(0, %r)
import ops
from led import store
progs = json.load(open(%r))
out = []
for lines in progs:
    st = store.Led()
    t = time.time()
    try:
        for line in lines:
            ops.ex(st, tuple(line.split()))
        out.append([len(st.out), time.time() - t])
    except Exception:
        out.append([None, time.time() - t])
    print("  one program: %%.1fs" %% (time.time() - t), flush=True)
json.dump(out, open(%r, "w"))
"""


def under(tree, progs, cap):
    room = Path(tempfile.mkdtemp())
    src, dst = room / "in.json", room / "out.json"
    src.write_text(json.dumps(progs), encoding="utf-8")
    start = time.time()
    try:
        subprocess.run([sys.executable, "-u", "-c", RUN % (str(tree), str(src), str(dst))],
                       timeout=cap, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None, time.time() - start
    return json.loads(dst.read_text(encoding="utf-8")), time.time() - start


def main():
    if len(sys.argv) > 2:
        fam, cap = sys.argv[1], float(sys.argv[2])
        which = sys.argv[3:] or list(WHICH)
        progs = [gen.one(fam, "timing/%s" % fam)]
        for name in which:
            got, spent = under(lay(WHICH[name]), progs, cap)
            print("%-11s %-6s %s" % (name, fam,
                                     "%.1fs" % spent if got else
                                     "did not finish inside %.0fs" % cap), flush=True)
        return 0
    work = gen.programs("timing-seed", 45)
    progs = [lines for _f, _n, lines in work]
    for name, where in WHICH.items():
        got, spent = under(lay(where), progs, 3600)
        print("%-11s whole graded set: %s" % (
            name, "%.1fs" % spent if got else "did not finish inside 3600s"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
