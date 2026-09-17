def arrive(st, name):
    st.oid.add(name)


def hand(st, name):
    st.nid += 1
    st.sid[name] = "s%d" % st.nid
    return st.sid[name]


def got(st, name):
    return name in st.sid or name in st.oid


def show(st, name):
    return st.sid.get(name, name)
