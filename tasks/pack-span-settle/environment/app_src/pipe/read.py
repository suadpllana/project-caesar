def ops(path):
    out = []
    with open(path, "r") as fh:
        for line in fh:
            part = line.split()
            if not part:
                continue
            k = part[0]
            if k == "rec":
                out.append((k, part[1], int(part[2]), int(part[3])))
            elif k == "seal":
                out.append((k,))
            elif k in ("width", "span", "floor"):
                out.append((k, int(part[1])))
            else:
                raise ValueError(k)
    return out
