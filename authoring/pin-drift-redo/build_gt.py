"""Freeze the hand-case answers, after three implementations agree on every one of them.

Additivity: when tests/seal/gt.json already exists, every answer it holds must come out
byte-identical, or the run stops and names the case. A contract change that moves a frozen
answer is a contract change, and it is reported here rather than discovered later.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "pin-drift-redo"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "proto"))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402
import naive  # noqa: E402

OUT = TASK / "tests" / "seal" / "gt.json"


def main():
    progs = [(name, cases.prog(name)) for name in cases.ORDER]
    ran = lab.run(progs, over=TASK / "solution")
    fresh = {}
    for name, lines in progs:
        want = model.expect(lines)
        ref, err = ran[name]
        nai = naive.run("\n".join(lines) + "\n")
        if err:
            raise SystemExit("reference raised on %s: %s" % (name, err))
        if ref != want:
            raise SystemExit("reference and model differ on %s:\n  ref   %s\n  model %s"
                             % (name, ref, want))
        if nai != want:
            raise SystemExit("naive engine and model differ on %s:\n  naive %s\n  model %s"
                             % (name, nai, want))
        fresh[name] = want

    if OUT.is_file():
        was = json.loads(OUT.read_text(encoding="utf-8"))
        moved = [n for n in was if n in fresh and was[n] != fresh[n]]
        gone = [n for n in was if n not in fresh]
        if moved or gone:
            raise SystemExit("frozen answers moved: %s; frozen cases dropped: %s"
                             % (moved, gone))
        print("additive: %d frozen answers unchanged" % len(was))

    body = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    if "\r" in body:
        raise SystemExit("carriage return in gt.json")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("froze %d cases into %s" % (len(fresh), OUT))
    for name in cases.ORDER:
        print("  %-20s %s" % (name, " | ".join(fresh[name]) or "(prints nothing)"))


if __name__ == "__main__":
    main()
