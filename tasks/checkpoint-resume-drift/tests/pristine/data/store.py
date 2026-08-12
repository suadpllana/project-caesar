MASK = 0xFFFFFFFF


def _mix(a, b):
    v = (a * 2654435761 + b * 40503 + 0x9E37) & MASK
    v ^= v >> 13
    v = (v * 1274126177) & MASK
    return v ^ (v >> 16)


class Store:
    def __init__(self, cfg, meter):
        self.n = cfg["nsamp"]
        self.sd = cfg["seed"]
        self.mt = meter

    def size(self, sid):
        return 2 + _mix(self.sd, sid) % 20

    def raw(self, sid):
        self.mt.reads += 1
        return [1 + _mix(sid * 31 + i, self.sd) % 61 for i in range(self.size(sid))]

    def snap(self):
        out = []
        for sid in range(self.n):
            out.append(sid)
            out.extend(1 + _mix(sid * 31 + i, self.sd) % 61 for i in range(self.size(sid)))
        return out

    def rest(self, vec):
        return None
