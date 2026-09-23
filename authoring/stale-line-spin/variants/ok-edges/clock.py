"""The clock: one launch, cycle by cycle, except where a multiprocessor can be carried forward
without being stepped.

Each cycle: blocks whose work has run out are ready again; the dispatcher fills free slots;
then the multiprocessors, in number order, issue one instruction each from their rotations.

Lanes. When every ready block on a multiprocessor sits at a sum or a spin, its next cycles are
nothing but lines and attempts taken in rotation. Up to a point that can be computed they are
all regular - every cached sum misses and fills, every bypassing sum reads a line that is not
cached, every attempt fails and changes nothing - and over regular cycles the cache moves only
by fills, first in first out: once the room left at the start is used up, each fill pushes out
the oldest line, so a line cached when the lane opened is gone after a number of fills that
its place in the queue decides. A lane is that run of regular cycles. It is carried forward in
one move when something needs the multiprocessor as it stands:

  * the lane's own end: its first issue that might not be regular, or the one after a sum's
    last line;
  * a block of its own waking or being placed, which changes the rotation;
  * a write the lane would see: to a line one of its sums reads during the lane - always from
    memory, since a sum reaching a cached line ends the lane first - or to the line a bypassing
    spinner of it reads. Nothing else written anywhere reaches it: a cached spinner reads its
    own copy all through the lane. The write lands only after the lane has been carried up to
    it, through the writing cycle itself when the lane's multiprocessor issues first in it.

Carrying a lane forward is arithmetic: over d cycles each of its k blocks issued once in k,
each sum added a range of memory, the cache is its surviving old lines followed by its last
fills, and the rotation sits on the block that issued last.

The hang. A launch hangs at cycle t when from t on every placed block that has not exited sits
at a spin, none is busy, and no attempt ever succeeds. From the first cycle of such a stretch
the machine is closed: no store, no exit, no placement. If it is frozen, it is hung from the
stretch's first cycle. If not, its caches and rotations are all that can change, so it is
stepped until an attempt succeeds (the stretch is over) or a state repeats (it never will),
and the hang is reported at the cycle the stretch began.
"""
import heapq
from bisect import bisect_left, bisect_right, insort

from sim import load
from sim.mem import LW, Mem
from sim.place import Place
from sim.step import PASS, SPIN, TEST, begin_sum, frozen, step
from sim.turn import Turn

NEVER = 1 << 62
CA_SUM, CG_SUM, CA_SPIN, CG_SPIN = range(4)
KIND = {"sum.ca": CA_SUM, "sum.cg": CG_SUM, "spin.ca": CA_SPIN, "spin.cg": CG_SPIN}


class Lane:
    """The regular cycles ahead of one multiprocessor, from t0 up to but not including end."""
    __slots__ = ("t0", "end", "serial", "blocks", "kinds", "k", "m", "ahead", "base", "old",
                 "room", "reads", "cg", "lo", "hi")


