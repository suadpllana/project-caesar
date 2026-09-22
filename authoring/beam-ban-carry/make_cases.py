"""Write tests/cases.py from the searched wrong-reading cases and the written ordinary ones.

Every file a generator writes is pinned to LF and checked for a stray carriage return before
it lands (CLAUDE.md, 2026-09-06: CRLF again, in the file no gate reads as text).
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import hand  # noqa: E402

TASK = HERE.parent.parent / "tasks" / "beam-ban-carry"
OUT = TASK / "tests" / "cases.py"

HEAD = '''"""The enumerated programs: one per graded decision, and the ordinary side of each fence.

Every name under `WRONG` is the name of a wrong reading of the contract, and the program is
the smallest one found that the reading gets wrong: a failure here says which rule broke
rather than "some of the generated programs differ". The names under `PLAIN` are written
rather than searched, and each pins that something does *not* happen - no refusal, no
eviction, no early halt, nothing carried from the request before.

Frozen answers for all of them live in `seal/gt.json`.
"""

WRONG = {
'''
MID = '''}

PLAIN = {
'''
TAIL = '''}

PROGS = dict(WRONG)
PROGS.update(PLAIN)
ORDER = sorted(PROGS)


def prog(name):
    return PROGS[name].strip("\\n").split("\\n")
'''


def block(items, notes):
    out = []
    for name in sorted(items):
        note = notes.get(name)
        if note:
            out.append("    # %s\n" % note)
        body = items[name].strip("\n")
        out.append('    "%s": """%s""",\n' % (name, body))
    return "".join(out)


def main():
    hunted = json.loads((HERE / "hunted.json").read_text(encoding="utf-8"))
    wrong = {name: "\n".join(lines) for name, lines in hunted.items()}
    missing = sorted(set(emit.READINGS) - set(wrong))
    if missing:
        raise SystemExit("no case for readings: %s - run hunt.py" % ", ".join(missing))
    text = HEAD + block(wrong, emit.NOTES) + MID + block(hand.HAND, {}) + TAIL
    if "\r" in text:
        raise SystemExit("carriage return in generated cases.py")
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %s: %d wrong-reading cases, %d ordinary" % (OUT, len(wrong), len(hand.HAND)))


if __name__ == "__main__":
    main()
