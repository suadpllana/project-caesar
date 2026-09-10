"""Time an overlay of naive-but-correct modules against the graded population.

Each overlay must produce exactly the reference's trace: a variant that is also wrong
measures nothing. The number that matters is wall clock against the stated limit.
"""
import pathlib
import shutil
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"
sys.path.insert(0, str(TASK / "tests"))
import gen  # noqa: E402

PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")


def stage(overlay=None):
    room = pathlib.Path(tempfile.mkdtemp())
    tree = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", tree)
    for part in PARTS:
        shutil.copy(TASK / "solution" / part, tree / "store" / part)
    if overlay:
        for part in sorted(pathlib.Path(overlay).glob("*.py")):
            shutil.copy(part, tree / "store" / part.name)
    return tree


def run(tree, work, want=None, budget=None):
    sys.path.insert(0, str(tree))
    for mod in [m for m in list(sys.modules) if m.split(".")[0] in ("base", "store", "ops")]:
        del sys.modules[mod]
    from base import feed
    out = {}
    t0 = time.time()
    for _fam, name, lines in work:
        out[name] = feed.run(lines)
        if budget and time.time() - t0 > budget:
            print("  over budget after %s (%.1fs)" % (name, time.time() - t0), flush=True)
            break
    spent = time.time() - t0
    sys.path.remove(str(tree))
    if want is not None:
        bad = [n for n in out if out[n] != want[n]]
        print("  trace differs on %d programs" % len(bad), flush=True)
    return spent, out


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--tree":
        work = gen.programs("s1", 45)
        spent, _ = run(pathlib.Path(sys.argv[2]), work)
        print("whole graded set %7.2fs" % spent)
        return
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    work = gen.programs("s1", per)
    base = stage()
    spent, want = run(base, work)
    print("reference          %7.2fs" % spent, flush=True)
    for overlay in sorted((HERE / "naive").iterdir()):
        if not overlay.is_dir():
            continue
        tree = stage(overlay)
        spent, got = run(tree, work, want, budget=600)
        print("%-18s %7.2fs" % (overlay.name, spent), flush=True)


if __name__ == "__main__":
    main()
