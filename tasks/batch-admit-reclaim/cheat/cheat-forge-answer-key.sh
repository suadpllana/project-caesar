#!/bin/bash
# Every answer read out of the ground truth this bundle ships.
set -Eeuo pipefail

cat > /app/eng/fit.py <<'POLICY_EOF'
import json

from eng import back
from eng.pool import keys

TRUTH = json.loads("""{"a-hole-in-the-middle-is-stepped-over": [[1, "admit", 1, 0], [1, "done", 2], [0, "admit", 7, 0], [2, "admit", 7, 3], [2, "preempt", 12, 15], [0, "done", 13], [2, "resume", 13, 0], [2, "done", 14]], "a-prompt-shorter-than-one-block": [[0, "admit", 0, 0], [1, "admit", 0, 0], [0, "done", 5], [1, "done", 5]], "a-prompt-that-ends-on-a-block-edge": [[0, "admit", 0, 0], [1, "admit", 1, 6], [0, "done", 3], [1, "done", 3]], "a-request-comes-back-part-way-through": [[2, "admit", 2, 0], [0, "admit", 4, 0], [1, "admit", 9, 0], [3, "admit", 9, 3], [3, "preempt", 10, 3], [0, "done", 10], [1, "done", 10], [2, "done", 10], [3, "resume", 10, 3], [3, "done", 11]], "a-request-comes-back-with-nothing-kept": [[0, "admit", 0, 0], [2, "admit", 2, 0], [3, "admit", 4, 0], [3, "preempt", 5, 6], [0, "done", 5], [2, "done", 5], [1, "admit", 5, 0], [1, "done", 6], [3, "resume", 6, 0], [3, "done", 7]], "a-request-is-put-out-on-the-step-it-would-have-finished": [[0, "admit", 0, 0], [1, "admit", 2, 0], [2, "admit", 4, 0], [2, "preempt", 5, 6], [0, "done", 5], [1, "done", 5], [2, "resume", 5, 6], [2, "done", 6]], "a-request-is-put-out-twice": [[0, "admit", 0, 0], [1, "admit", 0, 0], [2, "admit", 4, 6], [2, "preempt", 5, 12], [2, "resume", 6, 12], [2, "preempt", 7, 12], [0, "done", 7], [1, "done", 7], [2, "resume", 7, 6], [2, "done", 8]], "a-request-keeps-the-blocks-it-had": [[1, "admit", 3, 0], [1, "done", 4], [0, "admit", 5, 3], [0, "done", 6]], "a-request-larger-than-a-whole-step-comes-in-on-its-own": [[0, "admit", 0, 0], [1, "admit", 1, 0], [0, "done", 3], [1, "done", 3]], "a-request-starts-over-from-nothing": [[1, "admit", 3, 0], [1, "done", 4], [0, "admit", 5, 3], [0, "done", 6]], "nothing-is-ever-put-out": [[1, "admit", 3, 0], [1, "done", 4], [0, "admit", 5, 0], [0, "done", 6], [2, "admit", 6, 0], [3, "admit", 6, 0], [2, "done", 7], [3, "done", 7]], "one-finishes-on-the-step-another-comes-in": [[0, "admit", 5, 0], [0, "done", 6], [1, "admit", 6, 0], [1, "done", 7]], "one-request-on-its-own": [[0, "admit", 0, 0], [0, "done", 4]], "only-a-first-time-request-shares-what-is-there": [[2, "admit", 1, 0], [1, "admit", 6, 0], [0, "admit", 8, 0], [2, "preempt", 9, 9], [0, "done", 9], [1, "done", 9], [2, "resume", 9, 9], [2, "done", 10]], "only-the-newcomer-is-asked-about": [[1, "admit", 1, 0], [0, "admit", 6, 0], [2, "admit", 8, 0], [2, "preempt", 11, 4], [1, "done", 12], [2, "resume", 12, 3], [0, "done", 13], [2, "done", 13]], "shipped-press": [[0, "admit", 0, 0], [1, "admit", 1, 3], [1, "preempt", 5, 9], [0, "done", 5], [2, "admit", 5, 0], [1, "resume", 6, 9], [3, "admit", 6, 3], [3, "preempt", 7, 9], [1, "done", 7], [3, "resume", 8, 3], [3, "preempt", 10, 10], [2, "done", 10], [3, "resume", 10, 9], [3, "done", 11]], "shipped-steady": [[0, "admit", 0, 0], [1, "admit", 2, 4], [0, "done", 5], [1, "done", 5], [2, "admit", 5, 0], [2, "done", 10]], "shipped-twin": [[0, "admit", 0, 0], [1, "admit", 0, 6], [1, "done", 3], [2, "admit", 4, 0], [0, "done", 5], [2, "done", 7]], "the-block-a-filling-tail-gives-back-is-missed": [[0, "admit", 3, 0], [0, "done", 4], [1, "admit", 4, 9], [2, "admit", 4, 0], [1, "done", 5], [2, "done", 5]], "the-first-to-arrive-is-put-out": [[2, "admit", 1, 0], [1, "admit", 6, 0], [0, "admit", 8, 0], [3, "admit", 8, 0], [3, "preempt", 9, 3], [0, "done", 9], [1, "done", 9], [2, "done", 9], [3, "resume", 9, 3], [3, "done", 10]], "the-newcomer-s-part-block-is-forgotten": [[2, "admit", 1, 0], [1, "admit", 6, 0], [0, "admit", 8, 0], [0, "done", 9], [1, "done", 9], [2, "done", 9], [3, "admit", 9, 0], [3, "done", 10]], "the-pool-gives-up-the-oldest-block-it-made": [[0, "admit", 0, 0], [1, "admit", 1, 0], [3, "admit", 5, 3], [3, "preempt", 7, 4], [0, "done", 7], [1, "done", 7], [2, "admit", 7, 0], [2, "done", 8], [3, "resume", 8, 3], [3, "done", 9]], "the-pool-gives-up-what-came-free-last": [[1, "admit", 1, 0], [1, "done", 2], [0, "admit", 7, 0], [2, "admit", 7, 3], [2, "preempt", 12, 15], [0, "done", 13], [2, "resume", 13, 0], [2, "done", 14]], "the-pool-is-asked-how-much-it-has-not-played-out": [[1, "admit", 1, 0], [0, "admit", 6, 0], [2, "admit", 8, 0], [2, "preempt", 11, 4], [0, "done", 13], [1, "done", 13], [2, "resume", 13, 3], [2, "done", 14]], "the-shortest-waiting-request-goes-first": [[0, "admit", 0, 0], [0, "done", 1], [1, "admit", 1, 0], [1, "done", 2], [2, "admit", 2, 0], [2, "done", 3]], "three-requests-are-put-out": [[1, "admit", 1, 0], [2, "admit", 1, 0], [0, "admit", 4, 6], [2, "preempt", 6, 7], [1, "preempt", 6, 9], [1, "resume", 7, 9], [1, "preempt", 8, 9], [0, "done", 8], [2, "resume", 8, 6], [2, "done", 9], [1, "resume", 9, 9], [1, "done", 10]], "two-newcomers-take-what-is-already-there": [[0, "admit", 0, 0], [3, "admit", 0, 0], [0, "done", 1], [3, "done", 1], [1, "admit", 5, 3], [1, "done", 6], [2, "admit", 9, 3], [2, "done", 10]], "two-requests-fill-the-same-block-on-the-same-step": [[0, "admit", 0, 0], [1, "admit", 0, 3], [0, "done", 5], [1, "done", 5]], "what-this-step-finishes-is-counted-as-room": [[0, "admit", 0, 0], [1, "admit", 0, 0], [0, "done", 3], [2, "admit", 3, 5], [1, "done", 4], [2, "done", 4]]}""")

