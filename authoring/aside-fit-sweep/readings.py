"""Separate every wrong reading, and say what separates it.

For each reading: which enumerated case catches it, and what share of a nonce population it
moves. A reading nothing catches is a rule the verifier does not actually grade; a reading that
moves a fraction of a per cent of the population is a family that is not shaped for it, since
grading is all-or-nothing and a hand case has to exist.

    python3 readings.py [seed] [per]
"""
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "aside-fit-sweep"
READINGS = HERE / "readings"

RUNNER = r'''
import json, sys, time
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
import gen, ops, cases
from reg import live, text

def run(lines):
    span, part, body = text.parse(lines)
    h = live.Pool(span, part)
    out = []
    ex = ops.ex
    for line in body:
        ex(h, tuple(line.split()), out)
    return out

seed, per = sys.argv[3], int(sys.argv[4])
small = sys.argv[6] == "small"
res = {}
for name in cases.ORDER:
    try:
        res["hand:" + name] = run(cases.ops(name))
    except Exception as exc:
        res["hand:" + name] = ["RAISED %s" % exc]
t0 = time.time()
for fam, name, lines in gen.programs(seed, per):
    if small and fam in ("wide", "churn"):
        continue
    try:
        res[name] = run(lines)
    except Exception as exc:
        res[name] = ["RAISED %s" % exc]
json.dump({"res": res, "secs": time.time() - t0}, open(sys.argv[5], "w"))
'''


def stage(overlay=None):
    room = pathlib.Path(tempfile.mkdtemp(prefix="afs-"))
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    for part in ("find.py", "cut.py", "side.py", "back.py", "edge.py"):
        src = (overlay or (TASK / "solution")) / part
        if src.is_file():
            shutil.copy(src, app / "pool" / part)
    return room, app


def measure(overlay, seed, per, out):
    room, app = stage(overlay)
    script = room / "run.py"
    script.write_text(RUNNER, encoding="utf-8")
    subprocess.run([sys.executable, str(script), str(app), str(TASK / "tests"),
                    seed, str(per), str(out), "small"], check=True)
    shutil.rmtree(room, ignore_errors=True)
    import json
    return json.loads(pathlib.Path(out).read_text())


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "readings"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="afs-out-"))
    good = measure(None, seed, per, scratch / "ref.json")
    print("reference: %d programs, %.1fs on the nonce set" % (len(good["res"]), good["secs"]))
    rows = []
    for room in sorted(READINGS.iterdir()):
        got = measure(room, seed, per, scratch / ("%s.json" % room.name))
        hands = [k[5:] for k in good["res"] if k.startswith("hand:")
                 and good["res"][k] != got["res"].get(k)]
        nonce = [k for k in good["res"] if not k.startswith("hand:")
                 and good["res"][k] != got["res"].get(k)]
        total = sum(1 for k in good["res"] if not k.startswith("hand:"))
        rows.append((room.name, hands, len(nonce), total, got["secs"]))
        print("%-16s hand:%-28s nonce:%5.1f%%  %.1fs" % (
            room.name, ",".join(hands[:3]) or "-", 100.0 * len(nonce) / total, got["secs"]))
    print()
    blind = [r[0] for r in rows if not r[1] and r[2] == 0]
    nohand = [r[0] for r in rows if not r[1] and r[2]]
    print("caught by no case at all: %s" % (blind or "none"))
    print("no hand case, nonce only: %s" % (nohand or "none"))
    shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()


# --- the contract tools/readingcheck.py reads -----------------------------------------
#
# The same readings, offered the way that tool wants them: the reference directory, each
# reading as the files it replaces, one driver, and the two populations.

REFERENCE = str(TASK / "solution")

READINGS = {
    room.name: {p.name: p.read_text(encoding="utf-8")
                for p in sorted(room.iterdir()) if p.suffix == ".py"}
    for room in sorted(READINGS.iterdir()) if room.is_dir()
} if READINGS.is_dir() else {}

_TREES = {}


def _tree(policy):
    policy = str(policy)
    app = _TREES.get(policy)
    if app is None:
        room = pathlib.Path(tempfile.mkdtemp(prefix="afs-rc-"))
        app = room / "app"
        shutil.copytree(TASK / "environment" / "app_src", app)
        for part in ("find.py", "cut.py", "side.py", "back.py", "edge.py"):
            src = pathlib.Path(policy) / part
            if src.is_file():
                shutil.copy(src, app / "pool" / part)
        _TREES[policy] = app
    return app


def run(policy, text):
    """One program under one policy directory, as the trace it prints."""
    app = _tree(policy)
    for name in list(sys.modules):
        if name in ("ops", "reg", "pool") or name.startswith(("reg.", "pool.")):
            del sys.modules[name]
    sys.path.insert(0, str(app))
    try:
        import ops
        from reg import live
        from reg import text as reader
        span, part, body = reader.parse(text.splitlines())
        h = live.Pool(span, part)
        out = []
        for line in body:
            ops.ex(h, tuple(line.split()), out)
        return tuple(out)
    except Exception as exc:
        return ("RAISED %s" % type(exc).__name__,)
    finally:
        sys.path.remove(str(app))


def enumerated():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    sys.path.insert(0, str(TASK / "tests"))
    import gen
    out = []
    per = max(1, n // 10 + 1)
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in ("wide", "churn"):
            continue
        out.append((name, "\n".join(lines)))
        if len(out) >= n:
            break
    return out
