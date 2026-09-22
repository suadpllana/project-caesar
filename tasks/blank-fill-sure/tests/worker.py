"""The stage that runs submitted code. It is unprivileged, and nothing it writes is trusted.

It builds a fresh copy of the tree from the verifier's own pristine files, puts the three
submitted evaluator files over it, and runs every graded program through `run_ask.run`,
writing down what each one printed. It decides nothing: the grader recomputes every expected
report itself and reads this stage's output as hostile input.

The sealed model and the frozen answers are not readable from here - `tests/seal` is 0700 and
root's, and this process runs as uid 1002 - so a submission that tries to import them inside
the verifier fails instead of copying the answers.

The wall clock the platform puts on this process is the task's execution limit. A submission
that is right but cannot get through the whole set in time is scored exactly like a wrong one;
the wide and flag families exist for that.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("BFS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("BFS_WORK", "/work"))
SUBMITTED = pathlib.Path(os.environ.get("BFS_SUBMITTED", "/app/rs"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("cmp.py", "join.py", "keep.py")


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def fresh_tree():
    room = pathlib.Path(tempfile.mkdtemp(prefix="tree-", dir=str(WORK)))
    app = room / "app"
    shutil.copytree(PRISTINE, app)
    for part in PARTS:
        src = SUBMITTED / part
        if src.is_file():
            shutil.copyfile(src, app / "rs" / part)
    return app


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "seed").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    app = fresh_tree()
    sys.path.insert(0, str(app))
    import run_ask

    graded = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    graded += gen.programs(seed, per)

    records = []
    for fam, name, lines in graded:
        got, err = None, None
        try:
            got = run_ask.run("\n".join(lines) + "\n")
        except Exception:
            err = traceback.format_exc(limit=2).strip().splitlines()[-1]
        records.append({"fam": fam, "name": name, "sig": digest(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(records), encoding="utf-8")


if __name__ == "__main__":
    main()
