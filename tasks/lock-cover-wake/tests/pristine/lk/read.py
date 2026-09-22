def parse(text):
    out = []
    for line in text.splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == "cfg":
            out.append(("cfg", int(f[1])))
        elif f[0] == "beg":
            out.append(("beg", int(f[1])))
        elif f[0] == "req":
            out.append(("req", int(f[1]), f[2], f[3]))
        elif f[0] == "com":
            out.append(("com", int(f[1])))
    return out


def split_res(res):
    dot = res.find(".")
    if dot < 0:
        return int(res), -1
    return int(res[:dot]), int(res[dot + 1:])
