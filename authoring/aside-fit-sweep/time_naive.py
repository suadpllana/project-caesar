"""Time one wide and one churn program for the reference and for each correct-but-slow reading.

The limit in the brief covers the whole graded set: three of each large program and about four
hundred small ones. A reading that needs longer than the limit for a single large program is
already out.
"""
import pathlib, random, shutil, subprocess, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "aside-fit-sweep"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")
RUN = '''
import random, sys, time
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import gen, ops
from reg import live, text
lines = gen.BUILD[sys.argv[3]](random.Random("time|%s" % sys.argv[3]))
span, part, body = text.parse(lines)
h = live.Pool(span, part); out = []
t0 = time.time()
for line in body:
    ops.ex(h, tuple(line.split()), out)
print("%.1f" % (time.time() - t0))
'''

def one(overlay, fam, cap):
    room = pathlib.Path(tempfile.mkdtemp(prefix="afs-t-"))
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    for p in PARTS:
        src = (overlay or (TASK / "solution")) / p
        if src.is_file():
            shutil.copy(src, app / "pool" / p)
    (room / "r.py").write_text(RUN)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(room / "r.py"), str(app), str(TASK / "tests"), fam],
                           capture_output=True, text=True, timeout=cap)
        got = r.stdout.strip() or r.stderr.strip()[-80:]
    except subprocess.TimeoutExpired:
        got = "> %d (killed)" % cap
    shutil.rmtree(room, ignore_errors=True)
    return got

def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    names = ["<reference>"] + sys.argv[2:]
    for name in names:
        overlay = None if name == "<reference>" else (HERE / "variants" / name if (HERE / "variants" / name).is_dir() else HERE / "readings" / name)
        for fam in ("wide", "churn"):
            print("%-14s %-6s %s s" % (name, fam, one(overlay, fam, cap)), flush=True)

main()
