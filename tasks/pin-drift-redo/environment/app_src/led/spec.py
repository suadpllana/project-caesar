ARITY = {
    "cfg": 1,
    "tx": 1,
    "rd": 2,
    "put": 3,
    "add": 3,
    "cpy": 3,
    "raw": 3,
    "bmp": 4,
    "chk": 3,
    "lim": 3,
    "mk": 1,
    "un": 1,
    "fin": 1,
    "drp": 1,
}


def read(text):
    ops = []
    for line in text.splitlines():
        bits = line.split()
        if not bits:
            continue
        kind = bits[0]
        want = ARITY[kind]
        ops.append(tuple([kind] + [int(b) for b in bits[1:1 + want]]))
    return ops
