"""The only place submitted code is executed.

Runs unprivileged, in a work tree the harness assembled, and writes one JSON
document to a descriptor root opened and handed down before the privileges
were dropped. Nothing here decides whether an answer is right; it records what
the board said and lets the grader, which never imports any of this, decide.
"""

import json
import os
import sys
import traceback


def collect(app, streams):
    sys.path.insert(0, app)
    from note.board import Board
    from rev.store import Store

    out = {}
    for item in streams:
        try:
            store = Store()
            for lines in item["revs"]:
                store.land(lines)
            threads, log = Board(store).build([tuple(e) for e in item["events"]])
            table = sorted([[int(t["id"]), str(t["state"]),
                             sorted(int(x) for x in t["span"])] for t in threads])
            out[item["name"]] = {
                "threads": table,
                "log": [[str(e[0])] + [int(x) for x in e[1:]] for e in log],
            }
        except Exception:
            out[item["name"]] = {"error": traceback.format_exc(limit=3)}
    return out


def main():
    app = os.environ.get("APPDIR", "/work/app")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import scen

    seed = int(os.environ.get("RUN_SEED", "0"))
    streams = (list(scen.FIXED)
               + scen.generated(int(os.environ.get("RUN_COUNT", "300")), seed)
               + scen.wide(int(os.environ.get("RUN_WIDE", "36")), seed))
    report = {"seed": seed, "boards": collect(app, streams)}
    with os.fdopen(int(os.environ["OUT_FD"]), "w") as fh:
        fh.write(json.dumps(report))


if __name__ == "__main__":
    main()
