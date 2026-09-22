import re

KEY = re.compile(r"\A[a-z]{1,10}\Z")


class Bad(Exception):
    pass


def parse(body):
    cap = None
    floor = None
    ops = []
    for num, raw in enumerate(body.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        bits = line.split()
        if bits[0] == "page":
            if cap is not None or len(bits) != 3:
                raise Bad("line %d: bad page line" % num)
            cap = int(bits[1])
            floor = int(bits[2])
            continue
        if cap is None:
            raise Bad("line %d: no page line yet" % num)
        if len(bits) != 2 or bits[0] not in ("put", "del"):
            raise Bad("line %d: bad op" % num)
        if not KEY.match(bits[1]):
            raise Bad("line %d: bad key" % num)
        ops.append((bits[0], bits[1]))
    if cap is None:
        raise Bad("no page line")
    return cap, floor, ops
