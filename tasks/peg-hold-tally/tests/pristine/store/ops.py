from keep import cover, edge, gone, live, sole


def place(h, v, x, b):
    old = h.sp.now(v, x)
    if old == b:
        return
    h.sp.put(v, x, b, h.t)
    if old is not None:
        live.free(h.ac, v, x, old, h.t)
    if b is not None:
        live.hold(h.ac, v, x, b, h.t)


def ex(h, bits, acc):
    h.t += 1
    kind = bits[0]
    if kind == "vol":
        h.sp.vol(bits[1])
    elif kind == "set":
        b = h.sp.mint()
        live.born(h.ac, b, h.t)
        place(h, bits[1], bits[2], b)
    elif kind == "clr":
        place(h, bits[1], bits[2], None)
    elif kind == "dup":
        place(h, bits[1], bits[2], h.sp.now(bits[1], bits[3]))
    elif kind == "peg":
        h.mk.add(bits[1], bits[2], h.t)
        cover.pegged(h.ac, bits[1], bits[2], h.t)
    elif kind == "shed":
        h.mk.cut(bits[1])
        edge.shed(h.ac, bits[1], h.t)
    elif kind == "fork":
        v, t = h.mk.home(bits[2])
        h.sp.vol(bits[1])
        for x in h.sp.xs[v]:
            b = h.sp.then(v, x, t)
            if b is not None:
                place(h, bits[1], x, b)
    elif kind == "back":
        v, t = h.mk.home(bits[3])
        place(h, bits[1], bits[2], h.sp.then(v, bits[4], t))
    elif kind == "trim":
        for b in gone.trim(h.ac, h.t):
            acc.append("gone b%d" % b)
    elif kind == "tally":
        acc.append("tally %s %d" % (bits[1], sole.count(h.ac, bits[1])))
    else:
        raise ValueError(kind)
