"""Freeze the enumerated plans' answers from the sealed model.

The old file is read first and every answer that moves is named. A contract change that was
meant to be additive and moves a frozen answer is a contract change, and it has to be seen
rather than quietly written over.

    python3 build_gt.py            report what would move
    python3 build_gt.py --write    write tests/seal/gt.json
"""
from __future__ import annotations

import json
import pathlib
import sys

import lab

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = lab.TASK / "tests" / "seal" / "gt.json"


def main(argv):
    old = {}
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))
    fresh = {name: model.expect(cases.ops(name)) for name in cases.ORDER}

    added = [n for n in fresh if n not in old]
    dropped = [n for n in old if n not in fresh]
    moved = [n for n in fresh if n in old and old[n] != fresh[n]]
    print("%d plans: %d unchanged, %d new, %d moved, %d dropped"
          % (len(fresh), len(fresh) - len(added) - len(moved), len(added), len(moved),
             len(dropped)))
    for name in moved:
        print("   MOVED %s" % name)
        for a, b in zip(old[name], fresh[name]):
            if a != b:
                print("      was %s" % a[:160])
                print("      now %s" % b[:160])
    for name in added:
        print("   new   %s" % name)
    for name in dropped:
        print("   gone  %s" % name)

    if "--write" in argv:
        text = json.dumps({n: fresh[n] for n in sorted(fresh)}, indent=1, sort_keys=True)
        GT.write_text(text + "\n", encoding="utf-8", newline="\n")
        assert "\r" not in GT.read_text(encoding="utf-8")
        print("wrote %s (%d bytes)" % (GT, GT.stat().st_size))
    elif moved or added or dropped:
        print("nothing written; pass --write when the moves above are intended")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
