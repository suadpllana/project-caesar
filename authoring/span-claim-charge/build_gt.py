"""Freeze the enumerated answers from the sealed model, additively.

Every answer already in gt.json has to come out byte-identical, or the contract moved and
the run says so by name. New cases are added; nothing already frozen is rewritten without
the change being printed.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "span-claim-charge"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

OUT = TASK / "tests" / "seal" / "gt.json"


def main():
    old = {}
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))
    fresh = {}
    moved = []
    for name in cases.ORDER:
        fresh[name] = model.expect(cases.ops(name))
        if name in old and old[name] != fresh[name]:
            moved.append(name)
    added = [n for n in fresh if n not in old]
    dropped = [n for n in old if n not in fresh]
    if moved:
        print("CONTRACT CHANGE - these frozen answers moved: %s" % ", ".join(sorted(moved)))
    print("frozen %d, added %d, dropped %d, moved %d"
          % (len(fresh), len(added), len(dropped), len(moved)))
    body = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return 1 if moved else 0


if __name__ == "__main__":
    sys.exit(main())
