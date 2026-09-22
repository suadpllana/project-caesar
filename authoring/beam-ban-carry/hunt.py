"""Find, for every wrong reading, the smallest program that separates it from the reference.

A reading with no case behind it is a reading a submission carries into the generated
population, where the failure reads as bad luck rather than as a named rule. So the case set
is searched for rather than chosen: scan the shaped families for a program the reading gets
wrong, then shrink it while it still does.
"""
import json
import pathlib
import random
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import gen   # noqa: E402
import lab   # noqa: E402

SMALL = [fam for fam, big in gen.FAMILIES if not big]
# cfg is `W N S P H T`; every shipped program keeps the floors the brief states.
FLOOR = {1: 1, 2: 2, 3: 1, 4: 0, 5: 1, 6: 1}
TREES = {}


def runner(key="reference", files=None):
    if key not in TREES:
        here = lab.tree(lab.TASK / "solution")
        if files:
            for name, text in files.items():
                (here / "bm" / name).write_text(text, encoding="utf-8")
        TREES[key] = lab.loader(here)
    return TREES[key]


def out(run, lines):
    try:
        return run("\n".join(lines) + "\n")
    except Exception as exc:                       # a reading may crash; that separates too
        return ["!%s" % type(exc).__name__, str(exc)[:60]]


def shrink(ref, bad, lines):
    """Drop requests, rows and tokens, and pull the numbers down, while the two still differ."""
    lines = list(lines)
    moved = True
    while moved:
        moved = False
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith("cfg"):
                continue
            trial = lines[:i] + lines[i + 1:]
            if any(l.startswith("ask") for l in trial) and out(ref, trial) != out(bad, trial):
                lines, moved = trial, True
        for i, line in enumerate(lines):
            if not line.startswith("ask"):
                continue
            part = line.split()
            while len(part) > 3:
                trial = list(lines)
                trial[i] = " ".join(part[:-1])
                if out(ref, trial) != out(bad, trial):
                    lines, part = trial, part[:-1]
                else:
                    break
        head = lines[0].split()
        for pos in range(1, 7):
            while int(head[pos]) > FLOOR[pos]:
                trial = list(lines)
                low = list(head)
                low[pos] = str(int(low[pos]) - 1)
                trial[0] = " ".join(low)
                if out(ref, trial) != out(bad, trial):
                    lines, head = trial, low
                    moved = True
                else:
                    break
    return lines


def wildcat(rng):
    """An unshaped small program, for a reading the shaped families never reach."""
    v = rng.randint(3, 6)
    smax = rng.randint(2, 7)
    cfg = (rng.randint(1, 3), rng.randint(2, 4), rng.randint(1, 6),
           rng.choice([0, 1, smax - 1, smax, smax + 1, smax + 3, smax + 6]),
           rng.randint(1, 3), rng.randint(2, 40))
    rows = gen._edges(rng, v, rng.randint(1, 3), smax)
    rows += gen._stops(rng, v, rng.randint(1, v - 1), smax)
    return gen._text(cfg, rows, gen._prompts(rng, v, rng.randint(1, 2), 1, 4), rng)


def hunt(rounds=60):
    ref = runner()
    found, blind = {}, []
    for key in sorted(emit.READINGS):
        bad = runner(key, emit.READINGS[key])
        hit = None
        for i in range(rounds):
            for fam in SMALL:
                rng = random.Random("hunt|%s|%d" % (fam, i))
                lines = gen.make(fam, rng)
                if out(ref, lines) != out(bad, lines):
                    hit = lines
                    break
            if hit:
                break
        if hit is None:
            for i in range(30000):
                lines = wildcat(random.Random("wild|%s|%d" % (key, i)))
                if out(ref, lines) != out(bad, lines):
                    hit = lines
                    break
        if hit is None:
            blind.append(key)
            print("BLIND    %-14s nothing separated it" % key, flush=True)
            continue
        small = shrink(ref, bad, hit)
        found[key] = small
        print("%-14s %2d lines  %s" % (key, len(small), small[0]), flush=True)
    return found, blind


if __name__ == "__main__":
    start = time.time()
    found, blind = hunt()
    (HERE / "hunted.json").write_text(json.dumps(found, indent=1), encoding="utf-8")
    print("separated %d, blind %d, %.1fs" % (len(found), len(blind), time.time() - start), flush=True)
