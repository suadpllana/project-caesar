"""Drives the rebuilt engine through every scenario and dumps what it reported.

This is the only place agent-supplied code is executed.  It runs as an unprivileged uid,
in its own process group, under a wall-clock timeout, and writes its result into a
sandbox-writable work file.  It never sees the ground truth and never touches the reward
channel: grading happens afterwards, in a separate root process, from /tests/gt.json.

Any failure here - import error, exception, hang - leaves the work file absent or
incomplete, which the grader treats as a failed run.
"""

import json
import os
import sys
import traceback

APP = os.environ.get("APPDIR", "/work/app")


def main(dest):
    sys.path.insert(0, "/tests")
    import scen

    sys.path.insert(0, APP)
    os.chdir(APP)

    out = {"reports": {}, "errors": {}}
    import build
    from runtime.drv import play

    for sc in scen.SCENARIOS:
        name = sc["name"]
        try:
            eng = build.make(dict(sc.get("over") or {}))
            out["reports"][name] = play(eng, sc["ops"])
        except Exception:
            out["errors"][name] = traceback.format_exc()[-2000:]
        with open(dest, "w") as f:
            json.dump(out, f)
    return 0


if __name__ == "__main__":
    target = sys.argv[1]
    try:
        sys.exit(main(target))
    except Exception:
        with open(target, "w") as fh:
            json.dump({"reports": {}, "errors": {"fatal": traceback.format_exc()[-2000:]}}, fh)
        sys.exit(1)
