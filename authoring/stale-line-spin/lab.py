"""Install a set of model files into a scratch copy of the tree and diff it against the model.

usage: python3 authoring/stale-line-spin/lab.py <dir-with-six-files> [seed] [per]
The scratch tree lives in a temp directory outside the task folder (CLAUDE.md, token-seam-emit).
"""
import importlib, os, shutil, sys, tempfile, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASK = os.path.join(ROOT, "tasks", "stale-line-spin")
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
sys.path.insert(0, os.path.join(TASK, "tests"))
import model, gen, cases

PARTS = ("line.py", "mem.py", "place.py", "turn.py", "step.py", "clock.py")


def tree(src):
    room = tempfile.mkdtemp(prefix="sls-lab-")
    app = os.path.join(room, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
    for p in PARTS:
        f = os.path.join(src, p)
        if os.path.isfile(f):
            shutil.copy(f, os.path.join(app, "sim", p))
    return room, app


def main():
    src = sys.argv[1]
    seed = sys.argv[2] if len(sys.argv) > 2 else "lab"
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    room, app = tree(src)
    sys.path.insert(0, app)
    try:
        import run_launch
        work = [("hand", n, cases.prog(n)) for n in cases.ORDER] + gen.programs(seed, per)
        bad = []
        t0 = time.time()
        slow = []
        for fam, name, lines in work:
            t1 = time.time()
            try:
                got = run_launch.run("\n".join(lines) + "\n")
            except Exception as e:
                got = ["error %r" % e]
            dt = time.time() - t1
            if dt > 1:
                slow.append((name, round(dt, 2)))
            if got != model.expect(lines):
                bad.append(name)
        print("ran %d launches in %.1fs; %d differ %s" % (len(work), time.time() - t0, len(bad), bad[:8]))
        print("slow:", slow)
    finally:
        shutil.rmtree(room, ignore_errors=True)


main()
