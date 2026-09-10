"""Freeze the hand cases' answers from the sealed model, additively.

Every name already in gt.json has to come out byte-identical, so a rebuild can add cases
but can never quietly move an answer that was frozen before the grading file was written.

    python3 authoring/claim-raise-cut/build_gt.py [--allow-change name ...]
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "claim-raise-cut"
TESTS = TASK / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

GT = TESTS / "seal" / "gt.json"


def main(argv):
    allow = set(argv[argv.index("--allow-change") + 1:]) if "--allow-change" in argv else set()
    old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
    new = {}
    for name, steps in cases.programs():
        new[name] = model.trace(steps)
    moved = [n for n in old if n in new and old[n] != new[n] and n not in allow]
    gone = [n for n in old if n not in new]
    if moved or gone:
        raise SystemExit("frozen answers would change: moved=%s gone=%s" % (moved, gone))
    added = [n for n in new if n not in old]
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("gt.json: %d cases, %d kept byte-identical, %d added%s"
          % (len(new), len(new) - len(added), len(added), (": " + ", ".join(added)) if added else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