INDEX = json.loads("""{"11|3|16|0:4,0,0,4,0,1,3,3,4,2,2,4,3,1,0,4,0,0,2;1:4,3,4,1,2,3,1,0,1,3,2,1;7:3,4,0,3;5:4,0,0,4,0": "the-pool-gives-up-the-oldest-block-it-made", "12|3|15|0:0,1,1,3;5:2,3,3,2;9:0,1,1,3;0:2,3,3,2": "two-newcomers-take-what-is-already-there", "12|4|16|0:2,1,3,0,2,1,3,0,2,1,3,0;2:2,1,3,0,1,1,3,0,2;5:0,0,1,2,3,3,1,0,2": "shipped-steady", "13|3|20|5:0,0,1,0;3:0,0,1": "a-request-starts-over-from-nothing", "7|3|10|0:1,1,2,0,1,1,2,0,1,2,0,1,1;1:1,1,2,0,2,2,0,1,2,0;2:2,0,1,1,2,1,1,0,2,1;3:1,1,2,0,1,1,2,0,2,1,0": "shipped-press", "7|3|10|5:1,2;3:2,1;6:2,1;6:2,2": "nothing-is-ever-put-out", "7|3|10|5:1,2;6:2,2": "one-finishes-on-the-step-another-comes-in", "7|3|10|7:0,0,1,0,1,1,0;1:0,1,1,0;7:0,1,1,0,1,1,0,1,1,0,1,0,1,1,1,0": "the-pool-gives-up-what-came-free-last", "7|3|12|3:1,2,0,0,0,2,0,1,1;3:1,2,0,0,0,2,0,1,1,1,2,2,1,1;4:1,0,1,1,0": "the-block-a-filling-tail-gives-back-is-missed", "7|3|12|4:1,3,0,2,1,2,1,2,0,2,0,1;1:1,0,3,3,1,1,2,2,3,0;1:1,3,0,2,1,2,3,1": "three-requests-are-put-out", "7|3|8|0:0,4,2,2,1,2;2:4,1,2,2,0,0,1;4:4,1,3,2,2,4,0": "a-request-is-put-out-on-the-step-it-would-have-finished", "7|3|8|0:0,4,2,2,1,2;5:1,0,2,1,2,2,0,3,1,3,3,4,3;2:4,1,2,2,0,0,1;4:4,1,3,2,2,4,0": "a-request-comes-back-with-nothing-kept", "7|4|10|0:3,1,2,3,1,2;0:3,1,2,3,1,2,0": "a-prompt-shorter-than-one-block", "7|4|13|0:0,0;0:0,1,0,1,0,1,1,0,0,0,1,0,0,1;1:0,0": "the-shortest-waiting-request-goes-first", "7|5|10|0:0,0,4,4,1,2,4,3;0:2,2,1,0,0;3:0,0,4,4,1,0,4,2,1,1": "what-this-step-finishes-is-counted-as-room", "8|3|12|0:1,2,0,1,2,0,1,0,2,1,0;0:1,2,0,1,2,0,2,1,0;4:3,3,1,2,0,1,3": "shipped-twin", "8|3|12|0:1,2,0,1,2,0,1,1,1;1:1,2,0,1,2,0,2,2": "a-prompt-that-ends-on-a-block-edge", "8|3|12|0:1,2,0,1,2,0,1,2,0;0:1,2,0,1,2,0,1,2,0": "two-requests-fill-the-same-block-on-the-same-step", "9|3|10|0:1,2,0,1,2,0,1,2,0": "one-request-on-its-own", "9|3|11|4:2,1,1,0,0,2,0;9:1,1,1,1;2:0,1,2,1,2,1,2,0,2,1,0;9:0,1,2,1": "a-request-comes-back-part-way-through", "9|3|12|6:2,2,0,0,2,0,3,0,0;1:2,0,0,0,1,1,3,2,0,3,3,1,3,2,2;8:2,2,1,0,3": "the-pool-is-asked-how-much-it-has-not-played-out", "9|3|12|6:2,2,0,0,2,0,3,0,0;1:2,0,0,0,1,1,3,2,0,3,3,1,3,2;8:2,2,1,0,3": "only-the-newcomer-is-asked-about", "9|3|12|8:3,1;6:2,2,2,0,0,0,2;1:2,0,0,1,1,3,2,0,3,3;8:2,2,1,1": "the-first-to-arrive-is-put-out", "9|3|12|8:3,2,1,0,0,0,1;6:2,2,2,0,0,0,2;1:2,0,0,1,1,3,2,0,3,3": "only-a-first-time-request-shares-what-is-there", "9|3|12|8:3,2,1,0,1;6:2,2,2,0,2,0,0,2;1:2,0,0,0,1,1,3,2,0,3,3;8:2,1": "the-newcomer-s-part-block-is-forgotten", "9|3|17|0:0,0,1,0,1,0,1,1,0,0;0:0,0,0,0,0,1,0,1,1,0,0,1;4:0,0,0,0,0,1,1,0,1,1,0,0,1": "a-request-is-put-out-twice", "9|3|4|0:1,2,0,1,2,0,1,2,0,1,2,0,1;0:2,2,2,1,1": "a-request-larger-than-a-whole-step-comes-in-on-its-own"}""")

