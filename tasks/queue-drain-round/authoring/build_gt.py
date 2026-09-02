"""Write tests/gt.json, and refuse to write one that has not been proved.

Three things have to hold before the file is written: the reference and the sealed model
agree on every enumerated stream, they agree on a run of random streams, and on small
rounds the settlement both reach is the one an exhaustive search calls the largest that
stands up. A ground truth nobody can reproduce independently is one author's arrangement
of the rules rather than the rules.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tests"))

import fuzz
import harness
import oracle
import scen


def shaped(text):
    r = oracle.play(text)
    return {"rows": [list(x) for x in r["log"]], "sheet": {k: [v[0], v[1]] for k, v in r["sheet"].items()}}


def main():
    fuzz.small(600)
    bad = fuzz.streams(400)
    if bad:
        print("the reference and the model disagree on %d streams; nothing written" % bad)
        return 1
    out = {}
    for name, text in scen.STREAMS:
        got = harness.run(str(ROOT / "solution"), text)
        want = shaped(text)
        live = {"rows": [list(x) for x in got["log"]], "sheet": {k: [v[0], v[1]] for k, v in got["sheet"].items()}}
        if oracle.rounds(live["rows"]) != oracle.rounds(want["rows"]) or live["sheet"] != want["sheet"]:
            print("the reference and the model disagree on %s; nothing written" % name)
            return 1
        out[name] = want
    (ROOT / "tests" / "gt.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", newline="\n")
    rows = sum(len(v["rows"]) for v in out.values())
    print("gt.json written: %d streams, %d rows" % (len(out), rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
