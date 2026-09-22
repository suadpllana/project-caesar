"""The clock: one launch, cycle by cycle, with two exact shortcuts.

Each cycle: blocks whose work has run out are ready again; the dispatcher fills free slots;
then the multiprocessors, in number order, issue one instruction each from their rotations.

Shortcut one - a frozen stretch. When every ready block is at a spin whose attempt would fail
and change no cache (a cached spin on a line that is there, a bypassing spin on a line that is
not), and some block is busy, nothing can change until the next block comes out of its work:
no store happens, no cache moves, every attempt repeats the one before. The only thing that
moves is each rotation, one ready block per cycle, so the clock jumps to that wake and every
rotation advances by the length of the jump over its spinners. A stretch where some attempt
misses or drops a line is not frozen - a miss can push another spinner's line out - and is
stepped. Checking is cheap only after a cycle made entirely of idle attempts, so that is when
it is checked; stepping one more cycle is always exact.

Shortcut two - the hang. A launch hangs at cycle t when from t on every placed block that has
not exited sits at a spin, none is busy, and no attempt ever succeeds. From the first cycle
of such a stretch the machine is closed: no store, no exit, no placement. If it is frozen, it
is hung from the stretch's first cycle. If not, its caches and rotations are all that can
change, so it is stepped until an attempt succeeds (the stretch is over) or a state repeats
(it never will), and the hang is reported at the cycle the stretch began.
"""
import heapq

from sim import load
from sim.mem import Mem
from sim.place import Place
from sim.step import MOVED, OTHER, PASS, QUIET, frozen, spinning, step
from sim.turn import Turn


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.busy = 0
        b.slot = None
    mem = Mem(launch.mem, launch.sms, launch.lines)
    pl = Place(launch)
    rows = pl.rows
    turns = [Turn(launch.slots) for _ in range(launch.sms)]
    sms = range(launch.sms)
    wakes = []
    live = 0
    spin = 0
    t = 0
    phase, seen = None, None
    quiet = False

    def ready_any():
        for row in rows:
            for b in row:
                if b is not None and b.end is None and b.busy <= t:
                    return True
        return False

    def all_frozen():
        for s in sms:
            for b in rows[s]:
                if b is not None and b.end is None and b.busy <= t:
                    if not spinning(launch, b) or not frozen(launch, mem, b):
                        return False
        return True

    def snapshot():
        return (tuple(tuple((ln, tuple(w)) for ln, w in c.rows.items()) for c in mem.l1),
                tuple(tu.last for tu in turns))

    while True:
        while wakes and wakes[0] <= t:
            heapq.heappop(wakes)
        for b in pl.fill(blocks, t):
            live += 1
            spin += spinning(launch, b)
            quiet = False
        if live == 0 and pl.next == launch.grid:
            return blocks, None, 0, mem.gm
        if spin == live and not wakes:
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
            if not ready_any():
                t = wakes[0]
                continue
            if quiet and wakes and all_frozen():
                d = wakes[0] - t
                for s in sms:
                    turns[s].skip(rows[s], t, d)
                t = wakes[0]
                continue
        quiet = True
        for s in sms:
            b = turns[s].pick(rows[s], t)
            if b is None:
                continue
            was = spinning(launch, b)
            what = step(launch, mem, b, t)
            if what != QUIET:
                quiet = False
                if what == PASS:
                    phase = None
                if b.end is not None:
                    live -= 1
                    pl.release(b)
                    spin -= was
                    continue
                if b.busy > t:
                    heapq.heappush(wakes, b.busy)
                spin += spinning(launch, b) - was
        t += 1
