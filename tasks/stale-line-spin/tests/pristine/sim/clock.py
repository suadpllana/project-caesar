from sim import load
from sim.mem import Mem
from sim.place import Place
from sim.step import step
from sim.turn import Turn


def run(launch):
    blocks = [load.Blk(n) for n in range(launch.grid)]
    for b in blocks:
        b.busy = 0
        b.wait = None
    mem = Mem(launch.mem)
    pl = Place(launch, mem)
    turns = [Turn(launch.slots) for _ in range(launch.sms)]
    t = 0
    gone = []
    while True:
        for b in gone:
            pl.free(b)
        gone = []
        pl.fill(blocks, t)
        live = pl.live()
        if not live and pl.next == launch.grid:
            return blocks, None, 0, mem.gm
        ran = False
        for s in range(launch.sms):
            b = turns[s].pick(pl.rows[s], t)
            if b is None:
                continue
            ran = True
            hit = step(launch, mem, b, t)
            if b.end is not None:
                gone.append(b)
            if hit is not None:
                for w in live:
                    if w.wait == hit:
                        w.wait = None
        if not ran:
            later = [b.busy for b in live if b.busy > t]
            if not later:
                return blocks, t, launch.grid - pl.next, mem.gm
            t = min(later)
            continue
        t += 1
