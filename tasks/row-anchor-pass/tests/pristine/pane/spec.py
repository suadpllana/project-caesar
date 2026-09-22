class Bad(Exception):
    pass


class Cfg:
    __slots__ = ("vh", "over", "pcap", "est", "cap")

    def __init__(self, vh, over, pcap, est, cap):
        self.vh = vh
        self.over = over
        self.pcap = pcap
        self.est = est
        self.cap = cap


def _ints(bits, want, kind):
    if len(bits) != want:
        raise Bad("bad %s line" % kind)
    try:
        return [int(b) for b in bits[1:]]
    except ValueError:
        raise Bad("bad %s line" % kind)


def parse(text):
    cfg = None
    decls = []
    evs = []
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        kind = bits[0]
        if kind == "cfg":
            if cfg is not None:
                raise Bad("cfg twice")
            vh, over, pcap, est, cap = _ints(bits, 6, "cfg")
            if vh < 1 or over < 0 or pcap < 1 or est < 1 or cap < 1:
                raise Bad("bad cfg")
            cfg = Cfg(vh, over, pcap, est, cap)
        elif kind == "g":
            if cfg is None or evs:
                raise Bad("g line out of place")
            gid, hh, lo, hi, n = _ints(bits, 6, "g")
            if gid in seen:
                raise Bad("group %d twice" % gid)
            if hh < 1 or lo < 1 or hi < lo or n < 0:
                raise Bad("bad group %d" % gid)
            seen.add(gid)
            decls.append((gid, hh, lo, hi, n))
        elif kind == "scroll":
            evs.append(("scroll", _ints(bits, 2, "scroll")[0], 0, 0))
        elif kind == "go":
            p = _ints(bits, 2, "go")[0]
            if p < 0:
                raise Bad("bad go")
            evs.append(("go", p, 0, 0))
        elif kind == "size":
            v = _ints(bits, 2, "size")[0]
            if v < 1:
                raise Bad("bad size")
            evs.append(("size", v, 0, 0))
        elif kind in ("ins", "del"):
            gid, pos, n = _ints(bits, 4, kind)
            if gid not in seen or pos < 0 or n < 1:
                raise Bad("bad %s" % kind)
            evs.append((kind, gid, pos, n))
        else:
            raise Bad("unknown line %r" % kind)
    if cfg is None:
        raise Bad("no cfg")
    if not decls:
        raise Bad("no groups")
    return cfg, decls, evs
