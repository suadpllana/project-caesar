from core.st import PLAIN


def fade(st, out):
    doomed = list(out)
    for w in [st.wt[nm] for nm in list(st.wt)]:
        if w.kd == PLAIN and not w.off and w.tgt in doomed:
            st.wipe(w)


def close(st, i):
    for w in list(st.watches(i)):
        st.wipe(w)
