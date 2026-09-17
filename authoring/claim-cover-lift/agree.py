"""Run the reference and the sealed model over the generated population and diff them."""
import pathlib
import shutil
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent
TASK = ROOT.parent.parent / "tasks" / "claim-cover-lift"
PARTS = ("hold", "line", "fit", "lift", "knot", "gate")


def tree(src):
    room = pathlib.Path(tempfile.mkdtemp(prefix="ccl-agree-"))
    app = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", app)
    for part in PARTS:
        one = src / (part + ".py")
        if one.is_file():
            shutil.copy(one, app / "hb" / (part + ".py"))
    return room, app


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "agree"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    src = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else TASK / "solution"
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import gen
    import model

    room, app = tree(src)
    sys.path.insert(0, str(app))
    import ops
    from hb import store

    bad, took_ref, took_mod = [], 0.0, 0.0
    work = gen.programs(seed, per)
    for fam, name, body in work:
        start = time.time()
        st = store.Store()
        for raw in body:
            ops.ex(st, tuple(raw.split()))
        took_ref += time.time() - start
        start = time.time()
        want = model.expect(body)
        took_mod += time.time() - start
        if st.out != want:
            where = next((i for i, (a, b) in enumerate(zip(st.out, want)) if a != b),
                         min(len(st.out), len(want)))
            bad.append((name, where, st.out[where:where + 2], want[where:where + 2]))
    shutil.rmtree(room)
    print("%d programs, reference %.2fs, model %.2fs, %d mismatches"
          % (len(work), took_ref, took_mod, len(bad)))
    for row in bad[:5]:
        print("  %s at line %d: reference %s want %s" % row)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
