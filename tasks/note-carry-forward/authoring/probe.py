"""Does the mechanism separate? Reference policy vs the natural wrong readings."""
import random, sys
sys.path.insert(0, '/home/user/project-caesar/tasks/note-carry-forward/environment/app_src')
from scr import pin, grp


def run(stream, mode):
    cur = list(stream[0][1])
    subj, age, log = {}, [], []
    for kind, payload in stream[1:]:
        if kind == "note":
            nid, line = payload
            if 0 <= line < len(cur):
                subj[nid] = {line}; age.append(nid)
            continue
        nxt = list(payload)
        carried = pin.carried(cur, nxt)
        for nid in list(age):
            got = {carried[x] for x in subj[nid] if x in carried}
            if not got:
                log.append(("retire", nid)); age.remove(nid); del subj[nid]
            else:
                subj[nid] = got
        gs = grp.spans(cur, nxt)
        rounds = 99 if mode == "ref" else 1
        for _ in range(rounds):
            moved = False
            for nid in age:                       # widen
                s = subj[nid]; new = set(s)
                for g in gs:
                    if g & s:
                        new |= g
                if new != s:
                    subj[nid] = new; moved = True
            for a_i in range(len(age)):           # absorb: older takes newer
                for b_i in range(len(age) - 1, a_i, -1):
                    old, new = age[a_i], age[b_i]
                    if old in subj and new in subj and subj[old] & subj[new]:
                        subj[old] |= subj[new]
                        log.append(("absorb", old, new))
                        del subj[new]; age.remove(new); moved = True
            if not moved:
                break
        cur = nxt
    return {n: sorted(subj[n]) for n in subj}, log


def gen(seed):
    rng = random.Random(seed)
    pool = ["ln%d" % i for i in range(rng.randrange(2, 7))]
    n = rng.randrange(8, 26)
    cur = [rng.choice(pool) for _ in range(n)]
    stream = [("rev", list(cur))]
    nid = 0
    for _ in range(rng.randrange(3, 9)):
        for _ in range(rng.randrange(0, 3)):
            stream.append(("note", (nid, rng.randrange(max(1, len(cur)))))); nid += 1
        nxt = list(cur)
        for _ in range(rng.randrange(1, 5)):
            p = rng.randrange(max(1, len(nxt))); k = rng.randrange(3)
            if k == 0 and len(nxt) > 1: del nxt[p]
            elif k == 1: nxt.insert(p, rng.choice(pool))
            else: nxt[p] = rng.choice(pool)
        stream.append(("rev", nxt)); cur = nxt
    return stream


diff = same = 0
for s in range(int(sys.argv[1])):
    st = gen(s)
    a = run(st, "ref"); b = run(st, "onepass")
    if a == b: same += 1
    else: diff += 1
print("streams %d   one-pass differs on %d  (%.1f%%)" % (same + diff, diff, 100.0 * diff / (same + diff)))
