from base import tape


def band(st, name, keys):
    st.grp[name] = list(keys)


def pack(st, w, g):
    view = tape.seat(st, w)
    st.parc.append(dict((s, view[s]) for s in st.grp.get(g, ()) if s in view))
    return len(st.parc)


def held(st, w):
    return st.bag.setdefault(w, [])
