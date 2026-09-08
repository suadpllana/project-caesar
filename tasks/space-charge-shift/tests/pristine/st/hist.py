from st import tree


def inv(r):
    k = r[0]
    if k == "mkd":
        return ("rmd",) + r[1:]
    if k == "rmd":
        return ("mkd",) + r[1:]
    if k == "ln":
        return ("ul",) + r[1:]
    if k == "ul":
        return ("ln",) + r[1:]
    if k == "mvl":
        return ("mvl", r[1], r[3], r[2], r[5], r[4], r[6])
    if k == "mvd":
        return ("mvd", r[1], r[3], r[2], r[5], r[4])
    if k == "nw":
        return ("dl",) + r[1:]
    if k == "dl":
        return ("nw",) + r[1:]
    if k == "ct":
        return ("ct", r[1], r[3], r[2])
    if k == "lm":
        return ("lm", r[1], r[3], r[2])
    raise ValueError(k)


def put(st, r):
    k = r[0]
    if k == "mkd":
        st.dirs[r[1]] = tree.D(r[2])
        st.dirs[r[2]].ent[r[3]] = ("d", r[1])
    elif k == "rmd":
        del st.dirs[r[2]].ent[r[3]]
        del st.dirs[r[1]]
    elif k == "mvd":
        del st.dirs[r[2]].ent[r[4]]
        st.dirs[r[3]].ent[r[5]] = ("d", r[1])
        st.dirs[r[1]].up = r[3]
    elif k == "ln":
        st.dirs[r[2]].ent[r[3]] = ("l", r[1], r[4])
        st.itm[r[1]].nl += 1
        if r[4] > st.age:
            st.age = r[4]
    elif k == "ul":
        del st.dirs[r[2]].ent[r[3]]
        st.itm[r[1]].nl -= 1
    elif k == "mvl":
        del st.dirs[r[2]].ent[r[4]]
        st.dirs[r[3]].ent[r[5]] = ("l", r[1], r[6])
    elif k == "ct":
        st.itm[r[1]].tag = r[3]
    elif k == "nw":
        st.itm[r[1]] = tree.It(r[2])
        st.used.add(r[1])
    elif k == "dl":
        del st.itm[r[1]]
    elif k == "lm":
        st.lim[r[1]] = r[3]
    else:
        raise ValueError(k)


def run(st, eff, hook):
    for r in eff:
        put(st, r)
        hook(st, r)


def mark(st, nm):
    for got, _ in st.marks:
        if got == nm:
            return False
    st.marks.append((nm, len(st.log)))
    return True


def back(st, nm, hook):
    at = None
    for j in range(len(st.marks)):
        if st.marks[j][0] == nm:
            at = j
            break
    if at is None:
        return False
    want = st.marks[at][1]
    del st.marks[at:]
    born = set()
    for eff in st.log[want:]:
        for r in eff:
            if r[0] == "nw":
                born.add(r[1])
    kept = set(a for a in born if a in st.itm and st.itm[a].hld)
    while len(st.log) > want:
        eff = st.log.pop()
        for r in reversed(eff):
            if r[1] in kept and r[0] in ("nw", "ct"):
                continue
            q = inv(r)
            put(st, q)
            hook(st, q)
    return True
