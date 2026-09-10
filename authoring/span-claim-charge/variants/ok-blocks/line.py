"""Lines, handed to the engine in dev.py."""
from store import dev


def setup(st):
    return None


def fresh(st, name):
    return dev.do_fresh(st.w, name)


def stamp(st, src, dst):
    return dev.do_stamp(st.w, src, dst)


def drop(st, name):
    return dev.do_drop(st.w, name)
