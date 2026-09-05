def note(bk, tok, at):
    bk[tok] = at


def at_of(bk, tok, st):
    a = bk.get(tok, st.top())
    d = st.under(a)
    return d[-1] if d else a
