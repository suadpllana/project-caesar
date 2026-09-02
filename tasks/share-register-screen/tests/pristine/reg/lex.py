OPS = {
    "co": 2,
    "cl": 3,
    "is": 4,
    "mv": 5,
    "nm": 2,
    "nx": 1,
    "pg": 1,
}


class Bad(Exception):
    pass


def scan(text):
    out = []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        op = bits[0]
        if op not in OPS:
            raise Bad("%d: %s" % (i, op))
        rest = bits[1:]
        if len(rest) != OPS[op]:
            raise Bad("%d: %s wants %d" % (i, op, OPS[op]))
        out.append((op, tuple(rest)))
    return out
