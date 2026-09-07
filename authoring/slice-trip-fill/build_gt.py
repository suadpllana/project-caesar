"""Write tests/gt.json from the sealed model.

The ground truth is a tripwire, not the answer: the verifier requires the model to
reproduce it for the enumerated sessions, so a drift in oracle.py fails loudly instead of
quietly regrading the task.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "slice-trip-fill", "tests"))
sys.path.insert(0, TESTS)

import cases
import oracle


def main():
    body = {"cases": {nm: [list(r) for r in oracle.solve(cases.SESS[nm])]
                      for nm in sorted(cases.SESS)}}
    text = json.dumps(body, sort_keys=True, indent=1) + "\n"
    if "\r" in text:
        raise SystemExit("gt.json would carry a carriage return")
    out = os.path.join(TESTS, "gt.json")
    with open(out, "w", newline="\n") as fh:
        fh.write(text)
    with open(out, "rb") as fh:
        raw = fh.read()
    if b"\r" in raw:
        raise SystemExit("gt.json is not LF-only")
    print("%s: %d sessions, %d bytes" % (out, len(body["cases"]), len(raw)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
