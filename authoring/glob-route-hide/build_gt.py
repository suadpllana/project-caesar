#!/usr/bin/env python3
"""Freeze the enumerated answers into tests/seal/gt.json. Never ships.

The existing file is read first and every answer that moved is reported: a change meant to be
additive that moves a frozen answer is a contract change, and it must not happen quietly.

    python3 -u authoring/glob-route-hide/build_gt.py [--force]
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
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new = {name: model.expect(cases.prog(name)) for name in cases.ORDER}
    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    for name in moved:
        print("MOVED %s: was %r now %r" % (name, old[name], new[name]))
    for name in sorted(set(new) - set(old)):
        print("added %s (%d lines)" % (name, len(new[name])))
    for name in sorted(set(old) - set(new)):
        print("dropped %s" % name)
    if moved and not force:
        print("\n%d frozen answers moved. That is a contract change: record it in STATE.md and "
              "re-run with --force." % len(moved))
        return 1
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("froze %d enumerated answers" % len(new))
    return 0


if __name__ == "__main__":
    sys.exit(main())
