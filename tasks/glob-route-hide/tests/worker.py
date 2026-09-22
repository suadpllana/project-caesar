"""Run the submitted resolver over every exam program. Unprivileged, and trusted for nothing.

This is the only stage that executes submitted code, so it decides nothing: it stages a fresh
copy of the pristine tree, lays the five collected resolution files over it, runs every exam
program through the driver's `run(text)` and writes down what came back, with a digest of the
program it actually read. The grader treats this output as hostile. A crash, a hang or a
missing record is a failure, never a pass.

The wall clock the verifier puts on this process is also the task's execution limit, so a
correct resolver that cannot get through the exam in time scores exactly like a wrong one; the
two scale families - module trees where every module reads its parent and re-exports its
children, and flat modules reading each other at random - exist for that.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = pathlib.Path(os.environ.get("GRH_TESTS", "/tests"))
WORK = pathlib.Path(os.environ.get("GRH_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("GRH_SUB", "/app/fe"))
PARTS = ("vis.py", "own.py", "glob.py", "fix.py", "say.py")


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def stage():
    """A fresh copy of the pristine tree with the collected files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(TESTS / "pristine", here)
    for part in PARTS:
        sent = SENT / part
        if sent.is_file():
            shutil.copy(sent, here / "fe" / part)
    return here


def main():
    exam = pathlib.Path(sys.argv[sys.argv.index("--exam") + 1])
    out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
    index = json.loads((exam / "index.json").read_text(encoding="utf-8"))

    here = stage()
    sys.path.insert(0, str(here))
    import run_res

    recs = []
    for entry in index:
        text = (exam / entry["file"]).read_text(encoding="utf-8")
        lines = text.rstrip("\n").split("\n")
        got, err = None, None
        try:
            got = run_res.run(text)
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"name": entry["name"], "sig": digest(lines), "got": got, "err": err})

    out.write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
