from dbg.frames import mapping


def resolve(img, line):
    m = mapping(img)
    lowest = {}
    for r in img.rows:
        if not r.stmt or r.line != line:
            continue
        scope = m.chain(r.at)[-1]
        if id(scope) not in lowest or r.at < lowest[id(scope)]:
            lowest[id(scope)] = r.at
    return sorted(lowest.values())
