from . import spread


def sprout(st, nid, pa, seq):
    st.mk(nid, pa)
    spread.flow(st, nid)


def shut(st, nid, seq):
    st.bar(nid, True)


def free(st, nid, seq):
    st.bar(nid, False)
    spread.flow(st, nid)


def move(st, nid, dst, seq):
    st.relink(nid, dst)
    spread.flow(st, nid)
