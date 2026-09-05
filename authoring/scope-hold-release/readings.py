import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / HERE.name
ENV = TASK / "environment" / "app_src"
SOL = TASK / "solution"

sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402

READINGS = {
    "capture-taken-at-invocation": ["own", "gate", "tear"],
    "chain-under-a-singleton-ignored": ["gate", "tear", "hold"],
    "refusal-not-transitive": ["own", "tear", "hold"],
    "teardown-in-creation-order": ["own", "gate", "hold"],
}


def stage(tmp, name, fixed):
    d = pathlib.Path(tmp) / name
    shutil.copytree(ENV, d)
    shutil.rmtree(d / "wire" / "__pycache__", ignore_errors=True)
    for f in fixed:
        shutil.copy(SOL / (f + ".py"), d / "wire" / (f + ".py"))
    return str(d)


def play(root, rows, ops):
    for m in [m for m in list(sys.modules) if m.startswith("wire")]:
        del sys.modules[m]
    sys.path.insert(0, root)
    try:
        from wire import plan
        from wire.reg import load
        return [tuple(str(x) for x in r) for r in plan.run(load(rows), ops)]
    finally:
        sys.path.remove(root)


def main():
    tmp = tempfile.mkdtemp()
    try:
        gen_streams = [gen.stream(s, s % 2 == 0) for s in range(300)]
        gen_truth = [[tuple(str(x) for x in t) for t in oracle.play(r, o)] for r, o in gen_streams]
        fix_truth = {nm: [tuple(str(x) for x in t) for t in oracle.play(r, o)]
                     for nm, r, o in cases.FIXED}
        bad = 0
        print("%-34s %9s  %s" % ("reading", "generated", "pinned by"))
        for label, fixed in READINGS.items():
            root = stage(tmp, label, fixed)
            moved = sum(1 for (r, o), w in zip(gen_streams, gen_truth) if play(root, r, o) != w)
            pin = [nm for nm, r, o in cases.FIXED if play(root, r, o) != fix_truth[nm]]
            share = 100.0 * moved / len(gen_streams)
            ok = pin or share >= 10.0
            if not ok:
                bad += 1
            print("%-34s %5d %4.1f%%  %s" % (label, moved, share, pin[0] if pin else "NOTHING"))
        empty = [nm for nm in fix_truth if not fix_truth[nm]]
        if empty:
            bad += 1
            print("cases that grade nothing:", empty)
        dupes = {}
        for nm, rec in fix_truth.items():
            dupes.setdefault(tuple(rec), []).append(nm)
        for rec, nms in sorted(dupes.items()):
            if len(nms) > 1:
                print("cases with identical output:", nms)
        print("FAIL" if bad else "all readings pinned")
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
