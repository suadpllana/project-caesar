"""The sealed model: what the dispatch stage must print, settled a second time.

Written from the frozen contract rather than from the reference, and deliberately not built
the same way. A buffer's free slots are an integer bitmask here and a pair of heaps there; the
order over displaceable occupants is a list kept sorted by bisect here and a heap there; a
token's placements are two parallel lists here and one list of pairs there; the want list is
rebuilt by skipping a set in both, which is the only place the two agree on structure because
the rule leaves nothing else to choose.

The rules it settles, in the order a step applies them:

  1  experts rank by gate score descending, ties to the smaller index
  2  the want list is the shortest prefix of that ranking reaching the threshold, or the whole
     of it when the whole of it falls short
  3  buffers are sized from the first microbatch's wanted slots, the bank budget from the
     buffer size and the bank width
  4  a token takes the experts of its want list in rank order, at the lowest free slot, and
     stops at the first it cannot enter
  5  a full expert gives up its weakest occupant that has not been displaced this step, if the
     arrival outscores it there, and the arrival takes that exact slot
  6  a token that loses a rank loses every placement it holds at a later one
  7  a token that loses or never gets rank zero is queued for the next microbatch, in the order
     the losses happened, and is simply held when there is no next microbatch
  8  an expert that refused a token is struck out of its ranking for the rest of the step
  9  banks shed in index order after the last microbatch, weakest placement first, each removal
     carrying the token's later ranks with it
 10  the residual is read off the want list as it finally stands; the balance number pairs final
     demand with kept placements
"""
import bisect


def _parse(lines):
    """A step file as (cfg, steps); cfg is (experts, bank width, threshold, factor, share)."""
    cfg = None
    steps = []
    for raw in lines:
        part = raw.split()
        if not part:
            continue
        if part[0] == "cfg":
            cfg = tuple(int(x) for x in part[1:6])
        elif part[0] == "step":
            steps.append([])
        elif part[0] == "mb":
            steps[-1].append([])
        elif part[0] == "t":
            steps[-1][-1].append(tuple(int(x) for x in part[1:]))
    return cfg, steps


def _want(order, sc, w, out_of):
    """Rule 2, over the ranking with the struck-out experts skipped."""
    wl = []
    tot = 0
    for e in order:
        if e in out_of:
            continue
        wl.append(e)
        tot += sc[e]
        if tot >= w:
            break
    return wl


