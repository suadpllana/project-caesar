"""Runs the submitted engine. Unprivileged, sandboxed, and trusted for nothing.

This is the only stage that executes agent code, so it decides nothing: it stages a pristine
copy of the shipped tree, drops the six submitted modules into it, replays every graded shard
and writes down what came out. The grader treats this file's output as hostile input. A crash,
a hang or a silent exit loses the record, and a lost record is a failure, never a pass.

The wall clock the platform puts on this process is also the task's execution limit, so an
engine that settles every shard correctly and cannot get through the set in time is scored
exactly like a wrong one. Two of the ten families exist for that: `wide` lays forty-five
thousand records and `deep` twenty-five hundred, each shard declaring about four billion
tokens, which no engine that keeps a value per token position can reach.
"""
import contextlib
import hashlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import traceback

TESTS = os.environ.get("PSS_TESTS", "/tests")
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import gen  # noqa: E402

WORK = pathlib.Path(os.environ.get("PSS_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("PSS_SUB", "/app/pipe"))
PRISTINE = pathlib.Path(TESTS) / "pristine"
PARTS = ("cut.py", "win.py", "lay.py", "step.py", "hold.py", "weigh.py")


def sig(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def tree():
    """A fresh copy of the shipped tree with the submitted modules laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(dir=str(WORK)))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = SENT / part
        if one.is_file():
            shutil.copy(one, here / "pipe" / part)
    return here


def main():
    out = sys.argv[sys.argv.index("--out") + 1]
    seed = (WORK / "nonce").read_text(encoding="utf-8").strip()
    per = int((WORK / "per").read_text(encoding="utf-8").strip())

    here = tree()
    sys.path.insert(0, str(here))
    import run_shard

    shard = here / "shard.txt"
    work = [("hand", name, cases.ops(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)

    recs = []
    for fam, name, lines in work:
        got, err = None, None
        try:
            shard.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = run_shard.main(["run_shard.py", str(shard)])
            if rc:
                err = ["run_shard returned %r" % (rc,)]
            else:
                got = buf.getvalue().splitlines()
        except Exception:
            err = traceback.format_exc(limit=1).strip().splitlines()[-1:]
        recs.append({"fam": fam, "name": name, "sig": sig(lines), "got": got, "err": err})

    pathlib.Path(out).write_text(json.dumps(recs), encoding="utf-8")


if __name__ == "__main__":
    main()
