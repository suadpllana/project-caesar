"""Charges, handed to the engine in dev.py."""
from store import dev


def setup(st):
    return None


def charge(st, name):
    return dev.do_charge(st.w, name)


def gone(st, names):
    return dev.do_gone(st.w, names)
