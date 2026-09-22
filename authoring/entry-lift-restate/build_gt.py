import pathlib as _pl
import sys as _sys

_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent
                        / "tasks" / "entry-lift-restate" / "tests"))
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent
                        / "tasks" / "entry-lift-restate" / "tests" / "seal"))

"""Freeze the answers to the enumerated programs, and prove nothing already frozen moved.

Every answer written here has been produced by three implementations that agree: the
specification in `naive.py`, the sealed model, and the reference assembled over the shipped
tree. An answer that only one of them produces is not frozen.

The additivity check matters more than the freezing. A rule added later must leave every
already-frozen answer byte-identical unless the change really is a contract change, and
without this check that means re-deriving thirty-odd traces by hand and hoping.

    python build_gt.py            check, and write only if every answer is unchanged
    python build_gt.py --accept   write anyway, after reporting which answers moved
"""

import json
import sys

import cases
import lab
import model
import naive

GT = _pl.Path(__file__).resolve().parent.parent.parent \
    / "tasks" / "entry-lift-restate" / "tests" / "seal" / "gt.json"


def main(argv):
    ref = lab.reference()
    fresh, split = {}, []
    for name in cases.ORDER:
        lines = cases.prog(name)
        text = "\n".join(lines) + "\n"
        want = naive.run(text)
        got = model.expect(lines)
        mine = ref.run(text)
        if not (want == got == mine):
            split.append(name)
        fresh[name] = want

    if split:
        print("the three implementations disagree on: %s" % ", ".join(split))
        return 2

    moved, added, dropped = [], [], []
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))
        for name in sorted(set(old) | set(fresh)):
            if name not in old:
                added.append(name)
            elif name not in fresh:
                dropped.append(name)
            elif old[name] != fresh[name]:
                moved.append(name)

    print("%d enumerated programs, settled the same way by three implementations"
          % len(fresh))
    if added:
        print("new: %s" % ", ".join(added))
    if dropped:
        print("gone: %s" % ", ".join(dropped))
    if moved:
        print("CONTRACT CHANGE - these frozen answers moved: %s" % ", ".join(moved))
        for name in moved:
            print("   %s\n     was %s\n     now %s" % (name, old[name], fresh[name]))
        if "--accept" not in argv:
            print("nothing written; re-run with --accept once the change is deliberate")
            return 1

    GT.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n",
                  encoding="utf-8", newline="\n")
    raw = GT.read_text(encoding="utf-8")
    assert "\r" not in raw, "gt.json picked up a carriage return"
    print("wrote %s" % GT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
