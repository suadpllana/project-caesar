from sim import load
from sim.mem import Mem
from sim.place import Place
from sim.step import at_spin, idle_attempt, run_one
from sim.turn import Turn, ready


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.until = 0
        b.slot = None
    mem = Mem(launch.mem, launch.sms, launch.lines)
    pl = Place(launch)
    turns = [Turn(launch.slots) for _ in range(launch.sms)]
    t = 0
    stretch = None
    seen = set()
    calm = False
    while True:
        if pl.cycle(blocks, t):
            calm = False
        live = [b for row in pl.slots for b in row if b is not None and b.end is None]
        if not live:
            if pl.waiting == launch.grid:
                return blocks, None, 0, mem.words
        busy = [b.until for b in live if b.until > t]
        rdy = [b for b in live if b.until <= t]
        if not busy and all(at_spin(launch, b) for b in live):
            if stretch is None:
                stretch, seen = t, set()
            if all(idle_attempt(launch, mem, b) for b in rdy):
                return blocks, stretch, launch.grid - pl.waiting, mem.words
            key = (mem.state(), tuple(tu.prev for tu in turns))
            if key in seen:
                return blocks, stretch, launch.grid - pl.waiting, mem.words
            seen.add(key)
        else:
            stretch = None
            if not rdy:
                t = min(busy)
                continue
            if calm and busy and all(at_spin(launch, b) and idle_attempt(launch, mem, b)
                                     for b in rdy):
                nxt = min(busy)
                for sm, tu in enumerate(turns):
                    tu.advance(pl.slots[sm], t, nxt - t)
                t = nxt
                continue
        calm = True
        for sm, tu in enumerate(turns):
            b = tu.pick(pl.slots[sm], t)
            if b is None:
                continue
            kind = run_one(launch, mem, b, t)
            if kind != "idle":
                calm = False
            if kind == "passed":
                stretch = None
            if b.end is not None:
                pl.exit(b)
        t += 1
