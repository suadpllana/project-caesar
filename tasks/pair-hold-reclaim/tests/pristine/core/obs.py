from core.st import PLAIN


def fade(st, out):
    seen = set(out)
    for nm in st.wt:
        w = st.wt[nm]
        if w.off or w.kd != PLAIN:
            continue
        if w.tgt in seen:
            st.wipe(w)


def close(st, i):
    for w in st.watches(i):
        st.wipe(w)
