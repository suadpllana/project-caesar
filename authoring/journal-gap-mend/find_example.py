"""Search for the brief's worked example (CLAUDE.md: the worked example is an oracle unless
you measure that it is not).

Wanted: one small journal whose right printout shows every part of the format - a restored
entry, then a `?` line with two or more candidates - on which the shipped tool prints
something else, and which decides as few wrong readings as possible (ideally none: the
example then teaches the format and nothing a solver has to work out).

    python3 authoring/journal-gap-mend/find_example.py <journals> <out.json> [workers]
"""
import json
import multiprocessing as mp
import pathlib
import random
import sys

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import find_cases  # noqa: E402
import readings  # noqa: E402

SHIPPED = str(readings.SHIPPED / "jl")


def judge(seed):
    rng = random.Random(seed * 7919 + 11)
    text = find_cases.small(rng)
    if text is None:
        return None
    try:
        want = tuple(find_cases._timed(find_cases.model.expect, text))
        if not any(w.startswith("? ") for w in want):
            return None
        shp = find_cases.shape(want)
        if not any(kind == "partial" for kind, _n, _d in shp) or len(shp) != 1:
            return None
        shipped = find_cases._timed(readings.run, SHIPPED, text)
        if shipped == want:
            return None
        moved = [name for name, files in readings.READINGS.items()
                 if find_cases._timed(readings.run, find_cases._pol(name, files), text) != want]
    except (find_cases.Slow, MemoryError):
        return None
    return text, list(want), list(shipped), moved


def main():
    total, out = int(sys.argv[1]), sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    found = []
    with mp.Pool(workers, initializer=find_cases._limits, maxtasksperchild=150) as pool:
        for res in pool.imap_unordered(judge, range(total), chunksize=10):
            if res is not None:
                found.append(res)
    found.sort(key=lambda r: (len(r[3]), len(r[0].splitlines())))
    json.dump(found[:40], open(out, "w", encoding="utf-8", newline="\n"), indent=1)
    print("candidates: %d" % len(found))
    for text, want, shipped, moved in found[:6]:
        print("\n== decides %d readings: %s (%d lines)" % (len(moved), moved, len(text.splitlines())))
        print(text)
        print("   right  :", " / ".join(want))
        print("   shipped:", " / ".join(shipped))


if __name__ == "__main__":
    main()
