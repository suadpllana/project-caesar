"""Write the event files that ship under /app/evs. Authoring only.

tiny.txt is the document the brief's worked frame comes from (example.json, chosen by
pick_example.py); pair.txt is a small edit-heavy document; wide, deep and long are one draw each
from the verifier's own scale families, under a fixed seed that the verifier never uses.
"""
import json
import random

import lab

cases, gen, model = lab.sealed()
EVS = lab.APP / "evs"


def put(name, lines):
    text = "\n".join(lines) + "\n"
    assert "\r" not in text
    (EVS / name).write_text(text, encoding="utf-8", newline="\n")
    print("%-9s %d lines, %d bytes" % (name, len(lines), len(text)))


def main():
    ex = json.loads((lab.HERE / "example.json").read_text(encoding="utf-8"))
    put("tiny.txt", ex["doc"])
    put("pair.txt", [
        "cfg 45 1 4 6 8",
        "g 1 10 24 24 8",
        "g 2 22 6 6 3",
        "g 3 10 24 24 8",
        "go 70",
        "ins 1 2 3",
        "scroll 40",
        "del 1 1 4",
        "go 4000",
        "scroll -1",
        "ins 3 8 2",
        "size 120",
    ])
    for fam in ("wide", "deep", "long"):
        put(fam + ".txt", gen.MAKERS[fam](random.Random("shipped|" + fam)))


if __name__ == "__main__":
    main()
