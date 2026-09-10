"""Items, handed to the engine in dev.py."""
from store import dev


def setup(st):
    return None


def write(st, ln, nm, at, n):
    return dev.do_write(st.w, ln, nm, at, n)


def share(st, sl, sn, at, n, dl, dn, to):
    return dev.do_share(st.w, sl, sn, at, n, dl, dn, to)


def trim(st, ln, nm, n):
    return dev.do_trim(st.w, ln, nm, n)


def erase(st, ln, nm):
    return dev.do_erase(st.w, ln, nm)


def vac(st, ln, nm):
    return dev.do_vac(st.w, ln, nm)


def chart(st, ln, nm):
    return dev.do_chart(st.w, ln, nm)
