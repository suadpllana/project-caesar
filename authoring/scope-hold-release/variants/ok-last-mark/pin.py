from wire.scope import ROOT


def where(st, at, tag):
    hit = ROOT
    for sc in st.upto(at):
        if st.tag(sc) == tag:
            hit = sc
    return hit
