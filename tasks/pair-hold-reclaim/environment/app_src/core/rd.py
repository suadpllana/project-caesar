ACTS = ("bind", "unbind", "edge", "cut", "pair", "both", "look", "none")
OPS = ("new", "edge", "cut", "bind", "unbind", "pair", "both", "watch", "arm", "pass",
       "show")


def parse(text):
    ops = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        head = parts[0]
        if head not in OPS:
            raise ValueError("op %r" % head)
        if head == "arm":
            act = parts[2:]
            if not act or act[0] not in ACTS:
                raise ValueError("act %r" % (act,))
            ops.append(("arm", int(parts[1]), tuple(act)))
        elif head == "watch":
            ops.append(("watch", parts[1], parts[2], int(parts[3])))
        elif head in ("bind",):
            ops.append(("bind", parts[1], int(parts[2])))
        elif head in ("unbind", "show"):
            ops.append((head, parts[1]))
        elif head == "pass":
            ops.append(("pass",))
        elif head == "new":
            ops.append(("new", int(parts[1])))
        elif head == "both":
            ops.append(("both", int(parts[1]), int(parts[2]), int(parts[3])))
        else:
            ops.append((head, int(parts[1]), int(parts[2])))
    return ops
