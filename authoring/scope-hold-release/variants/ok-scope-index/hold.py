def note(bk, tok, at):
    bk.setdefault(at, set()).add(tok)


def at_of(bk, tok, st):
    for at, toks in bk.items():
        if tok in toks:
            return at
    return st.top()
