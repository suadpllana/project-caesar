from wire.scope import ROOT


def where(st, at, tag):
    for sc in reversed(st.upto(st.top())):
        if st.tag(sc) == tag:
            return sc
    return ROOT
