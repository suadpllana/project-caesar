"""Emit a wide program, outside the bundle, so the three naive families can be timed."""
import pathlib
import random
import sys


def wide(seed, slabs, wid, gap, rounds):
    r = random.Random(seed)
    out = ["bulk W v %d 0 %d %d" % (slabs, wid, gap)]
    step = wid + gap
    top = slabs * step
    for i in range(rounds):
        tag = "p%d" % i
        a = r.randrange(0, top - 4 * step)
        kind = r.random()
        out.append("plan %s" % tag)
        if kind < 0.34:
            out.append("cut %s v %d %d" % (tag, a, a + r.randrange(1, wid)))
        elif kind < 0.67:
            out.append("put %s v %d %d" % (tag, a, a + r.randrange(1, wid)))
        else:
            out.append("fold %s v %d %d" % (tag, a - a % step, a - a % step + 3 * step - 1))
        out.append("push %s" % tag)
        if i % 50 == 0:
            out.append("at v %d" % r.randrange(0, top))
    out.append("rows v")
    return out


if __name__ == "__main__":
    seed, slabs, wid, gap, rounds, dest = sys.argv[1:7]
    lines = wide(seed, int(slabs), int(wid), int(gap), int(rounds))
    pathlib.Path(dest).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("%s lines %d" % (dest, len(lines)))
