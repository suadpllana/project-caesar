"""Freeze the enumerated answers, and prove a contract change moved nothing it should not.

Every answer already in `gt.json` has to come back byte-identical. A rule that was meant to be
additive and moves a frozen answer is a contract change, and this is where that shows up
instead of in a probe.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "claim-line-stall"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    if moved:
        print("CONTRACT CHANGE: %d frozen answers moved" % len(moved))
        for n in moved:
            print("   %s" % n)
            for a, b in zip(old[n] + [""] * len(new[n]), new[n] + [""] * len(old[n])):
                if a != b:
                    print("      was %-46s now %s" % (a, b))
        if "--accept" not in sys.argv:
            return 1
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    GT.write_text(text, encoding="utf-8", newline="\n")
    assert "\r" not in GT.read_text(encoding="utf-8"), "gt.json has CRLF"
    print("froze %d answers (%d new, %d unchanged)"
          % (len(new), len(set(new) - set(old)), len(set(old) & set(new)) - len(moved)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
