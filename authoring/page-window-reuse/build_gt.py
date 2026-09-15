"""Freeze the answers for the enumerated programs, and prove a change was additive.

gt.json is written from the sealed model. Every answer already on disk must come out
byte-identical unless the contract itself changed: a rule that moves a frozen answer is a
contract change and is reported rather than quietly written.

    python build_gt.py [--force]
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "page-window-reuse"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

OUT = TASK / "tests" / "seal" / "gt.json"


def main():
    force = "--force" in sys.argv
    old = {}
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))
    new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    moved = [n for n in sorted(set(old) & set(new)) if old[n] != new[n]]
    if moved and not force:
        print("CONTRACT CHANGE: %d frozen answers moved: %s" % (len(moved), moved[:6]))
        print("re-run with --force only if the contract really changed, and say so in STATE.md")
        return 1
    OUT.write_text(json.dumps(new, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    assert b"\r" not in OUT.read_bytes()
    print("froze %d programs (%d unchanged, %d new, %d moved)" % (
        len(new), len(set(old) & set(new)) - len(moved),
        len(set(new) - set(old)), len(moved)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
