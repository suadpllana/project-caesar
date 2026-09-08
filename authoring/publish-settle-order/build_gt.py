"""Freeze the enumerated answers into tests/gt.json.

The truth is taken from the sealed model, then checked against the reference before it is
written, so the file can only be created when the two agree. Written with an explicit newline so
no platform can put CR bytes into a shipped artifact.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
TESTS = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "publish-settle-order" / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))
import cases  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402

lb = lab.Lab(lab.TASK / "solution")
truth = {}
for name in cases.ORDER:
    want = model.expect(cases.ops(name))
    got = lb.run(cases.ops(name))
    if got != want:
        raise SystemExit("reference and model disagree on %s:\n  ref %s\n  mod %s" % (name, got, want))
    truth[name] = want
lb.close()

text = json.dumps(truth, indent=1, sort_keys=True) + "\n"
if "\r" in text:
    raise SystemExit("CR byte in gt.json")
out = lab.TASK / "tests" / "seal" / "gt.json"
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("wrote %s: %d cases, %d lines of truth" % (out, len(truth), sum(len(v) for v in truth.values())))
