"""Freeze the hand programs' answers into tests/seal/gt.json.

Every answer already in the file must come out byte-identical, so a change meant to be additive
is proved additive rather than assumed. A moved answer is reported and has to be approved by
hand before the file is written.
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "claim-cover-lift"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    fresh = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    moved = [name for name in old if name in fresh and old[name] != fresh[name]]
    dropped = [name for name in old if name not in fresh]
    if moved or dropped:
        print("CONTRACT CHANGE - answers that moved: %s; gone: %s" % (moved, dropped))
        if "--force" not in sys.argv:
            return 1
    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("%d frozen, %d unchanged, %d new"
          % (len(fresh), sum(1 for n in fresh if n in old and old[n] == fresh[n]),
             sum(1 for n in fresh if n not in old)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
