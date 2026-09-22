#!/usr/bin/env python3
"""Freeze tests/seal/gt.json from the sealed model. Never ships.

If gt.json already exists it is read first and every answer that moves is reported, so a
change to the model or to a case cannot quietly redefine correct. Pass --accept to write the
new answers anyway after reading why each one moved.

    python3 -u authoring/owed-check-rewind/build_gt.py [--accept]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, gen, model = lab.sealed()
GT = lab.TASK / "tests" / "seal" / "gt.json"


def main(argv):
    new = {name: model.expect(cases.prog(name)) for name in cases.ORDER}
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    moved = [n for n in new if n in old and old[n] != new[n]]
    added = [n for n in new if n not in old]
    dropped = [n for n in old if n not in new]
    for n in moved:
        print("MOVED   %s" % n)
        for a, b in zip(old[n], new[n]):
            if a != b:
                print("        was %r now %r" % (a, b))
    for n in added:
        print("ADDED   %s" % n)
    for n in dropped:
        print("DROPPED %s" % n)
    if (moved or dropped) and "--accept" not in argv:
        print("refusing to rewrite gt.json: answers moved; rerun with --accept once explained")
        return 1
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %d cases to %s" % (len(new), GT.relative_to(lab.ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
