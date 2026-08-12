"""Drives the rebuilt loop through every scenario and dumps what it reported.

This is the only place agent-supplied code is executed.  It runs as an unprivileged uid,
in its own session, under a wall-clock timeout, and writes its result into a
sandbox-writable work file.  It never sees the ground truth and never touches the reward
channel: grading happens afterwards, in a separate root process, from /tests/gt.json.

Any failure here - import error, exception, hang - leaves the work file absent or
incomplete, which the grader treats as a failed run.

Nothing the submission hands back is used as the report.  The loop is driven and then
the report is assembled here, from the runtime's own attributes and from the tokenizer
and network objects pinned the moment they were built - before a line of agent code has
run - so a report method replaced at import time, or a meter swapped out from under the
runtime part way through, changes nothing that reaches the grader.  The tokenizer's
record of what it was actually given goes over with it; tests/audit.py works the
accounting out again from that record on the privileged side.
"""

import json
import os
import sys
import traceback

APP = os.environ.get("APPDIR", "/work/app")


def collect(rt, tok, net):
    """Assemble one scenario's report from state the run did not get to choose."""
    return {
        "enc_chars": tok.n_chars,
        "enc_calls": tok.n_calls,
        "fwd": net.n_fwd,
        "trace": [str(e) for e in rt.trace],
        "ids": {str(k): [int(x) for x in v] for k, v in sorted(rt.ids.items())},
        "spans": {str(k): [[int(a), int(b)] for a, b in v]
                  for k, v in sorted(rt.spans.items())},
        "log": [[str(text), [int(x) for x in ids]] for text, ids in tok.log],
    }


def main(dest):
    sys.path.insert(0, "/tests")
    import scen

    sys.path.insert(0, APP)
    os.chdir(APP)

    out = {"reports": {}, "errors": {}}
    import build
    from loop.drv import play

    for sc in scen.SCENARIOS:
        name = sc["name"]
        try:
            rt = build.make(dict(sc.get("over") or {}))
            tok = rt.tok
            net = rt.net
            play(rt, sc["ops"])
            out["reports"][name] = collect(rt, tok, net)
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
