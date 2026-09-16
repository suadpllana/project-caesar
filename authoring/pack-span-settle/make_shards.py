"""Build the shards that ship in the agent's tree.

`wide.txt` and `deep.txt` are drawn from the same makers the verifier uses, at a fixed seed, so
the sizes the agent times against the limit are the sizes it is graded at. They carry no
answers: a shard is a list of records and three settings, and nothing in it says what the
engine should print.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tasks" / "pack-span-settle" / "tests"))

import gen  # noqa: E402
import random  # noqa: E402

OUT = ROOT / "tasks" / "pack-span-settle" / "environment" / "app_src" / "shards"

HAND = {
    "tiny.txt": [
        "width 8", "span 2", "floor 3",
        "rec a 5 2", "rec b 6 3", "seal",
    ],
    "carry.txt": [
        "width 12", "span 2", "floor 14",
        "rec a 7 4", "rec b 1 9", "rec c 26 5", "rec d 3 2",
        "width 9", "rec e 11 6", "floor 40", "rec f 20 1", "seal",
    ],
}


def write(name, lines):
    path = OUT / name
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    assert "\r" not in path.read_text(encoding="utf-8"), name
    print("%-10s %d lines" % (name, len(lines)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, lines in HAND.items():
        write(name, lines)
    write("wide.txt", gen.MAKERS["wide"](random.Random("shipped|wide")) )
    write("deep.txt", gen.MAKERS["deep"](random.Random("shipped|deep")) )


if __name__ == "__main__":
    main()
