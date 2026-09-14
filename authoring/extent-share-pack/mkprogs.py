"""Write the four programs that ship in the agent tree.

tiny  the one the brief quotes: an extent left under half occupied is rewritten
pair  two volumes on one extent, so the drop question has something to say
wide  a large store asked many questions: the family that kills a per-query walk
deep  a large store rewritten a few thousand times: the family that kills a per-rewrite walk
"""
import pathlib

PROGS = pathlib.Path(__file__).resolve().parent.parent.parent / \
    "tasks" / "extent-share-pack" / "environment" / "app_src" / "progs"


def write(name, lines):
    PROGS.mkdir(parents=True, exist_ok=True)
    p = PROGS / name
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(x + "\n" for x in lines))
    assert "\r" not in p.read_text(encoding="utf-8")
    return len(lines)


def tiny():
    return ["vol a", "fil a p 3", "wr a p 0 2", "tr a p 1 2", "tot"]


def pair():
    return [
        "vol a", "fil a p 8", "wr a p 0 5",
        "vol b", "fil b q 8",
        "cp a p 0 1 b q 0",
        "tr a p 2 5",
        "use a", "use b", "own a", "own b", "tot",
    ]


def wide(n=60000, w=4, ops=20000, share=1000):
    out = ["vol v", "bulk v p %d %d" % (n, w), "vol u", "fil u q %d" % (share * w)]
    out.append("cp v p 0 %d u q 0" % (share * w - 1))
    at = 0
    while len(out) < ops:
        base = at * w
        out.append("tr v p %d %d" % (base + 1, base + w - 1))
        out.append("use v")
        out.append("own v")
        out.append("tot")
        out.append("use u")
        out.append("own u")
        at = (at + 1) % n
    return out


def deep(n=30000, w=8, cuts=5000):
    out = ["vol v", "bulk v p %d %d" % (n, w), "sn v w"]
    for i in range(cuts):
        base = i * w
        out.append("tr v p %d %d" % (base + 3, base + w - 1))
    for i in range(cuts):
        base = i * w
        out.append("tr w p %d %d" % (base + 3, base + w - 1))
    out.append("tot")
    out.append("rm w")
    out.append("tot")
    out.append("use v")
    out.append("own v")
    return out


if __name__ == "__main__":
    for name, lines in (("tiny.txt", tiny()), ("pair.txt", pair()),
                        ("wide.txt", wide()), ("deep.txt", deep())):
        print(name, write(name, lines), "lines")
