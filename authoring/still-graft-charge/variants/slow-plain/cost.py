from led import hold


def mine(st, name):
    one = st.lines[name]
    seen = {}
    for b in one.head.values():
        seen[id(b)] = b
    for s in one.stills:
        for b in st.stills[s].held.values():
            seen[id(b)] = b
    return seen.values()


def charge(st, name):
    total = 0
    for b in mine(st, name):
        if hold.who(b) == {name}:
            total += b.size
    return total
