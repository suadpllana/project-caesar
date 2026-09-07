"""Run the submitted collector. Unprivileged, sandboxed, and trusted for nothing.

Everything this file produces is treated as hostile by the grader: it is the only stage that
executes agent code, so it decides nothing. The trusted preparation stage has already placed a
pristine runtime and the program texts in `/work`, without expected records. This worker overlays
the five submitted collector modules, runs every program, and writes down what came out. It never
imports from `/tests`, which is unreadable while this process runs. A crash, a hang or a silent
exit loses the results, which the grader reads as a failure - never as a pass.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

WORK = pathlib.Path(os.environ.get("RPS_WORK", "/work"))
SUBMITTED = pathlib.Path(os.environ.get("RPS_SUB", "/app/col"))
PARTS = ("plan.py", "scan.py", "keep.py", "age.py", "wipe.py")
PRISTINE = WORK / "pristine"
PROGRAMS = WORK / "programs.json"


def build_tree():
    tmp = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    tree = tmp / "tree"
    shutil.copytree(PRISTINE, tree)
    for name in PARTS:
        one = SUBMITTED / name
        if one.is_file():
            shutil.copy(one, tree / "col" / name)
    return tree


def digest(lines):
    """What the grader checks the program against. A digest rather than the text itself: the
    graded set runs to megabytes, and echoing all of it back would price every submission's
    execution limit on JSON rather than on its collector."""
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def load_programs():
    raw = json.loads(PROGRAMS.read_text(encoding="utf-8"))
    return [(item["fam"], item["name"], item["lines"]) for item in raw]


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    progs = load_programs()

    tree = build_tree()
    sys.path.insert(0, str(tree))
    import ops
    from mem import heap

    recs = []
    for fam, name, lines in progs:
        got, err = None, None
        try:
            h = heap.Heap()
            acc = []
            for ln in lines:
                ops.ex(h, tuple(ln.split()), acc)
            got = acc
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "prog": digest(lines),
                     "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
