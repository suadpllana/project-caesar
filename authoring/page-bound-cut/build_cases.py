"""Write tests/cases.py from the searched cases plus the hand-written corners.

Twenty-two of the cases were found rather than chosen: for each wrong reading in emit.py,
pick.py drew small programs from the shipped families until one made that reading disagree
with the reference, then shrank it. Each is named for the reading it pins, so a failure says
which rule broke. The rest are hand-written for corners no reading reaches - a duplicate put,
a missing delete, an emptied root, and the ordinary side of the fit test, where a page that is
only within capacity once its common prefix is credited must not be cut at all.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

HAND = {
    # The ordinary side of the fit rule: eight keys sharing eight characters are 40 bytes
    # with the prefix credited and 96 without, so a page that fits must not be cut.
    "fit-ordinary": (44, 16, [("put", "marbleaa" + c) for c in "abcdefgh"]),
    # Two more of the same keys take it past the capacity and it is cut once.
    "fit-tips": (44, 16, [("put", "marbleaa" + c) for c in "abcdefghij"]),
    # A dividing string that is one character where the key it comes from is nine.
    "sep-far": (44, 16, [("put", "aaa" + c) for c in "abcde"]
                + [("put", "bbbbbbbb" + c) for c in "abcde"]),
    # The left key is a prefix of the right one, so the string is one longer than the left key.
    "sep-nested": (40, 14, [("put", "mark")] + [("put", "marketaa" + c) for c in "abcd"]),
    # A put of a key already there, and a delete of one that is not.
    "twice-missing": (40, 14, [("put", "kite"), ("put", "kite"), ("del", "kettle"),
                               ("del", "kite"), ("del", "kite")]),
    # The root leaf empties and stays; the next put lands in it again.
    "root-drains": (40, 14, [("put", "aa"), ("put", "ab"), ("del", "aa"), ("del", "ab"),
                             ("put", "ac")]),
    # A taller tree: three levels, a cut of an internal page, a new root over it.
    "tower": (32, 10, [("put", "mark" + a + b) for a in "abcd" for b in "abcd"]),
}


def lines(cap, floor, ops):
    out = ["page %d %d" % (cap, floor)]
    for kind, key in ops:
        out.append("%s %s" % (kind, key))
    return out


def main():
    picked = json.loads((HERE / "picked.json").read_text(encoding="utf-8"))
    table = {}
    for name in sorted(picked):
        cap, floor, ops = picked[name]
        table[name] = lines(cap, floor, [tuple(o) for o in ops])
    for name in sorted(HAND):
        cap, floor, ops = HAND[name]
        table[name] = lines(cap, floor, ops)
    order = sorted(table)
    body = ['"""The enumerated programs, one per graded decision and per fence.',
            "",
            "Each name says which decision its program pins. The twenty-two named for a wrong",
            "reading were found by searching the generated space for the shortest program on",
            "which that reading disagrees with the reference, so the set is known to separate",
            "them rather than assumed to. The rest cover corners no wrong reading reaches.",
            '"""',
            "",
            "PROGRAMS = {"]
    for name in order:
        body.append("    %r: [" % name)
        for line in table[name]:
            body.append("        %r," % line)
        body.append("    ],")
    body.append("}")
    body.append("")
    body.append("ORDER = [")
    for name in order:
        body.append("    %r," % name)
    body.append("]")
    body.append("")
    body.append("")
    body.append("def prog(name):")
    body.append("    return PROGRAMS[name]")
    body.append("")
    out = lab.TASK / "tests" / "cases.py"
    text = "\n".join(body)
    if "\r" in text:
        raise SystemExit("build_cases: carriage return in generated source")
    out.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %s: %d programs, %d lines" % (out, len(order), len(body)))


if __name__ == "__main__":
    main()
