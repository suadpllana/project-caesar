"""Freeze tests/seal/gt.json from the sealed model, one printout per hand journal.

Reads the existing gt.json first and refuses to change an answer already frozen unless the
journal text itself changed (CLAUDE.md: build_gt proves additivity only if it reads the old
file first). Writes LF only and checks no CR survives.

    python3 authoring/journal-gap-mend/build_gt.py [--allow-change NAME ...]
"""
import json
import pathlib
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "journal-gap-mend"
SEAL = TASK / "tests" / "seal"
sys.path.insert(0, str(SEAL))

import cases  # noqa: E402
import model  # noqa: E402


def main(argv):
    allow = set(argv[argv.index("--allow-change") + 1:]) if "--allow-change" in argv else set()
    path = SEAL / "gt.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    new = {}
    changed = []
    for name in cases.ORDER:
        new[name] = model.expect(cases.text(name))
        if name in old and old[name] != new[name]:
            changed.append(name)
    bad = [n for n in changed if n not in allow]
    if bad:
        print("frozen answers would change for %s; pass --allow-change to accept" % bad)
        return 1
    text = json.dumps(new, indent=1, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    assert "\r" not in path.read_bytes().decode("utf-8")
    kept = sum(1 for n in new if n in old and old[n] == new[n])
    print("gt.json: %d answers (%d unchanged, %d new, %d changed on purpose)" % (
        len(new), kept, sum(1 for n in new if n not in old), len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
