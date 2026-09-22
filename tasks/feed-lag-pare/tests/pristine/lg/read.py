WRITES = {"set": 2, "add": 2, "del": 1}


def parse(text):
    out = []
    for raw in text.splitlines():
        bits = raw.split()
        if not bits:
            continue
        op = bits[0]
        if op in WRITES:
            key = int(bits[1])
            arg = int(bits[2]) if WRITES[op] == 2 else None
            out.append((op, key, arg))
        elif op in ("mark", "unmark", "close"):
            out.append((op, bits[1]))
        elif op == "feed":
            out.append((op, bits[1], int(bits[2]), int(bits[3])))
        elif op == "ack":
            out.append((op, bits[1], int(bits[2])))
        elif op == "read":
            out.append((op, bits[1], int(bits[2])))
        elif op == "pare":
            out.append((op, int(bits[1])))
        else:
            raise ValueError(raw)
    return out
