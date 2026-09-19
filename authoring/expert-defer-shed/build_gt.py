#!/usr/bin/env python3
"""Freeze the enumerated answers into tests/seal/gt.json. Never ships.

It reads the existing file first and reports every answer that moved. A rule change that was
meant to be additive and moves a frozen answer is a contract change, and the point of this
script is that it cannot happen quietly.

    python3 -u authoring/expert-defer-shed/build_gt.py [--force]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

GT = lab.TASK / "tests" / "seal" / "gt.json"


def main():
    cases, _gen, model = lab.sealed()
    force = "--force" in sys.argv[1:]

    old = {}
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))

    new = {name: model.expect(cases.prog(name)) for name in cases.ORDER}

    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    added = sorted(set(new) - set(old))
    dropped = sorted(set(old) - set(new))

    for name in moved:
        print("MOVED %s" % name)
        for a, b in zip(old[name], new[name]):
            if a != b:
                print("   was %r now %r" % (a, b))
                break
        if len(old[name]) != len(new[name]):
            print("   %d lines now %d" % (len(old[name]), len(new[name])))
    for name in added:
        print("added %s (%d lines)" % (name, len(new[name])))
    for name in dropped:
        print("dropped %s" % name)

    if moved and not force:
        print("\n%d frozen answers moved. That is a contract change: say so in STATE.md and "
              "re-run with --force." % len(moved))
        return 1

    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("\nfroze %d enumerated answers" % len(new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
