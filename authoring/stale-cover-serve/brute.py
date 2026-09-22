"""The slowest possible correct engine, for differential testing only.

It keeps a full snapshot of the store for every version and answers the serving question by
trying every version from the present one down to the allowance floor, testing coverage by
walking the whole stretch table at each one. That is exactly the naive family the resource
gate is aimed at, which makes it useful twice: it is a third independent reading of the
contract, and it is the thing whose timings prove the gate bites.

Never shipped. Authoring only.
"""


class Part(object):
    __slots__ = ("lo", "hi", "born", "died", "dead")

    def __init__(self, lo, hi, born):
        self.lo = lo
        self.hi = hi
        self.born = born
        self.died = -1
        self.dead = False


def covered(parts, lo, hi, at):
    need = set(range(lo, hi + 1))
    for p in parts:
        if p.dead:
            continue
        if p.born > at:
            continue
        if 0 <= p.died < at:
            continue
        for k in range(max(p.lo, lo), min(p.hi, hi) + 1):
            need.discard(k)
    return not need


def trace(text):
    horizon = 0
    slack = 0
    cap = 1
    top = 0
    ops = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        if bits[0] == "h":
            horizon = int(bits[1])
            slack = int(bits[2])
            cap = int(bits[3])
        elif bits[0] == "w":
            ops.append(("w", int(bits[1]), int(bits[2]), 0))
            top = max(top, int(bits[1]))
        elif bits[0] == "x":
            ops.append(("x", int(bits[1]), 0, 0))
            top = max(top, int(bits[1]))
        elif bits[0] == "c":
            ops.append(("c", 0, 0, 0))
        elif bits[0] == "r":
            ops.append(("r", int(bits[1]), int(bits[2]), int(bits[3])))
            top = max(top, int(bits[2]))
        else:
            raise ValueError(line)

    span = top + 1
    snaps = [dict()]
    touch = [0] * span
    parts = []
    staged = []
    lines = []
    for op in ops:
        if op[0] == "w":
            staged.append((op[1], op[2]))
        elif op[0] == "x":
            staged.append((op[1], None))
        elif op[0] == "c":
            last = {}
            for k, v in staged:
                last[k] = v
            staged = []
            cur = dict(snaps[-1])
            for k in last:
                if last[k] is None:
                    cur.pop(k, None)
                else:
                    cur[k] = last[k]
            snaps.append(cur)
            now = len(snaps) - 1
            for k in last:
                touch[k] = now
            for p in parts:
                if p.dead or p.died >= 0:
                    continue
                for k in last:
                    if p.lo <= k <= p.hi:
                        p.died = now - 1
                        break
            if now - horizon > 0:
                for p in parts:
                    if 0 <= p.died < now - horizon:
                        p.dead = True
            lines.append("v %d" % now)
        else:
            lo, hi, s = op[1], op[2], op[3]
            now = len(snaps) - 1
            floor = now - s
            if floor < 0:
                floor = 0
            at = None
            for v in range(now, floor - 1, -1):
                if covered(parts, lo, hi, v):
                    at = v
                    break
            if at is None:
                holes = []
                run = None
                for k in range(lo, hi + 1):
                    ok = False
                    for p in parts:
                        if not p.dead and p.died < 0 and p.lo <= k <= p.hi:
                            ok = True
                            break
                    if ok:
                        if run is not None:
                            holes.append(run)
                            run = None
                    else:
                        if run is None:
                            run = [k, k]
                        else:
                            run[1] = k
                if run is not None:
                    holes.append(run)
                if holes:
                    joined = [holes[0]]
                    for a, b in holes[1:]:
                        if a - joined[-1][1] - 1 <= slack:
                            joined[-1][1] = b
                        else:
                            joined.append([a, b])
                    holes = [(lo, hi)] if len(joined) > cap else [tuple(x) for x in joined]
                for a, b in holes:
                    lines.append("f %d %d" % (a, b))
                    mark = 0
                    for k in range(a, b + 1):
                        if touch[k] > mark:
                            mark = touch[k]
                    parts.append(Part(a, b, mark))
                at = now
            snap = snaps[at]
            rows = [(k, snap[k]) for k in range(lo, hi + 1) if k in snap]
            if rows:
                lines.append("a %d %s" % (at, " ".join("%d=%d" % kv for kv in rows)))
            else:
                lines.append("a %d -" % at)
    return lines
