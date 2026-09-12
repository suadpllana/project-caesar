"""Freeze the enumerated answers, and prove that a change to the contract did not move them.

Every run reads the file it is about to write first. An answer that was already frozen and
comes out different is a contract change, and it is reported as one whether or not it was
meant: the additivity of a later rule is only worth anything if something checks it.

    python authoring/bind-claim-prune/build_gt.py [--write]
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lab  # noqa: E402

TASK = lab.TASK
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def ref_run():
    """The reference, through the shipped reader, so the two sides are compared as they run."""
    app = lab.tree("ref")
    sys.path.insert(0, str(app))
    import ops
    from bind import book
    out = {}
    for name in cases.ORDER:
        job = book.Job()
        for line in cases.ops(name):
            w = line.split()
            if w:
                ops.ex(job, tuple(w))
        out[name] = job.out
    return out, app


def main():
    write = "--write" in sys.argv
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    ref, app = ref_run()

    moved = [n for n in new if n in old and old[n] != new[n]]
    gone = [n for n in old if n not in new]
    fresh = [n for n in new if n not in old]
    split = [n for n in cases.ORDER if ref[n] != new[n]]

    for n in split:
        print("SPLIT %s" % n)
        for i in range(max(len(ref[n]), len(new[n]))):
            a = ref[n][i] if i < len(ref[n]) else "-"
            b = new[n][i] if i < len(new[n]) else "-"
            if a != b:
                print("   ref %-42s model %s" % (a, b))
    for n in moved:
        print("MOVED %s" % n)
        print("   was %s" % old[n])
        print("   now %s" % new[n])
    print("%d cases, %d new, %d removed, %d moved, %d reference/model splits"
          % (len(new), len(fresh), len(gone), len(moved), len(split)))
    import shutil
    shutil.rmtree(app.parent, ignore_errors=True)
    if split:
        return 1
    if write:
        body = json.dumps(new, indent=1, sort_keys=True) + "\n"
        if "\r" in body:
            raise SystemExit("carriage return in the frozen answers")
        GT.write_text(body, encoding="utf-8", newline="\n")
        print("wrote %s" % GT)
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
