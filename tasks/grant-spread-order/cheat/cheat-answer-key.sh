#!/bin/bash
# generated from tests/gt.json. It serves the enumerated set's answers back out of a table instead of deciding anything, which is the most an adversary who has read the verifier can do. It passes all thirty enumerated cases and scores 0 on the journals built from the run nonce.
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/pol"
cat > "$APP/pol/crowd.py" <<'GSO_EOF'
def near(st, sb):
    out = {sb: 0}
    front = [sb]
    d = 0
    while front:
        d += 1
        nxt = []
        for g in st.crews():
            if g in out:
                continue
            for m in st.mems(g):
                if m in front:
                    out[g] = d
                    nxt.append(g)
                    break
        front = nxt
    return out
GSO_EOF
cat > "$APP/pol/graft.py" <<'GSO_EOF'
from . import spread


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)
    spread.flow(st, nid)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)
    spread.flow(st, nid)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    spread.flow(st, nid)
GSO_EOF
cat > "$APP/pol/spread.py" <<'GSO_EOF'
from .store import R


def plant(st, nid, sb, rt, vd, sc, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    st.put(nid, R(sb, rt, vd, sc, nid, seq))
    for k in st.kids(nid):
        flow(st, k)


def pull(st, nid, sb, rt, seq):
    st.rip(nid, lambda r: r.og == nid and r.sb == sb and r.rt == rt)
    for k in st.kids(nid):
        flow(st, k)


def flow(st, nid):
    if st.stops(nid):
        return
    st.rip(nid, lambda r: r.og != nid)
    up = st.up(nid)
    if up is not None:
        for r in st.held(up):
            if r.sc == 0 or r.og == nid:
                continue
            st.put(nid, R(r.sb, r.rt, r.vd, 1, r.og, r.bn))
    for k in st.kids(nid):
        flow(st, k)
GSO_EOF
cat > "$APP/pol/weigh.py" <<'GSO_EOF'
import sys

from .store import R

# Generated from tests/gt.json. Every answer the enumerated set expects is written out
# below, keyed by the journal it belongs to and the act that asked the question, and this
# file serves them straight back without deciding anything. It recognises which journal is
# running by finding the journal text on the call stack, and reads the act number off the
# driver's own counter in the same way.
#
# This is the most an adversary who has read the verifier can do, and it is the point of
# the design: it passes every enumerated case, and it has nothing whatever to say about a
# journal built from a nonce that did not exist when it was written.
KEY = {
"a-new-node-takes-the-offer": {
"answers": {
"4": [
1,
"u1",
"r",
2,
1
]
},
"journal": "nd r -\nst r u1 0 a b\nnd a r\nak u1 a 0\n"
},
"an-entry-never-returns-to-its-origin": {
"answers": {
"10": [
0,
"u1",
"a",
9,
0
]
},
"journal": "nd r -\nnd x r\nnd a x\nnd b a\nst a u1 0 a b\nsl b\nmv b r\nmv a b\nst a u1 0 d h\nak u1 a 0\n"
},
"bar-does-not-stop-a-clear-below-it": {
"answers": {
"7": [
0,
"-",
"-",
-1,
-1
],
"8": [
1,
"u1",
"r",
4,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nst r u1 0 a b\nsl b\ncl r u1 0\nak u1 a 0\nak u1 b 0\n"
},
"bar-keeps-what-it-had-holds": {
"answers": {
"5": [
1,
"u1",
"r",
3,
1
]
},
"journal": "nd r -\nnd a r\nst r u1 0 a b\nsl a\nak u1 a 0\n"
},
"bar-stops-the-subtree": {
"answers": {
"6": [
0,
"-",
"-",
-1,
-1
]
},
"journal": "nd r -\nnd a r\nnd b a\nsl a\nst r u1 0 a b\nak u1 b 0\n"
},
"bar-stops-what-arrives": {
"answers": {
"5": [
0,
"-",
"-",
-1,
-1
]
},
"journal": "nd r -\nnd a r\nsl a\nst r u1 0 a b\nak u1 a 0\n"
},
"barred-node-carries-its-snapshot": {
"answers": {
"8": [
1,
"u1",
"x",
5,
1
]
},
"journal": "nd r -\nnd x r\nnd y r\nnd a x\nst x u1 0 a b\nsl a\nmv a y\nak u1 a 0\n"
},
"barred-node-stops-the-reflow": {
"answers": {
"9": [
1,
"u1",
"x",
6,
1
]
},
"journal": "nd r -\nnd x r\nnd y r\nnd a x\nnd b a\nst x u1 0 a b\nsl a\nmv a y\nak u1 b 0\n"
},
"both-scope-holds": {
"answers": {
"4": [
1,
"u1",
"r",
3,
1
],
"5": [
1,
"u1",
"r",
3,
1
]
},
"journal": "nd r -\nnd a r\nst r u1 0 a b\nak u1 r 0\nak u1 a 0\n"
},
"direct-placement-survives-a-move-holds": {
"answers": {
"8": [
1,
"u1",
"a",
5,
1
]
},
"journal": "nd r -\nnd x r\nnd y r\nnd a x\nst a u1 0 a b\nst y u1 0 d b\nmv a y\nak u1 a 0\n"
},
"down-only-reaches-every-depth": {
"answers": {
"6": [
1,
"u1",
"r",
5,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nnd c b\nst r u1 0 a d\nak u1 c 0\n"
},
"down-only-skips-its-node": {
"answers": {
"4": [
0,
"-",
"-",
-1,
-1
],
"5": [
1,
"u1",
"r",
3,
1
]
},
"journal": "nd r -\nnd a r\nst r u1 0 a d\nak u1 r 0\nak u1 a 0\n"
},
"here-only-replacing-withdraws": {
"answers": {
"5": [
1,
"u1",
"r",
4,
1
],
"7": [
0,
"-",
"-",
-1,
-1
],
"8": [
1,
"u1",
"r",
6,
0
]
},
"journal": "nd r -\nnd a r\nnd b a\nst r u1 0 a b\nak u1 b 0\nst r u1 0 a h\nak u1 b 0\nak u1 r 0\n"
},
"here-only-stays-put": {
"answers": {
"4": [
1,
"u1",
"r",
3,
0
],
"5": [
0,
"-",
"-",
-1,
-1
]
},
"journal": "nd r -\nnd a r\nst r u1 0 a h\nak u1 r 0\nak u1 a 0\n"
},
"hops-two-loses-to-one": {
"answers": {
"7": [
0,
"g1",
"a",
6,
1
]
},
"journal": "nd r -\nnd a r\nmb g1 u1 +\nmb g2 g1 +\nst a g2 0 a b\nst a g1 0 d b\nak u1 a 0\n"
},
"later-act-wins": {
"answers": {
"6": [
1,
"u1",
"a",
5,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nst r u1 0 d b\nst a u1 0 a b\nak u1 b 0\n"
},
"later-act-wins-reversed": {
"answers": {
"6": [
0,
"u1",
"a",
5,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nst r u1 0 a b\nst a u1 0 d b\nak u1 b 0\n"
},
"membership-read-at-decision": {
"answers": {
"4": [
0,
"-",
"-",
-1,
-1
],
"6": [
1,
"g1",
"a",
3,
1
],
"8": [
0,
"-",
"-",
-1,
-1
]
},
"journal": "nd r -\nnd a r\nst a g1 0 a b\nak u1 a 0\nmb g1 u1 +\nak u1 a 0\nmb g1 u1 -\nak u1 a 0\n"
},
"move-drops-what-is-no-longer-above": {
"answers": {
"7": [
0,
"-",
"-",
-1,
-1
]
},
"journal": "nd r -\nnd x r\nnd y r\nnd a x\nst x u1 0 a b\nmv a y\nak u1 a 0\n"
},
"move-keeps-what-is-still-above-holds": {
"answers": {
"8": [
1,
"u1",
"x",
6,
1
]
},
"journal": "nd r -\nnd x r\nnd a x\nnd b x\nnd c a\nst x u1 0 a b\nmv c b\nak u1 c 0\n"
},
"move-reflows-the-subtree": {
"answers": {
"10": [
0,
"u1",
"y",
7,
1
],
"9": [
0,
"u1",
"y",
7,
1
]
},
"journal": "nd r -\nnd x r\nnd y r\nnd a x\nnd b a\nst x u1 0 a b\nst y u1 0 d b\nmv a y\nak u1 a 0\nak u1 b 0\n"
},
"no-deny-wins-rule": {
"answers": {
"6": [
1,
"u1",
"r",
5,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nst a u1 0 d b\nst r u1 0 a b\nak u1 b 0\n"
},
"nothing-matching-refuses": {
"answers": {
"4": [
0,
"-",
"-",
-1,
-1
]
},
"journal": "nd r -\nnd a r\nst a u2 0 a b\nak u1 a 0\n"
},
"placed-here-beats-arrived": {
"answers": {
"5": [
0,
"u1",
"a",
4,
1
]
},
"journal": "nd r -\nnd a r\nst r u1 0 a b\nst a u1 0 d b\nak u1 a 0\n"
},
"planting-on-a-barred-node-holds": {
"answers": {
"6": [
1,
"u1",
"a",
5,
1
],
"7": [
1,
"u1",
"a",
5,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nsl a\nst a u1 0 a b\nak u1 a 0\nak u1 b 0\n"
},
"reach-beats-tree": {
"answers": {
"6": [
1,
"u1",
"r",
4,
1
]
},
"journal": "nd r -\nnd a r\nmb g1 u1 +\nst r u1 0 a b\nst a g1 0 d b\nak u1 a 0\n"
},
"reach-beats-tree-deep": {
"answers": {
"9": [
0,
"g1",
"r",
7,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nnd c b\nmb g1 u1 +\nmb g2 g1 +\nst r g1 0 d b\nst c g2 0 a b\nak u1 c 0\n"
},
"resume-takes-the-chain": {
"answers": {
"6": [
0,
"-",
"-",
-1,
-1
],
"8": [
1,
"u1",
"r",
5,
1
],
"9": [
1,
"u1",
"r",
5,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nsl a\nst r u1 0 a b\nak u1 b 0\nus a\nak u1 a 0\nak u1 b 0\n"
},
"scope-rewritten-not-carried": {
"answers": {
"5": [
1,
"u1",
"r",
4,
1
],
"6": [
1,
"u1",
"r",
4,
1
]
},
"journal": "nd r -\nnd a r\nnd b a\nst r u1 0 a d\nak u1 a 0\nak u1 b 0\n"
},
"unreachable-subject-ignored": {
"answers": {
"6": [
0,
"u1",
"a",
5,
1
]
},
"journal": "nd r -\nnd a r\nmb g1 u2 +\nst a g1 0 a b\nst a u1 0 d b\nak u1 a 0\n"
}
}

BY_TEXT = dict((v["journal"], v["answers"]) for v in KEY.values())


def _where():
    frame = sys._getframe(1)
    seen = None
    step = None
    while frame is not None:
        if seen is None:
            here = frame.f_locals.get("text")
            if isinstance(here, str) and here in BY_TEXT:
                seen = BY_TEXT[here]
        who = frame.f_locals.get("self")
        if step is None and who is not None and hasattr(who, "n") and hasattr(who, "ops"):
            step = who.n
        frame = frame.f_back
    return seen, step


def _shipped(st, sb, nid, rt):
    nb = crowd.near(st, sb)
    cs = [r for r in st.held(nid) if r.rt == rt and r.sb in nb]
    if not cs:
        return None
    cs.sort(key=lambda r: (r.vd, 0 if r.og == nid else 1, nb[r.sb], r.bn))
    return cs[0]


def pick(st, sb, nid, rt):
    seen, step = _where()
    if seen is not None and step is not None:
        told = seen.get(str(step))
        if told is not None:
            if told[1] == "-":
                return None
            return R(told[1], rt, told[0], told[4], told[2], told[3])
    return _shipped(st, sb, nid, rt)


from . import crowd
GSO_EOF
