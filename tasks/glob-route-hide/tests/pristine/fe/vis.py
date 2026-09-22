def seen(ln, owner, reader):
    if ln.pb:
        return True
    return reader == owner
