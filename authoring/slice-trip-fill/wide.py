"""Build a wide session and time the reference against the naive-but-correct form.

The scale axis is activation, not the book. An armed order trips at most once and its
condition is monotone in the price, so an engine that keeps the parked orders ordered by
their trip price touches only the ones that actually fire, plus one look, per fill. An
engine that scans the parked list once per fill is exactly as correct and costs
fills x parked.

To make that the only axis, the book stays small and the fills come from deeply sliced
resting orders: one resting order of twenty thousand showing four at a time answers five
thousand fills on its own.
"""

import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readings  # noqa: E402


def build(seed, deep, arms, slabs, slab, show):
    rng = random.Random(seed)
    mark = 1000
    lines = ["cap 40", "mark %d" % mark]
    oid = 0
    for i in range(deep):
        oid += 1
        side = "s" if i % 2 else "b"
        off = 1 + (i % 9)
        px = mark + off if side == "s" else mark - off
        lines.append("new %d %d %s %d %d %s day -"
                     % (oid, 1 + (i % 5), side, px, rng.choice([20, 40, 60]),
                        rng.choice(["-", "5", "8"])))
    for i in range(arms):
        oid += 1
        side = "b" if i % 2 else "s"
        trp = mark + (60 + (i % 400)) * (1 if side == "b" else -1)
        lines.append("new %d %d %s %d %d - day %d"
                     % (oid, 1 + (i % 5), side, mark, 10, trp))
    for i in range(slabs):
        oid += 1
        side = "s" if i % 2 else "b"
        px = mark + (1 if side == "s" else -1)
        lines.append("new %d 9 %s %d %d %d day -" % (oid, side, px, slab, show))
        oid += 1
        lines.append("new %d 8 %s %d %d - part -"
                     % (oid, "b" if side == "s" else "s", px, slab))
    return "\n".join(lines) + "\n"


SLOW_TRIP = '''def box(st):
    if st.arm is None:
        st.arm = []
    return st.arm


def park(st, o, out):
    box(st).append(o)
    out.row("arm", o.oid)


def drop(st, oid):
    a = box(st)
    for i, o in enumerate(a):
        if o.oid == oid:
            del a[i]
            return True
    return False


def check(st, out):
    a = box(st)
    hit = []
    for o in a:
        if o.side == "b" and st.last >= o.trp:
            hit.append(o)
        elif o.side == "s" and st.last <= o.trp:
            hit.append(o)
    hit.sort(key=lambda x: x.oid)
    for o in hit:
        a.remove(o)
        out.row("trp", o.oid)
        st.pend.append(o)
    return hit


def parked(st):
    return sorted(box(st), key=lambda o: o.oid)
'''


def policy(extra=None):
    d = tempfile.mkdtemp(prefix="wide-")
    for fn in os.listdir(readings.REFERENCE):
        if fn.endswith(".py"):
            shutil.copyfile(os.path.join(readings.REFERENCE, fn), os.path.join(d, fn))
    for name, src in (extra or {}).items():
        with open(os.path.join(d, name), "w") as fh:
            fh.write(src)
    return d


def timed(pol, path, limit):
    tree = readings._tree(pol)
    script = (
        "import sys,time\n"
        "sys.path.insert(0, %r)\n"
        "from mkt.rd import read\n"
        "from mkt.drv import drive\n"
        "t=time.time()\n"
        "cap,mark,msgs=read(open(%r).read())\n"
        "n=[0]\n"
        "def sink(r):\n    n[0]+=1\n"
        "drive(cap,mark,msgs,sink)\n"
        "print('%%.2f %%d' %% (time.time()-t, n[0]))\n" % (tree, path))
    t0 = time.time()
    p = subprocess.run([sys.executable, "-c", script], capture_output=True,
                       text=True, timeout=limit)
    if p.returncode:
        return None, p.stderr.strip()[-400:]
    return p.stdout.split(), None


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.join(tempfile.mkdtemp(), "wide.txt")
    deep = int(argv[2]) if len(argv) > 2 else 60
    arms = int(argv[3]) if len(argv) > 3 else 4000
    slabs = int(argv[4]) if len(argv) > 4 else 14
    slab = int(argv[5]) if len(argv) > 5 else 12000
    show = int(argv[6]) if len(argv) > 6 else 4
    text = build("wide", deep, arms, slabs, slab, show)
    with open(out, "w", newline="\n") as fh:
        fh.write(text)
    print("session %s  %d lines" % (out, text.count("\n")), flush=True)
    fast = policy()
    slow = policy({"trip.py": SLOW_TRIP})
    for label, pol, limit in (("reference", fast, 900), ("naive-scan", slow, 900)):
        got, err = timed(pol, out, limit)
        if err:
            print("%-12s FAILED %s" % (label, err), flush=True)
        else:
            print("%-12s %6ss  %s rows" % (label, got[0], got[1]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
