"""Write the example programs that ship under /app/progs.

The two scale examples are built by the same generator the verifier uses, at the size the brief
states, so what the agent times is the size it is graded at. Everything is written with LF and
checked for a stray carriage return, because a generated file is the one place nothing else
looks.
"""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tasks/queue-hold-drop/tests"))
import gen  # noqa: E402

OUT = ROOT / "tasks/queue-hold-drop/environment/app_src/progs"


def put(name, lines):
    text = "".join(line + "\n" for line in lines)
    assert "\r" not in text
    path = OUT / name
    path.write_text(text, encoding="utf-8", newline="\n")
    print("%-10s %7d lines" % (name, len(lines)))


TINY = """
oth new q1 -
oth new q2 q1
oth new q3 q1
set q3 k 22
set q3 w -9
oth cut q3
ask q3
snd
ok
no
ask q2
all
ask q3
"""

PAIR = """
oth new q1 -
new a q1
new b a
set b w 6
set q1 h 2
snd
ask b
ok
snd
ok
ok
ask b
all
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    put("tiny.txt", [l for l in TINY.strip().splitlines() if l.strip()])
    put("pair.txt", [l for l in PAIR.strip().splitlines() if l.strip()])
    put("wide.txt", gen.build("wide", random.Random("ship|wide"), small=False))
    put("deep.txt", gen.build("deep", random.Random("ship|deep"), small=False))


if __name__ == "__main__":
    main()
