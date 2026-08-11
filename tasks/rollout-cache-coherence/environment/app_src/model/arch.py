D = 8
V = 64
L = 4
M = 2147483647
EOS = 0

MODS = ("wq", "wk", "wv", "wo", "w1", "w2")

TIES = {"l3.wq": "l1.wq"}


def pid_list():
    out = ["emb"]
    for i in range(L):
        for m in MODS:
            out.append("l" + str(i) + "." + m)
    out.append("gsc")
    out.append("head")
    return out


def store_of(pid):
    return TIES.get(pid, pid)


def store_ids():
    seen = []
    for p in pid_list():
        s = store_of(p)
        if s not in seen:
            seen.append(s)
    return seen


def dims(pid):
    if pid == "emb":
        return (V, D)
    if pid == "gsc":
        return (1, D)
    if pid == "head":
        return (D, V)
    return (D, D)


def mix64(x):
    x &= 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 33)) * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    x = ((x ^ (x >> 33)) * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    return x ^ (x >> 33)


def tag(text, salt=0):
    h = mix64(salt ^ 0x243F6A8885A308D3)
    for ch in str(text):
        h = mix64(h ^ ord(ch))
    return h


def mat(pid, seed):
    r, c = dims(pid)
    s = mix64(tag(pid) ^ mix64(seed))
    rows = []
    for _ in range(r):
        row = []
        for _ in range(c):
            s = mix64(s + 0x9E3779B97F4A7C15)
            row.append(s % M)
        rows.append(tuple(row))
    return tuple(rows)
