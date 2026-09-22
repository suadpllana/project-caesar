# wrong reading: a breakpoint gets every statement row of its line
from dbg.frames import mapping


def resolve(img, line):
    m = mapping(img)
    lowest = {}
    for r in img.rows:
        if not r.stmt or r.line != line:
            continue
        scope = m.chain(r.at)[-1]
        lowest[r.at] = r.at
    return sorted(lowest.values())
