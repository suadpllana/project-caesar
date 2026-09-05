import json
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
ENV = TASK / "environment" / "app_src"
SOL = TASK / "solution"

sys.path.insert(0, str(TASK / "tests"))
import cases  # noqa: E402
import gen  # noqa: E402
import oracle  # noqa: E402


def reference(tmp):
    d = pathlib.Path(tmp) / "ref"
    shutil.copytree(ENV, d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for f in sorted(SOL.glob("*.py")):
        shutil.copy(f, d / "wire" / f.name)
    return str(d)


def play(root, rows, ops):
    for m in [m for m in list(sys.modules) if m.startswith("wire")]:
        del sys.modules[m]
    sys.path.insert(0, root)
    try:
        from wire import plan
        from wire.reg import load
        return [[str(x) for x in r] for r in plan.run(load(rows), ops)]
    finally:
        sys.path.remove(root)


def main():
    tmp = tempfile.mkdtemp()
    try:
        root = reference(tmp)
        fixed = {}
        for nm, rows, ops in cases.FIXED:
            got = play(root, rows, ops)
            want = [[str(x) for x in t] for t in oracle.play(rows, ops)]
            if got != want:
                print("reference disagrees with the sealed model on", nm)
                return 1
            fixed[nm] = got
        bad = 0
        for i in range(400):
            rows, ops = gen.stream("prove-%d" % i, i % 2 == 0)
            got = play(root, rows, ops)
            want = [[str(x) for x in t] for t in oracle.play(rows, ops)]
            if got != want:
                bad += 1
        if bad:
            print("reference disagrees with the sealed model on", bad, "of 400 streams")
            return 1
        out = TASK / "tests" / "gt.json"
        out.write_text(json.dumps({"fixed": fixed}, indent=1, sort_keys=True), newline="\n")
        print("proved on %d named cases and 400 generated streams" % len(fixed))
        print("wrote", out)
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