def _step(cfg, mbs, say):
    ex, bw, w, f, g = cfg
    sc = []
    for mb in mbs:
        sc.extend(mb)
    n = len(sc)
    order = [sorted(range(ex), key=lambda e: (-s[e], e)) for s in sc]

    # Rule 3: the first microbatch decides the size the whole step lives with.
    first = 0
    for i in range(len(mbs[0])):
        first += len(_want(order[i], sc[i], w, ()))
    unit = 100 * ex
    cap = (f * first * len(mbs) + unit - 1) // unit
    bud = (g * cap * bw + 99) // 100
    say("cap %d %d" % (cap, bud))

    full = (1 << cap) - 1
    freem = [full] * ex           # bit i set when slot i of that expert is free
    who = [dict() for _ in range(ex)]        # slot -> token
    # (-score, slot, token) kept ascending, so the weakest occupant - lowest score, and the
    # larger slot among equals - is the last element and a stale one pops in constant time.
    weak = [[] for _ in range(ex)]
    pl_e = [[] for _ in range(n)]            # experts a token holds, in rank order
    pl_s = [[] for _ in range(n)]            # the matching slot indices
    wl = [()] * n
    shut = [set() for _ in range(n)]         # experts that have refused this token
    spent = [False] * n                      # already displaced once this step
    queued = []

    def low(e):
        m = freem[e]
        return (m & -m).bit_length() - 1 if m else -1

    def hold(e, slot, tid):
        freem[e] &= ~(1 << slot)
        who[e][slot] = tid
        bisect.insort(weak[e], (-sc[tid][e], slot, tid))

    def give(e, slot):
        freem[e] |= 1 << slot
        del who[e][slot]

    def frail(e):
        row = weak[e]
        while row:
            negs, slot, tid = row[-1]
            if who[e].get(slot) == tid and not spent[tid]:
                return -negs, slot, tid
            row.pop()
        return None

    def strip(tid, r, last, hand=False):
        """Rules 6 and 7: from rank r on, the token holds nothing.

        `hand` is the displacement case, where the slot at rank r goes straight to the
        arrival and so never becomes free; only the ranks behind it are given back.
        """
        for i in range(r + 1 if hand else r, len(pl_e[tid])):
            give(pl_e[tid][i], pl_s[tid][i])
        del pl_e[tid][r:]
        del pl_s[tid][r:]
        if r == 0 and not last:
            queued.append(tid)
            say("def %d" % tid)

    def admit(tid, last):
        wl[tid] = _want(order[tid], sc[tid], w, shut[tid])
        pl_e[tid] = []
        pl_s[tid] = []
        for e in wl[tid]:
            mine = sc[tid][e]
            slot = low(e)
            if slot < 0:
                cand = frail(e)
                if cand is None or cand[0] >= mine:
                    shut[tid].add(e)
                    break
                # Rule 5: the occupant goes, and the arrival takes its slot, not a free one.
                victim = cand[2]
                seat = cand[1]
                r = pl_e[victim].index(e)
                spent[victim] = True
                shut[victim].add(e)
                strip(victim, r, last, hand=True)
                who[e][seat] = tid
                bisect.insort(weak[e], (-mine, seat, tid))
                pl_e[tid].append(e)
                pl_s[tid].append(seat)
                continue
            hold(e, slot, tid)
            pl_e[tid].append(e)
            pl_s[tid].append(slot)
        if wl[tid] and not pl_e[tid]:
            if not last:
                queued.append(tid)
                say("def %d" % tid)

    base = 0
    groups = []
    for mb in mbs:
        groups.append(list(range(base, base + len(mb))))
        base += len(mb)
    for m, group in enumerate(groups):
        run = queued[:] + group
        del queued[:]
        last = m == len(groups) - 1
        for tid in run:
            admit(tid, last)

    # Rule 9: banks in index order, and a removal here can relieve a bank not yet reached.
    for k in range(ex // bw):
        lo = k * bw
        hi = lo + bw
        load = sum(len(who[e]) for e in range(lo, hi))
        if load <= bud:
            continue
        row = []
        for e in range(lo, hi):
            for slot, tid in who[e].items():
                row.append((sc[tid][e], -e, -slot, tid))
        row.sort()
        at = 0
        while load > bud and at < len(row):
            _s, nege, negslot, tid = row[at]
            at += 1
            e = -nege
            slot = -negslot
            if who[e].get(slot) != tid:
                continue
            r = _rank_of(pl_e[tid], pl_s[tid], e, slot)
            for i in range(r, len(pl_e[tid])):
                if lo <= pl_e[tid][i] < hi:
                    load -= 1
            strip(tid, r, True)

    # Rule 10.
    demand = [0] * ex
    for tid in range(n):
        got = set(pl_e[tid])
        res = 0
        for e in wl[tid]:
            demand[e] += 1
            if e not in got:
                res += sc[tid][e]
        pairs = " ".join("%d:%d" % (pl_e[tid][i], pl_s[tid][i]) for i in range(len(pl_e[tid])))
        say("tok %d %s res %d" % (tid, pairs, res) if pairs else "tok %d res %d" % (tid, res))
    total = 0
    for e in range(ex):
        total += demand[e] * len(who[e])
    say("bal %d" % total)


def _rank_of(experts, slots, e, slot):
    for i in range(len(experts)):
        if experts[i] == e and slots[i] == slot:
            return i
    raise AssertionError("placement not on the token's own record")


def expect(lines):
    """The whole trace of a step file, as a list of lines."""
    cfg, steps = _parse(lines)
    out = []
    for mbs in steps:
        _step(cfg, mbs, out.append)
    return out
