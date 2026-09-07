"""Freeze the enumerated programs' answers into tests/gt.json from the sealed model.

Written before tests/test_outputs.py, which asserts the model still reproduces this file before
it grades anything - so a later change to the model that would quietly redefine correct fails
the run instead.
"""
import json
import pathlib
import sys

import harness

sys.path.insert(0, str(harness.TASK / "tests"))
import cases  # noqa: E402
import model  # noqa: E402

OUT = harness.TASK / "tests" / "gt.json"


def main():
    truth = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    body = json.dumps(truth, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    pathlib.Path(OUT).write_text(body, encoding="utf-8", newline="\n")
    print("wrote %s: %d programs" % (OUT.name, len(truth)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
