"""Write tests/gt.json, and refuse to write one that has not been proved.

The answers come from the reference, and they are only written once the reference
and the sealed model have been driven over a large random set and agreed on every
row of every trace. The two were written from the same specification by different
routes, so agreement is evidence about the specification rather than about one
author's habits, and it is the only reason to believe a ground truth produced by
the same code that will be graded against it.

Every writer here passes newline="\n" explicitly. Path.write_text on Windows opens
in text mode and would put CRLF into a file that is copied into the verifier image
and executed there.
"""

import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import cases
import gen
import harness
import oracle

PROVE = 900


def prove(app):
    bad = 0
    for name, p in gen.batch("prove", PROVE):
        text = gen.text(p)
        a = harness.drive(app, text)
        b = oracle.play(text)
        if a["tr"] != b["tr"] or a["sk"] != b["sk"]:
            print("MISMATCH on %s" % name)
            bad += 1
            if bad > 2:
                break
    return bad


def main():
    app = harness.tree(str(ROOT / "solution"))
    try:
        bad = prove(app)
        if bad:
            raise SystemExit("the reference and the model disagree on %d plans; "
                             "no ground truth written" % bad)
        out = {}
        for name in sorted(cases.PLANS):
            text = cases.PLANS[name]
            a = harness.drive(app, text)
            b = oracle.play(text)
            if a["tr"] != b["tr"] or a["sk"] != b["sk"]:
                raise SystemExit("the reference and the model disagree on %s" % name)
            out[name] = {"tr": [list(r) for r in a["tr"]],
                         "sk": dict((k, list(v)) for k, v in a["sk"].items())}
    finally:
        shutil.rmtree(app.parent, ignore_errors=True)
    path = ROOT / "tests" / "gt.json"
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, sort_keys=True, indent=1)
        fh.write("\n")
    rows = sum(len(v["tr"]) for v in out.values())
    print("proved on %d generated plans; wrote %d plans, %d rows"
          % (PROVE, len(out), rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
