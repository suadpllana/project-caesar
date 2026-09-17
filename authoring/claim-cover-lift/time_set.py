"""Time a reading over the whole graded population, the way the worker runs it.

Usage: python time_set.py <seed> <per> [slow-name ...]
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent
TASK = ROOT.parent.parent / "tasks" / "claim-cover-lift"
PARTS = ("hold", "line", "fit", "lift", "knot", "gate")

RUN = '''
import pathlib, sys, time
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import gen
import step
from hb import desk
work = gen.programs(%r, %d)
start = time.time()
for fam, name, body in work:
    st = desk.Store()
    for raw in body:
        step.ex(st, tuple(raw.split()))
print("%%.2f" %% (time.time() - start))
'''


def tree(src):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ccl-time-"))
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    for part in PARTS:
        one = src / (part + ".py")
        if one.is_file():
            shutil.copy(one, app / "hb" / (part + ".py"))
    return room, app


def main():
    seed, per = sys.argv[1], int(sys.argv[2])
    names = sys.argv[3:] or ["reference"] + sorted(p.name for p in (ROOT / "slow").iterdir()
                                                   if p.is_dir())
    for name in names:
        src = TASK / "solution" if name == "reference" else ROOT / "slow" / name
        room, app = tree(src)
        code = RUN % (str(TASK / "tests"), str(app), seed, per)
        try:
            done = subprocess.run([sys.executable, "-c", code], cwd=app, capture_output=True,
                                  text=True, timeout=1200)
            print("%-10s %s" % (name, done.stdout.strip() or done.stderr.strip()[-200:]),
                  flush=True)
        except subprocess.TimeoutExpired:
            print("%-10s past 1200s" % name, flush=True)
        shutil.rmtree(room)


if __name__ == "__main__":
    main()
