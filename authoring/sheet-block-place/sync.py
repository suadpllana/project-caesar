"""Keep tests/pristine byte-identical to the shipped tree, and rebuild gt.json.

The pristine copy is what the verifier lays the four submitted files over, so a drift
between it and environment/app_src would let the frozen-function check fail for a reason
that has nothing to do with the submission. gt.json is written with an explicit LF newline
and asserted free of carriage returns, because nothing else in the kit reads it as text.
"""

import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TASK = HERE.parents[1] / "tasks" / "sheet-block-place"
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402

APP = TASK / "environment" / "app_src"
PRISTINE = TASK / "tests" / "pristine"
GT = TASK / "tests" / "gt.json"


def mirror():
    if PRISTINE.exists():
        shutil.rmtree(PRISTINE)
    shutil.copytree(APP, PRISTINE, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return sum(1 for _ in PRISTINE.rglob("*") if _.is_file())


def truth():
    names = sorted(cases.CASES)
    got = harness.run_with(str(TASK / "solution"), [cases.CASES[n] for n in names], limit=900)
    out = {}
    for i, name in enumerate(names):
        if isinstance(got[i], dict):
            raise SystemExit("reference raised on %s: %s" % (name, got[i]))
        want = oracle.solve(cases.CASES[name])
        if got[i] != want:
            raise SystemExit("reference and sealed model disagree on %s" % name)
        out[name] = got[i]
    return out


def main():
    files = mirror()
    body = {"cases": truth()}
    text = json.dumps(body, sort_keys=True, indent=1) + "\n"
    if "\r" in text:
        raise SystemExit("gt.json would carry a carriage return")
    with open(GT, "w", newline="\n") as fh:
        fh.write(text)
    print("pristine: %d files; gt.json: %d cases" % (files, len(body["cases"])))


if __name__ == "__main__":
    main()
