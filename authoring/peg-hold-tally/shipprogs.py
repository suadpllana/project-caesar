"""Write the programs that ship in the environment. Authoring only."""
import pathlib
import sys

sys.path.insert(0, "../../tasks/peg-hold-tally/tests")
import gen  # noqa: E402

OUT = pathlib.Path("../../tasks/peg-hold-tally/environment/app_src/progs")

TINY = """vol v1
set v1 1
set v1 2
peg p1 v1
set v1 1
tally p1
trim
shed p1
trim
"""


def put(name, lines):
    text = "\n".join(lines) + "\n" if isinstance(lines, list) else lines
    assert "\r" not in text
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    print("%-10s %7d lines" % (name, text.count("\n")))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    put("tiny.txt", TINY)
    put("runs.txt", gen.small("mix", "shipped-runs", 140, 7, 3))
    put("wide.txt", gen.wide("shipped-wide"))
    put("crop.txt", gen.crop("shipped-crop"))
    put("fan.txt", gen.fan("shipped-fan"))


main()
