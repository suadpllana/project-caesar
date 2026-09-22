"""Freeze the answers for the enumerated trails, and say which of them moved.

The frozen file is the check on the model: the grader asserts the model still reproduces it
before it judges anything, so a model that drifted cannot quietly redefine correct. That only
works if a rebuild says what changed - an answer that moves is a contract change and has to be
a deliberate one (CLAUDE.md, 2026-09-09).

    python build_gt.py            rebuild, printing every answer that moved
    python build_gt.py --check    compare only, exit 1 if anything moved
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, _gen, model = lab.sealed()
GT = lab.TASK / "tests" / "seal" / "gt.json"


def main():
    was = {}
    if GT.is_file():
        was = json.loads(GT.read_text(encoding="utf-8"))
    now = {name: model.expect(cases.prog(name)) for name in cases.ORDER}

    moved = [n for n in sorted(set(was) & set(now)) if was[n] != now[n]]
    fresh = sorted(set(now) - set(was))
    gone = sorted(set(was) - set(now))
    for name in moved:
        print("CHANGED %s" % name)
        print("    was %s" % " | ".join(was[name]))
        print("    now %s" % " | ".join(now[name]))
    for name in fresh:
        print("new     %s" % name)
    for name in gone:
        print("dropped %s" % name)
    print("%d frozen, %d moved, %d new, %d dropped"
          % (len(now), len(moved), len(fresh), len(gone)))

    if "--check" in sys.argv:
        return 1 if (moved or fresh or gone) else 0
    body = json.dumps(now, indent=1, sort_keys=True) + "\n"
    assert "\r" not in body
    GT.write_text(body, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
