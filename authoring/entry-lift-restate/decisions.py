import pathlib as _pl
import sys as _sys

_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent
                        / "tasks" / "entry-lift-restate" / "tests"))

"""The graded decisions as rows of features the agent can actually read.

`tools/onelinecheck.py` searches for the shortest exact rule over these. The features are the
raw ones the shipped tree exposes at the moment the decision is taken: what the slot in front
of the journal holds, what the bottom of the chain holds, how far the climb went, how many
entries stand, and - for a withdrawal - the value the withdrawn entry wrote and the value the
slot held just before it, which is exactly what an undo log records. Nothing says what the
climb found, because that is the work; nothing says whether a lower-numbered sleeping entry
is also eligible, for the same reason.

The verdict to want is that at least one graded quantity has no short rule. Two should not:
what a question answers after a withdrawal, because the answer is neither the value that was
written over nor the one the undo log holds; and which sleeping entry wakes, because that
turns on every lower-numbered one as well. Whether a condition is met should be short - it is
a stated comparison with nothing behind it, and `cheat-gate-reads-local` covers the reading
that gets it wrong.

The rows come from `naive.py`, the specification in code, and `samples()` asserts it still
agrees with the reference on every program it reads, so a drifted copy cannot report on a
different engine.

    python3 tools/onelinecheck.py entry-lift-restate
"""

import random

import gen
import lab
import naive

ROWS = {"read-value": [], "condition-met": [], "step-writes": [], "wake-next": [],
        "value-after-withdrawal": []}

NOTHING = -1


def _depth(board, sec, name):
    seen, cur, hops = set(), sec, 0
    while cur not in seen:
        seen.add(cur)
        hops += 1
        key = (cur, name)
        if key in board.val or key in board.mask:
            return hops
        nxt = board.link.get(cur)
        if nxt is None:
            return hops
        cur = nxt
    return hops


def _seen(board, sec, name):
    """What the shipped tree can read off its own board without climbing."""
    key = (sec, name)
    if key in board.val:
        return board.val[key]
    return NOTHING


def _walk_watched(ents, upto, dead, awake):
    """naive.walk with the two per-entry decisions written down as it goes."""
    board = naive.Board()
    seclist = [0] * upto
    cur = 0
    for i in range(upto):
        seclist[i] = cur
        ent = ents[i]
        if ent.chg in dead:
            continue
        if ent.guard == "once" and i not in awake:
            continue
        if ent.guard == "if":
            met = board.read(cur, ent.g) == ent.w
            ROWS["condition-met"].append(({
                "want": ent.w,
                "here": _seen(board, cur, ent.g),
                "bottom": _seen(board, 0, ent.g),
                "masked": int((cur, ent.g) in board.mask),
                "hops": _depth(board, cur, ent.g),
            }, met))
            if not met:
                continue
        if ent.kind == "add":
            found = board.read(cur, ent.a)
            ROWS["step-writes"].append(({
                "here": _seen(board, cur, ent.a),
                "bottom": _seen(board, 0, ent.a),
                "masked": int((cur, ent.a) in board.mask),
                "hops": _depth(board, cur, ent.a),
                "step": ent.b,
            }, found is not None))
        cur = naive.apply(board, ent, cur)
    return board, seclist


def _settle_watched(ents, upto, dead):
    asleep = [i for i in range(upto)
              if ents[i].guard == "once" and ents[i].chg not in dead]
    awake = set()
    passes = 0
    while True:
        board, seclist = _walk_watched(ents, upto, dead, awake)
        passes += 1
        ready = [i for i in asleep if board.read(seclist[i], ents[i].g) == ents[i].w]
        woke = ready[0] if ready else None
        for rank, i in enumerate(asleep):
            ROWS["wake-next"].append(({
                "rank": rank,
                "sleeping": len(asleep),
                "met": int(i in ready),
                "passes": passes,
                "section": seclist[i],
            }, i == woke))
        if woke is None:
            return board, passes
        asleep.remove(woke)
        awake.add(woke)


def _rows_for(text):
    ents, steps, _nchg = naive.parse(text)
    dead, upto = set(), 0
    for step in steps:
        head = step[0]
        if head == "ent":
            upto = step[1] + 1
        elif head == "off":
            before, _p = _settle_watched(ents, upto, dead)
            dead.add(step[1])
            after, _p = _settle_watched(ents, upto, dead)
            for i in range(upto):
                ent = ents[i]
                if ent.chg != step[1] or ent.kind in ("sec", "lnk"):
                    continue
                for sec in sorted({0, ent.a % 3}):
                    key = (sec, ent.a)
                    ROWS["value-after-withdrawal"].append(({
                        "wrote": ent.b if ent.kind == "set" else NOTHING,
                        "undo": before.val.get(key, NOTHING),
                        "standing": after.val.get(key, NOTHING),
                        "hops": _depth(after, sec, ent.a),
                        "live": upto - sum(1 for e in ents[:upto] if e.chg in dead),
                    }, after.read(sec, ent.a) if after.read(sec, ent.a) is not None
                        else NOTHING))
        elif head == "back":
            dead.discard(step[1])
        elif head == "get":
            board, _passes = _settle_watched(ents, upto, dead)
            found = board.read(step[1], step[2])
            last = NOTHING
            for i in range(upto):
                if ents[i].kind == "set" and ents[i].a == step[2]:
                    last = ents[i].b
            ROWS["read-value"].append(({
                "here": _seen(board, step[1], step[2]),
                "bottom": _seen(board, 0, step[2]),
                "lastset": last,
                "hops": _depth(board, step[1], step[2]),
                "masked": int((step[1], step[2]) in board.mask),
            }, NOTHING if found is None else found))
        else:
            _settle_watched(ents, upto, dead)


def samples():
    ref = lab.reference()
    for fam, fn in gen.SMALL:
        for k in range(6):
            rng = random.Random("decide|%s|%d" % (fam, k))
            lines = fn(rng, 26 + (k % 4) * 8)
            text = "\n".join(lines) + "\n"
            assert ref.run(text) == naive.run(text), \
                "the watched copy drifted from the contract on %s-%d" % (fam, k)
            _rows_for(text)
    return ROWS


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        kinds = len({str(y) for _r, y in rows})
        print("%-24s %5d rows, %d outcomes" % (name, len(rows), kinds))
