"""Runs the submitted scan layer. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the tree, drops the six submitted files into it, runs every graded segment file and
writes down what came out. The grader treats this file's output as hostile input. A crash, a
hang or a silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the platform puts on this process is the task's execution limit, and the
programs were built before it started, so it measures the engine and nothing else. Two of the
seventeen families exist for it: one segment of sixty thousand rows over five columns in chunks of
sixteen to forty rows and pages of four to twelve, three queries of eight conditions, and one of
forty thousand rows over four columns in chunks of about two thousand, three queries of seven.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

WORK = pathlib.Path(os.environ.get("SCP_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("SCP_SUB", "/app/scn"))
PRISTINE = pathlib.Path(os.environ.get("SCP_TESTS", "/tests")) / "pristine"
PARTS = ("hdr.py", "dct.py", "live.py", "pick.py", "step.py", "proj.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted scn files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "scn" / part)
    return here


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--progs", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.progs, encoding="utf-8") as fh:
        work = json.load(fh)

    here = tree()
    sys.path.insert(0, str(here))
    import run_scan

    recs = []
    for item in work:
        lines = item["lines"]
        got, err = None, None
        try:
            got = run_scan.run("\n".join(lines) + "\n")
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": item["fam"], "name": item["name"], "sig": sig(lines),
                     "got": got, "err": err})

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(recs, fh)


if __name__ == "__main__":
    main()
