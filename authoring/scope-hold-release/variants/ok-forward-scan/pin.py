from wire.scope import ROOT


def where(st, at, tag):
    found = ROOT
    for sc in st.upto(at):
        if st.tag(sc) == tag:
            found = sc
    return found
