_plain = get


def get(f, name):
    v = _plain(f, name)
    if f.out:
        f.out[-1] = {"val": name, "v": v}
    return v
