"""Time one set of six model files over the whole graded set of one nonce, as the worker runs it.

Hand launches first, then gen.programs(seed, 40), all in one process. Prints the total and the
slowest launches, and whether any launch raised. No comparison with the model: this is the
number the 60-second clock is measured against (container_time.py runs it in the image).

usage: python3 authoring/stale-line-spin/whole.py <dir-with-six-files> [seed]
"""
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASK = os.path.join(ROOT, "tasks", "stale-line-spin")
sys.path.insert(0, os.path.join(TASK, "tests"))
import cases  # noqa: E402
import gen  # noqa: E402

PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")

src = sys.argv[1]
seed = sys.argv[2] if len(sys.argv) > 2 else "whole"
room = tempfile.mkdtemp(prefix="sls-whole-")
try:
    app = os.path.join(room, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
    for p in PARTS:
        if os.path.isfile(os.path.join(src, p)):
            shutil.copy(os.path.join(src, p), os.path.join(app, "sim", p))
    sys.path.insert(0, app)
    import run_launch
    work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, 40)
    times, bad = [], 0
    t0 = time.time()
    for fam, name, lines in work:
        t1 = time.time()
        try:
            run_launch.run("\n".join(lines) + "\n")
        except Exception as e:
            bad += 1
            print("raised", name, repr(e)[:120])
        times.append((time.time() - t1, name))
    total = time.time() - t0
    per = {}
    for dt, name in times:
        fam = name.rsplit("-", 1)[0] if "-" in name else name
        per[fam] = per.get(fam, 0) + dt
    print("whole set: %.1fs over %d launches, %d raised" % (total, len(work), bad))
    print("by family:", {k: round(v, 1) for k, v in sorted(per.items(), key=lambda x: -x[1])[:8]})
finally:
    shutil.rmtree(room, ignore_errors=True)
