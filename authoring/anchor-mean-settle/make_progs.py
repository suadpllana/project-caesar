"""Write the four programs that ship in the agent's tree.

The two wide shapes are the ones timed in authoring/anchor-mean-settle/lab/wide.py, so the
numbers quoted in the brief and the metadata are the numbers that were measured.
"""
import pathlib
import random
import sys

OUT = pathlib.Path("/home/user/project-caesar/tasks/anchor-mean-settle/environment/app_src/progs")

TINY = [
    "bulk 20 30 4",
    "tall",
    "roll 100",
    "face",
    "pass",
    "tall",
]

PAIR = [
    "bulk 12 30 4",
    "ins 3 a 460",
    "roll 240",
    "face",
    "pass",
    "seen_placeholder",
]


def pair():
    return [
        "bulk 12 30 4",
        "ins 3 a 460",
        "roll 240",
        "face",
        "pass",
        "top",
        "tall",
        "face",
        "set a 20",
        "top",
        "tall",
        "move k12 0",
        "face",
        "span 12",
        "tall",
        "pass",
        "top",
        "face",
    ]


def wide(n, ops, seed=5):
    rng = random.Random(seed)
    out = ["bulk %d 30 170" % n]
    for i in range(ops):
        k = i % 10
        if k in (0, 3, 6):
            out.append("roll %d" % rng.choice([-4000, -900, 700, 1500, 9000, 40000]))
        elif k in (1, 4, 7):
            out.append("pass")
        elif k == 2:
            out.append("top")
        elif k == 5:
            out.append("tall")
        elif k == 8:
            out.append("face")
        else:
            out.append("set k%d %d" % (rng.randrange(1, n + 1), rng.choice([20, 300])))
    out += ["top", "tall", "face"]
    return out


def deep(n, ops, seed=7):
    rng = random.Random(seed)
    out = ["bulk %d 40 90" % n]
    for _ in range(30):
        out += ["roll 5000000", "roll -700", "pass"]
    for i in range(ops):
        k = i % 8
        if k == 0:
            out.append("ins %d y%d %d" % (rng.randrange(4), i, rng.choice([10, 400])))
        elif k == 1:
            out.append("del y%d" % (i - 1))
        elif k in (2, 5):
            out.append("pass")
        elif k == 3:
            out.append("move k%d %d" % (rng.randrange(1, n + 1), rng.randrange(3)))
        elif k == 4:
            out.append("top")
        elif k == 6:
            out.append("tall")
        else:
            out.append("face")
    out += ["top", "tall", "face"]
    return out


def write(name, lines):
    text = "\n".join(lines) + "\n"
    assert "\r" not in text, name
    with open(OUT / name, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("%-10s %6d lines" % (name, len(lines)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write("tiny.txt", TINY)
    write("pair.txt", pair())
    write("wide.txt", wide(120000, 6000))
    write("deep.txt", deep(150000, 9000))


if __name__ == "__main__":
    main()
