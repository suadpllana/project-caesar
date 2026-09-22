def live(ln, on):
    return ln.cf is None or (ln.cf in on) == ln.cv
