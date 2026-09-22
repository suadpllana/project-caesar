"""Time one engine over the scale family, or over the whole graded set.

The resource gate is the only limit this task states, so its two numbers are measured here
rather than estimated: what the reference costs on the `deep` programs, and what the same
engine costs with the verdict memo taken out - an engine whose traces are identical and which
re-walks a record every time the step is pulled, so each level of a diamond is walked twice.

Usage:
    python authoring/pull-check-stale/timing.py <engine-dir> [deep|all] [timeout-seconds]
"""

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TASK = REPO / "tasks" / "pull-check-stale"
PARTS = ("keep.py", "mark.py", "hold.py", "step.py", "wake.py")

DRIVER = """
import sys, time, json
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import gen, run_eng
from eng import plan
which = %r
progs = [(n, t) for n, t in gen.programs("timing", 34)
         if which == "all" or n.startswith("deep")]
rows = []
for name, text in progs:
    t0 = time.time()
    run_eng.run(plan.parse(text))
    rows.append((name, time.time() - t0))
print(json.dumps(rows))
"""


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    engine = Path(argv[1])
    which = argv[2] if len(argv) > 2 else "deep"
    cap = int(argv[3]) if len(argv) > 3 else 900
    root = Path(tempfile.mkdtemp(prefix="pcs-time-"))
    try:
        app = root / "app"
        shutil.copytree(TASK / "environment" / "app_src", app)
        for part in PARTS:
            src = engine / part
            if src.is_file():
                shutil.copyfile(src, app / "eng" / part)
        script = root / "drive.py"
        script.write_text(DRIVER % (str(app), str(TASK / "tests"), which),
                          encoding="utf-8", newline="\n")
        t0 = time.time()
        run = subprocess.run([sys.executable, "-u", str(script)],
                             capture_output=True, text=True, timeout=cap)
        spent = time.time() - t0
        if run.returncode != 0:
            print("engine failed: %s" % run.stderr.strip()[-600:])
            return 1
        import json
        rows = json.loads(run.stdout.strip().splitlines()[-1])
        rows.sort(key=lambda r: -r[1])
        print("%s over %s: %d programs, %.2fs total" % (engine.name, which, len(rows), spent))
        for name, secs in rows[:6]:
            print("   %-14s %8.3fs" % (name, secs))
        return 0
    except subprocess.TimeoutExpired:
        print("%s over %s: still running after %ds" % (engine.name, which, cap))
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
