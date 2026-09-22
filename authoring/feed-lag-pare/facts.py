#!/usr/bin/env python3
"""Re-derive every number and every quoted line in the shipped prose from the code.

Counts drift with the generator, and prose is the last thing anyone re-reads. This checks the
brief and the task.toml explanations against what actually ships: the sample programs' sizes,
the size of the graded population, the execution limit, the counts of cheats and readings, and
the worked example - both the line the shipped service prints and the line the reference does.

    python3 -u authoring/feed-lag-pare/facts.py
"""
import collections
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

BRIEF = (lab.TASK / "instruction.md").read_text(encoding="utf-8")
TOML = (lab.TASK / "task.toml").read_text(encoding="utf-8")
WORDS = {
    "twelve hundred": 1200, "sixty-eight thousand": 68000, "eleven hundred": 1100,
    "twenty-four thousand": 24000, "hundred and thirty": 130, "four hundred": 400,
    "thirty-three": 33, "three programs": 3, "twenty-four keys": 24,
}


def shape(name):
    kinds = collections.Counter()
    keys = set()
    for line in (lab.SRC / "progs" / name).read_text(encoding="utf-8").splitlines():
        bits = line.split()
        if not bits:
            continue
        kinds[bits[0]] += 1
        if bits[0] in ("set", "add", "del"):
            keys.add(int(bits[1]))
    return {"keys": len(keys), "entries": kinds["set"] + kinds["add"] + kinds["del"],
            "pares": kinds["pare"], "marks": kinds["mark"]}


def main():
    cases, gen, _model = lab.sealed()
    bad = []

    def want(claim, ok):
        print("   %-58s %s" % (claim, "ok" if ok else "WRONG"))
        if not ok:
            bad.append(claim)

    wide, deep = shape("wide.txt"), shape("deep.txt")
    print("wide.txt %s" % wide)
    print("deep.txt %s" % deep)
    want("wide: twelve hundred keys", wide["keys"] == WORDS["twelve hundred"])
    want("wide: sixty-eight thousand entries",
         WORDS["sixty-eight thousand"] <= wide["entries"] < 69000)
    want("wide: eleven hundred pares", 1100 <= wide["pares"] < 1200)
    want("deep: twenty-four keys", deep["keys"] == WORDS["twenty-four keys"])
    want("deep: twenty-four thousand entries", deep["entries"] == WORDS["twenty-four thousand"])
    want("deep: a mark every hundred and thirty entries",
         deep["marks"] == deep["entries"] // WORDS["hundred and thirty"])

    wall = re.search(r"^wall=(\d+)$", (lab.TASK / "tests" / "test.sh").read_text(), re.M)
    per = re.search(r"^per=(\d+)$", (lab.TASK / "tests" / "test.sh").read_text(), re.M)
    want("the brief's 60 seconds is the harness wall clock",
         wall and wall.group(1) == "60" and "inside 60 seconds" in BRIEF)

    made = gen.programs("facts", int(per.group(1)))
    small = sum(1 for _f, _n, _l in made) - 2 * gen.BIG
    want("three programs of each large size", gen.BIG == WORDS["three programs"])
    want("four hundred smaller ones", small == WORDS["four hundred"])
    want("thirty-three written by hand", len(cases.ORDER) == WORDS["thirty-three"])
    want("four hundred and six generated, four hundred and thirty-nine graded",
         len(made) == 406 and len(made) + len(cases.ORDER) == 439
         and "four hundred and six" in TOML.lower()
         and "four hundred and thirty-nine" in TOML.lower())

    for build in emit.READING_BUILDERS + emit.OTHER_BUILDERS + emit.PROBE_BUILDERS:
        build()
    cheats = sorted((lab.TASK / "cheat").glob("cheat-*.sh"))
    want("thirty-eight cheats", len(cheats) == 38 and "Thirty-eight cheats" in TOML)
    want("twenty-four wrong readings",
         len(emit.READINGS) == 24 and "Twenty-four are" in TOML)
    want("twelve families", len(gen.FAMILIES) == 12 and "twelve families" in TOML)

    tiny = (lab.SRC / "progs" / "tiny.txt").read_text(encoding="utf-8")
    shipped = lab.run_text(lab.tree(None), tiny)
    right = lab.run_text(lab.tree(lab.SOL), tiny)
    print("   tiny.txt shipped -> %s" % shipped[-1])
    print("   tiny.txt correct -> %s" % right[-1])
    want("the brief quotes what the shipped service prints",
         ("`%s`" % shipped[-1]) in BRIEF)
    want("the brief quotes what it should read", ("`%s`" % right[-1]) in BRIEF)

    print("\n%d claim(s) wrong" % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
