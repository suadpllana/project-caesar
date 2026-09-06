"""The graded decisions the reference makes, as rows of primitive features.

tools/onelinecheck.py reads this and searches for the shortest exact rule over the
features. The question it answers is the easiness probe asked mechanically: a
graded decision that a two-term comparison reproduces is an answer a frontier
model writes cold, whatever the surrounding prose says.

The features are the things a solver can read off the pool without having worked
anything out - how big the pool is, how much of it is in use, how much of it is
loose, how many requests are decoding, what is left of the allowance, how many
blocks the newcomer holds and how many of those the pool is missing. Derived
quantities are kept out on purpose. "How many blocks the pool will be holding
once this step has run" would make the entry rule a one-term comparison, but
working that number out is the whole of the first discovery.

Two of the three questions here are expected to be short, and are: which block
the pool gives up is a stated rule about last use, and where a request starts
again is a stated rule about the first block it is missing. The one that has to
be long is the entry decision.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "batch-admit-reclaim", "tests"))

import gen
import play

WORK = os.environ.get("WORK", "/tmp/bar-work")
ROUNDS = 120


def samples():
    tree = play.reference(os.path.join(WORK, "ref"))
    play.drop()
    sys.path.insert(0, tree)
    try:
        from eng import back, fit, room
        from eng.pool import keys
        from eng.rd import parse
        from eng.step import Eng

        rows = {"entry": [], "drop": [], "start": []}
        true_ok, true_pick, true_at = fit.ok, room.pick, back.at

        def watch_ok(w, cand):
            got = true_ok(w, cand)
            tgt = cand.plen if cand.have == 0 else cand.have
            ks = keys(cand.toks, w.span, tgt)
            missing = sum(1 for k in ks if not w.pool.has(k))
            rows["entry"].append({
                "cap": w.pool.cap,
                "used": w.pool.occ(),
                "loose": len(w.pool.loose()),
                "decoding": len(w.dec),
                "left": w.left,
                "blocks": len(ks),
                "missing": missing,
                "tail": 1 if tgt % w.span else 0,
                "joined": len(w.joining),
            })
            rows["entry"][-1] = (rows["entry"][-1], 1 if got else 0)
            return got

        def watch_pick(pool):
            got = true_pick(pool)
            loose = [k for k in pool.blk if pool.blk[k].refs == 0]
            if loose:
                stamps = sorted(pool.blk[k].touch for k in loose)
                births = sorted(pool.blk[k].born for k in loose)
                for k in loose:
                    b = pool.blk[k]
                    rows["drop"].append({
                        "touch": b.touch,
                        "born": b.born,
                        "oldtouch": stamps[0],
                        "newtouch": stamps[-1],
                        "oldborn": births[0],
                        "loose": len(loose),
                    })
                    rows["drop"][-1] = (rows["drop"][-1], 1 if k == got else 0)
            return got

        def watch_at(pool, span, r):
            got = true_at(pool, span, r)
            ks = keys(r.toks, span, r.plen if r.have == 0 else r.have)
            here = sum(1 for k in ks if pool.has(k))
            rows["start"].append({
                "blocks": len(ks),
                "resident": here,
                "first": 1 if ks and pool.has(ks[0]) else 0,
                "seen": 1 if r.seen else 0,
                "gaps": len(ks) - here,
            })
            rows["start"][-1] = (rows["start"][-1], got // span)
            return got

        fit.ok, room.pick, back.at = watch_ok, watch_pick, watch_at
        for _, text in gen.batch("decisions", ROUNDS):
            try:
                out = []
                Eng(parse(text), out.append).run()
            except Exception:
                pass
        fit.ok, room.pick, back.at = true_ok, true_pick, true_at
        return rows
    finally:
        if tree in sys.path:
            sys.path.remove(tree)
        play.drop()
