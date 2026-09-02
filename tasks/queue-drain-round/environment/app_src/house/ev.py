from house import bk


def read(text):
    who = []
    run = 0
    rows = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f = ln.split()
        if f[0] == "who":
            who = f[1:]
        elif f[0] == "run":
            run = int(f[1])
        elif f[1] == "fund":
            rows.append((int(f[0]), "fund", f[2], int(f[3])))
        elif f[1] == "owe":
            rows.append((int(f[0]), "owe", f[2], f[3], f[4], int(f[5]), int(f[6])))
    return who, run, rows


def feed(b, rows, t):
    for r in rows:
        if r[0] != t:
            continue
        if r[1] == "fund":
            b.top(r[2], r[3])
        else:
            b.book(r[2], r[3], r[4], r[5], r[6])
