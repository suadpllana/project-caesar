from mkt.bk import Ord


def num(tok):
    return None if tok == "-" else int(tok)


def read(text):
    cap = 0
    mark = 0
    msgs = []
    for raw in text.splitlines():
        f = raw.split()
        if not f:
            continue
        if f[0] == "cap":
            cap = int(f[1])
        elif f[0] == "mark":
            mark = int(f[1])
        elif f[0] == "pull":
            msgs.append(("pull", int(f[1])))
        elif f[0] == "new":
            o = Ord(int(f[1]), int(f[2]), f[3], num(f[4]), int(f[5]),
                    num(f[6]), f[7], num(f[8]))
            msgs.append(("new", o))
        else:
            raise ValueError(raw)
    return cap, mark, msgs
