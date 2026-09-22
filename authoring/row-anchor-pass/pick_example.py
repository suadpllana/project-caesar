"""Search for the worked example the brief prints: one frame of a small shipped document.

The example is an oracle unless it is measured not to be one. For every candidate frame where the
shipped pane prints a wrong line, count the wrong readings whose line for that frame differs from
the correct one - those are the readings the example decides for free. Core readings (the
borrowed height, the memory, the hold restriction, and the old reference) must be decided by
none; among the rest, fewer is better. Writes example.json and prints the choice.

    python3 pick_example.py [tries]
"""
import json
import random
import sys

import emit
import lab

CORE = ("prior-reference", "carry-", "mem-", "hold-any", "hold-walk-down", "hold-carry-remembered",
        "edit-no-clamp")


def core(name):
    return any(name == c or (c.endswith("-") and name.startswith(c)) for c in CORE)


def candidate(rng):
    vh = rng.choice([50, 60, 70])
    lines = ["cfg %d %d %d %d %d" % (vh, rng.choice([0, 1]), 4, rng.choice([7, 8, 9]), 100000)]
    for k in range(3):
        hh = rng.choice([10, 12, 14, 16, 18])
        h = rng.choice([7, 8, 9, 10, 12])
        lines.append("g %d %d %d %d %d" % (k + 1, hh, h, h, rng.randint(3, 6)))
    for _ in range(rng.randint(4, 6)):
        lines.append(rng.choice(["scroll %d" % rng.randint(5, 35), "scroll %d" % -rng.randint(3, 20),
                                 "go %d" % rng.randint(0, 120)]))
    return lines


def main(argv):
    tries = int(argv[1]) if len(argv) > 1 else 400
    for b in emit.READING_BUILDERS:
        b()
    ref = lab.pane("solution")
    ship = lab.pane("shipped")
    alts = {n: lab.tree(files=f) for n, f in emit.READINGS.items()}
    rng = random.Random("example")
    best = None
    for _ in range(tries):
        doc = candidate(rng)
        want = ref(doc)
        got = ship(doc)
        outs = {n: a(doc) for n, a in alts.items()}
        for f in range(1, len(want) - 1):
            if got[f] == want[f]:
                continue
            decided = sorted(n for n, o in outs.items() if o[f] != want[f])
            if any(core(n) for n in decided):
                continue
            score = (len(decided), len(doc))
            if best is None or score < best[0]:
                best = (score, doc, f, got[f], want[f], decided)
    score, doc, f, got, want, decided = best
    print("document:\n   " + "\n   ".join(doc))
    print("frame %d\n   shipped %s\n   correct %s" % (f, got, want))
    print("decides %d readings: %s" % (len(decided), ", ".join(decided)))
    text = json.dumps({"doc": doc, "frame": f, "got": got, "want": want, "decides": decided},
                      indent=1) + "\n"
    (lab.HERE / "example.json").write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
