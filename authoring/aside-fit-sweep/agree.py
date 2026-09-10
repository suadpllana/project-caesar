"""Reference vs sealed model over every generated program.

The reference is laid over a copy of the shipped tree, exactly as the verifier does it, so this
never accidentally measures the broken allocator that ships in environment/.
"""
import pathlib
import shutil
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "aside-fit-sweep"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")

room = pathlib.Path(tempfile.mkdtemp(prefix="afs-agree-"))
app = room / "app"
shutil.copytree(TASK / "environment" / "app_src", app)
for part in PARTS:
    shutil.copy(TASK / "solution" / part, app / "pool" / part)

sys.path.insert(0, str(app))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import gen, model, ops  # noqa: E402
from reg import live, text  # noqa: E402


def run(lines):
    span, part, body = text.parse(lines)
    h = live.Pool(span, part)
    out = []
    ex = ops.ex
    for line in body:
        ex(h, tuple(line.split()), out)
    return out


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "agree"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    work = gen.programs(seed, per)
    tr = tm = 0.0
    bad = 0
    for _fam, name, lines in work:
        t0 = time.time(); a = run(lines); tr += time.time() - t0
        t0 = time.time(); b = model.expect(lines); tm += time.time() - t0
        if a != b:
            bad += 1
            if bad == 1:
                for i in range(max(len(a), len(b))):
                    x = a[i] if i < len(a) else None
                    y = b[i] if i < len(b) else None
                    if x != y:
                        print("first diff %s line %d ref=%r model=%r" % (name, i, x, y))
                        break
                pathlib.Path("/tmp/bad.txt").write_text("\n".join(lines) + "\n")
    print("programs %d  differing %d  reference %.1fs  model %.1fs" % (len(work), bad, tr, tm))
    shutil.rmtree(room, ignore_errors=True)


main()
