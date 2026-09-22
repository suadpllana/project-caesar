"""Freeze the answers to the enumerated programs, and prove a change was additive.

gt.json is written from the sealed model and is what the grader checks the model against before
it grades anything, so a model that drifted cannot quietly redefine correct. Every run compares
the new answers with the ones already on disk: a program whose answer moved is a contract
change and is printed as one, never applied quietly.
"""
import json
import pathlib
import sys

import lab

T = lab.ROOT / "tasks" / "claim-stand-break" / "tests"
sys.path.insert(0, str(T))
sys.path.insert(0, str(T / "seal"))
import cases  # noqa: E402
import model  # noqa: E402

GT = T / "seal" / "gt.json"


def main(argv):
    force = "--force" in argv
    fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}
    ref = lab.batch(lab.tree(lab.ROOT / "tasks" / "claim-stand-break" / "solution"),
                    ["\n".join(cases.prog(n)) + "\n" for n in cases.ORDER])
    off = [n for n, want in zip(cases.ORDER, ref) if fresh[n] != want]
    if off:
        print("model and reference disagree on %s" % off)
        return 1
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))
        moved = [n for n in old if n in fresh and old[n] != fresh[n]]
        added = [n for n in fresh if n not in old]
        gone = [n for n in old if n not in fresh]
        for name in moved:
            print("CONTRACT CHANGE %s:" % name)
            for j in range(max(len(old[name]), len(fresh[name]))):
                a = old[name][j] if j < len(old[name]) else "<none>"
                b = fresh[name][j] if j < len(fresh[name]) else "<none>"
                print("   was %-26s now %s" % (a, b) if a != b else "   %s" % a)
        print("%d frozen answers held, %d moved, %d new, %d gone"
              % (len(old) - len(moved) - len(gone), len(moved), len(added), len(gone)))
        if moved and not force:
            print("refusing to overwrite a moved answer without --force")
            return 1
    GT.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                  newline="\n")
    print("wrote %s: %d programs" % (GT, len(fresh)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
