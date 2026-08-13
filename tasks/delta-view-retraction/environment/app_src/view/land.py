from ingest import delta
from store import rows


class Edit:
    __slots__ = ("g", "v", "w", "rk")

    def __init__(self, g, v, w, rk):
        self.g = g
        self.v = v
        self.w = w
        self.rk = rk


def land(ms, d):
    prior = ms.get((d.src, d.k))
    out = []
    if prior is not None and prior.w > 0:
        out.append(Edit(prior.g, prior.v, -1, prior.key()))
    if d.op == delta.INS:
        row = rows.Row(d.k, d.g if d.g is not None else "", d.v, 1, d.seq, d.src)
    elif d.op == delta.DEL:
        if prior is None or prior.w <= 0:
            return []
        row = prior.copy()
        row.w = 0
        row.seq = d.seq
    elif d.op == delta.UPD:
        if prior is None or prior.w <= 0:
            row = rows.Row(d.k, d.g if d.g is not None else "", d.v, 1, d.seq, d.src)
        else:
            row = prior.copy()
            row.v = d.v
            if d.g is not None:
                row.g = d.g
            row.seq = d.seq
    else:
        return []
    ms.put(row)
    if row.w > 0:
        out.append(Edit(row.g, row.v, 1, row.key()))
    return out
