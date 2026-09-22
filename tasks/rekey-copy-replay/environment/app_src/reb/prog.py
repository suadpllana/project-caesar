def read(text):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        part = line.split()
        head = part[0]
        if head == "cfg":
            out.append(("cfg", int(part[1])))
        elif head == "set":
            out.append(("set", int(part[1]), int(part[2]), int(part[3]), int(part[4])))
        elif head == "del":
            out.append(("del", int(part[1])))
        elif head == "copy":
            out.append(("copy",))
        elif head == "play":
            out.append(("play", int(part[1])))
        elif head == "cut":
            out.append(("cut",))
        else:
            raise ValueError(head)
    return out
