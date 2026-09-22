"""Freeze the answers for the enumerated segment files.

Every answer already in `gt.json` must come out byte-identical, so a change that is supposed to
be additive can be proved additive rather than asserted. A moved answer is printed and the file
is only rewritten when `--accept` says the contract change was intended.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import host  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    accept = "--accept" in sys.argv
    ref = host.engine(host.tree(TASK / "solution"))
    fresh = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        want = model.expect(lines)
        got = ref.run("\n".join(lines) + "\n")
        if got != want:
            raise SystemExit("reference and model disagree on %s" % name)
        fresh[name] = want

    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    moved = [k for k in old if k in fresh and old[k] != fresh[k]]
    gone = [k for k in old if k not in fresh]
    if moved or gone:
        print("answers that moved: %s" % (moved,))
        print("answers that vanished: %s" % (gone,))
        if not accept:
            raise SystemExit("not additive - rerun with --accept if the contract really changed")
    else:
        print("additive: %d frozen answers unchanged, %d new"
              % (len(old), len(fresh) - len(old)))

    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    with open(GT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s with %d programs" % (GT, len(fresh)))


if __name__ == "__main__":
    main()
