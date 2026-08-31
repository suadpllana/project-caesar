PLAIN = ("S", "P", "W", "H", "M", "F", "N")


def _row(tok):
    k = tok[0]
    if k == "S":
        return ("S", int(tok[1]))
    if k == "P":
        return ("P",)
    if k == "W":
        return ("W", int(tok[1]))
    if k == "H":
        return ("H", int(tok[1]))
    if k == "M":
        return ("M", int(tok[1]))
    if k == "F":
        return ("F",)
    if k == "N":
        return ("N", tok[1])
    if k == "G":
        return ("G", int(tok[1]), int(tok[2]), int(tok[3]), -1)
    if k == "E":
        return ("E",)
    if k == "B":
        return ("B", int(tok[1]), -1)
    if k == "X":
        return ("X",)
    raise ValueError(k)


def parse(text):
    out = {}
    name = None
    body = []
    hold = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(":"):
            if name is not None:
                out[name] = link(body)
            name = line[1:].strip()
            body = []
            hold = None
            continue
        tok = line.split()
        if tok[0] == "A":
            hold = []
            continue
        if tok[0] == "Z":
            body.append(("A", tuple(hold)))
            hold = None
            continue
        r = _row(tok)
        if hold is not None:
            if r[0] not in PLAIN or r[0] == "N":
                raise ValueError(r[0])
            hold.append(r)
        else:
            body.append(r)
    if name is not None:
        out[name] = link(body)
    return out


def link(body):
    ops = list(body)
    st = []
    for i, op in enumerate(ops):
        k = op[0]
        if k == "G" or k == "B":
            st.append(i)
        elif k == "E" or k == "X":
            j = st.pop()
            want = "G" if k == "E" else "B"
            if ops[j][0] != want:
                raise ValueError(k)
            ops[j] = ops[j][:-1] + (i,)
    if st:
        raise ValueError("open")
    return tuple(ops)
