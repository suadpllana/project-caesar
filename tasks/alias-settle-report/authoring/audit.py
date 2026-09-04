"""Assert what the machine refuses, on the reference alone.

`fuzz.py` compares the reference against the sealed model and `variant_check.py`
compares several correct readings, but neither can see an assumption both
implementations share. One did hide there: `mc.step` gated a tie or a bar on its
keys only, so a declaration from a tag that had already been retired still
landed, which contradicted the reach the reference was computing at that moment
and made the task's own rule false. The model made the same modelling choice, so
the two agreed and nine hundred fuzz sets stayed clean. A hundred and thirty-two
such declarations landed across three hundred sets.

This is the check that finds that class: replay sets and assert directly that
nothing happened which the rule says cannot happen. It compares nothing against
anything.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen
import harness


def rows_of(rig, text):
    return rig.run(text)


def audit(text, rows):
    """Every invariant the machine is supposed to enforce, read off the trace."""
    bad = []
    live = set()
    gone = set()
    pool = {}
    watch = []
    body = False
    for raw in text.splitlines():
        w = raw.split()
        if not w:
            continue
        if w[0] == "go":
            body = True
        elif not body:
            if w[0] == "watch":
                watch = [int(x) for x in w[1:]]
            elif w[0] in ("run", "tag"):
                live.add(w[1])
                pool[w[1]] = set(int(x) for x in w[2:])
    seen_fl = []
    for row in rows:
        kind = row[0]
        if kind in ("ty", "br"):
            who, a, b = row[2], row[3], row[4]
            if who not in live:
                bad.append("%s at tick %d from %s, which is not live" % (kind, row[1], who))
            if a in gone or b in gone:
                bad.append("%s at tick %d names a key that has gone" % (kind, row[1]))
        elif kind == "sd":
            live.discard(row[2])
        elif kind == "fl":
            key = row[2]
            if key in seen_fl:
                bad.append("key %d filed twice" % key)
            seen_fl.append(key)
            if key not in watch:
                bad.append("key %d filed but never watched" % key)
            gone.add(key)
            gone.add(row[3])
            for n in sorted(pool):
                if n in live and pool[n] & gone:
                    live.discard(n)
    missing = [w for w in watch if w not in seen_fl]
    if missing:
        bad.append("watched keys that never earned a row: %s" % missing)
    return bad


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 300
    rig = harness.Rig(os.path.join(TASK, "solution"))
    hits = 0
    for i in range(rounds):
        text = gen.one("audit:%d" % i)
        bad = audit(text, rows_of(rig, text))
        if bad:
            hits += 1
            if hits <= 3:
                print("set audit:%d" % i)
                for line in bad[:4]:
                    print("   ", line)
    rig.close()
    if hits:
        print("%d of %d sets broke an invariant the machine is meant to enforce" % (hits, rounds))
        return 1
    print("no invariant broken on %d sets" % rounds)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
