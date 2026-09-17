"""Freeze the enumerated answers, and prove that a contract change did not move the old ones.

`gt.json` is what the grader checks the sealed model against before it grades anything, so it
has to be built from the model and then left alone. Every run compares what the model says now
with what the file already holds: an answer that moved is a contract change and is reported by
name, never written over silently.

    python3 authoring/queue-hold-drop/build_gt.py [--write]
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TESTS = ROOT / "tasks/queue-hold-drop/tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TESTS / "seal" / "gt.json"


def main(argv):
    fresh = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    moved = [n for n in sorted(set(old) & set(fresh)) if old[n] != fresh[n]]
    added = sorted(set(fresh) - set(old))
    lost = sorted(set(old) - set(fresh))
    for name in moved:
        print("MOVED %s" % name)
        print("   was %s" % old[name])
        print("   now %s" % fresh[name])
    for name in added:
        print("new   %s" % name)
    for name in lost:
        print("gone  %s" % name)
    if not moved and not added and not lost:
        print("%d answers unchanged" % len(fresh))
    if "--write" in argv:
        GT.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
        assert "\r" not in GT.read_text(encoding="utf-8")
        print("wrote %s (%d answers)" % (GT.relative_to(ROOT), len(fresh)))
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
