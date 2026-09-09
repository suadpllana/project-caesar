"""Freeze the enumerated answers into tests/seal/gt.json.

The truth is taken from the sealed model, then checked against the reference before it is
written, so the file can only be created when the two agree. Written with an explicit newline so
no platform can put CR bytes into a shipped artifact.

Every answer already in the file is checked against the new truth before the file is replaced.
A contract change that is meant to be additive - a new op, a new rule that only new programs
exercise - must leave every frozen answer byte-identical, and this is where that is proved rather
than assumed. Pass `--allow-change name` for a case whose answer is meant to move, and say why in
STATE.md.
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

out = lab.TASK / "tests" / "seal" / "gt.json"
argv = sys.argv[1:]
allowed = set()
while "--allow-change" in argv:
    i = argv.index("--allow-change")
    allowed.add(argv[i + 1])
    del argv[i:i + 2]

old = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}

lb = lab.Lab(lab.TASK / "solution")
truth = {}
for name in cases.ORDER:
    want = model.expect(cases.ops(name))
    got = lb.run(cases.ops(name))
    if got != want:
        raise SystemExit("reference and model disagree on %s:\n  ref %s\n  mod %s" % (name, got, want))
    truth[name] = want
lb.close()

moved = [n for n in old if n in truth and old[n] != truth[n] and n not in allowed]
gone = [n for n in old if n not in truth]
if moved:
    for n in moved:
        print("CHANGED %s\n  was %s\n  now %s" % (n, old[n], truth[n]))
    raise SystemExit("%d frozen answers changed; the change is not additive" % len(moved))
if gone:
    raise SystemExit("frozen cases removed: %s" % ", ".join(sorted(gone)))

text = json.dumps(truth, indent=1, sort_keys=True) + "\n"
if "\r" in text:
    raise SystemExit("CR byte in gt.json")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
kept = sum(1 for n in old if n in truth and old[n] == truth[n])
print("wrote %s: %d cases (%d frozen answers held, %d new), %d lines of truth"
      % (out, len(truth), kept, len(truth) - len(old), sum(len(v) for v in truth.values())))
