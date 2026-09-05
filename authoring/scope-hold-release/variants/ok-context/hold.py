def note(bk, tok, at):
    bk.setdefault(at, []).append(tok)


def at_of(bk, tok, st):
    for at in sorted(bk):
        if tok in bk[at]:
            return at
    return st.top()
