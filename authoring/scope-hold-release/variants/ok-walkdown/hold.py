def note(bk, tok, at):
    bk[tok] = at


def at_of(bk, tok, st):
    return bk.get(tok, st.top())
