"""Random well-formed programs, and the harness that checks an implementation against brute.

Usage:
    python3 fuzz.py <n> [seed]           brute against the reference laid over the shipped tree
    python3 fuzz.py <n> [seed] --model   brute against tests/seal/model.py
"""
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
PARTS = ("cell.py", "hold.py", "cost.py", "tree.py", "gate.py", "free.py")


def program(seed, big=False):
    r = random.Random(seed)
    lines = []
    live = []
    stills = []
    capped = set()
    nline = 0
    nstill = 0
    cells = r.choice((4, 6, 8))
    out = []

    def newline():
        nonlocal nline
        nline += 1
        name = "L%d" % nline
        live.append(name)
        return name

    root = newline()
    out.append("line %s" % root)
    for _ in range(r.randint(8, 30)):
        pick = r.random()
        if pick < 0.30 or not live:
            name = r.choice(live)
            lo = r.randrange(cells)
            hi = min(cells - 1, lo + r.randrange(3))
            out.append("put %s %d %d %d" % (name, lo, hi, r.randrange(1, 9)))
        elif pick < 0.40:
            name = r.choice(live)
            lo = r.randrange(cells)
            hi = min(cells - 1, lo + r.randrange(3))
            out.append("cut %s %d %d" % (name, lo, hi))
        elif pick < 0.55:
            nstill += 1
            name = "s%d" % nstill
            stills.append(name)
            out.append("still %s %s" % (r.choice(live), name))
        elif pick < 0.67 and stills:
            name = newline()
            out.append("graft %s %s" % (r.choice(stills), name))
        elif pick < 0.75:
            out.append("lift %s" % r.choice(live))
        elif pick < 0.82 and stills:
            name = r.choice(stills)
            stills.remove(name)
            out.append("drop %s" % name)
        elif pick < 0.88:
            name = r.choice(live)
            capped.add(name)
            out.append("cap %s %d" % (name, r.randrange(0, 60)))
        elif pick < 0.94:
            out.append("ask %s" % r.choice(live))
        else:
            out.append("at %s %d" % (r.choice(live), r.randrange(cells)))
    out.append("ask %s" % root)
    for name in live:
        out.append("ask %s" % name)
    lines.extend(out)
    return lines


def lay(which):
    """A scratch tree: the shipped environment with one implementation laid over it."""
    room = Path(tempfile.mkdtemp())
    shutil.copytree(TASK / "environment" / "app_src", room / "app")
    for part in PARTS:
        shutil.copy(which / part, room / "app" / "led" / part)
    return room / "app"


RUN = """
import json, sys, traceback
sys.path.insert(0, %r)
import ops
from led import store
out = []
for lines in json.load(open(%r)):
    st = store.Led()
    try:
        for line in lines:
            ops.ex(st, tuple(line.split()))
        out.append(st.out)
    except Exception:
        out.append(["ERR " + traceback.format_exc(limit=2).strip().splitlines()[-1]])
json.dump(out, open(%r, "w"))
"""


def under(tree, progs):
    import json
    room = Path(tempfile.mkdtemp())
    src, dst = room / "in.json", room / "out.json"
    src.write_text(json.dumps(progs), encoding="utf-8")
    code = RUN % (str(tree), str(src), str(dst))
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-2000:])
    return json.loads(dst.read_text(encoding="utf-8"))


def main():
    import brute
    n = int(sys.argv[1])
    seed = sys.argv[2] if len(sys.argv) > 2 else "f"
    if "--model" in sys.argv:
        sys.path.insert(0, str(TASK / "tests" / "seal"))
        import model
        run = model.expect
        got = None
    else:
        tree = lay(TASK / "solution")
        run = None
    progs = [program("%s/%d" % (seed, i)) for i in range(n)]
    if run is None:
        got = under(tree, progs)
    else:
        got = []
        for lines in progs:
            try:
                got.append(run(lines))
            except Exception as exc:
                got.append(["ERR %s" % exc])
    bad = 0
    for i, lines in enumerate(progs):
        want = brute.expect(lines)
        if got[i] != want:
            bad += 1
            if bad <= 3:
                print("=== program %d" % i)
                print("\n".join(lines))
                print("want:", want)
                print("got :", got[i])
    print("%d of %d differ" % (bad, n))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
