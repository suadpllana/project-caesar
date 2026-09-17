"""Freeze the enumerated answers into tests/seal/gt.json.

Three things have to hold before a byte is written:

  * the sealed model and `brute.py` agree on every enumerated program, so the frozen answers
    are what the rules mean and not what one implementation does;
  * the reference laid over the shipped tree agrees with both;
  * every answer already frozen comes out unchanged, or the run stops and names it - a
    contract change is a contract change even when it looks like a fix.

The file is written with explicit "\\n" endings; zipcheck rejects CRLF in a shipped .json and
Git normalising on commit would hide it, because what gets packaged is the working copy.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
sys.path.insert(0, str(HERE))

import brute  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402
from cross import under  # noqa: E402
from fuzz import lay  # noqa: E402

OUT = TASK / "tests" / "seal" / "gt.json"


def main():
    was = {}
    if OUT.is_file():
        was = json.loads(OUT.read_text(encoding="utf-8"))

    tree = lay(TASK / "solution")
    progs = [cases.ops(name) for name in cases.ORDER]
    ref = under(tree, progs)

    fresh = {}
    for name, got in zip(cases.ORDER, ref):
        want = model.expect(cases.ops(name))
        if brute.expect(cases.ops(name)) != want:
            raise SystemExit("model and brute disagree on %s" % name)
        if got[0] != want:
            raise SystemExit("the reference disagrees on %s: %r vs %r" % (name, got[0], want))
        fresh[name] = want

    moved = [n for n in was if n in fresh and was[n] != fresh[n]]
    if moved:
        raise SystemExit("frozen answers moved: %s" % moved)
    print("%d programs, %d already frozen and unchanged, %d new"
          % (len(fresh), len(was), len(fresh) - len(was)))

    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    if "\r" in text:
        raise SystemExit("carriage return in the frozen answers")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
