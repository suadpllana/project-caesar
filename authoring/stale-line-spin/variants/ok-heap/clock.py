import heapq

from sim import load
from sim.mem import Mem
from sim.place import Place
from sim.step import execute, idle, parked
from sim.turn import Turn


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.free_at = 0
        b.slot = None
    mem = Mem(launch.mem, launch.sms, launch.lines)
    pl = Place(launch)
    cells = pl.cells
    turns = [Turn(launch.slots) for _ in range(launch.sms)]
    events = []
    live = spinners = 0
    t = 0
    since, states = None, None
    still = False

    def all_idle():
        for s, tu in enumerate(turns):
            row = cells[s]
            for j in tu.ready:
                b = row[j]
                if not parked(launch, b) or not idle(launch, mem, b):
                    return False
        return True

    while True:
        while events and events[0][0] <= t:
            n = heapq.heappop(events)[1]
            turns[blocks[n].sm].add(blocks[n].slot)
        for b in pl.admit(blocks, t):
            turns[b.sm].add(b.slot)
            live += 1
            spinners += parked(launch, b)
            still = False
        if not live and pl.next == launch.grid:
            return blocks, None, 0, mem.cells
        if spinners == live and not events:
            if since is None:
                since, states = t, set()
            if all_idle():
                return blocks, since, launch.grid - pl.next, mem.cells
            key = (tuple(c.key() for c in mem.l1), tuple(tu.last for tu in turns))
            if key in states:
                return blocks, since, launch.grid - pl.next, mem.cells
            states.add(key)
        else:
            since = None
            if not any(tu.ready for tu in turns):
                t = events[0][0]
                continue
            if still and events and all_idle():
                d = events[0][0] - t
                for tu in turns:
                    tu.skip(d)
                t = events[0][0]
                continue
        still = True
        for s, tu in enumerate(turns):
            j = tu.pick()
            if j is None:
                continue
            b = cells[s][j]
            was = parked(launch, b)
            kind = execute(launch, mem, b, t)
            if kind != "idle":
                still = False
            if kind == "pass":
                since = None
            if b.end is not None:
                tu.drop(j)
                live -= 1
                spinners -= was
                pl.leave(b)
                continue
            if b.free_at > t:
                tu.drop(j)
                heapq.heappush(events, (b.free_at, b.n))
            spinners += parked(launch, b) - was
        t += 1
