from store import hold, item, tally


def setup(st):
    st.lines = {}
    st.kin = {}


def fresh(st, name):
    if name in st.lines:
        return "dup"
    st.lines[name] = {}
    tally.start(st, name)
    return None


def stamp(st, src, dst):
    if src not in st.lines:
        return "nosuch"
    if dst in st.lines:
        return "dup"
    st.lines[dst] = {}
    st.kin[dst] = src
    tally.start(st, dst)
    kit = st.lines[dst]
    for nm, it in st.lines[src].items():
        twin = item.Item(dst)
        twin.size = it.size
        for cl in it.cl:
            copy = hold.Claim(twin, cl.at, cl.sp, cl.off, cl.wide)
            twin.cl.append(copy)
            twin.ats.append(cl.at)
            hold.add(st, copy)
        kit[nm] = twin
    return (len(kit),)


def drop(st, name):
    if name not in st.lines:
        return "nosuch"
    for it in st.lines[name].values():
        for cl in it.cl:
            hold.rip(st, cl)
        it.cl = []
        it.ats = []
    del st.lines[name]
    st.kin.pop(name, None)
    tally.end(st, name)
    return (0,)
