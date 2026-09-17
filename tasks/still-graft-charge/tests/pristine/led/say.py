def full(st, name):
    st.out.append("full %s" % name)


def busy(st, still):
    st.out.append("busy %s" % still)


def gone(st, still, size):
    st.out.append("free %s %d" % (still, size))


def charge(st, name, size):
    st.out.append("charge %s %d" % (name, size))


def at(st, name, cell, num):
    st.out.append("at %s %d %s" % (name, cell, "-" if num is None else num))
