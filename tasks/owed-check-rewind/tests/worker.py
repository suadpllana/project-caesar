"""Stage one: run the submitted executor over every graded program. Trusted for nothing.

This is the only process that executes the agent's code, and it runs as an unprivileged user
under the wall clock that is also the task's execution limit. It decides nothing. It builds a
fresh copy of the verifier's own pristine tree, lays the six collected files from /app/tx over
it - nothing else from the agent is read, and a file the agent added anywhere is never copied -
runs every enumerated and generated program through the unchanged driver, and writes down what
each one printed. Stage two reads that record as hostile input.

Anything that goes wrong here - an exception, a hang, a process killed at the clock - leaves no
record or a record with holes, and either one is a failure.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

TESTS = Path(os.environ.get("OCR_TESTS", "/tests"))
SUBMITTED = Path(os.environ.get("OCR_SUBMITTED", "/app/tx"))
COLLECTED = ("heap.py", "act.py", "chk.py", "owe.py", "sp.py", "sess.py")
BIG = 5000      # a printout longer than this many lines is recorded by digest only

sys.path.insert(0, str(TESTS))
import cases  # noqa: E402
import gen  # noqa: E402


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def overlay(scratch):
    """The pristine tree with the collected files laid over it, in a fresh directory."""
    room = Path(tempfile.mkdtemp(prefix="run-", dir=str(scratch)))
    app = room / "app"
    shutil.copytree(TESTS / "pristine", app)
    for name in COLLECTED:
        src = SUBMITTED / name
        if src.is_file():
            shutil.copyfile(src, app / "tx" / name)
    return app


def main():
    out = Path(sys.argv[1])
    scratch = out.parent
    seed = (scratch / "seed").read_text(encoding="utf-8").strip()
    each = int((scratch / "each").read_text(encoding="utf-8").strip())

    app = overlay(scratch)
    sys.path.insert(0, str(app))
    import run_tx

    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work.extend(gen.programs(seed, each))

    record = []
    for fam, name, lines in work:
        entry = {"fam": fam, "name": name, "prog": digest(lines)}
        try:
            got = run_tx.run("\n".join(lines) + "\n")
            got = [str(x) for x in got]
            entry["n"] = len(got)
            entry["digest"] = digest(got)
            if len(got) <= BIG:
                entry["lines"] = got
        except Exception:
            entry["error"] = traceback.format_exc(limit=2).strip().splitlines()[-1][:300]
        record.append(entry)

    tmp = out.with_suffix(".part")
    tmp.write_text(json.dumps(record), encoding="utf-8")
    tmp.replace(out)


if __name__ == "__main__":
    main()
