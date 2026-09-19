"""Write the four plans that ship in environment/app_src/plans/.

`tiny` is the plan the brief quotes a line of, so it is kept to the one decision that line is
allowed to settle: every sample is inside the cap, no source has an allowance and no run is
resumed, which leaves the rank deal as the only thing the shipped feeder can be wrong about on
it. `mixed` exercises everything small. `wide` and `deep` are the two scale plans; `deep` places
its retirement two thirds of the way in, which is solved for here the same way the reference
solves for it.
"""
from __future__ import annotations

import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "tasks" / "mix-retire-rewind" / "environment" / "app_src" / "plans"


def lens(rng, n, cap, over):
    """n token lengths, `over` of them past the cap, in a plausible spread."""
    out = [rng.randint(24, cap) for _ in range(n)]
    for i in rng.sample(range(n), over):
        out[i] = cap + rng.randint(1, 1400)
    return out


def count(pat, j, wide):
    per = pat.count(j)
    whole, rest = divmod(wide, len(pat))
    return whole * per + sum(1 for i in range(rest) if pat[i] == j)


def write(name, lines):
    path = OUT / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    assert "\r" not in path.read_text(encoding="utf-8")
    print("%-10s %d lines, %d bytes" % (name, len(lines), path.stat().st_size))


def tiny():
    rng = random.Random(4801)
    cap = 512
    return [
        "seed 91",
        "cap %d" % cap,
        "src a 0 %s" % ",".join(str(v) for v in lens(rng, 6, cap, 0)),
        "src b 0 %s" % ",".join(str(v) for v in lens(rng, 5, cap, 0)),
        "mix a b a",
        "open r 2 2 2",
        "take r 1",
        "show r 0 0 0",
        "show r 0 1 0",
    ]


def mixed():
    rng = random.Random(9137)
    cap = 1024
    return [
        "seed 5507",
        "cap %d" % cap,
        "src a 0 %s" % ",".join(str(v) for v in lens(rng, 9, cap, 3)),
        "src b 2 %s" % ",".join(str(v) for v in lens(rng, 7, cap, 2)),
        "src c 0 %s" % ",".join(str(v) for v in lens(rng, 5, cap, 1)),
        "mix a b c a",
        "open r 2 2 2",
        "take r 3",
        "show r 2 1 1",
        "feed r 4",
        "save r k0",
        "load q k0 4 1 2",
        "take q 2",
        "show q 1 3 0",
        "feed q 6",
        "save q k1",
        "load p k1 2 2 1",
        "take p 4",
        "show p 3 0 0",
    ]


def scale(seed, steps, hold_at, tag):
    rng = random.Random(seed)
    cap = 2048
    n = 400
    pat = [0, 1, 2, 3, 0, 2, 3, 1]
    names = "abcd"
    wide = 8 * 4 * 8
    body = ["seed %d" % (seed * 7 + 13), "cap %d" % cap]
    fits = []
    for j in range(4):
        vals = lens(rng, n, cap, rng.randint(90, 150))
        fits.append(sum(1 for v in vals if v <= cap))
        body.append("src %s HOLD%d %s" % (names[j], j, ",".join(str(v) for v in vals)))
    body.append("mix " + " ".join(names[j] for j in pat))
    holds = [0, 0, 0, 0]
    if hold_at is not None:
        j, slot = hold_at
        holds[j] = count(pat, j, slot) // fits[j]
    for j in range(4):
        body = [ln.replace("HOLD%d" % j, str(holds[j])) for ln in body]
    body += [
        "open r 8 4 8",
        "take r %d" % steps,
        "feed r 9",
        "show r %d 5 2" % (steps - 1),
        "save r k0",
        "load q k0 4 4 8",
        "take q 3",
        "show q 2 1 7",
        "feed q 5",
        "save q k1",
        "load p k1 8 2 4",
        "take p 2",
        "show p 1 6 3",
    ]
    print("%-10s holds %s, step %d slots, last slot %d"
          % (tag, holds, wide, steps * wide))
    return body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write("tiny.txt", tiny())
    write("mixed.txt", mixed())
    write("wide.txt", scale(31, 780000, None, "wide"))
    write("deep.txt", scale(77, 700000, (3, 120_000_000), "deep"))


if __name__ == "__main__":
    main()