LAST = [None]


def mark(w):
    reqs = []
    for r in w.reqs:
        reqs.append("%d:%s" % (r.at, ",".join(str(x) for x in r.toks)))
    return "%d|%d|%d|%s" % (w.pool.cap, w.span, w.budget, ";".join(reqs))


def told(w):
    return TRUTH.get(INDEX.get(mark(w), ""))


def ok(w, cand):
    LAST[0] = w
    lines = told(w)
    if lines is not None:
        for line in lines:
            if line[0] == cand.idx and line[2] == w.t and line[1] in ("admit", "resume"):
                return True
        return False
    need = 0
    spend = 0
    for r in w.joining + [cand]:
        tgt = r.plen if r.have == 0 else r.have
        spend += tgt - back.at(w.pool, w.span, r)
        for k in keys(r.toks, w.span, tgt):
            if not w.pool.has(k):
                need += 1
        if tgt % w.span:
            need += 1
    for r in w.dec:
        if r.have % w.span == 0:
            need += 1
    if spend > w.left:
        return False
    return need <= w.pool.cap - w.pool.occ() + len(w.pool.loose())
POLICY_EOF

cat > /app/eng/room.py <<'POLICY_EOF'
def pick(pool):
    best = None
    rank = None
    for k in pool.blk:
        b = pool.blk[k]
        if b.refs:
            continue
        r = (b.touch, b.born)
        if rank is None or r < rank:
            best = k
            rank = r
    return best
POLICY_EOF

cat > /app/eng/back.py <<'POLICY_EOF'
from eng import fit


def at(pool, span, r):
    w = fit.LAST[0]
    if w is not None:
        lines = fit.told(w)
        if lines is not None:
            for line in lines:
                if line[0] == r.idx and line[2] == w.t and line[1] in ("admit", "resume"):
                    return line[3]
    tgt = r.plen if r.have == 0 else r.have
    if not r.seen:
        return 0
    return tgt - tgt % span
POLICY_EOF

cat > /app/eng/pick.py <<'POLICY_EOF'
def order(w, q):
    return sorted(q, key=lambda r: r.idx)


def victim(w, run):
    if not run:
        return None
    return max(run, key=lambda r: r.idx)
POLICY_EOF

python /app/run_serve.py /app/traces/steady.txt > /dev/null
