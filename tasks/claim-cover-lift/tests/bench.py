"""Stage one: run the submitted service and write down what it printed.

Nothing here decides anything. It runs as the sandbox uid, with the model and the frozen answers
out of reach, and everything it produces is treated by the grader as hostile input. A crash, a
hang or a silent exit loses the record, and a lost record fails the task - there is no path where
saying nothing is better than saying something wrong.

The clock the platform puts on this process is the task's own execution limit. Three of the
eleven program families exist for it: a box left holding forty thousand slot claims with a line
of readers waiting on the box itself, five hundred boxes with standing lines while other jobs
take and drop around them, and a queue of readers behind the holder in every box.
"""
import hashlib
import json
import os
import pathlib
import shutil
import sys
import traceback

TESTS = pathlib.Path(os.environ.get("CCL_TESTS", "/tests"))
YARD = pathlib.Path(os.environ.get("CCL_WORK", "/work"))
SENT = pathlib.Path(os.environ.get("CCL_SUB", "/app/hb"))
MINE = ("book.py", "fit.py", "line.py", "lift.py", "snarl.py", "door.py")

sys.path.insert(0, str(TESTS))

import cases  # noqa: E402
import gen  # noqa: E402


def fingerprint(body):
    """What the grader checks the program against, so a rewritten program cannot pass."""
    return hashlib.blake2s("\x1f".join(body).encode("utf-8")).hexdigest()


def staged():
    """The shipped tree with the submitted files laid over it, under a directory of our own."""
    room = YARD / "app"
    if room.exists():
        shutil.rmtree(room)
    shutil.copytree(TESTS / "pristine", room)
    for name in MINE:
        sent = SENT / name
        if sent.is_file():
            shutil.copy(sent, room / "hb" / name)
    return room


def exam():
    seed = (YARD / "nonce").read_text(encoding="utf-8").strip()
    per = int((YARD / "per").read_text(encoding="utf-8").strip())
    out = [("hand", name, cases.ops(name)) for name in cases.ORDER]
    out.extend(gen.programs(seed, per))
    return out


def main():
    where = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
    room = staged()
    sys.path.insert(0, str(room))
    import step
    from hb import desk

    ran, broke = {}, {}
    for _family, name, body in exam():
        try:
            spot = desk.Store()
            for one in body:
                step.ex(spot, tuple(one.split()))
            ran[name] = {"sig": fingerprint(body), "out": spot.out}
        except Exception:
            broke[name] = traceback.format_exc(limit=1).strip().splitlines()[-1]

    where.write_text(json.dumps({"ran": ran, "broke": broke}), encoding="utf-8")


if __name__ == "__main__":
    main()
