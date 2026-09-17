from led import hold


def charge(st, name):
    total = 0
    seen = set()
    for one in st.lines.values():
        for chain in one.cells.values():
            for e in chain.ents:
                if id(e.blk) in seen:
                    continue
                seen.add(id(e.blk))
                if hold.who(st, e.blk) == {name}:
                    total += e.blk.size
    return total