def open_lane(launch, mem, turn, row, s, t0, serial):
    """The lane of multiprocessor s from cycle t0, or None if its first issue is not regular."""
    queue = turn.queue(row, t0)
    if not queue:
        return None
    code = launch.code
    kinds = []
    for b in queue:
        kd = KIND.get(code[b.pc].op)
        if kd is None:
            return None
        kinds.append(kd)
    k = len(queue)
    ahead = [0] * (k + 1)
    for q in range(k):
        ahead[q + 1] = ahead[q] + (kinds[q] == CA_SUM)
    m = ahead[k]
    cache = mem.l1[s]
    old = cache.order()
    room = cache.cap - len(old)
    where = {ln: p for p, ln in enumerate(old)}

    def fills(u):
        return (u // k) * m + ahead[u % k]

    end = NEVER
    base = [0] * k
    sums = []
    for q, b in enumerate(queue):
        if kinds[q] <= CG_SUM:
            begin_sum(b, code[b.pc])
            base[q] = b.line
            sums.append((q, b.line, b.line + b.left))
            end = min(end, q + (b.left - 1) * k + 1)
    if old and sums:
        ordered = sorted(old)
        for q, lo, hi in sums:
            i = bisect_left(ordered, lo)
            if i < len(ordered) and ordered[i] < hi:
                return None
    for qa, la, ha in sums:
        if kinds[qa] != CA_SUM:
            continue
        for qb, lb, hb in sums:
            first = max(la, lb)
            if qb == qa or first >= min(ha, hb):
                continue
            return None
    cg = set()
    for q, b in enumerate(queue):
        kd = kinds[q]
        if kd <= CG_SUM:
            continue
        ins = code[b.pc]
        a = load.ea(b, ins.at)
        ln = a // LW
        want = load.val(launch, b, ins.b)
        test = TEST[ins.cmp]
        if kd == CA_SPIN:
            p = where.get(ln)
            if p is None or test(cache.rows[ln][a % LW], want) or m:
                end = min(end, q)
        else:
            cg.add(ln)
            if ln in where or test(mem.word(a), want):
                end = min(end, q)
            else:
                for qa, la, ha in sums:
                    if kinds[qa] == CA_SUM and la <= ln < ha:
                        end = min(end, qa + (ln - la) * k)
    if end <= 0:
        return None
    lane = Lane()
    lane.t0, lane.end, lane.serial = t0, (t0 + end if end < NEVER else NEVER), serial
    lane.blocks, lane.kinds, lane.k, lane.m, lane.ahead = queue, kinds, k, m, ahead
    lane.base, lane.old, lane.room = base, old, room
    lane.reads = [(lo, hi) for _, lo, hi in sums]
    lane.cg = cg
    edges = list(cg) + [x for lo, hi in lane.reads for x in (lo, hi - 1)]
    lane.lo, lane.hi = (min(edges), max(edges)) if edges else (1, 0)
    return lane


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.busy = 0
        b.slot = None
        b.line = b.left = b.acc = 0
    S = launch.sms
    mem = Mem(launch.mem, S, launch.lines)
    pl = Place(launch)
    rows = pl.rows
    turns = [Turn(launch.slots) for _ in range(S)]
    code = launch.code
    at_spin = [ins.op in SPIN for ins in code] + [False]
    lanes = [None] * S
    ends = []                # (end, serial, sm) of lanes; stale entries are skipped
    wakes = []               # (cycle, block number) of blocks inside a work
    ready = [0] * S          # placed, not exited, not busy
    active = set()           # multiprocessors with no lane and a ready block: they issue now
    live = spin = 0
    serial = 0
    now = 0
    index = [None]           # (starts, spans, reach) over every open lane's sum ranges
    shut = []                # lanes closed by a write during the current issue

    def refresh(s):
        if lanes[s] is None and ready[s]:
            active.add(s)
        else:
            active.discard(s)

    def close(s, x):
        """Carry multiprocessor s's lane through every cycle before x, then drop it."""
        nonlocal spin
        lane = lanes[s]
        lanes[s] = None
        index[0] = None
        refresh(s)
        d = x - lane.t0
        if d <= 0:
            return
        k = lane.k
        for q in range(min(k, d)):
            b = lane.blocks[q]
            n = (d - 1 - q) // k + 1
            kd = lane.kinds[q]
            if kd <= CG_SUM:
                b.acc += mem.span(b.line, b.line + n)
                b.line += n
                b.left -= n
                if b.left == 0:
                    b.reg[code[b.pc].rd] = b.acc
                    b.pc += 1
                    spin += at_spin[b.pc]
            else:
                ins = code[b.pc]
                a = load.ea(b, ins.at)
                if kd == CA_SPIN:
                    b.reg[ins.rd] = mem.l1[s].rows[a // LW][a % LW]
                else:
                    b.reg[ins.rd] = mem.word(a)
        m = lane.m
        if m:
            F = (d // k) * m + lane.ahead[d % k]
            cap = mem.l1[s].cap
            cas = [q for q in range(k) if lane.kinds[q] == CA_SUM]
            fresh = {}
            for f in range(max(1, F - cap + 1), F + 1):
                r, i = divmod(f - 1, m)
                ln = lane.base[cas[i]] + r
                fresh[ln] = mem.words(ln)
            gone = min(len(lane.old), max(0, F - lane.room))
            mem.l1[s].keep(lane.old[gone:], fresh)
        turns[s].last = lane.blocks[(d - 1) % k].slot

    def reindex():
        spans = sorted((lo, hi, j) for j, lane in enumerate(lanes) if lane is not None
                       for lo, hi in lane.reads)
        reach, top = [], None
        for lo, hi, j in spans:
            top = hi if top is None or hi > top else top
            reach.append(top)
        index[0] = ([x[0] for x in spans], spans, reach)
        return index[0]

    def before_write(sm, a):
        """A write is about to land: carry up to it every lane that would see it."""
        ln = a // LW
        hit = set()
        for j in range(S):
            lane = lanes[j]
            if lane is not None and j != sm and ln in lane.cg:
                hit.add(j)
        starts, spans, reach = index[0] or reindex()
        i = bisect_right(starts, ln) - 1
        while i >= 0 and reach[i] > ln:
            lo, hi, j = spans[i]
            if ln < hi and j != sm:
                hit.add(j)
            i -= 1
        for j in hit:
            close(j, now + 1 if j < sm else now)
            shut.append(j)

    mem.before_write = before_write

    def all_frozen():
        for s in range(S):
            for b in rows[s]:
                if b is not None and b.end is None and b.busy <= now:
                    if not at_spin[b.pc] or not frozen(launch, mem, b):
                        return False
        return True

    def snapshot():
        return (tuple(tuple((ln, tuple(w)) for ln, w in c.rows.items()) for c in mem.l1),
                tuple(tu.last for tu in turns))

    t = 0
    phase, seen = None, None
    while True:
        now = t
        while wakes and wakes[0][0] <= t:
            b = blocks[heapq.heappop(wakes)[1]]
            s = b.sm
            ready[s] += 1
            lane = lanes[s]
            if lane is not None and b not in lane.blocks:
                close(s, t)
            refresh(s)
        for b in pl.fill(blocks, t):
            s = b.sm
            live += 1
            spin += at_spin[b.pc]
            ready[s] += 1
            if lanes[s] is not None:
                close(s, t)
            refresh(s)
        if live == 0 and pl.next == launch.grid:
            return blocks, None, 0, mem.gm
        while ends and ends[0][0] <= t:
            _, num, s = heapq.heappop(ends)
            if lanes[s] is not None and lanes[s].serial == num:
                close(s, t)
        stepping = spin == live and not wakes
        if stepping:
            for s in range(S):
                if lanes[s] is not None:
                    close(s, t)
            if phase is None:
                phase, seen = t, set()
            if all_frozen():
                return blocks, phase, launch.grid - pl.next, mem.gm
            key = snapshot()
            if key in seen:
                return blocks, phase, launch.grid - pl.next, mem.gm
            seen.add(key)
        else:
            phase = None
        if not active:
            nxt = wakes[0][0] if wakes else NEVER
            while ends and (lanes[ends[0][2]] is None or lanes[ends[0][2]].serial != ends[0][1]):
                heapq.heappop(ends)
            if ends and ends[0][0] < nxt:
                nxt = ends[0][0]
            t = nxt
            continue
        order = sorted(active)
        issued = []
        i = 0
        while i < len(order):
            s = order[i]
            i += 1
            b = turns[s].pick(rows[s], t)
            was = at_spin[b.pc]
            if step(launch, mem, b, t) == PASS:
                phase = None
            if b.end is not None:
                live -= 1
                spin -= was
                ready[s] -= 1
                pl.release(b)
                refresh(s)
            else:
                if b.busy > t:
                    heapq.heappush(wakes, (b.busy, b.n))
                    ready[s] -= 1
                    refresh(s)
                spin += at_spin[b.pc] - was
            issued.append((s, b))
            if shut:
                for j in shut:
                    if j > s and j not in order:
                        insort(order, j)
                del shut[:]
        if not stepping:
            for s, b in issued:
                if lanes[s] is not None or not ready[s]:
                    continue
                if b.end is None and b.busy <= t + 1 and code[b.pc].op not in KIND:
                    continue
                serial += 1
                lane = open_lane(launch, mem, turns[s], rows[s], s, t + 1, serial)
                if lane is not None:
                    lanes[s] = lane
                    index[0] = None
                    active.discard(s)
                    if lane.end < NEVER:
                        heapq.heappush(ends, (lane.end, serial, s))
        t += 1
        if stepping or len(active) != 1:
            continue
        # One multiprocessor issues and nothing else can happen before the next wake or lane
        # end: its cycles need none of the bookkeeping above, until it writes (a write may
        # reach another multiprocessor's lane, which must then issue in the same cycle), a slot
        # is waiting to be filled, or every block left is spinning.
        (s,) = active
        horizon = wakes[0][0] if wakes else NEVER
        while ends and (lanes[ends[0][2]] is None or lanes[ends[0][2]].serial != ends[0][1]):
            heapq.heappop(ends)
        if ends and ends[0][0] < horizon:
            horizon = ends[0][0]
        row, turn = rows[s], turns[s]
        while t < horizon and ready[s] and lanes[s] is None and not pl.gone and spin < live:
            was_last = turn.last
            b = turn.pick(row, t)
            op = code[b.pc].op
            if op == "st" or op == "atom.add":
                turn.last = was_last        # not issued here: the full cycle issues it
                break
            was = at_spin[b.pc]
            now = t
            step(launch, mem, b, t)
            if b.end is not None:
                live -= 1
                spin -= was
                ready[s] -= 1
                pl.release(b)
                refresh(s)
                t += 1
                break
            if b.busy > t:
                heapq.heappush(wakes, (b.busy, b.n))
                ready[s] -= 1
                refresh(s)
                if b.busy < horizon:
                    horizon = b.busy
            spin += at_spin[b.pc] - was
            t += 1
            if ready[s] and (b.busy >= t + 1 or code[b.pc].op in KIND):
                serial += 1
                lane = open_lane(launch, mem, turn, row, s, t, serial)
                if lane is not None:
                    lanes[s] = lane
                    index[0] = None
                    active.discard(s)
                    if lane.end < NEVER:
                        heapq.heappush(ends, (lane.end, serial, s))
